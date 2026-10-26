"""Self-contained Streamlit formation board; no external scripts or services."""
import json
from pathlib import Path

import streamlit.components.v1 as components
from squad_cards import age_label
from mfl_text import font_url, read_font_url


def board_html(players, storage_key, suggestions=None, title="Squad tactics", compact=True):
    from tactics_engine import FORMATIONS, numeric, rating_at, recommend
    payload = [{"id": str(p["player_id"]), "name": str(p.get("player") or f"Player {p['player_id']}"),
                "position": str(p["position"]), "ovr": numeric(p.get("current_ovr")),
                "ratings": {role: {"value":rating_at(p,role)[0], "source":rating_at(p,role)[1]} for slots in FORMATIONS.values() for role,_,_ in slots},
                "age": age_label(p.get("age")), "club": str(p.get("club") or "—"),
                "photo": f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(p['player_id'])}/photo.webp"} for p in players]
    data = json.dumps({"players": payload, "storageKey": storage_key, "formations":FORMATIONS, "suggestions":suggestions if suggestions is not None else recommend(players), "title":title}, allow_nan=False).replace("<", "\\u003c")
    return Path(__file__).with_name("formation_board.html").read_text().replace("/*BOARD_DATA*/", data).replace("/*BODY_CLASS*/", "compact" if compact else "expanded").replace("TELETEXT_FONT_URL", font_url()).replace("READ_FONT_URL", read_font_url()).replace("BOLD_FONT_URL", read_font_url(True))


def render_board(players, storage_key, suggestions=None, title="Squad tactics", compact=True):
    components.html(board_html(players, storage_key, suggestions, title, compact), height=760 if compact else 1100, scrolling=True)
