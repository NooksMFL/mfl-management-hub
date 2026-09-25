
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

RATE_DELAY_SECONDS=3.0
DEFAULT_COOLDOWN_SECONDS=180

def _meta_get(key,default=None):
    c=db()
    r=c.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
    c.close()
    return r["value"] if r else default

def _meta_set(key,value):
    c=db()
    c.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,str(value)))
    c.commit(); c.close()

def cooldown_remaining():
    try:
        until=float(_meta_get("rate_limit_until","0") or 0)
    except Exception:
        until=0
    return max(0,int(until-time.time()))

def clear_cooldown():
    _meta_set("rate_limit_until","0")

CACHE_VERSION="3-cumulative-progression"

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT);
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
    row=c.execute("SELECT value FROM meta WHERE key='cache_version'").fetchone()
    if not row or row["value"] != CACHE_VERSION:
        c.execute("DELETE FROM club_player_s17")
        c.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('cache_version',?)",(CACHE_VERSION,))
    c.commit(); return c

def token():
    rt=os.getenv("MFL_REFRESH_TOKEN")
    if not rt: raise RuntimeError("MFL_REFRESH_TOKEN missing")
    r=requests.post(BASE+"/auth/refresh",headers=H,json={"refreshToken":rt},timeout=(5,20))
    r.raise_for_status()
    d=r.json(); a=d.get("access")
    if a is None and isinstance(d.get("data"),dict): a=d["data"].get("access")
    if isinstance(a,dict): a=a.get("token")
    if not a: raise RuntimeError("No access token returned")
    return a

def ah(t):
    h=dict(H); h["Authorization"]="Bearer "+t; return h

def get(path,t,params=None,timeout=(5,20)):
    remaining=cooldown_remaining()
    if remaining>0:
        raise RuntimeError(f"MFL_COOLDOWN:{remaining}")

    last_error=None
    for attempt in range(3):
        try:
            r=requests.get(BASE+path,headers=ah(t),params=params,timeout=timeout)
            if r.status_code==429:
                retry=r.headers.get("Retry-After")
                try:
                    wait=max(DEFAULT_COOLDOWN_SECONDS,int(float(retry))) if retry else DEFAULT_COOLDOWN_SECONDS
                except Exception:
                    wait=DEFAULT_COOLDOWN_SECONDS
                _meta_set("rate_limit_until",time.time()+wait)
                raise RuntimeError(f"MFL_RATE_LIMITED:{wait}")
            if not r.ok:
                raise RuntimeError(f"{path} returned {r.status_code}: {r.text[:120]}")
            return r.json()
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError) as e:
            last_error=e
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"MFL_TIMEOUT:{path}") from e
    raise last_error

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

KNOWN_OWNER_CLUBS={
 "0x65cc0e72dd71ad80":[
  {"id":3983,"name":"FCN Supermarine"},
  {"id":5884,"name":"FCN Goyang"},
  {"id":6390,"name":"FCN Vélez Academy"},
  {"id":6451,"name":"FCN Gladbach"},
  {"id":7126,"name":"FCN Angrense"},
  {"id":7530,"name":"FCN David Academy"},
  {"id":7580,"name":"FCN Antibes"},
  {"id":7756,"name":"FCN Swindon Town"},
  {"id":8026,"name":"FCN Gorzów"},
  {"id":8199,"name":"FCN Pickering"},
  {"id":9582,"name":"FCN Halesowen Academy"},
  {"id":10910,"name":"FCN Garza Academy"},
 ]
}

def _save_owned(wallet,found):
    c=db(); now=datetime.now(timezone.utc).isoformat()
    c.execute("DELETE FROM owned_clubs WHERE wallet=?",(wallet.lower(),))
    for x in found:
        c.execute("INSERT OR REPLACE INTO owned_clubs(wallet,club_id,club_name,checked_at) VALUES(?,?,?,?)",
                  (wallet.lower(),x["id"],x["name"],now))
    c.commit();c.close()

