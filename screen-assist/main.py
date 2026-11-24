"""Screen-Assist -- Hauptprogramm.

Zeigt das (entzerrte) Spiegelbild von PC 1 auf einem Monitor an PC 2 und legt
live KI-Hinweise darueber: Markierungen 'Hier klicken' / 'Das eintippen' genau
auf der richtigen Stelle, plus ein Seitenpanel mit Erklaerung und Code.

Bedienung:
  LEERTASTE  Frage stellen (tippen, ENTER sendet das aktuelle Bild + Frage)
  C          Neu kalibrieren (startet calibrate.py-Hinweis)
  TAB        Seitenpanel ein/aus
  ESC        Beenden

Start:  python main.py
Vorher einmal:  python calibrate.py   (Bildschirmecken markieren)
"""

import json
import threading

import pygame

from source import FrameSource
from dewarp import Dewarper
from display import Display
from assistant import Assistant

CONFIG_PATH = "config.json"


class App:
    def __init__(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.source = FrameSource(self.config)
        dw = self.config["dewarp"]
        self.dewarper = Dewarper(dw.get("corners"), dw["output_width"], dw["output_height"])
        self.display = Display(self.config)
        self.assistant = None  # erst bei Bedarf -- braucht API-Key
        self.result = None
        self.status = ""
        self.typing = False
        self.question = ""
        self._lock = threading.Lock()

    def _ensure_assistant(self):
        if self.assistant is None:
            self.assistant = Assistant(self.config)

    def _ask_async(self, frame, question):
        def worker():
            try:
                self._ensure_assistant()
                res = self.assistant.ask(frame, question)
                with self._lock:
                    self.result = res
                    self.status = ""
            except Exception as e:  # noqa: BLE001  -- Fehler sichtbar machen
                with self._lock:
                    self.result = {"summary": f"Fehler: {e}", "annotations": []}
                    self.status = ""
        with self._lock:
            self.status = "Denke nach..."
        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            frame = self.source.read()
            warped = self.dewarper.apply(frame)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.typing:
                        running = self._handle_typing(event, warped)
                    else:
                        running = self._handle_hotkey(event, warped)

            with self._lock:
                result, status = self.result, self.status
            if self.typing:
                status = f"Frage: {self.question}_"
            self.display.render(warped, result, status)
            clock.tick(30)

        self.source.release()
        self.display.quit()

    def _handle_hotkey(self, event, warped):
        if event.key == pygame.K_ESCAPE:
            return False
        if event.key == pygame.K_TAB:
            self.display.show_panel = not self.display.show_panel
        elif event.key == pygame.K_c:
            self.result = {
                "summary": "Zum Kalibrieren Programm beenden und "
                "'python calibrate.py' ausfuehren.",
                "annotations": [],
            }
        elif event.key == pygame.K_SPACE:
            self.typing = True
            self.question = ""
        return True

    def _handle_typing(self, event, warped):
        if event.key == pygame.K_ESCAPE:
            self.typing = False
            self.question = ""
        elif event.key == pygame.K_RETURN:
            self.typing = False
            self._ask_async(warped.copy(), self.question)
            self.question = ""
        elif event.key == pygame.K_BACKSPACE:
            self.question = self.question[:-1]
        elif event.unicode and event.unicode.isprintable():
            self.question += event.unicode
        return True


if __name__ == "__main__":
    App().run()
