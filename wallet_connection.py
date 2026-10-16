"""Public-wallet selection and optional Dapper authentication for the UI."""
import os
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_component = components.declare_component('mfl_dapper_wallet',path=str(Path(__file__).with_name('dapper_component')))


def valid_address(value):
    return isinstance(value,str) and bool(re.fullmatch(r'0x[0-9a-fA-F]{16}',value.strip()))


def restore_wallet(session, query_wallet, remembered):
    """Browser storage arrives asynchronously; retry restoration after first render."""
    if 'wallet' not in session:
        candidate=query_wallet if valid_address(query_wallet) else remembered
        session['wallet']=candidate.strip().lower() if valid_address(candidate) else ''
    elif not session['wallet'] and not session.get('wallet_forgotten'):
        candidate=query_wallet if valid_address(query_wallet) else remembered
        if valid_address(candidate):
            session['wallet']=candidate.strip().lower()
            session['edit_wallet']=False


def login_enabled():
    try:
        value=st.secrets.get('DAPPER_LOGIN_ENABLED',os.getenv('DAPPER_LOGIN_ENABLED','false'))
    except Exception:
        value=os.getenv('DAPPER_LOGIN_ENABLED','false')
    return value is True or str(value).lower()=='true'


def connect_widget():
    result=_component(current_wallet=st.session_state.get('wallet',''),
                      ignore_restore=bool(st.session_state.get('wallet_forgotten')),
                      enabled=login_enabled(),default=None,key='dapper_connection')
    if not isinstance(result,dict) or not isinstance(result.get('event_id'),str):
        return
    if st.session_state.get('wallet_event_seen')==result['event_id']:
        return
    st.session_state['wallet_event_seen']=result['event_id']
    action=result.get('action')
    if action=='forget':
        st.session_state['wallet']=''
        st.session_state['wallet_forgotten']=True
        st.session_state['edit_wallet']=True
        st.query_params.pop('wallet',None)
        st.rerun()
    elif action in ('connected','restore') and valid_address(result.get('address')):
        # Restoring a remembered watch address must never replace an explicit wallet.
        if action=='restore' and (st.session_state.get('wallet') or st.session_state.get('wallet_forgotten')):
            return
        if action=='connected' and not login_enabled():
            return
        st.session_state['wallet']=result['address'].strip().lower()
        st.session_state['wallet_forgotten']=False
        st.session_state['edit_wallet']=False
        st.query_params['wallet']=st.session_state['wallet']
        st.rerun()
