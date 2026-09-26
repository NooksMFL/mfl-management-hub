
from __future__ import annotations
import os, sqlite3, time, requests, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

BASE="https://api.playmfl.com"
DB=Path("wallet_shared_cache.db")
H={"Accept":"*/*","Origin":"https://app.playmfl.com","Referer":"https://app.playmfl.com/",
   "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"}
MAX_AGE_HOURS=6

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS roster(
      wallet TEXT,player_id INTEGER,player_name TEXT,club TEXT,age REAL,position TEXT,
      overall REAL,pace REAL,shooting REAL,passing REAL,dribbling REAL,defense REAL,physical REAL,
      cached_at TEXT,PRIMARY KEY(wallet,player_id));
    CREATE TABLE IF NOT EXISTS clubs(
      wallet TEXT,club_id INTEGER,club_name TEXT,cached_at TEXT,PRIMARY KEY(wallet,club_id,club_name));
    CREATE TABLE IF NOT EXISTS meta(wallet TEXT,key TEXT,value TEXT,PRIMARY KEY(wallet,key));
    CREATE TABLE IF NOT EXISTS watchlist(wallet TEXT,player_id INTEGER,created_at TEXT,PRIMARY KEY(wallet,player_id));
    CREATE TABLE IF NOT EXISTS club_snapshots(
      wallet TEXT,player_id INTEGER,snapshot_at TEXT,current_ovr REAL,ovr_gain REAL,attr_gain REAL,
      PRIMARY KEY(wallet,player_id,snapshot_at));
    """)
    c.commit()
    return c

def _now(): return datetime.now(timezone.utc).replace(microsecond=0)
def _iso(dt=None): return (dt or _now()).isoformat()
def _meta_get(wallet,key):
    c=db(); r=c.execute("SELECT value FROM meta WHERE wallet=? AND key=?",(wallet.lower(),key)).fetchone(); c.close()
    return r["value"] if r else None
def _meta_set(wallet,key,value):
    c=db(); c.execute("INSERT OR REPLACE INTO meta(wallet,key,value) VALUES(?,?,?)",(wallet.lower(),key,str(value))); c.commit(); c.close()

def token():
    rt=os.getenv("MFL_REFRESH_TOKEN")
    if not rt: raise RuntimeError("MFL_REFRESH_TOKEN missing")
    last=None
    for attempt in range(4):
        try:
            r=requests.post(BASE+"/auth/refresh",headers=H,json={"refreshToken":rt},timeout=20)
            if r.status_code in (429,500,502,503,504):
                last=f"HTTP {r.status_code}: {r.text[:120]}"; time.sleep(min(15,2*(2**attempt))); continue
            r.raise_for_status()
            d=r.json(); a=d.get("access")
            if a is None and isinstance(d.get("data"),dict): a=d["data"].get("access")
            if isinstance(a,dict): a=a.get("token")
            if not a: raise RuntimeError("No access token returned")
            return a
        except (requests.Timeout,requests.ConnectionError) as e:
            last=str(e); time.sleep(min(15,2*(2**attempt)))
    raise RuntimeError(f"MFL authentication failed: {last}")

def _ah(t):
    h=dict(H); h["Authorization"]="Bearer "+t; return h

def _get(path,t,params=None,timeout=25):
    last=None
    for attempt in range(4):
        try:
            r=requests.get(BASE+path,headers=_ah(t),params=params,timeout=timeout)
            if r.status_code==429:
                last="HTTP 429"; time.sleep(min(45,5*(2**attempt))); continue
            if r.status_code in (500,502,503,504):
                last=f"HTTP {r.status_code}"; time.sleep(min(20,2*(2**attempt))); continue
            if not r.ok: raise RuntimeError(f"{path} returned {r.status_code}: {r.text[:160]}")
            return r.json()
        except (requests.Timeout,requests.ConnectionError) as e:
            last=str(e); time.sleep(min(20,2*(2**attempt)))
    raise RuntimeError(f"{path} failed after retries: {last}")

def _arr(d):
    if isinstance(d,list): return d
    if isinstance(d,dict):
        for k in ("data","items","results","players","clubs"):
            x=d.get(k)
            if isinstance(x,list): return x
            if isinstance(x,dict):
                y=_arr(x)
                if y:return y
    return []

def _unwrap(p):
    if isinstance(p,dict):
        if isinstance(p.get("player"),dict): return p["player"]
        if isinstance(p.get("data"),dict): return p["data"]
    return p or {}

def _val(p,*names):
    p=_unwrap(p); m=p.get("metadata") if isinstance(p.get("metadata"),dict) else {}
    attrs=p.get("attributes") if isinstance(p.get("attributes"),dict) else {}
    for src in (p,attrs,m):
        for n in names:
            if isinstance(src,dict) and src.get(n) is not None: return src[n]
    return None

def _club_name(p):
    p=_unwrap(p); m=p.get("metadata") if isinstance(p.get("metadata"),dict) else {}
    for src in (p,m):
        for key in ("parentClub","owningClub","registeredClub","club","currentClub"):
            v=src.get(key)
            if isinstance(v,dict):
                n=v.get("name") or v.get("clubName")
                if n:return str(n)
            elif isinstance(v,str) and v:return v
    for key in ("activeContract","contract"):
        v=p.get(key)
        if isinstance(v,dict):
            cv=v.get("club")
            if isinstance(cv,dict):
                n=cv.get("name") or cv.get("clubName")
                if n:return str(n)
    return None

def _position(p):
    p=_unwrap(p); m=p.get("metadata") if isinstance(p.get("metadata"),dict) else {}
    pos=m.get("positions") or p.get("positions") or []
    if isinstance(pos,str): pos=[pos]
    return " / ".join(str(x) for x in pos if x) or None

def _is_fresh(wallet,key,max_age_hours=MAX_AGE_HOURS):
    raw=_meta_get(wallet,key)
    if not raw:return False
    try:
        dt=pd.to_datetime(raw,utc=True).to_pydatetime()
        return _now()-dt < timedelta(hours=max_age_hours)
    except:return False

def roster_rows(wallet):
    c=db(); rows=c.execute("SELECT * FROM roster WHERE wallet=? ORDER BY player_name",(wallet.lower(),)).fetchall(); c.close()
    return [dict(r) for r in rows]

def roster_payload(wallet,t=None,force=False):
    wallet=wallet.strip().lower()
    rows=roster_rows(wallet)
    if rows and not force and _is_fresh(wallet,"roster_updated"):
        return [{
          "id":r["player_id"],"name":r["player_name"],
          "metadata":{"id":r["player_id"],"age":r["age"],"positions":[r["position"]] if r["position"] else [],
                      "overall":r["overall"],"pace":r["pace"],"shooting":r["shooting"],"passing":r["passing"],
                      "dribbling":r["dribbling"],"defense":r["defense"],"physical":r["physical"]},
          "club":{"name":r["club"]} if r["club"] else None
        } for r in rows]
    t=t or token()
    raw=_arr(_get("/players",t,{"ownerWalletAddress":wallet,"limit":1200},timeout=30))
    now=_iso()
    c=db()
    c.execute("DELETE FROM roster WHERE wallet=?",(wallet,))
    for item in raw:
        p=_unwrap(item); m=p.get("metadata") if isinstance(p.get("metadata"),dict) else {}
        pid=p.get("id") or p.get("playerId") or m.get("id")
        try:pid=int(pid)
        except:continue
        name=p.get("name") or m.get("name") or (str(p.get("firstName") or m.get("firstName") or "")+" "+str(p.get("lastName") or m.get("lastName") or "")).strip() or f"Player {pid}"
        c.execute("""INSERT OR REPLACE INTO roster VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (wallet,pid,name,_club_name(p),m.get("age") or p.get("age"),_position(p),
                   _val(p,"overall","overallRating","ovr"),_val(p,"pace","PAC"),_val(p,"shooting","SHO"),
                   _val(p,"passing","PAS"),_val(p,"dribbling","DRI"),_val(p,"defense","defending","DEF"),
                   _val(p,"physical","physicality","PHY"),now))
    c.commit(); c.close()
    _meta_set(wallet,"roster_updated",now)
    return roster_payload(wallet,t,False)

