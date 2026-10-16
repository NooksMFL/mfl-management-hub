"""Agency estimates based on comparable active asks, never realised sales."""
import json
import math
import re
import sqlite3
import statistics
import time
from datetime import datetime, timezone

import requests
import agency_backend as agency
from squad_builder import has_current_club

DB = 'valuation_market_cache.db'
MIN_COMPARABLES = 5


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def positions(value):
    if isinstance(value, list):
        value = ' / '.join(str(p) for p in value)
    aliases = {'LWB':'LB', 'RWB':'RB', 'DM':'CDM', 'AM':'CAM', 'LCM':'CM', 'RCM':'CM'}
    known = {'GK','LB','CB','RB','CDM','CM','LM','RM','CAM','LW','RW','ST','CF','SS','LF','RF'}
    return {aliases.get(p,p) for p in re.findall(r'[A-Z]+',str(value).upper()) if aliases.get(p,p) in known}


def normalize_listings(records):
    result, seen = [], set()
    for record in records:
        if not isinstance(record,dict) or str(record.get('status','')).upper() not in ('AVAILABLE','ACTIVE'):
            continue
        player = record.get('player') or {}
        if not isinstance(player,dict):
            continue
        meta = player.get('metadata') or {}
        if not isinstance(meta,dict):
            meta = {}
        pid = player.get('id') or player.get('playerId') or meta.get('id')
        if pid is None or str(pid) in seen:
            continue
        price = record.get('price')
        currency = record.get('currency') or record.get('priceCurrency')
        if isinstance(price,dict):
            currency = price.get('currency') or currency
            price = price.get('amount')
        price = number(price)
        age = number(meta.get('age',player.get('age')))
        ovr = number(meta.get('overall',player.get('overall')))
        pos = meta.get('positions') or player.get('positions')
        if price is None or price <= 0 or age is None or age <= 0 or ovr is None or not positions(pos):
            continue
        seen.add(str(pid))
        name = player.get('name') or meta.get('name') or ' '.join(str(meta.get(k) or player.get(k) or '') for k in ('firstName','lastName')).strip()
        result.append({'player_id':str(pid),'player':name or f'Player {pid}', 'age':age,'overall':ovr,
                       'position':' / '.join(sorted(positions(pos))), 'price':price,
                       'currency':str(currency).upper() if isinstance(currency,str) and currency.strip() else 'MARKET UNITS',
                       'listing_id':str(record.get('listingResourceId') or record.get('id') or '')})
    return result


def fetch_market(pages=12, progress=None):
    rows, seen = [], set()
    before = None
    for page in range(pages):
        params = {'limit':25,'type':'PLAYER','status':'AVAILABLE','view':'full'}
        if before is not None:
            params['beforeListingId'] = before
        try:
            response = requests.get(agency.BASE+'/listings',headers=agency.H,params=params,timeout=25)
        except requests.RequestException as exc:
            raise RuntimeError('Could not connect to the MFL market. Your previous saved snapshot has been kept.') from exc
        if not response.ok:
            raise RuntimeError(f'MFL market returned HTTP {response.status_code}. Your previous saved snapshot has been kept.')
        try:
            batch = agency.arr(response.json())
        except ValueError as exc:
            raise RuntimeError('MFL returned an unreadable market response. Previous snapshot kept.') from exc
        if not batch:
            break
        fresh = []
        for row in batch:
            if not isinstance(row,dict):
                continue
            identity = row.get('listingResourceId') or row.get('id')
            if identity is not None and str(identity) not in seen:
                seen.add(str(identity));fresh.append(row)
        if not fresh:
            break
        rows.extend(fresh)
        if progress:
            progress(page+1,pages,len(rows))
        cursor = batch[-1].get('listingResourceId') or batch[-1].get('id') if isinstance(batch[-1],dict) else None
        if cursor is None or str(cursor)==str(before):
            break
        before = cursor
        if page+1<pages:
            time.sleep(0.2)
    normalized = normalize_listings(rows)
    if not normalized:
        raise RuntimeError('No usable active player listings were returned. Previous snapshot kept.')
    snapshot = {'captured_at':datetime.now(timezone.utc).isoformat(), 'listings':normalized,
                'records_scanned':len(rows), 'pages_requested':pages}
    with sqlite3.connect(DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS market_snapshot(id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
        conn.execute('INSERT OR REPLACE INTO market_snapshot VALUES(1,?)',(json.dumps(snapshot,allow_nan=False),))
    return snapshot


def load_market():
    with sqlite3.connect(DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS market_snapshot(id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
        row = conn.execute('SELECT payload FROM market_snapshot WHERE id=1').fetchone()
    return json.loads(row[0]) if row else None


def percentile(values, fraction):
    values=sorted(values)
    index=(len(values)-1)*fraction
    low=int(index);high=min(low+1,len(values)-1)
    return values[low]+(values[high]-values[low])*(index-low)


def value_agency(records, listings, currency):
    """Keep every owned player visible; unpriced values remain None, not zero."""
    owned_ids={str(r['player_id']) for r in records}
    reference=[p for p in listings if p['currency']==currency and str(p['player_id']) not in owned_ids]
    output, evidence, seen = [], {}, set()
    for record in records:
        pid=str(record['player_id'])
        if pid in seen:
            continue
        seen.add(pid)
        age,ovr=number(record.get('age')),number(record.get('current_ovr'))
        pos=positions(record.get('position'))
        row={'Player ID':pid,'Player':record.get('player') or f'Player {pid}', 'Age':age,
             'Positions':record.get('position'), 'OVR':ovr,'Current club':record.get('club'),
             'Estimate':None,'Lower ask':None,'Upper ask':None,'Comparables':0,
             'Match':'Unpriced','Status':'Insufficient comparables','Currency':currency}
        if not has_current_club(record.get('club')):
            row['Status']='Retired / no current club'
        elif age is None or age<=0 or ovr is None or not pos:
            row['Status']='Missing age, rating or position'
        else:
            for tolerance, label in [(3,'Tight'),(5,'Broader')]:
                comps=[p for p in reference if abs(p['overall']-ovr)<=tolerance and abs(p['age']-age)<=tolerance
                       and positions(p['position']) & pos]
                if len(comps)>=MIN_COMPARABLES:
                    prices=[p['price'] for p in comps]
                    row.update({'Estimate':round(statistics.median(prices),2),
                                'Lower ask':round(percentile(prices,.25),2),'Upper ask':round(percentile(prices,.75),2),
                                'Comparables':len(comps),'Match':label,'Status':'Estimated from active asks'})
                    evidence[pid]=comps
                    break
        output.append(row)
    return output,evidence
