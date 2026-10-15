"""Self-contained Streamlit formation board; no external scripts or services."""
import json
from pathlib import Path

import streamlit.components.v1 as components
from squad_cards import age_label


def board_html(players, storage_key):
    payload = [{"id": str(p["player_id"]), "name": str(p.get("player") or f"Player {p['player_id']}"),
                "position": str(p["position"]), "ovr": float(p["current_ovr"]),
                "age": age_label(p.get("age")), "club": str(p.get("club") or "—"),
                "photo": f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(p['player_id'])}/photo.webp"} for p in players]
    data = json.dumps({"players": payload, "storageKey": storage_key}, allow_nan=False).replace("<", "\\u003c")
    return Path(__file__).with_name("formation_board.html").read_text().replace("/*BOARD_DATA*/", data)


def render_board(players, storage_key):
    components.html(board_html(players, storage_key), height=880, scrolling=True)