def clubs_rows(wallet):
    c=db(); rows=c.execute("SELECT * FROM clubs WHERE wallet=? ORDER BY club_name",(wallet.lower(),)).fetchall(); c.close()
    return [{"id":r["club_id"],"name":r["club_name"]} for r in rows]

def save_clubs(wallet,clubs):
    wallet=wallet.strip().lower(); now=_iso(); c=db()
    c.execute("DELETE FROM clubs WHERE wallet=?",(wallet,))
    for x in clubs:
        c.execute("INSERT OR REPLACE INTO clubs(wallet,club_id,club_name,cached_at) VALUES(?,?,?,?)",
                  (wallet,x.get("id"),x.get("name"),now))
    c.commit(); c.close(); _meta_set(wallet,"clubs_updated",now)

def fetch_clubs(wallet,t=None,force=False):
    wallet=wallet.strip().lower()
    saved=clubs_rows(wallet)
    if saved and not force and _is_fresh(wallet,"clubs_updated"): return saved
    t=t or token()
    found=[]
    for params in ({"walletAddress":wallet},{"walletAddress":wallet,"withStaffContracts":"true"}):
        try:
            raw=_arr(_get("/clubs",t,params,timeout=15))
            for x in raw:
                if not isinstance(x,dict):continue
                if str(x.get("title") or "").upper()!="MFL_OWNER":continue
                club=x.get("club") if isinstance(x.get("club"),dict) else x
                name=club.get("name") or club.get("clubName"); cid=club.get("id") or club.get("clubId")
                if name: found.append({"id":cid,"name":str(name)})
            if found:break
        except Exception:
            continue
    uniq=[]; seen=set()
    for x in found:
        k=(x["id"],x["name"].casefold())
        if k not in seen:seen.add(k);uniq.append(x)
    save_clubs(wallet,uniq)
    return uniq

