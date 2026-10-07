from __future__ import annotations
import sqlite3, time, math
from datetime import datetime, timezone
import pandas as pd
import agency_backend as agency

DB="career_projection.db"
STATUSES=("D1","D2","D3","D4","D5","D6","D7","D8","D9","D10")

def db():
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS careers(
      player_id INTEGER PRIMARY KEY,name TEXT,position TEXT,mint_age INTEGER,start_ovr REAL,current_age INTEGER,current_ovr REAL,
      division TEXT,seasons INTEGER,career_gain REAL,season_gains TEXT,updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS scan_status(
      division TEXT PRIMARY KEY,status TEXT,clubs_scanned INTEGER DEFAULT 0,players INTEGER DEFAULT 0,last_run TEXT,error TEXT)""")
    c.commit();return c

def _vals(e):
    return e.get("values") if isinstance(e,dict) and isinstance(e.get("values"),dict) else {}

def _reason(e):
    return str((e or {}).get("reasonType") or (e or {}).get("reason") or "").upper()

def _profile(pid,t):
    p=agency.profile(int(pid),t)
    if isinstance(p,dict) and isinstance(p.get("player"),dict):p=p["player"]
    m=p.get("metadata") if isinstance(p,dict) and isinstance(p.get("metadata"),dict) else {}
    pos=m.get("positions") or []
    return p,m,(pos[0] if pos else "")

def career_from_history(pid,t=None):
    t=t or agency.token();p,m,pos=_profile(pid,t);ev=agency.exp_history(int(pid),t)
    ev=[e for e in ev if isinstance(e,dict)]
    ev.sort(key=lambda e:e.get("date") or e.get("createdAt") or 0)
    age=None;ovr=None;mint_age=None;start_ovr=None;season_start=None;gains=[]
    last_ovr=None
    for e in ev:
        v=_vals(e); reason=_reason(e)
        if v.get("age") is not None:
            new_age=int(v["age"])
            if age is None:
                age=new_age;mint_age=new_age
            elif new_age!=age:
                if season_start is not None and last_ovr is not None:gains.append(max(0,last_ovr-season_start))
                age=new_age;season_start=last_ovr
        if v.get("overall") is not None:
            o=float(v["overall"])
            if start_ovr is None:start_ovr=o
            if season_start is None:season_start=o
            ovr=o;last_ovr=o
    if season_start is not None and last_ovr is not None and (not gains or age is not None):
        gains.append(max(0,last_ovr-season_start))
    if start_ovr is None:start_ovr=float(m.get("overall") or 0)
    if ovr is None:ovr=float(m.get("overall") or start_ovr)
    if mint_age is None:mint_age=int(m.get("age") or 0)
    if age is None:age=int(m.get("age") or mint_age)
    name=(str(m.get("firstName") or "")+" "+str(m.get("lastName") or "")).strip() or str(p.get("name") or f"Player {pid}")
    return {"player_id":int(pid),"name":name,"position":pos,"mint_age":mint_age,"start_ovr":start_ovr,
      "current_age":age,"current_ovr":ovr,"seasons":len(gains),"career_gain":ovr-start_ovr,"gains":gains}

def save(row,division=""):
    c=db();sg=",".join(str(round(float(x),3)) for x in row["gains"])
    c.execute("""INSERT OR REPLACE INTO careers VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
      (row["player_id"],row["name"],row["position"],row["mint_age"],row["start_ovr"],row["current_age"],row["current_ovr"],
       division,row["seasons"],row["career_gain"],sg,datetime.now(timezone.utc).isoformat()))
    c.commit();c.close()

def rows(min_seasons=0):
    c=db();rs=[dict(x) for x in c.execute("SELECT * FROM careers WHERE seasons>=?",(int(min_seasons),)).fetchall()];c.close()
    for r in rs:r["gains"]=[float(x) for x in (r.pop("season_gains") or "").split(",") if x!=""]
    return rs

def status_rows():
    c=db();existing={r["division"]:dict(r) for r in c.execute("SELECT * FROM scan_status").fetchall()};c.close()
    return [existing.get(d,{"division":d,"status":"Not run","clubs_scanned":0,"players":0,"last_run":None,"error":None}) for d in STATUSES]

def find_matches(start_ovr=None,mint_age=None,groups=None,ranges=None,total_min=None,total_max=None,first_n=None,min_seasons=8):
    data=rows(min_seasons);out=[]
    def group(pos):
        if pos=="GK":return "GK"
        if pos in {"CB","LB","RB","LWB","RWB"}:return "DEF"
        if pos in {"CDM","CM","LM","RM"}:return "MID"
        return "ATT"
    for r in data:
        if start_ovr is not None and int(round(r["start_ovr"]))!=int(start_ovr):continue
        if mint_age is not None and int(r["mint_age"])!=int(mint_age):continue
        if groups and group(r["position"]) not in groups:continue
        ok=True
        for idx,(lo,hi) in (ranges or {}).items():
            if idx>=len(r["gains"]):ok=False;break
            g=r["gains"][idx]
            if lo is not None and g<lo:ok=False
            if hi is not None and g>hi:ok=False
        if not ok:continue
        if total_min is not None or total_max is not None:
            n=int(first_n or len(r["gains"]));tot=sum(r["gains"][:n])
            if total_min is not None and tot<total_min:continue
            if total_max is not None and tot>total_max:continue
        out.append(r)
    return out
