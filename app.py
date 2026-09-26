
import os
import base64
import html
import math
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

# ---------------- MOCKUP-MATCH PRODUCT UI ----------------
st.markdown("""
<style>
:root{
 --bg:#03090e;--panel:#07131a;--panel2:#091922;--line:#173944;
 --text:#f4f8f7;--muted:#7b9096;--mint:#13e0b4;--cyan:#16a6ff;--violet:#9a52ff;
}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.stApp{background:radial-gradient(1100px 700px at 78% -12%,rgba(20,124,180,.09),transparent 65%),#03090e;color:var(--text)}
[data-testid="stHeader"]{background:rgba(3,9,14,.80);backdrop-filter:blur(16px);border-bottom:1px solid #0e252d}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#040b10,#07131a)!important;border-right:1px solid #142f38!important;min-width:264px!important}
[data-testid="stSidebarContent"]{padding:0!important}
.block-container{max-width:1510px!important;padding:1.15rem 1.7rem 3.4rem!important}
#MainMenu,footer,[data-testid="stDecoration"]{display:none!important}

/* SIDEBAR BRAND */
.side-poster{margin:14px 13px 12px;border:1px solid #1b313a;border-radius:13px;overflow:hidden;background:
 linear-gradient(155deg,rgba(255,255,255,.035),rgba(255,255,255,0) 38%),
 repeating-linear-gradient(168deg,rgba(255,255,255,.012) 0 1px,transparent 1px 5px),
 #0a1115;position:relative;min-height:205px}
.poster-crown{font-size:2.1rem;color:var(--mint);line-height:1;text-align:center;margin-top:23px;text-shadow:0 0 18px rgba(19,224,180,.18)}
.poster-mfl{font-family:"Arial Black",Impact,sans-serif;font-size:3.15rem;font-style:italic;font-weight:950;color:#fff;line-height:.86;text-align:center;letter-spacing:-.09em;transform:skew(-7deg)}
.poster-sub{font-size:.84rem;font-style:italic;font-weight:900;text-align:center;color:#f2f5f4;letter-spacing:.03em;margin-top:7px}
.poster-swipe{width:126px;height:7px;margin:11px auto 0;background:linear-gradient(90deg,transparent 0,var(--mint) 18%,var(--mint) 78%,transparent 100%);transform:skew(-18deg);box-shadow:0 0 20px rgba(19,224,180,.26)}

[data-testid="stSidebar"] [role="radiogroup"]{gap:4px;padding:4px 12px 0}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:9px 11px!important;border:1px solid transparent}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#0b1d25}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#0e785f,#0b5b4b);border-color:#15cfa7;box-shadow:inset 3px 0 0 #1ff1c1}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none!important}
[data-testid="stSidebar"] [role="radiogroup"] p{font-size:.76rem!important;color:#c1cbcd!important;font-weight:720!important}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#fff!important}
.wallet-area{padding:16px 13px 0;margin-top:13px;border-top:1px solid #17323a}
.wallet-label{font-size:.52rem;color:#557179;letter-spacing:.15em;font-weight:900;margin-bottom:7px}
.wallet-chip{font-family:ui-monospace,monospace;font-size:.62rem;color:#aababc;background:#07161d;border:1px solid #173944;border-radius:8px;padding:9px 10px;overflow:hidden}
.season-box{margin:18px 13px 0;padding:13px;background:#07151c;border:1px solid #173843;border-radius:11px}
.season-top{display:flex;align-items:center;justify-content:space-between;color:#cad4d5;font-size:.68rem;font-weight:750}
.connected{display:flex;align-items:center;gap:8px;color:#8ca1a5;font-size:.60rem;margin-top:14px}
.connected i{width:8px;height:8px;border-radius:50%;background:var(--mint);box-shadow:0 0 0 4px rgba(19,224,180,.08)}
.build{font-size:.52rem;color:#435f66;letter-spacing:.08em;margin:13px 13px 0}

/* HERO BANNER */
.banner{position:relative;overflow:hidden;min-height:150px;border:1px solid #173844;border-radius:14px;background:
 radial-gradient(460px 190px at 77% 5%,rgba(26,155,255,.22),transparent 65%),
 linear-gradient(95deg,#07151c 0%,#07141b 44%,#09202a 72%,#061016 100%);padding:23px 29px 22px}
.banner:before{content:"";position:absolute;inset:0;background:
 linear-gradient(116deg,transparent 0 66%,rgba(255,255,255,.025) 66% 67%,transparent 67%),
 radial-gradient(circle at 78% 20%,rgba(255,255,255,.7) 0 1px,transparent 2px),
 radial-gradient(circle at 81% 24%,rgba(255,255,255,.5) 0 1px,transparent 2px),
 radial-gradient(circle at 84% 16%,rgba(255,255,255,.45) 0 1px,transparent 2px)}
.banner-row{position:relative;z-index:2;display:flex;align-items:flex-start;justify-content:space-between;gap:20px}
.brand-word{font-family:"Arial Black",Impact,sans-serif;font-style:italic;font-size:3rem;line-height:.86;letter-spacing:-.07em;color:#fff;transform:skew(-5deg)}
.brand-word span{font-size:1.18rem;letter-spacing:.02em;margin-left:9px;vertical-align:middle}
.brand-stroke{width:210px;height:5px;background:linear-gradient(90deg,transparent,var(--mint) 15%,var(--mint) 82%,transparent);margin:12px 0 0 112px;transform:skew(-20deg)}
.brand-tag{font-size:.70rem;color:#c2ccce;font-style:italic;letter-spacing:.09em;margin:7px 0 0 117px}
.season-badge{position:relative;z-index:3;background:#0b1c24;border:1px solid #27434c;color:#dbe4e5;border-radius:8px;padding:8px 11px;font-size:.67rem;font-weight:750}
.banner-note{position:absolute;right:30px;bottom:18px;z-index:2;color:#eef2f2;font-size:.75rem;font-style:italic;letter-spacing:.06em;transform:rotate(-4deg)}
.banner-note b{color:var(--mint)}

/* KPI CARDS */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px}
.stat-card{position:relative;overflow:hidden;display:grid;grid-template-columns:48px 1fr auto;align-items:center;gap:12px;background:linear-gradient(145deg,#08161d,#071119);border:1px solid #183b45;border-radius:10px;padding:14px 15px;min-height:76px}
.stat-card.cyan{border-color:#164c70}.stat-card.violet{border-color:#4c2875}
.stat-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:var(--mint);background:rgba(19,224,180,.06);border:1px solid rgba(19,224,180,.2);font-size:1.08rem}
.stat-card.cyan .stat-icon{color:var(--cyan);background:rgba(22,166,255,.07);border-color:rgba(22,166,255,.18)}
.stat-card.violet .stat-icon{color:var(--violet);background:rgba(154,82,255,.07);border-color:rgba(154,82,255,.18)}
.stat-num{font-size:1.5rem;font-weight:900;color:#f7fbfa;letter-spacing:-.045em;line-height:1}.stat-lab{font-size:.66rem;color:#afbdbf;margin-top:4px}
.stat-trend{font-size:.68rem;color:#19eab9;font-weight:850}

/* FEATURE CARDS */
.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.feature-card{position:relative;overflow:hidden;min-height:155px;border-radius:11px;border:1px solid #153c45;background:#07141b}
.feature-card.grower{border-color:#10b991}.feature-card.agency{border-color:#1687d1}.feature-card.club{border-color:#6d35a7}
.feature-bg{position:absolute;inset:0;opacity:.95}
.grower .feature-bg{background:radial-gradient(circle at 58% 20%,rgba(19,224,180,.40),transparent 36%),linear-gradient(180deg,#07372e 0%,#071319 69%)}
.agency .feature-bg{background:radial-gradient(circle at 58% 20%,rgba(22,166,255,.34),transparent 38%),linear-gradient(180deg,#082a43 0%,#071319 69%)}
.club .feature-bg{background:radial-gradient(circle at 72% 15%,rgba(154,82,255,.32),transparent 40%),linear-gradient(180deg,#25103b 0%,#071319 69%)}
.feature-art{position:absolute;right:22px;top:13px;font-size:4.7rem;opacity:.78;filter:drop-shadow(0 12px 22px rgba(0,0,0,.5))}
.feature-copy{position:absolute;left:20px;right:20px;bottom:17px;z-index:2}.feature-title{font-size:1.03rem;color:#fff;font-weight:850}.feature-sub{font-size:.68rem;color:#bdc8ca;margin-top:3px}
.feature-go{position:absolute;right:17px;bottom:17px;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#031a15;font-weight:900;background:var(--mint)}
.agency .feature-go{background:var(--cyan);color:#03111a}.club .feature-go{background:var(--violet);color:#12091b}

/* LOWER DASHBOARD */
.dash-grid{display:grid;grid-template-columns:1.25fr .76fr .76fr;gap:12px;margin-top:13px}
.bottom-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:12px;margin-top:12px}
.card{background:linear-gradient(145deg,#07161d,#061219);border:1px solid #183743;border-radius:11px;padding:15px}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px}.card-title{font-size:.79rem;color:#eaf0f0;font-weight:820}.card-meta{font-size:.56rem;color:#587178;letter-spacing:.08em}
.chart-box{height:190px;position:relative;padding:5px 6px 0}
.chart-grid{position:absolute;inset:10px 12px 26px 40px;background:
 linear-gradient(to right,transparent calc(25% - .5px),#102b33 25%,transparent calc(25% + .5px),transparent calc(50% - .5px),#102b33 50%,transparent calc(50% + .5px),transparent calc(75% - .5px),#102b33 75%,transparent calc(75% + .5px)),
 linear-gradient(to bottom,transparent calc(25% - .5px),#102b33 25%,transparent calc(25% + .5px),transparent calc(50% - .5px),#102b33 50%,transparent calc(50% + .5px),transparent calc(75% - .5px),#102b33 75%,transparent calc(75% + .5px))}
.chart-svg{position:absolute;left:40px;right:12px;top:10px;bottom:26px;width:calc(100% - 52px);height:calc(100% - 36px)}
.chart-labels{position:absolute;left:40px;right:12px;bottom:3px;display:flex;justify-content:space-between;color:#667d83;font-size:.56rem}
.list-row{display:grid;grid-template-columns:24px 1fr auto;gap:9px;align-items:center;padding:9px 0;border-bottom:1px solid #112b33}.list-row:last-child{border-bottom:0}
.list-rank{width:22px;height:22px;border-radius:50%;background:#10252c;color:#aebcbf;display:flex;align-items:center;justify-content:center;font-size:.58rem}.list-main{font-size:.69rem;color:#d5dfdf;font-weight:700}.list-sub{font-size:.54rem;color:#5f767c;margin-top:2px}.list-value{font-size:.68rem;color:#19e5b5;font-weight:900}
.activity-row{display:grid;grid-template-columns:10px 1fr auto;gap:9px;align-items:center;padding:8px 0;border-bottom:1px solid #112b33}.activity-row:last-child{border-bottom:0}
.activity-dot{width:8px;height:8px;border-radius:50%;background:var(--mint)}.activity-main{font-size:.66rem;color:#d0dcdd}.activity-main b{color:#18e4b4}.activity-time{font-size:.54rem;color:#526a70}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:9px}.action{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 13px;border-radius:9px;border:1px solid #193842;background:#08161d;color:#d8e2e2;font-size:.68rem;font-weight:700}.action span{color:#6f858a}

/* SUBPAGES */
.topline{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin:5px 0 17px}.crumb{font-size:.57rem;color:var(--mint);letter-spacing:.15em;font-weight:900}.h1{font-size:2rem;line-height:1.03;font-weight:930;color:#f5fbfa;letter-spacing:-.05em;margin-top:6px}.subtitle{font-size:.74rem;color:#71878d;margin-top:5px}.live{font-size:.58rem;color:#9db0b3;background:#07171e;border:1px solid #193d46;border-radius:999px;padding:7px 10px}.live:before{content:"●";color:var(--mint);margin-right:6px}
.hero-card,.panel,.sync-box,.club-card2,.tool-card{background:linear-gradient(145deg,#07161d,#061219)!important;border:1px solid #183743!important;border-radius:11px!important}
.hero-card{padding:17px!important}.podium-1{border-color:#12bc95!important}.podium-2{border-color:#1688d0!important}.podium-3{border-color:#6f35a8!important}
.section-head2{display:flex;align-items:center;justify-content:space-between;margin:22px 0 9px}.section-head2 h3{font-size:1.05rem;margin:0;color:#e8efef}.small-note2{font-size:.64rem;color:#5b7379;letter-spacing:.08em}
.rank-row{display:grid;grid-template-columns:26px 1fr auto;align-items:center;gap:9px;padding:9px 0;border-bottom:1px solid #112b33}.rank-row:last-child{border-bottom:0}.rank-pos{width:23px;height:23px;border-radius:50%;background:#10252c;color:#aebcbf;display:flex;align-items:center;justify-content:center;font-size:.57rem}.rank-name{font-size:.68rem;color:#d4dede}.rank-gain{font-size:.68rem;color:#19e5b5;font-weight:900}
.stButton>button{background:#081a21!important;color:#d7e1e1!important;border:1px solid #214650!important;border-radius:8px!important;font-weight:720!important;font-size:.69rem!important}
.stButton>button[kind="primary"]{background:#13d9ad!important;color:#021b15!important;border-color:#13d9ad!important}
[data-testid="stDataFrame"]{border:1px solid #173843!important;border-radius:10px!important;overflow:hidden}
[data-testid="stExpander"]{background:#06151b!important;border:1px solid #173843!important;border-radius:9px!important}
div[data-baseweb="select"]>div,.stTextInput input{background:#07171e!important;border-color:#1b4049!important;color:#edf4f4!important;border-radius:8px!important}
[data-baseweb="tab-list"]{background:#06151b!important;border:1px solid #173843!important;border-radius:9px!important;padding:4px!important}
[data-baseweb="tab"][aria-selected="true"]{background:#0d272f!important;color:var(--mint)!important}
.stProgress>div>div>div>div{background:linear-gradient(90deg,var(--mint),var(--cyan))!important}
@media(max-width:1000px){.stats-grid,.feature-grid,.dash-grid,.bottom-grid{grid-template-columns:1fr 1fr}.banner-note{display:none}}
@media(max-width:700px){.stats-grid,.feature-grid,.dash-grid,.bottom-grid{grid-template-columns:1fr}.block-container{padding:1rem!important}.brand-word{font-size:2.2rem}}
</style>
""",unsafe_allow_html=True)


st.markdown(r'''
<style>
.grower-hero{position:relative;overflow:hidden;border:1px solid #173944;border-radius:14px;background:linear-gradient(120deg,#07151c 0%,#07151c 45%,#09232c 100%);min-height:168px;padding:22px 24px;margin-bottom:13px}
.grower-hero:after{content:"";position:absolute;right:-40px;top:-60px;width:270px;height:270px;border-radius:50%;border:42px solid rgba(19,224,180,.035)}
.gh-kicker{font-size:.68rem;letter-spacing:.16em;color:#13e0b4;font-weight:900}.gh-title{font-size:2.08rem;color:#f7fbfa;font-weight:930;letter-spacing:-.055em;margin-top:7px}
.gh-copy{font-size:.86rem;color:#758c92;line-height:1.55;margin-top:7px;max-width:650px}.gh-badges{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}
.gh-badge{font-size:.70rem;color:#a6b7ba;background:#0c252d;border:1px solid #1e4650;border-radius:999px;padding:6px 8px}.gh-badge b{color:#13e0b4}
.leader-grid{display:grid;grid-template-columns:1.18fr .91fr .91fr;gap:12px;margin-bottom:14px}
.leader-card{position:relative;overflow:hidden;background:linear-gradient(145deg,#08171e,#061219);border:1px solid #173944;border-radius:13px;min-height:220px;padding:18px}
.leader-card.first{border-color:#13c79f}.leader-card.second{border-color:#1888c9}.leader-card.third{border-color:#6b39a4}
.leader-card:after{content:"";position:absolute;right:-43px;top:-38px;width:120px;height:120px;border-radius:50%;border:20px solid rgba(255,255,255,.018)}
.leader-rank{font-size:.56rem;letter-spacing:.14em;font-weight:900;color:#13e0b4}.second .leader-rank{color:#24a9ff}.third .leader-rank{color:#a065ff}
.leader-player{font-size:1.35rem;color:#f4f9f8;font-weight:920;letter-spacing:-.045em;margin-top:11px}.leader-owner{font-size:.67rem;color:#758c92;margin-top:3px}
.leader-ovr{display:flex;align-items:flex-end;justify-content:space-between;margin-top:17px}.leader-ovr-num{font-size:2.25rem;color:#fff;font-weight:950;letter-spacing:-.07em;line-height:.9}.leader-ovr-lab{font-size:.66rem;color:#5f787f;margin-top:5px}
.rating-disc{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:radial-gradient(circle at 35% 28%,#123c39,#09221f 65%);border:1px solid #1d5c51}
.rating-disc strong{font-size:1.12rem;color:#d9fff4}.rating-disc span{font-size:.58rem;color:#6f9d91;letter-spacing:.09em}
.leader-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:11px}.ls{background:#0a2028;border:1px solid #173b45;border-radius:8px;padding:8px}.ls span{display:block;font-size:.61rem;color:#58737a;text-transform:uppercase;letter-spacing:.08em}.ls b{display:block;font-size:.90rem;color:#e1ecea;margin-top:3px}.ls b.up{color:#13e0b4}
.gain-pills{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}.gain-pill{font-size:.68rem;padding:4px 6px;border-radius:6px;color:#657e85;background:#0b2028;border:1px solid #173840}.gain-pill.up{color:#13e0b4;background:rgba(19,224,180,.045);border-color:rgba(19,224,180,.22)}
.comp-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:13px}.comp-card{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px}.comp-title{font-size:.84rem;color:#e8f0ef;font-weight:800}.comp-big{font-size:1.95rem;color:#13e0b4;font-weight:930;letter-spacing:-.05em;margin-top:10px}.comp-sub{font-size:.70rem;color:#607a80;margin-top:2px}
.standing-wrap{background:#061219;border:1px solid #173843;border-radius:12px;overflow:hidden}.standing-head,.standing-row{display:grid;grid-template-columns:46px 1fr 1.3fr 80px 84px 90px 72px 1.55fr;gap:10px;align-items:center}
.standing-head{padding:11px 13px;background:#091a22;border-bottom:1px solid #173843;font-size:.63rem;color:#60777d;text-transform:uppercase;letter-spacing:.09em;font-weight:900}
.standing-row{padding:10px 13px;border-bottom:1px solid #102c34;min-height:57px}.standing-row:last-child{border-bottom:0}
.s-rank{width:30px;height:30px;border-radius:8px;background:#0d242c;color:#aab9bc;display:flex;align-items:center;justify-content:center;font-size:.67rem;font-weight:850}.s-rank.top{background:linear-gradient(145deg,#0c6a55,#0a463a);color:#eafff8;border:1px solid #12c89f}
.s-owner{font-size:.80rem;color:#dfe9e8;font-weight:800}.s-player{font-size:.82rem;color:#e3eceb;font-weight:730}.s-club{font-size:.66rem;color:#5e777d;margin-top:2px}.s-num{font-size:.80rem;color:#cbd8d8;font-weight:750}.s-up{font-size:.80rem;color:#13e0b4;font-weight:900}
.s-rating{display:inline-flex;align-items:center;gap:5px;font-size:.80rem;color:#eef6f4;font-weight:850}.rating-dot{width:7px;height:7px;border-radius:50%;background:#13e0b4}.s-apps{font-size:.80rem;color:#9db0b3}.s-gains{display:flex;gap:4px;flex-wrap:wrap}.s-gain{font-size:.64rem;color:#657d83;background:#0a2028;border:1px solid #173841;border-radius:5px;padding:3px 5px}.s-gain.up{color:#13e0b4;border-color:rgba(19,224,180,.22);background:rgba(19,224,180,.04)}
.development-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.dev-card{background:#07161d;border:1px solid #173843;border-radius:11px;padding:13px}.dev-player{font-size:.88rem;color:#edf5f4;font-weight:820}.dev-owner{font-size:.68rem;color:#607980;margin-top:2px}.dev-gain{font-size:1.55rem;color:#13e0b4;font-weight:930;margin-top:10px}.dev-sub{font-size:.68rem;color:#637c82;margin-top:2px}
@media(max-width:1000px){.leader-grid{grid-template-columns:1fr}.standing-head,.standing-row{grid-template-columns:40px 1fr 1.2fr 70px 80px 70px}.standing-head>*:nth-child(7),.standing-head>*:nth-child(8),.standing-row>*:nth-child(7),.standing-row>*:nth-child(8){display:none}}
</style>
''', unsafe_allow_html=True)


st.markdown(r"""
<style>
/* ===== v12 official MFL player portraits ===== */
.leader-card{padding:0!important;min-height:0!important}
.leader-photo-zone{position:relative;height:132px;overflow:hidden;background:
 radial-gradient(circle at 70% 35%,rgba(19,224,180,.18),transparent 45%),
 linear-gradient(145deg,#0b252d,#07151b)}
.second .leader-photo-zone{background:radial-gradient(circle at 70% 35%,rgba(36,169,255,.18),transparent 45%),linear-gradient(145deg,#0a2231,#07151b)}
.third .leader-photo-zone{background:radial-gradient(circle at 70% 35%,rgba(160,101,255,.18),transparent 45%),linear-gradient(145deg,#1a1130,#07151b)}
.leader-photo-zone:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,12,16,.88) 0%,rgba(5,12,16,.42) 42%,rgba(5,12,16,.08) 75%,rgba(5,12,16,.20) 100%)}
.leader-photo{position:absolute;right:8px;top:7px;height:132px;width:132px;object-fit:contain;object-position:center top;z-index:1;filter:drop-shadow(0 10px 16px rgba(0,0,0,.40))}
.leader-photo-copy{position:absolute;left:16px;top:15px;z-index:3;max-width:62%}
.leader-photo-rank{font-size:.68rem;letter-spacing:.14em;font-weight:900;color:#13e0b4}
.second .leader-photo-rank{color:#24a9ff}.third .leader-photo-rank{color:#a065ff}
.leader-photo-name{font-size:1.38rem;color:#f5faf9;font-weight:930;line-height:1.02;letter-spacing:-.045em;margin-top:7px}
.leader-photo-owner{font-size:.76rem;color:#82969b;margin-top:5px}
.leader-body{padding:13px 14px 14px}
.leader-body-top{display:flex;align-items:flex-end;justify-content:space-between;gap:10px}
.leader-ovr-block .leader-ovr-num{font-size:2.02rem}
.photo-source{display:none}
@media(max-width:1000px){
  .leader-photo{height:136px;width:136px;right:8px;top:6px}
  .leader-photo-copy{max-width:52%}
}
</style>
""", unsafe_allow_html=True)


st.markdown(r"""
<style>
/* ===== v13 Agency Development ===== */
.agency-hero{position:relative;overflow:hidden;border:1px solid #173944;border-radius:14px;
 background:linear-gradient(115deg,#07151c 0%,#07151c 48%,#0a2230 100%);
 min-height:170px;padding:22px 24px;margin-bottom:13px}
.agency-hero:after{content:"";position:absolute;right:-45px;top:-70px;width:280px;height:280px;border-radius:50%;
 border:44px solid rgba(22,166,255,.035)}
.ah-kicker{font-size:.68rem;letter-spacing:.16em;color:#29a9ff;font-weight:900}
.ah-title{font-size:2.08rem;color:#f7fbfa;font-weight:930;letter-spacing:-.055em;margin-top:7px}
.ah-copy{font-size:.86rem;color:#758c92;line-height:1.55;margin-top:7px;max-width:720px}
.ah-badges{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}
.ah-badge{font-size:.70rem;color:#a6b7ba;background:#0b2330;border:1px solid #19465d;border-radius:999px;padding:6px 9px}
.ah-badge b{color:#45b6ff}

.agency-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:13px 0 18px}
.ag-kpi{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px}
.ag-kpi-label{font-size:.61rem;color:#607b82;text-transform:uppercase;letter-spacing:.08em;font-weight:850}
.ag-kpi-value{font-size:1.7rem;color:#f3f9f8;font-weight:930;letter-spacing:-.05em;margin-top:8px}
.ag-kpi-value.blue{color:#38afff}.ag-kpi-value.green{color:#13e0b4}.ag-kpi-value.violet{color:#a56cff}

.movers-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.mover-card{position:relative;overflow:hidden;background:linear-gradient(145deg,#08171e,#061219);border:1px solid #173944;border-radius:12px;min-height:250px}
.mover-photo-zone{position:relative;height:135px;overflow:hidden;background:
 radial-gradient(circle at 72% 32%,rgba(22,166,255,.18),transparent 45%),linear-gradient(145deg,#0a2130,#07151b)}
.mover-photo{position:absolute;right:6px;top:6px;height:136px;width:136px;object-fit:contain;object-position:center top;
 filter:drop-shadow(0 10px 16px rgba(0,0,0,.42))}
.mover-rank{position:absolute;left:14px;top:13px;z-index:2;font-size:.61rem;color:#37b1ff;letter-spacing:.13em;font-weight:900}
.mover-tag{position:absolute;left:14px;top:34px;z-index:2;font-size:.56rem;padding:4px 6px;border-radius:6px;
 background:#0b2430;border:1px solid #1d4c5e;color:#8fb7c7}
.mover-body{padding:13px 14px 14px}.mover-name{font-size:1.02rem;color:#f1f7f6;font-weight:900;letter-spacing:-.035em}
.mover-meta{font-size:.67rem;color:#6d858b;margin-top:3px}.mover-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:11px}
.mstat{background:#0a2028;border:1px solid #173b45;border-radius:8px;padding:8px}.mstat span{display:block;font-size:.56rem;color:#58737a;letter-spacing:.07em;text-transform:uppercase}
.mstat b{display:block;font-size:.88rem;color:#e8f1f0;margin-top:3px}.mstat b.up{color:#13e0b4}
.mover-gains{display:flex;gap:4px;flex-wrap:wrap;margin-top:9px}.mgain{font-size:.60rem;padding:4px 6px;border-radius:5px;background:#0a2028;color:#637c82;border:1px solid #173841}
.mgain.up{color:#13e0b4;border-color:rgba(19,224,180,.22);background:rgba(19,224,180,.04)}

.mint-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.mint-card{display:grid;grid-template-columns:82px 1fr;gap:12px;align-items:center;background:#07161d;border:1px solid #173843;border-radius:11px;padding:11px}
.mint-photo-wrap{width:82px;height:92px;overflow:hidden;border-radius:9px;background:linear-gradient(145deg,#0a2130,#07151b);border:1px solid #183f4d}
.mint-photo{width:100%;height:100%;object-fit:contain;object-position:center top}
.mint-name{font-size:.84rem;color:#edf5f4;font-weight:850}.mint-meta{font-size:.62rem;color:#637c82;margin-top:3px}
.mint-ovr{font-size:1.25rem;color:#38afff;font-weight:930;margin-top:8px}.mint-gain{font-size:.63rem;color:#13e0b4;margin-top:2px}

.tag-board{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.tag-card{background:#07161d;border:1px solid #173843;border-radius:11px;padding:13px}
.tag-pill{display:inline-block;font-size:.56rem;padding:4px 6px;border-radius:6px;background:#10242c;color:#a9b8ba;border:1px solid #1b424c}
.tag-pill.PRIORITY{color:#ffcf66;border-color:#6f5720;background:#241e0a}
.tag-pill.DEVELOP{color:#13e0b4;border-color:#1f584c;background:#0c231e}
.tag-pill.WATCH{color:#a86fff;border-color:#4d3170;background:#1a1026}
.tag-name{font-size:.82rem;color:#edf5f4;font-weight:850;margin-top:9px}.tag-note{font-size:.63rem;color:#637c82;margin-top:4px;line-height:1.45}

.agency-filterbar{display:grid;grid-template-columns:1.8fr 1fr 1fr;gap:9px;margin-bottom:11px}
.agency-table-note{font-size:.61rem;color:#59727a;margin-top:6px}
@media(max-width:1100px){.movers-grid{grid-template-columns:1fr 1fr}.mint-grid,.tag-board{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.agency-kpis,.movers-grid,.mint-grid,.tag-board,.agency-filterbar{grid-template-columns:1fr}}
</style>
""",unsafe_allow_html=True)


st.markdown(r"""
<style>
/* ===== v14 Club Development ===== */
.club-hero{position:relative;overflow:hidden;border:1px solid #173944;border-radius:14px;
 background:linear-gradient(115deg,#07151c 0%,#07151c 45%,#1a1030 100%);
 min-height:170px;padding:22px 24px;margin-bottom:13px}
.club-hero:after{content:"";position:absolute;right:-35px;top:-55px;width:280px;height:280px;border-radius:50%;
 border:44px solid rgba(154,82,255,.035)}
.ch-kicker{font-size:.68rem;letter-spacing:.16em;color:#a56cff;font-weight:900}
.ch-title{font-size:2.08rem;color:#f7fbfa;font-weight:930;letter-spacing:-.055em;margin-top:7px}
.ch-copy{font-size:.86rem;color:#758c92;line-height:1.55;margin-top:7px;max-width:720px}
.ch-badges{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}
.ch-badge{font-size:.70rem;color:#a6b7ba;background:#1a1428;border:1px solid #4b356a;border-radius:999px;padding:6px 9px}
.ch-badge b{color:#b57dff}

.club-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:13px 0 18px}
.ckpi{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px}
.ckpi-label{font-size:.61rem;color:#607b82;text-transform:uppercase;letter-spacing:.08em;font-weight:850}
.ckpi-value{font-size:1.7rem;color:#f3f9f8;font-weight:930;letter-spacing:-.05em;margin-top:8px}
.ckpi-value.green{color:#13e0b4}.ckpi-value.blue{color:#38afff}.ckpi-value.violet{color:#ad76ff}

.club-rank-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.club-feature{position:relative;overflow:hidden;background:linear-gradient(145deg,#08171e,#061219);border:1px solid #173944;border-radius:12px;min-height:235px;padding:17px}
.club-feature.first{border-color:#13c79f}.club-feature.second{border-color:#1888c9}.club-feature.third{border-color:#6b39a4}
.club-feature:after{content:"";position:absolute;right:-35px;bottom:-45px;width:130px;height:130px;border-radius:50%;border:22px solid rgba(255,255,255,.018)}
.cf-rank{font-size:.58rem;letter-spacing:.14em;font-weight:900;color:#13e0b4}.second .cf-rank{color:#24a9ff}.third .cf-rank{color:#a065ff}
.cf-name{font-size:1.08rem;color:#f4f9f8;font-weight:900;letter-spacing:-.035em;margin-top:10px}
.cf-big{font-size:2.3rem;color:#fff;font-weight:950;letter-spacing:-.07em;margin-top:20px}
.cf-big span{font-size:.72rem;color:#687f85;letter-spacing:0;font-weight:750;margin-left:3px}
.cf-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:15px}
.cf-stat{background:#0a2028;border:1px solid #173b45;border-radius:8px;padding:8px}
.cf-stat span{display:block;font-size:.56rem;color:#58737a;text-transform:uppercase;letter-spacing:.07em}
.cf-stat b{display:block;font-size:.88rem;color:#e8f1f0;margin-top:3px}.cf-stat b.up{color:#13e0b4}
.cf-track{height:6px;background:#0d252d;border-radius:99px;overflow:hidden;margin-top:14px}.cf-fill{height:100%;background:linear-gradient(90deg,#13e0b4,#38afff);border-radius:99px}

.club-selector-wrap{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px;margin-top:12px}
.club-detail-head{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;margin-bottom:12px}
.club-detail-name{font-size:1.1rem;color:#eef6f4;font-weight:900}.club-detail-meta{font-size:.64rem;color:#617b82;margin-top:3px}
.club-detail-total{font-size:1.25rem;color:#13e0b4;font-weight:930}

.player-grid-club{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.club-player{background:#07161d;border:1px solid #173843;border-radius:11px;overflow:hidden}
.cp-photo-zone{position:relative;height:118px;background:radial-gradient(circle at 68% 30%,rgba(154,82,255,.18),transparent 45%),linear-gradient(145deg,#171027,#07151b);overflow:hidden}
.cp-photo{position:absolute;right:6px;top:4px;height:122px;width:122px;object-fit:contain;object-position:center top}
.cp-copy{position:absolute;left:12px;top:11px;z-index:2;max-width:58%}
.cp-name{font-size:.84rem;color:#f1f7f6;font-weight:880;line-height:1.05}.cp-pos{font-size:.56rem;color:#687f85;margin-top:4px}
.cp-body{padding:11px 12px 12px}.cp-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}
.cp-stat{background:#0a2028;border:1px solid #173b45;border-radius:7px;padding:7px}.cp-stat span{display:block;font-size:.49rem;color:#58737a;text-transform:uppercase}.cp-stat b{display:block;font-size:.78rem;color:#e8f1f0;margin-top:2px}.cp-stat b.up{color:#13e0b4}
.cp-gains{display:flex;gap:4px;flex-wrap:wrap;margin-top:8px}.cp-gain{font-size:.54rem;padding:3px 5px;border-radius:5px;background:#0a2028;color:#637c82;border:1px solid #173841}.cp-gain.up{color:#13e0b4;border-color:rgba(19,224,180,.22);background:rgba(19,224,180,.04)}

.club-table-wrap{margin-top:12px}
.sync-panel{background:linear-gradient(145deg,#07161d,#061219);border:1px solid #173843;border-radius:12px;padding:15px}
.sync-row{display:flex;align-items:center;justify-content:space-between;gap:16px}
.sync-left{display:flex;align-items:center;gap:11px}.sync-icon{width:38px;height:38px;border-radius:10px;background:#181127;border:1px solid #4b356a;color:#b57dff;display:flex;align-items:center;justify-content:center;font-weight:900}
.sync-title2{font-size:.82rem;color:#edf5f4;font-weight:850}.sync-sub2{font-size:.61rem;color:#607a80;margin-top:3px}
.sync-status{font-size:.61rem;color:#13e0b4;background:#0d251f;border:1px solid #1b5146;border-radius:999px;padding:6px 8px}
@media(max-width:1100px){.club-rank-grid,.player-grid-club{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.club-kpis,.club-rank-grid,.player-grid-club{grid-template-columns:1fr}}
</style>
""",unsafe_allow_html=True)


