
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

# ---------------- PRODUCT UI ----------------
st.markdown("""
<style>
:root{--bg:#061016;--panel:#091920;--panel2:#0c2028;--line:#173944;--text:#f3faf8;--muted:#718a90;--mint:#20e0b2;--blue:#48a6ff;--violet:#9275ff}
.stApp{background:radial-gradient(800px 400px at 80% -10%,rgba(32,224,178,.06),transparent 60%),#061016}
[data-testid="stHeader"]{background:rgba(6,16,22,.85);border-bottom:1px solid #102b34}
[data-testid="stSidebar"]{background:#07151c!important;border-right:1px solid #16343d!important;min-width:260px!important}
[data-testid="stSidebarContent"]{padding:0!important}
.block-container{max-width:1420px!important;padding:1.7rem 2.2rem 4rem!important}
#MainMenu,footer,[data-testid="stDecoration"]{display:none!important}
.brand-shell{padding:25px 20px 19px;border-bottom:1px solid #15333c}
.brand-row{display:flex;align-items:center;gap:12px}.brand-logo{width:51px;height:51px}
.brand-title{font-size:.98rem;font-weight:900;color:#f4faf8;letter-spacing:-.035em}.brand-title b{color:#20e0b2}
.brand-sub{font-size:.56rem;color:#607b82;font-weight:850;letter-spacing:.16em;margin-top:6px}
.brand-season{margin-top:15px;display:flex;align-items:center;gap:8px;font-size:.57rem;color:#607c83;font-weight:800;letter-spacing:.08em}
.brand-season i{width:21px;height:2px;border-radius:9px;background:#20e0b2}
[data-testid="stSidebar"] [role="radiogroup"]{gap:4px;padding:13px}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:10px;padding:9px 11px!important;border:1px solid transparent}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#0a1d25}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#0c252d;border-color:#1d4b55;box-shadow:inset 3px 0 0 #20e0b2}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none!important}
[data-testid="stSidebar"] [role="radiogroup"] p{font-size:.78rem!important;color:#9eb2b6!important;font-weight:720!important}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#f0f8f6!important}
.side-section{padding:20px 14px 0;margin-top:4px;border-top:1px solid #14313a}.side-label{font-size:.54rem;color:#557179;letter-spacing:.15em;font-weight:900;margin-bottom:8px}
.wallet-chip{font-family:monospace;font-size:.65rem;color:#aec1c4;background:#091c24;border:1px solid #173d47;border-radius:9px;padding:10px}.build{font-size:.56rem;color:#425e65;margin-top:13px;letter-spacing:.08em}
.topline{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:19px}.crumb{font-size:.57rem;color:#20e0b2;letter-spacing:.16em;font-weight:900;text-transform:uppercase}
.h1{font-size:2rem;line-height:1.03;font-weight:930;color:#f6fbfa;letter-spacing:-.055em;margin-top:7px}.subtitle{font-size:.78rem;color:#708a90;margin-top:6px}
.live{display:flex;align-items:center;gap:7px;font-size:.60rem;color:#94abae;border:1px solid #1a414b;background:#091b23;border-radius:999px;padding:7px 10px}.live:before{content:"";width:6px;height:6px;border-radius:50%;background:#20e0b2;box-shadow:0 0 0 4px rgba(32,224,178,.08)}
.overview{display:grid;grid-template-columns:1.65fr .75fr;gap:13px;margin-bottom:13px}
.hero-v9{position:relative;overflow:hidden;min-height:230px;background:linear-gradient(135deg,#0c2028,#091820);border:1px solid #1a404a;border-radius:18px;padding:27px}
.hero-v9:after{content:"";position:absolute;right:-75px;top:-85px;width:280px;height:280px;border-radius:50%;border:42px solid rgba(32,224,178,.035)}
.hero-kicker-v9{font-size:.57rem;color:#20e0b2;letter-spacing:.16em;font-weight:900}.hero-title-v9{font-size:2.05rem;color:#f5fbfa;font-weight:930;letter-spacing:-.055em;line-height:1.04;margin-top:10px;max-width:550px}
.hero-copy-v9{font-size:.77rem;color:#799198;line-height:1.6;margin-top:12px;max-width:560px}.hero-chips-v9{display:flex;flex-wrap:wrap;gap:7px;margin-top:20px}
.hero-chip-v9{font-size:.60rem;color:#9bb1b4;background:#0d252d;border:1px solid #214852;border-radius:999px;padding:6px 9px}.hero-chip-v9 b{color:#20e0b2}
.snapshot{background:linear-gradient(145deg,#0b1d25,#08171e);border:1px solid #183b45;border-radius:18px;padding:20px}.snap-label{font-size:.57rem;color:#5d7b82;letter-spacing:.13em;font-weight:900}
.snap-big{font-size:2.5rem;color:#20e0b2;font-weight:950;letter-spacing:-.07em;margin-top:18px}.snap-copy{font-size:.68rem;color:#789198;margin-top:3px}.snap-line{height:1px;background:#16343d;margin:18px 0}
.snap-row{display:flex;justify-content:space-between;gap:12px;font-size:.66rem;color:#789198;margin-top:9px}.snap-row b{color:#d8e6e4}
.kpis-v9{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin-bottom:21px}.kpi-v9{background:#091920;border:1px solid #173944;border-radius:14px;padding:16px 17px;min-height:105px}
.kpi-head-v9{display:flex;justify-content:space-between}.kpi-icon-v9{font-size:.56rem;font-weight:900;color:#20e0b2;background:#0d2a31;border:1px solid #17464f;border-radius:7px;padding:5px 7px}.kpi-season-v9{font-size:.49rem;color:#49666d;letter-spacing:.1em;font-weight:850}
.kpi-value-v9{font-size:1.62rem;font-weight:930;color:#f3faf8;letter-spacing:-.05em;margin-top:13px;line-height:1}.kpi-label-v9{font-size:.62rem;color:#6e888e;margin-top:6px}
.section-v9{display:flex;align-items:end;justify-content:space-between;margin:23px 0 10px}.section-v9 h3{font-size:.91rem!important;margin:0;color:#eaf4f2}.section-v9 span{font-size:.51rem;color:#4f6b72;letter-spacing:.12em;font-weight:850}
.workspace-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}.workspace{position:relative;background:#091920;border:1px solid #173944;border-radius:14px;padding:18px;min-height:137px}
.workspace-no{font-size:.51rem;color:#49676e;letter-spacing:.13em;font-weight:900}.workspace h4{font-size:.9rem;margin:17px 0 7px;color:#eef7f5}.workspace p{font-size:.67rem!important;line-height:1.5!important;color:#6e888f!important;margin:0}
.workspace-arrow{position:absolute;right:16px;top:15px;color:#385961}.workspace-accent{position:absolute;left:18px;bottom:0;width:38px;height:2px;background:#20e0b2}
.panel,.sync-box{background:#091920;border:1px solid #173944;border-radius:14px;padding:17px}.rank-row{display:grid;grid-template-columns:27px 1fr auto;gap:9px;align-items:center;padding:10px 0;border-bottom:1px solid #13313a}.rank-row:last-child{border-bottom:0}
.rank-pos{width:24px;height:24px;border-radius:7px;background:#0e2730;color:#8fa6aa;display:flex;align-items:center;justify-content:center;font-size:.61rem;font-weight:850}.rank-name{font-size:.72rem;color:#d9e6e4;font-weight:720}.rank-gain{font-size:.72rem;color:#20e0b2;font-weight:900}
.hero-card{background:#091920!important;border:1px solid #173944!important;border-radius:14px!important;padding:18px!important}.podium-1{border-color:rgba(32,224,178,.48)!important}.podium-2{border-color:rgba(72,166,255,.35)!important}.podium-3{border-color:rgba(146,117,255,.35)!important}
.club-card2{background:#091920!important;border:1px solid #173944!important;border-radius:14px!important}
.stButton>button{background:#0a2028!important;color:#d5e3e1!important;border:1px solid #214a55!important;border-radius:9px!important;font-weight:720!important;font-size:.72rem!important}
.stButton>button[kind="primary"]{background:#20dbae!important;color:#032019!important;border-color:#20dbae!important}
[data-testid="stDataFrame"]{border:1px solid #173944!important;border-radius:12px!important;overflow:hidden}[data-testid="stExpander"]{background:#08171e!important;border:1px solid #173944!important;border-radius:11px!important}
div[data-baseweb="select"]>div,.stTextInput input{background:#091b23!important;border-color:#1d424c!important;color:#e9f3f1!important;border-radius:9px!important}
[data-baseweb="tab-list"]{background:#08171e!important;border:1px solid #173944!important;border-radius:10px!important;padding:4px!important;gap:4px!important}
[data-baseweb="tab"][aria-selected="true"]{background:#0d2830!important;color:#20e0b2!important}
.stProgress>div>div>div>div{background:#20e0b2!important}
@media(max-width:900px){.overview{grid-template-columns:1fr}.kpis-v9,.workspace-grid{grid-template-columns:1fr 1fr}.block-container{padding:1.2rem!important}}
</style>
""",unsafe_allow_html=True)

