
import os, html, math
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

import agency_backend as agency
import grower_backend as grower
import club_backend as club

st.set_page_config(
    page_title="MFL Management Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    if "MFL_REFRESH_TOKEN" in st.secrets:
        os.environ["MFL_REFRESH_TOKEN"]=st.secrets["MFL_REFRESH_TOKEN"]
    if "DISCORD_WEBHOOK_URL" in st.secrets:
        os.environ["DISCORD_WEBHOOK_URL"]=st.secrets["DISCORD_WEBHOOK_URL"]
except Exception:
    pass

# ---------------- THEME ----------------
st.markdown("""
<style>
:root{
  --bg:#071118;
  --panel:#0b1820;
  --panel2:#0d1c25;
  --line:#17333d;
  --muted:#829aa2;
  --text:#eff8f6;
  --mint:#20deb7;
  --blue:#2b9cff;
  --violet:#a85cff;
}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
.stApp{
  background:
    radial-gradient(circle at 96% 0%,rgba(32,222,183,.055),transparent 28rem),
    radial-gradient(circle at 22% 100%,rgba(43,156,255,.035),transparent 30rem),
    var(--bg);
  color:var(--text);
}
[data-testid="stHeader"]{background:rgba(7,17,24,.92);border-bottom:1px solid rgba(23,51,61,.45);}
[data-testid="stSidebar"]{
  background:#08131a;
  border-right:1px solid var(--line);
  min-width:245px!important;
}
[data-testid="stSidebarContent"]{padding:1.15rem .9rem;}
.block-container{max-width:1420px;padding-top:2rem;padding-bottom:4rem;}
h1,h2,h3,h4{color:var(--text);letter-spacing:-.035em;}
p,label,.stCaption{color:var(--muted)!important;}
hr{border-color:var(--line)!important;}

.brand{padding:6px 8px 24px;margin-bottom:18px;border-bottom:1px solid var(--line);}
.logo{font-size:2rem;font-weight:950;letter-spacing:-.075em;color:#fff;line-height:.95;}
.logo .crown{color:var(--mint);font-size:1rem;vertical-align:top;margin-left:4px;}
.logo-sub{margin-top:7px;font-size:.68rem;font-weight:850;letter-spacing:.14em;color:#d9e9e6;}
.logo-line{margin-top:10px;width:68px;height:4px;border-radius:99px;background:var(--mint);}

[data-testid="stSidebar"] [role="radiogroup"]{gap:5px;}
[data-testid="stSidebar"] [role="radiogroup"] label{
  border-radius:10px;
  padding:10px 12px;
  transition:.15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#0d2029;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
  background:linear-gradient(90deg,rgba(32,222,183,.18),rgba(32,222,183,.06));
  border:1px solid rgba(32,222,183,.28);
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child{display:none;}
[data-testid="stSidebar"] [role="radiogroup"] p{font-weight:650!important;color:#c7d7da!important;}

.eyebrow{color:var(--mint);font-size:.68rem;letter-spacing:.16em;font-weight:850;text-transform:uppercase;}
.page-title{font-size:2.1rem;line-height:1.05;font-weight:900;color:#f8fcfb;letter-spacing:-.05em;margin-top:5px;}
.page-sub{font-size:.93rem;color:#8ea4aa;margin-top:7px;margin-bottom:22px;}
.topbar{
 display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:4px;
}
.pill{
 display:inline-flex;align-items:center;gap:7px;border:1px solid #21444e;background:#0a1921;
 color:#bdd0d2;border-radius:999px;padding:8px 12px;font-size:.76rem;font-weight:700;
}
.dot{width:7px;height:7px;border-radius:50%;background:var(--mint);box-shadow:0 0 0 4px rgba(32,222,183,.08);}

.stat{
 background:linear-gradient(145deg,#0b1921,#09161d);
 border:1px solid var(--line);
 border-radius:15px;padding:18px 19px;min-height:125px;
 box-shadow:0 10px 30px rgba(0,0,0,.10);
}
.stat-icon{font-size:1.1rem;color:var(--mint);font-weight:900;}
.stat-value{font-size:2rem;font-weight:900;letter-spacing:-.045em;color:#f8fcfb;line-height:1;margin-top:12px;}
.stat-label{font-size:.77rem;color:#8fa4a9;margin-top:7px;}

.section-title{font-size:1.05rem;font-weight:800;color:#eff8f6;margin:6px 0 12px;}
.panel{
 background:#09161e;border:1px solid var(--line);border-radius:15px;padding:18px;
}
.tool-card{
 background:linear-gradient(145deg,#0b1921,#09161e);border:1px solid var(--line);
 border-radius:15px;padding:20px;min-height:145px;
}
.tool-icon{width:36px;height:36px;border-radius:10px;background:rgba(32,222,183,.10);color:var(--mint);
 display:flex;align-items:center;justify-content:center;font-weight:900;margin-bottom:14px;}
.tool-card h4{margin:0 0 6px;color:#f6fbfa;font-size:1.02rem;}
.tool-card p{font-size:.82rem;line-height:1.5;margin:0;color:#81969d!important;}

.empty{
 border:1px dashed #274852;border-radius:14px;padding:28px;background:rgba(10,25,33,.45);
 text-align:center;color:#8ea4aa;
}
.empty b{display:block;color:#e9f4f2;font-size:1rem;margin-bottom:6px;}

.sync-box{
 background:linear-gradient(145deg,#0b1921,#0a161d);border:1px solid #1a3943;border-radius:15px;
 padding:18px 20px;margin-bottom:18px;
}
.sync-head{display:flex;align-items:center;justify-content:space-between;gap:16px;}
.sync-title{font-weight:800;color:#eef8f6;}
.sync-sub{font-size:.78rem;color:#83999f;margin-top:3px;}

.rank-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #142b33;}
.rank-row:last-child{border-bottom:0;}
.rank-pos{width:25px;height:25px;border-radius:50%;background:#10242d;color:#bfd1d4;display:flex;align-items:center;justify-content:center;font-size:.72rem;}
.rank-name{flex:1;color:#dde9e8;font-size:.86rem;}
.rank-gain{color:var(--mint);font-size:.85rem;font-weight:850;}

.stButton>button{
 background:#0c1d25;color:#dce9e8;border:1px solid #244752;border-radius:10px;font-weight:750;
 min-height:40px;
}
.stButton>button:hover{border-color:var(--mint);color:var(--mint);background:#0d222a;}
.stButton>button[kind="primary"]{
 background:var(--mint);color:#062018;border-color:var(--mint);
}
.stButton>button[kind="primary"]:hover{background:#38e7c5;color:#062018;border-color:#38e7c5;}

div[data-testid="stMetric"]{background:#0b1921;border:1px solid var(--line);border-radius:14px;padding:16px;}
div[data-testid="stMetricValue"]{color:var(--mint);}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden;}
[data-testid="stExpander"]{background:#09161e;border:1px solid var(--line);border-radius:12px;}
div[data-baseweb="select"]>div,.stTextInput input{
 background:#0b1921!important;border-color:#244752!important;color:#eef8f6!important;
}
.stProgress>div>div>div>div{background-color:var(--mint)!important;}

.hero-card{background:linear-gradient(145deg,#0b1921,#09161e);border:1px solid #1b3640;border-radius:15px;padding:22px;min-height:200px}.podium-1{border-color:rgba(32,222,183,.6)!important}.podium-2{border-color:rgba(43,156,255,.45)!important}.podium-3{border-color:rgba(168,92,255,.45)!important}.hero-label{color:#20deb7;font-size:.68rem;font-weight:850;letter-spacing:.14em;text-transform:uppercase}.hero-name{font-size:1.48rem;font-weight:900;color:#f7fbfa;margin-top:8px}.hero-player{font-size:.88rem;color:#9aafb3;margin-top:3px}.hero-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:15px}.chip{background:#10232c;border:1px solid #234954;border-radius:999px;color:#cfe0e0;padding:6px 9px;font-size:.72rem}.chip strong{color:#20deb7}.attr-strip{display:flex;gap:5px;flex-wrap:wrap;margin-top:9px}.attr-pill{font-size:.66rem;padding:3px 6px;border-radius:6px;background:#10232b;color:#789096}.attr-up{color:#20deb7;border:1px solid rgba(32,222,183,.22)}.club-card2{background:linear-gradient(145deg,#0b1921,#09161e);border:1px solid #1b3640;border-radius:15px;padding:18px;min-height:145px}.club-pos2{color:#20deb7;font-weight:900;font-size:.68rem;letter-spacing:.12em}.club-name2{font-size:1.08rem;color:#f3faf8;font-weight:850;margin-top:8px}.club-total2{font-size:1.8rem;font-weight:900;color:#20deb7;margin-top:10px}.club-sub2{font-size:.73rem;color:#81979d}.progress-track2{height:6px;background:#10242c;border-radius:99px;margin-top:13px;overflow:hidden}.progress-fill2{height:100%;background:linear-gradient(90deg,#20deb7,#2b9cff);border-radius:99px}.section-head2{display:flex;align-items:center;justify-content:space-between;margin:21px 0 10px}.section-head2 h3{margin:0;font-size:1.06rem}.small-note2{font-size:.72rem;color:#758d93}
</style>
""",unsafe_allow_html=True)

def esc(x): return html.escape(str(x))

def page_head(kicker,title,sub,live=True):
    live_html='<span class="pill"><span class="dot"></span>Live</span>' if live else ''
    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="eyebrow">{esc(kicker)}</div>
        <div class="page-title">{esc(title)}</div>
        <div class="page-sub">{esc(sub)}</div>
      </div>
      <div>{live_html}</div>
    </div>""",unsafe_allow_html=True)

def stat(icon,value,label):
    st.markdown(f'<div class="stat"><div class="stat-icon">{esc(icon)}</div><div class="stat-value">{esc(value)}</div><div class="stat-label">{esc(label)}</div></div>',unsafe_allow_html=True)

def delta_text(v):
    try:
        v=float(v);return f"+{v:g}" if v>0 else f"{v:g}"
    except:return "—"

def fmt_rating(v):
    try:return f"{float(v):.2f}"
    except:return "—"

def podium_card(rank,row):
    gains=[]
    for key,label in [("pace_growth","PAC"),("shooting_growth","SHO"),("passing_growth","PAS"),("dribbling_growth","DRI"),("defense_growth","DEF"),("physical_growth","PHY")]:
        v=row.get(key)
        if v is not None and float(v)>0:gains.append(f'<span class="attr-pill attr-up">{label} +{float(v):g}</span>')
    attrs="".join(gains) or '<span class="attr-pill">No attribute gain</span>'
    cls={1:"podium-1",2:"podium-2",3:"podium-3"}.get(rank,"")
    html_box=f'<div class="hero-card {cls}"><div class="hero-label">#{rank} · {esc(row["owner"])}</div><div class="hero-name">{esc(row["player"])}</div><div class="hero-player">OVR {esc(row["ovr"])} · {esc(row.get("club") or "—")}</div><div class="hero-chips"><span class="chip">OVR <strong>{delta_text(row["ovr_growth"])}</strong></span><span class="chip">ATTR <strong>{delta_text(row.get("attribute_growth",0))}</strong></span><span class="chip">Rating <strong>{fmt_rating(row.get("avg_rating"))}</strong></span><span class="chip">Apps <strong>{esc(row.get("apps") or 0)}</strong></span></div><div class="attr-strip">{attrs}</div></div>'
    st.markdown(html_box,unsafe_allow_html=True)

def valid_wallet(v):
    v=(v or "").strip()
    return len(v)>=10 and v.lower().startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in v[2:])

DEFAULT_WALLET="0x65cc0e72dd71ad80"
if "wallet" not in st.session_state: st.session_state.wallet=DEFAULT_WALLET

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("""<div class="brand">
      <div class="logo">MFL<span class="crown">♛</span></div>
      <div class="logo-sub">MANAGEMENT HUB</div>
      <div class="logo-line"></div>
    </div>""",unsafe_allow_html=True)

    page=st.radio(
        "Navigation",
        ["Home","Grower or Shower","Agency Development","Club Development"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("WALLET")
    st.code(st.session_state.wallet,language=None)
    if st.button("Change wallet",use_container_width=True):
        st.session_state.edit_wallet=not st.session_state.get("edit_wallet",False)
    if st.session_state.get("edit_wallet"):
        nw=st.text_input("Wallet",value=st.session_state.wallet,label_visibility="collapsed")
        if st.button("Use wallet",use_container_width=True):
            if valid_wallet(nw):
                st.session_state.wallet=nw.strip().lower()
                st.session_state.edit_wallet=False
                st.rerun()
            else:
                st.error("Enter a valid 0x wallet.")

    st.divider()
    st.markdown('<span class="pill"><span class="dot"></span>Season 17</span>',unsafe_allow_html=True)
    st.caption("TRUE ALL-REMAINING v6.1")

wallet=st.session_state.wallet

# ---------------- HOME ----------------
if page=="Home":
    page_head("MFL · MANAGEMENT HUB","Good to see you!","Track. Analyse. Develop. All in one place.")
    try:
        c=agency.db();agency.init(c);agency.ensure_v2(c)
        players=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=?",(wallet.lower(),)).fetchone()[0]
        improved=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=? AND current_ovr>start_ovr",(wallet.lower(),)).fetchone()[0]
        c.close()
    except Exception:
        players=0;improved=0

    try:
        mine=club.owned_clubs(wallet)
    except Exception:
        mine=[]

    cached=club.cached(wallet)
    ovr=float(cached["ovr_gain"].fillna(0).sum()) if not cached.empty else 0

    cols=st.columns(4)
    with cols[0]: stat("◆",len(mine) if mine else "—","Owned Clubs")
    with cols[1]: stat("●",players or "—","Players Tracked")
    with cols[2]: stat("▲",f"+{ovr:g}" if not cached.empty else "—","Club OVR Loaded")
    with cols[3]: stat("▥",improved,"Agency Players Improved")

    st.write("")
    st.markdown('<div class="section-title">Your tools</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    with a:
        st.markdown("""<div class="tool-card"><div class="tool-icon">G</div><h4>Grower or Shower</h4>
        <p>Competition standings, OVR growth, attribute gains and Season 17 ratings.</p></div>""",unsafe_allow_html=True)
    with b:
        st.markdown("""<div class="tool-card"><div class="tool-icon" style="color:#2b9cff;background:rgba(43,156,255,.10)">A</div><h4>Agency Development</h4>
        <p>Player baselines, new mints, tags, notes and development history.</p></div>""",unsafe_allow_html=True)
    with c:
        st.markdown("""<div class="tool-card"><div class="tool-icon" style="color:#a85cff;background:rgba(168,92,255,.10)">C</div><h4>Club Development</h4>
        <p>Season 17 development across clubs verified as MFL_OWNER only.</p></div>""",unsafe_allow_html=True)

    st.write("")
    left,right=st.columns([1.45,1])
    with left:
        st.markdown('<div class="section-title">Club development coverage</div>',unsafe_allow_html=True)
        if cached.empty:
            st.markdown('<div class="empty"><b>No club progression synced yet</b>Open Club Development and sync the first batch.</div>',unsafe_allow_html=True)
        else:
            temp=cached.copy()
            temp["checked_at"]=pd.to_datetime(temp["checked_at"],utc=True,errors="coerce")
            daily=temp.groupby(temp["checked_at"].dt.date)["ovr_gain"].sum().cumsum()
            if len(daily)>1: st.line_chart(daily,height=260)
            else: st.bar_chart(temp.groupby("club")["ovr_gain"].sum().sort_values(ascending=False).head(8),height=260)
    with right:
        st.markdown('<div class="section-title">Top clubs loaded</div>',unsafe_allow_html=True)
        if cached.empty:
            st.markdown('<div class="empty"><b>Waiting for club data</b>Your first synced batch will appear here.</div>',unsafe_allow_html=True)
        else:
            rank=cached.groupby("club")["ovr_gain"].sum().sort_values(ascending=False).head(5)
            body=""
            for i,(name,gain) in enumerate(rank.items(),1):
                body+=f'<div class="rank-row"><div class="rank-pos">{i}</div><div class="rank-name">{esc(name)}</div><div class="rank-gain">+{gain:g}</div></div>'
            st.markdown(f'<div class="panel">{body}</div>',unsafe_allow_html=True)

# ---------------- GROWER ----------------
elif page=="Grower or Shower":
    page_head("WORKTHESPACE · SEASON 17","Grower or Shower","Live development race · OVR first, attribute growth second, rating next.")
    with st.expander("Competition settings"):
        grower_start=st.text_input("Competition / Season 17 baseline (UTC)",value=st.session_state.get("grower_start","2026-09-22T00:00:00Z"));st.session_state.grower_start=grower_start;os.environ["GROWER_START"]=grower_start
    conn=grower.db();grower.init_db(conn)
    c1,c2=st.columns([1,4])
    with c1:refresh=st.button("Refresh entrants",type="primary",use_container_width=True)
    if refresh:
        try:
            tok=grower.refresh_access_token();bar=st.progress(0,text="Refreshing 14 entrants…");errs=[]
            for i,(pid,owner) in enumerate(grower.ENTRANTS.items(),1):
                try:grower.sync_player(conn,tok,pid,owner)
                except Exception:errs.append(owner)
                bar.progress(i/len(grower.ENTRANTS),text=f"{i}/{len(grower.ENTRANTS)} entrants")
            bar.empty();st.success("Competition refreshed." if not errs else f"Refreshed with {len(errs)} skipped entrant(s).")
        except Exception as e:st.error("MFL could not refresh the competition.");st.code(str(e))
    rows=grower.leaderboard(conn)
    if not rows:st.markdown('<div class="empty"><b>No competition data yet</b>Press Refresh entrants once.</div>',unsafe_allow_html=True)
    else:
        cols=st.columns(3)
        for col,(rank,row) in zip(cols,enumerate(rows[:3],1)):
            with col:podium_card(rank,row)
        st.markdown('<div class="section-head2"><h3>Live standings</h3><span class="small-note2">OVR → ATTR → Rating</span></div>',unsafe_allow_html=True)
        table=[]
        for i,r in enumerate(rows,1):
            table.append({"#":i,"Owner":r["owner"],"Player":r["player"],"OVR":r["ovr"],"OVR ↑":delta_text(r["ovr_growth"]),"ATTR ↑":delta_text(r.get("attribute_growth",0)),"Rating":r["avg_rating"],"Apps":r["apps"],"PAC ↑":delta_text(r["pace_growth"]),"SHO ↑":delta_text(r["shooting_growth"]),"PAS ↑":delta_text(r["passing_growth"]),"DRI ↑":delta_text(r["dribbling_growth"]),"DEF ↑":delta_text(r["defense_growth"]),"PHY ↑":delta_text(r["physical_growth"])})
        st.dataframe(pd.DataFrame(table),use_container_width=True,hide_index=True,height=560)
        growers=[r for r in rows if (r.get("attribute_growth") or 0)>0]
        if growers:
            st.markdown('<div class="section-head2"><h3>Attribute growers</h3></div>',unsafe_allow_html=True)
            gc=st.columns(min(3,len(growers)))
            for col,row in zip(gc,growers[:3]):
                gains=[]
                for key,label in [("pace_growth","PAC"),("shooting_growth","SHO"),("passing_growth","PAS"),("dribbling_growth","DRI"),("defense_growth","DEF"),("physical_growth","PHY")]:
                    v=row.get(key)
                    if v is not None and float(v)>0:gains.append(f"{label} +{float(v):g}")
                with col:st.markdown(f'<div class="tool-card"><div class="tool-icon">↑</div><h4>{esc(row["player"])}</h4><p><strong style="color:#20deb7">{esc(row["owner"])}</strong><br>{" · ".join(gains)}<br>Rating {fmt_rating(row.get("avg_rating"))} · {row.get("apps") or 0} apps</p></div>',unsafe_allow_html=True)
    conn.close()

# ---------------- AGENCY ----------------
elif page=="Agency Development":
    page_head("PLAYER DEVELOPMENT","Agency Development","Track ownership baselines, tags, new mints and player progression.")
    c=agency.db();agency.init(c);agency.ensure_v2(c)
    rows=c.execute("""SELECT o.*,COALESCE(t.tag,'NORMAL') tag,COALESCE(t.note,'') note,
      m.age,m.position,m.club,a.last_event_at,a.match_events,a.training_events,a.total_events
      FROM ownership_v65 o
      LEFT JOIN tags t ON t.wallet=o.wallet AND t.player_id=o.player_id
      LEFT JOIN player_meta m ON m.wallet=o.wallet AND m.player_id=o.player_id
      LEFT JOIN activity a ON a.wallet=o.wallet AND a.player_id=o.player_id
      WHERE o.wallet=?""",(wallet.lower(),)).fetchall()
    if not rows:
        st.markdown('<div class="empty"><b>No seeded agency data for this wallet</b>Use your main wallet or build its agency cache first.</div>',unsafe_allow_html=True)
    else:
        df=pd.DataFrame([dict(r) for r in rows])
        for lab,cur,start in [
            ("OVR ↑","current_ovr","start_ovr"),("PAC ↑","current_pac","start_pac"),("SHO ↑","current_sho","start_sho"),
            ("PAS ↑","current_pas","start_pas"),("DRI ↑","current_dri","start_dri"),("DEF ↑","current_def","start_def"),("PHY ↑","current_phy","start_phy")]:
            df[lab]=pd.to_numeric(df[cur],errors="coerce")-pd.to_numeric(df[start],errors="coerce")
        df["Acquired"]=pd.to_datetime(df.acquired_at,utc=True,errors="coerce")
        df["Initial date"]=pd.to_datetime(df.history_start,utc=True,errors="coerce")

        m=st.columns(4)
        with m[0]: stat("●",len(df),"Players")
        with m[1]: stat("▲",int((df["OVR ↑"]>0).sum()),"Improved OVR")
        with m[2]: stat("◆",int((df.source=="NEW MINT / ORIGINAL").sum()),"New / Original")
        with m[3]: stat("★",int((df.tag=="PRIORITY").sum()),"Priority")

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
            if mine.empty:
                st.markdown('<div class="empty"><b>No tagged players yet</b>Add DEVELOP, PRIORITY or WATCH tags below.</div>',unsafe_allow_html=True)
            else:
                st.dataframe(mine[["tag","player_name","age","current_ovr","OVR ↑","note"]]
                             .rename(columns={"player_name":"Player","age":"Age","current_ovr":"OVR","tag":"Tag","note":"Note"}),
                             use_container_width=True,hide_index=True)
            opts={f"{r.player_name} · {int(r.player_id)}":int(r.player_id) for _,r in df.sort_values("player_name").iterrows()}
            who=st.selectbox("Player",list(opts))
            ex=df[df.player_id==opts[who]].iloc[0]
            tags=["NORMAL","DEVELOP","PRIORITY","WATCH"]
            tag=st.selectbox("Tag",tags,index=tags.index(ex.tag) if ex.tag in tags else 0)
            note=st.text_input("Note",value=ex.note or "")
            if st.button("Save tag",type="primary"):
                c.execute("""INSERT INTO tags(wallet,player_id,tag,note) VALUES(?,?,?,?)
                ON CONFLICT(wallet,player_id) DO UPDATE SET tag=excluded.tag,note=excluded.note""",
                          (wallet.lower(),opts[who],tag,note))
                c.commit();st.rerun()
        with tabs[3]:
            q=st.text_input("Search players",placeholder="Search by player name")
            v=df if not q else df[df.player_name.str.contains(q,case=False,na=False)]
            sort=st.selectbox("Sort",["OVR gain","OVR","Age","Name"])
            if sort=="OVR gain":v=v.sort_values(["OVR ↑","current_ovr"],ascending=False,na_position="last")
            elif sort=="OVR":v=v.sort_values("current_ovr",ascending=False,na_position="last")
            elif sort=="Age":v=v.sort_values("age",na_position="last")
            else:v=v.sort_values("player_name")
            st.dataframe(v[["player_name","age","position","club","source","Acquired","start_ovr","current_ovr","OVR ↑","tag"]]
                         .rename(columns={"player_name":"Player","age":"Age","position":"Position","club":"Club","source":"Ownership","start_ovr":"Start","current_ovr":"OVR","tag":"Tag"}),
                         use_container_width=True,hide_index=True)

        with st.expander("Refresh player data"):
            st.caption("Refreshes 20 players at a time so MFL rate limits cannot lock the page.")
            if st.button("Refresh next 20 players"):
                bar=st.progress(0,text="Refreshing players…")
                def prog(n,total):bar.progress(n/max(total,1),text=f"{n}/{min(total,20)}")
                try:
                    done,total,errs=agency.refresh_current_v21(wallet,prog,20)
                    bar.empty()
                    st.success(f"Updated {done} players." if not errs else f"Updated {done}; {len(errs)} issue(s).")
                except Exception as e:
                    bar.empty();st.error("MFL could not refresh this batch.")
                    with st.expander("Technical detail"):st.code(str(e))
    c.close()

# ---------------- CLUBS ----------------
elif page=="Club Development":
    page_head("CLUB ANALYTICS · SEASON 17","Club Development","Which of your owned clubs is producing the most development?")
    with st.expander("Season settings"):
        season_start=st.text_input("Season 17 baseline (UTC)",value=st.session_state.get("season_start","2026-09-22T00:00:00Z"));st.session_state.season_start=season_start
        st.caption("One click processes every remaining owned-club player slowly and automatically.")
    try:mine=club.owned_clubs(wallet)
    except Exception:mine=[]
    cached=club.cached(wallet)
    top=st.columns(4)
    with top[0]:stat("◆",len(mine) if mine else "—","Owned Clubs")
    with top[1]:stat("●",len(cached),"Players Synced")
    with top[2]:stat("▲",f"+{cached['ovr_gain'].fillna(0).sum():g}" if not cached.empty else "—","S17 OVR Loaded")
    with top[3]:stat("▥",f"+{cached['attr_gain'].fillna(0).sum():g}" if not cached.empty else "—","Attributes Loaded")
    st.markdown('<div class="section-head2"><h3>Progression sync</h3><span class="small-note2">Resumes from your existing saved players</span></div>',unsafe_allow_html=True)
    remaining=club.cooldown_remaining()
    if remaining>0:
        mins=max(1,math.ceil(remaining/60))
        st.info(f"MFL cooldown active — wait about {mins} minute(s). Your {len(cached)} synced players are still saved.")
    b1,b2=st.columns([1,4])
    with b1:do_sync=st.button("Sync all remaining",type="primary",use_container_width=True,disabled=remaining>0)
    if do_sync:
        bar=st.progress(0,text="Preparing batch…");status=st.empty()
        def prog(done,total,errs):bar.progress(done/max(total,1),text=f"{done}/{total} players");status.caption(f"{errs} skipped/failed")
        try:
            res=club.sync_batch(wallet,season_start,None,prog);bar.empty();status.empty()
            if res.get("rate_limited"):
                mins=max(1,math.ceil(res.get("cooldown",0)/60))
                st.warning(f"MFL finally imposed a rate limit after {res['saved']} new player(s). Everything completed is saved. Wait about {mins} minute(s); one click will resume the remaining players.")
            elif any("MFL_TIMEOUT" in str(x[1]) for x in res.get("errors",[])):
                st.warning(f"The full run finished with {len(res['errors'])} slow player(s) left for the next run. {res['saved']} player(s) were saved.")
            elif res["errors"]:
                st.warning(f"Saved {res['saved']}; {len(res['errors'])} player(s) skipped.")
            else:
                st.success(f"Saved {res['saved']} players. Batch complete.")
            st.rerun()
        except Exception as e:
            bar.empty();status.empty()
            msg=str(e)
            if "MFL_TIMEOUT" in msg or "Read timed out" in msg:
                st.warning("MFL is responding slowly. Nothing already synced has been lost. Wait a moment and try the next batch again.")
            else:
                st.error("MFL could not complete this batch.")
                with st.expander("Technical detail"):st.code(msg)
    cached=club.cached(wallet)
    if cached.empty:st.markdown('<div class="empty"><b>No progression synced yet</b>Press Sync next 30. The old zero-only cache has been discarded.</div>',unsafe_allow_html=True)
    else:
        good=cached[cached["error"].isna()] if "error" in cached.columns else cached
        clubs=good.groupby("club").agg(Players=("player_id","count"),OVR=("ovr_gain","sum"),Attributes=("attr_gain","sum"),PAC=("pac","sum"),SHO=("sho","sum"),PAS=("pas","sum"),DRI=("dri","sum"),DEF=("defn","sum"),PHY=("phy","sum")).reset_index().sort_values(["OVR","Attributes"],ascending=False)
        st.markdown('<div class="section-head2"><h3>Top developing clubs</h3><span class="small-note2">Loaded Season 17 data</span></div>',unsafe_allow_html=True)
        topclubs=clubs.head(3);cols=st.columns(3);mx=max(float(topclubs["Attributes"].max()) if not topclubs.empty else 1,1)
        for i,(col,row) in enumerate(zip(cols,topclubs.to_dict("records")),1):
            pct=min(100,max(5,float(row["Attributes"])/mx*100))
            html_box=f'<div class="club-card2"><div class="club-pos2">#{i} DEVELOPMENT</div><div class="club-name2">{esc(row["club"])}</div><div class="club-total2">+{row["OVR"]:g} OVR</div><div class="club-sub2">{int(row["Players"])} players · +{row["Attributes"]:g} attributes</div><div class="progress-track2"><div class="progress-fill2" style="width:{pct:.0f}%"></div></div></div>'
            with col:st.markdown(html_box,unsafe_allow_html=True)
        st.markdown('<div class="section-head2"><h3>Club leaderboard</h3></div>',unsafe_allow_html=True)
        st.dataframe(clubs.rename(columns={"club":"Club","OVR":"OVR ↑","Attributes":"ATTR ↑"}),use_container_width=True,hide_index=True,height=min(520,75+35*len(clubs)))
        if not clubs.empty:
            left,right=st.columns([1.55,1])
            with left:
                choice=st.selectbox("Club detail",clubs["club"].tolist());detail=good[good.club==choice].sort_values(["ovr_gain","attr_gain"],ascending=False);st.dataframe(detail[["player","start_ovr","current_ovr","ovr_gain","attr_gain","pac","sho","pas","dri","defn","phy"]].rename(columns={"player":"Player","start_ovr":"S17 Start","current_ovr":"Current","ovr_gain":"OVR ↑","attr_gain":"ATTR ↑","pac":"PAC ↑","sho":"SHO ↑","pas":"PAS ↑","dri":"DRI ↑","defn":"DEF ↑","phy":"PHY ↑"}),use_container_width=True,hide_index=True)
            with right:
                body=""
                for i,x in enumerate(mine,1):
                    crow=clubs[clubs.club==x["name"]];gain=float(crow.iloc[0]["OVR"]) if not crow.empty else 0;body+=f'<div class="rank-row"><div class="rank-pos">{i}</div><div class="rank-name">{esc(x["name"])}</div><div class="rank-gain">+{gain:g}</div></div>'
                st.markdown(f'<div class="panel">{body}</div>',unsafe_allow_html=True)
        st.caption("Progression is rebuilt cumulatively from MFL events in this version. Continue syncing batches until coverage is complete.")

