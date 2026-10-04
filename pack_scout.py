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
            "ageMin": AGE_MIN,
            "ageMax": AGE_MAX,
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
            if (
                row["overall"] is not None
                and lo <= row["overall"] <= hi
                and row["age"] is not None
                and AGE_MIN <= row["age"] <= AGE_MAX
            ):
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
    # Defensive local filter: Pack Scout must NEVER include non-packable ages.
    df = df[df["age"].between(AGE_MIN, AGE_MAX, inclusive="both")].copy()
    if df.empty:
        return df
    df["age_bonus"] = [
        round(max(0, (AGE_MAX - max(AGE_MIN, min(AGE_MAX, int(a))))) * AGE_WEIGHT, 2)
        if pd.notna(a) else 0.0
        for a in df["age"]
    ]
    df["pull_score"] = [pull_score(o, a) for o, a in zip(df["overall"], df["age"])]
    df["ovr_band_pct"] = ((df["overall"] - lo) / max(hi - lo, 1)).clip(0, 1)
    df["prospect"] = df["age"].fillna(99).le(20)
    df = df.sort_values(["pull_score", "overall", "age"], ascending=[False, False, True]).reset_index(drop=True)
    n = len(df)
    df["rank"] = range(1, n + 1)
    if n > 1:
        df["percentile"] = 1 - ((df["rank"] - 1) / (n - 1))
    else:
        df["percentile"] = 1.0

    def label(p):
        # Make the top labels genuinely special within the live rarity pool.
        if p >= 0.98:
            return "Jackpot"
        if p >= 0.90:
            return "Excellent"
        if p >= 0.65:
            return "Good"
        if p >= 0.25:
            return "Average"
        return "Poor"

    df["pull_label"] = df["percentile"].map(label)

    # Estimated per-player chance assuming every currently packable player
    # in the selected rarity is equally likely. This is NOT an official MFL
    # pack probability unless MFL confirms the draw is uniformly random.
    pool_size = len(df)
    df["estimated_pull_chance_pct"] = round(100.0 / pool_size, 6) if pool_size else 0.0
    df["estimated_one_in"] = pool_size
    return df

def portrait_url(player_id):
    return f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(player_id)}/photo.webp"


def pull_reason(row):
    """Short human-readable explanation for a player's Pack Scout rank."""
    try:
        age = int(row["age"])
    except Exception:
        age = None
    try:
        overall = int(row["overall"])
    except Exception:
        overall = None
    bonus = float(row.get("age_bonus", 0) or 0)

    if age is None or overall is None:
        return "Ranked from the available player data"

    if age <= 18 and bonus >= 5:
        return f"Elite age value: only {age}, adding +{bonus:.1f} to the Scout Score"
    if age <= 20 and bonus >= 4:
        return f"High-upside prospect: age {age} adds +{bonus:.1f} to the Scout Score"
    if age <= 23:
        return f"Good age profile: age {age} adds +{bonus:.1f} while keeping current OVR important"
    if age >= 27:
        return f"Current quality matters most here: age {age} gives only +{bonus:.1f} age premium"
    return f"Balanced profile: {overall} OVR with a +{bonus:.1f} age premium"

def top_attributes(row, limit=3):
    labels = [
        ("PAC", row.get("pace")),
        ("SHO", row.get("shooting")),
        ("PAS", row.get("passing")),
        ("DRI", row.get("dribbling")),
        ("DEF", row.get("defense")),
        ("PHY", row.get("physical")),
    ]
    if "GK" in str(row.get("positions") or ""):
        labels.append(("GK", row.get("goalkeeping")))
    vals=[]
    for lab,val in labels:
        try:
            vals.append((lab, int(val)))
        except Exception:
            continue
    vals.sort(key=lambda x:x[1], reverse=True)
    return vals[:limit]
