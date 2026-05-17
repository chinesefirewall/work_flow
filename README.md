# Work Flow: Windows-friendly Auto Typer/Key Presser

This is a small, beginner‑friendly Python script that can:
- Type text into the currently active window at fixed intervals, or
- Press one or more keys (like Enter, Down, Ctrl+S) at fixed intervals,
for a total duration that you choose. It works with Google Sheets (in your browser), Microsoft Excel, Notepad, etc., as long as the target window is focused.

Script location: work_flow.py
Run it from the project root using: python work_flow.py

Tiny GUI wrapper: app_gui.py
Run the GUI from the project root using: python app_gui.py


## What it’s useful for
- Keeping a session “alive” by pressing a key periodically.
- Repeating a simple action in Excel or Google Sheets (e.g., Down then Enter).
- Typing a piece of text periodically.


## Quick start (newbie‑friendly)
If you don’t want to pass any command‑line options, you can change the default behavior at the top of `work_flow.py` in the section:

User-configurable defaults (easy to edit)

By default, it is set to TYPE into the currently active window every 5 seconds for 3 hours.

- To use the defaults, simply run:
  `python work_flow.py`

- To customize via CLI flags instead of editing the file, see the Examples section below.


## Requirements
- Windows PC
- Python 3.8 or newer
- Optional for actual typing/pressing: pyautogui (installed automatically if you use the requirements file below). If pyautogui is not available, the script will print what it would have typed/pressed instead.

A minimal requirements file is provided at:
- requirements.txt


## Step-by-step: Install and set up on Windows
1) Install Python (if you don’t already have it)
- Download the latest Python 3 for Windows from https://www.python.org/downloads/windows/
- During installation, check the box “Add Python to PATH”.
- After install, open PowerShell and verify:
  `python --version`
  You should see something like Python 3.11.x

2) Get this project on your PC
- If you already have the repository, open PowerShell in the project’s root folder.
- Otherwise, clone it (requires Git):
  `git clone <your-repo-url>`
  `cd work_flow`

3) Create and activate a virtual environment (recommended)
- Create venv:
  `python -m venv .venv`
- Activate venv (PowerShell):
  `.\.venv\Scripts\Activate`
  Your prompt should show (.venv) at the beginning when active.

4) Install the requirement for typing/pressing
- From the project root, run:
  `pip install -r requirements.txt`

5) Test a simple run (prints to console)
- Run from the project root:
  `python work_flow.py --mode print --duration 10 --interval 2`
  You should see messages printed every 2 seconds for ~10 seconds.

6) Try typing into a focused window (optional)
- Open Notepad (or focus your browser with Google Sheets/Excel window).
- Run:
  `python work_flow.py --mode type --action type --message "Hello" --duration 10 --interval 2`
  Keep Notepad (or the target app) focused; you should see typing occur automatically.


## How to run (common examples)
Run commands from the project root (this folder).

- Use defaults (TYPE every 5s for 3h; see the DEFAULT_* values inside work_flow.py):
  python work_flow.py

- Print every 5 seconds for 1 minute (no typing):
  python work_flow.py --mode print --duration 60 --interval 5

- Type into the active window every 5 seconds for 2 minutes:
  python work_flow.py --mode type --action type --message "Still here" --duration 120 --interval 5

- Google Sheets: type a slash without pressing Enter (open shortcuts) every 5 seconds for 1 minute:
  python work_flow.py --mode type --action type --message "/" --no-enter --duration 60 --interval 5

- Excel (Windows): press Ctrl+S every 30 seconds for 10 minutes (to save):
  python work_flow.py --mode type --action press --keys "ctrl+s" --duration 600 --interval 30

- Google Sheets navigation: go Down then Enter every 5 seconds for 1 minute:
  python work_flow.py --mode type --action press --keys "down,enter" --duration 60 --interval 5


## Explanation of options
- --duration: Total run time in seconds (e.g., 60)
- --interval: Seconds between actions (e.g., 5)
- --mode: auto | type | print
  - auto: try to use pyautogui; fall back to printing if not available
  - type: force using pyautogui (if not available, it will fall back and tell you)
  - print: only print to console (no keyboard control)
- --action: type | press
  - type: type the text in --message (and press Enter by default)
  - press: press key(s) specified by --keys
- --message: Text to type when --action type is used
- --no-enter: Don’t press Enter after typing (useful for typing "/" in Google Sheets)
- --keys: Keys to press for --action press. Examples:
  - Single key: "enter", "f2", "down"
  - Chord (hold together): "ctrl+s", "ctrl+shift+v"
  - Sequence (in order): "down,enter"


## Using an IDE (VS Code, PyCharm, etc.)
- VS Code
  - Open the project folder.
  - Select the Python interpreter: Command Palette > Python: Select Interpreter > choose .venv if you created it.
  - Run: Terminal > New Terminal, then use the same commands as above.
  - Or configure a launch.json to run the script `work_flow.py` with desired args.

- PyCharm
  - Open the project folder.
  - Set your interpreter to the project’s .venv.
  - Run/Debug configuration:
    - Script path: point to `work_flow.py` (or choose Script path mode).
    - Parameters: add desired args (e.g., --mode type --action press --keys "enter")


