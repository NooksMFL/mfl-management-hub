"""Roster-scoped player profile dialog; opening a card makes no API calls."""
from html import escape
import streamlit as st
import wallet_cache_backend as shared
from mfl_text import page_link
from squad_cards import age_label
from tactics_engine import numeric,positions,explicit_ratings,rating_at

ATTRIBUTES=(('pace','current_pac','Pace','PAC'),('shooting','current_sho','Shooting','SHO'),
            ('passing','current_pas','Passing','PAS'),('dribbling','current_dri','Dribbling','DRI'),
            ('defense','current_def','Defence','DEF'),('physical','current_phy','Physical','PHY'))


def attributes(player):
    # Each caller supplies either shared-roster fields or agency current_* fields.
    return [{'label':label,'short':short,'value':numeric(player[key] if key in player else player.get(fallback))}
            for key,fallback,label,short in ATTRIBUTES]


def profile_html(player):
    pid=int(player['player_id']);name=str(player.get('player_name') or player.get('player') or f'Player {pid}')
    overall=numeric(player.get('overall',player.get('current_ovr')))
    ovr=f'{overall:g}' if overall is not None else '—'
    listed=' / '.join(positions(player.get('position'))) or 'Position unavailable'
    club=str(player.get('club') or 'No current club')
    heading=(f'<div class="ops-profile-hero"><span class="ops-profile-photo" style="background-image:url(https://d13e14gtps4iwl.cloudfront.net/players/v2/{pid}/photo.webp)"></span>'
             f'<div><div class="ops-profile-name">{escape(name)}</div><div class="ops-profile-meta">{escape(listed)} · Age {age_label(player.get("age"))}</div><div class="ops-profile-club">{escape(club)}</div></div>'
             f'<div class="ops-profile-ovr">{ovr}<small>BASE OVR</small></div></div>')
    cards=[]
    for attr in attributes(player):
        value=attr['value'];text=f'{value:g}' if value is not None else 'Unavailable'
        bar=f'<div class="ops-attribute-track"><i style="width:{value:g}%"></i></div>' if value is not None else '<div class="ops-attribute-missing">No saved measurement</div>'
        cards.append(f'<div class="ops-attribute"><div><span>{attr["label"]}</span><strong>{text}</strong></div>{bar}</div>')
    return heading+'<div class="ops-profile-section">Attributes</div><div class="ops-attribute-grid">'+''.join(cards)+'</div>'


def close_profile():
    st.query_params.pop('player',None)
    st.session_state.pop('active_player_profile',None)


def open_requested(players,wallet,value=None):
    active=st.session_state.get('active_player_profile')
    if value is None:
        if not active or active.get('wallet')!=wallet:
            st.session_state.pop('active_player_profile',None)
            return
        value=active.get('player_id')
    try:pid=int(value)
    except (TypeError,ValueError):
        close_profile();st.warning('That player is not available in this roster.');return
    player=next((dict(p) for p in players if int(p['player_id'])==pid),None)
    if player is None:
        close_profile();st.warning('That player is not available in the currently visible roster.');return
    # Consume URL requests, but retain modal state across browser-storage reruns.
    st.query_params.pop('player',None)
    st.session_state['active_player_profile']={'wallet':wallet,'player_id':pid}
    overrides=shared.tactics_ratings(wallet).get(pid,{})
    player['manual_position_ratings']={pos:row['rating'] for pos,row in overrides.items()}

    @st.dialog('Player profile',width='large',on_dismiss=close_profile)
    def show():
        st.markdown(profile_html(player),unsafe_allow_html=True)
        pos=list(dict.fromkeys(positions(player.get('position'))+list(explicit_ratings(player.get('position_ratings')))+list(player['manual_position_ratings'])))
        st.markdown('**Position ratings**')
        rows=[]
        for position in pos:
            rating,source=rating_at(player,position)
            rows.append({'Position':position,'Rating':f'{rating:g}' if rating is not None else 'Unavailable','Source':source})
        if rows:st.dataframe(rows,hide_index=True,use_container_width=True)
        else:st.caption('No saved positions available.')
        st.caption('Secondary positions can have a different rating. A base-OVR fallback applies only to the first listed position; missing secondary ratings are unavailable.')
        stamp=player.get('cached_at') or player.get('updated_at') or 'Unknown'
        st.caption(f'Saved data updated: {stamp} · Player ID: {pid}. Use Load / refresh team players on Home to update the saved attributes.')
        st.markdown(f'<a class="ops-profile-agency" href="{escape(page_link("Agency Development",wallet),quote=True)}" target="_self">Open My agency ↗</a>',unsafe_allow_html=True)
        if st.button('Close profile',key='close_player_profile'):
            close_profile();st.rerun()
    show()
