
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
.section-head2{display:flex;align-items:center;justify-content:space-between;margin:22px 0 9px}.section-head2 h3{font-size:.88rem;margin:0;color:#e8efef}.small-note2{font-size:.54rem;color:#5b7379;letter-spacing:.08em}
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
.gh-kicker{font-size:.56rem;letter-spacing:.16em;color:#13e0b4;font-weight:900}.gh-title{font-size:1.85rem;color:#f7fbfa;font-weight:930;letter-spacing:-.055em;margin-top:7px}
.gh-copy{font-size:.72rem;color:#758c92;line-height:1.55;margin-top:7px;max-width:650px}.gh-badges{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}
.gh-badge{font-size:.58rem;color:#a6b7ba;background:#0c252d;border:1px solid #1e4650;border-radius:999px;padding:6px 8px}.gh-badge b{color:#13e0b4}
.leader-grid{display:grid;grid-template-columns:1.18fr .91fr .91fr;gap:12px;margin-bottom:14px}
.leader-card{position:relative;overflow:hidden;background:linear-gradient(145deg,#08171e,#061219);border:1px solid #173944;border-radius:13px;min-height:220px;padding:18px}
.leader-card.first{border-color:#13c79f}.leader-card.second{border-color:#1888c9}.leader-card.third{border-color:#6b39a4}
.leader-card:after{content:"";position:absolute;right:-43px;top:-38px;width:120px;height:120px;border-radius:50%;border:20px solid rgba(255,255,255,.018)}
.leader-rank{font-size:.56rem;letter-spacing:.14em;font-weight:900;color:#13e0b4}.second .leader-rank{color:#24a9ff}.third .leader-rank{color:#a065ff}
.leader-player{font-size:1.35rem;color:#f4f9f8;font-weight:920;letter-spacing:-.045em;margin-top:11px}.leader-owner{font-size:.67rem;color:#758c92;margin-top:3px}
.leader-ovr{display:flex;align-items:flex-end;justify-content:space-between;margin-top:17px}.leader-ovr-num{font-size:2.25rem;color:#fff;font-weight:950;letter-spacing:-.07em;line-height:.9}.leader-ovr-lab{font-size:.54rem;color:#5f787f;margin-top:5px}
.rating-disc{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:radial-gradient(circle at 35% 28%,#123c39,#09221f 65%);border:1px solid #1d5c51}
.rating-disc strong{font-size:1.10rem;color:#d9fff4}.rating-disc span{font-size:.48rem;color:#6f9d91;letter-spacing:.09em}
.leader-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:15px}.ls{background:#0a2028;border:1px solid #173b45;border-radius:8px;padding:8px}.ls span{display:block;font-size:.49rem;color:#58737a;text-transform:uppercase;letter-spacing:.08em}.ls b{display:block;font-size:.77rem;color:#e1ecea;margin-top:3px}.ls b.up{color:#13e0b4}
.gain-pills{display:flex;gap:5px;flex-wrap:wrap;margin-top:10px}.gain-pill{font-size:.56rem;padding:4px 6px;border-radius:6px;color:#657e85;background:#0b2028;border:1px solid #173840}.gain-pill.up{color:#13e0b4;background:rgba(19,224,180,.045);border-color:rgba(19,224,180,.22)}
.comp-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:13px}.comp-card{background:#07161d;border:1px solid #173843;border-radius:11px;padding:14px}.comp-title{font-size:.72rem;color:#e8f0ef;font-weight:800}.comp-big{font-size:1.7rem;color:#13e0b4;font-weight:930;letter-spacing:-.05em;margin-top:10px}.comp-sub{font-size:.59rem;color:#607a80;margin-top:2px}
.standing-wrap{background:#061219;border:1px solid #173843;border-radius:12px;overflow:hidden}.standing-head,.standing-row{display:grid;grid-template-columns:46px 1fr 1.3fr 80px 84px 90px 72px 1.55fr;gap:10px;align-items:center}
.standing-head{padding:10px 13px;background:#091a22;border-bottom:1px solid #173843;font-size:.52rem;color:#60777d;text-transform:uppercase;letter-spacing:.09em;font-weight:900}
.standing-row{padding:10px 13px;border-bottom:1px solid #102c34;min-height:57px}.standing-row:last-child{border-bottom:0}
.s-rank{width:28px;height:28px;border-radius:8px;background:#0d242c;color:#aab9bc;display:flex;align-items:center;justify-content:center;font-size:.67rem;font-weight:850}.s-rank.top{background:linear-gradient(145deg,#0c6a55,#0a463a);color:#eafff8;border:1px solid #12c89f}
.s-owner{font-size:.69rem;color:#dfe9e8;font-weight:800}.s-player{font-size:.70rem;color:#e3eceb;font-weight:730}.s-club{font-size:.55rem;color:#5e777d;margin-top:2px}.s-num{font-size:.69rem;color:#cbd8d8;font-weight:750}.s-up{font-size:.69rem;color:#13e0b4;font-weight:900}
.s-rating{display:inline-flex;align-items:center;gap:5px;font-size:.68rem;color:#eef6f4;font-weight:850}.rating-dot{width:7px;height:7px;border-radius:50%;background:#13e0b4}.s-apps{font-size:.68rem;color:#9db0b3}.s-gains{display:flex;gap:4px;flex-wrap:wrap}.s-gain{font-size:.52rem;color:#657d83;background:#0a2028;border:1px solid #173841;border-radius:5px;padding:3px 5px}.s-gain.up{color:#13e0b4;border-color:rgba(19,224,180,.22);background:rgba(19,224,180,.04)}
.development-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.dev-card{background:#07161d;border:1px solid #173843;border-radius:11px;padding:13px}.dev-player{font-size:.76rem;color:#edf5f4;font-weight:820}.dev-owner{font-size:.57rem;color:#607980;margin-top:2px}.dev-gain{font-size:1.35rem;color:#13e0b4;font-weight:930;margin-top:10px}.dev-sub{font-size:.56rem;color:#637c82;margin-top:2px}
@media(max-width:1000px){.leader-grid{grid-template-columns:1fr}.standing-head,.standing-row{grid-template-columns:40px 1fr 1.2fr 70px 80px 70px}.standing-head>*:nth-child(7),.standing-head>*:nth-child(8),.standing-row>*:nth-child(7),.standing-row>*:nth-child(8){display:none}}
</style>
''', unsafe_allow_html=True)


st.markdown(r"""
<style>
/* ===== v12 official MFL player portraits ===== */
.leader-card{padding:0!important;min-height:265px!important}
.leader-photo-zone{position:relative;height:142px;overflow:hidden;background:
 radial-gradient(circle at 70% 35%,rgba(19,224,180,.18),transparent 45%),
 linear-gradient(145deg,#0b252d,#07151b)}
.second .leader-photo-zone{background:radial-gradient(circle at 70% 35%,rgba(36,169,255,.18),transparent 45%),linear-gradient(145deg,#0a2231,#07151b)}
.third .leader-photo-zone{background:radial-gradient(circle at 70% 35%,rgba(160,101,255,.18),transparent 45%),linear-gradient(145deg,#1a1130,#07151b)}
.leader-photo-zone:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,12,16,.88) 0%,rgba(5,12,16,.42) 42%,rgba(5,12,16,.08) 75%,rgba(5,12,16,.20) 100%)}
.leader-photo{position:absolute;right:-4px;bottom:-12px;height:170px;width:170px;object-fit:contain;z-index:1;filter:drop-shadow(0 12px 18px rgba(0,0,0,.42))}
.leader-photo-copy{position:absolute;left:17px;top:16px;z-index:3;max-width:58%}
.leader-photo-rank{font-size:.54rem;letter-spacing:.14em;font-weight:900;color:#13e0b4}
.second .leader-photo-rank{color:#24a9ff}.third .leader-photo-rank{color:#a065ff}
.leader-photo-name{font-size:1.33rem;color:#f5faf9;font-weight:930;line-height:1.02;letter-spacing:-.045em;margin-top:8px}
.leader-photo-owner{font-size:.62rem;color:#82969b;margin-top:5px}
.leader-body{padding:14px 16px 16px}
.leader-body-top{display:flex;align-items:flex-end;justify-content:space-between;gap:10px}
.leader-ovr-block .leader-ovr-num{font-size:2rem}
.photo-source{font-size:.48rem;color:#4f6a70;letter-spacing:.07em;margin-top:8px}
@media(max-width:1000px){
  .leader-photo{height:185px;width:185px;right:12px}
  .leader-photo-copy{max-width:52%}
}
</style>
""", unsafe_allow_html=True)

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


def valid_wallet(v):
    v=(v or "").strip()
    return len(v)>=10 and v.lower().startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in v[2:])

DEFAULT_WALLET="0x65cc0e72dd71ad80"
if "wallet" not in st.session_state: st.session_state.wallet=DEFAULT_WALLET

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("""
    <div class="side-poster">
      <div class="poster-crown">♕</div>
      <div class="poster-mfl">MFL</div>
      <div class="poster-sub">MANAGEMENT HUB</div>
      <div class="poster-swipe"></div>
    </div>
    """,unsafe_allow_html=True)

    page=st.radio(
        "Navigation",
        ["Home","Grower or Shower","Agency Development","Club Development"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="wallet-area"><div class="wallet-label">ACTIVE WALLET</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="wallet-chip">{esc(st.session_state.wallet)}</div>',unsafe_allow_html=True)
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
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown("""<div class="season-box">
      <div class="season-top"><span>Season 17</span><span>⌄</span></div>
      <div class="connected"><i></i><span>Connected</span></div>
    </div>
    <div class="build">MFL PORTRAITS · v12</div>""",unsafe_allow_html=True)

wallet=st.session_state.wallet

# ---------------- HOME ----------------
if page=="Home":
    try:
        c=agency.db();agency.init(c);agency.ensure_v2(c)
        players=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=?",(wallet.lower(),)).fetchone()[0]
        improved=c.execute("SELECT COUNT(*) FROM ownership_v65 WHERE wallet=? AND current_ovr>start_ovr",(wallet.lower(),)).fetchone()[0]
        c.close()
    except Exception:
        players=0
        improved=0

    try:
        mine=club.owned_clubs(wallet)
    except Exception:
        mine=[]

    cached=club.cached(wallet)
    good=cached[cached["error"].isna()] if (not cached.empty and "error" in cached.columns) else cached
    total_ovr=float(good["ovr_gain"].fillna(0).sum()) if not good.empty else 0
    total_attr=float(good["attr_gain"].fillna(0).sum()) if not good.empty else 0
    total_start=float(good["start_ovr"].fillna(0).sum()) if not good.empty else 0
    total_current=float(good["current_ovr"].fillna(0).sum()) if not good.empty else 0

    clubs_rank=pd.DataFrame()
    top_players=pd.DataFrame()
    if not good.empty:
        clubs_rank=(good.groupby("club").agg(ovr=("ovr_gain","sum"),attrs=("attr_gain","sum"),players=("player_id","count"))
                    .reset_index().sort_values(["ovr","attrs"],ascending=False).head(5))
        top_players=good.sort_values(["attr_gain","ovr_gain"],ascending=False).head(5)

    st.markdown(f"""
      <div class="banner">
        <div class="banner-row">
          <div>
            <div class="brand-word">MFL <span>MANAGEMENT HUB</span></div>
            <div class="brand-stroke"></div>
            <div class="brand-tag">TRACK. ANALYSE. DEVELOP. ALL IN ONE PLACE.</div>
          </div>
          <div class="season-badge">Season 17⌄</div>
        </div>
        <div class="banner-note">SAME GAME.<br><b>BIGGER INSIGHTS.</b></div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">♢</div><div><div class="stat-num">{len(mine) if mine else "—"}</div><div class="stat-lab">Owned Clubs</div></div><div class="stat-trend">LIVE</div>
        </div>
        <div class="stat-card cyan">
          <div class="stat-icon">👥</div><div><div class="stat-num">{players or "—"}</div><div class="stat-lab">Players Tracked</div></div><div class="stat-trend">LIVE</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⇈</div><div><div class="stat-num">+{total_ovr:g}</div><div class="stat-lab">Total OVR Gained</div></div><div class="stat-trend">S17</div>
        </div>
        <div class="stat-card violet">
          <div class="stat-icon">▥</div><div><div class="stat-num">+{total_attr:g}</div><div class="stat-lab">Total Attributes</div></div><div class="stat-trend">S17</div>
        </div>
      </div>

      <div class="feature-grid">
        <div class="feature-card grower"><div class="feature-bg"></div><div class="feature-art">🏆</div>
          <div class="feature-copy"><div class="feature-title">Grower or Shower</div><div class="feature-sub">Competition tracking and leaderboards</div></div><div class="feature-go">›</div>
        </div>
        <div class="feature-card agency"><div class="feature-bg"></div><div class="feature-art">♟♟♟</div>
          <div class="feature-copy"><div class="feature-title">Agency Development</div><div class="feature-sub">Track all your players and progress</div></div><div class="feature-go">›</div>
        </div>
        <div class="feature-card club"><div class="feature-bg"></div><div class="feature-art">⚽</div>
          <div class="feature-copy"><div class="feature-title">Club Development</div><div class="feature-sub">Compare club progression</div></div><div class="feature-go">›</div>
        </div>
      </div>
    """,unsafe_allow_html=True)

    if total_start>0:
        lo=min(total_start,total_current); hi=max(total_start,total_current); rng=max(hi-lo,1)
        y1=140-(total_start-lo)/rng*95; y2=140-(total_current-lo)/rng*95
        chart_svg=f"""<svg class="chart-svg" viewBox="0 0 500 150" preserveAspectRatio="none">
          <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#13e0b4" stop-opacity=".26"/><stop offset="1" stop-color="#13e0b4" stop-opacity="0"/></linearGradient></defs>
          <path d="M18,{y1:.1f} L482,{y2:.1f} L482,148 L18,148 Z" fill="url(#area)"/>
          <path d="M18,{y1:.1f} L482,{y2:.1f}" fill="none" stroke="#13e0b4" stroke-width="3"/>
          <circle cx="18" cy="{y1:.1f}" r="5" fill="#13e0b4"/><circle cx="482" cy="{y2:.1f}" r="5" fill="#13e0b4"/>
        </svg>"""
        chart_note=f"{total_start:g} → {total_current:g}"
    else:
        chart_svg='<div style="color:#5c747a;font-size:.68rem;padding:65px 20px;text-align:center">Sync Club Development to populate Season 17 progression.</div>'
        chart_note="Waiting for club data"

    club_rows=""
    if not clubs_rank.empty:
        for i,r in enumerate(clubs_rank.to_dict("records"),1):
            club_rows+=f'<div class="list-row"><div class="list-rank">{i}</div><div><div class="list-main">{esc(r["club"])}</div><div class="list-sub">{int(r["players"])} players · +{r["attrs"]:g} attrs</div></div><div class="list-value">+{r["ovr"]:g}</div></div>'
    else:
        club_rows='<div style="color:#5c747a;font-size:.66rem;padding:35px 4px;text-align:center">No club data loaded yet.</div>'

    player_rows=""
    if not top_players.empty:
        for i,(_,r) in enumerate(top_players.iterrows(),1):
            player_rows+=f'<div class="list-row"><div class="list-rank">{i}</div><div><div class="list-main">{esc(r["player"])}</div><div class="list-sub">{esc(r["club"])}</div></div><div class="list-value">+{float(r["attr_gain"] or 0):g}</div></div>'
    else:
        player_rows='<div style="color:#5c747a;font-size:.66rem;padding:35px 4px;text-align:center">No player development loaded yet.</div>'

    st.markdown(f"""
      <div class="dash-grid">
        <div class="card">
          <div class="card-head"><div class="card-title">♢ &nbsp; OVR Progression (Season 17)</div><div class="card-meta">{esc(chart_note)}</div></div>
          <div class="chart-box"><div class="chart-grid"></div>{chart_svg}<div class="chart-labels"><span>S17 Start</span><span>Current</span></div></div>
        </div>
        <div class="card"><div class="card-head"><div class="card-title">♢ &nbsp; Top 5 Clubs (OVR Gained)</div><div class="card-meta">S17</div></div>{club_rows}</div>
        <div class="card"><div class="card-head"><div class="card-title">▥ &nbsp; Top 5 Players (Attributes Gained)</div><div class="card-meta">S17</div></div>{player_rows}</div>
      </div>
    """,unsafe_allow_html=True)

    activity=""
    if not good.empty and "last_progression" in good.columns:
        act=good.copy()
        act["_dt"]=pd.to_datetime(act["last_progression"],utc=True,errors="coerce")
        act=act.sort_values("_dt",ascending=False).head(5)
        for _,r in act.iterrows():
            gains=[]
            if float(r.get("ovr_gain") or 0)>0: gains.append(f'+{float(r["ovr_gain"]):g} OVR')
            if float(r.get("attr_gain") or 0)>0: gains.append(f'+{float(r["attr_gain"]):g} Attributes')
            gaintext=" · ".join(gains) if gains else "progression checked"
            date_txt=r["_dt"].strftime("%d %b") if pd.notna(r["_dt"]) else ""
            activity+=f'<div class="activity-row"><div class="activity-dot"></div><div class="activity-main">{esc(r["player"])} &nbsp; <b>{esc(gaintext)}</b></div><div class="activity-time">{esc(date_txt)}</div></div>'
    if not activity:
        activity='<div style="color:#5c747a;font-size:.66rem;padding:35px 4px;text-align:center">Recent progression will appear after Club Development is synced.</div>'

    st.markdown(f"""
      <div class="bottom-grid">
        <div class="card"><div class="card-head"><div class="card-title">⚡ &nbsp; Recent Activity</div><div class="card-meta">LATEST PROGRESSION</div></div>{activity}</div>
        <div class="card">
          <div class="card-head"><div class="card-title">◎ &nbsp; Quick Actions</div><div class="card-meta">WORKSPACES</div></div>
          <div class="actions">
            <div class="action">🏆 &nbsp; Grower or Shower <span>→</span></div>
            <div class="action">👥 &nbsp; Agency Development <span>→</span></div>
            <div class="action">▥ &nbsp; Club Development <span>→</span></div>
            <div class="action">⟳ &nbsp; Sync Latest Data <span>→</span></div>
          </div>
        </div>
      </div>
    """,unsafe_allow_html=True)

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
        st.markdown('<div class="empty"><b>No competition data yet</b>Refresh the competition once to build the standings.</div>',unsafe_allow_html=True)
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

