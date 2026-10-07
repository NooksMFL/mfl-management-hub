from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
import requests

DB = "career_projection.db"
BASE = "https://api.playmfl.com"
H = {
    "Accept":"*/*",
    "Origin":"https://app.playmfl.com",
    "Referer":"https://app.playmfl.com/",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0"
}
PAGE_SIZE = 1500

def _now():
    return datetime.now(timezone.utc).isoformat()

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS careers(
      player_id INTEGER PRIMARY KEY,name TEXT,position TEXT,mint_age INTEGER,start_ovr REAL,
      current_age INTEGER,current_ovr REAL,division TEXT,seasons INTEGER,career_gain REAL,
      season_gains TEXT,updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS player_index(
      player_id INTEGER PRIMARY KEY,name TEXT,position TEXT,current_age INTEGER,current_ovr REAL,
      mint_age INTEGER,seasons_hint INTEGER,division TEXT,is_retired INTEGER DEFAULT 0,
      processed INTEGER DEFAULT 0,error TEXT,updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS build_state(
      key TEXT PRIMARY KEY,value TEXT,updated_at TEXT)""")
    c.commit()
    return c

def _state(key, default=None):
    c=db(); r=c.execute("SELECT value FROM build_state WHERE key=?",(key,)).fetchone(); c.close()
    return default if r is None else r["value"]

def _set_state(key, value):
    c=db()
    c.execute("""INSERT INTO build_state(key,value,updated_at) VALUES(?,?,?)
      ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at""",
      (key,str(value),_now()))
    c.commit(); c.close()

def _get(path, params=None, retries=4):
    last=None
    for attempt in range(retries):
        try:
            r=requests.get(BASE+path,headers=H,params=params,timeout=35)
            if r.status_code==429:
                wait=float(r.headers.get("Retry-After") or min(30,3*(attempt+1)))
                time.sleep(wait); last=f"HTTP 429"; continue
            if r.status_code in (500,502,503,504):
                last=f"HTTP {r.status_code}: {r.text[:160]}"
                time.sleep(min(12,2**attempt)); continue
            if not r.ok:
                raise RuntimeError(f"{path} returned {r.status_code}: {r.text[:220]}")
            return r.json()
        except (requests.RequestException, ValueError) as e:
            last=str(e)
            if attempt<retries-1: time.sleep(min(8,2**attempt))
    raise RuntimeError(f"{path} failed after retries: {last}")

def _meta(p):
    return p.get("metadata") if isinstance(p,dict) and isinstance(p.get("metadata"),dict) else {}

def _to_int(v):
    try:return None if v in (None,"") else int(v)
    except:return None

def _to_float(v):
    try:return None if v in (None,"") else float(v)
    except:return None

def _name(p,m):
    name=str(m.get("name") or "").strip()
    if not name:
        name=(str(m.get("firstName") or "")+" "+str(m.get("lastName") or "")).strip()
    return name or f"Player {p.get('id')}"

def _division(p):
    contract=p.get("activeContract") if isinstance(p.get("activeContract"),dict) else {}
    club=contract.get("club") if isinstance(contract.get("club"),dict) else {}
    return str(club.get("division") or "").strip()

def _seasons_hint(p,m):
    direct=(p.get("playerSeasons") or m.get("playerSeasons") or p.get("seasons") or m.get("seasons"))
    val=_to_int(direct)
    if val: return val
    age=_to_int(m.get("age"))
    mint=_to_int(m.get("ageAtMint") or p.get("ageAtMint") or m.get("mintAge"))
    return (age-mint+1) if age is not None and mint is not None else None

def _save_index(players, retired):
    c=db(); n=0
    for p in players:
        if not isinstance(p,dict) or p.get("id") is None: continue
        m=_meta(p); positions=m.get("positions") if isinstance(m.get("positions"),list) else []
        pid=int(p["id"])
        vals=(pid,_name(p,m),str(positions[0] if positions else ""),_to_int(m.get("age")),
              _to_float(m.get("overall")),_to_int(m.get("ageAtMint") or p.get("ageAtMint") or m.get("mintAge")),
              _seasons_hint(p,m),_division(p),1 if retired else 0,_now())
        c.execute("""INSERT INTO player_index(player_id,name,position,current_age,current_ovr,mint_age,seasons_hint,division,is_retired,updated_at)
          VALUES(?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(player_id) DO UPDATE SET
          name=excluded.name,position=excluded.position,current_age=excluded.current_age,current_ovr=excluded.current_ovr,
          mint_age=COALESCE(excluded.mint_age,player_index.mint_age),
          seasons_hint=COALESCE(excluded.seasons_hint,player_index.seasons_hint),
          division=CASE WHEN excluded.division<>'' THEN excluded.division ELSE player_index.division END,
          is_retired=excluded.is_retired,updated_at=excluded.updated_at""",vals)
        n+=1
    c.commit(); c.close(); return n

def index_source(retired=False, pages=4, progress=None):
    prefix="retired" if retired else "active"
    if _state(prefix+"_done","0")=="1":
        return {"source":prefix,"done":True,"pages":0,"saved":0}
    before=_state(prefix+"_before")
    before=int(before) if before not in (None,"","None") else None
    saved=0; page_count=0
    for _ in range(int(pages)):
        params={"limit":PAGE_SIZE,"isRetired":"true" if retired else "false"}
        if before is not None: params["beforePlayerId"]=before
        payload=_get("/players",params)
        if not isinstance(payload,list): raise RuntimeError("/players response was not a list")
        fresh=[x for x in payload if isinstance(x,dict) and x.get("id") is not None]
        saved+=_save_index(fresh,retired); page_count+=1
        if progress: progress(prefix,page_count,saved,len(fresh))
        if len(fresh)<PAGE_SIZE:
            _set_state(prefix+"_done","1"); _set_state(prefix+"_before","")
            return {"source":prefix,"done":True,"pages":page_count,"saved":saved}
        nxt=min(int(x["id"]) for x in fresh)
        if before is not None and nxt>=before:
            raise RuntimeError(f"{prefix} player pagination did not advance")
        before=nxt; _set_state(prefix+"_before",before)
        time.sleep(.2)
    return {"source":prefix,"done":False,"pages":page_count,"saved":saved}

def index_stats():
    c=db()
    total=int(c.execute("SELECT COUNT(*) FROM player_index").fetchone()[0])
    eligible=int(c.execute("SELECT COUNT(*) FROM player_index WHERE seasons_hint>=8").fetchone()[0])
    processed=int(c.execute("SELECT COUNT(*) FROM player_index WHERE processed=1").fetchone()[0])
    errors=int(c.execute("SELECT COUNT(*) FROM player_index WHERE error IS NOT NULL AND error<>''").fetchone()[0])
    careers=int(c.execute("SELECT COUNT(*) FROM careers").fetchone()[0])
    c.close()
    return {"indexed":total,"eligible":eligible,"processed":processed,"errors":errors,"careers":careers,
            "active_done":_state("active_done","0")=="1","retired_done":_state("retired_done","0")=="1"}

def _vals(e):
    return e.get("values") if isinstance(e,dict) and isinstance(e.get("values"),dict) else {}

def public_history(pid):
    data=_get(f"/players/{int(pid)}/experiences/history")
    return data if isinstance(data,list) else (data.get("data",[]) if isinstance(data,dict) else [])

def career_from_events(idx, events):
    events=[e for e in events if isinstance(e,dict)]
    events.sort(key=lambda e:e.get("date") or e.get("createdAt") or e.get("timestamp") or 0)
    age=None; mint_age=idx.get("mint_age"); start_ovr=None; current_ovr=None
    season_start=None; gains=[]
    for e in events:
        v=_vals(e)
        if v.get("age") is not None:
            new_age=_to_int(v.get("age"))
            if age is None:
                age=new_age
                if mint_age is None: mint_age=new_age
            elif new_age is not None and new_age!=age:
                if season_start is not None and current_ovr is not None:
                    gains.append(max(0.0,current_ovr-season_start))
                age=new_age
                season_start=current_ovr
        if v.get("overall") is not None:
            o=_to_float(v.get("overall"))
            if o is not None:
                if start_ovr is None: start_ovr=o
                if season_start is None: season_start=o
                current_ovr=o
    if season_start is not None and current_ovr is not None:
        gains.append(max(0.0,current_ovr-season_start))
    if start_ovr is None: start_ovr=idx.get("current_ovr")
    if current_ovr is None: current_ovr=idx.get("current_ovr")
    if age is None: age=idx.get("current_age")
    if mint_age is None and age is not None and idx.get("seasons_hint"):
        mint_age=age-int(idx["seasons_hint"])+1
    if start_ovr is None or current_ovr is None:
        raise RuntimeError("No OVR data in player metadata/history")
    return {"player_id":idx["player_id"],"name":idx["name"],"position":idx["position"],
      "mint_age":mint_age,"start_ovr":start_ovr,"current_age":age,"current_ovr":current_ovr,
      "division":idx.get("division") or "","seasons":len(gains),"career_gain":current_ovr-start_ovr,"gains":gains}

def save(row):
    c=db(); sg=",".join(str(round(float(x),3)) for x in row["gains"])
    c.execute("""INSERT OR REPLACE INTO careers VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
      (row["player_id"],row["name"],row["position"],row["mint_age"],row["start_ovr"],row["current_age"],
       row["current_ovr"],row["division"],row["seasons"],row["career_gain"],sg,_now()))
    c.execute("UPDATE player_index SET processed=1,error=NULL WHERE player_id=?",(row["player_id"],))
    c.commit(); c.close()

def process_history_batch(limit=100, progress=None):
    c=db()
    rs=[dict(r) for r in c.execute("""SELECT * FROM player_index
      WHERE processed=0 AND seasons_hint>=8 ORDER BY player_id DESC LIMIT ?""",(int(limit),)).fetchall()]
    c.close()
    done=0; errors=0
    for i,idx in enumerate(rs,1):
        try:
            row=career_from_events(idx,public_history(idx["player_id"]))
            save(row); done+=1
        except Exception as e:
            c=db(); c.execute("UPDATE player_index SET error=? WHERE player_id=?",(str(e)[:500],idx["player_id"])); c.commit(); c.close()
            errors+=1
        if progress: progress(i,len(rs),done,errors)
        time.sleep(.08)
    return {"requested":len(rs),"saved":done,"errors":errors}

def build_batch(index_pages=4,history_limit=100,progress=None):
    results=[]
    if _state("active_done","0")!="1": results.append(index_source(False,index_pages,progress))
    elif _state("retired_done","0")!="1": results.append(index_source(True,index_pages,progress))
    hist=process_history_batch(history_limit,progress)
    return {"index":results,"history":hist,"stats":index_stats()}

def rows(min_seasons=0):
    c=db(); rs=[dict(x) for x in c.execute("SELECT * FROM careers WHERE seasons>=?",(int(min_seasons),)).fetchall()]; c.close()
    for r in rs:r["gains"]=[float(x) for x in (r.pop("season_gains") or "").split(",") if x!=""]
    return rs

def find_matches(start_ovr=None,mint_age=None,groups=None,ranges=None,total_min=None,total_max=None,first_n=None,min_seasons=8):
    data=rows(min_seasons);out=[]
    def group(pos):
        if pos=="GK":return "GK"
        if pos in {"CB","LB","RB","LWB","RWB"}:return "DEF"
        if pos in {"CDM","CM","LM","RM"}:return "MID"
        return "ATT"
    for r in data:
        if start_ovr is not None and int(round(r["start_ovr"]))!=int(start_ovr):continue
        if mint_age is not None and r.get("mint_age") is not None and int(r["mint_age"])!=int(mint_age):continue
        if groups and group(r["position"]) not in groups:continue
        ok=True
        for idx,(lo,hi) in (ranges or {}).items():
            if idx>=len(r["gains"]):ok=False;break
            g=r["gains"][idx]
            if lo is not None and g<lo:ok=False
            if hi is not None and g>hi:ok=False
        if not ok:continue
        if total_min is not None or total_max is not None:
            n=int(first_n or len(r["gains"])); tot=sum(r["gains"][:n])
            if total_min is not None and tot<total_min:continue
            if total_max is not None and tot>total_max:continue
        out.append(r)
    return out

def reset_build():
    c=db()
    c.execute("DELETE FROM player_index"); c.execute("DELETE FROM careers"); c.execute("DELETE FROM build_state")
    c.commit(); c.close()
