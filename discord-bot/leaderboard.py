"""Ranglisten aus den Minecraft-Statistikdateien, gezeichnet als Karten im Pixel-Look."""

import io
import json
import os
import random
import urllib.request
from glob import glob

from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
FONT_PATH = os.path.join(ASSETS, "PixelifySans.ttf")
# Pixelify-Ziffern sind schwer zu lesen (5 wie S, 2 wie 8) — Zahlen in Silkscreen
NUMBER_FONT_PATH = os.path.join(ASSETS, "Silkscreen-Bold.ttf")

INK = (24, 22, 18)
SCALE = 4  # intern hochskaliert für scharfe Kanten, Maße unten in Kartenpixeln
CARD_W, CARD_H = 340, 570
ROWS = 10

# Kleine Pixel-Symbole, 10 × 9: "H" und "S" werden in der Kartenfarbe gemalt
ICONS = {
    "pickaxe": ["..HHHHH...", "....HHHH..", ".......HH.", "......SHH.", ".....S..H.",
                "....S...H.", "...S......", "..S.......", ".S........"],
    "sword": [".......HHH", "......HHHH", ".....HHHH.", "....HHHH..", ".S.HHHH...",
              "..SHHH....", "..SSH.....", ".S..S.....", "S........."],
    "clock": ["...HHHH...", ".HH....HH.", ".H...S..H.", "H....S...H", "H....SSS.H",
              "H........H", ".H......H.", ".HH....HH.", "...HHHH..."],
}


# ------------------------------------------------------------------ Statistik