## Tips and safety notes for Windows
- Keep the target window focused so it receives the keystrokes.
- You can stop early with Ctrl+C in the terminal, or use the GUI Stop button (now a true stop via a cooperative event).
- pyautogui has a failsafe: quickly move your mouse to a screen corner to abort (if enabled).
- If typing/pressing doesn’t work in a specific app window, ensure the terminal and the target app are running with the same privilege level (both normal user). Some elevated (Admin) windows may ignore simulated input from non‑elevated processes.
- Keyboard layout matters (e.g., different behavior on non‑US layouts). Adjust your message/keys accordingly.
- High DPI/scaling or multi‑monitor setups generally don’t affect key presses, but keep the app visible and focused.

## Browser Flow — Automated URL Task Runner

WorkKeeper now includes a **Browser Flow** feature that opens a list of URLs in Chrome and runs a configured task on each page automatically.

### Quick start (Browser Flow)

**Note for macOS Users:** You may need to grant "Screen Recording" and "Accessibility" permissions to your terminal or IDE if you encounter issues with browser automation or screenshots.

1) Install the new dependencies:
   `pip install -r requirements.txt`

2) Edit `urls_config.json` with your URLs and tasks (see below for available tasks).

3) Run from the command line:
   `python browser_flow.py --config urls_config.json`

   Or use the GUI — open the **Browser Flow** tab:
   `python app_gui.py`

### urls_config.json format

```json
{
  "browser": "chrome",
  "headless": false,
  "delay_between_sites": 5,
  "page_load_wait": 3,
  "max_retries": 2,
  "chrome_profile_path": "",
  "chrome_profile_name": "Default",
  "sites": [
    {
      "url": "https://www.google.com",
      "task": "screenshot",
      "params": { "output": "screenshots/google.png" }
    },
    {
      "url": "https://example.com/login",
      "task": "fill_form",
      "params": {
        "fields": { "#username": "myuser", "#password": "mypass" },
        "submit_selector": "button[type=submit]"
      }
    }
  ],
  "repeat": {
    "enabled": false,
    "count": 1,
    "delay_between_cycles": 60
  }
}
```

Config fields:
- **headless**: run Chrome without a visible window (true/false)
- **delay_between_sites**: seconds to wait between each URL
- **page_load_wait**: seconds to wait after opening a page before running the task
- **max_retries**: number of retry attempts per task on failure (with exponential backoff)
- **chrome_profile_path**: path to a Chrome user data directory to reuse logins (leave empty for a fresh profile). Windows example: `C:/Users/YourName/AppData/Local/Google/Chrome/User Data`
- **chrome_profile_name**: profile folder name inside the user data dir (default: `Default`)
- **repeat**: enable cycling through the URL list multiple times with a delay between cycles
- **total_duration_minutes**: stop the entire flow after this many minutes regardless of cycle count (optional)

### Available browser tasks (defined in browser_tasks.py)

| Task name        | Description                                      | Key params                                    |
|-----------------|--------------------------------------------------|-----------------------------------------------|
| screenshot       | Save a screenshot of the page                    | output (file path)                            |
| check_email      | Wait for Gmail inbox to load                     | timeout                                       |
| type_in_cell     | Type into a Google Sheets formula bar            | text (supports {timestamp})                   |
| click_element    | Click an element by CSS selector                 | selector, timeout                             |
| fill_form        | Fill multiple form fields and optionally submit  | fields (selector→value map), submit_selector  |
| wait_and_scroll  | Scroll to page bottom (for lazy-loaded content)  | pause, scrolls                                |
| browse_and_scroll| Randomly browse and scroll for a set duration    | duration, scroll_pause, screenshot_dir        |
| navigate_back    | Go back in browser history                       | —                                             |
| refresh_page     | Refresh the current page                         | —                                             |
| run_javascript   | Execute custom JavaScript                        | script                                        |
| wait_for_element | Wait for an element to appear                    | selector, timeout                             |
| type_text        | Type into any input element by CSS selector      | selector, text, clear, press_enter, timeout   |

You can add your own tasks by defining a function in `browser_tasks.py` with the signature `def my_task(driver, params: dict) -> None`.

### Browser Flow CLI options

- `python browser_flow.py --config urls_config.json` — run with a config file
- `python browser_flow.py --headless` — force headless mode (overrides config)
- `python browser_flow.py --log-file browser.log` — enable file logging with rotation
- `python browser_flow.py --total-duration 60` — force total duration in minutes (overrides config)

### Chrome profile tip (Windows)

To avoid logging in every time, set `chrome_profile_path` in your config to your Chrome user data directory. On Windows this is typically:
```
C:/Users/YourName/AppData/Local/Google/Chrome/User Data
```
**Important:** Close all Chrome windows before running browser_flow with a profile path, or Chrome will refuse to start a second instance using the same profile.


## Efficiency notes
- The main loop uses a fixed‑cadence scheduler (`next_fire`) to reduce drift over long runs.
- It uses a short sleep and, when available, `threading.Event.wait()` to remain responsive to Stop without busy‑waiting.
- It falls back from pyautogui to console printing if control fails, avoiding repeated exceptions.