st.markdown(r"""
<style>
.brand-clean{padding:18px 16px 16px;border-bottom:1px solid #15333c}
.brand-lock{display:flex;align-items:center;gap:12px}.brand-mark-v15{width:48px;height:48px;flex:0 0 48px}
.brand-mfl-v15{font-size:1.12rem;font-weight:950;color:#f7fbfa;letter-spacing:-.055em;line-height:1}.brand-mfl-v15 span{color:#13e0b4}
.brand-hub-v15{font-size:.58rem;color:#6f858b;letter-spacing:.17em;font-weight:900;margin-top:6px}.brand-line-v15{width:86px;height:3px;background:linear-gradient(90deg,#13e0b4,transparent);border-radius:99px;margin-top:10px}
.brand-season-v15{font-size:.56rem;color:#4f696f;letter-spacing:.10em;font-weight:800;margin-top:10px}

.home-shell{max-width:1400px;margin:auto}
.home-hero-v15{position:relative;overflow:hidden;display:grid;grid-template-columns:1.35fr .65fr;gap:16px;background:linear-gradient(118deg,#07151c 0%,#081922 58%,#0b2430 100%);border:1px solid #173944;border-radius:16px;padding:27px 28px;margin-bottom:13px;min-height:220px}
.home-hero-v15:after{content:"";position:absolute;right:-90px;top:-90px;width:330px;height:330px;border-radius:50%;border:48px solid rgba(19,224,180,.03)}
.home-eyebrow-v15{font-size:.60rem;color:#13e0b4;letter-spacing:.18em;font-weight:900}.home-title-v15{font-size:2.35rem;line-height:1.02;color:#f6fbfa;font-weight:950;letter-spacing:-.065em;margin-top:10px;max-width:720px}
.home-copy-v15{font-size:.83rem;color:#7c9399;line-height:1.6;margin-top:13px;max-width:680px}.home-meta-v15{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
.home-pill-v15{font-size:.62rem;color:#a8b8bb;background:#0c252d;border:1px solid #1d4650;border-radius:999px;padding:6px 9px}.home-pill-v15 b{color:#13e0b4}
.network-card-v15{position:relative;z-index:2;background:rgba(5,15,20,.60);border:1px solid #1a414b;border-radius:13px;padding:18px}
.network-label-v15{font-size:.56rem;color:#5b767d;letter-spacing:.13em;font-weight:900}.network-big-v15{font-size:2.45rem;color:#13e0b4;font-weight:950;letter-spacing:-.07em;margin-top:16px}.network-sub-v15{font-size:.66rem;color:#6f878d;margin-top:3px}
.network-rule-v15{height:1px;background:#15343d;margin:16px 0}.network-row-v15{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:9px;font-size:.66rem;color:#70888e}.network-row-v15 b{color:#e2ecea}

.home-kpis-v15{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:17px}.home-kpi-v15{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px 15px}
.hk-label{font-size:.56rem;color:#58747a;letter-spacing:.10em;font-weight:850;text-transform:uppercase}.hk-value{font-size:1.58rem;color:#f2f8f7;font-weight:930;letter-spacing:-.05em;margin-top:8px}.hk-value.mint{color:#13e0b4}.hk-value.blue{color:#38afff}.hk-value.violet{color:#ad76ff}.hk-sub{font-size:.60rem;color:#667f85;margin-top:4px}

.home-section-v15{display:flex;align-items:end;justify-content:space-between;margin:22px 0 9px}.home-section-v15 h3{font-size:.95rem;color:#eaf2f1;margin:0}.home-section-v15 span{font-size:.54rem;color:#526d74;letter-spacing:.10em;font-weight:850}
.workspace-grid-v15{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
a.workspace-card-v15{text-decoration:none!important;color:inherit!important;display:block;position:relative;overflow:hidden;background:linear-gradient(145deg,#07161d,#061219);border:1px solid #173843;border-radius:12px;min-height:170px;padding:18px;transition:.16s ease}
a.workspace-card-v15:hover{transform:translateY(-2px);border-color:#2a5b66;box-shadow:0 16px 30px rgba(0,0,0,.16)}
.workspace-top-v15{display:flex;align-items:center;justify-content:space-between}.workspace-icon-v15{width:42px;height:42px;border-radius:11px;display:flex;align-items:center;justify-content:center;background:#0c2926;border:1px solid #155449}
.workspace-icon-v15.blue{background:#0b2333;border-color:#164968}.workspace-icon-v15.violet{background:#1b122d;border-color:#4c3370}.workspace-icon-v15 svg{width:22px;height:22px}
.workspace-arrow-v15{width:31px;height:31px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#0b2229;border:1px solid #1c4650;color:#8ba1a5;font-size:.85rem}
.workspace-title-v15{font-size:1rem;color:#f2f8f7;font-weight:880;margin-top:18px}.workspace-sub-v15{font-size:.67rem;color:#70878d;line-height:1.45;margin-top:5px;max-width:88%}
.workspace-accent-v15{position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,#13e0b4,transparent)}
.workspace-card-v15.blue .workspace-accent-v15{background:linear-gradient(90deg,#38afff,transparent)}.workspace-card-v15.violet .workspace-accent-v15{background:linear-gradient(90deg,#ad76ff,transparent)}

.home-dashboard-v15{display:grid;grid-template-columns:1.2fr .8fr .8fr;gap:10px;margin-top:10px}.home-bottom-v15{display:grid;grid-template-columns:1.1fr .9fr;gap:10px;margin-top:10px}
.home-panel-v15{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px}.hp-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}
.hp-title{font-size:.76rem;color:#e8f0ef;font-weight:820}.hp-meta{font-size:.52rem;color:#536e74;letter-spacing:.08em}
.home-list-row{display:grid;grid-template-columns:24px 1fr auto;gap:9px;align-items:center;padding:9px 0;border-bottom:1px solid #102b33}.home-list-row:last-child{border-bottom:0}
.home-list-rank{width:22px;height:22px;border-radius:50%;background:#0d252d;color:#a8b7b9;display:flex;align-items:center;justify-content:center;font-size:.57rem}.home-list-main{font-size:.67rem;color:#dbe5e4;font-weight:730}.home-list-sub{font-size:.54rem;color:#59737a;margin-top:2px}.home-list-value{font-size:.68rem;color:#13e0b4;font-weight:900}
.quick-grid-v15{display:grid;grid-template-columns:1fr 1fr;gap:8px}
a.quick-v15{text-decoration:none!important;color:inherit!important;display:flex;align-items:center;justify-content:space-between;gap:10px;background:#081820;border:1px solid #193b45;border-radius:9px;padding:11px 12px;transition:.14s ease}
a.quick-v15:hover{background:#0b222a;border-color:#2a5a65;transform:translateY(-1px)}.quick-left-v15{display:flex;align-items:center;gap:9px}.quick-ico-v15{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:#0d272f;border:1px solid #1d4650}
.quick-ico-v15 svg{width:16px;height:16px}.quick-title-v15{font-size:.68rem;color:#e0e8e7;font-weight:760}.quick-arr-v15{color:#698086}
.spark-chart-v15{height:205px;position:relative}.spark-grid-v15{position:absolute;inset:10px 8px 26px 38px;background:linear-gradient(to right,transparent calc(25% - .5px),#102a32 25%,transparent calc(25% + .5px),transparent calc(50% - .5px),#102a32 50%,transparent calc(50% + .5px),transparent calc(75% - .5px),#102a32 75%,transparent calc(75% + .5px)),linear-gradient(to bottom,transparent calc(25% - .5px),#102a32 25%,transparent calc(25% + .5px),transparent calc(50% - .5px),#102a32 50%,transparent calc(50% + .5px),transparent calc(75% - .5px),#102a32 75%,transparent calc(75% + .5px))}
.spark-svg-v15{position:absolute;left:38px;right:8px;top:10px;bottom:26px;width:calc(100% - 46px);height:calc(100% - 36px)}.spark-labels-v15{position:absolute;left:38px;right:8px;bottom:2px;display:flex;justify-content:space-between;color:#5c747a;font-size:.54rem}
@media(max-width:1000px){.home-hero-v15{grid-template-columns:1fr}.home-kpis-v15,.workspace-grid-v15,.home-dashboard-v15,.home-bottom-v15{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.home-kpis-v15,.workspace-grid-v15,.home-dashboard-v15,.home-bottom-v15,.quick-grid-v15{grid-template-columns:1fr}.home-title-v15{font-size:1.9rem}}
</style>
""",unsafe_allow_html=True)



st.markdown(r"""
<style>
/* ===== v17 PUBLIC BUILD ===== */
.public-brand{padding:20px 16px 17px;border-bottom:1px solid #15333c}
.public-brand-mfl{font-size:1.55rem;color:#f7fbfa;font-weight:950;letter-spacing:-.07em;line-height:1}
.public-brand-mfl span{color:#13e0b4}
.public-brand-sub{font-size:.59rem;color:#70868c;letter-spacing:.18em;font-weight:900;margin-top:7px}
.public-brand-line{width:70px;height:3px;border-radius:99px;background:#13e0b4;margin-top:11px}
.public-brand-season{font-size:.54rem;color:#526c73;letter-spacing:.10em;font-weight:800;margin-top:11px}

.wallet-empty{background:#07161d;border:1px solid #173843;border-radius:9px;padding:10px;font-size:.66rem;color:#70888e}
.wallet-short{font-family:ui-monospace,monospace;background:#07161d;border:1px solid #173843;border-radius:9px;padding:10px;font-size:.67rem;color:#c7d4d5}
.public-connect{background:linear-gradient(135deg,#07171e,#09232a);border:1px solid #1a414b;border-radius:14px;padding:22px;margin:14px 0}
.public-connect-kicker{font-size:.59rem;color:#13e0b4;letter-spacing:.15em;font-weight:900}
.public-connect-title{font-size:1.48rem;color:#f3f9f8;font-weight:900;letter-spacing:-.04em;margin-top:7px}
.public-connect-copy{font-size:.75rem;color:#748b91;line-height:1.55;margin-top:7px;max-width:720px}

.public-home-head{margin-bottom:13px}
.public-home-kicker{font-size:.60rem;color:#13e0b4;letter-spacing:.16em;font-weight:900}
.public-home-title{font-size:2.15rem;color:#f5faf9;font-weight:950;letter-spacing:-.06em;line-height:1.02;margin-top:8px}
.public-home-copy{font-size:.80rem;color:#788f95;margin-top:8px;line-height:1.55;max-width:760px}

.home-brand-row-v16{display:none!important}
.brand-image-shell{display:none!important}
</style>
""",unsafe_allow_html=True)


st.markdown(r"""
<style>
/* ===== v17.3 Public polish ===== */
.wallet-load-warning{margin-top:8px;padding:9px 10px;border-radius:8px;background:#211a08;border:1px solid #5b4818;color:#d8c68c;font-size:.61rem;line-height:1.45}
.wallet-load-warning b{color:#ffe39a}

.home-dashboard-v15{grid-template-columns:1.05fr .78fr 1.05fr!important}
.dev-breakdown-v173{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:5px}
.dev-metric-v173{background:#081b23;border:1px solid #173943;border-radius:9px;padding:11px}
.dev-metric-lab-v173{font-size:.58rem;color:#5c767d;text-transform:uppercase;letter-spacing:.08em;font-weight:800}
.dev-metric-val-v173{font-size:1.35rem;color:#f1f8f6;font-weight:930;margin-top:5px;letter-spacing:-.04em}
.dev-metric-val-v173.mint{color:#13e0b4}.dev-metric-val-v173.blue{color:#38afff}.dev-metric-val-v173.violet{color:#ad76ff}
.attr-bars-v173{margin-top:13px}
.attr-row-v173{display:grid;grid-template-columns:38px 1fr 38px;gap:8px;align-items:center;margin:8px 0}
.attr-name-v173{font-size:.58rem;color:#718990;font-weight:800}
.attr-track-v173{height:7px;background:#0b252d;border-radius:99px;overflow:hidden}
.attr-fill-v173{height:100%;border-radius:99px;background:linear-gradient(90deg,#13e0b4,#38afff)}
.attr-val-v173{font-size:.61rem;color:#c9d6d6;font-weight:800;text-align:right}

.progressor-list-v173{display:flex;flex-direction:column;gap:7px}
.progressor-v173{display:grid;grid-template-columns:32px 44px 1fr auto;gap:9px;align-items:center;background:#081820;border:1px solid #163842;border-radius:9px;padding:7px 9px}
.progress-rank-v173{width:27px;height:27px;border-radius:8px;background:#0d252d;color:#aab9bb;display:flex;align-items:center;justify-content:center;font-size:.61rem;font-weight:850}
.progress-photo-v173{width:42px;height:42px;border-radius:8px;overflow:hidden;background:#0a2028;border:1px solid #1a404a}
.progress-photo-v173 img{width:100%;height:100%;object-fit:contain;object-position:center top}
.progress-name-v173{font-size:.69rem;color:#e1e9e8;font-weight:800}
.progress-club-v173{font-size:.54rem;color:#617a80;margin-top:2px}
.progress-gains-v173{text-align:right}.progress-ovr-v173{font-size:.66rem;color:#13e0b4;font-weight:900}.progress-attr-v173{font-size:.55rem;color:#8da2a6;margin-top:2px}

.highlight-grid-v173{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.highlight-v173{background:#081820;border:1px solid #173843;border-radius:9px;padding:11px;min-height:76px}
.highlight-kicker-v173{font-size:.52rem;color:#58747a;text-transform:uppercase;letter-spacing:.09em;font-weight:850}
.highlight-main-v173{font-size:.84rem;color:#edf5f4;font-weight:850;margin-top:6px;line-height:1.2}
.highlight-sub-v173{font-size:.56rem;color:#647d83;margin-top:4px}

.export-row-v173{display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 12px}
@media(max-width:1000px){.home-dashboard-v15{grid-template-columns:1fr!important}}
@media(max-width:700px){.highlight-grid-v173,.dev-breakdown-v173{grid-template-columns:1fr}}
</style>
""",unsafe_allow_html=True)

def esc(x): return html.escape(str(x))

def page_head(kicker,title,sub):
    st.markdown(
        f'<div class="topline"><div><div class="crumb">{esc(kicker)}</div>'
        f'<div class="h1">{esc(title)}</div><div class="subtitle">{esc(sub)}</div></div>'
        f'<div class="live">LIVE</div></div>',
        unsafe_allow_html=True
    )

def stat(icon,value,label):
    st.markdown(
        f'<div class="stat-card"><div class="stat-icon">{esc(icon)}</div>'
        f'<div><div class="stat-num">{esc(value)}</div><div class="stat-lab">{esc(label)}</div></div></div>',
        unsafe_allow_html=True
    )


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


def grower_gain_html(row):
    pills=[]
    for key,label in [("pace_growth","PAC"),("shooting_growth","SHO"),("passing_growth","PAS"),
                      ("dribbling_growth","DRI"),("defense_growth","DEF"),("physical_growth","PHY")]:
        v=float(row.get(key) or 0)
        if v>0:
            pills.append(f'<span class="gain-pill up">{label} +{v:g}</span>')
    return "".join(pills) or '<span class="gain-pill">No attribute gain</span>'

def grower_leader_card(rank,row):
    cls={1:"first",2:"second",3:"third"}.get(rank,"")
    rating=fmt_rating(row.get("avg_rating"))
    attr=float(row.get("attribute_growth") or 0)
    ovr_growth=float(row.get("ovr_growth") or 0)
    apps=int(row.get("apps") or 0)
    pid=int(row["player_id"])
    photo=f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{pid}/photo.webp"
    return (
      f'<div class="leader-card {cls}">'
      f'<div class="leader-photo-zone">'
      f'<img class="leader-photo" src="{photo}" alt="{esc(row["player"])}">'
      f'<div class="leader-photo-copy">'
      f'<div class="leader-photo-rank">#{rank} · {esc(row["owner"])}</div>'
      f'<div class="leader-photo-name">{esc(row["player"])}</div>'
      f'<div class="leader-photo-owner">{esc(row.get("club") or "No club")}</div>'
      f'</div></div>'
      f'<div class="leader-body">'
      f'<div class="leader-body-top"><div class="leader-ovr-block"><div class="leader-ovr-num">{float(row["ovr"]):g}</div><div class="leader-ovr-lab">CURRENT OVR</div></div>'
      f'<div class="rating-disc"><strong>{rating}</strong><span>RATING</span></div></div>'
      f'<div class="leader-stats">'
      f'<div class="ls"><span>OVR Growth</span><b class="{"up" if ovr_growth>0 else ""}">{delta_text(ovr_growth)}</b></div>'
      f'<div class="ls"><span>Attributes</span><b class="{"up" if attr>0 else ""}">{delta_text(attr)}</b></div>'
      f'<div class="ls"><span>Apps</span><b>{apps}</b></div></div>'
      f'<div class="gain-pills">{grower_gain_html(row)}</div>'
      f'<div class="photo-source">MFL PLAYER PORTRAIT · ID {pid}</div>'
      f'</div></div>'
    )

