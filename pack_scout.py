import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import agency_backend as agency

MFL_WALLET = "0xff8d2bbed8164db0"
AGE_MIN = 16
AGE_MAX = 28
AGE_WEIGHT = 0.5

# Observed on player 164286: the most recent global NEW_AGE rollover.
# A player already owned by MFL before this timestamp had an opportunity to age.
FALLBACK_AGE_ROLLOVER_MS = 1789383117448
ROLLOVER_SENTINEL_PLAYER_ID = 164286
CACHE_DB = os.getenv("PACK_SCOUT_DB", "pack_scout_cache.db")
AUTO_VERIFY_LIMIT = 24
VERIFY_WORKERS = 6

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
        "owned_since": (
            p.get("ownedSince")
            or p.get("ownershipDate")
            or ((p.get("ownedBy") or {}).get("since") if isinstance(p.get("ownedBy"), dict) else None)
        ),
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

    # Verify incrementally and cache results. This avoids the old N+1 request
    # problem while permanently excluding players proven to have aged in MFL custody.
    df = _apply_history_verification(df, token, verify_limit=AUTO_VERIFY_LIMIT)
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



def _cache_conn():
    con = sqlite3.connect(CACHE_DB, timeout=20)
    con.execute("""
        CREATE TABLE IF NOT EXISTS pack_history_cache(
            player_id INTEGER PRIMARY KEY,
            owned_since INTEGER,
            status TEXT NOT NULL,
            latest_new_age INTEGER,
            checked_rollover INTEGER NOT NULL
        )
    """)
    con.commit()
    return con

def _history_events(player_id, token):
    """Fetch the actual player experience/history feed used by MFL player history."""
    payload = agency.get(f"/players/{int(player_id)}/experiences/history", token)
    return agency.arr(payload)

def _latest_rollover(token):
    """Derive the current global age-rollover marker from a known ageing player."""
    try:
        events = _history_events(ROLLOVER_SENTINEL_PLAYER_ID, token)
        dates = []
        for e in events:
            if str(e.get("reasonType") or "").upper() == "NEW_AGE":
                try:
                    dates.append(int(e.get("date")))
                except Exception:
                    pass
        if dates:
            return max(dates)
    except Exception:
        pass
    return FALLBACK_AGE_ROLLOVER_MS

def _classify_from_history(row, token, rollover_ms):
    """
    VERIFIED_FROZEN: MFL owned the player before the latest known rollover and
    no NEW_AGE happened after acquisition.
    AGED: at least one NEW_AGE happened while MFL owned the player.
    TOO_NEW: MFL acquired the player after the latest known rollover, so there
    has not yet been a rollover with which to test freezing.
    """
    try:
        pid = int(row["player_id"])
        owned_ms = int(row["owned_since"])
    except Exception:
        return "UNKNOWN", None

    if owned_ms > rollover_ms:
        return "TOO_NEW", None

    events = _history_events(pid, token)
    latest = None
    for e in events:
        if str(e.get("reasonType") or "").upper() != "NEW_AGE":
            continue
        try:
            event_ms = int(e.get("date"))
        except Exception:
            continue
        if latest is None or event_ms > latest:
            latest = event_ms
        if event_ms >= owned_ms:
            return "AGED", latest

    return "VERIFIED_FROZEN", latest

def _read_cached_statuses(player_ids):
    if not player_ids:
        return {}
    con = _cache_conn()
    try:
        qmarks = ",".join("?" for _ in player_ids)
        rows = con.execute(
            f"SELECT player_id, owned_since, status, latest_new_age, checked_rollover "
            f"FROM pack_history_cache WHERE player_id IN ({qmarks})",
            [int(x) for x in player_ids]
        ).fetchall()
        return {
            int(r[0]): {
                "owned_since": r[1],
                "status": r[2],
                "latest_new_age": r[3],
                "checked_rollover": r[4],
            }
            for r in rows
        }
    finally:
        con.close()

def _write_cache(results):
    if not results:
        return
    con = _cache_conn()
    try:
        con.executemany("""
            INSERT INTO pack_history_cache(player_id, owned_since, status, latest_new_age, checked_rollover)
            VALUES(?,?,?,?,?)
            ON CONFLICT(player_id) DO UPDATE SET
                owned_since=excluded.owned_since,
                status=excluded.status,
                latest_new_age=excluded.latest_new_age,
                checked_rollover=excluded.checked_rollover
        """, results)
        con.commit()
    finally:
        con.close()

def _apply_history_verification(df, token, verify_limit=AUTO_VERIFY_LIMIT):
    """
    Incrementally verify the pool without stalling Streamlit.

    Historical results are cached in SQLite. AGED players never need another
    history request for this ownership spell. VERIFIED_FROZEN players are reused
    until the known rollover marker changes. Unknown pre-rollover players are
    checked in a small concurrent batch on each load.
    """
    if df.empty:
        return df

    rollover_ms = _latest_rollover(token)
    ids = [int(x) for x in df["player_id"].tolist()]
    cached = _read_cached_statuses(ids)

    # Cache entries are reusable only if they refer to the same ownership spell
    # and were checked against the current rollover marker.
    statuses = {}
    pending = []
    for _, row in df.iterrows():
        pid = int(row["player_id"])
        try:
            owned_ms = int(row["owned_since"])
        except Exception:
            statuses[pid] = "UNKNOWN"
            continue

        if owned_ms > rollover_ms:
            statuses[pid] = "TOO_NEW"
            continue

        hit = cached.get(pid)
        if (
            hit
            and hit.get("owned_since") == owned_ms
            and int(hit.get("checked_rollover") or 0) == rollover_ms
        ):
            statuses[pid] = hit["status"]
        else:
            pending.append(row)

    # Oldest ownership first: this quickly removes legacy MFL stock.
    pending.sort(key=lambda r: int(r.get("owned_since") or 0))
    pending = pending[:max(0, int(verify_limit or 0))]

    writes = []
    if pending:
        with ThreadPoolExecutor(max_workers=VERIFY_WORKERS) as ex:
            futures = {ex.submit(_classify_from_history, row, token, rollover_ms): row for row in pending}
            for fut in as_completed(futures):
                row = futures[fut]
                pid = int(row["player_id"])
                try:
                    owned_ms = int(row["owned_since"])
                    status, latest = fut.result()
                except Exception:
                    status, latest = "UNKNOWN", None
                    owned_ms = int(row.get("owned_since") or 0)
                statuses[pid] = status
                if status in ("AGED", "VERIFIED_FROZEN", "TOO_NEW"):
                    writes.append((pid, owned_ms, status, latest, rollover_ms))
    _write_cache(writes)

    out = df.copy()
    out["verification_status"] = out["player_id"].map(
        lambda x: statuses.get(int(x), "PENDING")
    )

    # Proven ageing while MFL-owned is a hard exclusion.
    out = out[out["verification_status"] != "AGED"].copy()
    out["packable_candidate"] = True
    out["verification_rollover"] = rollover_ms
    out["packable_reason"] = out["verification_status"].map({
        "VERIFIED_FROZEN": "Verified frozen across latest rollover",
        "TOO_NEW": "Acquired after latest rollover; not yet testable",
        "PENDING": "Awaiting cached history verification",
        "UNKNOWN": "History/ownership could not yet be verified",
    }).fillna("Candidate")
    return out
