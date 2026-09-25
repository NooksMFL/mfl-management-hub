
from __future__ import annotations
import os, sqlite3, requests, time
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

BASE="https://api.playmfl.com"
DB=Path("club_development_cache.db")
H={"Accept":"*/*","Origin":"https://app.playmfl.com","Referer":"https://app.playmfl.com/",
   "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152 Safari/537.36"}
ATTRS=("pace","shooting","passing","dribbling","defense","physical")
SHORT={"pace":"PAC","shooting":"SHO","passing":"PAS","dribbling":"DRI","defense":"DEF","physical":"PHY"}

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS club_player_s17(
      wallet TEXT, player_id INTEGER, player TEXT, club TEXT,
      start_ovr REAL,current_ovr REAL,ovr_gain REAL,attr_gain REAL,
      pac REAL,sho REAL,pas REAL,dri REAL,defn REAL,phy REAL,
      baseline_at TEXT,last_progression TEXT,checked_at TEXT,error TEXT,
      PRIMARY KEY(wallet,player_id)
    );
    CREATE TABLE IF NOT EXISTS owned_clubs(
      wallet TEXT,club_id INTEGER,club_name TEXT,checked_at TEXT,
      PRIMARY KEY(wallet,club_id)
    );
    """)
    c.commit(); return c

def token():
    rt=os.getenv("MFL_REFRESH_TOKEN")
    if not rt: raise RuntimeError("MFL_REFRESH_TOKEN missing")
    r=requests.post(BASE+"/auth/refresh",headers=H,json={"refreshToken":rt},timeout=(3,6))
    r.raise_for_status()
    d=r.json(); a=d.get("access")
    if a is None and isinstance(d.get("data"),dict): a=d["data"].get("access")
    if isinstance(a,dict): a=a.get("token")
    if not a: raise RuntimeError("No access token returned")
    return a

def ah(t):
    h=dict(H); h["Authorization"]="Bearer "+t; return h

def get(path,t,params=None,timeout=(3,6)):
    r=requests.get(BASE+path,headers=ah(t),params=params,timeout=timeout)
    if r.status_code==429:
        raise RuntimeError("MFL_RATE_LIMITED")
    if not r.ok:
        raise RuntimeError(f"{path} returned {r.status_code}: {r.text[:120]}")
    return r.json()

def arr(d):
    if isinstance(d,list): return d
    if isinstance(d,dict):
        for k in ("data","items","results","players","clubs","history","experiences"):
            x=d.get(k)
            if isinstance(x,list): return x
            if isinstance(x,dict):
                y=arr(x)
                if y:return y
    return []

def unwrap(p):
    if isinstance(p,dict):
        if isinstance(p.get("player"),dict): return p["player"]
        if isinstance(p.get("data"),dict): return p["data"]
    return p or {}

def club_name(p):
    p=unwrap(p); m=p.get("metadata") if isinstance(p.get("metadata"),dict) else {}
    # Prefer owning/registered/parent club before current club.
    for src in (p,m):
        for key in ("parentClub","owningClub","registeredClub","club"):
            v=src.get(key)
            if isinstance(v,dict):
                n=v.get("name") or v.get("clubName")
                if n:return str(n)
            if isinstance(v,str) and v:return v
    for key in ("activeContract","contract"):
        v=p.get(key)
        if isinstance(v,dict) and isinstance(v.get("club"),dict):
            c=v["club"]; n=c.get("name") or c.get("clubName")
            if n:return str(n)
    return None

def owned_clubs(wallet,t=None,refresh=False):
    c=db()
    saved=c.execute("SELECT club_id,club_name FROM owned_clubs WHERE wallet=? ORDER BY club_name",(wallet.lower(),)).fetchall()
    if saved and not refresh:
        c.close(); return [{"id":r["club_id"],"name":r["club_name"]} for r in saved]
    c.close()
    if t is None:t=token()
    raw=get("/clubs",t,{"walletAddress":wallet,"withStaffContracts":"true","withLeague":"true"},timeout=(3,7))
    found=[]
    for x in arr(raw):
        if not isinstance(x,dict) or str(x.get("title") or "").strip().upper()!="MFL_OWNER": continue
        club=x.get("club") if isinstance(x.get("club"),dict) else x
        name=club.get("name") or club.get("clubName"); cid=club.get("id") or club.get("clubId")
        if name:found.append({"id":cid,"name":str(name).strip()})
    c=db(); now=datetime.now(timezone.utc).isoformat()
    c.execute("DELETE FROM owned_clubs WHERE wallet=?",(wallet.lower(),))
    for x in found:
        c.execute("INSERT OR REPLACE INTO owned_clubs(wallet,club_id,club_name,checked_at) VALUES(?,?,?,?)",
                  (wallet.lower(),x["id"],x["name"],now))
    c.commit();c.close()
    return found

def roster(wallet,t):
    raw=get("/players",t,{"ownerWalletAddress":wallet,"limit":1200},timeout=(4,8))
    rows=[]
    for item in arr(raw):
        p=unwrap(item); m=p.get("metadata") if isinstance(p.get("metadata"),dict) else {}
        pid=p.get("id") or p.get("playerId") or m.get("id")
        try:pid=int(pid)
        except:continue
        name=p.get("name") or m.get("name") or (str(p.get("firstName") or m.get("firstName") or "")+" "+str(p.get("lastName") or m.get("lastName") or "")).strip()
        rows.append({"player_id":pid,"player":name or f"Player {pid}","club":club_name(p)})
    return rows

def todt(v):
    if v is None:return None
    try:
        if isinstance(v,(int,float)):
            return pd.to_datetime(v,unit="ms" if v>10_000_000_000 else "s",utc=True).to_pydatetime()
        return pd.to_datetime(v,utc=True).to_pydatetime()
    except:return None

def events(pid,t):
    return arr(get(f"/players/{pid}/experiences/history",t,timeout=(2.5,5)))

def vals(e):
    return e.get("values") if isinstance(e,dict) and isinstance(e.get("values"),dict) else {}

def states(ev):
    out=[]
    for e in ev:
        if not isinstance(e,dict):continue
        d=todt(e.get("date") or e.get("timestamp") or e.get("createdAt"))
        v=vals(e)
        if d and v:out.append((d,v))
    out.sort(key=lambda x:x[0]); return out

def num(v):
    try:return float(v)
    except:return None

def analyse_player(r,t,season_start):
    ev=states(events(r["player_id"],t))
    if not ev:raise RuntimeError("NO_HISTORY")
    cutoff=pd.to_datetime(season_start,utc=True).to_pydatetime()
    prior=[x for x in ev if x[0]<=cutoff]
    start=prior[-1] if prior else ev[0]
    current=ev[-1]
    def delta(k):
        a=num(current[1].get(k));b=num(start[1].get(k))
        return max(0,a-b) if a is not None and b is not None else 0
    gains={k:delta(k) for k in ATTRS}
    return {
      "player_id":r["player_id"],"player":r["player"],"club":r["club"],
      "start_ovr":num(start[1].get("overall")),"current_ovr":num(current[1].get("overall")),
      "ovr_gain":delta("overall"),"attr_gain":sum(gains.values()),
      "pac":gains["pace"],"sho":gains["shooting"],"pas":gains["passing"],
      "dri":gains["dribbling"],"defn":gains["defense"],"phy":gains["physical"],
      "baseline_at":start[0].isoformat(),"last_progression":current[0].isoformat()
    }

def cached(wallet):
    c=db()
    rows=c.execute("SELECT * FROM club_player_s17 WHERE wallet=?",(wallet.lower(),)).fetchall()
    c.close()
    return pd.DataFrame([dict(r) for r in rows])

def sync_batch(wallet,season_start,batch_size=30,progress=None):
    t=token()
    mine=owned_clubs(wallet,t)
    names={x["name"].strip().casefold():x["name"] for x in mine}
    rs=roster(wallet,t)
    eligible=[]
    excluded=0
    for r in rs:
        cn=(r.get("club") or "").strip()
        if cn.casefold() in names:
            r["club"]=names[cn.casefold()];eligible.append(r)
        else:
            excluded+=1
    c=db()
    checked={r[0] for r in c.execute("SELECT player_id FROM club_player_s17 WHERE wallet=? AND error IS NULL",(wallet.lower(),)).fetchall()}
    c.close()
    todo=[r for r in eligible if r["player_id"] not in checked][:int(batch_size)]
    if not todo:
        # refresh oldest successful rows when full cache exists
        c=db()
        old=[r[0] for r in c.execute("SELECT player_id FROM club_player_s17 WHERE wallet=? ORDER BY checked_at LIMIT ?",(wallet.lower(),int(batch_size))).fetchall()]
        c.close()
        wanted=set(old);todo=[r for r in eligible if r["player_id"] in wanted]

    done=0;errors=[];saved=0
    with ThreadPoolExecutor(max_workers=min(12,max(1,len(todo)))) as ex:
        fut={ex.submit(analyse_player,r,t,season_start):r for r in todo}
        for f in as_completed(fut):
            r=fut[f]
            try:
                x=f.result()
                c=db()
                c.execute("""INSERT OR REPLACE INTO club_player_s17
                (wallet,player_id,player,club,start_ovr,current_ovr,ovr_gain,attr_gain,pac,sho,pas,dri,defn,phy,baseline_at,last_progression,checked_at,error)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
                (wallet.lower(),x["player_id"],x["player"],x["club"],x["start_ovr"],x["current_ovr"],x["ovr_gain"],x["attr_gain"],
                 x["pac"],x["sho"],x["pas"],x["dri"],x["defn"],x["phy"],x["baseline_at"],x["last_progression"],datetime.now(timezone.utc).isoformat()))
                c.commit();c.close();saved+=1
            except Exception as e:
                errors.append((r["player_id"],str(e)))
            done+=1
            if progress:progress(done,len(todo),len(errors))
    return {"saved":saved,"errors":errors,"batch":len(todo),"eligible":len(eligible),"excluded":excluded,"owned":mine}

def counts(wallet):
    d=cached(wallet)
    return {"cached":len(d),"errors":int(d["error"].notna().sum()) if not d.empty and "error" in d else 0}
