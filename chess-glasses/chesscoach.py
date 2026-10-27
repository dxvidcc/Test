"""Speak the best chess move into a WhatsApp call from Meta glasses.

Pipeline, once a second:
  1. Screenshot the WhatsApp call window on the Mac (the glasses' camera view).
  2. Cheap local check: skip frames that barely changed or are blurry.
  3. Claude reads the board from the frame.
  4. python-chess matches that to a legal move; a move is committed once two
     frames in a row agree.
  5. Game over? Announce it. Otherwise Stockfish picks the reply.
  6. macOS `say` speaks it into BlackHole, which WhatsApp uses as microphone,
     so you hear it in the glasses.
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

def find_whatsapp_window_id():
    """CGWindowID of the largest WhatsApp window, or None if Quartz is missing."""
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


def grab_frame(window_id, region):
    with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
        cmd = ["screencapture", "-x", "-t", "jpg"]
        if window_id:
            cmd += ["-o", "-l", str(window_id)]
        elif region:
            cmd += ["-R", region]
        subprocess.run(cmd + [tmp.name], check=True)
        img = Image.open(tmp.name)
        img.load()
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
    cmd = ["say"]
    if device:
        cmd += ["-a", device]
    if voice:
        cmd += ["-v", voice]
    subprocess.run(cmd + [text], check=False)


# --- Main loop ---------------------------------------------------------------

def game_over_text(board, player_color, lang):
    p = PHRASES[lang]
    if board.is_checkmate():
        return p["lose"] if board.turn == player_color else p["win"]
    return p["draw"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--color", choices=["white", "black"], required=True, help="your colour")
    ap.add_argument("--fen", help="start from this position instead of the initial one")
    ap.add_argument("--think", type=float, default=0.5, help="Stockfish seconds per move")
    ap.add_argument("--interval", type=float, default=1.0, help="seconds between screenshots")
    ap.add_argument("--region", help="x,y,w,h to capture if the WhatsApp window is not found")
    ap.add_argument("--device", default="BlackHole 2ch", help="audio device for `say` ('' = speakers)")
    ap.add_argument("--voice", default="Anna", help="macOS voice ('' = system default)")
    ap.add_argument("--lang", choices=["de", "en"], default="de")
    ap.add_argument("--announce-opponent", action="store_true", help="also speak the move that was detected")
    ap.add_argument("--tolerance", type=int, default=3, help="misread squares allowed elsewhere")
    ap.add_argument("--change-threshold", type=float, default=2.0)
    ap.add_argument("--blur-threshold", type=float, default=50.0)
    args = ap.parse_args()

    stockfish = shutil.which("stockfish")
    if not stockfish:
        sys.exit("Stockfish not found: brew install stockfish")

    player = chess.WHITE if args.color == "white" else chess.BLACK
    board = chess.Board(args.fen) if args.fen else chess.Board()
    client = anthropic.Anthropic()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish)
    frames = FrameFilter(args.change_threshold, args.blur_threshold)

    window_id = find_whatsapp_window_id()
    if not window_id and not args.region:
        sys.exit("WhatsApp window not found. Install pyobjc-framework-Quartz or pass --region x,y,w,h")

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
            img = grab_frame(window_id, args.region)
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
