"""MFL Management Hub: shared football management identity and numbered page navigation."""
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


SECTION_COLOURS={
    'Home':('#b9e83f','#142332'),'Squad Builder':('#b9e83f','#142b2b'),
    'Club Development':('#57dab1','#142a2b'),'Agency Development':('#79d6ff','#15283a'),
    'Transfer Window':('#e7c17b','#2a251c'),'Transfer Bargains':('#e7c17b','#2a251c'),
    'Agency / Player Valuation':('#d7cd8b','#27291f'),'Watchlist':('#dca1bc','#292131'),
    'Compare':('#86cdeb','#142835'),'Insights':('#bea6ed','#221e34'),
    'Sync Centre':('#b9e83f','#1d2b23'),'Grower or Shower':('#b9d87f','#233020'),
    'Design Studio':('#bba8dd','#211f32')}


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
    css = Path(__file__).with_name('command.css').read_text().replace('TELETEXT_FONT_URL',font_url()).replace('READ_FONT_URL',read_font_url()).replace('BOLD_FONT_URL',read_font_url(True))
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
    return f'<img class="{kind}" src="{logo_uri(compact)}" alt="MFL Management Hub">'


def header(page,wallet=''):
    number=PAGES.get(page,'100')
    accent,tint=SECTION_COLOURS.get(page,SECTION_COLOURS['Home'])
    st.markdown(f'<style>:root{{--section-accent:{accent};--section-tint:{tint};}}</style>',unsafe_allow_html=True)
    now=datetime.now(ZoneInfo('Europe/London'))
    links=''.join(f'<a class="{"active" if name==page else ""}" href="{escape(page_link(name,wallet),quote=True)}" target="_self">{label}</a>'
        for name,label in [('Home','Overview'),('Squad Builder','Squad & tactics'),('Agency Development','Development'),('Agency / Player Valuation','Valuations'),('Sync Centre','Load & sync')])
    st.markdown(f'<div class="manager-header" data-page="{number}"><div><div class="manager-breadcrumb">MFL Management Hub / Matchday workspace</div>'
        f'<div class="manager-page-title">{escape({"Home":"Command centre","Club Development":"Club progression","Agency Development":"Agency progression"}.get(page,page))}</div></div><div class="manager-season"><strong>WORKSPACE</strong><br>{now.strftime("%d %b %Y")}</div></div>'
        f'<nav class="manager-tabs" aria-label="Application shortcuts">{links}</nav>'
        '<nav class="signal-route" aria-label="Workspace steps">'+''.join(
            f'<a href="{escape(page_link(name,wallet),quote=True)}" target="_self"><b>{step}</b>{label}</a>'+('<i aria-hidden="true"></i>' if step!='03' else '')
            for step,name,label in [('01','Sync Centre','Load players'),('02','Club Development','Track clubs'),('03','Squad Builder','Select XI')])+'</nav>',unsafe_allow_html=True)


def jump_to_page():
    number=st.session_state.get('tt_page_number','').strip()
    target=next((name for name,code in PAGES.items() if code==number),None)
    if target:
        st.session_state['hub_nav']=target
        st.query_params['page']=target
        st.query_params.pop('player',None)
        st.session_state.pop('active_player_profile',None)
        st.session_state.pop('tt_page_error',None)
    else:
        st.session_state['tt_page_error']='PAGE NOT FOUND. TRY 100, 201, 202 OR 302.'


def sync_navigation():
    st.query_params['page']=st.session_state['hub_nav']
    st.query_params.pop('player',None)
    st.session_state.pop('active_player_profile',None)