def grower_standings_html(rows):
    out=['<div class="standing-wrap"><div class="standing-head"><div>#</div><div>Owner</div><div>Player</div><div>OVR</div><div>Growth</div><div>Rating</div><div>Apps</div><div>Attribute gains</div></div>']
    for i,r in enumerate(rows,1):
        gains=[]
        for key,label in [("pace_growth","PAC"),("shooting_growth","SHO"),("passing_growth","PAS"),
                          ("dribbling_growth","DRI"),("defense_growth","DEF"),("physical_growth","PHY")]:
            v=float(r.get(key) or 0)
            if v>0:
                gains.append(f'<span class="s-gain up">{label} +{v:g}</span>')
        gain_html="".join(gains) or '<span class="s-gain">—</span>'
        rank_cls=" top" if i<=3 else ""
        growth=float(r.get("ovr_growth") or 0)
        out.append(
          f'<div class="standing-row">'
          f'<div><div class="s-rank{rank_cls}">{i}</div></div>'
          f'<div class="s-owner">{esc(r["owner"])}</div>'
          f'<div><div class="s-player">{esc(r["player"])}</div><div class="s-club">{esc(r.get("club") or "—")}</div></div>'
          f'<div class="s-num">{float(r["ovr"]):g}</div>'
          f'<div class="{"s-up" if growth>0 else "s-num"}">{delta_text(growth)}</div>'
          f'<div class="s-rating"><span class="rating-dot"></span>{fmt_rating(r.get("avg_rating"))}</div>'
          f'<div class="s-apps">{int(r.get("apps") or 0)}</div>'
          f'<div class="s-gains">{gain_html}</div></div>'
        )
    out.append("</div>")
    return "".join(out)



def agency_portrait(pid):
    return f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(pid)}/photo.webp"

def agency_gain_pills(row):
    gains=[]
    for key,label in [("PAC ↑","PAC"),("SHO ↑","SHO"),("PAS ↑","PAS"),("DRI ↑","DRI"),("DEF ↑","DEF"),("PHY ↑","PHY")]:
        try:v=float(row.get(key) or 0)
        except:v=0
        if v>0:
            gains.append(f'<span class="mgain up">{label} +{v:g}</span>')
    return "".join(gains) or '<span class="mgain">No attribute gain</span>'

def agency_mover_card(rank,row):
    gain=float(row.get("OVR ↑") or 0)
    current=row.get("current_ovr")
    age=row.get("age")
    pos=row.get("position") or "—"
    club=row.get("club") or "No club"
    tag=str(row.get("tag") or "NORMAL")
    return (
      f'<div class="mover-card">'
      f'<div class="mover-photo-zone"><img class="mover-photo" src="{agency_portrait(row["player_id"])}">'
      f'<div class="mover-rank">#{rank} · TOP MOVER</div><div class="mover-tag">{esc(tag)}</div></div>'
      f'<div class="mover-body"><div class="mover-name">{esc(row["player_name"])}</div>'
      f'<div class="mover-meta">{esc(pos)} · {esc(club)} · Age {esc(age if pd.notna(age) else "—")}</div>'
      f'<div class="mover-stats">'
      f'<div class="mstat"><span>OVR</span><b>{esc(current)}</b></div>'
      f'<div class="mstat"><span>Gain</span><b class="up">+{gain:g}</b></div>'
      f'<div class="mstat"><span>Start</span><b>{esc(row.get("start_ovr") or "—")}</b></div>'
      f'</div><div class="mover-gains">{agency_gain_pills(row)}</div></div></div>'
    )

def agency_mint_card(row):
    gain=float(row.get("OVR ↑") or 0)
    date=row.get("Initial date")
    if pd.notna(date):
        try: date_txt=pd.Timestamp(date).strftime("%d %b %Y")
        except: date_txt="—"
    else:
        date_txt="—"
    return (
      f'<div class="mint-card"><div class="mint-photo-wrap"><img class="mint-photo" src="{agency_portrait(row["player_id"])}"></div>'
      f'<div><div class="mint-name">{esc(row["player_name"])}</div>'
      f'<div class="mint-meta">{esc(row.get("position") or "—")} · Age {esc(row.get("age") if pd.notna(row.get("age")) else "—")}<br>{esc(row.get("club") or "No club")}<br>Joined agency {esc(date_txt)}</div>'
      f'<div class="mint-ovr">{esc(row.get("current_ovr") or "—")} OVR</div><div class="mint-gain">+{gain:g} since initial</div></div></div>'
    )



def club_player_portrait(pid):
    return f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(pid)}/photo.webp"

def club_gain_badges(row):
    bits=[]
    for key,label in [("pac","PAC"),("sho","SHO"),("pas","PAS"),("dri","DRI"),("defn","DEF"),("phy","PHY")]:
        v=float(row.get(key) or 0)
        if v>0:
            bits.append(f'<span class="cp-gain up">{label} +{v:g}</span>')
    return "".join(bits) or '<span class="cp-gain">No attribute gain</span>'

def club_feature_card(rank,row,max_attr):
    cls={1:"first",2:"second",3:"third"}.get(rank,"")
    pct=min(100,max(6,float(row.get("ATTR ↑") or 0)/max(max_attr,1)*100))
    return (
      f'<div class="club-feature {cls}">'
      f'<div class="cf-rank">#{rank} · DEVELOPMENT</div>'
      f'<div class="cf-name">{esc(row["Club"])}</div>'
      f'<div class="cf-big">+{float(row["OVR ↑"]):g}<span>OVR</span></div>'
      f'<div class="cf-stats">'
      f'<div class="cf-stat"><span>Players</span><b>{int(row["Players"])}</b></div>'
      f'<div class="cf-stat"><span>Attributes</span><b class="up">+{float(row["ATTR ↑"]):g}</b></div>'
      f'<div class="cf-stat"><span>Avg / player</span><b>{float(row["ATTR ↑"])/max(int(row["Players"]),1):.1f}</b></div>'
      f'</div><div class="cf-track"><div class="cf-fill" style="width:{pct:.0f}%"></div></div></div>'
    )

def club_player_card(row):
    return (
      f'<div class="club-player"><div class="cp-photo-zone">'
      f'<img class="cp-photo" src="{club_player_portrait(row["player_id"])}">'
      f'<div class="cp-copy"><div class="cp-name">{esc(row["player"])}</div><div class="cp-pos">{esc(row["club"])}</div></div></div>'
      f'<div class="cp-body"><div class="cp-stats">'
      f'<div class="cp-stat"><span>OVR</span><b>{esc(row["current_ovr"])}</b></div>'
      f'<div class="cp-stat"><span>OVR ↑</span><b class="{"up" if float(row.get("ovr_gain") or 0)>0 else ""}">+{float(row.get("ovr_gain") or 0):g}</b></div>'
      f'<div class="cp-stat"><span>ATTR ↑</span><b class="{"up" if float(row.get("attr_gain") or 0)>0 else ""}">+{float(row.get("attr_gain") or 0):g}</b></div>'
      f'</div><div class="cp-gains">{club_gain_badges(row)}</div></div></div>'
    )



def short_wallet(v):
    v=(v or "").strip()
    if not v:
        return ""
    if len(v)<=14:
        return v
    return f"{v[:8]}…{v[-5:]}"


def valid_wallet(v):
    v=(v or "").strip()
    return len(v)>=10 and v.lower().startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in v[2:])

if "wallet" not in st.session_state: st.session_state.wallet=""

# ---------------- SIDEBAR ----------------
nav_pages=["Home","Grower or Shower","Agency Development","Club Development"]
query_page=st.query_params.get("page","Home")
if query_page not in nav_pages:
    query_page="Home"

with st.sidebar:
    st.markdown("""<div class="public-brand">
      <div class="public-brand-mfl"><span>MFL</span> HUB</div>
      <div class="public-brand-sub">MANAGEMENT & DEVELOPMENT</div>
      <div class="public-brand-line"></div>
      <div class="public-brand-season">SEASON 17 · PUBLIC</div>
    </div>""",unsafe_allow_html=True)

    page=st.radio("Navigation",nav_pages,index=nav_pages.index(query_page),label_visibility="collapsed")

    st.markdown('<div class="wallet-area"><div class="wallet-label">ACTIVE WALLET</div>',unsafe_allow_html=True)
    if st.session_state.wallet:
        st.markdown(f'<div class="wallet-short">{esc(short_wallet(st.session_state.wallet))}</div>',unsafe_allow_html=True)
        if st.button("Change wallet",use_container_width=True):
            st.session_state.edit_wallet=True
    else:
        st.markdown('<div class="wallet-empty">No wallet connected</div>',unsafe_allow_html=True)
        st.session_state.edit_wallet=True

    if st.session_state.get("edit_wallet",False):
        nw=st.text_input("MFL wallet",value="" if not st.session_state.wallet else st.session_state.wallet,
                         placeholder="0x…",label_visibility="collapsed",key="public_wallet_input")
        st.markdown('<div class="wallet-load-warning"><b>First-time wallet load can take several minutes.</b><br>MFL has to fetch and analyse your players/clubs. Keep the page open while it loads; later visits use cached data where available.</div>',unsafe_allow_html=True)
        if st.button("Use wallet",type="primary",use_container_width=True,key="public_wallet_use"):
            if valid_wallet(nw):
                st.session_state.wallet=nw.strip().lower()
                st.session_state.edit_wallet=False
                st.rerun()
            else:
                st.error("Enter a valid 0x wallet address.")
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown("""<div class="season-box">
      <div class="season-top"><span>Season 17</span><span>PUBLIC</span></div>
      <div class="connected"><i></i><span>MFL API ready</span></div>
    </div>
    <div class="build">PUBLIC POLISH · v17.3</div>""",unsafe_allow_html=True)

wallet=st.session_state.wallet

# ---------------- HOME ----------------
if page=="Home":
    if not wallet:
        st.markdown("""<div class="public-connect">
          <div class="public-connect-kicker">CONNECT YOUR WALLET</div>
          <div class="public-connect-title">Load your own agency and clubs</div>
          <div class="public-connect-copy">Enter your public MFL wallet in the sidebar. This public build does not contain or default to another user's wallet.</div>
        </div>""",unsafe_allow_html=True)

    try:
        c=agency.db();agency.init(c);agency.ensure_v2(c)
        players=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=?",(wallet.lower(),)).fetchone()[0] if wallet else 0
        improved=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=? AND current_ovr>start_ovr",(wallet.lower(),)).fetchone()[0] if wallet else 0
        c.close()
    except Exception:
        players=0; improved=0

    if wallet:
        try:
            mine=club.owned_clubs(wallet)
        except Exception:
            mine=[]
        cached=club.cached(wallet)
    else:
        mine=[]
        cached=pd.DataFrame()
    good=cached[cached["error"].isna()] if (not cached.empty and "error" in cached.columns) else cached
    total_ovr=float(good["ovr_gain"].fillna(0).sum()) if not good.empty else 0
    total_attr=float(good["attr_gain"].fillna(0).sum()) if not good.empty else 0
    total_start=float(good["start_ovr"].fillna(0).sum()) if not good.empty else 0
    total_current=float(good["current_ovr"].fillna(0).sum()) if not good.empty else 0
    synced=len(good)

    st.markdown(f"""
    <div class="home-shell">
      <div class="home-hero-v15">
        <div>
          <div class="home-eyebrow-v15">YOUR SEASON 17 WORKSPACE</div>
          <div class="home-title-v15">Track your MFL network.</div>
          <div class="home-copy-v15">Competition tracking is public. Connect a wallet to unlock personal agency and club development views.</div>
          <div class="home-meta-v15">
            <span class="home-pill-v15"><b>{len(mine) if mine else "—"}</b> owned clubs</span>
            <span class="home-pill-v15"><b>{players or "—"}</b> agency players</span>
            <span class="home-pill-v15"><b>{synced}</b> club players synced</span>
          </div>
        </div>
        <div class="network-card-v15">
          <div class="network-label-v15">SEASON 17 NETWORK DEVELOPMENT</div>
          <div class="network-big-v15">+{total_ovr:g}</div>
          <div class="network-sub-v15">Total OVR gained across loaded club data</div>
          <div class="network-rule-v15"></div>
          <div class="network-row-v15"><span>Attribute gains</span><b>+{total_attr:g}</b></div>
          <div class="network-row-v15"><span>Agency improved</span><b>{improved}</b></div>
          <div class="network-row-v15"><span>Owned clubs</span><b>{len(mine) if mine else "—"}</b></div>
        </div>
      </div>

      <div class="home-kpis-v15">
        <div class="home-kpi-v15"><div class="hk-label">Owned clubs</div><div class="hk-value">{len(mine) if mine else "—"}</div><div class="hk-sub">Verified MFL_OWNER clubs</div></div>
        <div class="home-kpi-v15"><div class="hk-label">Agency players</div><div class="hk-value blue">{players or "—"}</div><div class="hk-sub">Tracked in your current agency</div></div>
        <div class="home-kpi-v15"><div class="hk-label">Club OVR gained</div><div class="hk-value mint">+{total_ovr:g}</div><div class="hk-sub">Loaded Season 17 progression</div></div>
        <div class="home-kpi-v15"><div class="hk-label">Attribute gains</div><div class="hk-value violet">+{total_attr:g}</div><div class="hk-sub">Across synced club players</div></div>
      </div>

      <div class="home-section-v15"><h3>Workspaces</h3><span>CLICK TO OPEN</span></div>
      <div class="workspace-grid-v15">
        <a class="workspace-card-v15" href="?page=Grower%20or%20Shower" target="_self">
          <div class="workspace-top-v15"><div class="workspace-icon-v15"><svg viewBox="0 0 24 24" fill="none" stroke="#13e0b4" stroke-width="1.8"><path d="M6 4h12v3c0 3.8-2.4 6.7-6 7.8C8.4 13.7 6 10.8 6 7V4Z"/><path d="M9 15h6M10 15v3h4v-3M8 20h8"/></svg></div><div class="workspace-arrow-v15">→</div></div>
          <div class="workspace-title-v15">Grower or Shower</div><div class="workspace-sub-v15">Competition leaderboard, player ratings and every recorded stat gain.</div><div class="workspace-accent-v15"></div>
        </a>
        <a class="workspace-card-v15 blue" href="?page=Agency%20Development" target="_self">
          <div class="workspace-top-v15"><div class="workspace-icon-v15 blue"><svg viewBox="0 0 24 24" fill="none" stroke="#38afff" stroke-width="1.8"><circle cx="8" cy="8" r="3"/><circle cx="16" cy="8" r="3"/><path d="M3.5 18c.3-3 2.1-4.7 4.5-4.7S12.2 15 12.5 18M11.5 18c.3-3 2.1-4.7 4.5-4.7s4.2 1.7 4.5 4.7"/></svg></div><div class="workspace-arrow-v15">→</div></div>
          <div class="workspace-title-v15">Agency Development</div><div class="workspace-sub-v15">Top movers, new mints, priority players and ownership-spell progress.</div><div class="workspace-accent-v15"></div>
        </a>
        <a class="workspace-card-v15 violet" href="?page=Club%20Development" target="_self">
          <div class="workspace-top-v15"><div class="workspace-icon-v15 violet"><svg viewBox="0 0 24 24" fill="none" stroke="#ad76ff" stroke-width="1.8"><path d="M4 19h16M6 19V9l6-4 6 4v10"/><path d="M9 19v-5h6v5"/></svg></div><div class="workspace-arrow-v15">→</div></div>
          <div class="workspace-title-v15">Club Development</div><div class="workspace-sub-v15">Compare development across every owned club and drill into the players.</div><div class="workspace-accent-v15"></div>
        </a>
      </div>
    """,unsafe_allow_html=True)

    club_rows=""
    progressor_rows=""
    highlights_html=""
    attr_html=""
    developing_players=0

    if not good.empty:
        clubs_rank=(good.groupby("club").agg(
            ovr=("ovr_gain","sum"),attrs=("attr_gain","sum"),players=("player_id","count")
        ).reset_index().sort_values(["ovr","attrs"],ascending=False).head(5))

        for i,r in enumerate(clubs_rank.to_dict("records"),1):
            club_rows += (
                f'<div class="home-list-row"><div class="home-list-rank">{i}</div>'
                f'<div><div class="home-list-main">{esc(r["club"])}</div>'
                f'<div class="home-list-sub">{int(r["players"])} players · +{float(r["attrs"]):g} attributes</div></div>'
                f'<div class="home-list-value">+{float(r["ovr"]):g}</div></div>'
            )

        # Top Progressors = OVR gain first, then total attribute gain.
        top_progressors=good.sort_values(["ovr_gain","attr_gain","current_ovr"],ascending=False).head(5)
        for i,(_,r) in enumerate(top_progressors.iterrows(),1):
            pid=int(r["player_id"])
            portrait=f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{pid}/photo.webp"
            progressor_rows += (
                f'<div class="progressor-v173">'
                f'<div class="progress-rank-v173">{i}</div>'
                f'<div class="progress-photo-v173"><img src="{portrait}" alt="{esc(r["player"])}"></div>'
                f'<div><div class="progress-name-v173">{esc(r["player"])}</div><div class="progress-club-v173">{esc(r["club"])}</div></div>'
                f'<div class="progress-gains-v173"><div class="progress-ovr-v173">+{float(r["ovr_gain"] or 0):g} OVR</div>'
                f'<div class="progress-attr-v173">+{float(r["attr_gain"] or 0):g} attributes</div></div></div>'
            )

        attr_totals={
            "PAC":float(good["pac"].fillna(0).sum()),
            "SHO":float(good["sho"].fillna(0).sum()),
            "PAS":float(good["pas"].fillna(0).sum()),
            "DRI":float(good["dri"].fillna(0).sum()),
            "DEF":float(good["defn"].fillna(0).sum()),
            "PHY":float(good["phy"].fillna(0).sum()),
        }
        max_attr=max(max(attr_totals.values()),1)
        for lab,val in attr_totals.items():
            pct=max(3,(val/max_attr)*100) if val>0 else 0
            attr_html += (
                f'<div class="attr-row-v173"><div class="attr-name-v173">{lab}</div>'
                f'<div class="attr-track-v173"><div class="attr-fill-v173" style="width:{pct:.1f}%"></div></div>'
                f'<div class="attr-val-v173">+{val:g}</div></div>'
            )

        developing_players=int(((good["ovr_gain"].fillna(0)>0) | (good["attr_gain"].fillna(0)>0)).sum())
        best_club=clubs_rank.iloc[0] if not clubs_rank.empty else None
        best_player=top_progressors.iloc[0] if not top_progressors.empty else None
        best_attr=max(attr_totals,key=attr_totals.get)

        highlights_html = (
            f'<div class="highlight-grid-v173">'
            f'<div class="highlight-v173"><div class="highlight-kicker-v173">Most developed club</div>'
            f'<div class="highlight-main-v173">{esc(best_club["club"]) if best_club is not None else "—"}</div>'
            f'<div class="highlight-sub-v173">+{float(best_club["ovr"]):g} OVR · +{float(best_club["attrs"]):g} attributes</div></div>'
            f'<div class="highlight-v173"><div class="highlight-kicker-v173">Top progressor</div>'
            f'<div class="highlight-main-v173">{esc(best_player["player"]) if best_player is not None else "—"}</div>'
            f'<div class="highlight-sub-v173">+{float(best_player["ovr_gain"]):g} OVR · +{float(best_player["attr_gain"]):g} attributes</div></div>'
            f'<div class="highlight-v173"><div class="highlight-kicker-v173">Players developing</div>'
            f'<div class="highlight-main-v173">{developing_players}</div>'
            f'<div class="highlight-sub-v173">of {len(good)} synced players</div></div>'
            f'<div class="highlight-v173"><div class="highlight-kicker-v173">Strongest attribute</div>'
            f'<div class="highlight-main-v173">{best_attr}</div>'
            f'<div class="highlight-sub-v173">+{attr_totals.get(best_attr,0):g} total gains</div></div>'
            f'</div>'
        )
    else:
        club_rows='<div style="color:#5a7279;font-size:.64rem;padding:34px 4px;text-align:center">Sync Club Development to populate this panel.</div>'
        progressor_rows='<div style="color:#5a7279;font-size:.64rem;padding:34px 4px;text-align:center">Top progressors will appear after club sync.</div>'
        attr_html='<div style="color:#5a7279;font-size:.64rem;padding:34px 4px;text-align:center">Attribute development will appear after club sync.</div>'
        highlights_html='<div style="color:#5a7279;font-size:.64rem;padding:34px 4px;text-align:center">Network highlights will appear after club sync.</div>'

    st.markdown(
        '<div class="home-section-v15"><h3>Network intelligence</h3><span>SEASON 17</span></div>'
        f'<div class="home-dashboard-v15">'
        f'<div class="home-panel-v15"><div class="hp-head"><div class="hp-title">Development breakdown</div><div class="hp-meta">WHAT IS IMPROVING</div></div>'
        f'<div class="dev-breakdown-v173">'
        f'<div class="dev-metric-v173"><div class="dev-metric-lab-v173">OVR gained</div><div class="dev-metric-val-v173 mint">+{total_ovr:g}</div></div>'
        f'<div class="dev-metric-v173"><div class="dev-metric-lab-v173">Attribute gains</div><div class="dev-metric-val-v173 violet">+{total_attr:g}</div></div>'
        f'<div class="dev-metric-v173"><div class="dev-metric-lab-v173">Players developing</div><div class="dev-metric-val-v173 blue">{developing_players}</div></div>'
        f'<div class="dev-metric-v173"><div class="dev-metric-lab-v173">Players synced</div><div class="dev-metric-val-v173">{synced}</div></div>'
        f'</div><div class="attr-bars-v173">{attr_html}</div></div>'
        f'<div class="home-panel-v15"><div class="hp-head"><div class="hp-title">Top 5 clubs</div><div class="hp-meta">OVR GAINED</div></div>{club_rows}</div>'
        f'<div class="home-panel-v15"><div class="hp-head"><div class="hp-title">Top 5 Progressors</div><div class="hp-meta">OVR → ATTRIBUTES</div></div>'
        f'<div class="progressor-list-v173">{progressor_rows}</div></div></div>',
        unsafe_allow_html=True
    )

    st.markdown("""
      <div class="home-bottom-v15">
        <div class="home-panel-v15">
          <div class="hp-head"><div class="hp-title">Quick actions</div><div class="hp-meta">CLICK TO OPEN</div></div>
          <div class="quick-grid-v15">
            <a class="quick-v15" href="?page=Grower%20or%20Shower" target="_self"><div class="quick-left-v15"><div class="quick-ico-v15"><svg viewBox="0 0 24 24" fill="none" stroke="#13e0b4" stroke-width="1.8"><path d="M6 4h12v3c0 3.8-2.4 6.7-6 7.8C8.4 13.7 6 10.8 6 7V4Z"/></svg></div><div class="quick-title-v15">Grower or Shower</div></div><div class="quick-arr-v15">→</div></a>
            <a class="quick-v15" href="?page=Agency%20Development" target="_self"><div class="quick-left-v15"><div class="quick-ico-v15"><svg viewBox="0 0 24 24" fill="none" stroke="#38afff" stroke-width="1.8"><circle cx="8" cy="8" r="3"/><circle cx="16" cy="8" r="3"/></svg></div><div class="quick-title-v15">Agency Development</div></div><div class="quick-arr-v15">→</div></a>
            <a class="quick-v15" href="?page=Club%20Development" target="_self"><div class="quick-left-v15"><div class="quick-ico-v15"><svg viewBox="0 0 24 24" fill="none" stroke="#ad76ff" stroke-width="1.8"><path d="M4 19h16M6 19V9l6-4 6 4v10"/></svg></div><div class="quick-title-v15">Club Development</div></div><div class="quick-arr-v15">→</div></a>
            <a class="quick-v15" href="?page=Club%20Development" target="_self"><div class="quick-left-v15"><div class="quick-ico-v15"><svg viewBox="0 0 24 24" fill="none" stroke="#13e0b4" stroke-width="1.8"><path d="M20 7v5h-5"/><path d="M18.5 15A7 7 0 1 1 19 8l1 4"/></svg></div><div class="quick-title-v15">Sync latest data</div></div><div class="quick-arr-v15">→</div></a>
          </div>
        </div>
        <div class="home-panel-v15">
          <div class="hp-head"><div class="hp-title">Network highlights</div><div class="hp-meta">LIVE DEVELOPMENT</div></div>
    """,unsafe_allow_html=True)
    st.markdown(f'{highlights_html}</div></div>',unsafe_allow_html=True)

