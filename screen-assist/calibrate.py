"""Einmalige Kalibrierung: die vier Bildschirmecken im Kamerabild anklicken.

Aufruf:  python calibrate.py

Es oeffnet ein Fenster mit dem aktuellen Kamerabild. Klicke die vier Ecken
des Bildschirms von PC 1 an -- Reihenfolge egal, die Software sortiert sie.
Mit Taste 's' speichern, 'r' zuruecksetzen, 'q' abbrechen. Die Ecken werden
in config.json geschrieben.
"""

import json
import sys

import cv2

from source import FrameSource

CONFIG_PATH = "config.json"


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    source = FrameSource(config)
    frame = source.read()
    clone = frame.copy()
    points = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
            points.append([x, y])

    win = "Kalibrierung - 4 Bildschirmecken anklicken"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, on_mouse)

    print("Klicke die 4 Ecken des Bildschirms an. s=speichern r=reset q=quit")

    while True:
        # Bei Kamera: Live-Bild; bei Testbild: Standbild.
        if config["source"]["type"] == "camera":
            frame = source.read()
        clone = frame.copy()

        for i, (px, py) in enumerate(points):
            cv2.circle(clone, (px, py), 6, (0, 255, 0), -1)
            cv2.putText(clone, str(i + 1), (px + 8, py - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if len(points) >= 2:
            cv2.polylines(clone, [cv2.convexHull(
                __import__("numpy").array(points))], True, (0, 200, 0), 1)

        cv2.imshow(win, clone)
        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            print("Abgebrochen.")
            break
        if key == ord("r"):
            points = []
            print("Zurueckgesetzt.")
        if key == ord("s"):
            if len(points) != 4:
                print(f"Erst 4 Ecken anklicken (aktuell {len(points)}).")
                continue
            config["dewarp"]["corners"] = points
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"Gespeichert: {points}")
            break

    source.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    sys.exit(main())
