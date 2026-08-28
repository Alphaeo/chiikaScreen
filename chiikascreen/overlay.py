"""Visual overlay: an agent 'cursor' that rides along the real mouse cursor,
click-through so it never blocks clicks, plus the Ctrl+T prompt box and the
popup used to show the model's answer."""

import tkinter as tk

import win32api
import win32con
import win32gui


def _make_clickthrough(win: tk.Toplevel) -> None:
    hwnd = win.winfo_id()
    styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT,
    )


class AgentCursor:
    """Small always-on-top, click-through marker that follows the real
    mouse cursor so the agent visibly 'has its own cursor' on screen."""

    IDLE_COLOR = "#4da3ff"
    BUSY_COLOR = "#ffb64d"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", "black")
        self.win.config(bg="black")

        self.label = tk.Label(
            self.win, text="●", fg=self.IDLE_COLOR, bg="black",
            font=("Segoe UI", 14),
        )
        self.label.pack()

        self.win.update_idletasks()
        _make_clickthrough(self.win)
        self._follow()

    def set_busy(self, busy: bool) -> None:
        self.label.config(fg=self.BUSY_COLOR if busy else self.IDLE_COLOR)

    def position(self) -> tuple[int, int]:
        return win32api.GetCursorPos()

    def _follow(self) -> None:
        x, y = win32api.GetCursorPos()
        self.win.geometry(f"+{x + 14}+{y + 10}")
        self.win.after(16, self._follow)


class InputBox:
    """Borderless text entry that pops up below the cursor on Ctrl+T."""

    def __init__(self, root: tk.Tk, x: int, y: int, on_submit):
        self.on_submit = on_submit
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1e1e1e")
        self.win.geometry(f"320x36+{x}+{y + 24}")

        self.entry = tk.Entry(
            self.win, font=("Segoe UI", 11), bg="#2a2a2a", fg="white",
            insertbackground="white", relief="flat",
        )
        self.entry.pack(fill="both", expand=True, padx=4, pady=4)
        self.entry.focus_force()
        self.entry.bind("<Return>", self._submit)
        self.entry.bind("<Escape>", lambda e: self.win.destroy())
        self.win.bind("<FocusOut>", lambda e: self.win.destroy())

    def _submit(self, _event=None) -> None:
        text = self.entry.get().strip()
        self.win.destroy()
        if text:
            self.on_submit(text)


class AnswerPopup:
    """Small popup used to show the model's answer near the cursor."""

    def __init__(self, root: tk.Tk, x: int, y: int, text: str, timeout_ms: int = 15000):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1e1e1e")

        label = tk.Label(
            self.win, text=text, font=("Segoe UI", 10), fg="white", bg="#1e1e1e",
            wraplength=360, justify="left", padx=10, pady=8,
        )
        label.pack()
        self.win.update_idletasks()
        self.win.geometry(f"+{x}+{y + 24}")
        label.bind("<Button-1>", lambda e: self.win.destroy())
        self.win.after(timeout_ms, self.win.destroy)