## Packaging for Windows (PyInstaller)
You can create a single‑file EXE for the console script and a windowed EXE for the GUI.

1) Install PyInstaller in your venv:
   `pip install pyinstaller`

2) Build console executable (prints a console window):
   `pyinstaller --onefile --name WorkFlowCLI work_flow.py`
   - Output appears in `dist/WorkFlowCLI.exe`.

3) Build GUI executable (no console window, launches the Tkinter app):
   `pyinstaller --onefile --windowed --name WorkKeeper app_gui.py`
   - Output appears in `dist/WorkKeeper.exe`.

4) Test the EXEs on your machine. On first run, Windows SmartScreen may warn you (unsigned binary).

Tips:
- If you see missing module errors, ensure you installed requirements into the same venv before building.
- To include an app icon (optional), add `--icon path/to/icon.ico` to the PyInstaller command.
- For distribution, zip the `dist/*.exe` file(s) and share. For corporate environments, consider code‑signing to reduce SmartScreen warnings.


## Troubleshooting
- I only see “(would type)” or “(would press)” messages
  - pyautogui may not be installed, or failed to load. Install the requirement:
    pip install -r requirements.txt
  - Or you ran with --mode print. Use --mode type or --mode auto.

- Nothing is typed in my app
  - Ensure the target window is focused and not minimized.
  - Try running PowerShell/Terminal and the target app at the same privilege level (both non‑Admin).
  - Some apps may block simulated input; test with Notepad to verify your setup.

- How do I stop it?
  - Press Ctrl+C in the terminal.


## Default behavior reference (edit inside the script)
At the top of `work_flow.py` you’ll see:
- DEFAULT_DURATION_SECONDS = 3 * 60 * 60  (3 hours)
- DEFAULT_INTERVAL_SECONDS = 5
- DEFAULT_MODE = "type"
- DEFAULT_ACTION = "type"
- DEFAULT_MESSAGE = "Hello from work_flow"
- DEFAULT_NO_ENTER = False
- DEFAULT_KEYS = "enter"

Change these values to modify the behavior when running with no arguments:
  python -m test_dags.work_flow


## Uninstall / clean up
- Deactivate venv: deactivate
- Remove venv folder if you created one: delete the .venv directory
- Remove installed package(s) from the venv if desired: pip uninstall pyautogui


## Executables in build/ and dist (how to find and use them)
When you build this project with PyInstaller, two folders are involved:

- build/
  - Temporary/intermediate files produced during the build. Useful for debugging, but you don’t distribute anything from here.
  - You can safely delete this folder; PyInstaller will recreate it next time.

- dist/
  - Final, ready‑to‑run executables. This is the folder you’ll share with others.

What you’ll typically see after running the packaging commands in the section above:

- Windows (after building with the commands shown):
  - dist/WorkFlowCLI.exe — Console executable for the CLI script (`work_flow.py`).
  - dist/WorkKeeper.exe — GUI executable for the Tkinter app (`app_gui.py`).

- macOS (example artifacts already present in this repo):
  - dist/WorkFlowCLI — Console executable (no .exe suffix on macOS/Linux).
  - dist/WorkKeeper — GUI binary, and also a full app bundle:
  - dist/WorkKeeper.app — Standard macOS app bundle (double‑click to launch).

Notes about run/launch methods by platform:
- Windows
  - Double‑click `dist\WorkKeeper.exe` to open the GUI.
  - Or, from PowerShell/Command Prompt in the project root:
    - `.\\dist\\WorkKeeper.exe`
    - `.\\dist\\WorkFlowCLI.exe --mode print --duration 10 --interval 2`

- macOS
  - GUI: double‑click `dist/WorkKeeper.app`. If Gatekeeper warns that the app is from an unidentified developer, you can:
    - Right‑click the app > Open, then confirm, or
    - Run: `xattr -r -d com.apple.quarantine "dist/WorkKeeper.app"` once to remove the quarantine attribute.
  - CLI/GUI from Terminal:
    - `./dist/WorkFlowCLI --mode print --duration 10 --interval 2`
    - `./dist/WorkKeeper`

- Linux (if you build there):
  - Executables will be similar to macOS (no `.exe` suffix). Example:
    - `./dist/WorkFlowCLI`

One‑file vs one‑folder (for reference):
- The examples here use `--onefile`, which produces a single executable in `dist/` (recommended for distribution).
- If you build without `--onefile` (a “one‑folder” build), PyInstaller creates a subfolder under `dist/` (e.g., `dist/WorkFlowCLI/`) that contains the executable plus supporting files. In that case, run the executable inside that subfolder.

Building from .spec files (optional):
- This repo includes `WorkFlowCLI.spec` and `WorkKeeper.spec`. You can reproduce the same builds by running:
  - `pyinstaller WorkFlowCLI.spec`
  - `pyinstaller WorkKeeper.spec`

Cleaning up:
- To remove previous build outputs, delete the `build/` and `dist/` folders and rebuild.
