"""MFL Management Hub: bargains, agency progression and club progression."""
from __future__ import annotations

import base64
from datetime import datetime
import html
import os
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from streamlit_js_eval import get_local_storage, set_local_storage, streamlit_js_eval

import agency_full_sync as full
import agency_full_sync_ui as sync_ui
import browser_persistence as persistence
import hub_progression as progression
import wallet_cache_backend as shared
import wallet_connection

ROOT=Path(__file__).resolve().parent
PAGES=['Agency progression','Club progression','Transfer Bargains','Squad analyser']
ALIASES={'Agency Development':'Agency progression','Club Development':'Club progression'}

st.set_page_config(page_title='MFL Management Hub',page_icon='⚽',layout='wide',initial_sidebar_state='expanded')
try:
    if st.secrets.get('MFL_REFRESH_TOKEN') and not os.getenv('MFL_REFRESH_TOKEN'):
        os.environ['MFL_REFRESH_TOKEN']=st.secrets['MFL_REFRESH_TOKEN']
except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):
    pass

regular=base64.b64encode((ROOT/'assets/hub-fonts/hub-regular.ttf').read_bytes()).decode('ascii')
bold=base64.b64encode((ROOT/'assets/hub-fonts/hub-semibold.ttf').read_bytes()).decode('ascii')
st.markdown('<style>@font-face{font-family:"Hub Sans";src:url(data:font/ttf;base64,'+regular+') format("truetype");font-weight:400;font-display:swap}@font-face{font-family:"Hub Sans";src:url(data:font/ttf;base64,'+bold+') format("truetype");font-weight:600 900;font-display:swap}'+(ROOT/'hub.css').read_text()+'</style>',unsafe_allow_html=True)

remembered=get_local_storage('mfl_hub_last_wallet',component_key='hub_last_wallet')
wallet_connection.restore_wallet(st.session_state,st.query_params.get('wallet',''),remembered)
requested=ALIASES.get(st.query_params.get('page',''),st.query_params.get('page',''))
if requested not in PAGES:requested=PAGES[0]
if 'hub_page' not in st.session_state or st.session_state['hub_page'] not in PAGES:
    st.session_state['hub_page']=requested

def navigate():
    st.query_params['page']=st.session_state['hub_page']

with st.sidebar:
    st.markdown('<div class="hub-brand"><div class="hub-brand-mark">MH</div><div><strong>Management Hub</strong><small>MFL</small></div></div>',unsafe_allow_html=True)
    page=st.radio('Navigate',PAGES,key='hub_page',on_change=navigate,label_visibility='collapsed')
    st.divider()
    st.caption('YOUR WALLET')
    with st.form('wallet_form'):
        address=st.text_input('Wallet address',value=st.session_state.get('wallet',''),placeholder='0x…',label_visibility='collapsed',key='hub_wallet_input')
        if st.form_submit_button('Save wallet',use_container_width=True):
            if wallet_connection.valid_address(address):
                st.session_state['wallet']=address.strip().lower()
                st.session_state['wallet_forgotten']=False
                st.query_params['wallet']=st.session_state['wallet']
                st.rerun()
            else:st.error('Enter a valid MFL wallet address.')
    if st.session_state.get('wallet'):st.caption('Wallet saved')

wallet=st.session_state.get('wallet','')
st.query_params['page']=page
if wallet:
    st.query_params['wallet']=wallet
    set_local_storage('mfl_hub_last_wallet',wallet,component_key='hub_save_wallet')
    # An explicit ready flag separates an empty browser backup from a component
    # that has not replied yet. Never overwrite a backup during startup.
    storage_key=f'mfl_hub_wallet_{wallet[2:]}'
    backup_reply=streamlit_js_eval(js_expressions="({ready:true,value:localStorage.getItem('"+storage_key+"')})",key='hub_safe_restore_'+wallet[-8:])
    backup_ready=isinstance(backup_reply,dict) and backup_reply.get('ready') is True
    if backup_ready and not st.session_state.get('hub_restored_'+wallet):
        backup=backup_reply.get('value')
        if backup and not shared.roster_rows(wallet) and not full.state(wallet):
            try:persistence.restore_wallet(backup,wallet)
            except Exception:
                st.session_state['hub_restore_failed']=True
        st.session_state['hub_restored_'+wallet]=True
    if st.session_state.get('hub_restore_failed'):
        st.error('Your browser backup could not be restored. It has been kept unchanged.')

