
import os, sqlite3, html
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

import agency_backend as agency
import grower_backend as grower
import club_backend as club

st.set_page_config(page_title="MFL Management Hub",page_icon="⚽",layout="wide",initial_sidebar_state="expanded")

try:
    if "MFL_REFRESH_TOKEN" in st.secrets:
        os.environ["MFL_REFRESH_TOKEN"]=st.secrets["MFL_REFRESH_TOKEN"]
    if "DISCORD_WEBHOOK_URL" in st.secrets:
        os.environ["DISCORD_WEBHOOK_URL"]=st.secrets["DISCORD_WEBHOOK_URL"]
except Exception:
    pass

# ---------- Design ----------
st.markdown("""
<style>
:root {color-scheme:dark;}
.stApp{
 background:
 radial-gradient(circle at 100% 0%,rgba(18,184,166,.055),transparent 28rem),
 #071017;color:#edf6f5;
}
[data-testid="stHeader"]{background:rgba(7,16,23,.94);}
[data-testid="stSidebar"]{background:#08131a;border-right:1px solid #17313a;}
.block-container{max-width:1450px;padding-top:1.8rem;}
h1,h2,h3{color:#f5fbfa;letter-spacing:-.035em;}
p,label,.stCaption{color:#91a5ab!important;}
.brand{padding:10px 8px 22px;border-bottom:1px solid #17313a;margin-bottom:18px;}
.brand-logo{font-size:2.15rem;font-weight:950;letter-spacing:-.07em;color:#fff;line-height:1;}
.brand-logo span{color:#20dfb8;}
.brand-sub{color:#dce7e6;font-size:.72rem;font-weight:800;letter-spacing:.12em;margin-top:5px;}
.brand-line{height:4px;width:70px;background:#20dfb8;border-radius:99px;margin-top:10px;}
.page-head{margin-bottom:18px;}
.kicker{color:#20dfb8;font-size:.7rem;font-weight:850;letter-spacing:.15em;text-transform:uppercase;}
.page-title{font-size:2rem;font-weight:900;color:#f8fcfc;letter-spacing:-.045em;margin-top:4px;}
.page-sub{font-size:.92rem;color:#8ca1a8;margin-top:3px;}
.card{background:#0a171f;border:1px solid #1b3640;border-radius:14px;padding:18px;min-height:118px;}
.card .icon{font-size:1.35rem;color:#20dfb8;}
.card .big{font-size:1.95rem;font-weight:900;color:#f7fbfb;margin-top:7px;line-height:1;}
.card .label{font-size:.79rem;color:#9aadb2;margin-top:7px;}
.tool{background:#09161e;border:1px solid #1b3640;border-radius:14px;padding:20px;min-height:145px;}
.tool h4{color:#f5fbfa;margin:.4rem 0 .2rem;font-size:1.03rem;}
.tool p{color:#8399a0!important;font-size:.84rem;line-height:1.45;}
.rowbox{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #142a32;}
.rowbox:last-child{border-bottom:0;}
.rnum{width:25px;height:25px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#122630;color:#c8d8dc;font-size:.75rem;}
.rname{flex:1;color:#dfeaea;font-size:.86rem;}
.gain{color:#20dfb8;font-weight:800;font-size:.86rem;}
.stButton>button{background:#0b1a22;color:#dce9e9;border:1px solid #244650;border-radius:10px;font-weight:700;}
.stButton>button:hover{border-color:#20dfb8;color:#20dfb8;background:#0b1d24;}
div[data-testid="stMetric"]{background:#0a171f;border:1px solid #1b3640;border-radius:14px;padding:15px;}
div[data-testid="stMetricValue"]{color:#20dfb8;}
[data-testid="stDataFrame"]{border:1px solid #1b3640;border-radius:12px;overflow:hidden;}
[data-testid="stExpander"]{background:#09161e;border:1px solid #1a3640;border-radius:12px;}
div[data-baseweb="select"]>div,.stTextInput input{background:#0a171f!important;border-color:#244650!important;color:#edf7f6!important;}
</style>
""",unsafe_allow_html=True)

def head(k,title,sub):
    st.markdown(f'<div class="page-head"><div class="kicker">{html.escape(k)}</div><div class="page-title">{html.escape(title)}</div><div class="page-sub">{html.escape(sub)}</div></div>',unsafe_allow_html=True)