def esc(x): return html.escape(str(x))

def page_head(kicker,title,sub):
    html = f'<div class="topline"><div><div class="crumb">{esc(kicker)}</div><div class="h1">{esc(title)}</div><div class="subtitle">{esc(sub)}</div></div><div class="live">LIVE</div></div>'
    st.markdown(html,unsafe_allow_html=True)

def stat(icon,value,label):
    html = f'<div class="kpi-v9"><div class="kpi-head-v9"><span class="kpi-icon-v9">{esc(icon)}</span><span class="kpi-season-v9">S17</span></div><div class="kpi-value-v9">{esc(value)}</div><div class="kpi-label-v9">{esc(label)}</div></div>'
    st.markdown(html,unsafe_allow_html=True)


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
    st.markdown("""
    <div class="brand-shell"><div class="brand-row">
      <svg class="brand-logo" viewBox="0 0 64 64" aria-label="MFL">
        <defs><linearGradient id="mflg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#5bf1d1"/><stop offset="1" stop-color="#16c69e"/></linearGradient></defs>
        <path d="M32 3 56 12v17c0 15.2-9.7 25.5-24 31C17.7 54.5 8 44.2 8 29V12L32 3Z" fill="#0a2028" stroke="#20e0b2" stroke-width="2"/>
        <path d="M18 18h6l3 6 5-9 5 9 3-6h6l-4 11H22l-4-11Z" fill="url(#mflg)"/>
        <text x="32" y="45" text-anchor="middle" fill="#f4fbfa" font-size="14" font-family="Arial" font-weight="900">MFL</text>
      </svg>
      <div><div class="brand-title"><b>MFL</b> Management</div><div class="brand-sub">PERFORMANCE HUB</div></div>
    </div><div class="brand-season"><i></i> SEASON 17 · LIVE</div></div>
    """,unsafe_allow_html=True)
    page=st.radio("Navigation",["Home","Grower or Shower","Agency Development","Club Development"],label_visibility="collapsed")
    st.markdown('<div class="side-section"><div class="side-label">ACTIVE WALLET</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="wallet-chip">{esc(st.session_state.wallet)}</div>',unsafe_allow_html=True)
    if st.button("Change wallet",use_container_width=True):
        st.session_state.edit_wallet=not st.session_state.get("edit_wallet",False)
    if st.session_state.get("edit_wallet"):
        nw=st.text_input("Wallet",value=st.session_state.wallet,label_visibility="collapsed")
        if st.button("Use wallet",use_container_width=True):
            if valid_wallet(nw):
                st.session_state.wallet=nw.strip().lower();st.session_state.edit_wallet=False;st.rerun()
            else: st.error("Enter a valid 0x wallet.")
    st.markdown('<div class="build">PRODUCT UI · v9</div></div>',unsafe_allow_html=True)

