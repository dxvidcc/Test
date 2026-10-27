"""Speak the best chess move into a WhatsApp call from Meta glasses.

Pipeline, once a second:
  1. Screenshot the WhatsApp call window (the glasses' camera view).
  2. Cheap local check: skip frames that barely changed or are blurry.
  3. Claude reads the board from the frame.
  4. python-chess matches that to a legal move; a move is committed once two
     frames in a row agree.
  5. Game over? Announce it. Otherwise Stockfish picks the reply.
  6. Text-to-speech plays it into a virtual cable (BlackHole on macOS,
     VB-CABLE on Windows) that WhatsApp uses as microphone, so you hear it in
     the glasses.
"""

import argparse
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import anthropic
import chess
import chess.engine
from PIL import Image, ImageChops, ImageFilter, ImageStat

MODEL = os.environ.get("CHESSCOACH_MODEL", "claude-opus-5-5")
WINDOWS = sys.platform == "win32"
DEFAULT_DEVICE = "CABLE Input" if WINDOWS else "BlackHole 2ch"
DEFAULT_VOICE = "German" if WINDOWS else "Anna"

PIECE_NAMES = {
    "de": {chess.KING: "König", chess.QUEEN: "Dame", chess.ROOK: "Turm",
           chess.BISHOP: "Läufer", chess.KNIGHT: "Springer", chess.PAWN: "Bauer"},
    "en": {chess.KING: "King", chess.QUEEN: "Queen", chess.ROOK: "Rook",
           chess.BISHOP: "Bishop", chess.KNIGHT: "Knight", chess.PAWN: "Pawn"},
}
PHRASES = {
    "de": {"takes": "schlägt", "to": "nach", "check": "Schach", "mate": "Schachmatt",
           "castle_short": "Kurze Rochade", "castle_long": "Lange Rochade",
           "promote": "wird", "win": "Schachmatt. Du gewinnst.",
           "lose": "Schachmatt. Du verlierst.", "draw": "Remis.",
           "ready": "Bereit.", "opponent": "Gegner"},
    "en": {"takes": "takes", "to": "to", "check": "check", "mate": "checkmate",
           "castle_short": "Castle kingside", "castle_long": "Castle queenside",
           "promote": "promotes to", "win": "Checkmate. You win.",
           "lose": "Checkmate. You lose.", "draw": "Draw.",
           "ready": "Ready.", "opponent": "Opponent"},
}