def card(icon,big,label):
    st.markdown(f'<div class="card"><div class="icon">{icon}</div><div class="big">{big}</div><div class="label">{label}</div></div>',unsafe_allow_html=True)

def valid_wallet(v):
    v=(v or "").strip()
    return len(v)>=10 and v.lower().startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in v[2:])

DEFAULT_WALLET="0x65cc0e72dd71ad80"
if "wallet" not in st.session_state: st.session_state.wallet=DEFAULT_WALLET

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("""<div class="brand"><div class="brand-logo">MFL<span>♛</span></div>
    <div class="brand-sub">MANAGEMENT HUB</div><div class="brand-line"></div></div>""",unsafe_allow_html=True)
    pages=["⌂ Home","🏆 Grower or Shower","👥 Agency Development","▥ Club Development"]
    page=st.radio("Navigation",pages,label_visibility="collapsed")
    st.divider()
    st.caption("WALLET")
    st.code(st.session_state.wallet,language=None)
    if st.button("Change wallet",use_container_width=True):
        st.session_state.edit_wallet=True
    if st.session_state.get("edit_wallet"):
        nw=st.text_input("Wallet",value=st.session_state.wallet,key="side_wallet")
        if st.button("Use wallet",use_container_width=True):
            if valid_wallet(nw):
                st.session_state.wallet=nw.strip().lower();st.session_state.edit_wallet=False;st.rerun()
            else: st.error("Enter a valid 0x wallet.")
    st.divider()
    st.caption("SEASON 17 · CLEAN START v1")

wallet=st.session_state.wallet

# ---------- Home ----------
if page=="⌂ Home":
    head("MFL · SEASON 17","Good to see you!","Track. Analyse. Develop. All in one place.")
    # Agency seed provides immediate stored counts.
    try:
        c=agency.db();agency.init(c);agency.ensure_v2(c)
        n_agency=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=?",(wallet.lower(),)).fetchone()[0]
        improved=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=? AND current_ovr>start_ovr",(wallet.lower(),)).fetchone()[0]
        c.close()
    except Exception:
        n_agency=0;improved=0
    try:
        mine=club.owned_clubs(wallet)
    except Exception:
        mine=[]
    cache=club.cached(wallet)
    club_ovr=float(cache["ovr_gain"].fillna(0).sum()) if not cache.empty else 0
    cols=st.columns(4)
    with cols[0]: card("♢",str(len(mine) if mine else "—"),"Owned Clubs")
    with cols[1]: card("♟",str(n_agency or "—"),"Players Tracked")
    with cols[2]: card("⌃",f"+{club_ovr:g}" if not cache.empty else "—","S17 Club OVR Loaded")
    with cols[3]: card("✓",str(improved or "0"),"Agency Players Improved")
    st.write("")
    a,b,c=st.columns(3)
    with a:
        st.markdown('<div class="tool">🏆<h4>Grower or Shower</h4><p>Competition standings, OVR/attribute development and Season 17 ratings.</p></div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="tool">👥<h4>Agency Development</h4><p>Ownership baselines, new mints, tags, notes and player development.</p></div>',unsafe_allow_html=True)
    with c:
        st.markdown('<div class="tool">▥<h4>Club Development</h4><p>Season 17 progression across verified MFL_OWNER clubs.</p></div>',unsafe_allow_html=True)
    st.info("This clean-start build has no embedded legacy Streamlit pages. Every section is rendered natively in this app.")

