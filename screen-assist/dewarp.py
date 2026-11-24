"""Entzerrung: rechnet das schraege Kamerabild auf einen geraden,
frontalen Bildschirm-Ausschnitt um (perspektivische Korrektur).

Du markierst einmalig die vier Ecken des Bildschirms im Kamerabild
(calibrate.py). Danach weiss die Software, wo der Schirm ist, und kann
jedes Kamerabild in ein gerades Rechteck verwandeln. Dadurch ist die
genaue Kamera-/Armposition fast egal -- Hauptsache alle vier Ecken sind
im Bild.

Normalisierte Koordinaten (0..1) der KI beziehen sich immer auf dieses
gerade Rechteck und landen so pixelgenau auf der richtigen Stelle.
"""

import cv2
import numpy as np


def order_corners(pts: np.ndarray) -> np.ndarray:
    """Sortiert 4 Punkte als oben-links, oben-rechts, unten-rechts, unten-links."""
    pts = np.array(pts, dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).ravel()
    return np.array(
        [
            pts[np.argmin(s)],      # oben-links  (kleinste Summe)
            pts[np.argmin(diff)],   # oben-rechts (kleinste Differenz)
            pts[np.argmax(s)],      # unten-rechts(groesste Summe)
            pts[np.argmax(diff)],   # unten-links (groesste Differenz)
        ],
        dtype="float32",
    )


class Dewarper:
    def __init__(self, corners, out_w: int, out_h: int):
        self.out_w = int(out_w)
        self.out_h = int(out_h)
        self.matrix = None
        if corners:
            self.set_corners(corners)

    def set_corners(self, corners):
        src = order_corners(corners)
        dst = np.array(
            [[0, 0], [self.out_w, 0], [self.out_w, self.out_h], [0, self.out_h]],
            dtype="float32",
        )
        self.matrix = cv2.getPerspectiveTransform(src, dst)

    @property
    def ready(self) -> bool:
        return self.matrix is not None

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Verwandelt ein Kamerabild in den geraden Bildschirm-Ausschnitt."""
        if self.matrix is None:
            # Noch nicht kalibriert: Bild nur auf Zielgroesse skalieren.
            return cv2.resize(frame, (self.out_w, self.out_h))
        return cv2.warpPerspective(frame, self.matrix, (self.out_w, self.out_h))
