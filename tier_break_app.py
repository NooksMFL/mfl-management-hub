import pandas as pd
import streamlit as st

import tier_break_backend as tierbreak

st.set_page_config(page_title="MFL Tier Break Scanner", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1500px;padding-top:2rem}
.hero{padding:24px 28px;border:1px solid rgba(128,128,128,.25);border-radius:18px;margin-bottom:18px}
.kicker{font-size:.78rem;letter-spacing:.18em;font-weight:700;opacity:.65}
.title{font-size:2.35rem;font-weight:800;margin:.25rem 0 .4rem}
.copy{font-size:1.02rem;opacity:.82;max-width:900px}
.metric-card{padding:18px;border:1px solid rgba(128,128,128,.25);border-radius:14px}
.small{font-size:.85rem;opacity:.7}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="kicker">NOOKS · MFL SCOUTING</div>
  <div class="title">Tier Break Scanner</div>
  <div class="copy">Find players sitting closest to the next rarity boundary. The scanner uses MFL's positional OVR weightings to work out the exact raw score, the gap to the next tier, and the smallest useful attribute gains.</div>
</div>
""", unsafe_allow_html=True)

RARITY_BREAKS = {
    54: (55, "Common → Uncommon"),
    64: (65, "Uncommon threshold"),
    74: (75, "Uncommon → Rare"),
    84: (85, "Rare → Ultra Rare"),
    94: (95, "Ultra Rare → Legendary"),
}

all_positions=["GK","RB","LB","CB","RWB","LWB","CDM","CM","CAM","RM","LM","RW","LW","CF","ST"]

f1,f2,f3,f4=st.columns([1,1,1.6,1.6])
with f1:
    current_ovr=st.number_input("Current OVR",min_value=45,max_value=94,value=74,step=1)
with f2:
    target_default=RARITY_BREAKS.get(int(current_ovr),(int(current_ovr)+1,""))[0]
    target_ovr=st.number_input("Target OVR",min_value=int(current_ovr)+1,max_value=95,value=int(target_default),step=1)
with f3:
    age_range=st.slider("Age",16,42,(16,28))
with f4:
    selected_positions=st.multiselect("Positions",all_positions,default=[])

label=RARITY_BREAKS.get(int(current_ovr))
if label and label[0] == int(target_ovr):
    st.caption(f"Preset: {label[1]}")

scan=st.button("Scan players",type="primary",use_container_width=False)

if "tier_rows" not in st.session_state:
    st.session_state.tier_rows=[]
    st.session_state.tier_key=None

key=(int(current_ovr),int(target_ovr),tuple(age_range),tuple(selected_positions))

if scan:
    try:
        with st.spinner(f"Scanning {int(current_ovr)} OVR players…"):
            rows=tierbreak.scan_tier_break(
                current_ovr=int(current_ovr),
                target_ovr=int(target_ovr),
                age_min=int(age_range[0]),
                age_max=int(age_range[1]),
                positions=selected_positions or None,
                max_pages=15,
            )
        st.session_state.tier_rows=rows
        st.session_state.tier_key=key
    except Exception as e:
        st.error("The scanner could not load player data.")
        with st.expander("Technical detail"):
            st.code(str(e))

rows=st.session_state.tier_rows if st.session_state.tier_key==key else []

if not rows:
    st.info("Start with 74 → 75 and click **Scan players**.")
else:
    one_gain=sum(1 for r in rows if r.get("one_point_stats"))
    two_or_less=sum(1 for r in rows if (r.get("min_points") or 999)<=2)
    closest=min((r.get("gap",999) for r in rows),default=0)

    m1,m2,m3,m4=st.columns(4)
    m1.metric("Players scanned",f"{len(rows):,}")
    m2.metric("1 gain from target",f"{one_gain:,}")
    m3.metric("≤2 gains away",f"{two_or_less:,}")
    m4.metric("Closest raw gap",f"{closest:.3f}")

    st.subheader("Closest tier-break candidates")
    st.caption("Lowest development requirement first. ‘1-point break’ means a single +1 to any listed stat immediately crosses the target OVR threshold.")

    display=[]
    for r in rows:
        display.append({
            "Player":r["name"],
            "Age":r["age"],
            "Pos":r["position"],
            "OVR":r["overall"],
            "Raw OVR":r["raw_ovr"],
            f"Gap to {int(target_ovr)}":r["gap"],
            "Min gains":r["min_points"],
            "Best route":r["best_route"],
            "1-point break":r["one_point_stats"] or "—",
            "PAC":r["PAC"],
            "SHO":r["SHO"],
            "PAS":r["PAS"],
            "DRI":r["DRI"],
            "DEF":r["DEF"],
            "PHY":r["PHY"],
            "Club":r["club"],
            "Owner":r["owner"],
            "MFL":r["mfl_url"],
        })

    df=pd.DataFrame(display)

    only_one=st.toggle("Show only 1-gain candidates",value=False)
    if only_one:
        df=df[df["1-point break"]!="—"]

    sort_mode=st.selectbox(
        "Rank by",
        ["Minimum gains, then raw gap","Raw gap only","Youngest first"],
        index=0,
    )
    if sort_mode=="Raw gap only":
        df=df.sort_values([f"Gap to {int(target_ovr)}","Age"],ascending=[True,True])
    elif sort_mode=="Youngest first":
        df=df.sort_values(["Age","Min gains",f"Gap to {int(target_ovr)}"],ascending=[True,True,True])

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Raw OVR":st.column_config.NumberColumn(format="%.3f"),
            f"Gap to {int(target_ovr)}":st.column_config.NumberColumn(format="%.3f"),
            "MFL":st.column_config.LinkColumn("MFL",display_text="Open"),
        }
    )

    st.divider()
    st.markdown("**How it works:** MFL calculates outfield OVR using position-specific attribute weights and rounds the result. For a displayed 75, the raw weighted score needs to reach **74.50**.")
