
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

# ---------------- DESIGN SYSTEM ----------------
st.markdown("""
<style>
:root{
 --bg:#050d12; --bg-soft:#071219; --panel:#091820; --panel2:#0c1d26;
 --line:#163640; --line2:#22505c; --text:#f5fbfa; --muted:#789097;
 --mint:#20e2b5; --mint-soft:#8ff6df; --blue:#4ba6ff; --violet:#9a72ff;
}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.stApp{
 background:
 radial-gradient(900px 500px at 82% -8%,rgba(32,226,181,.075),transparent 60%),
 radial-gradient(700px 520px at 0% 100%,rgba(75,166,255,.045),transparent 65%),
 linear-gradient(180deg,#050d12,#071118 62%,#061016);
 color:var(--text)
}
[data-testid="stHeader"]{background:rgba(5,13,18,.78);backdrop-filter:blur(16px);border-bottom:1px solid rgba(22,54,64,.45)}
[data-testid="stToolbar"]{opacity:.55}
[data-testid="stSidebar"]{
 background:linear-gradient(180deg,#061118 0%,#07151c 100%)!important;
 border-right:1px solid #15343e!important; min-width:278px!important
}
[data-testid="stSidebarContent"]{padding:1.05rem 1rem 1rem!important}
.block-container{max-width:1500px!important;padding:2rem 2.6rem 4rem!important}
h1,h2,h3,h4{color:var(--text);letter-spacing:-.04em}
p,label,.stCaption{color:var(--muted)!important}
hr{border-color:#15343e!important}

/* Logo */
.mfl-brand{padding:5px 3px 23px;margin-bottom:14px;border-bottom:1px solid #15343e}
.mfl-lockup{display:flex;align-items:center;gap:13px}
.mfl-shield{width:55px;height:55px;filter:drop-shadow(0 10px 22px rgba(32,226,181,.13))}
.mfl-wordmark{line-height:1}
.mfl-wordmark-main{font-size:1.03rem;font-weight:950;color:#f6fcfb;letter-spacing:-.035em}
.mfl-wordmark-sub{font-size:.60rem;font-weight:850;color:#6f8a91;letter-spacing:.18em;margin-top:7px}
.mfl-seasonline{display:flex;align-items:center;gap:8px;margin-top:17px;color:#769198;font-size:.64rem;font-weight:750}
.mfl-seasonline:before{content:"";width:27px;height:2px;border-radius:99px;background:#20e2b5}

/* Sidebar navigation */
[data-testid="stSidebar"] [role="radiogroup"]{gap:5px}
[data-testid="stSidebar"] [role="radiogroup"] label{
 border:1px solid transparent;border-radius:11px;padding:10px 12px!important;transition:.16s ease
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#0a1e26!important;border-color:#173c47!important}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
 background:linear-gradient(90deg,rgba(32,226,181,.14),rgba(32,226,181,.025))!important;
 border-color:rgba(32,226,181,.24)!important;box-shadow:inset 3px 0 0 #20e2b5
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child{display:none!important}
[data-testid="stSidebar"] [role="radiogroup"] p{font-size:.82rem!important;font-weight:720!important;color:#a7babd!important}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#f0faf8!important}
.side-label{font-size:.58rem;letter-spacing:.16em;color:#536f76;font-weight:900;margin:19px 0 8px}
.wallet-card{background:#091a22;border:1px solid #173b46;border-radius:11px;padding:11px 12px;color:#c7d7d9;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.72rem;overflow:hidden}
.side-status{display:flex;align-items:center;gap:8px;color:#8ca4a9;font-size:.66rem;margin-top:15px}
.side-dot{width:7px;height:7px;border-radius:50%;background:#20e2b5;box-shadow:0 0 0 4px rgba(32,226,181,.08)}

/* Header */
.topbar{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:8px}
.eyebrow{display:flex;align-items:center;gap:8px;color:#20e2b5;font-size:.62rem;letter-spacing:.17em;font-weight:900;text-transform:uppercase}
.eyebrow:before{content:"";width:18px;height:2px;border-radius:99px;background:#20e2b5}
.page-title{font-size:2.35rem;line-height:1.02;font-weight:930;color:#f8fcfb;letter-spacing:-.055em;margin-top:9px}
.page-sub{font-size:.89rem;color:#789198;margin-top:8px;margin-bottom:23px}
.pill{display:inline-flex;align-items:center;gap:7px;border:1px solid #204650;background:#091a22;color:#9db5b9;border-radius:999px;padding:8px 11px;font-size:.67rem;font-weight:800;letter-spacing:.03em}
.dot{width:7px;height:7px;border-radius:50%;background:#20e2b5;box-shadow:0 0 0 4px rgba(32,226,181,.08)}

/* Dashboard hero */
.command-hero{position:relative;overflow:hidden;min-height:245px;background:
 linear-gradient(118deg,#0c2029 0%,#091820 65%,#08151c 100%);
 border:1px solid #1b414c;border-radius:20px;padding:30px 31px;box-shadow:0 24px 70px rgba(0,0,0,.15)}
.command-hero:before{content:"";position:absolute;right:-65px;top:-100px;width:350px;height:350px;border-radius:50%;
 background:radial-gradient(circle,rgba(32,226,181,.13),rgba(32,226,181,.02) 48%,transparent 70%)}
.command-hero:after{content:"";position:absolute;right:155px;bottom:-135px;width:270px;height:270px;border-radius:50%;border:42px solid rgba(75,166,255,.025)}
.hero-kicker{font-size:.62rem;color:#20e2b5;font-weight:900;letter-spacing:.17em}
.hero-title{font-size:2.42rem;color:#f7fcfb;font-weight:950;letter-spacing:-.06em;line-height:1.03;margin-top:11px;max-width:650px}
.hero-copy{font-size:.86rem;color:#81999f;line-height:1.65;max-width:610px;margin-top:13px}
.hero-pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:22px}
.hero-pill{background:#0d252e;border:1px solid #214852;border-radius:999px;padding:7px 10px;color:#9eb4b8;font-size:.66rem}
.hero-pill b{color:#20e2b5}

/* KPI */
.stat{position:relative;overflow:hidden;background:linear-gradient(145deg,#0b1d25,#08161d);border:1px solid #173944;border-radius:16px;padding:18px 19px;min-height:128px;box-shadow:0 14px 38px rgba(0,0,0,.1)}
.stat:after{content:"";position:absolute;right:-34px;top:-45px;width:100px;height:100px;border-radius:50%;border:18px solid rgba(32,226,181,.028)}
.stat-icon{width:31px;height:31px;border-radius:9px;background:rgba(32,226,181,.07);border:1px solid rgba(32,226,181,.13);display:flex;align-items:center;justify-content:center;color:#20e2b5;font-size:.72rem;font-weight:900}
.stat-value{font-size:1.95rem;font-weight:930;letter-spacing:-.05em;color:#f7fcfb;line-height:1;margin-top:16px}
.stat-label{font-size:.70rem;color:#708a91;margin-top:7px;font-weight:650}

/* Sections/cards */
.section-title{font-size:1.02rem;font-weight:850;color:#edf7f5;margin:27px 0 11px;display:flex;align-items:center;justify-content:space-between}
.section-title span{font-size:.62rem;letter-spacing:.1em;color:#58747b;font-weight:800}
.panel,.sync-box{background:linear-gradient(145deg,#091a22,#08161d);border:1px solid #173944;border-radius:16px;padding:18px}
.tool-card{position:relative;overflow:hidden;background:linear-gradient(145deg,#0b1d25,#08161d);border:1px solid #173944;border-radius:16px;padding:20px;min-height:165px;transition:.16s ease}
.tool-card:hover{border-color:#285b67;transform:translateY(-1px)}
.tool-card:after{content:"↗";position:absolute;right:18px;top:16px;color:#45656c;font-size:.9rem}
.tool-icon{width:38px;height:38px;border-radius:11px;background:rgba(32,226,181,.075);border:1px solid rgba(32,226,181,.1);color:#20e2b5;display:flex;align-items:center;justify-content:center;font-weight:900;margin-bottom:17px}
.tool-card h4{margin:0 0 7px;color:#f4faf8;font-size:1rem}
.tool-card p{font-size:.76rem!important;line-height:1.55!important;margin:0;color:#708990!important}
.empty{border:1px dashed #27505a;border-radius:15px;padding:29px;background:rgba(9,24,32,.48);text-align:center;color:#80989e}
.empty b{display:block;color:#eaf5f3;font-size:.96rem;margin-bottom:6px}
.sync-head{display:flex;align-items:center;justify-content:space-between;gap:16px}
.sync-title{font-weight:830;color:#edf7f5}
.sync-sub{font-size:.72rem;color:#708a91;margin-top:4px}

/* Grower */
.hero-card{position:relative;overflow:hidden;background:linear-gradient(145deg,#0b1d25,#08161d);border:1px solid #1a3c46;border-radius:17px;padding:20px;min-height:205px}
.hero-card:after{content:"";position:absolute;right:-35px;bottom:-50px;width:120px;height:120px;border-radius:50%;border:21px solid rgba(32,226,181,.025)}
.podium-1{border-color:rgba(32,226,181,.48)!important;box-shadow:0 18px 45px rgba(32,226,181,.055)}
.podium-2{border-color:rgba(75,166,255,.38)!important}.podium-3{border-color:rgba(154,114,255,.38)!important}
.hero-label{color:#20e2b5;font-size:.61rem;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.hero-name{font-size:1.32rem;font-weight:920;color:#f7fbfa;margin-top:10px;letter-spacing:-.04em}
.hero-player{font-size:.76rem;color:#82999e;margin-top:4px}
.hero-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:16px}
.chip{background:#0d252e;border:1px solid #214852;border-radius:999px;color:#a9bdc0;padding:6px 8px;font-size:.65rem}.chip strong{color:#20e2b5}
.attr-strip{display:flex;gap:5px;flex-wrap:wrap;margin-top:10px}.attr-pill{font-size:.60rem;padding:4px 6px;border-radius:6px;background:#0d232b;color:#688188}.attr-up{color:#20e2b5;border:1px solid rgba(32,226,181,.2);background:rgba(32,226,181,.04)}

/* Club */
.club-card2{position:relative;overflow:hidden;background:linear-gradient(145deg,#0b1d25,#08161d);border:1px solid #173944;border-radius:17px;padding:20px;min-height:160px}
.club-card2:after{content:"";position:absolute;right:-32px;bottom:-46px;width:120px;height:120px;border-radius:50%;border:22px solid rgba(32,226,181,.025)}
.club-pos2{color:#20e2b5;font-weight:900;font-size:.60rem;letter-spacing:.14em}.club-name2{font-size:1.05rem;color:#f3faf8;font-weight:880;margin-top:9px}
.club-total2{font-size:1.75rem;font-weight:930;color:#20e2b5;margin-top:12px;letter-spacing:-.045em}.club-sub2{font-size:.68rem;color:#748e94}
.progress-track2{height:5px;background:#102730;border-radius:99px;margin-top:14px;overflow:hidden}.progress-fill2{height:100%;background:linear-gradient(90deg,#20e2b5,#4ba6ff);border-radius:99px}
.section-head2{display:flex;align-items:center;justify-content:space-between;margin:27px 0 11px}.section-head2 h3{margin:0;font-size:1.02rem}.small-note2{font-size:.62rem;color:#5c777e;letter-spacing:.08em}

/* Lists */
.rank-row{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #12303a}.rank-row:last-child{border-bottom:0}
.rank-pos{width:26px;height:26px;border-radius:8px;background:#0f2831;color:#9cb2b6;display:flex;align-items:center;justify-content:center;font-size:.67rem;font-weight:850}
.rank-name{flex:1;color:#dce9e7;font-size:.80rem;font-weight:700}.rank-gain{color:#20e2b5;font-size:.78rem;font-weight:900}

/* Native controls */
.stButton>button{background:#0b2028!important;color:#d7e5e3!important;border:1px solid #234b56!important;border-radius:10px!important;font-weight:760!important;min-height:40px}
.stButton>button:hover{border-color:#20e2b5!important;color:#20e2b5!important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#20e2b5,#17c99f)!important;color:#032119!important;border-color:#20e2b5!important;box-shadow:0 9px 24px rgba(32,226,181,.11)!important}
[data-testid="stDataFrame"]{border:1px solid #173944!important;border-radius:13px!important;overflow:hidden!important}
[data-testid="stExpander"]{background:#08171e!important;border:1px solid #173944!important;border-radius:12px!important}
div[data-baseweb="select"]>div,.stTextInput input{background:#091a22!important;border-color:#204751!important;color:#edf7f5!important;border-radius:10px!important}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#20e2b5,#4ba6ff)!important}
[data-baseweb="tab-list"]{gap:6px!important;background:#08171e!important;border:1px solid #173944!important;border-radius:11px!important;padding:5px!important}
[data-baseweb="tab"]{border-radius:8px!important;padding:7px 12px!important}
[data-baseweb="tab"][aria-selected="true"]{background:#0e2831!important;color:#20e2b5!important}
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
    st.markdown("""
    <div class="mfl-brand">
      <div class="mfl-lockup">
        <svg class="mfl-shield" viewBox="0 0 64 64" aria-label="MFL Management Hub logo">
          <defs>
            <linearGradient id="mintg" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#57f2d1"/>
              <stop offset="1" stop-color="#14bf98"/>
            </linearGradient>
          </defs>
          <path d="M32 3 56 12v18c0 15-9.6 25.1-24 31C17.6 55.1 8 45 8 30V12L32 3Z" fill="#0a2028" stroke="#20e2b5" stroke-width="2"/>
          <path d="M20 20h5l3 6 4-8 4 8 3-6h5l-3 9H23l-3-9Z" fill="url(#mintg)"/>
          <path d="M18 35h5v11h-5V35Zm8 0h5l3 5 3-5h5v11h-5v-5l-3 4-3-4v5h-5V35Zm19 0h10v4h-5v2h4v4h-4v1h-5V35Z" fill="#f4fbfa"/>
        </svg>
        <div class="mfl-wordmark">
          <div class="mfl-wordmark-main">MFL Management</div>
          <div class="mfl-wordmark-sub">PERFORMANCE HUB</div>
        </div>
      </div>
      <div class="mfl-seasonline">SEASON 17 · LIVE WORKSPACE</div>
    </div>
    """,unsafe_allow_html=True)

    page=st.radio(
        "Navigation",
        ["Home","Grower or Shower","Agency Development","Club Development"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="side-label">ACTIVE WALLET</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="wallet-card">{esc(st.session_state.wallet)}</div>',unsafe_allow_html=True)
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

    st.markdown('<div class="side-status"><span class="side-dot"></span> MFL API connected</div>',unsafe_allow_html=True)
    st.caption("FULL REDESIGN · v8")

wallet=st.session_state.wallet

# ---------------- HOME ----------------
if page=="Home":
    try:
        c=agency.db();agency.init(c);agency.ensure_v2(c)
        players=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=?",(wallet.lower(),)).fetchone()[0]
        improved=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=? AND current_ovr>start_ovr",(wallet.lower(),)).fetchone()[0]
        c.close()
    except Exception:
        players=0;improved=0

    try: mine=club.owned_clubs(wallet)
    except Exception: mine=[]
    cached=club.cached(wallet)
    ovr=float(cached["ovr_gain"].fillna(0).sum()) if not cached.empty else 0
    attrs=float(cached["attr_gain"].fillna(0).sum()) if not cached.empty else 0

    st.markdown(f"""
    <div class="command-hero">
      <div class="hero-kicker">MFL · SEASON 17 COMMAND CENTRE</div>
      <div class="hero-title">Manage the network.<br>See what is developing.</div>
      <div class="hero-copy">Your agency, owned clubs and Grower or Shower competition in one live workspace — focused on progression, not admin.</div>
      <div class="hero-pills">
        <span class="hero-pill"><b>{len(mine) if mine else "—"}</b> owned clubs</span>
        <span class="hero-pill"><b>{players or "—"}</b> agency players</span>
        <span class="hero-pill"><b>+{ovr:g}</b> club OVR</span>
        <span class="hero-pill"><b>+{attrs:g}</b> attributes</span>
      </div>
    </div>""",unsafe_allow_html=True)

    st.markdown('<div class="section-title">Season overview <span>LIVE SAVED DATA</span></div>',unsafe_allow_html=True)
    cols=st.columns(4)
    with cols[0]: stat("CL",len(mine) if mine else "—","Owned Clubs")
    with cols[1]: stat("PL",players or "—","Players Tracked")
    with cols[2]: stat("↑",f"+{ovr:g}" if not cached.empty else "—","Club OVR Gained")
    with cols[3]: stat("DV",improved,"Agency Players Improved")

    st.markdown('<div class="section-title">Workspaces <span>MANAGEMENT TOOLS</span></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    with a:
        st.markdown('<div class="tool-card"><div class="tool-icon">GS</div><h4>Grower or Shower</h4><p>Competition ranking, player ratings and every OVR or attribute gain.</p></div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="tool-card"><div class="tool-icon" style="color:#4ba6ff;background:rgba(75,166,255,.07);border-color:rgba(75,166,255,.12)">AD</div><h4>Agency Development</h4><p>Track ownership baselines, new mints, priority players and progression.</p></div>',unsafe_allow_html=True)
    with c:
        st.markdown('<div class="tool-card"><div class="tool-icon" style="color:#9a72ff;background:rgba(154,114,255,.07);border-color:rgba(154,114,255,.12)">CD</div><h4>Club Development</h4><p>Compare Season 17 development across your entire owned-club network.</p></div>',unsafe_allow_html=True)

    st.markdown('<div class="section-title">Club intelligence <span>TOP DEVELOPMENT</span></div>',unsafe_allow_html=True)
    left,right=st.columns([1.6,1])
    with left:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        if cached.empty:
            st.markdown('<div class="empty"><b>No club development loaded</b>Run Club Development sync to populate the dashboard.</div>',unsafe_allow_html=True)
        else:
            chart=cached.groupby("club")["ovr_gain"].sum().sort_values(ascending=False).head(8)
            st.bar_chart(chart,height=285)
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        if cached.empty:
            st.markdown('<div class="panel"><div class="empty"><b>Top clubs</b>Waiting for synced data.</div></div>',unsafe_allow_html=True)
        else:
            ranks=cached.groupby("club").agg(ovr=("ovr_gain","sum"),attrs=("attr_gain","sum"),players=("player_id","count")).sort_values(["ovr","attrs"],ascending=False).head(5)
            body=""
            for i,(name,row) in enumerate(ranks.iterrows(),1):
                body += f'<div class="rank-row"><div class="rank-pos">{i}</div><div class="rank-name">{esc(name)}<div style="font-size:.61rem;color:#5f7b82;margin-top:2px">{int(row["players"])} players · +{row["attrs"]:g} attributes</div></div><div class="rank-gain">+{row["ovr"]:g}</div></div>'
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

