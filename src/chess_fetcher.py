"""
Chess Game Fetcher:
Fetches game data from Chess.com URLs or direct PGN strings.
Decodes Chess.com's proprietary TCN moveList format into standard chess moves.
"""

import io
import re
import requests
import chess
import chess.pgn
from typing import Dict, Optional, Tuple, List

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

TCN_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?{~}(^)[_]@#$,./&-*++="
PIECE_CHARS = "qnrbkp"

def decode_tcn_to_uci(tcn_string: str) -> List[str]:
    """
    Decodes Chess.com's proprietary TCN (2-character compressed notation)
    into standard UCI moves (e.g. 'e2e4', 'e7e5').
    """
    uci_moves = []
    length = len(tcn_string)
    
    for i in range(0, length, 2):
        if i + 1 >= length:
            break
            
        c1 = tcn_string[i]
        c2 = tcn_string[i + 1]
        
        if c1 not in TCN_CHARS or c2 not in TCN_CHARS:
            continue
            
        from_idx = TCN_CHARS.index(c1)
        to_idx = TCN_CHARS.index(c2)
        promotion = ""
        
        # Handle pawn promotions in TCN
        if to_idx > 63:
            promo_piece_idx = int((to_idx - 64) / 3)
            if promo_piece_idx < len(PIECE_CHARS):
                promotion = PIECE_CHARS[promo_piece_idx]
            to_idx = from_idx + (-8 if from_idx < 16 else 8) + ((to_idx - 1) % 3) - 1
            
        if from_idx < 64 and to_idx < 64:
            from_sq = chess.square_name(from_idx)
            to_sq = chess.square_name(to_idx)
            uci_moves.append(f"{from_sq}{to_sq}{promotion}")
            
    return uci_moves


def uci_moves_to_game(uci_moves: List[str], headers: Optional[Dict] = None) -> chess.pgn.Game:
    """Constructs a python-chess Game tree from a list of UCI move strings."""
    game = chess.pgn.Game()
    if headers:
        for k, v in headers.items():
            game.headers[k] = str(v)
            
    node = game
    board = game.board()
    
    for uci_str in uci_moves:
        try:
            move = chess.Move.from_uci(uci_str)
            if move in board.legal_moves:
                node = node.add_variation(move)
                board.push(move)
            else:
                break
        except Exception:
            break
            
    return game


def extract_game_id(url: str) -> Optional[Tuple[str, str]]:
    """Extracts (game_type, game_id) from Chess.com URL."""
    match = re.search(r"chess\.com/game/(live|daily)/(\d+)", url)
    if match:
        return match.group(1), match.group(2)
    return None


def fetch_from_chess_com(url: str) -> Dict:
    """Fetches game details from Chess.com callback API and decodes moves."""
    extracted = extract_game_id(url)
    if not extracted:
        raise ValueError(f"Invalid Chess.com URL. Expected format: https://www.chess.com/game/live/123456789")

    game_type, game_id = extracted
    callback_url = f"https://www.chess.com/callback/{game_type}/game/{game_id}"

    response = requests.get(callback_url, headers=HEADERS, timeout=12)
    if response.status_code != 200:
        raise ConnectionError(f"Could not fetch game from Chess.com. Status code: {response.status_code}")

    data = response.json()
    game_obj = data.get("game", {})

    # Extract clean player details from pgnHeaders
    pgn_headers = game_obj.get("pgnHeaders", {}) or {}
    user1 = game_obj.get("user1", {}) or {}
    user2 = game_obj.get("user2", {}) or {}

    white_name = pgn_headers.get("White") or user1.get("username", "White")
    white_elo = pgn_headers.get("WhiteElo") or user1.get("rating", "?")

    black_name = pgn_headers.get("Black") or user2.get("username", "Black")
    black_elo = pgn_headers.get("BlackElo") or user2.get("rating", "?")

    result_text = pgn_headers.get("Termination") or game_obj.get("resultMessage", pgn_headers.get("Result", "Complete"))

    raw_pgn = game_obj.get("pgn", "")
    move_list = game_obj.get("moveList", "")

    # Decode TCN to UCI moves
    uci_moves = []
    if move_list:
        uci_moves = decode_tcn_to_uci(move_list)

    return {
        "game_id": game_id,
        "game_type": game_type,
        "white": f"{white_name} ({white_elo})",
        "black": f"{black_name} ({black_elo})",
        "result": result_text,
        "pgn": raw_pgn,
        "uci_moves": uci_moves
    }

    return {
        "game_id": game_id,
        "game_type": game_type,
        "white": f"{white_player} ({white_rating})",
        "black": f"{black_player} ({black_rating})",
        "result": game_obj.get("resultMessage", "Game Complete"),
        "pgn": raw_pgn,
        "uci_moves": uci_moves
    }


def parse_pgn_to_game(pgn_str: str, uci_moves: Optional[List[str]] = None) -> chess.pgn.Game:
    """Parses PGN text or falls back to UCI move sequence."""
    if uci_moves:
        return uci_moves_to_game(uci_moves)
        
    pgn_io = io.StringIO(pgn_str)
    game = chess.pgn.read_game(pgn_io)
    if not game:
        raise ValueError("Failed to parse PGN. Move data is empty or corrupted.")
    return game