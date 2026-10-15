"""Deterministic, position-aware squad selection without API requests."""
import math
import re

LEAGUES = ("Stone", "Ice", "Spark", "Flint")
QUOTAS = {"Goalkeeper": 3, "Defender": 8, "Midfielder": 8, "Forward": 6}
POSITIONS = {
    "Goalkeeper": {"GK"},
    "Defender": {"CB", "LB", "RB", "LWB", "RWB", "SW"},
    "Midfielder": {"DM", "CDM", "CM", "LM", "RM", "AM", "CAM", "LDM", "RDM", "LCM", "RCM"},
    "Forward": {"ST", "CF", "LW", "RW", "LF", "RF", "SS"},
}


def league_for(rating, sixty_league="Spark"):
    if sixty_league not in ("Spark", "Flint"):
        raise ValueError("60-rated players must belong to Spark or Flint")
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(rating) or rating < 0:
        return None
    if rating >= 73:
        return "Stone"
    if rating >= 67:
        return "Ice"
    if rating > 60 or (rating == 60 and sixty_league == "Spark"):
        return "Spark"
    return "Flint"


def position_groups(value):
    tokens = set(re.findall(r"[A-Z]+", str(value).upper()))
    return {group for group, positions in POSITIONS.items() if tokens & positions}


def _assign(players):
    """Maximum-weight assignment to 25 role slots, with dummy empty slots.

    Hungarian assignment prioritises filled slots, then total OVR. Unlike a
    greedy selection, a versatile player cannot displace the only specialist
    needed for another role.
    """
    slots = [role for role, count in QUOTAS.items() for _ in range(count)]
    n, m = len(slots), len(players) + len(slots)
    costs = []
    for role in slots:
        costs.append([
            -(100000 + min(p["current_ovr"], 1000)) if role in p["groups"] else 1000000
            for p in players
        ] + [0] * n)
    u, v, matched, way = [0] * (n+1), [0] * (m+1), [0] * (m+1), [0] * (m+1)
    for i in range(1, n+1):
        matched[0] = i
        j0 = 0
        minimum, used = [float("inf")] * (m+1), [False] * (m+1)
        while True:
            used[j0] = True
            i0, delta, j1 = matched[j0], float("inf"), 0
            for j in range(1, m+1):
                if not used[j]:
                    cur = costs[i0-1][j-1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j], way[j] = cur, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(m+1):
                if used[j]:
                    u[matched[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if matched[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            matched[j0] = matched[j1]
            j0 = j1
    result = []
    for j in range(1, len(players)+1):
        if matched[j] and costs[matched[j]-1][j-1] < 0:
            result.append({**players[j-1], "assigned_role": slots[matched[j]-1]})
    return sorted(result, key=lambda p: (list(QUOTAS).index(p["assigned_role"]), -p["current_ovr"], p["player_id"]))


def build_squads(records, sixty_league="Spark"):
    pools = {league: [] for league in LEAGUES}
    excluded, seen = [], set()
    for row in records:
        row = dict(row)
        try:
            pid = int(row["player_id"])
        except (KeyError, TypeError, ValueError):
            excluded.append({**row, "reason": "Missing player ID"})
            continue
        if pid in seen:
            continue
        seen.add(pid)
        league = league_for(row.get("current_ovr"), sixty_league)
        groups = position_groups(row.get("position"))
        if league is None or not groups:
            excluded.append({**row, "reason": "Missing rating" if league is None else "Unknown position"})
            continue
        pools[league].append({**row, "player_id": pid, "current_ovr": float(row["current_ovr"]), "groups": groups})
    result = {}
    for league, pool in pools.items():
        pool.sort(key=lambda p: (-p["current_ovr"], p["player_id"]))
        squads = []
        while pool:
            selected = _assign(pool)
            if not selected:
                break
            counts = {role: sum(p["assigned_role"] == role for p in selected) for role in QUOTAS}
            squads.append({"players": selected, "shortages": {role: count-counts[role] for role, count in QUOTAS.items() if counts[role] < count}})
            used = {p["player_id"] for p in selected}
            pool = [p for p in pool if p["player_id"] not in used]
        result[league] = squads
    return result, excluded
