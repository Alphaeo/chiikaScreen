"""Visual overlay: an agent 'cursor' that rides along the real mouse cursor,
click-through so it never blocks clicks, plus the Ctrl+T prompt box and the
popup used to show the model's answer."""

import tkinter as tk
from pathlib import Path

import win32api
import win32con
import win32gui
from PIL import Image, ImageTk

# Color-key used for window transparency (-transparentcolor). Anything that
# exact color becomes a hole in the window. Magenta instead of black/white
# because real cursor art is unlikely to use it, avoiding accidental holes.
TRANSPARENT_KEY = "#ff00ff"

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
IDLE_CURSOR = ASSETS_DIR / "cursor.png"
BUSY_CURSOR = ASSETS_DIR / "cursor_busy.png"


def _make_clickthrough_and_keyed(win: tk.Toplevel) -> None:
    """Make the window click-through AND key out TRANSPARENT_KEY - done via
    raw win32 calls, not Tk's own `-transparentcolor` attribute. Tk manages
    the layered window's color key internally when you set -transparentcolor,
    and if we also poke GWL_EXSTYLE via SetWindowLong (needed for
    WS_EX_TRANSPARENT click-through, which Tk has no API for), the two
    fight over the same layered-window state and the window paints solid
    black instead of the image. Doing both raw win32 calls ourselves avoids
    the conflict entirely."""
    hwnd = win.winfo_id()
    styles = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(
        hwnd,
        win32con.GWL_EXSTYLE,
        styles | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT,
    )
    colorref = win32api.RGB(*_hex_to_rgb(TRANSPARENT_KEY))
    win32gui.SetLayeredWindowAttributes(hwnd, colorref, 0, win32con.LWA_COLORKEY)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _load_keyed(path: Path) -> ImageTk.PhotoImage:
    """Load a transparent PNG and pre-blend it onto the color-key so
    anti-aliased/semi-transparent edges fade into "invisible" instead of
    being flattened onto some default (that's what caused the black square:
    Tk needs a background to flatten a text glyph itself has no alpha)."""
    img = Image.open(path).convert("RGBA")
    keyed_bg = Image.new("RGBA", img.size, TRANSPARENT_KEY)
    flat = Image.alpha_composite(keyed_bg, img).convert("RGB")
    return ImageTk.PhotoImage(flat)


class AgentCursor:
    """Small always-on-top, click-through marker that follows the real
    mouse cursor so the agent visibly 'has its own cursor' on screen.

    Customize the look by dropping your own transparent PNG (~48x48) at
    chiikascreen/assets/cursor.png (idle) and/or cursor_busy.png (thinking)."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.config(bg=TRANSPARENT_KEY)

        self._idle_img = _load_keyed(IDLE_CURSOR)
        self._busy_img = _load_keyed(BUSY_CURSOR) if BUSY_CURSOR.exists() else self._idle_img

        self.label = tk.Label(self.win, image=self._idle_img, bg=TRANSPARENT_KEY, bd=0)
        self.label.pack()

        self.win.update_idletasks()
        _make_clickthrough_and_keyed(self.win)
        self._follow()

    def set_busy(self, busy: bool) -> None:
        self.label.config(image=self._busy_img if busy else self._idle_img)

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
    """Popup used to show the model's answer near the cursor. Stays open
    until the user closes it (click anywhere on it, or the x) - answers can
    take minutes to arrive, so auto-hiding after a few seconds just loses them."""

    def __init__(self, root: tk.Tk, x: int, y: int, text: str):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1e1e1e", highlightbackground="#3a3a3a", highlightthickness=1)

        close = tk.Label(
            self.win, text="✕", font=("Segoe UI", 9), fg="#888888", bg="#1e1e1e",
            cursor="hand2", padx=6, pady=2,
        )
        close.pack(anchor="ne")
        close.bind("<Button-1>", lambda e: self.win.destroy())

        label = tk.Label(
            self.win, text=text, font=("Segoe UI", 10), fg="white", bg="#1e1e1e",
            wraplength=360, justify="left", padx=10, pady=(0, 10),
        )
        label.pack()
        label.bind("<Button-1>", lambda e: self.win.destroy())

        self.win.update_idletasks()
        self.win.geometry(f"+{x}+{y + 24}")
