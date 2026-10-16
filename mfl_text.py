"""MFL Text: shared teletext identity and numbered page navigation."""
import base64
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import streamlit as st

PAGES = {"Home":"100", "Grower or Shower":"200", "Agency Development":"201", "Club Development":"202",
         "Squad Builder":"302", "Transfer Window":"303", "Transfer Bargains":"304", "Watchlist":"305",
         "Compare":"400", "Insights":"500", "Sync Centre":"888", "Design Studio":"999"}


@lru_cache(maxsize=1)
def font_url():
    font = Path(__file__).with_name('design-concepts') / 'assets' / 'teletext.ttf'
    return 'data:font/ttf;base64,' + base64.b64encode(font.read_bytes()).decode('ascii')


def apply_theme():
    css = Path(__file__).with_name('mfl_text.css').read_text().replace('TELETEXT_FONT_URL',font_url())
    st.markdown('<style>'+css+'</style>',unsafe_allow_html=True)


def page_link(page,wallet=''):
    params={'page':page}
    if wallet:params['wallet']=wallet
    return '?'+urlencode(params)


def header(page,wallet=''):
    number=PAGES.get(page,'100')
    date=datetime.now(ZoneInfo('Europe/London')).strftime('%a %d %b %Y').upper()
    st.markdown(f'<div class="tt-status"><span>P{number} MFLTEXT {number}</span><span>{date}</span></div>'
        '<div class="tt-masthead">MFL TEXT<span>YOUR FOOTBALL INFORMATION SERVICE</span></div>'
        f'<div class="tt-pagebar"><span>{number} / {escape(page.upper())}</span><span>SEASON 17</span></div>'
        '<nav class="tt-fastext" aria-label="Teletext shortcuts">'+''.join(
            f'<a class="tt-{color}" href="{escape(page_link(name,wallet),quote=True)}" target="_self">{PAGES[name]} {label}</a>'
            for name,label,color in [('Home','HOME','red'),('Squad Builder','SQUADS','green'),('Agency Development','AGENCY','yellow'),('Club Development','CLUBS','cyan')])+'</nav>',unsafe_allow_html=True)


def jump_to_page():
    number=st.session_state.get('tt_page_number','').strip()
    target=next((name for name,code in PAGES.items() if code==number),None)
    if target:
        st.session_state['hub_nav']=target
        st.query_params['page']=target
        st.session_state.pop('tt_page_error',None)
    else:
        st.session_state['tt_page_error']='PAGE NOT FOUND. TRY 100, 201, 202 OR 302.'


def sync_navigation():
    st.query_params['page']=st.session_state['hub_nav']