def owned_clubs(wallet,t=None,refresh=False):
    wallet=wallet.strip().lower()
    c=db()
    saved=c.execute("SELECT club_id,club_name FROM owned_clubs WHERE wallet=? ORDER BY club_name",(wallet,)).fetchall()
    c.close()
    if saved and not refresh:
        return [{"id":r["club_id"],"name":r["club_name"]} for r in saved]

    if t is None:
        try:t=token()
        except Exception:
            fallback=KNOWN_OWNER_CLUBS.get(wallet,[])
            if fallback:_save_owned(wallet,fallback)
            return fallback

    # The actual MFL web response mixes owned and staff-role clubs. The reliable
    # discriminator is title == MFL_OWNER. Do NOT send withLeague; MFL rejects it
    # on this API route in some sessions.
    attempts=[
        {"walletAddress":wallet},
        {"walletAddress":wallet,"withStaffContracts":"true"},
    ]
    last_error=None
    for params in attempts:
        try:
            raw=get("/clubs",t,params,timeout=(3,7))
            found=[]
            for x in arr(raw):
                if not isinstance(x,dict):continue
                if str(x.get("title") or "").strip().upper()!="MFL_OWNER":continue
                club=x.get("club") if isinstance(x.get("club"),dict) else x
                name=club.get("name") or club.get("clubName")
                cid=club.get("id") or club.get("clubId")
                if name:found.append({"id":cid,"name":str(name).strip()})
            if found:
                # unique
                uniq=[];seen=set()
                for x in found:
                    k=(x["id"],x["name"].casefold())
                    if k not in seen:
                        seen.add(k);uniq.append(x)
                _save_owned(wallet,uniq)
                return uniq
        except Exception as e:
            last_error=e

    fallback=KNOWN_OWNER_CLUBS.get(wallet,[])
    if fallback:
        _save_owned(wallet,fallback)
        return fallback
    if last_error: raise last_error
    return []

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
    raw=[]
    for e in ev:
        if not isinstance(e,dict): continue
        d=todt(e.get("date") or e.get("timestamp") or e.get("createdAt"));v=vals(e)
        if d and v: raw.append((d,v))
    raw.sort(key=lambda x:x[0]);current={};out=[]
    allowed={"overall","pace","shooting","passing","dribbling","defense","physical"}
    for d,v in raw:
        for k,val in v.items():
            if k in allowed and val is not None: current[k]=val
        if current: out.append((d,current.copy()))
    return out

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

def sync_batch(wallet,season_start,batch_size=None,progress=None):
    remaining=cooldown_remaining()
    if remaining>0:
        return {"saved":0,"errors":[],"batch":0,"eligible":0,"excluded":0,"owned":owned_clubs(wallet),
                "cooldown":remaining,"rate_limited":True}

    t=token()
    mine=owned_clubs(wallet,t)
    names={x["name"].strip().casefold():x["name"] for x in mine}
    rs=roster(wallet,t)
    eligible=[]
    excluded=0
    for r in rs:
        cn=(r.get("club") or "").strip()
        if cn.casefold() in names:
            r["club"]=names[cn.casefold()]
            eligible.append(r)
        else:
            excluded+=1

    c=db()
    checked={r[0] for r in c.execute(
        "SELECT player_id FROM club_player_s17 WHERE wallet=? AND error IS NULL",
        (wallet.lower(),)
    ).fetchall()}
    c.close()

    remaining_players=[r for r in eligible if r["player_id"] not in checked]
    if remaining_players:
        todo=remaining_players if batch_size is None else remaining_players[:int(batch_size)]
    else:
        # Full coverage exists: a one-click refresh walks every owned-club player,
        # oldest cached first, at the same conservative pace.
        c=db()
        old=[r[0] for r in c.execute(
            "SELECT player_id FROM club_player_s17 WHERE wallet=? AND error IS NULL ORDER BY checked_at",
            (wallet.lower(),)
        ).fetchall()]
        c.close()
        wanted_order={pid:i for i,pid in enumerate(old)}
        todo=sorted(eligible,key=lambda r:wanted_order.get(r["player_id"],999999))
        if batch_size is not None:
            todo=todo[:int(batch_size)]

    errors=[]; saved=0; done=0; rate_limited=False; cooldown=0
    total=len(todo)

    # Deliberately sequential. MFL was rate-limiting concurrent history requests
    # after ~70 players. One call at a time with a short gap is slower per batch
    # but reliable and preserves every completed player.
    for r in todo:
        try:
            x=analyse_player(r,t,season_start)
            c=db()
            c.execute("""INSERT OR REPLACE INTO club_player_s17
            (wallet,player_id,player,club,start_ovr,current_ovr,ovr_gain,attr_gain,pac,sho,pas,dri,defn,phy,baseline_at,last_progression,checked_at,error)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
            (wallet.lower(),x["player_id"],x["player"],x["club"],x["start_ovr"],x["current_ovr"],x["ovr_gain"],x["attr_gain"],
             x["pac"],x["sho"],x["pas"],x["dri"],x["defn"],x["phy"],x["baseline_at"],x["last_progression"],datetime.now(timezone.utc).isoformat()))
            c.commit(); c.close(); saved+=1
        except Exception as e:
            msg=str(e)
            if "MFL_RATE_LIMITED" in msg or "MFL_COOLDOWN" in msg:
                rate_limited=True
                cooldown=cooldown_remaining()
                errors.append((r["player_id"],msg))
                done+=1
                if progress: progress(done,total,len(errors))
                break
            if "MFL_TIMEOUT" in msg:
                # One slow player must not kill an hours-long full sync.
                # Leave it unsynced for the next run, pause, then continue.
                errors.append((r["player_id"],msg))
                done+=1
                if progress: progress(done,total,len(errors))
                time.sleep(8)
                continue
            errors.append((r["player_id"],msg))
        done+=1
        if progress: progress(done,total,len(errors))
        time.sleep(RATE_DELAY_SECONDS)

    return {
        "saved":saved,"errors":errors,"batch":total,"eligible":len(eligible),
        "excluded":excluded,"owned":mine,"cooldown":cooldown,
        "rate_limited":rate_limited
    }

def counts(wallet):
    d=cached(wallet)
    return {"cached":len(d),"errors":int(d["error"].notna().sum()) if not d.empty and "error" in d else 0}