BOARD_SCHEMA = {
    "type": "object",
    "properties": {
        "board_visible": {"type": "boolean"},
        "ranks": {
            "type": "array",
            "description": "8 strings, rank 8 first, file a to h, FEN letters, '.' for empty",
            "items": {"type": "string"},
        },
    },
    "required": ["board_visible", "ranks"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You read physical chess boards from photos taken by smart glasses.
The photo is a screenshot of a video call, so it can be blurry, tilted or partly covered.

Return the position as 8 strings, rank 8 first, each listing files a to h.
Use FEN letters (KQRBNP white, kqrbnp black) and '.' for an empty square,
so the start position is "rnbqkbnr", "pppppppp", "........" x4, "PPPPPPPP", "RNBQKBNR".
Always give the board from White's side in this notation, whichever side the camera is on.
If no full board is visible, set board_visible to false and return an empty list."""


# --- 1. Screenshot -----------------------------------------------------------

def find_whatsapp_window():
    """The largest WhatsApp window, or None.

    macOS: its CGWindowID (needs pyobjc-framework-Quartz).
    Windows: a pygetwindow window, whose position is re-read on every capture.
    """
    if WINDOWS:
        import pygetwindow
        found = [w for w in pygetwindow.getWindowsWithTitle("WhatsApp")
                 if w.visible and not w.isMinimized and w.width > 200]
        return max(found, key=lambda w: w.width * w.height, default=None)
    try:
        import Quartz
    except ImportError:
        return None
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    best, best_area = None, 0
    for w in windows:
        if "WhatsApp" not in (w.get("kCGWindowOwnerName") or ""):
            continue
        bounds = w.get("kCGWindowBounds") or {}
        area = bounds.get("Width", 0) * bounds.get("Height", 0)
        if area > best_area:
            best, best_area = w.get("kCGWindowNumber"), area
    return best


def grab_frame(window, region):
    if WINDOWS:
        import mss
        if window:
            box = {"left": window.left, "top": window.top, "width": window.width, "height": window.height}
        else:
            x, y, w, h = (int(v) for v in region.split(","))
            box = {"left": x, "top": y, "width": w, "height": h}
        with mss.mss() as screen:
            shot = screen.grab(box)
        img = Image.frombytes("RGB", shot.size, shot.rgb)
    else:
        # delete=False: Windows can't reopen a NamedTemporaryFile, and macOS shares this path.
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            path = tmp.name
        try:
            cmd = ["screencapture", "-x", "-t", "jpg"]
            if window:
                cmd += ["-o", "-l", str(window)]
            elif region:
                cmd += ["-R", region]
            subprocess.run(cmd + [path], check=True)
            img = Image.open(path)
            img.load()
        finally:
            os.unlink(path)
    img = img.convert("RGB")
    img.thumbnail((1280, 1280))
    return img


# --- 2. Quick local look -----------------------------------------------------

class FrameFilter:
    """Skips frames that are blurry or show no change since the last one sent."""

    def __init__(self, change_threshold, blur_threshold):
        self.change_threshold = change_threshold
        self.blur_threshold = blur_threshold
        self.last_sent = None

    def worth_reading(self, img):
        small = img.convert("L").resize((160, 160))
        sharpness = ImageStat.Stat(small.filter(ImageFilter.FIND_EDGES)).var[0]
        if sharpness < self.blur_threshold:
            return False
        if self.last_sent is not None:
            diff = ImageStat.Stat(ImageChops.difference(small, self.last_sent)).mean[0]
            if diff < self.change_threshold:
                return False
        self.last_sent = small
        return True

    def force_next(self):
        self.last_sent = None


# --- 3. Read the board -------------------------------------------------------

def read_board(client, img, player_color):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    side = "White" if player_color == chess.WHITE else "Black"
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=2000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low",
                       "format": {"type": "json_schema", "schema": BOARD_SCHEMA}},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(buf.getvalue()).decode()}},
                {"type": "text", "text": f"The camera wearer plays {side}; their pieces are nearest the camera."},
            ],
        }],
    )
    if response.stop_reason in ("refusal", "max_tokens"):
        return None
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        return None
    data = json.loads(text)
    ranks = data["ranks"]
    if not data["board_visible"] or len(ranks) != 8 or any(len(r) != 8 for r in ranks):
        return None
    return ranks


# --- 4. Match it to a legal move ---------------------------------------------

def square_symbol(board, square):
    piece = board.piece_at(square)
    return piece.symbol() if piece else "."


def observed_symbol(ranks, square):
    return ranks[7 - chess.square_rank(square)][chess.square_file(square)]


def match_move(board, ranks, tolerance):
    """The legal move whose result fits the observed board, or None.

    Every square the move changes must look as expected, and the result must
    fit the observation better than the current position does. `tolerance`
    allows that many misread squares elsewhere on the board.
    """
    def mismatches(b):
        return sum(square_symbol(b, sq) != observed_symbol(ranks, sq) for sq in chess.SQUARES)

    current = mismatches(board)
    best_move, best_score = None, None
    for move in board.legal_moves:
        after = board.copy(stack=False)
        after.push(move)
        changed = [sq for sq in chess.SQUARES
                   if square_symbol(board, sq) != square_symbol(after, sq)]
        if any(square_symbol(after, sq) != observed_symbol(ranks, sq) for sq in changed):
            continue
        score = mismatches(after)
        if best_score is None or score < best_score:
            best_move, best_score = move, score
    if best_move is None or best_score >= current or best_score > tolerance:
        return None
    return best_move


# --- 6. Speak ----------------------------------------------------------------

def describe_move(board, move, lang):
    p, names = PHRASES[lang], PIECE_NAMES[lang]
    if board.is_castling(move):
        text = p["castle_short"] if chess.square_file(move.to_square) == 6 else p["castle_long"]
    else:
        piece = board.piece_at(move.from_square)
        frm, to = chess.square_name(move.from_square), chess.square_name(move.to_square)
        verb = p["takes"] if board.is_capture(move) else p["to"]
        text = f"{names[piece.piece_type]} {frm} {verb} {to}"
        if move.promotion:
            text += f", {p['promote']} {names[move.promotion]}"
    after = board.copy(stack=False)
    after.push(move)
    if after.is_checkmate():
        text += f", {p['mate']}"
    elif after.is_check():
        text += f", {p['check']}"
    return text


def speak(text, device, voice):
    print(f"  >> {text}")
    if WINDOWS:
        speak_windows(text, device, voice)
        return
    cmd = ["say"]
    if device:
        cmd += ["-a", device]
    if voice:
        cmd += ["-v", voice]
    subprocess.run(cmd + [text], check=False)


def speak_windows(text, device, voice):
    """Render with the Windows voices (SAPI5), then play on `device` (e.g. VB-CABLE's input)."""
    import pyttsx3
    import sounddevice
    import soundfile

    engine = pyttsx3.init()
    if voice:
        match = next((v for v in engine.getProperty("voices")
                      if voice.lower() in f"{v.name} {v.id}".lower()), None)
        if match:
            engine.setProperty("voice", match.id)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    try:
        engine.save_to_file(text, path)
        engine.runAndWait()
        data, rate = soundfile.read(path)
        out = None
        if device:
            out = next((i for i, d in enumerate(sounddevice.query_devices())
                        if device.lower() in d["name"].lower() and d["max_output_channels"] > 0), None)
            if out is None:
                print(f"  audio device {device!r} not found, using the default speakers")
        sounddevice.play(data, rate, device=out)
        sounddevice.wait()
    finally:
        os.unlink(path)


# --- Main loop ---------------------------------------------------------------

def game_over_text(board, player_color, lang):
    p = PHRASES[lang]
    if board.is_checkmate():
        return p["lose"] if board.turn == player_color else p["win"]
    return p["draw"]


def photo_test(paths, color, stockfish, think, lang):
    """Show what Claude reads from each photo, and the move Stockfish would pick there."""
    player = chess.WHITE if color == "white" else chess.BLACK
    client = anthropic.Anthropic()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish)
    try:
        for path in paths:
            print(f"\n=== {path}")
            img = Image.open(path).convert("RGB")
            img.thumbnail((1280, 1280))
            started = time.monotonic()
            ranks = read_board(client, img, player)
            print(f"  read in {time.monotonic() - started:.1f} s")
            if ranks is None:
                print("  no board recognised")
                continue
            placement = "/".join(ranks)
            for n in range(8, 0, -1):
                placement = placement.replace("." * n, str(n))
            board = chess.Board(f"{placement} {'w' if player == chess.WHITE else 'b'} - - 0 1")
            print(board)
            print(f"  FEN: {board.fen()}")
            if not board.is_valid():
                print("  not a legal position (a piece was misread), so no move")
                continue
            if board.is_game_over():
                print(f"  {game_over_text(board, player, lang)}")
                continue
            move = engine.play(board, chess.engine.Limit(time=think)).move
            print(f"  best move: {board.san(move)}  ({describe_move(board, move, lang)})")
    finally:
        engine.quit()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--color", choices=["white", "black"], help="your colour")
    ap.add_argument("--test-voice", action="store_true", help="speak one test line into the call, then quit")
    ap.add_argument("--photo", nargs="+", metavar="FILE",
                    help="read the board from these photos and print the best move (--color = side to move)")
    ap.add_argument("--fen", help="start from this position instead of the initial one")
    ap.add_argument("--think", type=float, default=0.5, help="Stockfish seconds per move")
    ap.add_argument("--interval", type=float, default=1.0, help="seconds between screenshots")
    ap.add_argument("--region", help="x,y,w,h to capture if the WhatsApp window is not found")
    ap.add_argument("--device", default=DEFAULT_DEVICE, help="audio device to speak into ('' = speakers)")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help="voice name, or part of it ('' = system default)")
    ap.add_argument("--stockfish", help="path to the Stockfish program, if it isn't on PATH")
    ap.add_argument("--lang", choices=["de", "en"], default="de")
    ap.add_argument("--announce-opponent", action="store_true", help="also speak the move that was detected")
    ap.add_argument("--tolerance", type=int, default=3, help="misread squares allowed elsewhere")
    ap.add_argument("--change-threshold", type=float, default=2.0)
    ap.add_argument("--blur-threshold", type=float, default=50.0)
    args = ap.parse_args()

    if args.test_voice:
        speak("Test. Springer f3." if args.lang == "de" else "Test. Knight to f3.", args.device, args.voice)
        return
    if not args.color and not args.photo:
        ap.error("--color is required")

    stockfish = args.stockfish or shutil.which("stockfish")
    if not stockfish:
        sys.exit("Stockfish not found: pass --stockfish C:\\path\\to\\stockfish.exe" if WINDOWS
                 else "Stockfish not found: brew install stockfish")

    if args.photo:
        photo_test(args.photo, args.color or "white", stockfish, args.think, args.lang)
        return

    player = chess.WHITE if args.color == "white" else chess.BLACK
    board = chess.Board(args.fen) if args.fen else chess.Board()
    client = anthropic.Anthropic()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish)
    frames = FrameFilter(args.change_threshold, args.blur_threshold)

    window = None
    if not args.region:
        print("Waiting for the WhatsApp call window (answer the call and keep it visible)...")
        while not (window := find_whatsapp_window()):
            time.sleep(2)

    def suggest():
        result = engine.play(board, chess.engine.Limit(time=args.think))
        speak(describe_move(board, result.move, args.lang), args.device, args.voice)

    speak(PHRASES[args.lang]["ready"], args.device, args.voice)
    if board.turn == player:
        suggest()

    pending = None
    try:
        while not board.is_game_over():
            started = time.monotonic()
            img = grab_frame(window, args.region)
            if frames.worth_reading(img):
                try:
                    ranks = read_board(client, img, player)
                except anthropic.APIError as e:
                    print(f"  API error: {e}")
                    ranks = None
                move = match_move(board, ranks, args.tolerance) if ranks else None
                if move is None:
                    pending = None
                elif move != pending:
                    # Seen once; keep re-reading until a second frame agrees.
                    pending = move
                    frames.force_next()
                else:
                    mover = board.turn
                    print(f"{board.fullmove_number}. {board.san(move)}")
                    if mover != player and args.announce_opponent:
                        speak(f"{PHRASES[args.lang]['opponent']}: {describe_move(board, move, args.lang)}",
                              args.device, args.voice)
                    board.push(move)
                    pending = None
                    if board.is_game_over():
                        break
                    if board.turn == player:
                        suggest()
            time.sleep(max(0.0, args.interval - (time.monotonic() - started)))
        speak(game_over_text(board, player, args.lang), args.device, args.voice)
    except KeyboardInterrupt:
        pass
    finally:
        engine.quit()
        print(board.fen())


if __name__ == "__main__":
    main()
