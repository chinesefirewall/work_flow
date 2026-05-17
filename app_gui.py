import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import queue

# import your functions
import work_flow  # assumes work_flow.py is next to this file


class App(tk.Tk):
    VERSION = "1.1.0"
    def __init__(self):
        super().__init__()
        self.title(f"Work Keeper v{self.VERSION}")
        self.geometry("600x520")
        self.resizable(False, False)

        # state
        self.worker = None
        self.stop_event = threading.Event()
        self.log_q = queue.Queue()

        # Notebook (tabs)
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # --- Tab 1: Original Work Flow ---
        tab_wf = ttk.Frame(notebook, padding=12)
        notebook.add(tab_wf, text="Work Flow")
        self._build_workflow_tab(tab_wf)

        # --- Tab 2: Browser Flow ---
        tab_bf = ttk.Frame(notebook, padding=12)
        notebook.add(tab_bf, text="Browser Flow")
        self._build_browser_tab(tab_bf)

        self.after(100, self.drain_log)

    # ------------------------------------------------------------------ #
    # Tab 1 — Work Flow (original)
    # ------------------------------------------------------------------ #
    def _build_workflow_tab(self, frm):
        self.duration = tk.StringVar(value="60")
        self.interval = tk.StringVar(value="5")
        self.mode     = tk.StringVar(value="auto")
        self.action   = tk.StringVar(value="type")
        self.message  = tk.StringVar(value="Hello from work_flow")
        self.keys     = tk.StringVar(value="enter")
        self.no_enter = tk.BooleanVar(value=False)

        row = 0
        def add(label, widget):
            nonlocal row
            ttk.Label(frm, text=label, width=18).grid(row=row, column=0, sticky="w", pady=3)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            row += 1

        add("Duration (s):", ttk.Entry(frm, textvariable=self.duration, width=12))
        add("Interval (s):", ttk.Entry(frm, textvariable=self.interval, width=12))
        add("Mode:", ttk.Combobox(frm, textvariable=self.mode, values=["auto","type","print"], width=10, state="readonly"))
        add("Action:", ttk.Combobox(frm, textvariable=self.action, values=["type","press"], width=10, state="readonly"))
        add("Message (type):", ttk.Entry(frm, textvariable=self.message, width=36))
        add("Keys (press):", ttk.Entry(frm, textvariable=self.keys, width=36))

        c = ttk.Checkbutton(frm, text="Do NOT press Enter after typing", variable=self.no_enter)
        c.grid(row=row, column=0, columnspan=2, sticky="w", pady=4); row += 1

        # buttons
        btns = ttk.Frame(frm); btns.grid(row=row, column=0, columnspan=2, pady=6); row += 1
        self.start_btn = ttk.Button(btns, text="Start", command=self.start)
        self.stop_btn  = ttk.Button(btns, text="Stop",  command=self.stop, state="disabled")
        self.start_btn.grid(row=0, column=0, padx=4)
        self.stop_btn.grid(row=0, column=1, padx=4)

        # log
        ttk.Label(frm, text="Log:").grid(row=row, column=0, sticky="w"); row += 1
        self.log = tk.Text(frm, height=8, width=56, state="disabled")
        self.log.grid(row=row, column=0, columnspan=2, sticky="nsew")
        frm.columnconfigure(1, weight=1)

    def start(self):
        try:
            duration = int(self.duration.get())
            interval = int(self.interval.get())
            if duration <= 0 or interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Duration and Interval must be positive integers.")
            return

        self.append_log("Starting...")
        self.stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        def target():
            self.append_log(f"Mode={self.mode.get()}, Action={self.action.get()}")
            rc = work_flow.run(
                duration=duration,
                interval=interval,
                message=self.message.get(),
                mode=self.mode.get(),
                action=self.action.get(),
                keys=self.keys.get(),
                no_enter=self.no_enter.get(),
                stop_event=self.stop_event,
            )
            self.log_q.put(("wf", f"Finished with code {rc} at {datetime.now().strftime('%H:%M:%S')}"))
            self.after(0, self._on_done)

        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.append_log("Stopping...")
            self.stop_event.set()
            self.stop_btn.config(state="disabled")
            self._wait_for_worker()
        else:
            self.append_log("No active run to stop.")

    def _wait_for_worker(self):
        if self.worker and self.worker.is_alive():
            self.after(100, self._wait_for_worker)
        else:
            self._on_done()

    def _on_done(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    # ------------------------------------------------------------------ #
    # Tab 2 — Browser Flow
    # ------------------------------------------------------------------ #
    def _build_browser_tab(self, frm):
        self.bf_config_path = tk.StringVar(value="urls_config.json")
        self.bf_headless = tk.BooleanVar(value=False)
        self.bf_worker = None
        self.bf_stop_event = threading.Event()

        row = 0

        # Config file picker
        ttk.Label(frm, text="Config file:").grid(row=row, column=0, sticky="w", pady=3)
        cfg_frame = ttk.Frame(frm)
        cfg_frame.grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Entry(cfg_frame, textvariable=self.bf_config_path, width=32).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg_frame, text="Browse...", command=self._browse_config).pack(side="left", padx=4)
        row += 1

        # Headless checkbox
        ttk.Checkbutton(frm, text="Run headless (no visible browser window)", variable=self.bf_headless).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        row += 1

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=2, pady=6)
        row += 1
        self.bf_start_btn = ttk.Button(btns, text="Start Browser Flow", command=self._bf_start)
        self.bf_stop_btn = ttk.Button(btns, text="Stop", command=self._bf_stop, state="disabled")
        self.bf_start_btn.grid(row=0, column=0, padx=4)
        self.bf_stop_btn.grid(row=0, column=1, padx=4)

        # Status list
        ttk.Label(frm, text="Status:").grid(row=row, column=0, sticky="w")
        row += 1
        self.bf_log = tk.Text(frm, height=12, width=56, state="disabled")
        self.bf_log.grid(row=row, column=0, columnspan=2, sticky="nsew")
        frm.columnconfigure(1, weight=1)

    def _browse_config(self):
        path = filedialog.askopenfilename(
            title="Select Browser Flow Config",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.bf_config_path.set(path)

    def _bf_start(self):
        config_path = self.bf_config_path.get().strip()
        if not config_path or not os.path.isfile(config_path):
            messagebox.showerror("Config not found", f"Cannot find config file:\n{config_path}")
            return

        self._bf_append("Starting browser flow...")
        self.bf_stop_event.clear()
        self.bf_start_btn.config(state="disabled")
        self.bf_stop_btn.config(state="normal")

        def target():
            try:
                import browser_flow
                rc = browser_flow.run_browser_flow(
                    config_path=config_path,
                    headless_override=self.bf_headless.get() or None,
                    stop_event=self.bf_stop_event,
                )
                self._bf_append(f"Finished with code {rc} at {datetime.now().strftime('%H:%M:%S')}")
            except ImportError:
                self._bf_append("ERROR: browser_flow module not found. Install selenium & webdriver-manager.")
            except Exception as e:
                self._bf_append(f"ERROR: {e}")
            self.after(0, self._bf_on_done)

        self.bf_worker = threading.Thread(target=target, daemon=True)
        self.bf_worker.start()

    def _bf_stop(self):
        if self.bf_worker and self.bf_worker.is_alive():
            self._bf_append("Stopping...")
            self.bf_stop_event.set()
            self.bf_stop_btn.config(state="disabled")
            self._bf_wait()
        else:
            self._bf_append("No active browser flow to stop.")

    def _bf_wait(self):
        if self.bf_worker and self.bf_worker.is_alive():
            self.after(100, self._bf_wait)
        else:
            self._bf_on_done()

    def _bf_on_done(self):
        self.bf_start_btn.config(state="normal")
        self.bf_stop_btn.config(state="disabled")

    def _bf_append(self, line):
        self.log_q.put(("bf", line))

    # ------------------------------------------------------------------ #
    # Shared logging
    # ------------------------------------------------------------------ #
    def append_log(self, line):
        self.log_q.put(("wf", line))

    def drain_log(self):
        try:
            while True:
                item = self.log_q.get_nowait()
                if isinstance(item, tuple):
                    target, line = item
                else:
                    target, line = "wf", item

                if target == "bf":
                    widget = self.bf_log
                else:
                    widget = self.log

                widget.config(state="normal")
                widget.insert("end", f"{line}\n")
                widget.see("end")
                widget.config(state="disabled")
        except queue.Empty:
            pass
        self.after(200, self.drain_log)


if __name__ == "__main__":
    App().mainloop()