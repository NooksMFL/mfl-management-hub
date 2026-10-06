import math
import os
import time
import requests

AUTH_BASE = "https://api.playmfl.com"
COMMON_HEADERS = {
    "Accept": "*/*",
    "Origin": "https://app.playmfl.com",
    "Referer": "https://app.playmfl.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0"
    ),
}

PLAYERS_URL = "https://api.playmfl.com/players"
LISTINGS_URL = "https://api.playmfl.com/listings"
TIER_BREAK_OVRS = {55, 65, 75, 85, 95}

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


def _access_token():
    refresh_token = os.getenv("MFL_REFRESH_TOKEN")
    if not refresh_token:
        raise RuntimeError("MFL_REFRESH_TOKEN is missing from Streamlit Secrets.")

    last_error = None
    for attempt in range(4):
        try:
            response = requests.post(
                AUTH_BASE + "/auth/refresh",
                headers=COMMON_HEADERS,
                json={"refreshToken": refresh_token},
                timeout=20,
            )
            if response.status_code in (429, 500, 502, 503, 504):
                last_error = f"HTTP {response.status_code}"
                time.sleep(min(10, 2 ** attempt))
                continue
            if response.status_code == 403:
                raise RuntimeError(
                    "MFL rejected the refresh token (HTTP 403). "
                    "Replace MFL_REFRESH_TOKEN in this Streamlit app's Secrets with the current token used by your working MFL app."
                )
            response.raise_for_status()
            payload = response.json()
            access = payload.get("access")
            if access is None and isinstance(payload.get("data"), dict):
                access = payload["data"].get("access")
            if isinstance(access, dict):
                access = access.get("token")
            if not access:
                raise RuntimeError("MFL did not return an access token.")
            return access
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = str(exc)
            time.sleep(min(10, 2 ** attempt))

    raise RuntimeError(f"MFL authentication failed: {last_error}")


def _headers():
    headers = dict(COMMON_HEADERS)
    headers["Authorization"] = "Bearer " + _access_token()
    return headers


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


def analyse_listing(listing):
    if not isinstance(listing, dict):
        return None

    player = listing.get("player")
    if not isinstance(player, dict):
        return None

    metadata = player.get("metadata") if isinstance(player.get("metadata"), dict) else {}
    positions = metadata.get("positions") or []
    primary = positions[0] if positions else None
    current_ovr = int(metadata.get("overall") or 0)
    if current_ovr <= 0:
        return None

    next_ovr = current_ovr + 1
    raw = raw_ovr(metadata, primary)
    if raw is None:
        return None

    threshold = float(next_ovr) - 0.5
    gap = max(0.0, threshold - raw)
    min_points, route, options = _minimum_route(metadata, primary, threshold)
    one_point = _one_point_breaks(metadata, primary, threshold)

    tier_break = next_ovr in TIER_BREAK_OVRS

    if gap <= 0:
        closeness = "Already over threshold"
    elif one_point:
        closeness = "🔥 1 stat gain away"
    elif min_points == 2:
        closeness = "🟢 2 gains away"
    elif min_points == 3:
        closeness = "🟡 3 gains away"
    else:
        closeness = "⚪ Further away"

    if tier_break and one_point:
        opportunity = "🚨 TIER BREAK +1 AWAY"
    elif tier_break and min_points is not None and min_points <= 2:
        opportunity = "🔥 Near tier break"
    elif one_point:
        opportunity = "⚡ +1 OVR close"
    elif min_points is not None and min_points <= 2:
        opportunity = "🟢 Near +1 OVR"
    else:
        opportunity = ""

    contract = player.get("activeContract") if isinstance(player.get("activeContract"), dict) else {}
    club = contract.get("club") if isinstance(contract.get("club"), dict) else {}
    owner = player.get("ownedBy") if isinstance(player.get("ownedBy"), dict) else {}

    price = listing.get("price")
    try:
        price = float(price) if price is not None else None
    except (TypeError, ValueError):
        price = None

    return {
        "listing_id": listing.get("listingResourceId") or listing.get("id"),
        "id": player.get("id"),
        "name": (str(metadata.get("firstName") or "") + " " + str(metadata.get("lastName") or "")).strip(),
        "age": metadata.get("age"),
        "position": primary,
        "positions": ", ".join(positions),
        "overall": current_ovr,
        "next_ovr": next_ovr,
        "raw_ovr": round(raw, 3),
        "gap": round(gap, 3),
        "min_points": min_points,
        "best_route": route,
        "one_point_stats": ", ".join(one_point),
        "tier_break": tier_break,
        "opportunity": opportunity,
        "closeness": closeness,
        "price": price,
        "owner": owner.get("name") or "",
        "club": club.get("name") or "Free Agent",
        "PAC": metadata.get("pace"),
        "SHO": metadata.get("shooting"),
        "PAS": metadata.get("passing"),
        "DRI": metadata.get("dribbling"),
        "DEF": metadata.get("defense"),
        "PHY": metadata.get("physical"),
        "GK": metadata.get("goalkeeping"),
        "mfl_url": f"https://app.playmfl.com/players/{player.get('id')}",
    }


