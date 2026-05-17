"""
Reusable browser task functions for WorkKeeper.

Each function receives (driver, params) and performs an action on the current page.
Add your own task functions here — they will be auto-discovered by browser_flow.py
as long as they follow the signature: def task_name(driver, params: dict) -> None

Windows notes:
- All tasks work on Windows with Chrome + ChromeDriver (managed by webdriver-manager).
- Screenshot paths use forward slashes or raw strings to avoid backslash issues.
"""
from __future__ import annotations

import os
import time
from datetime import datetime

from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def screenshot(driver, params: dict) -> None:
    """Take a screenshot of the current page.

    params:
        output (str): file path for the screenshot (default: auto-generated name).
    """
    output = params.get(
        "output",
        f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
    )
    # Ensure the directory exists (Windows-safe)
    directory = os.path.dirname(output)
    if directory:
        os.makedirs(directory, exist_ok=True)
    driver.save_screenshot(output)


def check_email(driver, params: dict) -> None:
    """Wait for Gmail inbox to load.

    params:
        timeout (int): max seconds to wait (default: 15).
    """
    timeout = params.get("timeout", 15)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
    )


def type_in_cell(driver, params: dict) -> None:
    """Type text into a Google Sheets cell via the formula bar.

    params:
        text (str): text to type. Use {timestamp} as a placeholder for the current time.
    """
    text = params.get("text", "").replace(
        "{timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    formula_bar = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "t-formula-bar-input"))
    )
    formula_bar.click()
    formula_bar.send_keys(text)
    formula_bar.send_keys(Keys.ENTER)


def click_element(driver, params: dict) -> None:
    """Click an element identified by CSS selector.

    params:
        selector (str): CSS selector of the element to click.
        timeout (int): max seconds to wait for the element (default: 10).
    """
    selector = params.get("selector")
    if not selector:
        raise ValueError("click_element requires a 'selector' param")
    timeout = params.get("timeout", 10)
    el = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    el.click()


def fill_form(driver, params: dict) -> None:
    """Fill form fields identified by CSS selectors.

    params:
        fields (dict): mapping of CSS selector -> value to type.
        submit_selector (str, optional): CSS selector of a submit button to click after filling.
        timeout (int): max seconds to wait per field (default: 10).
    """
    fields = params.get("fields", {})
    timeout = params.get("timeout", 10)
    for selector, value in fields.items():
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        el.clear()
        el.send_keys(value)

    submit = params.get("submit_selector")
    if submit:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, submit))
        )
        btn.click()


def wait_and_scroll(driver, params: dict, stop_event: Optional[threading.Event] = None) -> None:
    """Scroll to the bottom of the page (useful for lazy-loaded content).

    params:
        pause (float): seconds to pause after scrolling (default: 1.0).
        scrolls (int): number of scroll-to-bottom actions (default: 1).
    """
    pause = params.get("pause", 1.0)
    scrolls = params.get("scrolls", 1)
    for _ in range(scrolls):
        if stop_event and stop_event.is_set():
            break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Sleep in small increments for stop_event
        waited = 0
        while waited < pause:
            if stop_event and stop_event.is_set():
                return
            time.sleep(min(0.2, pause - waited))
            waited += 0.2


def browse_and_scroll(driver, params: dict, stop_event: Optional[threading.Event] = None) -> None:
    """Spend a configurable amount of time on a page, scrolling up and down,
    then take a screenshot before leaving.

    params:
        duration (int): seconds to spend on the page (default: 180 i.e. 3 minutes).
        scroll_pause (float): seconds to pause between each scroll action (default: 3.0).
        screenshot_dir (str): directory to save screenshots (default: "screenshots").
    """
    duration = params.get("duration", 180)
    scroll_pause = params.get("scroll_pause", 3.0)
    screenshot_dir = params.get("screenshot_dir", "screenshots")

    os.makedirs(screenshot_dir, exist_ok=True)

    start = time.time()
    scroll_down_flag = True

    while time.time() - start < duration:
        if stop_event and stop_event.is_set():
            return

        if scroll_down_flag:
            driver.execute_script("window.scrollBy(0, 600);")
        else:
            driver.execute_script("window.scrollBy(0, -600);")

        # Sleep in small increments for stop_event
        waited = 0
        while waited < scroll_pause:
            if stop_event and stop_event.is_set():
                return
            time.sleep(min(0.5, scroll_pause - waited))
            waited += 0.5

        # Check if we hit the bottom or top and reverse direction
        at_bottom = driver.execute_script(
            "return (window.innerHeight + window.scrollY) >= document.body.scrollHeight;"
        )
        at_top = driver.execute_script("return window.scrollY === 0;")

        if at_bottom:
            scroll_down_flag = False
        elif at_top:
            scroll_down_flag = True

    # Take a screenshot at the end
    page_title = driver.title or "page"
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in page_title)[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(screenshot_dir, f"{safe_name}_{timestamp}.png")
    driver.save_screenshot(filepath)


def navigate_back(driver, params: dict) -> None:
    """Navigate back in browser history."""
    driver.back()


def refresh_page(driver, params: dict) -> None:
    """Refresh the current page."""
    driver.refresh()


def run_javascript(driver, params: dict) -> None:
    """Execute arbitrary JavaScript on the current page.

    params:
        script (str): JavaScript code to execute.
    """
    script = params.get("script")
    if not script:
        raise ValueError("run_javascript requires a 'script' param")
    driver.execute_script(script)


def wait_for_element(driver, params: dict) -> None:
    """Wait for an element to appear on the page.

    params:
        selector (str): CSS selector of the element.
        timeout (int): max seconds to wait (default: 10).
    """
    selector = params.get("selector")
    if not selector:
        raise ValueError("wait_for_element requires a 'selector' param")
    timeout = params.get("timeout", 10)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def type_text(driver, params: dict) -> None:
    """Type text into an element identified by CSS selector.

    params:
        selector (str): CSS selector of the input element.
        text (str): text to type. Use {timestamp} for current time.
        clear (bool): whether to clear the field first (default: True).
        press_enter (bool): whether to press Enter after typing (default: False).
        timeout (int): max seconds to wait (default: 10).
    """
    selector = params.get("selector")
    if not selector:
        raise ValueError("type_text requires a 'selector' param")
    text = params.get("text", "").replace(
        "{timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    timeout = params.get("timeout", 10)
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    if params.get("clear", True):
        el.clear()
    el.send_keys(text)
    if params.get("press_enter", False):
        el.send_keys(Keys.ENTER)
