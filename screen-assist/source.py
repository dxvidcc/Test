"""Bildquelle: liefert Frames von einer Kamera ODER einem Testbild.

Eingangs-unabhaengig gebaut: die restliche Software bekommt immer nur
'ein Bild' (ein numpy-Array im BGR-Format), egal woher es kommt. Wenn du
spaeter doch einen Capture-Stick (Splitter) verwendest, muss nur hier eine
weitere Quelle ergaenzt werden -- der Rest bleibt unveraendert.
"""

import cv2
import numpy as np


class FrameSource:
    def __init__(self, config: dict):
        src = config["source"]
        self.type = src["type"]
        self._test_frame = None
        self._cap = None

        if self.type == "camera":
            self._cap = cv2.VideoCapture(int(src["camera_index"]))
            # Moeglichst hohe Aufloesung anfordern -- scharfe Schrift braucht Pixel.
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            if not self._cap.isOpened():
                raise RuntimeError(
                    f"Kamera {src['camera_index']} konnte nicht geoeffnet werden."
                )
        elif self.type == "test_image":
            frame = cv2.imread(src["test_image"])
            if frame is None:
                raise RuntimeError(f"Testbild nicht gefunden: {src['test_image']}")
            self._test_frame = frame
        else:
            raise ValueError(f"Unbekannter Quelltyp: {self.type}")

    def read(self) -> np.ndarray:
        """Gibt den aktuellen Frame zurueck (BGR)."""
        if self.type == "camera":
            ok, frame = self._cap.read()
            if not ok:
                raise RuntimeError("Kamera lieferte kein Bild.")
            return frame
        return self._test_frame.copy()

    def release(self):
        if self._cap is not None:
            self._cap.release()