wallet=st.session_state.wallet

# ---------------- HOME ----------------
if page=="Home":
    try:
        c=agency.db();agency.init(c);agency.ensure_v2(c)
        players=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=?",(wallet.lower(),)).fetchone()[0]
        improved=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=? AND current_ovr>start_ovr",(wallet.lower(),)).fetchone()[0]
        c.close()
    except Exception:
        players=0; improved=0
    try: mine=club.owned_clubs(wallet)
    except Exception: mine=[]
    cached=club.cached(wallet)
    ovr=float(cached["ovr_gain"].fillna(0).sum()) if not cached.empty else 0
    attrs=float(cached["attr_gain"].fillna(0).sum()) if not cached.empty else 0
    synced=len(cached)

    page_head("MFL · SEASON 17","Management Hub","Your agency and club network at a glance.")

    overview = f"""
    <div class="overview">
      <div class="hero-v9">
        <div class="hero-kicker-v9">SEASON 17 PERFORMANCE</div>
        <div class="hero-title-v9">One place to see<br>what's actually improving.</div>
        <div class="hero-copy-v9">Track your players, compare your clubs and follow Grower or Shower without jumping between separate tools.</div>
        <div class="hero-chips-v9"><span class="hero-chip-v9"><b>{len(mine) if mine else "—"}</b> clubs</span><span class="hero-chip-v9"><b>{players or "—"}</b> players</span><span class="hero-chip-v9"><b>{synced}</b> club players synced</span></div>
      </div>
      <div class="snapshot"><div class="snap-label">NETWORK DEVELOPMENT</div><div class="snap-big">+{ovr:g}</div><div class="snap-copy">OVR gained in loaded S17 club data</div>
        <div class="snap-line"></div><div class="snap-row"><span>Attribute gains</span><b>+{attrs:g}</b></div><div class="snap-row"><span>Agency improved</span><b>{improved}</b></div><div class="snap-row"><span>Owned clubs</span><b>{len(mine) if mine else "—"}</b></div>
      </div>
    </div>
    <div class="kpis-v9">
      <div class="kpi-v9"><div class="kpi-head-v9"><span class="kpi-icon-v9">CL</span><span class="kpi-season-v9">S17</span></div><div class="kpi-value-v9">{len(mine) if mine else "—"}</div><div class="kpi-label-v9">Owned clubs</div></div>
      <div class="kpi-v9"><div class="kpi-head-v9"><span class="kpi-icon-v9">PL</span><span class="kpi-season-v9">LIVE</span></div><div class="kpi-value-v9">{players or "—"}</div><div class="kpi-label-v9">Agency players</div></div>
      <div class="kpi-v9"><div class="kpi-head-v9"><span class="kpi-icon-v9">↑</span><span class="kpi-season-v9">S17</span></div><div class="kpi-value-v9">+{attrs:g}</div><div class="kpi-label-v9">Club attribute gains</div></div>
      <div class="kpi-v9"><div class="kpi-head-v9"><span class="kpi-icon-v9">DV</span><span class="kpi-season-v9">AGENCY</span></div><div class="kpi-value-v9">{improved}</div><div class="kpi-label-v9">Players improved</div></div>
    </div>
    """
    st.markdown(overview,unsafe_allow_html=True)
    st.markdown('<div class="section-v9"><h3>Workspaces</h3><span>MANAGEMENT TOOLS</span></div>',unsafe_allow_html=True)
    st.markdown("""<div class="workspace-grid">
      <div class="workspace"><span class="workspace-arrow">↗</span><div class="workspace-no">01 · COMPETITION</div><h4>Grower or Shower</h4><p>Live ranking, ratings and individual stat gains.</p><div class="workspace-accent"></div></div>
      <div class="workspace"><span class="workspace-arrow">↗</span><div class="workspace-no">02 · AGENCY</div><h4>Player Development</h4><p>Ownership baselines, new mints and priority players.</p><div class="workspace-accent" style="background:#48a6ff"></div></div>
      <div class="workspace"><span class="workspace-arrow">↗</span><div class="workspace-no">03 · CLUBS</div><h4>Club Development</h4><p>Compare progression across the full owned network.</p><div class="workspace-accent" style="background:#9275ff"></div></div>
    </div>""",unsafe_allow_html=True)
    if not cached.empty:
        st.markdown('<div class="section-v9"><h3>Top developing clubs</h3><span>LOADED S17 DATA</span></div>',unsafe_allow_html=True)
        ranks=cached.groupby("club").agg(ovr=("ovr_gain","sum"),attrs=("attr_gain","sum"),players=("player_id","count")).sort_values(["ovr","attrs"],ascending=False).head(5)
        body=""
        for i,(name,row) in enumerate(ranks.iterrows(),1):
            body += f'<div class="rank-row"><div class="rank-pos">{i}</div><div class="rank-name">{esc(name)}<div style="font-size:.56rem;color:#58747b;margin-top:2px">{int(row["players"])} players · +{row["attrs"]:g} attributes</div></div><div class="rank-gain">+{row["ovr"]:g} OVR</div></div>'
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

