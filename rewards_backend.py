import os
import re
import json
import base64
import requests
import wallet_cache_backend as shared

BASE = "https://api.playmfl.com"
HEADERS = {
    "Accept": "*/*",
    "Origin": "https://app.playmfl.com",
    "Referer": "https://app.playmfl.com/",
    "User-Agent": "Mozilla/5.0",
}

_AMOUNT = re.compile(r"([0-9]+(?:[.,][0-9]+)?)")


def _token():
    rt = os.getenv("MFL_REFRESH_TOKEN", "").strip()
    if not rt:
        raise RuntimeError("MFL_REFRESH_TOKEN missing")
    r = requests.post(BASE + "/auth/refresh", headers=HEADERS, json={"refreshToken": rt}, timeout=20)
    r.raise_for_status()
    data = r.json()
    access = data.get("access")
    if access is None and isinstance(data.get("data"), dict):
        access = data["data"].get("access")
    if isinstance(access, dict):
        access = access.get("token")
    if not access:
        raise RuntimeError("No access token returned")
    return access


def api_get(path, params=None):
    # Reuse the Management Hub's proven MFL authentication/request layer.
    # This keeps Rewards on the same browser headers, retries and token flow
    # as Agency/Club Development instead of maintaining a second auth path.
    token = shared.token()
    return shared._get(path, token, params=params, timeout=30)


def api_probe(path, params=None):
    token = shared.token()
    h = dict(shared.H)
    h["Authorization"] = "Bearer " + token
    try:
        r = requests.get(BASE + path, headers=h, params=params, timeout=20)
        payload = None
        try:
            payload = r.json()
        except Exception:
            payload = r.text[:1200]
        return {"path": path, "status": r.status_code, "payload": payload}
    except Exception as exc:
        return {"path": path, "status": None, "payload": str(exc)}


