import pandas as pd
import agency_backend as agency

MFL_WALLET = "0xff8d2bbed8164db0"
AGE_MIN = 16
AGE_MAX = 28
AGE_WEIGHT = 0.5

# Current MFL rarity bands. Ultimate is progression-only and therefore not a mint/pack tier.
RARITIES = {
    "Common": (32, 54),
    "Limited": (55, 64),
    "Uncommon": (65, 74),
    "Rare": (75, 84),
    "Legendary": (85, 94),
}

def _player_id(p):
    if p.get("id") is not None:
        return int(p["id"])
    meta = p.get("metadata") or {}
    if meta.get("id") is not None:
        return int(meta["id"])
    return None

def _to_row(p):
    m = p.get("metadata") or {}
    pid = _player_id(p)
    positions = m.get("positions") or []
    if isinstance(positions, str):
        positions = [positions]
    nationalities = m.get("nationalities") or []
    if isinstance(nationalities, str):
        nationalities = [nationalities]
    first = str(m.get("firstName") or "").strip()
    last = str(m.get("lastName") or "").strip()
    name = (first + " " + last).strip() or f"Player {pid}"
    age = m.get("age")
    overall = m.get("overall")
    try:
        age = int(age)
    except Exception:
        age = None
    try:
        overall = int(overall)
    except Exception:
        overall = None
    return {
        "player_id": pid,
        "player": name,
        "overall": overall,
        "age": age,
        "positions": " / ".join(str(x) for x in positions),
        "nationality": ", ".join(str(x).replace("_", " ").title() for x in nationalities),
        "pace": m.get("pace"),
        "shooting": m.get("shooting"),
        "passing": m.get("passing"),
        "dribbling": m.get("dribbling"),
        "defense": m.get("defense"),
        "physical": m.get("physical"),
        "goalkeeping": m.get("goalkeeping"),
    }

def pull_score(overall, age):
    """Age-adjusted pack value heuristic. Not an official MFL metric."""
    if overall is None:
        return None
    if age is None:
        return float(overall)
    age = max(AGE_MIN, min(AGE_MAX, int(age)))
    return round(float(overall) + (AGE_MAX - age) * AGE_WEIGHT, 2)

def fetch_rarity_pool(rarity):
    if rarity not in RARITIES:
        raise ValueError(f"Unknown rarity: {rarity}")
    lo, hi = RARITIES[rarity]
    token = agency.token()
    rows = []
    before = None
    seen = set()

    for _ in range(100):
        params = {
            "limit": 1500,
            "ownerWalletAddress": MFL_WALLET,
            "overallMin": lo,
            "overallMax": hi,
        }
        if before is not None:
            params["beforePlayerId"] = before

        payload = agency.get("/players", token, params)
        batch = agency.arr(payload)
        if not batch:
            break

        new_count = 0
        last_id = None
        for p in batch:
            pid = _player_id(p)
            if pid is None:
                continue
            last_id = pid
            if pid in seen:
                continue
            seen.add(pid)
            row = _to_row(p)
            if row["overall"] is not None and lo <= row["overall"] <= hi:
                rows.append(row)
                new_count += 1

        if len(batch) < 1500 or last_id is None or new_count == 0:
            break
        if before == last_id:
            break
        before = last_id

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates("player_id").copy()
    df["pull_score"] = [pull_score(o, a) for o, a in zip(df["overall"], df["age"])]
    df = df.sort_values(["pull_score", "overall", "age"], ascending=[False, False, True]).reset_index(drop=True)
    n = len(df)
    df["rank"] = range(1, n + 1)
    if n > 1:
        df["percentile"] = 1 - ((df["rank"] - 1) / (n - 1))
    else:
        df["percentile"] = 1.0

    def label(p):
        if p >= 0.95:
            return "Jackpot"
        if p >= 0.80:
            return "Excellent"
        if p >= 0.55:
            return "Good"
        if p >= 0.20:
            return "Average"
        return "Poor"

    df["pull_label"] = df["percentile"].map(label)
    return df

def portrait_url(player_id):
    return f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(player_id)}/photo.webp"
