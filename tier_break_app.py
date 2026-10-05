import pandas as pd
import streamlit as st

import tier_break_backend as tierbreak

st.set_page_config(page_title="MFL Transfer Tier Break Scanner", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1550px;padding-top:2rem}
.hero{padding:24px 28px;border:1px solid rgba(128,128,128,.25);border-radius:18px;margin-bottom:18px}
.kicker{font-size:.78rem;letter-spacing:.18em;font-weight:700;opacity:.65}
.title{font-size:2.35rem;font-weight:800;margin:.25rem 0 .4rem}
.copy{font-size:1.02rem;opacity:.82;max-width:980px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="kicker">NOOKS · TRANSFER MARKET SCOUTING</div>
  <div class="title">Tier Break Bargain Finder</div>
  <div class="copy">
    Scan players currently listed for transfer and rank the ones closest to a +1 OVR.
    Players whose next +1 also crosses a rarity boundary are highlighted as tier-break opportunities.
  </div>
</div>
""", unsafe_allow_html=True)

all_positions=["GK","RB","LB","CB","RWB","LWB","CDM","CM","CAM","RM","LM","RW","LW","CF","ST"]

with st.expander("Filters", expanded=True):
    c1,c2,c3,c4=st.columns(4)
    with c1:
        age_range=st.slider("Age",16,42,(16,28))
    with c2:
        ovr_range=st.slider("OVR",45,94,(60,84))
    with c3:
        price_min=st.number_input("Min price",min_value=0.0,value=0.0,step=1.0)
    with c4:
        price_max=st.number_input("Max price",min_value=0.0,value=100.0,step=5.0)

    selected_positions=st.multiselect("Positions",all_positions,default=[])

scan=st.button("Scan live transfer listings",type="primary")

if "market_rows" not in st.session_state:
    st.session_state.market_rows=[]
    st.session_state.market_key=None

key=(tuple(age_range),tuple(ovr_range),float(price_min),float(price_max),tuple(selected_positions))

if scan:
    try:
        with st.spinner("Scanning MFL transfer listings…"):
            rows=tierbreak.scan_transfer_market(
                age_min=int(age_range[0]),
                age_max=int(age_range[1]),
                overall_min=int(ovr_range[0]),
                overall_max=int(ovr_range[1]),
                price_min=float(price_min),
                price_max=float(price_max) if price_max > 0 else None,
                positions=selected_positions or None,
                max_pages=24,
            )
        st.session_state.market_rows=rows
        st.session_state.market_key=key
    except Exception as e:
        st.error("Could not load MFL transfer listings.")
        with st.expander("Technical detail"):
            st.code(str(e))

rows=st.session_state.market_rows if st.session_state.market_key==key else []

if not rows:
    st.info("Choose your filters and click **Scan live transfer listings**.")
else:
    tier_breaks=sum(1 for r in rows if r["tier_break"])
    tier_one=sum(1 for r in rows if r["tier_break"] and r["one_point_stats"])
    plus_one=sum(1 for r in rows if r["one_point_stats"])
    closest=min((r["gap"] for r in rows), default=0)

    m1,m2,m3,m4=st.columns(4)
    m1.metric("Listings scanned",f"{len(rows):,}")
    m2.metric("Tier-break listings",f"{tier_breaks:,}")
    m3.metric("Tier break +1 away",f"{tier_one:,}")
    m4.metric("Any +1 OVR close",f"{plus_one:,}")

    st.subheader("Best market opportunities")

    f1,f2,f3=st.columns([1.4,1.4,1.4])
    with f1:
        view=st.selectbox(
            "Show",
            ["Best opportunities","Tier breaks only","1-stat-gain only","All listings"],
            index=0,
        )
    with f2:
        max_rows=st.selectbox("Rows", [25,50,100,250,500], index=2)
    with f3:
        sort_mode=st.selectbox(
            "Rank by",
            ["Opportunity","Closest to +1","Cheapest","Youngest"],
            index=0,
        )

    filtered=list(rows)
    if view=="Tier breaks only":
        filtered=[r for r in filtered if r["tier_break"]]
    elif view=="1-stat-gain only":
        filtered=[r for r in filtered if r["one_point_stats"]]
    elif view=="Best opportunities":
        filtered=[r for r in filtered if r["tier_break"] or r["one_point_stats"] or (r["min_points"] is not None and r["min_points"]<=2)]

    if sort_mode=="Closest to +1":
        filtered.sort(key=lambda r:(r["gap"],999 if r["min_points"] is None else r["min_points"],r["price"] if r["price"] is not None else 1e18))
    elif sort_mode=="Cheapest":
        filtered.sort(key=lambda r:(r["price"] if r["price"] is not None else 1e18,r["gap"]))
    elif sort_mode=="Youngest":
        filtered.sort(key=lambda r:(r["age"] if r["age"] is not None else 999,r["gap"]))
    else:
        filtered.sort(key=lambda r:(
            0 if r["tier_break"] and r["one_point_stats"] else
            1 if r["tier_break"] else
            2 if r["one_point_stats"] else 3,
            999 if r["min_points"] is None else r["min_points"],
            r["gap"],
            r["price"] if r["price"] is not None else 1e18
        ))

    display=[]
    for r in filtered[:int(max_rows)]:
        display.append({
            "Signal":r["opportunity"] or r["closeness"],
            "Player":r["name"],
            "Age":r["age"],
            "Pos":r["position"],
            "OVR":r["overall"],
            "Next":r["next_ovr"],
            "Tier break":"YES" if r["tier_break"] else "",
            "Raw OVR":r["raw_ovr"],
            "Gap to +1":r["gap"],
            "Min gains":r["min_points"],
            "Best route":r["best_route"],
            "1-point break":r["one_point_stats"] or "—",
            "Price":r["price"],
            "PAC":r["PAC"],
            "SHO":r["SHO"],
            "PAS":r["PAS"],
            "DRI":r["DRI"],
            "DEF":r["DEF"],
            "PHY":r["PHY"],
            "Club":r["club"],
            "MFL":r["mfl_url"],
        })

    df=pd.DataFrame(display)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Raw OVR":st.column_config.NumberColumn(format="%.3f"),
            "Gap to +1":st.column_config.NumberColumn(format="%.3f"),
            "Price":st.column_config.NumberColumn(format="%.2f"),
            "MFL":st.column_config.LinkColumn("MFL",display_text="Open"),
        }
    )

    st.caption(
        "‘+1 soon’ here means mathematically close to the next displayed OVR based on current attributes. "
        "It does not yet predict when training/development will happen. A tier break is flagged when the next OVR crosses 55, 65, 75, 85 or 95."
    )
