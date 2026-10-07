from __future__ import annotations
import time
import pandas as pd
import agency_backend as agency
import wallet_cache_backend as shared

SEASON = 17
MAX_APPS = 3

def _arr(d):
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in ("data","items","results","competitions","stats","playerCompetitions"):
            v=d.get(k)
            if isinstance(v,list): return v
            if isinstance(v,dict):
                a=_arr(v)
                if a:return a
    return []

def _first(obj, names):
    wanted={str(x).lower() for x in names}
    found=[]
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if str(k).lower() in wanted and v not in (None,"",[],{}):
                    found.append(v)
                walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(obj)
    for v in found:
        if isinstance(v,(str,int,float,bool)): return v
    return None

def _season(rec):
    # MFL competition records use a nested season object, e.g. season.name == "Season 17".
    # _first deliberately returns scalars only, so inspect season objects explicitly first.
    def walk(x):
        if isinstance(x,dict):
            season=x.get("season")
            if isinstance(season,dict):
                v=season.get("name") or season.get("number") or season.get("id")
                if v is not None:return v
            for k in ("seasonName","seasonNumber","seasonId","season_id"):
                if x.get(k) is not None:return x.get(k)
            for v in x.values():
                hit=walk(v)
                if hit is not None:return hit
        elif isinstance(x,list):
            for v in x:
                hit=walk(v)
                if hit is not None:return hit
        return None
    v=walk(rec)
    text=str(v or "")
    digits="".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None

def _apps(rec):
    # The working MFL competition payload calls this "matches" (older scanner:
    # Aspirants Cup 3 matches + Spark League 14 matches = 17 appearances).
    v=_first(rec,("matches","appearances","apps","gamesPlayed","matchesPlayed","played"))
    if v is None:
        raise ValueError("Competition record has no recognised appearance/match field")
    try:return int(float(v))
    except Exception as e:raise ValueError(f"Unrecognised appearance value: {v!r}") from e

def _competition_name(rec):
    v=_first(rec,("competitionName","competition","name","type","competitionType"))
    return str(v or "").strip()

def _is_official(rec):
    name=_competition_name(rec).upper()
    # Explicitly exclude non-competitive match buckets.
    blocked=("FRIENDLY","PRESEASON","PRE-SEASON","EXHIBITION")
    return not any(x in name for x in blocked)

def player_apps(pid, token):
    raw=agency.get(f"/players/{int(pid)}/competitions",token)
    rows=_arr(raw)
    season_rows=[r for r in rows if isinstance(r,dict) and _season(r)==SEASON and _is_official(r)]
    if not season_rows:
        seasons=sorted({x for x in (_season(r) for r in rows if isinstance(r,dict)) if x is not None})
        raise ValueError(f"No Season {SEASON} official competition records found; seasons returned={seasons}")
    return sum(_apps(r) for r in season_rows), season_rows

def _owned_names(wallet, token):
    clubs=shared.fetch_clubs(wallet,token,force=False)
    return {str(x.get("name") or "").strip().casefold():str(x.get("name") or "").strip() for x in clubs if x.get("name")}

def candidates(wallet, progress=None, delay=0.55):
    wallet=wallet.strip().lower()
    token=agency.token()
    # Refresh only when no cache exists; avoids wasting API calls during the 72h window.
    roster=shared.roster_rows(wallet)
    if not roster:
        shared.sync_wallet(wallet,True)
        roster=shared.roster_rows(wallet)
    owned=_owned_names(wallet,token)
    eligible=[]
    for r in roster:
        club=(r.get("club") or "").strip()
        if club.casefold() in owned:
            x=dict(r);x["club"]=owned[club.casefold()];eligible.append(x)
    out=[];errors=[]
    total=len(eligible)
    for i,r in enumerate(eligible,1):
        try:
            apps,_=player_apps(r["player_id"],token)
            if apps<=MAX_APPS:
                out.append({
                    "Club":r.get("club"),"Player":r.get("player_name"),
                    "Age":r.get("age"),"Position":r.get("position"),
                    "OVR":r.get("overall"),"Apps":apps,"Player ID":int(r["player_id"])
                })
        except Exception as e:
            errors.append((int(r["player_id"]),str(e)))
            if "429" in str(e):
                time.sleep(10)
        if progress:progress(i,total,len(out),len(errors))
        time.sleep(delay)
    df=pd.DataFrame(out)
    if not df.empty:
        df=df.sort_values(["Apps","Club","OVR"],ascending=[True,True,False],na_position="last").reset_index(drop=True)
    return df,errors,total