head,date=st.columns([4,1])
with head:st.title(page)
with date:st.markdown('<div class="hub-date">'+datetime.now(ZoneInfo('Europe/London')).strftime('%d %B %Y')+'</div>',unsafe_allow_html=True)
if wallet:sync_ui.render(wallet,key='hub_sync')
elif page!='Transfer Bargains':st.info('Save your wallet on the left to load your players.')


def number(value,decimals=0):
    return f'{value:,.{decimals}f}' if pd.notna(value) else '—'


def player_filter(frame,key):
    if frame.empty:return frame
    search_col,club_col=st.columns([2,1])
    with search_col:search=st.text_input('Search players',placeholder='Search players',key=key+'_search',label_visibility='collapsed')
    names=sorted(frame['Club'].dropna().unique())
    with club_col:club=st.selectbox('Club',['All clubs']+names,key=key+'_club',label_visibility='collapsed')
    result=frame.copy()
    if club!='All clubs':result=result[result.Club==club]
    if search:result=result[result.Player.fillna('').str.contains(search,case=False,regex=False)]
    return result


def show_players(frame,key):
    if frame.empty:
        st.info('No players match your selection.')
        return
    frame=frame.copy()
    frame['Photo']=frame['Player ID'].map(lambda p:f'https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(p)}/photo.webp')
    frame['MFL']=frame['Player ID'].map(lambda p:f'https://app.playmfl.com/players/{int(p)}')
    frame['Club']=frame['Club'].fillna('No club recorded')
    if 'OVR gain' in frame:frame=frame.sort_values('OVR gain',ascending=False,na_position='last')
    columns=['Photo','Player','Club','Position','Age','Start OVR','Current OVR','OVR gain','Attribute gain']
    st.dataframe(frame.reindex(columns=columns),hide_index=True,width='stretch',row_height=54,height=min(650,55+len(frame)*54),
                 column_config={'Photo':st.column_config.ImageColumn('Player',width='small'),
                                'OVR gain':st.column_config.NumberColumn('OVR gained',format='%+.0f'),
                                'Attribute gain':st.column_config.NumberColumn('Attributes gained',format='%+.0f')})
    st.download_button('Download progression CSV',frame.drop(columns=['Photo']).to_csv(index=False).encode('utf-8-sig'),
                       key=key+'_download',file_name='mfl_'+key+'_progression.csv',mime='text/csv')
    with st.expander('Attribute changes'):
        attributes=['Player','Club']+[label+' gain' for label in progression.LABELS[1:]]
        st.dataframe(frame.reindex(columns=attributes),hide_index=True,width='stretch')
        if 'Tracking from' in frame:st.caption('Purchase uses your recorded purchase date. First record uses the earliest available player history.')


def update_button(kind,start=''):
    state=progression.job(wallet,kind+':'+start)
    label='Continue update' if state.get('status') in ('paused','running') else 'Update progression'
    if st.button(label,key='update_'+kind,type='primary',disabled=state.get('retry_until',0)>time.time()):
        if not shared.roster_rows(wallet):st.info('Sync your agency first.')
        else:
            bar=st.progress(0,text='Updating progression…')
            result=progression.update(wallet,kind,start,progress=lambda done,total,name:bar.progress(min(1.0,done/total) if total else 0,text=f'Updating progression · {done} of {total}'))
            bar.empty()
            st.rerun()
    if state.get('status')=='paused':
        st.warning('Progression update paused. Your progress is saved.')
        with st.expander('Update help'):st.write(state.get('error'))
    elif state.get('status')=='complete':st.caption('Progression updated '+sync_ui.short_date(state.get('checked_at')))


if page=='Agency progression' and wallet:
    frame=progression.agency_frame(wallet)
    if not frame.empty:
        import squad_analysis
        latest,_=squad_analysis.snapshot(wallet)
        by_id={p['player_id']:p for p in latest}
        show_inactive=st.toggle('Show retired / no club',value=False,key='agency_show_inactive')
        active_mask=frame.apply(lambda r:squad_analysis.is_active(by_id.get(r['Player ID'],{'club':r['Club']})),axis=1)
        excluded=int((~active_mask).sum())
        if excluded:st.caption(f'{excluded} retired or no-club players hidden. Their saved records are kept.')
        if not show_inactive:frame=frame[active_mask].copy()
    if frame.empty:st.info('No active players to show. Continue your existing sync, or show retired / no-club players.')
    else:
        columns=st.columns(3)
        gains=pd.to_numeric(frame['OVR gain'],errors='coerce')
        columns[0].metric('Players',len(frame))
        columns[1].metric('OVR gained',number(gains.sum(min_count=1)))
        columns[2].metric('Players improved',int((gains>0).sum()))
        st.write('')
        update_button('agency')
        pending=int(frame['OVR gain'].isna().sum())
        if pending:st.caption(f'{pending} players need a progression update. Missing changes show as —.')
        show_players(player_filter(frame,'agency'),'agency')