def sync_wallet(wallet,force=True):
    t=token()
    roster=roster_payload(wallet,t,force=force)
    clubs=fetch_clubs(wallet,t,force=force)
    return {"players":len(roster),"clubs":len(clubs),"updated_at":_iso()}

def freshness(wallet):
    return {"roster":_meta_get(wallet,"roster_updated"),"clubs":_meta_get(wallet,"clubs_updated")}

def add_watch(wallet,pid):
    c=db(); c.execute("INSERT OR IGNORE INTO watchlist(wallet,player_id,created_at) VALUES(?,?,?)",(wallet.lower(),int(pid),_iso())); c.commit(); c.close()
def remove_watch(wallet,pid):
    c=db(); c.execute("DELETE FROM watchlist WHERE wallet=? AND player_id=?",(wallet.lower(),int(pid))); c.commit(); c.close()
def watched(wallet):
    c=db(); rows=c.execute("SELECT player_id,created_at FROM watchlist WHERE wallet=? ORDER BY created_at DESC",(wallet.lower(),)).fetchall(); c.close()
    return [dict(r) for r in rows]

def capture_club_snapshot(wallet,df):
    if df is None or len(df)==0:return
    now=_now().strftime("%Y-%m-%dT00:00:00+00:00")
    c=db()
    for _,r in df.iterrows():
        c.execute("""INSERT OR REPLACE INTO club_snapshots(wallet,player_id,snapshot_at,current_ovr,ovr_gain,attr_gain)
                     VALUES(?,?,?,?,?,?)""",(wallet.lower(),int(r["player_id"]),now,
                     float(r.get("current_ovr") or 0),float(r.get("ovr_gain") or 0),float(r.get("attr_gain") or 0)))
    c.commit(); c.close()

def snapshot_deltas(wallet,days):
    c=db()
    now=_now()
    latest=pd.read_sql_query("SELECT * FROM club_snapshots WHERE wallet=? AND snapshot_at=(SELECT MAX(snapshot_at) FROM club_snapshots WHERE wallet=?)",(c,),params=None) if False else None
    rows=c.execute("SELECT * FROM club_snapshots WHERE wallet=? ORDER BY snapshot_at",(wallet.lower(),)).fetchall()
    c.close()
    if not rows:return pd.DataFrame()
    df=pd.DataFrame([dict(r) for r in rows]); df["snapshot_at"]=pd.to_datetime(df["snapshot_at"],utc=True)
    newest=df["snapshot_at"].max(); target=newest-pd.Timedelta(days=days)
    latest=df[df["snapshot_at"]==newest].set_index("player_id")
    older_dates=df[df["snapshot_at"]<=target]["snapshot_at"]
    if older_dates.empty:return pd.DataFrame()
    old_date=older_dates.max(); old=df[df["snapshot_at"]==old_date].set_index("player_id")
    out=latest.join(old[["current_ovr","ovr_gain","attr_gain"]],rsuffix="_old",how="inner")
    out["period_ovr"]=out["current_ovr"]-out["current_ovr_old"]
    out["period_attr"]=out["attr_gain"]-out["attr_gain_old"]
    return out.reset_index()
