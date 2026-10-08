"""Live MFL bargains: recent completed sales versus current asking prices."""
from __future__ import annotations
import time
import statistics
import requests
import pandas as pd
import agency_backend as agency

def _num(v):
    try: return float(v)
    except (TypeError,ValueError): return None

def _player(obj):
    p=obj.get("player") or {}
    if not isinstance(p,dict): return {}
    m=p.get("metadata") or {}
    if not isinstance(m,dict): m={}
    positions=m.get("positions") or p.get("positions") or []
    if isinstance(positions,str): positions=[positions]
    position=str(positions[0]) if positions else ""
    age=_num(m.get("age",p.get("age")))
    overall=_num(m.get("overall",p.get("overall")))
    first=m.get("firstName") or p.get("firstName") or ""
    last=m.get("lastName") or p.get("lastName") or ""
    name=(str(first)+" "+str(last)).strip() or p.get("name") or "Unknown"
    return {"player":name,"age":age,"overall":overall,"position":position,
            "player_id":p.get("id") or p.get("playerId") or m.get("id")}

def _public_market_get(path, params):
    url=agency.BASE+path
    try:
        r=requests.get(url,headers=agency.H,params=params,timeout=25)
    except requests.RequestException as e:
        raise RuntimeError(f"MFL market API connection failed: {e}") from e
    if r.status_code in (401,403):
        raise RuntimeError("MFL does not permit unauthenticated market access. A working MFL session is required.")
    if r.status_code==429:
        raise RuntimeError("MFL market rate limit reached (429). Try a smaller scan later.")
    if not r.ok:
        raise RuntimeError(f"MFL market endpoint {path} returned HTTP {r.status_code}: {r.text[:180]}")
    return r.json()

def _fetch_pages(path, token, pages, params, progress=None):
    rows=[];seen=set();before=None
    for page in range(pages):
        opts=dict(params)
        if before is not None: opts["beforeListingId"]=before
        data=_public_market_get(path,opts)
        batch=agency.arr(data)
        if not batch:break
        fresh=0
        for rec in batch:
            if not isinstance(rec,dict):continue
            rid=rec.get("listingResourceId") or rec.get("id")
            if rid is None:continue
            if str(rid) in seen:continue
            seen.add(str(rid));rows.append(rec);fresh+=1
        last=batch[-1]
        new_before=last.get("listingResourceId") or last.get("id") if isinstance(last,dict) else None
        if progress: progress(path,page+1,pages,len(rows))
        if not fresh or new_before is None or str(new_before)==str(before):break
        before=new_before
        time.sleep(0.25)
    return rows

def _median(vals):
    return statistics.median(vals)

def scan(listing_pages=12,sales_pages=24,max_age=24,min_discount=15,progress=None):
    # Marketplace listings do not need wallet data; don't refresh a wallet token.
    live=_fetch_pages("/listings",None,listing_pages,
                      {"limit":25,"type":"PLAYER","status":"AVAILABLE","view":"full"},progress)
    # MFL /listings rejects SOLD; use other active asking prices as a
    # clearly labelled comparison, NEVER describe them as realised sales.
    reference=[]
    for x in live:
        if str(x.get("status") or "").upper() not in ("AVAILABLE","ACTIVE"):continue
        info=_player(x)
        price=_num(x.get("price"))
        if price is not None and price>0 and info["overall"] is not None and info["age"] is not None:
            reference.append({**info,"price":price,"listing_id":x.get("listingResourceId") or x.get("id")})
    output=[]
    for x in live:
        if str(x.get("status") or "").upper() not in ("AVAILABLE","ACTIVE"):continue
        info=_player(x);ask=_num(x.get("price"))
        if ask is None or ask<=0 or info["age"] is None or info["age"]>max_age or info["overall"] is None:continue
        comps=[s["price"] for s in reference if s["listing_id"] != (x.get("listingResourceId") or x.get("id")) and s["position"]==info["position"]
               and abs(s["overall"]-info["overall"])<=3 and abs(s["age"]-info["age"])<=3]
        if len(comps)<5:continue
        fair=_median(comps)
        discount=100*(fair-ask)/fair if fair else 0
        if discount<min_discount:continue
        output.append({"Player":info["player"],"Age":int(info["age"]),
                       "Position":info["position"],"OVR":int(info["overall"]),
                       "Asking Price":ask,"Comparable Asking Median":round(fair,2),
                       "Discount %":round(discount,1),"Comparables":len(comps),
                       "Player ID":info["player_id"],
                       "Listing ID":x.get("listingResourceId") or x.get("id")})
    df=pd.DataFrame(output)
    if not df.empty:df=df.sort_values("Discount %",ascending=False).reset_index(drop=True)
    return df,{"listings":len(live),"reference_listings":len(reference),
               "minimum_comparables":5}
