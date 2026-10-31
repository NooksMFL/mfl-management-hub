"""Discoverable roster loading, independent of development analysis."""
import streamlit as st
import wallet_cache_backend as shared

def render(wallet,key):
    if not wallet:return
    import agency_full_sync_ui
    agency_full_sync_ui.render(wallet,key=key+'_entire_agency')
    col1,col2=st.columns([1,2])
    with col1:clicked=st.button('Load / refresh team players',key=key,use_container_width=True)
    with col2:st.caption('Quick roster-list refresh. Use Sync entire agency above to check each player profile and produce a full analysis export.')
    if clicked:
        try:
            with st.spinner('Loading players and clubs from MFL…'):
                result=shared.sync_wallet(wallet,force=True)
            st.session_state['squad_sync_notice']=f'Loaded {result["players"]} player(s) and {result["clubs"]} club(s).'
            st.rerun()
        except Exception as error:
            st.error(f'Could not finish loading from MFL: {error}. Saved players remain available; retry here or use Sync Centre.')
    if st.session_state.get('squad_sync_notice'):st.success(st.session_state.pop('squad_sync_notice'))
