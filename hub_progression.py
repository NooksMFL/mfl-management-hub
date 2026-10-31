"""Agency and season progression for the focused three-page Hub."""
import json
import time
from datetime import datetime, timezone

import pandas as pd

import agency_backend as agency
import agency_full_sync as full
import club_backend as club_api
import wallet_cache_backend as shared

FIELDS = ('overall','pace','shooting','passing','dribbling','defense','physical')
LABELS = ('OVR','PAC','SHO','PAS','DRI','DEF','PHY')
SEASONS = {'Season 18':'2026-11-04T00:00:00+00:00','Season 17':'2026-09-22T00:00:00+00:00'}


def job(wallet, key):
    with shared.db() as c:
        row = c.execute('SELECT payload FROM hub_progress_jobs WHERE wallet=? AND job_key=?',(wallet,key)).fetchone()
    return json.loads(row[0]) if row else {}


def save_job(wallet,key,value):
    with shared.db() as c:
        c.execute('INSERT OR REPLACE INTO hub_progress_jobs VALUES(?,?,?)',(wallet,key,json.dumps(value)))


def roster(wallet,owned_only=False):
    rows = shared.roster_rows(wallet)
    if owned_only:
        clubs = {c['name'].casefold() for c in shared.clubs_rows(wallet)}
        rows = [r for r in rows if str(r.get('club') or '').casefold() in clubs]
    return rows


def agency_frame(wallet):
    c=agency.db();agency.init(c);agency.ensure_v2(c)
    rows=c.execute('''SELECT o.*,m.age,m.position,m.club FROM ownership_v65 o
        LEFT JOIN player_meta m ON m.wallet=o.wallet AND m.player_id=o.player_id WHERE o.wallet=?''',(wallet,)).fetchall()
    columns=[d[0] for d in c.execute('SELECT o.*,m.age,m.position,m.club FROM ownership_v65 o LEFT JOIN player_meta m ON 0 LIMIT 0').description]
    c.close()
    if not rows and shared.roster_rows(wallet):
        agency.seed_from_shared(wallet)
        return agency_frame(wallet)
    current={r['player_id']:r for r in roster(wallet)}
    output=[]
    for values in rows:
        r=dict(values) if hasattr(values,'keys') else dict(zip(columns,values))
        if shared._meta_get(wallet,'agency_membership_verified')=='true' and r['player_id'] not in current:
            continue
        p=current.get(r['player_id'],{})
        newer=str(r.get('updated_at') or '')>=str(p.get('cached_at') or '')
        checked=str(r.get('confidence') or '')!='BASELINE PENDING'
        row={'Player ID':r['player_id'],'Player':r['player_name'] if newer else p.get('player_name') or r['player_name'],
             'Club':r.get('club') if newer else p.get('club'),'Age':r.get('age') if newer else p.get('age'),
             'Position':r.get('position') if newer else p.get('position'),
             'Start OVR':r.get('start_ovr') if checked else None,
             'Current OVR':r.get('current_ovr') if newer else p.get('overall'),
             'Tracking from':'Purchase' if r.get('confidence')=='VERIFIED' else 'First record' if r.get('confidence')=='INITIAL HISTORY' else 'Unverified' if checked else 'Not checked',
             'Checked':r.get('updated_at')}
        gains=[]
        for label,short,field in zip(LABELS,('ovr','pac','sho','pas','dri','def','phy'),FIELDS):
            a=r.get('start_'+short) if checked else None
            z=r.get('current_'+short) if newer else p.get(field)
            value=float(z)-float(a) if a is not None and z is not None else None
            row[label+' gain']=value
            if label!='OVR':gains.append(value)
        row['Attribute gain']=sum(gains) if all(v is not None for v in gains) else None
        output.append(row)
    return pd.DataFrame(output)


def season_measure(events,profile,start,previous=None):
    cutoff=pd.to_datetime(start,utc=True).to_pydatetime()
    states=club_api.states(events)
    checked=club_api.todt(profile.get('cached_at'))
    current={f:profile.get(f) for f in FIELDS}
    before=[(d,v) for d,v in states if d<=cutoff]
    if checked and checked<=cutoff:
        before.append((checked,current.copy()))
    baseline=max(before,key=lambda x:x[0]) if before else None
    if baseline:
        baseline_at,base=baseline[0].isoformat(),baseline[1]
    elif previous and previous.get('baseline'):
        baseline_at,base=previous.get('baseline_at'),previous['baseline']
    else:
        baseline_at,base=None,{}
    if states and (not checked or states[-1][0]>=checked):
        current.update({k:v for k,v in states[-1][1].items() if k in FIELDS and v is not None})
    gains={f:float(current[f])-float(base[f]) if current.get(f) is not None and base.get(f) is not None else None for f in FIELDS}
    attrs=[gains[f] for f in FIELDS[1:]]
    return {'baseline':base,'baseline_at':baseline_at,'current':current,'gains':gains,
            'attribute_gain':sum(attrs) if all(v is not None for v in attrs) else None}


def club_frame(wallet,start):
    with shared.db() as c:
        saved={(r['player_id'],r['club']):json.loads(r['payload']) for r in c.execute(
            'SELECT player_id,club,payload FROM hub_club_progress WHERE wallet=? AND season_start=?',(wallet,start))}
    output=[]
    for p in roster(wallet,True):
        record=saved.get((p['player_id'],p['club']),{})
        row={'Player ID':p['player_id'],'Player':p['player_name'],'Club':p['club'],'Position':p['position'],'Age':p['age'],
             'Start OVR':record.get('baseline',{}).get('overall'),'Current OVR':record.get('current',{}).get('overall',p['overall']),
             'Attribute gain':record.get('attribute_gain'),'Checked':record.get('checked_at')}
        for label,field in zip(LABELS,FIELDS):row[label+' gain']=record.get('gains',{}).get(field)
        output.append(row)
    return pd.DataFrame(output)


def update(wallet,kind,start='',progress=None,client=None,delay=.25):
    key=kind+':'+start
    state=job(wallet,key)
    if state.get('retry_until',0)>time.time():return state
    rows=roster(wallet,kind=='club')
    ids={r['player_id'] for r in rows}
    if state.get('status') not in ('paused','running'):state={'done':[],'started_at':full.now()}
    done=set(state['done']) & ids
    client=client or full.Client()
    state.update(status='running',error=None,total=len(rows))
    save_job(wallet,key,state)
    try:
        for p in rows:
            pid=p['player_id']
            if pid in done:continue
            if progress:progress(len(done),len(rows),p['player_name'])
            if kind=='agency':
                analysis=agency.analyse(pid,wallet,client)
                agency.save_analysis(wallet,analysis)
            else:
                events=full.items(client.get(f'/players/{pid}/experiences/history'),'history')
                with shared.db() as c:
                    previous=c.execute('SELECT payload FROM hub_club_progress WHERE wallet=? AND player_id=? AND club=? AND season_start=?',(wallet,pid,p['club'],start)).fetchone()
                record=season_measure(events,p,start,json.loads(previous[0]) if previous else None)
                record['checked_at']=full.now()
                with shared.db() as c:
                    c.execute('INSERT OR REPLACE INTO hub_club_progress VALUES(?,?,?,?,?,?)',(wallet,pid,p['club'],start,json.dumps(record),record['checked_at']))
            done.add(pid)
            state.update(done=sorted(done),checked_at=full.now())
            save_job(wallet,key,state)
            if progress:progress(len(done),len(rows),p['player_name'])
            if delay:time.sleep(delay)
        state.update(status='complete',checked_at=full.now())
    except Exception as exc:
        state.update(status='paused',error=str(exc) if isinstance(exc,full.SyncError) else 'MFL could not finish the update. Your progress is saved.')
        if getattr(exc,'retry_after',0):state['retry_until']=time.time()+exc.retry_after
    save_job(wallet,key,state)
    return state
