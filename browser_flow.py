"""
Browser automation engine for WorkKeeper.

Opens a list of URLs in Chrome and executes configured tasks on each page.
Supports repeat cycles, Chrome profile persistence, retry logic, and file logging.

Windows notes:
- Uses webdriver-manager to auto-download the correct ChromeDriver for your Chrome version.
- Chrome profile paths should use forward slashes or raw strings (e.g., "C:/Users/You/AppData/Local/Google/Chrome/User Data").
- No admin rights required.

Usage:
    python browser_flow.py --config urls_config.json
    python browser_flow.py --config urls_config.json --headless
    python browser_flow.py --config urls_config.json --log-file browser.log
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import browser_tasks

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("browser_flow")


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """Configure logging to console and optionally to a rotating file."""
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_file:
        # Ensure log directory exists (Windows-safe)
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    logger.setLevel(level)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    """Load and return the JSON config file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Driver creation
# ---------------------------------------------------------------------------

def create_driver(config: dict, headless_override: Optional[bool] = None) -> webdriver.Chrome:
    """Create a Chrome WebDriver instance based on config settings."""
    options = Options()

    headless = headless_override if headless_override is not None else config.get("headless", False)
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    # Suppress "Chrome is being controlled by automated test software" bar
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Chrome profile support — avoids re-login on every run
    profile_path = config.get("chrome_profile_path")
    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")
        profile_name = config.get("chrome_profile_name", "Default")
        options.add_argument(f"--profile-directory={profile_name}")

    # Use webdriver-manager to auto-download matching ChromeDriver
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ---------------------------------------------------------------------------
# Task execution with retry
# ---------------------------------------------------------------------------

