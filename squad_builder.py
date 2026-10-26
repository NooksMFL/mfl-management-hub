"""Deterministic, position-aware squad selection without API requests."""
import math
import re

LEAGUES = ("Stone", "Ice", "Spark", "Flint")
QUOTAS = {"Goalkeeper": 2, "LB": 2, "CB": 4, "RB": 2, "CDM": 2, "CM": 3, "Winger": 4, "Additional outfield": 6}
POSITIONS = {
    "Goalkeeper": {"GK"},
    "LB": {"LB", "LWB"},
    "CB": {"CB", "SW"},
    "RB": {"RB", "RWB"},
    "CDM": {"DM", "CDM", "LDM", "RDM"},
    "CM": {"CM", "LCM", "RCM"},
    "Winger": {"LW", "RW", "LM", "RM", "LF", "RF"},
    "Additional outfield": {"LB", "LWB", "CB", "SW", "RB", "RWB", "DM", "CDM", "LDM", "RDM",
                            "CM", "LCM", "RCM", "LW", "RW", "LM", "RM", "LF", "RF", "ST", "CF", "SS", "AM", "CAM"},
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


def has_current_club(value):
    return isinstance(value, str) and value.strip().lower() not in {
        "", "none", "null", "nan", "n/a", "no club", "retired", "-", "—"
    }


def role_rating(player,role):
    from tactics_engine import rating_at
    values=[rating_at(player,p)[0] for p in POSITIONS[role]]
    return max((v for v in values if v is not None),default=None)


def _assign(players, quotas=None):
    """Maximum-weight assignment to 25 role slots, with dummy empty slots.

    Hungarian assignment prioritises mandatory positions, then squad size and OVR. Unlike a
    greedy selection, a versatile player cannot displace the only specialist
    needed for another role.
    """
    slots = [role for role, count in (QUOTAS if quotas is None else quotas).items() for _ in range(count)]
    n, m = len(slots), len(players) + len(slots)
    role_values={(i,role):role_rating(p,role) for i,p in enumerate(players) for role in set(slots)}
    costs = []
    for role in slots:
        costs.append([
            -((100000 if role == "Additional outfield" else 10000000) + role_values[i,role]) if role in p["groups"] and role_values[i,role] is not None else 1000000
            for i,p in enumerate(players)
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
            result.append({**players[j-1], "assigned_role": slots[matched[j]-1], "assigned_role_rating":role_values[j-1,slots[matched[j]-1]]})
    return sorted(result, key=lambda p: (list(QUOTAS).index(p["assigned_role"]), -p["current_ovr"], p["player_id"]))


def build_squads(records, sixty_league="Spark"):
    pools = {league: [] for league in LEAGUES}
    excluded, seen = [], set()
    keepers = []
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
        if not has_current_club(row.get("club")):
            excluded.append({**row, "reason": "Retired / no current club"})
            continue
        league = league_for(row.get("current_ovr"), sixty_league)
        groups = position_groups(row.get("position"))
        if league is None or not groups:
            excluded.append({**row, "reason": "Missing rating" if league is None else "Unknown position"})
            continue
        candidate = {**row, "player_id": pid, "current_ovr": float(row["current_ovr"]), "groups": groups}
        if "Goalkeeper" in groups:
            keepers.append(candidate)
        else:
            pools[league].append(candidate)
    result = {}
    for league, pool in pools.items():
        pool.sort(key=lambda p: (-p["current_ovr"], p["player_id"]))
        squads = []
        while pool:
            selected = _assign(pool, {role: count for role, count in QUOTAS.items() if role != "Goalkeeper"})
            if not selected:
                break
            counts = {role: sum(p["assigned_role"] == role for p in selected) for role in QUOTAS}
            squads.append({"players": selected, "shortages": {role: count-counts[role] for role, count in QUOTAS.items() if counts[role] < count}})
            used = {p["player_id"] for p in selected}
            pool = [p for p in pool if p["player_id"] not in used]
        result[league] = squads
    # Fill a starting keeper for every squad before allocating backups. Keepers
    # can cross rating bands; prefer the closest band, then the stronger player.
    bands = {"Stone": (73, float("inf")), "Ice": (67, 72),
             "Spark": (60 if sixty_league == "Spark" else 61, 66),
             "Flint": (0, 59 if sixty_league == "Spark" else 60)}
    for _ in range(2):
        for league, squads in result.items():
            low, high = bands[league]
            for squad in squads:
                if not keepers:
                    continue
                keeper = min(keepers, key=lambda p: (
                    max(low-p["current_ovr"], 0, p["current_ovr"]-high),
                    -p["current_ovr"], p["player_id"]))
                squad["players"].insert(0, {**keeper, "assigned_role": "Goalkeeper", "assigned_role_rating": role_rating(keeper,"Goalkeeper")})
                keepers.remove(keeper)
    for squads in result.values():
        for squad in squads:
            squad["players"].sort(key=lambda p: (list(QUOTAS).index(p["assigned_role"]), -p["current_ovr"], p["player_id"]))
            counts = {role: sum(p["assigned_role"] == role for p in squad["players"]) for role in QUOTAS}
            squad["shortages"] = {role: count-counts[role] for role, count in QUOTAS.items() if counts[role] < count}
    excluded.extend({**p, "reason": "Surplus goalkeeper — two per squad"} for p in keepers)
    return result, excluded