def fetch_transfer_listings(
    age_min=16,
    age_max=28,
    overall_min=45,
    overall_max=94,
    price_min=None,
    price_max=None,
    positions=None,
    max_pages=20,
):
    params = {
        "limit": 25,
        "type": "PLAYER",
        "status": "AVAILABLE",
        "view": "full",
        "sorts": "metadata.overall",
        "sortsOrders": "DESC",
        "ageMin": age_min,
        "ageMax": age_max,
        "overallMin": overall_min,
        "overallMax": overall_max,
    }
    if price_min is not None:
        params["priceMin"] = price_min
    if price_max is not None:
        params["priceMax"] = price_max
    if positions:
        params["positions"] = ",".join(positions)

    headers = _headers()
    listings = []
    seen = set()
    before_id = None

    for _ in range(max_pages):
        call_params = dict(params)
        if before_id is not None:
            call_params["beforeListingId"] = before_id

        response = None
        for attempt in range(6):
            try:
                response = requests.get(
                    LISTINGS_URL,
                    headers=headers,
                    params=call_params,
                    timeout=30,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait_seconds = float(retry_after) if retry_after else min(45, 4 * (2 ** attempt))
                    except (TypeError, ValueError):
                        wait_seconds = min(45, 4 * (2 ** attempt))
                    time.sleep(wait_seconds)
                    continue

                if response.status_code in (500, 502, 503, 504):
                    time.sleep(min(20, 2 * (2 ** attempt)))
                    continue

                response.raise_for_status()
                break

            except (requests.Timeout, requests.ConnectionError):
                if attempt == 5:
                    raise
                time.sleep(min(20, 2 * (2 ** attempt)))
        else:
            raise RuntimeError("MFL listings API remained rate-limited after several retries.")

        if response is None or response.status_code == 429:
            raise RuntimeError("MFL listings API is temporarily rate-limiting requests. Please try the scan again shortly.")

        rows = response.json()
        if not isinstance(rows, list) or not rows:
            break

        new_count = 0
        for row in rows:
            listing_id = row.get("listingResourceId") or row.get("id")
            if listing_id in seen:
                continue
            seen.add(listing_id)
            listings.append(row)
            new_count += 1

        if len(rows) < 25 or new_count == 0:
            break

        before_id = rows[-1].get("listingResourceId") or rows[-1].get("id")
        if before_id is None:
            break

        # Be deliberately gentle with the live marketplace API.
        time.sleep(1.25)

    return listings


def scan_transfer_market(
    age_min=16,
    age_max=28,
    overall_min=45,
    overall_max=94,
    price_min=None,
    price_max=None,
    positions=None,
    max_pages=20,
):
    listings = fetch_transfer_listings(
        age_min=age_min,
        age_max=age_max,
        overall_min=overall_min,
        overall_max=overall_max,
        price_min=price_min,
        price_max=price_max,
        positions=positions,
        max_pages=max_pages,
    )

    rows = []
    for listing in listings:
        row = analyse_listing(listing)
        if row is not None:
            rows.append(row)

    rows.sort(
        key=lambda r: (
            0 if r["tier_break"] and r["one_point_stats"] else
            1 if r["tier_break"] else
            2 if r["one_point_stats"] else
            3,
            999 if r["min_points"] is None else r["min_points"],
            r["gap"],
            r["price"] if r["price"] is not None else float("inf"),
            r["age"] if r["age"] is not None else 999,
        )
    )
    return rows


def fetch_wallet_players(wallet, limit=100, max_pages=20):
    wallet = (wallet or "").strip().lower()
    if not wallet:
        return []

    headers = _headers()
    players = []
    seen = set()
    before_id = None

    for _ in range(max_pages):
        params = {
            "limit": limit,
            "ownerWalletAddress": wallet,
        }
        if before_id is not None:
            params["beforePlayerId"] = before_id

        response = None
        for attempt in range(5):
            response = requests.get(
                PLAYERS_URL,
                headers=headers,
                params=params,
                timeout=30,
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    wait_seconds = float(retry_after) if retry_after else min(30, 3 * (2 ** attempt))
                except (TypeError, ValueError):
                    wait_seconds = min(30, 3 * (2 ** attempt))
                time.sleep(wait_seconds)
                continue
            if response.status_code in (500, 502, 503, 504):
                time.sleep(min(15, 2 * (2 ** attempt)))
                continue
            response.raise_for_status()
            break

        if response is None or response.status_code == 429:
            raise RuntimeError("MFL players API is temporarily rate-limiting the wallet scan.")

        rows = response.json()
        if not isinstance(rows, list) or not rows:
            break

        new_count = 0
        for row in rows:
            pid = row.get("id") if isinstance(row, dict) else None
            if pid in seen:
                continue
            seen.add(pid)
            players.append(row)
            new_count += 1

        if len(rows) < limit or new_count == 0:
            break

        before_id = rows[-1].get("id")
        if before_id is None:
            break
        time.sleep(0.8)

    return players


def fetch_wallet_listings(wallet, max_pages=12):
    """
    The public MFL /listings endpoint does not accept sellerAddress as a filter.
    Do not crawl the full marketplace just to price one wallet's squad, as that
    quickly triggers 429s. Agency scans therefore prioritise development/tier
    analysis and leave listing price blank until a wallet-specific listing
    source is available.
    """
    return {}

def analyse_wallet_player(player, listing=None):
    if not isinstance(player, dict):
        return None
    metadata = player.get("metadata") if isinstance(player.get("metadata"), dict) else {}
    positions = metadata.get("positions") or []
    primary = positions[0] if positions else None
    current_ovr = int(metadata.get("overall") or 0)
    if current_ovr <= 0:
        return None

    raw = raw_ovr(metadata, primary)
    if raw is None:
        return None

    next_ovr = current_ovr + 1
    threshold = float(next_ovr) - 0.5
    gap = max(0.0, threshold - raw)
    min_points, route, _ = _minimum_route(metadata, primary, threshold)
    one_point = _one_point_breaks(metadata, primary, threshold)
    tier_break = next_ovr in TIER_BREAK_OVRS

    if tier_break and one_point:
        signal = "🚨 TIER BREAK +1 AWAY"
    elif tier_break and min_points is not None and min_points <= 2:
        signal = "🔥 Near tier break"
    elif one_point:
        signal = "⚡ +1 OVR close"
    elif min_points is not None and min_points <= 2:
        signal = "🟢 Near +1 OVR"
    else:
        signal = ""

    contract = player.get("activeContract") if isinstance(player.get("activeContract"), dict) else {}
    club = contract.get("club") if isinstance(contract.get("club"), dict) else {}

    return {
        "id": player.get("id"),
        "name": (str(metadata.get("firstName") or "") + " " + str(metadata.get("lastName") or "")).strip(),
        "age": metadata.get("age"),
        "position": primary,
        "positions": ", ".join(positions),
        "overall": current_ovr,
        "next_ovr": next_ovr,
        "raw_ovr": round(raw, 3),
        "gap": round(gap, 3),
        "min_points": min_points,
        "best_route": route,
        "one_point_stats": ", ".join(one_point),
        "tier_break": tier_break,
        "signal": signal,
        "price": listing.get("price") if isinstance(listing, dict) else None,
        "listed": isinstance(listing, dict),
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


def scan_agency(wallet, include_listings=True):
    players = fetch_wallet_players(wallet)
    listings = fetch_wallet_listings(wallet) if include_listings else {}

    rows = []
    for player in players:
        pid = player.get("id") if isinstance(player, dict) else None
        row = analyse_wallet_player(player, listings.get(pid))
        if row is not None:
            rows.append(row)

    rows.sort(
        key=lambda r: (
            0 if r["tier_break"] and r["one_point_stats"] else
            1 if r["tier_break"] else
            2 if r["one_point_stats"] else
            3,
            999 if r["min_points"] is None else r["min_points"],
            r["gap"],
            r["age"] if r["age"] is not None else 999,
        )
    )
    return rows
