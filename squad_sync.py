"""Discoverable roster loading, independent of development analysis."""
import streamlit as st
import wallet_cache_backend as shared

def render(wallet,key):
    if not wallet:return
    col1,col2=st.columns([1,2])
    with col1:clicked=st.button('Load / refresh team players',key=key,type='primary',use_container_width=True)
    with col2:st.caption('Loads your agency roster and owned-club list. No need to visit Club Development first. Club progression has separate since-joining and whole-season views.')
    if clicked:
        try:
            with st.spinner('Loading players and clubs from MFL…'):
                result=shared.sync_wallet(wallet,force=True)
            st.session_state['squad_sync_notice']=f'Loaded {result["players"]} player(s) and {result["clubs"]} club(s).'
            st.rerun()
        except Exception as error:
            st.error(f'Could not finish loading from MFL: {error}. Saved players remain available; retry here or use Sync Centre.')
    if st.session_state.get('squad_sync_notice'):st.success(st.session_state.pop('squad_sync_notice'))
