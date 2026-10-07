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
    v=_first(rec,("season","seasonNumber","seasonId","season_id"))
    if isinstance(v,dict):
        v=v.get("number") or v.get("id") or v.get("name")
    s=str(v or "")
    digits="".join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else None

def _apps(rec):
    v=_first(rec,("appearances","apps","gamesPlayed","matchesPlayed","played"))
    try:return int(float(v))
    except:return 0

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