def _level_dir(server_dir):
    level = "world"
    try:
        with open(os.path.join(server_dir, "server.properties"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("level-name="):
                    level = line.split("=", 1)[1].strip() or level
    except OSError:
        pass
    return os.path.join(server_dir, level)


def _player_names(server_dir):
    """UUID → Name aus der usercache.json des Servers."""
    try:
        with open(os.path.join(server_dir, "usercache.json"), encoding="utf-8") as f:
            return {entry["uuid"]: entry["name"] for entry in json.load(f)}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def _blocks_mined(stats):
    return sum(stats.get("minecraft:mined", {}).values())


def _mobs_killed(stats):
    killed = stats.get("minecraft:killed", {})
    return sum(count for mob, count in killed.items() if mob != "minecraft:player")


def _play_hours(stats):
    custom = stats.get("minecraft:custom", {})
    ticks = custom.get("minecraft:play_time", custom.get("minecraft:play_one_minute", 0))
    return ticks / 20 / 3600


BOARDS = [
    {"title": "Abrissbirne", "subtitle": "Meiste Blöcke abgebaut", "icon": "pickaxe",
     "color": (240, 212, 110), "value": _blocks_mined, "unit": ""},
    {"title": "Monsterjäger", "subtitle": "Meiste Mobs getötet", "icon": "sword",
     "color": (232, 132, 112), "value": _mobs_killed, "unit": ""},
    {"title": "Dauerzocker", "subtitle": "Meiste Spielzeit", "icon": "clock",
     "color": (130, 182, 226), "value": _play_hours, "unit": " h"},
]


def collect_rankings(server_dir):
    """Liest alle Spielerstatistiken und gibt pro Rangliste die Top 10 zurück.

    Jeder Eintrag ist (uuid, name, wert); Spieler mit 0 tauchen nicht auf.
    """
    names = _player_names(server_dir)
    level = _level_dir(server_dir)
    # Ältere Versionen legen die Dateien unter world/stats ab, neuere unter world/players/stats
    files = glob(os.path.join(level, "stats", "*.json")) + glob(
        os.path.join(level, "players", "stats", "*.json")
    )

    players = {}
    for path in files:
        uuid = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, encoding="utf-8") as f:
                players[uuid] = json.load(f).get("stats", {})
        except (OSError, ValueError):
            continue

    rankings = []
    for board in BOARDS:
        rows = [
            (uuid, names.get(uuid, uuid[:8]), board["value"](stats))
            for uuid, stats in players.items()
        ]
        rows = sorted((row for row in rows if row[2] > 0), key=lambda row: -row[2])
        rankings.append(rows[:ROWS])
    return rankings


# ---------------------------------------------------------------------- Köpfe


_head_cache = {}


def _fallback_head(seed):
    """Platzhalter-Gesicht, falls der Kopf-Dienst nicht erreichbar ist."""
    rnd = random.Random(seed)
    skin = rnd.choice([(198, 150, 110), (140, 95, 60), (230, 190, 150), (90, 60, 40)])
    hair = rnd.choice([(60, 40, 20), (20, 20, 20), (200, 160, 60), (120, 40, 30)])
    face = Image.new("RGB", (8, 8), skin)
    d = ImageDraw.Draw(face)
    d.rectangle([0, 0, 7, 1], fill=hair)
    d.point([(1, 4), (6, 4)], fill=(255, 255, 255))
    d.point([(2, 4), (5, 4)], fill=(60, 80, 160))
    return face


def player_head(uuid):
    """8 × 8-Gesicht inklusive Hut-Ebene, einmal pro Lauf des Bots geladen."""
    if uuid not in _head_cache:
        try:
            request = urllib.request.Request(
                f"https://mc-heads.net/avatar/{uuid}/8",
                headers={"User-Agent": "minecraft-discord-bot"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                face = Image.open(io.BytesIO(response.read())).convert("RGB")
            _head_cache[uuid] = face.resize((8, 8), Image.NEAREST)
        except Exception:
            return _fallback_head(uuid)  # nicht cachen, nächstes Mal neu versuchen
    return _head_cache[uuid]


# ------------------------------------------------------------------- Zeichnen


def _font(size, weight):
    font = ImageFont.truetype(FONT_PATH, int(size * SCALE))
    font.set_variation_by_axes([weight])
    return font


def _number_font(size):
    return ImageFont.truetype(NUMBER_FONT_PATH, int(size * SCALE))


def _fit(draw, text, font, width):
    """Kürzt einen Namen mit „…“, bis er in `width` passt."""
    if draw.textlength(text, font=font) <= width:
        return text
    while text and draw.textlength(text + "…", font=font) > width:
        text = text[:-1]
    return text + "…"


def _shade(color, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in color)


def _format(value, unit):
    if unit == " h":
        if value < 1:
            return f"{int(value * 60)} min"
        return f"{int(value):,}".replace(",", ".") + " h"
    return f"{int(value):,}".replace(",", ".") + unit


def _card(board, rows):
    R = lambda *v: [int(x * SCALE) for x in v]
    color = board["color"]
    faint = _shade(color, 0.78)

    img = Image.new("RGBA", R(CARD_W, CARD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle(R(23, 22, 319, 552), fill=INK)  # Schatten
    d.rectangle(R(19, 18, 315, 548), fill=color, outline=INK, width=3 * SCALE)

    d.rectangle(R(37, 42, 80, 83), fill=INK)
    icon = Image.new("RGB", (10, 9), INK)
    for y, line in enumerate(ICONS[board["icon"]]):
        for x, c in enumerate(line):
            if c != ".":
                icon.putpixel((x, y), color)
    img.paste(icon.resize(R(26, 23), Image.NEAREST), tuple(R(45, 51)))
    d.text(R(92, 59), board["title"], font=_font(23, 700), fill=INK, anchor="ls")
    d.text(R(93, 81), board["subtitle"], font=_font(11.5, 600), fill=_shade(color, 0.5), anchor="ls")

    rank_font, row_font, value_font = _number_font(11), _font(15.5, 600), _number_font(11.5)
    y = 110
    for place in range(1, ROWS + 1):
        mid = y + 10
        entry = rows[place - 1] if place <= len(rows) else None

        if place <= 3:
            if entry:
                d.rectangle(R(37, mid - 15, 68, mid + 15), fill=INK)
            else:
                d.rectangle(R(37, mid - 15, 68, mid + 15), outline=faint, width=SCALE)
        rank_color = color if place <= 3 and entry else (INK if entry else faint)
        d.text(R(52.5, mid), str(place), font=rank_font, fill=rank_color, anchor="mm")

        if entry:
            uuid, name, value = entry
            d.rectangle(R(75, mid - 16, 110, mid + 16), fill=INK)
            img.paste(player_head(uuid).resize(R(32, 32), Image.NEAREST), tuple(R(76.5, mid - 15)))
            text = _format(value, board["unit"])
            d.text(R(296, mid), text, font=value_font, fill=INK, anchor="rm")
            room = R(296)[0] - d.textlength(text, font=value_font) - R(116 + 8)[0]
            d.text(R(116, mid), _fit(d, name, row_font, room), font=row_font, fill=INK, anchor="lm")
        else:
            d.rectangle(R(75, mid - 16, 110, mid + 16), outline=faint, width=SCALE)
            d.text(R(116, mid), "—", font=row_font, fill=faint, anchor="lm")
            d.text(R(296, mid), "—", font=row_font, fill=faint, anchor="rm")

        if place < ROWS:
            d.line(R(37, mid + 22, 298, mid + 22), fill=_shade(color, 0.88), width=SCALE)
        y += 43.5

    # Doppelte Auflösung reicht für Discord und hält die Datei klein
    return img.resize((CARD_W * 2, CARD_H * 2), Image.LANCZOS)


def render_rankings(server_dir):
    """Alle Ranglisten nebeneinander als PNG mit durchsichtigem Hintergrund."""
    cards = [_card(board, rows) for board, rows in zip(BOARDS, collect_rankings(server_dir))]
    strip = Image.new("RGBA", (CARD_W * 2 * len(cards), CARD_H * 2), (0, 0, 0, 0))
    for index, card in enumerate(cards):
        strip.alpha_composite(card, (CARD_W * 2 * index, 0))

    buffer = io.BytesIO()
    strip.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer
