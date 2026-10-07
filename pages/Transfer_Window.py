import streamlit as st
import pandas as pd
import transfer_window_backend as tw

st.set_page_config(page_title="MFL Transfer Window",page_icon="🚨",layout="wide")
WALLET="0x65cc0e72dd71ad80"

st.title("🚨 Season 17 Transfer Window")
st.caption("All managed clubs · official Season 17 appearances only · friendlies/preseason excluded · flags players with 0–3 apps")

if "tw_results" not in st.session_state:
    st.session_state.tw_results=None
if "tw_errors" not in st.session_state:
    st.session_state.tw_errors=[]

if st.button("Scan all managed clubs",type="primary",use_container_width=True):
    bar=st.progress(0)
    status=st.empty()
    def prog(done,total,flagged,errors):
        bar.progress(done/max(total,1))
        status.caption(f"Scanning {done}/{total} players · {flagged} currently under 4 apps · {errors} API errors")
    try:
        with st.spinner("Checking Season 17 competition appearances…"):
            df,errs,total=tw.candidates(WALLET,prog)
        st.session_state.tw_results=df
        st.session_state.tw_errors=errs
        status.success(f"Scan complete: {total} contracted players checked.")
    except Exception as e:
        st.error(f"Scan stopped: {e}")

df=st.session_state.tw_results
if df is not None:
    if df.empty:
        st.success("No managed-club players are below 4 official Season 17 appearances.")
    else:
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Players under 4 apps",len(df))
        c2.metric("0 apps",int((df["Apps"]==0).sum()))
        c3.metric("1–2 apps",int(df["Apps"].isin([1,2]).sum()))
        c4.metric("3 apps",int((df["Apps"]==3).sum()))
        clubs=["All clubs"]+sorted(df["Club"].dropna().unique().tolist())
        chosen=st.selectbox("Club",clubs)
        view=df if chosen=="All clubs" else df[df["Club"]==chosen]
        st.dataframe(view,use_container_width=True,hide_index=True,column_config={
            "Apps":st.column_config.NumberColumn("S17 Apps",format="%d"),
            "OVR":st.column_config.NumberColumn("OVR",format="%.0f"),
            "Age":st.column_config.NumberColumn("Age",format="%.0f")
        })
        st.download_button("Download shortlist CSV",df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="mfl_s17_under_4_apps.csv",mime="text/csv")
        st.subheader("By club")
        summary=df.groupby("Club").agg(Flagged=("Player","count"),Zero_apps=("Apps",lambda x:int((x==0).sum())),
                                       Three_apps=("Apps",lambda x:int((x==3).sum()))).reset_index()
        st.dataframe(summary,use_container_width=True,hide_index=True)
if st.session_state.tw_errors:
    with st.expander(f"API errors ({len(st.session_state.tw_errors)})"):
        st.dataframe(pd.DataFrame(st.session_state.tw_errors,columns=["Player ID","Error"]),use_container_width=True,hide_index=True)
