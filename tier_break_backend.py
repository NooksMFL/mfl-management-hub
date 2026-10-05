import math
import urllib.parse
import requests

import wallet_cache_backend as shared

PLAYERS_URL = "https://z519wdyajg.execute-api.us-east-1.amazonaws.com/prod/players"

WEIGHTS = {
    "GK": {"GK": 1.00},
    "CB": {"PAS": 0.05, "DEF": 0.64, "DRI": 0.09, "PAC": 0.02, "PHY": 0.20},
    "LB": {"PAS": 0.19, "DEF": 0.44, "DRI": 0.17, "PAC": 0.10, "PHY": 0.10},
    "RB": {"PAS": 0.19, "DEF": 0.44, "DRI": 0.17, "PAC": 0.10, "PHY": 0.10},
    "LWB": {"PAS": 0.19, "DEF": 0.44, "DRI": 0.17, "PAC": 0.10, "PHY": 0.10},
    "RWB": {"PAS": 0.19, "DEF": 0.44, "DRI": 0.17, "PAC": 0.10, "PHY": 0.10},
    "CDM": {"PAS": 0.28, "DEF": 0.40, "DRI": 0.17, "PHY": 0.15},
    "CM": {"PAS": 0.43, "SHO": 0.12, "DEF": 0.10, "DRI": 0.29, "PHY": 0.06},
    "LM": {"PAS": 0.43, "SHO": 0.12, "DEF": 0.10, "DRI": 0.29, "PHY": 0.06},
    "RM": {"PAS": 0.43, "SHO": 0.12, "DEF": 0.10, "DRI": 0.29, "PHY": 0.06},
    "CAM": {"PAS": 0.34, "SHO": 0.21, "DRI": 0.38, "PAC": 0.07},
    "CF": {"PAS": 0.24, "SHO": 0.23, "DRI": 0.40, "PAC": 0.13},
    "LW": {"PAS": 0.24, "SHO": 0.23, "DRI": 0.40, "PAC": 0.13},
    "RW": {"PAS": 0.24, "SHO": 0.23, "DRI": 0.40, "PAC": 0.13},
    "ST": {"PAS": 0.10, "SHO": 0.46, "DRI": 0.29, "PAC": 0.10, "PHY": 0.05},
}

STAT_KEYS = {
    "PAC": "pace",
    "SHO": "shooting",
    "PAS": "passing",
    "DRI": "dribbling",
    "DEF": "defense",
    "PHY": "physical",
    "GK": "goalkeeping",
}


def _headers():
    return {
        "Authorization": "Bearer " + shared.token(),
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }


def _js_round(value):
    # MFL player-info uses Math.round; ratings are positive, so this matches JS.
    return math.floor(value + 0.5)


def raw_ovr(metadata, position):
    weights = WEIGHTS.get(position)
    if not weights:
        return None
    total = 0.0
    for short, weight in weights.items():
        stat = metadata.get(STAT_KEYS[short], 0) or 0
        total += float(stat) * weight
    return total


def _minimum_route(metadata, position, threshold):
    weights = WEIGHTS.get(position, {})
    if not weights:
        return None, None, []

    current = raw_ovr(metadata, position)
    if current is None:
        return None, None, []
    gap = max(0.0, threshold - current)
    if gap <= 1e-9:
        return 0, "Already over threshold", []

    options = []
    for stat, weight in weights.items():
        current_stat = int(metadata.get(STAT_KEYS[stat], 0) or 0)
        room = max(0, 99 - current_stat)
        if weight <= 0 or room <= 0:
            continue
        points = math.ceil((gap - 1e-12) / weight)
        if points <= room:
            options.append({
                "stat": stat,
                "points": points,
                "weight": weight,
                "gain": points * weight,
            })

    options.sort(key=lambda x: (x["points"], -x["weight"], x["stat"]))
    if not options:
        return None, "No single-stat route", []

    best_points = options[0]["points"]
    best = [x for x in options if x["points"] == best_points]
    route = " / ".join(f'+{x["points"]} {x["stat"]}' for x in best[:3])
    return best_points, route, options


