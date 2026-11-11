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


def _stats_files(server_dir):
    level = _level_dir(server_dir)
    # Ältere Versionen legen die Dateien unter world/stats ab, neuere unter world/players/stats
    return glob(os.path.join(level, "stats", "*.json")) + glob(
        os.path.join(level, "players", "stats", "*.json")
    )


def stats_signature(server_dir):
    """Ändert sich, sobald Minecraft Statistiken speichert oder ein Spieler dazukommt."""
    files = _stats_files(server_dir)
    newest = max((os.path.getmtime(path) for path in files), default=0)
    return len(files), newest


def collect_rankings(server_dir):
    """Liest alle Spielerstatistiken und gibt pro Rangliste die Top 10 zurück.

    Jeder Eintrag ist (uuid, name, wert); Spieler mit 0 tauchen nicht auf.
    """
    names = _player_names(server_dir)

    players = {}
    for path in _stats_files(server_dir):
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


def player_head(key):
    """8 × 8-Gesicht inklusive Hut-Ebene, per UUID oder Name; einmal pro Lauf des Bots geladen."""
    if key not in _head_cache:
        try:
            request = urllib.request.Request(
                f"https://mc-heads.net/avatar/{key}/8",
                headers={"User-Agent": "minecraft-discord-bot"},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                face = Image.open(io.BytesIO(response.read())).convert("RGB")
            _head_cache[key] = face.resize((8, 8), Image.NEAREST)
        except Exception:
            return _fallback_head(key)  # nicht cachen, nächstes Mal neu versuchen
    return _head_cache[key]


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


# Grasblock fürs Server-Banner, als einziges Symbol mehrfarbig
GRASS_BLOCK = ["GGGGGGGGG", "GgGGGgGGg", "GBgGBGgBG", "BBBgBBBGB", "BbBBBbBBB",
               "BBBbBBBbB", "bBBBBBbBB", "BBbBBBBBb", "BBBBbBBBB"]
GRASS_COLORS = {"G": (106, 170, 64), "g": (80, 140, 50), "B": (134, 96, 67), "b": (106, 76, 52)}

BANNER_COLOR = (178, 150, 232)
BANNER_OFFLINE = (150, 140, 165)
GREEN, RED = (70, 170, 90), (200, 70, 70)
BANNER_H = 300


def _banner(info):
    """Server-Banner über den Ranglisten, so breit wie die drei Karten zusammen.

    `info` kommt aus dem Bot: online, address, players, max, tps, whitelist,
    deaths (Liste (Name, Anzahl) absteigend, None wenn offline) und dims (Liste (Name, offen)).
    """
    R = lambda *v: [int(x * SCALE) for x in v]
    W = CARD_W * 3
    color = BANNER_COLOR if info["online"] else BANNER_OFFLINE
    muted, line = _shade(color, 0.42), _shade(color, 0.82)

    img = Image.new("RGBA", R(W, BANNER_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Ränder wie bei den Karten: links bündig mit der ersten, rechts mit der dritten
    x0, y0, x1, y1 = 19, 18, CARD_W * 2 + 315, BANNER_H - 22
    d.rectangle(R(x0 + 4, y0 + 4, x1 + 4, y1 + 4), fill=INK)
    d.rectangle(R(x0, y0, x1, y1), fill=color, outline=INK, width=3 * SCALE)

    d.rectangle(R(37, 42, 80, 83), fill=INK)
    block = Image.new("RGB", (9, 9))
    for y, row in enumerate(GRASS_BLOCK):
        for x, c in enumerate(row):
            block.putpixel((x, y), GRASS_COLORS[c])
    img.paste(block.resize(R(27, 27), Image.NEAREST), tuple(R(45, 49)))
    d.text(R(92, 59), "Server", font=_font(23, 700), fill=INK, anchor="ls")
    d.text(R(93, 81), info["address"], font=_number_font(10), fill=muted, anchor="ls")

    status = "ONLINE" if info["online"] else "OFFLINE"
    status_font = _number_font(11)
    right = x1 - 18
    width = d.textlength(status, font=status_font) / SCALE + 34
    d.rectangle(R(right - width, 44, right, 74), fill=INK)
    d.rectangle(R(right - width + 10, 54, right - width + 20, 64), fill=GREEN if info["online"] else RED)
    d.text(R(right - width + 27, 59), status, font=status_font, fill=color, anchor="lm")
    d.line(R(37, 100, right, 100), fill=line, width=SCALE)

    label_font, name_font = _number_font(10), _font(14, 600)
    column = (right - 37) / 3

    def label(x, text):
        d.text(R(x, 126), text, font=label_font, fill=muted, anchor="ls")

    def head(x, y, key, size=26):
        d.rectangle(R(x, y, x + size, y + size), fill=INK)
        img.paste(player_head(key).resize(R(size - 2, size - 2), Image.NEAREST), tuple(R(x + 1, y + 1)))

    # Spieler
    x = 37
    label(x, "SPIELER")
    count = f"{len(info['players'])}/{info['max']}" if info["online"] else "-"
    d.text(R(x, 166), count, font=_number_font(24), fill=INK, anchor="ls")
    shown = info["players"][:8]
    for index, name in enumerate(shown):
        head(x + index * 30, 180, name)
    if len(info["players"]) > len(shown):
        d.text(R(x + len(shown) * 30 + 4, 193), f"+{len(info['players']) - len(shown)}",
               font=_number_font(10), fill=INK, anchor="lm")
    if not info["players"]:
        text = "niemand online" if info["online"] else "Server nicht erreichbar"
        d.text(R(x, 197), text, font=_font(12, 600), fill=muted, anchor="ls")
    extra = [f"WHITELIST {info['whitelist']}"]
    if info["tps"] is not None:
        extra.insert(0, f"TPS {info['tps']:.1f}")
    d.text(R(x, 240), "   ".join(extra), font=_number_font(9.5), fill=INK, anchor="ls")

    # Tode, die Top 3
    x = 37 + column
    d.line(R(x - 12, 112, x - 12, 250), fill=line, width=SCALE)
    deaths = info["deaths"]
    label(x, f"TODE · {sum(n for _, n in deaths)}" if deaths is not None else "TODE")
    if not deaths:
        text = "noch niemand gestorben" if deaths is not None else "Server nicht erreichbar"
        d.text(R(x, 160), text, font=_font(12, 600), fill=muted, anchor="ls")
    for index, (name, n) in enumerate((deaths or [])[:3]):
        y = 140 + index * 34
        head(x, y, name)
        value = str(n)
        d.text(R(x + column - 26, y + 13), value, font=_number_font(11.5), fill=INK, anchor="rm")
        room = R(x + column - 26)[0] - d.textlength(value, font=_number_font(11.5)) - R(x + 34 + 8)[0]
        d.text(R(x + 34, y + 13), _fit(d, name, name_font, room), font=name_font, fill=INK, anchor="lm")

    # Dimensionen
    x = 37 + 2 * column
    d.line(R(x - 12, 112, x - 12, 250), fill=line, width=SCALE)
    label(x, "DIMENSIONEN")
    for index, (name, open_) in enumerate(info["dims"]):
        y = 140 + index * 40
        d.rectangle(R(x, y, x + 26, y + 26), fill=INK)
        d.rectangle(R(x + 6, y + 6, x + 20, y + 20), fill=GREEN if open_ else RED)
        d.text(R(x + 34, y + 13), name, font=name_font, fill=INK, anchor="lm")
        d.text(R(x + column - 26, y + 13), "OFFEN" if open_ else "GESPERRT",
               font=label_font, fill=INK, anchor="rm")

    return img.resize((W * 2, BANNER_H * 2), Image.LANCZOS)


def render_info(info, server_dir=None):
    """Server-Banner und darunter die Ranglisten als ein PNG mit durchsichtigem Hintergrund.

    Ohne Server-Ordner gibt es keine Statistiken, dann nur das Banner.
    """
    banner = _banner(info)
    cards = []
    if server_dir:
        cards = [_card(board, rows) for board, rows in zip(BOARDS, collect_rankings(server_dir))]

    height = banner.height + (CARD_H * 2 if cards else 0)
    image = Image.new("RGBA", (banner.width, height), (0, 0, 0, 0))
    image.alpha_composite(banner, (0, 0))
    for index, card in enumerate(cards):
        image.alpha_composite(card, (CARD_W * 2 * index, banner.height))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer
