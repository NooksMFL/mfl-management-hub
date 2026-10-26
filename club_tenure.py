"""Explicit club-joining baselines, kept separate from whole-season caches."""
import json
import math
from datetime import datetime, timezone
import time
import pandas as pd
import streamlit as st
import wallet_cache_backend as shared
import club_backend as club_api

FIELDS=('overall','pace','shooting','passing','dribbling','defense','physical')
LABELS={'overall':'OVR','pace':'PAC','shooting':'SHO','passing':'PAS','dribbling':'DRI','defense':'DEF','physical':'PHY'}

def db():
    c=shared.db()
    c.execute('''CREATE TABLE IF NOT EXISTS club_tenure(
      wallet TEXT,player_id INTEGER,club TEXT,joined_at TEXT,baseline_at TEXT,latest_at TEXT,
      baseline_json TEXT,current_json TEXT,checked_at TEXT,status TEXT,
      PRIMARY KEY(wallet,player_id,club))''');c.commit();return c

def track(wallet,player_id,club,joined_at):
    stamp=pd.to_datetime(joined_at,utc=True).isoformat()
    with db() as c:
        previous=c.execute('SELECT joined_at FROM club_tenure WHERE wallet=? AND player_id=? AND club=?',(wallet.lower(),int(player_id),club)).fetchone()
        if previous and previous['joined_at']==stamp:return
        c.execute('INSERT OR REPLACE INTO club_tenure(wallet,player_id,club,joined_at,status) VALUES(?,?,?,?,?)',(wallet.lower(),int(player_id),club,stamp,'Joining date entered; refresh history'))

def tracked(wallet):
    with db() as c:return [dict(r) for r in c.execute('SELECT * FROM club_tenure WHERE wallet=?',(wallet.lower(),))]

def measure(events,joined_at):
    states=club_api.states(events)
    if not states:return {'status':'No progression history returned'}
    cutoff=pd.to_datetime(joined_at,utc=True).to_pydatetime()
    prior=[s for s in states if s[0]<=cutoff]
    if not prior:return {'status':'Baseline unavailable: no history at or before joining'}
    baseline=prior[-1];latest=states[-1]
    return {'status':'Tracked','baseline_at':baseline[0].isoformat(),'latest_at':latest[0].isoformat(),
            'baseline_json':json.dumps(baseline[1]),'current_json':json.dumps(latest[1])}

def changes(record):
    try:start=json.loads(record.get('baseline_json') or '{}');current=json.loads(record.get('current_json') or '{}')
    except (ValueError,TypeError):start={};current={}
    result={}
    for key in FIELDS:
        try:
            before=float(start[key]);after=float(current[key]);value=after-before
            result[key]=value if math.isfinite(value) else None
        except (KeyError,TypeError,ValueError):result[key]=None
    return result

def refresh(wallet,players,limit=8):
    active={(int(p['player_id']),p['club']) for p in players if p.get('club')}
    records=[r for r in tracked(wallet) if (int(r['player_id']),r['club']) in active and pd.to_datetime(r['joined_at'],utc=True).to_pydatetime()<=datetime.now(timezone.utc)]
    records.sort(key=lambda r:r.get('checked_at') or '')
    processed=0;errors=[]
    for row in records[:limit]:
        if pd.to_datetime(row['joined_at'],utc=True).to_pydatetime()>datetime.now(timezone.utc):continue
        try:
            update=measure(club_api.events(row['player_id']),row['joined_at'])
            with db() as c:
                c.execute('''UPDATE club_tenure SET baseline_at=?,latest_at=?,baseline_json=?,current_json=?,checked_at=?,status=?
                    WHERE wallet=? AND player_id=? AND club=?''',(update.get('baseline_at'),update.get('latest_at'),update.get('baseline_json'),update.get('current_json'),datetime.now(timezone.utc).isoformat(),update['status'],wallet.lower(),row['player_id'],row['club']))
            processed+=1
        except Exception as error:
            errors.append((row['player_id'],str(error)))
            if '429' in str(error) or 'RATE_LIMIT' in str(error):break
        if processed+len(errors)<min(limit,len(records)):time.sleep(club_api.RATE_DELAY_SECONDS)
    return processed,errors

def render(wallet):
    st.subheader('Progression since joining my club')
    st.caption('This view starts at each player’s entered club-joining date. Whole-season gains and agency-ownership gains use different baselines and are not added to these totals.')
    roster=shared.roster_rows(wallet)
    from squad_builder import has_current_club
    roster=[r for r in roster if has_current_club(r.get('club'))]
    if not roster:
        st.info('Load / refresh team players in Squad Builder or on Home first.');return
    names=sorted({r['club'] for r in roster})
    chosen=st.selectbox('Club to track',['All my clubs']+names,key='tenure_club');players=[p for p in roster if chosen=='All my clubs' or p['club']==chosen]
    lookup={int(p['player_id']):p for p in players}
    records=[r for r in tracked(wallet) if int(r['player_id']) in lookup and r['club']==lookup[int(r['player_id'])]['club']]
    good=[r for r in records if r.get('status')=='Tracked']
    a,b,c=st.columns(3)
    a.metric('Players with joining dates',f'{len(records)}/{len(players)}')
    b.metric('Measured baselines',len(good))
    deltas=[changes(r) for r in good]
    known=[d['overall'] for d in deltas if d['overall'] is not None]
    c.metric('OVR change since joining',f'{sum(known):+g}' if known else '—')
    st.caption(f'OVR coverage: {len(known)}/{len(players)} current players. Players without a joining date or a valid baseline are excluded, not counted as zero.')
    st.info('Joining dates are not verified by the saved roster. Enter the actual arrival date below; no season-start or agency-acquisition date is substituted. For a player who rejoined, use the current spell’s arrival date.')
    with st.expander('Set club-joining dates',expanded=not records):
        choices={f'{r["player_name"]} · {r["player_id"]}':r for r in players}
        selected=st.multiselect('Players joining on this date',list(choices),key=f'tenure_players_{chosen}')
        joined=st.date_input('Actual joining date',key=f'tenure_joined_{chosen}')
        st.caption('Date-only entries use 00:00 UTC. The baseline uses the last known attribute snapshot at or before that time. Entering a different date resets that player’s tracked baseline.')
        if st.button('Save joining dates',key='tenure_save'):
            if not selected:st.warning('Select at least one player.')
            else:
                for label in selected:track(wallet,choices[label]['player_id'],choices[label]['club'],joined)
                st.rerun()
    if records and st.button('Refresh club-joining progression (next 8)',type='primary',key='tenure_refresh'):
        with st.spinner('Reading player progression histories…'):
            done,errors=refresh(wallet,players)
        st.session_state['tenure_notice']=f'Refreshed {done} player(s). '+(f'{len(errors)} failed; saved data retained. Retry later.' if errors else '')
        st.rerun()
    if st.session_state.get('tenure_notice'):st.info(st.session_state.pop('tenure_notice'))
    if records:
        output=[]
        for r in records:
            p=lookup[int(r['player_id'])];d=changes(r)
            output.append({'Player':p['player_name'],'Player ID':r['player_id'],'Club':r['club'],'Joined at UTC':r['joined_at'],
                **{f'{LABELS[k]} change':v for k,v in d.items()},'Baseline snapshot':r['baseline_at'],'Latest snapshot':r['latest_at'],'Last checked':r['checked_at'],'Status':r['status']})
        frame=pd.DataFrame(output)
        import ranked_table
        st.markdown('**Club summary — since joining**')
        summary=frame.groupby('Club',dropna=False).agg(Tracked=('Player ID','count'),Measured=('OVR change','count'),OVR_change=('OVR change',lambda x:x.sum(min_count=1))).reset_index().rename(columns={'OVR_change':'OVR change'})
        ranked_table.render(summary,sort_by='OVR change',height=min(300,90+50*len(summary)))
        st.markdown('**Individual players — since joining**')
        ranked_table.render(frame,sort_by="OVR change",height=500)
        st.download_button('Download club-joining progression CSV',frame.to_csv(index=False).encode('utf-8-sig'),file_name='mfl_since_club_joining.csv',mime='text/csv')
    else:st.info('Choose players and save their actual joining dates to start tracking this club.')