def _one_point_breaks(metadata, position, threshold):
    current = raw_ovr(metadata, position)
    if current is None:
        return []
    result = []
    for stat, weight in WEIGHTS.get(position, {}).items():
        current_stat = int(metadata.get(STAT_KEYS[stat], 0) or 0)
        if current_stat >= 99:
            continue
        if current + weight >= threshold - 1e-9:
            result.append(stat)
    return result


def analyse_player(player, target_ovr=75):
    metadata = player.get("metadata") if isinstance(player, dict) else {}
    metadata = metadata if isinstance(metadata, dict) else {}
    positions = metadata.get("positions") or []
    primary = positions[0] if positions else None
    current_ovr = int(metadata.get("overall") or 0)
    raw = raw_ovr(metadata, primary)
    if raw is None:
        return None

    # To display target_ovr with Math.round, raw rating must reach target - 0.5.
    threshold = float(target_ovr) - 0.5
    gap = max(0.0, threshold - raw)
    min_points, route, options = _minimum_route(metadata, primary, threshold)
    one_point = _one_point_breaks(metadata, primary, threshold)

    if gap <= 0:
        band = "Already there"
    elif one_point:
        band = "🔥 1 gain away"
    elif min_points == 2:
        band = "🟢 Very close"
    elif min_points == 3:
        band = "🟡 Close"
    else:
        band = "⚪ Further away"

    owner = player.get("ownedBy") if isinstance(player.get("ownedBy"), dict) else {}
    contract = player.get("activeContract") if isinstance(player.get("activeContract"), dict) else {}
    club = contract.get("club") if isinstance(contract.get("club"), dict) else {}

    return {
        "id": player.get("id"),
        "name": (str(metadata.get("firstName") or "") + " " + str(metadata.get("lastName") or "")).strip(),
        "age": metadata.get("age"),
        "position": primary,
        "positions": ", ".join(positions),
        "overall": current_ovr,
        "raw_ovr": round(raw, 3),
        "gap": round(gap, 3),
        "min_points": min_points,
        "best_route": route,
        "one_point_stats": ", ".join(one_point),
        "band": band,
        "owner": owner.get("name") or "",
        "club": club.get("name") or "",
        "PAC": metadata.get("pace"),
        "SHO": metadata.get("shooting"),
        "PAS": metadata.get("passing"),
        "DRI": metadata.get("dribbling"),
        "DEF": metadata.get("defense"),
        "PHY": metadata.get("physical"),
        "GK": metadata.get("goalkeeping"),
        "mfl_url": f"https://app.playmfl.com/players/{player.get('id')}",
    }


def fetch_players(overall=74, age_min=16, age_max=42, positions=None, max_pages=10):
    params = {
        "limit": 100,
        "sorts": "metadata.overall",
        "sortsOrders": "DESC",
        "overallMin": overall,
        "overallMax": overall,
        "ageMin": age_min,
        "ageMax": age_max,
    }
    if positions:
        params["positions"] = ",".join(positions)

    all_rows = []
    before_id = None
    seen = set()

    for _ in range(max_pages):
        call_params = dict(params)
        if before_id is not None:
            call_params["beforePlayerId"] = before_id

        response = requests.get(
            PLAYERS_URL,
            headers=_headers(),
            params=call_params,
            timeout=30,
        )
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list) or not rows:
            break

        new_count = 0
        for row in rows:
            pid = row.get("id") if isinstance(row, dict) else None
            if pid in seen:
                continue
            seen.add(pid)
            all_rows.append(row)
            new_count += 1

        if len(rows) < 100 or new_count == 0:
            break
        before_id = rows[-1].get("id")

    return all_rows


def scan_tier_break(current_ovr=74, target_ovr=75, age_min=16, age_max=42, positions=None, max_pages=10):
    players = fetch_players(
        overall=current_ovr,
        age_min=age_min,
        age_max=age_max,
        positions=positions,
        max_pages=max_pages,
    )
    analysed = []
    for player in players:
        row = analyse_player(player, target_ovr=target_ovr)
        if row is not None and row["overall"] == current_ovr:
            analysed.append(row)

    analysed.sort(
        key=lambda r: (
            999 if r["min_points"] is None else r["min_points"],
            r["gap"],
            r["age"] if r["age"] is not None else 999,
            r["name"],
        )
    )
    return analysed
