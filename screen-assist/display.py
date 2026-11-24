"""Anzeige: zeigt das entzerrte Spiegelbild auf einem Monitor an PC 2 und
legt die KI-Hinweise als Overlay darueber -- Markierungen mit Sprechblasen
('Hier klicken', 'Das eintippen') direkt auf der richtigen Stelle, plus ein
Seitenpanel fuer laengeren Text und Code.

Rendering mit pygame; die Frames kommen als numpy-Arrays (BGR) von OpenCV.
"""

import cv2
import numpy as np
import pygame

# Farben (RGB)
COL = {
    "click": (46, 204, 113),
    "type": (52, 152, 219),
    "look": (241, 196, 15),
    "warning": (231, 76, 60),
}
PANEL_BG = (24, 26, 32)
PANEL_FG = (235, 235, 235)
PANEL_W = 380


class Display:
    def __init__(self, config: dict):
        d = config["display"]
        self.show_panel = d.get("show_panel", True)
        self.win_w = int(d["window_width"])
        self.win_h = int(d["window_height"])
        pygame.init()
        pygame.display.set_caption("Screen-Assist")
        flags = pygame.FULLSCREEN if d.get("fullscreen") else 0
        monitor = int(d.get("monitor_index", 0))
        try:
            self.screen = pygame.display.set_mode(
                (self.win_w, self.win_h), flags, display=monitor
            )
        except TypeError:
            # Aeltere pygame-Version ohne display=-Parameter.
            self.screen = pygame.display.set_mode((self.win_w, self.win_h), flags)
        self.font = pygame.font.SysFont("dejavusans", 18)
        self.font_small = pygame.font.SysFont("dejavusans", 15)
        self.font_mono = pygame.font.SysFont("dejavusansmono", 14)
        self.font_big = pygame.font.SysFont("dejavusans", 22, bold=True)

    @property
    def video_w(self):
        return self.win_w - (PANEL_W if self.show_panel else 0)

    def _frame_to_surface(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (self.video_w, self.win_h))
        # pygame erwartet (width, height, 3) -> Achsen tauschen.
        return pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))

    def _draw_marker(self, a):
        x = int(a["x"] * self.video_w)
        y = int(a["y"] * self.win_h)
        color = COL.get(a.get("type", "look"), COL["look"])
        # Pulsierender Ring
        pygame.draw.circle(self.screen, color, (x, y), 26, 3)
        pygame.draw.circle(self.screen, color, (x, y), 6)
        # Sprechblase mit Label
        label = a.get("label", "")
        if label:
            txt = self.font.render(label, True, (255, 255, 255))
            pad = 8
            bw, bh = txt.get_width() + 2 * pad, txt.get_height() + 2 * pad
            bx = min(max(x + 30, 0), self.video_w - bw)
            by = min(max(y - bh // 2, 0), self.win_h - bh)
            bubble = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bubble.fill((*color, 230))
            self.screen.blit(bubble, (bx, by))
            self.screen.blit(txt, (bx + pad, by + pad))

    def _draw_panel(self, result, status):
        px = self.win_w - PANEL_W
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, PANEL_W, self.win_h))
        y = 16
        head = self.font_big.render("Assistent", True, PANEL_FG)
        self.screen.blit(head, (px + 16, y))
        y += 40
        if status:
            st = self.font_small.render(status, True, (241, 196, 15))
            self.screen.blit(st, (px + 16, y))
            y += 26
        if result:
            y = self._wrap(result.get("summary", ""), px + 16, y,
                           PANEL_W - 32, self.font, PANEL_FG)
            y += 10
            for i, a in enumerate(result.get("annotations", []), 1):
                color = COL.get(a.get("type", "look"), PANEL_FG)
                line = f"{i}. {a.get('label','')}"
                self.screen.blit(self.font.render(line, True, color), (px + 16, y))
                y += 24
                if a.get("detail"):
                    y = self._wrap(a["detail"], px + 28, y, PANEL_W - 44,
                                   self.font_small, (200, 200, 200))
                if a.get("code"):
                    y = self._code_block(a["code"], px + 16, y)
                y += 8

    def _wrap(self, text, x, y, width, font, color):
        for para in text.split("\n"):
            words, line = para.split(" "), ""
            for w in words:
                test = (line + " " + w).strip()
                if font.size(test)[0] > width and line:
                    self.screen.blit(font.render(line, True, color), (x, y))
                    y += font.get_height() + 2
                    line = w
                else:
                    line = test
            if line:
                self.screen.blit(font.render(line, True, color), (x, y))
                y += font.get_height() + 2
        return y

    def _code_block(self, code, x, y):
        lines = code.split("\n")
        box_h = len(lines) * (self.font_mono.get_height() + 2) + 10
        pygame.draw.rect(self.screen, (12, 14, 18),
                         (x, y, PANEL_W - 32, box_h))
        y += 5
        for ln in lines:
            self.screen.blit(self.font_mono.render(ln, True, (120, 230, 170)),
                             (x + 6, y))
            y += self.font_mono.get_height() + 2
        return y + 6

    def _draw_hud(self):
        hint = "LEER=Fragen  C=Kalibrieren neu  TAB=Panel  ESC=Beenden"
        s = self.font_small.render(hint, True, (180, 180, 180))
        bg = pygame.Surface((s.get_width() + 12, s.get_height() + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        self.screen.blit(bg, (10, self.win_h - s.get_height() - 16))
        self.screen.blit(s, (16, self.win_h - s.get_height() - 12))

    def render(self, frame, result, status):
        self.screen.blit(self._frame_to_surface(frame), (0, 0))
        if result:
            for a in result.get("annotations", []):
                self._draw_marker(a)
        if self.show_panel:
            self._draw_panel(result, status)
        self._draw_hud()
        pygame.display.flip()

    def quit(self):
        pygame.quit()
