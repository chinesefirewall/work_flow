import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import queue

# import your functions
import work_flow  # assumes work_flow.py is next to this file

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Work Keeper")
        self.geometry("520x420")
        self.resizable(False, False)

        # state
        self.worker = None
        self.stop_event = threading.Event()
        self.log_q = queue.Queue()

        # form
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        self.duration = tk.StringVar(value="60")
        self.interval = tk.StringVar(value="5")
        self.mode     = tk.StringVar(value="auto")  # auto|type|print
        self.action   = tk.StringVar(value="type")  # type|press
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
        self.log = tk.Text(frm, height=10, width=56, state="disabled")
        self.log.grid(row=row, column=0, columnspan=2, sticky="nsew")
        frm.columnconfigure(1, weight=1)

        self.after(100, self.drain_log)

    def start(self):
        try:
            duration = int(self.duration.get())
            interval = int(self.interval.get())
            if duration <= 0 or interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Duration and Interval must be positive integers.")
            return

        self.append_log("Starting…")
        self.stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        # run() is blocking; we run it in a thread
        def target():
            # Wrap work_flow.run to add a bit of UI logging
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
            self.log_q.put(f"Finished with code {rc} at {datetime.now().strftime('%H:%M:%S')}")
            self.after(0, self._on_done)

        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    def stop(self):
        # True stop: signal the worker via stop_event; the run() loop cooperatively exits.
        if self.worker and self.worker.is_alive():
            self.append_log("Stopping…")
            self.stop_event.set()
            self.stop_btn.config(state="disabled")
            # Poll until the thread ends to avoid blocking the UI.
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

    def append_log(self, line):
        self.log_q.put(line)

    def drain_log(self):
        try:
            while True:
                line = self.log_q.get_nowait()
                self.log.config(state="normal")
                self.log.insert("end", f"{line}\n")
                self.log.see("end")
                self.log.config(state="disabled")
        except queue.Empty:
            pass
        self.after(200, self.drain_log)

if __name__ == "__main__":
    App().mainloop()