# ---------- Grower ----------
elif page=="🏆 Grower or Shower":
    head("WORKTHESPACE · SEASON 17","Grower or Shower","Live competition tracking in the Hub design.")
    with st.expander("Competition settings"):
        grower_start=st.text_input("Competition baseline / Season 17 start (UTC)",value=st.session_state.get("grower_start","2026-09-22T00:00:00Z"),key="grower_start_input")
        st.session_state.grower_start=grower_start
        os.environ["GROWER_START"]=grower_start
        st.caption("The fresh Hub reconstructs the baseline from MFL progression history at this point, rather than treating the first Hub refresh as zero.")
    conn=grower.db();grower.init_db(conn)
    if st.button("Refresh competition data",type="primary"):
        try:
            tok=grower.refresh_access_token()
            bar=st.progress(0,text="Refreshing entrants…")
            errs=[]
            for i,(pid,owner) in enumerate(grower.ENTRANTS.items(),1):
                try: grower.sync_player(conn,tok,pid,owner)
                except Exception as e: errs.append(f"{owner}: {e}")
                bar.progress(i/len(grower.ENTRANTS),text=f"{i}/{len(grower.ENTRANTS)} entrants")
            bar.empty()
            if errs: st.warning(f"{len(errs)} entrant(s) could not refresh; saved data is still shown.")
            else: st.success("Competition refreshed.")
        except Exception as e: st.error(f"{type(e).__name__}: {e}")
    rows=grower.leaderboard(conn)
    if not rows:
        st.info("No competition snapshots are stored in this fresh Hub yet. Press Refresh competition data once.")
    else:
        m=st.columns(4)
        with m[0]: card("🏆",rows[0]["owner"],"Current Leader")
        with m[1]: card("⌃",grower.fmt_delta(rows[0]["ovr_growth"]), "Best OVR Growth")
        with m[2]: card("✦",grower.fmt_delta(rows[0].get("attribute_growth",0)),"Leader Attr Growth")
        with m[3]: card("●",str(len(rows)),"Entrants")
        st.write("")
        table=[]
        for i,r in enumerate(rows,1):
            table.append({
              "#":i,"Owner":r["owner"],"Player":r["player"],"OVR":r["ovr"],
              "OVR ↑":grower.fmt_delta(r["ovr_growth"]),
              "ATTR ↑":grower.fmt_delta(r.get("attribute_growth",0)),
              "Rating":r["avg_rating"],"Apps":r["apps"],
              "PAC ↑":grower.fmt_delta(r["pace_growth"]),"SHO ↑":grower.fmt_delta(r["shooting_growth"]),
              "PAS ↑":grower.fmt_delta(r["passing_growth"]),"DRI ↑":grower.fmt_delta(r["dribbling_growth"]),
              "DEF ↑":grower.fmt_delta(r["defense_growth"]),"PHY ↑":grower.fmt_delta(r["physical_growth"])
            })
        st.dataframe(pd.DataFrame(table),use_container_width=True,hide_index=True)
        st.caption("Ranking: OVR growth → total attribute growth → average Season 17 rating.")
    conn.close()

