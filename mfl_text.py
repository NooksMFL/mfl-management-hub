"""MFL Management Hub: shared Windows 95 identity and numbered page navigation."""
import base64
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import streamlit as st

PAGES = {"Home":"100", "Grower or Shower":"200", "Agency Development":"201", "Club Development":"202",
         "Squad Builder":"302", "Transfer Window":"303", "Transfer Bargains":"304", "Watchlist":"305", "Agency / Player Valuation":"306",
         "Compare":"400", "Insights":"500", "Sync Centre":"888", "Design Studio":"999"}


@lru_cache(maxsize=1)
def font_url():
    font = Path(__file__).with_name('design-concepts') / 'assets' / 'teletext.ttf'
    return 'data:font/ttf;base64,' + base64.b64encode(font.read_bytes()).decode('ascii')


@lru_cache(maxsize=2)
def read_font_url(bold=False):
    filename='sans-bold.ttf' if bold else 'sans.ttf'
    font=Path(__file__).with_name('design-concepts') / 'assets' / filename
    return 'data:font/ttf;base64,'+base64.b64encode(font.read_bytes()).decode('ascii')


def apply_theme():
    css = Path(__file__).with_name('win95.css').read_text().replace('TELETEXT_FONT_URL',font_url()).replace('READ_FONT_URL',read_font_url()).replace('BOLD_FONT_URL',read_font_url(True))
    st.markdown('<style>'+css+'</style>',unsafe_allow_html=True)


def page_link(page,wallet=''):
    params={'page':page}
    if wallet:params['wallet']=wallet
    return '?'+urlencode(params)


@lru_cache(maxsize=2)
def logo_uri(compact=False):
    name='mfl-management-hub-compact.svg' if compact else 'mfl-management-hub.svg'
    asset=Path(__file__).with_name('assets') / name
    return 'data:image/svg+xml;base64,'+base64.b64encode(asset.read_bytes()).decode('ascii')


def logo_html(compact=False):
    kind='tt-brand-compact' if compact else 'tt-brand-full'
    return f'<img class="{kind}" src="{logo_uri(compact)}" alt="MFL Management Hub — Manager 95 desktop">'


def header(page,wallet=''):
    number=PAGES.get(page,'100')
    now=datetime.now(ZoneInfo('Europe/London'))
    icon_asset=Path(__file__).with_name('assets')/'mfl-desktop-icon.svg'
    icon='data:image/svg+xml;base64,'+base64.b64encode(icon_asset.read_bytes()).decode('ascii')
    st.markdown(f'<section class="win-window-header" data-page="{number}">'
        f'<div class="win-window-title"><span><img src="{icon}" alt="">{escape(page)} — MFL Management Hub</span>'
        '<span class="win-caption-buttons" aria-hidden="true">_ □ ×</span></div>'
        '<nav class="win-menubar" aria-label="Application shortcuts">'+''.join(
            f'<a href="{escape(page_link(name,wallet),quote=True)}" target="_self">{label}</a>'
            for name,label in [('Home','My Agency'),('Squad Builder','Squads'),('Agency Development','Development'),('Agency / Player Valuation','Valuations'),('Sync Centre','Synchronise')])+'</nav>'
        f'<div class="win-location"><span>Location: {escape(page)} / {number}</span><span>Season 17 · {now.strftime("%d %b %Y")}</span></div></section>'
        '<nav class="win-taskbar" aria-label="Desktop taskbar">'
        f'<a href="{escape(page_link("Home",wallet),quote=True)}" target="_self"><img src="{icon}" alt=""><b>Start</b></a>'
        f'<a href="{escape(page_link("Squad Builder",wallet),quote=True)}" target="_self">Squads</a>'
        f'<a href="{escape(page_link("Agency / Player Valuation",wallet),quote=True)}" target="_self">Values</a>'
        f'<span class="win-task-title">MFL Management Hub</span><span class="win-clock">{now.strftime("%H:%M")}</span></nav>',unsafe_allow_html=True)


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