def execute_task(driver, task_name: str, params: dict, max_retries: int = 1, stop_event: Optional[threading.Event] = None, screenshot_dir_override: Optional[str] = None) -> bool:
    """Look up and execute a task function from browser_tasks with optional retry.

    Returns True on success, False on failure.
    """
    task_fn = getattr(browser_tasks, task_name, None)
    if task_fn is None:
        logger.warning("Unknown task: '%s' — skipping", task_name)
        return False

    # Inject screenshot_dir_override if provided
    if screenshot_dir_override:
        if task_name == "screenshot":
            # If 'output' is provided, we might want to change its directory
            # or if it's not provided, we use the override as the base.
            output = params.get("output")
            if output:
                filename = os.path.basename(output)
                params["output"] = os.path.join(screenshot_dir_override, filename)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                params["output"] = os.path.join(screenshot_dir_override, f"screenshot_{timestamp}.png")
        elif task_name == "browse_and_scroll":
            params["screenshot_dir"] = screenshot_dir_override

    attempt = 0
    while attempt < max_retries:
        if stop_event and stop_event.is_set():
            return False
        attempt += 1
        try:
            # Pass stop_event to tasks if they support it
            import inspect
            sig = inspect.signature(task_fn)
            if "stop_event" in sig.parameters:
                task_fn(driver, params, stop_event=stop_event)
            else:
                task_fn(driver, params)
            return True
        except Exception as e:
            wait = min(2 ** attempt, 30)  # exponential backoff capped at 30s
            if attempt < max_retries:
                logger.warning(
                    "Task '%s' failed (attempt %d/%d): %s — retrying in %ds",
                    task_name, attempt, max_retries, e, wait,
                )
                # Sleep in small increments for stop_event
                waited = 0
                while waited < wait:
                    if stop_event and stop_event.is_set():
                        return False
                    time.sleep(min(0.5, wait - waited))
                    waited += 0.5
            else:
                logger.error("Task '%s' failed after %d attempt(s): %s", task_name, max_retries, e)
    return False


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def run_browser_flow(
    config_path: str,
    headless_override: Optional[bool] = None,
    log_file: Optional[str] = None,
    stop_event: Optional[threading.Event] = None,
    screenshot_dir_override: Optional[str] = None,
    total_duration_override: Optional[int] = None,
) -> int:
    """Run the full browser automation flow.

    Returns 0 on success, 1 on error.
    """
    setup_logging(log_file)

    try:
        config = load_config(config_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Failed to load config '%s': %s", config_path, e)
        return 1

    delay = config.get("delay_between_sites", 5)
    page_load_wait = config.get("page_load_wait", 3)
    max_retries = config.get("max_retries", 1)
    repeat = config.get("repeat", {})
    cycles = repeat.get("count", 1) if repeat.get("enabled", False) else 1
    cycle_delay = repeat.get("delay_between_cycles", 60)
    sites = config.get("sites", [])
    
    total_duration_minutes = total_duration_override if total_duration_override is not None else config.get("total_duration_minutes", 0)
    total_duration_seconds = total_duration_minutes * 60 if total_duration_minutes else 0
    flow_start_time = time.time()

    if not sites:
        logger.warning("No sites configured — nothing to do.")
        return 0

    # If total_duration_minutes is set, loop indefinitely until time runs out
    if total_duration_seconds:
        cycles = 999999  # effectively unlimited; time limit will stop us
        logger.info("Starting browser flow: %d site(s), running for %d minute(s)", len(sites), total_duration_minutes)
    else:
        logger.info("Starting browser flow: %d site(s), %d cycle(s)", len(sites), cycles)

    driver = None
    try:
        driver = create_driver(config, headless_override)

        for cycle in range(cycles):
            if stop_event and stop_event.is_set():
                logger.info("Stopped by user before cycle %d.", cycle + 1)
                return 0
            if total_duration_seconds and (time.time() - flow_start_time) >= total_duration_seconds:
                logger.info("Total duration of %d minute(s) reached. Stopping.", total_duration_minutes)
                break

            logger.info("--- Cycle %d/%d at %s ---", cycle + 1, cycles, datetime.now().strftime("%H:%M:%S"))

            for idx, site in enumerate(sites, 1):
                if stop_event and stop_event.is_set():
                    logger.info("Stopped by user during cycle %d.", cycle + 1)
                    return 0
                if total_duration_seconds and (time.time() - flow_start_time) >= total_duration_seconds:
                    logger.info("Total duration of %d minute(s) reached. Stopping.", total_duration_minutes)
                    break

                url = site.get("url", "")
                task_name = site.get("task", "")
                params = site.get("params", {})

                logger.info("[%d/%d] Opening: %s", idx, len(sites), url)
                try:
                    driver.get(url)
                    # Sleep in small increments for stop_event
                    waited = 0
                    while waited < page_load_wait:
                        if stop_event and stop_event.is_set():
                            logger.info("Stopped by user during page load wait.")
                            return 0
                        time.sleep(min(0.5, page_load_wait - waited))
                        waited += 0.5
                except Exception as e:
                    logger.error("[%d/%d] Failed to open %s: %s", idx, len(sites), url, e)
                    continue

                if task_name:
                    ok = execute_task(
                        driver, 
                        task_name, 
                        params, 
                        max_retries=max_retries, 
                        stop_event=stop_event, 
                        screenshot_dir_override=screenshot_dir_override
                    )
                    status = "completed" if ok else "FAILED"
                    logger.info("[%d/%d] Task '%s' %s", idx, len(sites), task_name, status)
                else:
                    logger.info("[%d/%d] No task configured — page opened only", idx, len(sites))

                if idx < len(sites):
                    # Sleep in small increments for stop_event
                    waited = 0
                    while waited < delay:
                        if stop_event and stop_event.is_set():
                            logger.info("Stopped by user during delay between sites.")
                            return 0
                        time.sleep(min(0.5, delay - waited))
                        waited += 0.5

                if cycle < cycles - 1:
                    logger.info("Waiting %ds before next cycle...", cycle_delay)
                    # Sleep in small increments so we can respond to stop_event
                    waited = 0.0
                    while waited < cycle_delay:
                        if stop_event and stop_event.is_set():
                            logger.info("Stopped by user between cycles.")
                            return 0
                        sleep_step = min(0.5, cycle_delay - waited)
                        time.sleep(sleep_step)
                        waited += sleep_step

        logger.info("Browser flow completed successfully.")
        return 0

    except Exception as e:
        logger.error("Browser flow error: %s", e, exc_info=True)
        return 1
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed.")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WorkKeeper Browser Automation — open URLs in Chrome and run tasks on each."
    )
    parser.add_argument(
        "--config", default="urls_config.json",
        help="Path to the JSON config file (default: urls_config.json)",
    )
    parser.add_argument(
        "--headless", action="store_true", default=None,
        help="Run Chrome in headless mode (overrides config setting)",
    )
    parser.add_argument(
        "--log-file", default=None,
        help="Path to a log file (enables file logging with rotation)",
    )
    parser.add_argument(
        "--screenshot-dir", default=None,
        help="Optional override for the directory where screenshots are saved",
    )
    parser.add_argument(
        "--total-duration", type=int, default=None,
        help="Force total duration in minutes (overrides config setting)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    # Command-line overrides for config settings
    if args.total_duration:
        # We need to load config first or pass it to run_browser_flow differently
        # Actually run_browser_flow loads it.
        pass

    sys.exit(run_browser_flow(
        config_path=args.config,
        headless_override=args.headless,
        log_file=args.log_file,
        screenshot_dir_override=args.screenshot_dir,
        total_duration_override=args.total_duration
    ))