def as_list(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "results", "clubs", "players", "competitions"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                found = as_list(value)
                if found:
                    return found
    return []


def first(mapping, *keys):
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def deep_first(obj, key_names):
    wanted = {str(k).lower() for k in key_names}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in wanted and value not in (None, "", [], {}):
                if not isinstance(value, (dict, list)):
                    return value
            found = deep_first(value, key_names)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = deep_first(value, key_names)
            if found not in (None, ""):
                return found
    return None


def share(raw):
    value = to_float(raw)
    if value is None:
        return 0.0
    return value / 10000.0 if value > 100 else value / 100.0


def club_id(value):
    direct = to_int(value)
    if direct is not None:
        return direct
    if not isinstance(value, dict):
        return None
    for key in ("clubId", "club_id", "id"):
        direct = to_int(value.get(key))
        if direct is not None:
            return direct
    if isinstance(value.get("club"), dict):
        return club_id(value["club"])
    return None


def match_club_id(match, side):
    for key in (f"{side}ClubId", f"{side}_club_id", f"{side}Club", f"{side}_club", f"{side}Squad"):
        resolved = club_id(match.get(key))
        if resolved is not None:
            return resolved
    return None


def reward_amount(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("amount", "value", "reward", "prize"):
            amount = reward_amount(value.get(key))
            if amount is not None:
                return amount
        return None
    if value is None:
        return None
    match = _AMOUNT.search(str(value).replace(",", ""))
    return float(match.group(1)) if match else None


def reward_label(row):
    if not isinstance(row, dict):
        return str(row or "")
    return str(first(row, "ranks", "rank", "position", "label", "name") or "").strip()


def reward_value(row):
    if not isinstance(row, dict):
        return reward_amount(row)
    lines = row.get("lines")
    if isinstance(lines, list):
        for line in lines:
            amount = reward_amount(line)
            if amount is not None:
                return amount
    for key in ("reward", "prize", "value", "amount"):
        amount = reward_amount(row.get(key))
        if amount is not None:
            return amount
    return None


def rank_range(label):
    m = re.fullmatch(r"\s*(\d+)\s*(?:[-–—]\s*(\d+))?\s*", str(label or ""))
    return (int(m.group(1)), int(m.group(2) or m.group(1))) if m else None


def stages(detail):
    schedule = detail.get("schedule") if isinstance(detail, dict) else {}
    rows = schedule.get("stages") if isinstance(schedule, dict) else []
    return [x for x in rows if isinstance(x, dict)] if isinstance(rows, list) else []


def members(detail):
    ids = set()
    for stage in stages(detail):
        groups = stage.get("groups") or []
        for group in groups:
            if not isinstance(group, dict):
                continue
            for member in group.get("members") or []:
                cid = club_id(member)
                if cid is not None:
                    ids.add(cid)
        for owner in [stage] + [g for g in groups if isinstance(g, dict)]:
            for rnd in owner.get("rounds") or []:
                if not isinstance(rnd, dict):
                    continue
                for match in rnd.get("matches") or []:
                    if not isinstance(match, dict):
                        continue
                    for side in ("home", "away"):
                        cid = match_club_id(match, side)
                        if cid is not None:
                            ids.add(cid)
    return ids


def standing(detail, wanted):
    for stage in stages(detail):
        for group in stage.get("groups") or []:
            if not isinstance(group, dict):
                continue
            rows = None
            for key in ("standings", "ranking", "rankings", "table"):
                if isinstance(group.get(key), list):
                    rows = group[key]
                    break
            for index, row in enumerate(rows or [], 1):
                if not isinstance(row, dict):
                    continue
                rid = club_id(row.get("club")) or club_id(row.get("squad")) or club_id(first(row, "clubId", "club_id"))
                if rid == wanted:
                    return to_int(first(row, "position", "rank", "ranking")) or index
    return None


def calculated_league_standing(detail, wanted):
    table = {}

    def stats(cid):
        cid = to_int(cid)
        if cid is None:
            return None
        if cid not in table:
            table[cid] = {
                "club_id": cid,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals": 0,
                "goals_against": 0,
                "points": 0,
            }
        return table[cid]

    for stage in stages(detail):
        groups = stage.get("groups") or []
        owners = [stage] + [g for g in groups if isinstance(g, dict)]
        for owner in owners:
            for rnd in owner.get("rounds") or []:
                if not isinstance(rnd, dict):
                    continue
                for match in rnd.get("matches") or []:
                    if not isinstance(match, dict):
                        continue
                    status = str(match.get("status") or "").upper()
                    if status not in ("ENDED", "FINISHED", "FT", "FORFEITED"):
                        continue
                    hid = match_club_id(match, "home")
                    aid = match_club_id(match, "away")
                    hs = to_int(match.get("homeScore"))
                    aws = to_int(match.get("awayScore"))
                    if hid is None or aid is None or hs is None or aws is None:
                        continue

                    home = stats(hid)
                    away = stats(aid)
                    if home is None or away is None:
                        continue

                    home["goals"] += hs
                    home["goals_against"] += aws
                    away["goals"] += aws
                    away["goals_against"] += hs

                    if hs > aws:
                        home["wins"] += 1
                        away["losses"] += 1
                        home["points"] += 3
                    elif aws > hs:
                        away["wins"] += 1
                        home["losses"] += 1
                        away["points"] += 3
                    else:
                        home["draws"] += 1
                        away["draws"] += 1
                        home["points"] += 1
                        away["points"] += 1

    ordered = sorted(
        table.values(),
        key=lambda r: (
            -r["points"],
            -(r["goals"] - r["goals_against"]),
            -r["goals"],
            -r["wins"],
            r["club_id"],
        ),
    )
    for index, row in enumerate(ordered, start=1):
        if row["club_id"] == wanted:
            return index
    return None


def league_reward(detail, position):
    if position is None:
        return 0.0
    for row in detail.get("rewards") or []:
        rr = rank_range(reward_label(row))
        if rr and rr[0] <= position <= rr[1]:
            return reward_value(row) or 0.0
    return 0.0


def group_wins(detail, wanted):
    wins, seen = 0, set()
    for stage in stages(detail):
        for group in stage.get("groups") or []:
            if not isinstance(group, dict):
                continue
            for rnd in group.get("rounds") or []:
                if not isinstance(rnd, dict):
                    continue
                for match in rnd.get("matches") or []:
                    if not isinstance(match, dict):
                        continue
                    mid = first(match, "matchId", "id")
                    if mid in seen:
                        continue
                    seen.add(mid)
                    if str(match.get("status") or "").upper() not in ("ENDED", "FINISHED", "FT", "FORFEITED"):
                        continue
                    hs, aws = to_int(match.get("homeScore")), to_int(match.get("awayScore"))
                    if hs is None or aws is None:
                        continue
                    hid, aid = match_club_id(match, "home"), match_club_id(match, "away")
                    if (hid == wanted and hs > aws) or (aid == wanted and aws > hs):
                        wins += 1
    return wins


def group_win_value(detail):
    for row in detail.get("rewards") or []:
        text = (reward_label(row) + " " + str(row)).lower()
        if "group" in text and "win" in text:
            return reward_value(row) or 0.0
    return 0.0


def club_detail(cid):
    data = api_get(f"/clubs/{cid}")
    return data.get("data") if isinstance(data, dict) and isinstance(data.get("data"), dict) else data


def competition_detail(cid):
    data = api_get(f"/competitions/{cid}")
    return data.get("data") if isinstance(data, dict) and isinstance(data.get("data"), dict) else data


def competition_ids(club):
    found = []
    if not isinstance(club, dict):
        return found

    def add(value):
        cid = to_int(value)
        if cid is None and isinstance(value, dict):
            cid = to_int(first(value, "competitionId", "competitionID", "id"))
        if cid is not None and cid > 0:
            found.append(cid)

    for key in ("currentCompetitionIds", "competitionIds", "currentCompetitions",
                "competitions", "competitionMemberships", "competitionsMemberships"):
        value = club.get(key)
        if isinstance(value, list):
            for item in value:
                add(item)
        elif isinstance(value, dict):
            add(value)

    def walk(obj, parent_key=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                lk = str(key).lower()
                context = f"{parent_key}.{lk}" if parent_key else lk
                if "competition" in context:
                    if lk in ("competitionid", "competition_id", "id") and not isinstance(value, (dict, list)):
                        add(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, (dict, int, str)):
                                add(item)
                if isinstance(value, (dict, list)):
                    walk(value, context)
        elif isinstance(obj, list):
            for value in obj:
                if isinstance(value, (dict, list)):
                    walk(value, parent_key)

    walk(club)
    return sorted(set(found))




FLOW_SCRIPT_URL = "https://rest-mainnet.onflow.org/v1/scripts?block_height=sealed"
MFL_CLUB_ADDRESS = "0x8ebcbfd516b1da27"
_FLOW_CLUB_COMPETITIONS = {}

FLOW_CLUB_COMPETITIONS_SCRIPT = f"""
import MFLClub from {MFL_CLUB_ADDRESS}

access(all) struct ClubCompetitions {{
    access(all) let clubId: UInt64
    access(all) let competitionIds: [UInt64]

    init(clubId: UInt64, competitionIds: [UInt64]) {{
        self.clubId = clubId
        self.competitionIds = competitionIds
    }}
}}

access(all) fun main(clubIds: [UInt64]): [ClubCompetitions] {{
    let result: [ClubCompetitions] = []

    for clubId in clubIds {{
        let ids: [UInt64] = []

        if let clubData = MFLClub.getClubData(id: clubId) {{
            for squadId in clubData.getSquadIDs() {{
                if let squadData = MFLClub.getSquadData(id: squadId) {{
                    let memberships = squadData.getCompetitionsMemberships()
                    for competitionId in memberships.keys {{
                        ids.append(competitionId)
                    }}
                }}
            }}
        }}

        result.append(ClubCompetitions(clubId: clubId, competitionIds: ids))
    }}

    return result
}}
"""


def _flow_arg(argument):
    return base64.b64encode(
        json.dumps(argument, separators=(",", ":")).encode("utf-8")
    ).decode("utf-8")


def _cadence_decode(value):
    if not isinstance(value, dict):
        return value
    typ = value.get("type")
    raw = value.get("value")
    if typ == "Optional":
        return None if raw is None else _cadence_decode(raw)
    if typ in ("UInt", "UInt8", "UInt16", "UInt32", "UInt64", "UInt128", "UInt256",
               "Int", "Int8", "Int16", "Int32", "Int64", "Int128", "Int256"):
        return int(raw)
    if typ in ("UFix64", "Fix64"):
        return float(raw)
    if typ in ("String", "Address", "Character"):
        return str(raw)
    if typ == "Bool":
        return bool(raw)
    if typ in ("Array", "VariableSizedArray", "ConstantSizedArray"):
        return [_cadence_decode(x) for x in (raw or [])]
    if typ in ("Struct", "Resource", "Event"):
        fields = (raw or {}).get("fields") or []
        return {field.get("name"): _cadence_decode(field.get("value")) for field in fields}
    if typ == "Dictionary":
        out = {}
        for item in raw or []:
            out[_cadence_decode(item.get("key"))] = _cadence_decode(item.get("value"))
        return out
    return raw


def flow_competitions_for_clubs(club_ids):
    ids = sorted({int(x) for x in club_ids if to_int(x) is not None})
    missing = [cid for cid in ids if cid not in _FLOW_CLUB_COMPETITIONS]
    if missing:
        body = {
            "script": base64.b64encode(FLOW_CLUB_COMPETITIONS_SCRIPT.encode("utf-8")).decode("utf-8"),
            "arguments": [
                _flow_arg({
                    "type": "Array",
                    "value": [{"type": "UInt64", "value": str(cid)} for cid in missing],
                })
            ],
        }
        r = requests.post(
            FLOW_SCRIPT_URL,
            json=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "mfl-management-hub-rewards/1.0",
            },
            timeout=25,
        )
        r.raise_for_status()
        encoded = r.json()
        cadence_json = json.loads(base64.b64decode(encoded).decode("utf-8"))
        decoded = _cadence_decode(cadence_json)
        if isinstance(decoded, list):
            for row in decoded:
                if not isinstance(row, dict):
                    continue
                cid = to_int(row.get("clubId"))
                comps = row.get("competitionIds") if isinstance(row.get("competitionIds"), list) else []
                if cid is not None:
                    _FLOW_CLUB_COMPETITIONS[cid] = sorted({
                        int(x) for x in comps
                        if to_int(x) is not None and int(x) > 1000
                    })
        for cid in missing:
            _FLOW_CLUB_COMPETITIONS.setdefault(cid, [])
    return {cid: list(_FLOW_CLUB_COMPETITIONS.get(cid, [])) for cid in ids}


_STAFF_SHARE_CACHE = {}

def resolve_staff_share(relation):
    rid = to_int(relation.get("relationship_payload", {}).get("id"))
    cid = to_int(relation.get("id"))
    cache_key = (rid, cid)
    if cache_key in _STAFF_SHARE_CACHE:
        return _STAFF_SHARE_CACHE[cache_key]

    candidates = []
    if rid:
        candidates.extend([
            f"/staff/{rid}",
            f"/staff/{rid}/contract",
            f"/staff/{rid}/contracts",
            f"/contracts/{rid}",
            f"/staff/contracts/{rid}",
            f"/managerContracts/{rid}",
        ])
    if cid:
        candidates.extend([
            f"/clubs/{cid}/staff",
            f"/clubs/{cid}/contracts",
            f"/clubs/{cid}/managerContracts",
        ])

    for path in candidates:
        probe = api_probe(path)
        if probe.get("status") != 200:
            continue
        raw = deep_first(
            probe.get("payload"),
            ("revenueShare", "rewardShare", "revenue_share")
        )
        resolved = share(raw)
        if resolved > 0:
            _STAFF_SHARE_CACHE[cache_key] = resolved
            return resolved

    _STAFF_SHARE_CACHE[cache_key] = 0.0
    return 0.0


def discover_competition_ids_for_club(cid):
    try:
        direct = competition_ids(club_detail(cid))
    except Exception:
        direct = []
    direct = [int(x) for x in direct if to_int(x) is not None and int(x) > 1000]
    if direct:
        return direct
    return [int(x) for x in _FLOW_CLUB_COMPETITIONS.get(int(cid), []) if int(x) > 1000]


def project_club(cid, name="", club_payload=None):
    raw = club_detail(cid)
    ids = []
    if isinstance(club_payload, dict):
        ids.extend(competition_ids(club_payload))
    ids.extend(competition_ids(raw))
    ids = sorted({int(x) for x in ids if to_int(x) is not None and int(x) > 1000})
    if not ids:
        ids = discover_competition_ids_for_club(cid)
    gross, comps = 0.0, []
    for comp_id in ids:
        comp = competition_detail(comp_id)
        if not isinstance(comp, dict):
            continue
        pos = standing(comp, cid)
        if cid not in members(comp) and pos is None:
            continue
        ctype = str(comp.get("type") or "").upper()
        amount, note = 0.0, ""
        if ctype == "LEAGUE":
            if pos is None:
                pos = calculated_league_standing(comp, cid)
            amount = league_reward(comp, pos)
            note = f"Rank {pos}" if pos else "Rank unavailable"
        elif ctype == "CUP":
            wins = group_wins(comp, cid)
            amount = wins * group_win_value(comp)
            note = f"Group stage, {wins} wins"
        else:
            continue
        gross += amount
        comps.append({"Competition": str(comp.get("name") or comp_id), "Type": ctype, "Status": note, "Projected MFL": round(amount, 2)})
    return {"id": cid, "name": name or str(cid), "gross": gross, "competitions": comps}


def wallet_relationships(wallet):
    rows = as_list(api_get("/clubs", {"walletAddress": wallet}))
    owned, staff = [], []
    for row in rows:
        if not isinstance(row, dict):
            continue
        club = row.get("club") if isinstance(row.get("club"), dict) else row
        cid = to_int(first(club, "id", "clubId"))
        name = first(club, "name", "clubName")
        if cid is None or not name:
            continue
        revenue_raw = deep_first(row, ("revenueShare", "rewardShare", "revenue_share"))
        item = {
            "id": cid,
            "name": str(name),
            "share": share(revenue_raw),
            "club_payload": club,
            "relationship_payload": row,
        }
        (owned if str(row.get("title") or "").upper() == "MFL_OWNER" else staff).append(item)
    return owned, staff


def wallet_players(wallet):
    rows = as_list(api_get("/players", {"ownerWalletAddress": wallet, "limit": 500}))
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        contract = row.get("activeContract") if isinstance(row.get("activeContract"), dict) else {}
        club = contract.get("club") if isinstance(contract.get("club"), dict) else {}
        out.append({
            "id": first(row, "id", "playerId"),
            "name": (str(meta.get("firstName") or "") + " " + str(meta.get("lastName") or "")).strip(),
            "club_id": to_int(first(club, "id", "clubId")),
            "club_name": str(first(club, "name", "clubName") or ""),
            "share": share(contract.get("revenueShare")),
            "raw": row,
        })
    return out




def diagnostic_wallet_payload(wallet):
    rows = as_list(api_get("/clubs", {"walletAddress": wallet}))
    owned = None
    staff = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").upper()
        if title == "MFL_OWNER" and owned is None:
            owned = row
        elif title != "MFL_OWNER" and staff is None:
            staff = row
        if owned is not None and staff is not None:
            break

    players = wallet_players(wallet)
    loan_sample = next((p for p in players if p.get("club_id") and p.get("share", 0) > 0), None)

    probes = []
    if staff:
        sid = to_int(staff.get("id"))
        cid = to_int(first(staff.get("club") or {}, "id", "clubId"))
        candidates = []
        if sid:
            candidates += [
                f"/staff/{sid}",
                f"/staff/{sid}/contracts",
                f"/contracts/{sid}",
                f"/staff/contracts/{sid}",
                f"/managerContracts/{sid}",
            ]
        if cid:
            candidates += [
                f"/clubs/{cid}/staff",
                f"/clubs/{cid}/contracts",
                f"/clubs/{cid}/managerContracts",
            ]
        for path in candidates:
            probes.append(api_probe(path))

    return {
        "owned_sample": owned,
        "staff_sample": staff,
        "loan_player_sample": loan_sample.get("raw") if loan_sample else None,
        "staff_contract_probes": probes,
    }

def calculate(wallet):
    wallet = (wallet or "").strip().lower()
    owned, staff = wallet_relationships(wallet)
    players = wallet_players(wallet)
    owned_ids = {x["id"] for x in owned}

    club_rows = [project_club(c["id"], c["name"], c.get("relationship_payload")) for c in owned]
    club_gross = sum(x["gross"] for x in club_rows)

    staff_rows, staff_total = [], 0.0
    for rel in staff:
        if rel.get("share", 0) <= 0:
            rel["share"] = resolve_staff_share(rel)
        proj = project_club(rel["id"], rel["name"], rel.get("relationship_payload"))
        cut = proj["gross"] * rel["share"]
        staff_total += cut
        staff_rows.append({**rel, "gross": proj["gross"], "cut": cut, "competitions": proj["competitions"]})

    cache, loan_rows, loan_total = {}, [], 0.0
    external_club_ids = sorted({
        int(p["club_id"]) for p in players
        if p.get("club_id") is not None
        and p.get("club_id") not in owned_ids
        and p.get("share", 0) > 0
    })
    if external_club_ids:
        try:
            flow_competitions_for_clubs(external_club_ids)
        except Exception:
            # Keep the rest of the wallet calculation usable if Flow is temporarily unavailable.
            pass

    for p in players:
        cid = p["club_id"]
        if cid is None or cid in owned_ids or p["share"] <= 0:
            continue
        if cid not in cache:
            cache[cid] = project_club(cid, p["club_name"] or str(cid))
        gross = cache[cid]["gross"]
        cut = gross * p["share"]
        loan_total += cut
        loan_rows.append({**p, "gross": gross, "cut": cut})

    return {
        "owned": club_rows,
        "staff": staff_rows,
        "loans_out": loan_rows,
        "club_gross": club_gross,
        "staff_total": staff_total,
        "loan_total": loan_total,
        "known_total": club_gross + staff_total + loan_total,
        "owned_count": len(owned),
        "staff_count": len(staff_rows),
        "loan_count": len(loan_rows),
    }
