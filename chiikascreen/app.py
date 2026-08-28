"""Wires the hotkey, overlay, screen capture and local model together."""

import threading
import tkinter as tk

import keyboard

from .capture import capture_screen
from .model import ScreenModel
from .overlay import AgentCursor, AnswerPopup, InputBox

HOTKEY = "ctrl+t"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.cursor = AgentCursor(self.root)
        self.model: ScreenModel | None = None
        self.model_error: str | None = None

        threading.Thread(target=self._load_model, daemon=True).start()
        keyboard.add_hotkey(HOTKEY, self._on_hotkey, suppress=True)
        print(f"chiikaScreen pret. {HOTKEY} pour poser une question. Chargement du modele en cours...")

    def _load_model(self) -> None:
        try:
            self.model = ScreenModel()
            print("Modele charge.")
        except Exception as exc:  # noqa: BLE001 - surfaced to the user via the popup
            self.model_error = str(exc)
            print(f"Erreur de chargement du modele: {exc}")

    def _on_hotkey(self) -> None:
        x, y = self.cursor.position()
        self.root.after(0, lambda: InputBox(self.root, x, y, lambda q: self._handle_question(q, x, y)))

    def _handle_question(self, question: str, x: int, y: int) -> None:
        threading.Thread(target=self._answer, args=(question, x, y), daemon=True).start()

    def _answer(self, question: str, x: int, y: int) -> None:
        self.root.after(0, lambda: self.cursor.set_busy(True))

        if self.model is None:
            msg = self.model_error or "Le modele charge encore, reessaie dans quelques secondes."
            self.root.after(0, lambda: self._show(x, y, msg))
            self.root.after(0, lambda: self.cursor.set_busy(False))
            return

        try:
            image = capture_screen()
            answer = self.model.ask(image, question)
        except OSError:
            answer = "Le modele a crashe sur cette capture (memoire insuffisante). Reessaie."
        except Exception as exc:  # noqa: BLE001
            answer = f"Erreur: {exc}"

        self.root.after(0, lambda: self._show(x, y, answer))
        self.root.after(0, lambda: self.cursor.set_busy(False))

    def _show(self, x: int, y: int, text: str) -> None:
        AnswerPopup(self.root, x, y, text)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