elif page=='Club progression' and wallet:
    season=st.selectbox('Season',list(progression.SEASONS),key='club_season')
    start=progression.SEASONS[season]
    frame=progression.club_frame(wallet,start)
    if frame.empty:st.info('Sync your agency to load players at your clubs.')
    else:
        cols=st.columns(3)
        gains=pd.to_numeric(frame['OVR gain'],errors='coerce')
        cols[0].metric('Clubs',frame.Club.nunique())
        cols[1].metric('Players',len(frame))
        cols[2].metric('OVR gained',number(gains.sum(min_count=1)))
        st.write('')
        update_button('club',start)
        view=player_filter(frame,'clubs')
        summary=view.groupby('Club').agg(Players=('Player ID','count'),Measured=('OVR gain','count'),OVR_gained=('OVR gain',lambda x:x.sum(min_count=1)),Attributes_gained=('Attribute gain',lambda x:x.sum(min_count=1))).reset_index().rename(columns={'OVR_gained':'OVR gained','Attributes_gained':'Attributes gained'})
        st.subheader('Club overview')
        st.dataframe(summary.sort_values('OVR gained',ascending=False,na_position='last'),hide_index=True,width='stretch')
        st.subheader('Players')
        show_players(view,'clubs')
        with st.expander('Season dates'):
            st.write(f'{season} is measured from {datetime.fromisoformat(start).strftime("%d %B %Y")}. Players without starting stats show —.')

elif page=='Squad analyser' and wallet:
    import squad_analysis_ui
    squad_analysis_ui.render(wallet)

elif page=='Transfer Bargains':
    import transfer_bargains_backend as bargains
    with st.container(border=True):
        age_col,saving_col,scan_col=st.columns([1,1,1])
        with age_col:max_age=st.number_input('Maximum age',min_value=16,max_value=40,value=24,step=1)
        with saving_col:discount=st.slider('Minimum saving',min_value=5,max_value=60,value=15,step=5,format='%d%%')
        with scan_col:depth=st.selectbox('Search size',['Quick','More players'])
        search=st.button('Find bargains',type='primary',key='find_bargains')
    st.caption('Compares current asking prices with similar listed players. These are asking prices, not completed sales.')
    if search:
        bar=st.progress(0,text='Checking the market…')
        pages=6 if depth=='Quick' else 16
        try:
            result,stats=bargains.scan(listing_pages=pages,sales_pages=pages,max_age=max_age,min_discount=discount,
                                       progress=lambda path,done,total,count:bar.progress(min(1.0,done/total),text=f'Checking the market · {count} listings'))
            st.session_state['hub_bargains']=result
            st.session_state['hub_bargains_checked']=stats['listings']
        except Exception:
            st.error('The market could not be refreshed. Try again shortly.')
        bar.empty()
    result=st.session_state.get('hub_bargains')
    if result is None:st.info('Choose your filters, then select Find bargains.')
    elif result.empty:st.info('No matches this time. Try a lower minimum saving or a larger search.')
    else:
        left,right=st.columns(2)
        left.metric('Players found',len(result))
        right.metric('Largest saving',number(result['Discount %'].max(),1)+'%')
        display=result.rename(columns={'Comparable Asking Median':'Similar asking price','Discount %':'Saving %'})
        st.dataframe(display.drop(columns=['Listing ID'],errors='ignore'),hide_index=True,width='stretch')
        st.download_button('Download bargains CSV',result.to_csv(index=False).encode('utf-8-sig'),'mfl_bargains.csv','text/csv')

if wallet and backup_ready and not st.session_state.get('hub_restore_failed'):
    try:
        backup=persistence.dump_wallet(wallet)
        if backup and backup['signature']!=st.session_state.get('hub_backup_signature'):
            set_local_storage(f'mfl_hub_wallet_{wallet[2:]}',backup['value'],component_key='hub_backup_'+backup['signature'])
            st.session_state['hub_backup_signature']=backup['signature']
    except Exception:
        pass