# ---------- Agency ----------
elif page=="👥 Agency Development":
    head("PLAYER DEVELOPMENT","Agency Development","Ownership baselines, new mints, tags and progression.")
    c=agency.db();agency.init(c);agency.ensure_v2(c)
    rows=c.execute("""SELECT o.*,COALESCE(t.tag,'NORMAL') tag,COALESCE(t.note,'') note,
      m.age,m.position,m.club,a.last_event_at,a.match_events,a.training_events,a.total_events
      FROM ownership_v65 o
      LEFT JOIN tags t ON t.wallet=o.wallet AND t.player_id=o.player_id
      LEFT JOIN player_meta m ON m.wallet=o.wallet AND m.player_id=o.player_id
      LEFT JOIN activity a ON a.wallet=o.wallet AND a.player_id=o.player_id
      WHERE o.wallet=?""",(wallet.lower(),)).fetchall()
    if not rows:
        st.warning("This wallet is not in the bundled agency database.")
    else:
        df=pd.DataFrame([dict(r) for r in rows])
        for lab,cur,start in [("OVR ↑","current_ovr","start_ovr"),("PAC ↑","current_pac","start_pac"),("SHO ↑","current_sho","start_sho"),
                              ("PAS ↑","current_pas","start_pas"),("DRI ↑","current_dri","start_dri"),("DEF ↑","current_def","start_def"),("PHY ↑","current_phy","start_phy")]:
            df[lab]=pd.to_numeric(df[cur],errors="coerce")-pd.to_numeric(df[start],errors="coerce")
        df["Acquired"]=pd.to_datetime(df.acquired_at,utc=True,errors="coerce")
        df["Initial date"]=pd.to_datetime(df.history_start,utc=True,errors="coerce")
        m=st.columns(4)
        with m[0]: card("♟",str(len(df)),"Players")
        with m[1]: card("⌃",str(int((df["OVR ↑"]>0).sum())),"Improved OVR")
        with m[2]: card("◉",str(int((df.source=="NEW MINT / ORIGINAL").sum())),"New / Original")
        with m[3]: card("★",str(int((df.tag=="PRIORITY").sum())),"Priority")
        st.write("")
        tabs=st.tabs(["Development","New Mints","My List","Agency"])
        with tabs[0]:
            v=df[df["OVR ↑"]>0].sort_values(["OVR ↑","current_ovr"],ascending=False)
            st.dataframe(v[["player_name","age","position","club","start_ovr","current_ovr","OVR ↑","PAC ↑","SHO ↑","PAS ↑","DRI ↑","DEF ↑","PHY ↑"]]
                         .rename(columns={"player_name":"Player","age":"Age","position":"Position","club":"Club","start_ovr":"Start","current_ovr":"Current"}),
                         use_container_width=True,hide_index=True)
        with tabs[1]:
            v=df[df.source=="NEW MINT / ORIGINAL"].sort_values(["OVR ↑","current_ovr"],ascending=False)
            st.dataframe(v[["player_name","age","Initial date","start_ovr","current_ovr","OVR ↑","club"]]
                         .rename(columns={"player_name":"Player","age":"Age","start_ovr":"Initial","current_ovr":"Current","club":"Club"}),
                         use_container_width=True,hide_index=True)
        with tabs[2]:
            mine=df[df.tag!="NORMAL"].copy()
            if mine.empty: st.info("No tagged players yet.")
            else:
                st.dataframe(mine[["tag","player_name","age","current_ovr","OVR ↑","note"]].rename(columns={"player_name":"Player","age":"Age","current_ovr":"OVR","tag":"Tag","note":"Note"}),use_container_width=True,hide_index=True)
            opts={f"{r.player_name} · {int(r.player_id)}":int(r.player_id) for _,r in df.sort_values("player_name").iterrows()}
            who=st.selectbox("Player",list(opts),key="tag_player")
            ex=df[df.player_id==opts[who]].iloc[0]
            tags=["NORMAL","DEVELOP","PRIORITY","WATCH"]
            tag=st.selectbox("Tag",tags,index=tags.index(ex.tag) if ex.tag in tags else 0,key="tag_value")
            note=st.text_input("Note",value=ex.note or "",key="tag_note")
            if st.button("Save player tag"):
                c.execute("""INSERT INTO tags(wallet,player_id,tag,note) VALUES(?,?,?,?)
                ON CONFLICT(wallet,player_id) DO UPDATE SET tag=excluded.tag,note=excluded.note""",(wallet.lower(),opts[who],tag,note))
                c.commit();st.rerun()
        with tabs[3]:
            q=st.text_input("Search players")
            v=df if not q else df[df.player_name.str.contains(q,case=False,na=False)]
            sort=st.selectbox("Sort",["OVR gain","OVR","Age","Name"])
            if sort=="OVR gain":v=v.sort_values(["OVR ↑","current_ovr"],ascending=False,na_position="last")
            elif sort=="OVR":v=v.sort_values("current_ovr",ascending=False,na_position="last")
            elif sort=="Age":v=v.sort_values("age",na_position="last")
            else:v=v.sort_values("player_name")
            st.dataframe(v[["player_name","age","position","club","source","Acquired","start_ovr","current_ovr","OVR ↑","tag"]]
                         .rename(columns={"player_name":"Player","age":"Age","position":"Position","club":"Club","source":"Ownership","start_ovr":"Start","current_ovr":"OVR","tag":"Tag"}),
                         use_container_width=True,hide_index=True)
        with st.expander("Refresh tools"):
            st.caption("These jobs are deliberately small/resumable so MFL rate limits do not freeze the whole Hub.")
            if st.button("Refresh next 20 player stats"):
                bar=st.progress(0,text="Refreshing next 20…")
                def prog(n,total):bar.progress(n/max(total,1),text=f"{n}/{total}")
                try:
                    done,total,errs=agency.refresh_current_v21(wallet,prog,20);bar.empty()
                    if errs:st.warning(f"Updated {done}; {len(errs)} issue(s).")
                    else:st.success(f"Updated {done} players.")
                except Exception as e:bar.empty();st.error(f"{type(e).__name__}: {e}")
    c.close()

