"""Squad analyser page; only reads saved profiles."""
import pandas as pd
import streamlit as st
import squad_analysis as analysis
import tactics_engine as tactics


def render(wallet):
    players,coverage=analysis.snapshot(wallet)
    if not players:
        st.info('No checked player profiles are available yet. Continue your existing sync to load them.')
        return
    active=[p for p in players if analysis.is_active(p)]
    excluded=len(players)-len(active)
    if coverage['partial']:
        st.warning(f"Using {coverage['checked']} of {coverage['total']} checked profiles. The remaining {coverage['total']-coverage['checked']} players may change these recommendations.")
    st.caption(f'{excluded} retired or no-club players excluded. Analysis uses saved profiles and makes no MFL requests.')
    fcn_only=st.toggle('FCN clubs only',value=True,key='analysis_fcn')
    clubs=analysis.club_names(wallet,players,fcn_only)
    if not clubs:
        st.info('No matching clubs in the checked profiles yet.')
        return
    controls=st.columns([2,1])
    with controls[0]:club=st.selectbox('Club',['All FCN clubs' if fcn_only else 'All owned clubs']+clubs,key='analysis_club')
    with controls[1]:formation=st.selectbox('Formation',list(tactics.FORMATIONS),index=list(tactics.FORMATIONS).index('4-3-3'),key='analysis_formation')
    st.caption('Each formation needs a starting XI and one cover player per starting place. Players count once. A ? means a listed position has no saved rating.')
    selected=clubs if club not in clubs else [club]
    exports=[]
    for name in selected:
        squad=[p for p in active if p['club'].strip().casefold()==name.casefold()]
        with st.container(border=True):
            st.subheader(name)
            target=st.number_input('Target starting rating',min_value=1,max_value=100,value=analysis.target_rating(squad),key='analysis_target_'+name,
                help='Defaults to the squad median OVR. Set this to the standard you want for this club. Cover is assessed five points below this target.')
            report,allocation=analysis.analyse(squad,formation,target)
            need=[r['Position'] for r in report if r['Priority']!='Covered']
            left,mid,right=st.columns(3)
            left.metric('Active players',len(squad));mid.metric('Starting places filled',f"{sum(r['Starters'] for r in report)} / 11")
            right.metric('Cover places filled',f"{sum(r['Cover'] for r in report)} / 11")
            if need:st.write('**Positions to review:** '+', '.join(need))
            else:st.success('Every position has a starter and cover at your target rating.')
            frame=pd.DataFrame(report)
            st.dataframe(frame[['Position','Priority','Starting places','Starters','Cover','Starting players','Cover players','Action']],hide_index=True,width='stretch',height=40+len(frame)*40,row_height=40)
            exports.append(frame.assign(Club=name,Formation=formation,Target=target))
            with st.expander('Squad players'):
                rows=[{'Player':p['player_name'],'Position':p.get('position'),'OVR':p.get('overall'),'Age':p.get('age'),'Checked':p.get('cached_at')} for p in squad]
                st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    if exports:st.download_button('Download squad report',pd.concat(exports).to_csv(index=False).encode('utf-8-sig'),'mfl_squad_report.csv','text/csv')
