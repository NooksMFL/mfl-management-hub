"""Simple sync control for the focused Management Hub."""
import math
import time
from datetime import datetime

import streamlit as st

import agency_full_sync as full
import wallet_cache_backend as shared


def short_date(value):
    try:return datetime.fromisoformat(value).strftime('%d %b, %H:%M')
    except (ValueError,TypeError):return 'Not updated yet'


def render(wallet,key):
    if not wallet:return
    run=full.state(wallet)
    paused=run.get('status') in ('paused','running')
    waiting=run.get('retry_until',0)>time.time()
    with st.container(border=True):
        info,action=st.columns([3,1])
        with info:
            st.markdown('**Agency data**')
            completed=shared._meta_get(wallet,'agency_full_sync_completed_at')
            st.caption('Updated '+short_date(completed) if completed else 'Sync your agency to load your players.')
        with action:
            clicked=st.button('Continue sync' if paused else 'Sync entire agency',type='primary',key=key,width='stretch',disabled=waiting)
        if clicked:
            bar=st.progress(0,text='Finding your players…')
            def progress(done,total,message):
                bar.progress(min(1.0,done/total) if total else 0,text=f'Updating players · {done} of {total}' if total else 'Finding your players…')
            try:result=full.sync(wallet,progress=progress)
            except Exception:st.error('The update stopped. Your saved players are safe. Choose Continue sync to try again.')
            else:
                if result.get('busy'):st.info('An update is already running. If it was interrupted, try again in two minutes.')
                else:st.rerun()
        if run.get('status')=='complete':
            st.caption(f"All {run.get('checked',0)} players updated · {len(run.get('clubs') or [])} clubs")
            if run.get('unverified_clubs') or run.get('missing_squad_fields'):
                st.warning('Some player details were unavailable. They are marked in the download.')
        elif run.get('status')=='paused':
            if run.get('ids') is None:st.warning('MFL could not load your player list yet. Your saved players are unchanged.')
            else:st.warning(f"Update paused · {run.get('checked',0)} of {len(run.get('ids') or [])} players checked. Your progress is saved.")
        if waiting:st.caption(f'Try again in about {max(1,math.ceil((run["retry_until"]-time.time())/60))} minutes.')
        if completed:
            export=full.export_frame(wallet)
            st.download_button('Download agency CSV',export.to_csv(index=False).encode('utf-8-sig'),
                               file_name='mfl_full_agency.csv',mime='text/csv',key=key+'_csv')
        if run.get('status') in ('paused','running'):
            with st.expander('Sync help'):
                st.write(run.get('error') or 'A previous update may have been interrupted.')
                st.caption('Starting again checks the agency list afresh. Your last completed update stays available.')
                if st.button('Start again',key=key+'_restart',disabled=waiting):
                    full.sync(wallet,restart=True)
                    st.rerun()