# ---------- Club ----------
elif page=="▥ Club Development":
    head("CLUB ANALYTICS · SEASON 17","Club Development","Development totals for clubs verified as MFL_OWNER.")
    with st.expander("Season settings"):
        season_start=st.text_input("Season 17 start (UTC)",value=st.session_state.get("season_start","2026-09-22T00:00:00Z"))
        st.session_state.season_start=season_start
        batch=st.selectbox("Players per refresh batch",[20,30,40],index=1)
    cached=club.cached(wallet)
    try: mine=club.owned_clubs(wallet)
    except Exception: mine=[]
    top=st.columns(4)
    with top[0]:card("♢",str(len(mine) if mine else "—"),"Owned Clubs")
    with top[1]:card("♟",str(len(cached)),"Players Cached")
    with top[2]:card("⌃",f"+{cached['ovr_gain'].fillna(0).sum():g}" if not cached.empty else "—","S17 OVR Loaded")
    with top[3]:card("▥",f"+{cached['attr_gain'].fillna(0).sum():g}" if not cached.empty else "—","Attributes Loaded")
    st.write("")
    if st.button(f"Sync next {batch} players",type="primary"):
        bar=st.progress(0,text="Preparing batch…");status=st.empty()
        def prog(done,total,errs):
            bar.progress(done/max(total,1),text=f"{done}/{total} players in this batch")
            status.caption(f"{errs} skipped/failed in this batch")
        try:
            res=club.sync_batch(wallet,season_start,batch,prog)
            bar.empty();status.empty()
            if res["errors"]:st.warning(f"Saved {res['saved']} players. {len(res['errors'])} requests were skipped/failed. Press Sync next batch to continue.")
            else:st.success(f"Saved {res['saved']} players. Press Sync next batch to continue updating the agency.")
            st.rerun()
        except Exception as e:
            bar.empty();status.empty()
            if "MFL_RATE_LIMITED" in str(e):st.warning("MFL rate limit reached before this batch could complete. Wait a little, then press Sync next batch.")
            else:st.error(f"{type(e).__name__}: {e}")
    cached=club.cached(wallet)
    if cached.empty:
        st.info("No Season 17 club progression is cached yet. Press Sync next 30 players. The app no longer attempts all 271 players in one request cycle.")
    else:
        clubs=(cached[cached.error.isna() if "error" in cached else pd.Series(True,index=cached.index)]
               .groupby("club").agg(Players=("player_id","count"),OVR=("ovr_gain","sum"),Attributes=("attr_gain","sum"),
                PAC=("pac","sum"),SHO=("sho","sum"),PAS=("pas","sum"),DRI=("dri","sum"),DEF=("defn","sum"),PHY=("phy","sum"))
               .reset_index().sort_values(["OVR","Attributes"],ascending=False))
        st.markdown("### Club leaderboard")
        st.dataframe(clubs.rename(columns={"club":"Club","OVR":"OVR ↑","Attributes":"ATTR ↑"}),use_container_width=True,hide_index=True)
        if not clubs.empty:
            choice=st.selectbox("Club detail",clubs["club"].tolist())
            detail=cached[(cached.club==choice)&cached.error.isna()].sort_values(["ovr_gain","attr_gain"],ascending=False)
            st.dataframe(detail[["player","start_ovr","current_ovr","ovr_gain","attr_gain","pac","sho","pas","dri","defn","phy"]]
                         .rename(columns={"player":"Player","start_ovr":"S17 Start","current_ovr":"Current","ovr_gain":"OVR ↑","attr_gain":"ATTR ↑",
                                          "pac":"PAC ↑","sho":"SHO ↑","pas":"PAS ↑","dri":"DRI ↑","defn":"DEF ↑","phy":"PHY ↑"}),
                         use_container_width=True,hide_index=True)
        if mine:
            with st.expander("Owned clubs detected"):
                st.write(" · ".join(x["name"] for x in mine))
        st.caption("Club data refreshes in small saved batches by design. This avoids the previous 45–66% freeze caused by trying to pull hundreds of progression histories in one run.")
