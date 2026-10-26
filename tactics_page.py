"""Club-first tactics workspace with transparent positional-rating provenance."""
import pandas as pd
import streamlit as st
import wallet_cache_backend as shared
from squad_builder import has_current_club
from tactics_engine import explicit_ratings, positions, rating_at, recommend
from formation_board import render_board


def prepare(records,wallet,active_only=True):
    overrides=shared.tactics_ratings(wallet)
    return [{**r,'manual_position_ratings':{pos:v['rating'] for pos,v in overrides.get(int(r['player_id']),{}).items()}} for r in records if not active_only or has_current_club(r.get('club'))]


def render(records,wallet):
    st.subheader('Club tactics & formation recommendations')
    players=prepare(records,wallet)
    if not players:
        st.info('No active players with a current club. Refresh your roster in Sync Centre.');return
    clubs=sorted({p['club'] for p in players})
    team_col,title_col=st.columns(2)
    with team_col:chosen=st.selectbox('Team to plan',clubs+['All active agency players'],key='tactics_club')
    team=[p for p in players if chosen=='All active agency players' or p['club']==chosen]
    with title_col:title=st.text_input('Tactics board title',value=f'{chosen if chosen!="All active agency players" else "My squad"} – Season 18',key=f'tactics_title_{chosen}')
    st.caption(f"{len(team)} active players · secondary ratings are used only when supplied or entered. Edit ratings in the panel below the pitch.")
    suggestions=recommend(team)
    best=suggestions[0]
    if best['filled']==11:
        st.success(f'Recommended: {best["formation"]} · {best["average"]:.1f} average position OVR · {best["fallbacks"]} first-position fallback(s).')
    else:
        st.warning(f'Best available fit: {best["formation"]} · {best["filled"]}/11 rated positions. Verify secondary ratings or add cover for: '+', '.join(best['missing'])+'. A complete-XI average is unavailable.')
    expanded=st.toggle("Large pitch",value=False,key="tactics_large_pitch",help="The compact pitch fits most laptop screens. Expand for larger portraits and text.")
    render_board(team,f'mfl_tactics_v2_{wallet}_{chosen}',suggestions=suggestions,title=title,compact=not expanded)

    comparisons=[{'Formation':r['formation'],'Rated positions':f'{r["filled"]}/11','XI position OVR':round(r['average'],1) if r['average'] is not None else None,'First-position fallbacks':r['fallbacks'],'Missing rated cover':', '.join(r['missing']) or 'None'} for r in suggestions]
    with st.expander('Compare all formations'):
        st.dataframe(pd.DataFrame(comparisons),hide_index=True,use_container_width=True)
    st.caption('Ranked by rated positions filled, then summed position OVR. Formation fit is a planning estimate, not a prediction of results. Club membership reflects the saved roster, not an unverified future contract.')
    with st.expander('Review / enter position ratings'):
        choices={f'{p.get("player")} · {p["player_id"]}':p for p in sorted(team,key=lambda p:str(p.get('player')))}
        label=st.selectbox('Player to verify',list(choices),key=f'tactics_verify_{chosen}');p=choices[label]
        pos=list(dict.fromkeys(positions(p.get('position'))+list(explicit_ratings(p.get('position_ratings')))+list(p['manual_position_ratings'])))
        st.caption('Enter the ratings shown on the MFL position map. Example: Habibou CM 69, CDM 62. Blank means unknown. Clear an entered value and save to remove the override. Refresh these entries when players develop.')
        supplied=explicit_ratings(p.get('position_ratings'))
        rows=[{'Position':position,'Entered rating':p['manual_position_ratings'].get(position),'Supplied rating':supplied.get(position),'Currently used':rating_at(p,position)[0],'Source':rating_at(p,position)[1]} for position in pos]
        edited=st.data_editor(pd.DataFrame(rows),hide_index=True,disabled=['Position','Supplied rating','Currently used','Source'],
            column_config={'Entered rating':st.column_config.NumberColumn(min_value=0,max_value=100,step=1)},key=f'tactics_edit_{wallet}_{p["player_id"]}')
        saved=shared.tactics_ratings(wallet).get(int(p['player_id']),{})
        if saved:st.caption('Entered ratings last saved: '+max(v['updated_at'] for v in saved.values()))
        if st.button('Save verified position ratings',key='save_tactics_ratings'):
            shared.save_tactics_ratings(wallet,p['player_id'],dict(zip(edited['Position'],edited['Entered rating'])));st.rerun()