# ---------------- GROWER ----------------
elif page=="Grower or Shower":
    conn=grower.db();grower.init_db(conn)
    rows=grower.leaderboard(conn)
    leader=rows[0] if rows else None
    total_attr=sum(float(r.get("attribute_growth") or 0) for r in rows) if rows else 0
    total_apps=sum(int(r.get("apps") or 0) for r in rows) if rows else 0

    st.markdown(
        f'<div class="grower-hero"><div class="gh-kicker">WORKTHESPACE · SEASON 17</div>'
        f'<div class="gh-title">Grower or Shower</div>'
        f'<div class="gh-copy">A live development race. OVR growth decides the winner, total attribute growth breaks ties, then Season 17 rating.</div>'
        f'<div class="gh-badges"><span class="gh-badge"><b>{len(rows) if rows else 14}</b> entrants</span>'
        f'<span class="gh-badge"><b>+{total_attr:g}</b> attribute growth</span>'
        f'<span class="gh-badge"><b>{total_apps}</b> rated apps</span>'
        f'<span class="gh-badge">Leader <b>{esc(leader["owner"]) if leader else "—"}</b></span></div></div>',
        unsafe_allow_html=True
    )

    controls=st.columns([1.25,1.1,4])
    with controls[0]:
        refresh=st.button("↻ Refresh competition",type="primary",use_container_width=True)
    with controls[1]:
        with st.popover("Competition settings",use_container_width=True):
            grower_start=st.text_input("Season 17 baseline (UTC)",value=st.session_state.get("grower_start","2026-09-22T00:00:00Z"))
            st.session_state.grower_start=grower_start
            os.environ["GROWER_START"]=grower_start

    if refresh:
        try:
            tok=grower.refresh_access_token()
            bar=st.progress(0,text="Refreshing entrants…")
            errs=[]
            for i,(pid,owner) in enumerate(grower.ENTRANTS.items(),1):
                try:
                    grower.sync_player(conn,tok,pid,owner)
                except Exception:
                    errs.append(owner)
                bar.progress(i/len(grower.ENTRANTS),text=f"{i}/{len(grower.ENTRANTS)} entrants")
            bar.empty()
            if errs:
                st.warning(f"Updated competition with {len(errs)} entrant(s) skipped.")
            else:
                st.success("Competition refreshed.")
            rows=grower.leaderboard(conn)
        except Exception as e:
            st.error("MFL could not refresh the competition.")
            with st.expander("Technical detail"):
                st.code(str(e))

    if not rows:
        st.markdown('<div class="empty"><b>Competition cache is empty on this fresh public deployment</b>Click <strong>Refresh competition</strong> above once to load the 14 entrants and current Season 17 data.</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-head2"><h3>Front runners</h3><span class="small-note2">OVR → ATTR → RATING</span></div>',unsafe_allow_html=True)
        cards="".join(grower_leader_card(i,r) for i,r in enumerate(rows[:3],1))
        st.markdown(f'<div class="leader-grid">{cards}</div>',unsafe_allow_html=True)

        best_rating=max((float(r.get("avg_rating") or 0) for r in rows),default=0)
        growers=sum(1 for r in rows if float(r.get("attribute_growth") or 0)>0)
        st.markdown(
            f'<div class="comp-grid">'
            f'<div class="comp-card"><div class="comp-title">Players showing development</div><div class="comp-big">{growers}</div><div class="comp-sub">Entrants with a recorded attribute gain</div></div>'
            f'<div class="comp-card"><div class="comp-title">Best Season 17 rating</div><div class="comp-big">{best_rating:.2f}</div><div class="comp-sub">Highest current competition average</div></div></div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="section-head2"><h3>Live standings</h3><span class="small-note2">ALL ENTRANTS</span></div>',unsafe_allow_html=True)
        st.markdown(grower_standings_html(rows),unsafe_allow_html=True)

        developed=[r for r in rows if float(r.get("attribute_growth") or 0)>0 or float(r.get("ovr_growth") or 0)>0]
        if developed:
            st.markdown('<div class="section-head2"><h3>Development spotlight</h3><span class="small-note2">RECORDED THIS COMPETITION</span></div>',unsafe_allow_html=True)
            spotlight=[]
            for r in developed[:3]:
                gains=[]
                for key,label in [("pace_growth","PAC"),("shooting_growth","SHO"),("passing_growth","PAS"),("dribbling_growth","DRI"),("defense_growth","DEF"),("physical_growth","PHY")]:
                    v=float(r.get(key) or 0)
                    if v>0:
                        gains.append(f"{label} +{v:g}")
                spotlight.append(
                    f'<div class="dev-card"><div class="dev-player">{esc(r["player"])}</div>'
                    f'<div class="dev-owner">{esc(r["owner"])}</div>'
                    f'<div class="dev-gain">+{float(r.get("attribute_growth") or 0):g}</div>'
                    f'<div class="dev-sub">{" · ".join(gains) if gains else "OVR development"}</div></div>'
                )
            st.markdown(f'<div class="development-strip">{"".join(spotlight)}</div>',unsafe_allow_html=True)
    conn.close()

# ---------------- AGENCY ----------------
elif page=="Agency Development":
    if not wallet:
        st.markdown("""<div class="public-connect">
          <div class="public-connect-kicker">AGENCY DEVELOPMENT</div>
          <div class="public-connect-title">Connect a wallet to continue</div>
          <div class="public-connect-copy">Enter your public MFL wallet in the sidebar to build your agency development view.</div>
        </div>""",unsafe_allow_html=True)
        st.stop()

    c=agency.db();agency.init(c);agency.ensure_v2(c)
    rows=c.execute("""SELECT o.*,COALESCE(t.tag,'NORMAL') tag,COALESCE(t.note,'') note,
      m.age,m.position,m.club,a.last_event_at,a.match_events,a.training_events,a.total_events
      FROM ownership_v65 o
      LEFT JOIN tags t ON t.wallet=o.wallet AND t.player_id=o.player_id
      LEFT JOIN player_meta m ON m.wallet=o.wallet AND m.player_id=o.player_id
      LEFT JOIN activity a ON a.wallet=o.wallet AND a.player_id=o.player_id
      WHERE o.wallet=?""",(wallet.lower(),)).fetchall()

    if not rows:
        st.markdown("""<div class="public-connect">
          <div class="public-connect-kicker">FIRST-TIME AGENCY LOAD</div>
          <div class="public-connect-title">Build this wallet's agency</div>
          <div class="public-connect-copy">This wallet has not been cached yet. <strong>The first load can take several minutes</strong> because MFL player history has to be analysed. Keep this page open while it runs. Start with a small batch below, then continue safely from the Agency page.</div>
        </div>""",unsafe_allow_html=True)
        if st.button("Load first 4 players",type="primary",key="public_agency_first_load"):
            bar=st.progress(0,text="Loading agency safely…")
            try:
                def p(n,total):
                    bar.progress(n/max(total,1),text=f"{n}/{max(total,1)}")
                total,added,errs,analysed,planned=agency.sync(wallet,p,batch_size=4)
                bar.empty()
                if added:
                    st.success(f"Loaded {added} player(s). Continue in small batches once the page opens.")
                    st.rerun()
                elif total == 0:
                    st.info("MFL returned no players for this wallet.")
                elif errs:
                    st.warning(f"MFL returned {len(errs)} player error(s) before anything could be saved. Wait a moment and try again.")
                    with st.expander("Import detail"):
                        for pid,msg in errs[:8]:
                            st.code(f"{pid}: {msg}")
                else:
                    st.warning("Nothing was saved yet. Try again in a moment.")
            except Exception as e:
                bar.empty()
                st.error("MFL could not load this wallet yet.")
                with st.expander("Technical detail"):
                    st.code(str(e))
    else:
        df=pd.DataFrame([dict(r) for r in rows])
        for lab,cur,start_col in [
            ("OVR ↑","current_ovr","start_ovr"),("PAC ↑","current_pac","start_pac"),("SHO ↑","current_sho","start_sho"),
            ("PAS ↑","current_pas","start_pas"),("DRI ↑","current_dri","start_dri"),("DEF ↑","current_def","start_def"),("PHY ↑","current_phy","start_phy")]:
            df[lab]=pd.to_numeric(df[cur],errors="coerce")-pd.to_numeric(df[start_col],errors="coerce")
        df["Acquired"]=pd.to_datetime(df.acquired_at,utc=True,errors="coerce")
        df["Initial date"]=pd.to_datetime(df.history_start,utc=True,errors="coerce")

        improved=int((df["OVR ↑"]>0).sum())
        originals=int((df.source=="NEW MINT / ORIGINAL").sum())
        priority=int((df.tag=="PRIORITY").sum())
        total_ovr=float(df["OVR ↑"].fillna(0).clip(lower=0).sum())

        st.markdown(
            f'<div class="agency-hero"><div class="ah-kicker">AGENCY · OWNERSHIP DEVELOPMENT</div>'
            f'<div class="ah-title">Agency Development</div>'
            f'<div class="ah-copy">See which players are moving, where they started, and which new mints or priority players deserve attention.</div>'
            f'<div class="ah-badges"><span class="ah-badge"><b>{len(df)}</b> players</span>'
            f'<span class="ah-badge"><b>{improved}</b> improved OVR</span>'
            f'<span class="ah-badge"><b>{originals}</b> new/original</span>'
            f'<span class="ah-badge"><b>{priority}</b> priority</span></div></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="agency-kpis">'
            f'<div class="ag-kpi"><div class="ag-kpi-label">Players tracked</div><div class="ag-kpi-value">{len(df)}</div></div>'
            f'<div class="ag-kpi"><div class="ag-kpi-label">OVR gained</div><div class="ag-kpi-value green">+{total_ovr:g}</div></div>'
            f'<div class="ag-kpi"><div class="ag-kpi-label">Improved players</div><div class="ag-kpi-value blue">{improved}</div></div>'
            f'<div class="ag-kpi"><div class="ag-kpi-label">Priority list</div><div class="ag-kpi-value violet">{priority}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        agency_export=df[[
            "player_id","player_name","age","position","club","source","Acquired","Initial date",
            "start_ovr","current_ovr","OVR ↑","PAC ↑","SHO ↑","PAS ↑","DRI ↑","DEF ↑","PHY ↑","tag","note"
        ]].copy()
        agency_export=agency_export.rename(columns={
            "player_id":"Player ID","player_name":"Player","age":"Age","position":"Position","club":"Club",
            "source":"Ownership","Initial date":"Joined Agency","start_ovr":"Start OVR",
            "current_ovr":"Current OVR","tag":"Tag","note":"Note"
        })
        for col in ["Acquired","Joined Agency"]:
            agency_export[col]=pd.to_datetime(agency_export[col],utc=True,errors="coerce").dt.strftime("%Y-%m-%d %H:%M UTC").fillna("")
        st.download_button(
            "↓ Export Agency Development CSV",
            data=agency_export.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"mfl_agency_development_{short_wallet(wallet).replace('…','_')}.csv",
            mime="text/csv",
            key="agency_export_csv"
        )

        movers=df[df["OVR ↑"]>0].sort_values(["OVR ↑","current_ovr"],ascending=False).head(4)
        st.markdown('<div class="section-head2"><h3>Top movers</h3><span class="small-note2">OWNERSHIP-SPELL DEVELOPMENT</span></div>',unsafe_allow_html=True)
        if movers.empty:
            st.markdown('<div class="empty"><b>No OVR movers yet</b>Attribute-level progression can still be reviewed below.</div>',unsafe_allow_html=True)
        else:
            mover_html="".join(agency_mover_card(i,r) for i,(_,r) in enumerate(movers.iterrows(),1))
            st.markdown(f'<div class="movers-grid">{mover_html}</div>',unsafe_allow_html=True)

        mints=df[df.source=="NEW MINT / ORIGINAL"].sort_values(["OVR ↑","current_ovr"],ascending=False).head(6)
        if not mints.empty:
            st.markdown('<div class="section-head2"><h3>New mints & originals</h3><span class="small-note2">JOINED AGENCY FROM INITIAL STATE</span></div>',unsafe_allow_html=True)
            mint_html="".join(agency_mint_card(r) for _,r in mints.iterrows())
            st.markdown(f'<div class="mint-grid">{mint_html}</div>',unsafe_allow_html=True)

        st.markdown('<div class="section-head2"><h3>Agency workspace</h3><span class="small-note2">FILTER · TAG · REVIEW</span></div>',unsafe_allow_html=True)
        tabs=st.tabs(["Development","My List","All Agency"])

        with tabs[0]:
            v=df.sort_values(["OVR ↑","current_ovr"],ascending=False,na_position="last")
            q=st.text_input("Search development",placeholder="Search player name",key="agency_dev_search")
            if q:
                v=v[v.player_name.str.contains(q,case=False,na=False)]
            st.dataframe(
                v[["player_name","age","position","club","start_ovr","current_ovr","OVR ↑","PAC ↑","SHO ↑","PAS ↑","DRI ↑","DEF ↑","PHY ↑","tag"]]
                .rename(columns={"player_name":"Player","age":"Age","position":"Position","club":"Club","start_ovr":"Start","current_ovr":"Current","tag":"Tag"}),
                use_container_width=True,hide_index=True,height=520
            )
            st.caption("Detailed table retained for scanning the full agency; the visual cards above surface the important movers first.")

        with tabs[1]:
            tagged=df[df.tag!="NORMAL"].copy()
            if tagged.empty:
                st.markdown('<div class="empty"><b>No tagged players yet</b>Add DEVELOP, PRIORITY or WATCH tags below.</div>',unsafe_allow_html=True)
            else:
                tag_cards=[]
                for _,r in tagged.sort_values(["tag","OVR ↑"],ascending=[True,False]).head(12).iterrows():
                    tag_cards.append(
                        f'<div class="tag-card"><span class="tag-pill {esc(r["tag"])}">{esc(r["tag"])}</span>'
                        f'<div class="tag-name">{esc(r["player_name"])}</div>'
                        f'<div class="tag-note">{esc(r["note"] or "No note")}<br>OVR {esc(r["current_ovr"])} · +{float(r["OVR ↑"] or 0):g}</div></div>'
                    )
                st.markdown(f'<div class="tag-board">{"".join(tag_cards)}</div>',unsafe_allow_html=True)
                st.write("")

            opts={f"{r.player_name} · {int(r.player_id)}":int(r.player_id) for _,r in df.sort_values("player_name").iterrows()}
            col1,col2=st.columns([1.2,1])
            with col1:
                who=st.selectbox("Player",list(opts),key="agency_tag_player")
            ex=df[df.player_id==opts[who]].iloc[0]
            with col2:
                tags=["NORMAL","DEVELOP","PRIORITY","WATCH"]
                tag=st.selectbox("Tag",tags,index=tags.index(ex.tag) if ex.tag in tags else 0,key="agency_tag_type")
            note=st.text_input("Note",value=ex.note or "",key="agency_tag_note")
            if st.button("Save tag",type="primary",key="agency_save_tag"):
                c.execute("""INSERT INTO tags(wallet,player_id,tag,note) VALUES(?,?,?,?)
                ON CONFLICT(wallet,player_id) DO UPDATE SET tag=excluded.tag,note=excluded.note""",
                          (wallet.lower(),opts[who],tag,note))
                c.commit();st.rerun()

        with tabs[2]:
            f1,f2,f3=st.columns([1.7,1,1])
            with f1:
                q=st.text_input("Search players",placeholder="Search by player name",key="agency_all_search")
            with f2:
                tag_filter=st.selectbox("Tag",["All","PRIORITY","DEVELOP","WATCH","NORMAL"],key="agency_all_tag")
            with f3:
                sort=st.selectbox("Sort",["OVR gain","OVR","Age","Name"],key="agency_all_sort")
            v=df.copy()
            if q:
                v=v[v.player_name.str.contains(q,case=False,na=False)]
            if tag_filter!="All":
                v=v[v.tag==tag_filter]
            if sort=="OVR gain":
                v=v.sort_values(["OVR ↑","current_ovr"],ascending=False,na_position="last")
            elif sort=="OVR":
                v=v.sort_values("current_ovr",ascending=False,na_position="last")
            elif sort=="Age":
                v=v.sort_values("age",na_position="last")
            else:
                v=v.sort_values("player_name")
            st.dataframe(
                v[["player_name","age","position","club","source","Acquired","start_ovr","current_ovr","OVR ↑","tag"]]
                .rename(columns={"player_name":"Player","age":"Age","position":"Position","club":"Club","source":"Ownership","start_ovr":"Start","current_ovr":"OVR","tag":"Tag"}),
                use_container_width=True,hide_index=True,height=600
            )

        with st.expander("Refresh player data"):
            st.caption("Refreshes 8 players at a time to reduce MFL rate-limit pressure on the public app.")
            if st.button("Refresh next 8 players",key="agency_refresh20"):
                bar=st.progress(0,text="Refreshing players…")
                def prog(n,total):
                    bar.progress(n/max(total,1),text=f"{n}/{min(total,8)}")
                try:
                    done,total,errs=agency.refresh_current_v21(wallet,prog,8)
                    bar.empty()
                    st.success(f"Updated {done} players." if not errs else f"Updated {done}; {len(errs)} issue(s).")
                except Exception as e:
                    bar.empty()
                    st.error("MFL could not refresh this batch.")
                    with st.expander("Technical detail"):
                        st.code(str(e))
    c.close()

# ---------------- CLUBS ----------------
elif page=="Club Development":
    if not wallet:
        st.markdown("""<div class="public-connect">
          <div class="public-connect-kicker">CLUB DEVELOPMENT</div>
          <div class="public-connect-title">Connect a wallet to continue</div>
          <div class="public-connect-copy">Enter your public MFL wallet in the sidebar to discover owned clubs and sync Season 17 development.</div>
        </div>""",unsafe_allow_html=True)
        st.stop()

    try:
        mine=club.owned_clubs(wallet)
    except Exception:
        mine=[]
    cached=club.cached(wallet)
    good=cached[cached["error"].isna()] if (not cached.empty and "error" in cached.columns) else cached

    total_ovr=float(good["ovr_gain"].fillna(0).sum()) if not good.empty else 0
    total_attr=float(good["attr_gain"].fillna(0).sum()) if not good.empty else 0
    developed=int(((good["ovr_gain"].fillna(0)>0) | (good["attr_gain"].fillna(0)>0)).sum()) if not good.empty else 0
    synced=len(good)

    st.markdown(
        f'<div class="club-hero"><div class="ch-kicker">CLUB NETWORK · SEASON 17</div>'
        f'<div class="ch-title">Club Development</div>'
        f'<div class="ch-copy">Compare progression across your owned clubs, then drill into the players driving each club forward.</div>'
        f'<div class="ch-badges"><span class="ch-badge"><b>{len(mine) if mine else "—"}</b> owned clubs</span>'
        f'<span class="ch-badge"><b>{synced}</b> players synced</span>'
        f'<span class="ch-badge"><b>+{total_ovr:g}</b> OVR</span>'
        f'<span class="ch-badge"><b>+{total_attr:g}</b> attributes</span></div></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="club-kpis">'
        f'<div class="ckpi"><div class="ckpi-label">Owned clubs</div><div class="ckpi-value">{len(mine) if mine else "—"}</div></div>'
        f'<div class="ckpi"><div class="ckpi-label">Players synced</div><div class="ckpi-value blue">{synced}</div></div>'
        f'<div class="ckpi"><div class="ckpi-label">OVR gained</div><div class="ckpi-value green">+{total_ovr:g}</div></div>'
        f'<div class="ckpi"><div class="ckpi-label">Players developing</div><div class="ckpi-value violet">{developed}</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    remaining=club.cooldown_remaining()
    st.markdown(
        f'<div class="sync-panel"><div class="sync-row"><div class="sync-left"><div class="sync-icon">⟳</div><div>'
        f'<div class="sync-title2">Slow full-network sync</div><div class="sync-sub2">Processes all remaining owned-club players safely and saves each one immediately.</div>'
        f'</div></div><div class="sync-status">{"COOLDOWN" if remaining>0 else "READY"}</div></div></div>',
        unsafe_allow_html=True
    )
    st.write("")
    b1,b2=st.columns([1.2,4])
    with b1:
        do_sync=st.button("Sync all remaining",type="primary",use_container_width=True,disabled=remaining>0)
    with b2:
        if remaining>0:
            st.info(f"MFL cooldown active — about {max(1,math.ceil(remaining/60))} minute(s) remaining. Cached data is safe.")
        else:
            st.caption(f"{synced} player records currently cached. One click continues from the first unsynced player.")

    if do_sync:
        bar=st.progress(0,text="Preparing full sync…")
        status=st.empty()
        starting=synced
        def prog(done,total,errs):
            bar.progress(done/max(total,1),text=f"{done}/{total} remaining players processed")
            status.caption(f"{starting + done - errs} total cached · {errs} delayed/skipped · leave this page open")
        try:
            season_start=st.session_state.get("season_start","2026-09-22T00:00:00Z")
            res=club.sync_batch(wallet,season_start,None,prog)
            bar.empty();status.empty()
            if res.get("rate_limited"):
                mins=max(1,math.ceil(res.get("cooldown",0)/60))
                st.warning(f"MFL rate limit reached after saving {res['saved']} player(s). Wait about {mins} minute(s), then run again.")
            elif res["errors"]:
                st.warning(f"Saved {res['saved']} player(s); {len(res['errors'])} slow/failed player(s) can be retried next run.")
            else:
                st.success(f"Saved {res['saved']} player(s). Full run complete.")
            st.rerun()
        except Exception as e:
            bar.empty();status.empty()
            st.error("MFL could not complete the sync.")
            with st.expander("Technical detail"):
                st.code(str(e))

    cached=club.cached(wallet)
    good=cached[cached["error"].isna()] if (not cached.empty and "error" in cached.columns) else cached

    if good.empty:
        st.markdown('<div class="empty"><b>No club development loaded yet</b>Run the sync once and this page will populate automatically.</div>',unsafe_allow_html=True)
    else:
        clubs=(good.groupby("club").agg(
            Players=("player_id","count"),OVR=("ovr_gain","sum"),Attributes=("attr_gain","sum"),
            PAC=("pac","sum"),SHO=("sho","sum"),PAS=("pas","sum"),DRI=("dri","sum"),DEF=("defn","sum"),PHY=("phy","sum")
        ).reset_index().sort_values(["OVR","Attributes"],ascending=False))
        clubs=clubs.rename(columns={"club":"Club","OVR":"OVR ↑","Attributes":"ATTR ↑"})

        club_players_export=good[[
            "player_id","player","club","start_ovr","current_ovr","ovr_gain","attr_gain",
            "pac","sho","pas","dri","defn","phy","baseline_at","last_progression","checked_at"
        ]].copy()
        club_players_export=club_players_export.rename(columns={
            "player_id":"Player ID","player":"Player","club":"Club","start_ovr":"S17 Start OVR",
            "current_ovr":"Current OVR","ovr_gain":"OVR ↑","attr_gain":"ATTR ↑","pac":"PAC ↑",
            "sho":"SHO ↑","pas":"PAS ↑","dri":"DRI ↑","defn":"DEF ↑","phy":"PHY ↑",
            "baseline_at":"Baseline Date","last_progression":"Last Progression","checked_at":"Last Checked"
        })
        for col in ["Baseline Date","Last Progression","Last Checked"]:
            club_players_export[col]=pd.to_datetime(club_players_export[col],utc=True,errors="coerce").dt.strftime("%Y-%m-%d %H:%M UTC").fillna("")

        ex1,ex2,_=st.columns([1.3,1.5,4])
        with ex1:
            st.download_button(
                "↓ Export Club Summary CSV",
                data=clubs.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"mfl_club_summary_{short_wallet(wallet).replace('…','_')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="club_summary_export_csv"
            )
        with ex2:
            st.download_button(
                "↓ Export All Club Players CSV",
                data=club_players_export.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"mfl_club_development_{short_wallet(wallet).replace('…','_')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="club_players_export_csv"
            )

        st.markdown('<div class="section-head2"><h3>Top developing clubs</h3><span class="small-note2">SEASON 17 NETWORK LEADERS</span></div>',unsafe_allow_html=True)
        top=clubs.head(3)
        max_attr=float(top["ATTR ↑"].max()) if not top.empty else 1
        cards="".join(club_feature_card(i,r,max_attr) for i,r in enumerate(top.to_dict("records"),1))
        st.markdown(f'<div class="club-rank-grid">{cards}</div>',unsafe_allow_html=True)

        st.markdown('<div class="section-head2"><h3>Club drill-down</h3><span class="small-note2">PLAYER DEVELOPMENT</span></div>',unsafe_allow_html=True)
        choice=st.selectbox("Choose club",clubs["Club"].tolist(),label_visibility="collapsed",key="club_visual_choice")
        detail=good[good.club==choice].sort_values(["ovr_gain","attr_gain","current_ovr"],ascending=False)
        selected_row=clubs[clubs["Club"]==choice].iloc[0]

        st.markdown(
            f'<div class="club-selector-wrap"><div class="club-detail-head"><div>'
            f'<div class="club-detail-name">{esc(choice)}</div>'
            f'<div class="club-detail-meta">{int(selected_row["Players"])} players · +{float(selected_row["ATTR ↑"]):g} attributes</div>'
            f'</div><div class="club-detail-total">+{float(selected_row["OVR ↑"]):g} OVR</div></div></div>',
            unsafe_allow_html=True
        )

        movers=detail[(detail["ovr_gain"].fillna(0)>0) | (detail["attr_gain"].fillna(0)>0)].head(8)
        if movers.empty:
            st.markdown('<div class="empty"><b>No recorded development in this club yet</b>The detail table below still shows every synced player.</div>',unsafe_allow_html=True)
        else:
            st.write("")
            player_html="".join(club_player_card(r) for _,r in movers.iterrows())
            st.markdown(f'<div class="player-grid-club">{player_html}</div>',unsafe_allow_html=True)

        st.markdown('<div class="section-head2"><h3>Club leaderboard</h3><span class="small-note2">ALL OWNED CLUBS</span></div>',unsafe_allow_html=True)
        st.dataframe(
            clubs,
            use_container_width=True,hide_index=True,height=min(500,75+35*len(clubs))
        )

        st.markdown('<div class="section-head2"><h3>Full player detail</h3><span class="small-note2">SELECTED CLUB</span></div>',unsafe_allow_html=True)
        st.dataframe(
            detail[["player","start_ovr","current_ovr","ovr_gain","attr_gain","pac","sho","pas","dri","defn","phy"]]
            .rename(columns={"player":"Player","start_ovr":"S17 Start","current_ovr":"Current","ovr_gain":"OVR ↑","attr_gain":"ATTR ↑",
                             "pac":"PAC ↑","sho":"SHO ↑","pas":"PAS ↑","dri":"DRI ↑","defn":"DEF ↑","phy":"PHY ↑"}),
            use_container_width=True,hide_index=True,height=520
        )
