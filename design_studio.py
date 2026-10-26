"""Preview themed Hub collections using local, self-contained assets."""
import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).with_name("design-concepts")


@st.cache_data
def embedded_concept(slug):
    allowed = {c["slug"] for c in json.loads((ROOT / "concepts.json").read_text())}
    if slug not in allowed:
        raise ValueError("Unknown design concept")
    source = (ROOT / f"{slug}.html").read_text()
    for font in (ROOT / "assets").glob("*.ttf"):
        encoded = base64.b64encode(font.read_bytes()).decode("ascii")
        source = source.replace(f"url(assets/{font.name})", f"url(data:font/ttf;base64,{encoded})")
    source = source.replace('<a href="index.html">← ALL SIX CONCEPTS</a>',
                            '<span>Choose another concept above this preview.</span>')
    source = source.replace('<a href="wild-index.html">ALL TEN NEW CONCEPTS ↗</a>',
                            '<span>Choose another concept above this preview.</span>')
    source = source.replace('<a href="fresh-index.html">ALL FIFTEEN NEW DESIGNS ↗</a>', '<span>Choose another concept above this preview.</span>')
    return source


def render():
    st.title("Design Studio")
    st.write("Fifteen fresh directions with different layouts, fonts and colours. Try their navigation, progression periods, squad previews and player filters.")
    collection = st.radio("Theme collection", ["Fifteen new · Fresh directions", "Ten new · Wild collection", "Original six"], horizontal=True)
    all_concepts = json.loads((ROOT / "concepts.json").read_text())
    group={"Fifteen new · Fresh directions":"Fresh fifteen","Ten new · Wild collection":"Wild collection","Original six":None}[collection]
    concepts = [c for c in all_concepts if c.get("collection")==group]
    selected = st.selectbox("Design concept", range(len(concepts)),
                            format_func=lambda i: f'{concepts[i].get("collection_number",concepts[i]["number"])} · {concepts[i]["title"]} — {concepts[i]["style"]}',
                            key="design_choice_"+str(group or "original"))
    concept = concepts[selected]
    st.subheader(concept["title"])
    st.write(concept["description"])
    st.caption("Design previews use illustrative data. Your agency data and squad assignments are unaffected.")
    if concept["slug"] == "01-teletext":
        st.info("Try the green 302 SQUADS button, or type 302 in the PAGE box and press Enter. Type 100 to return home.")
    components.html(embedded_concept(concept["slug"]), height=1120, scrolling=True)
    with st.expander("Compare this collection at a glance"):
        for row in range(0, len(concepts), 2):
            for col, item in zip(st.columns(2), concepts[row:row+2]):
                with col:
                    st.image(str(ROOT / "previews" / f'{item["slug"]}.png'), caption=f'{item.get("collection_number",item["number"])} · {item["title"]}')
    pdf = ROOT / ({"Fresh fifteen":"MFL_Fresh_15_Lookbook.pdf","Wild collection":"MFL_Wild_Design_Lookbook.pdf",None:"MFL_Design_Lookbook.pdf"}[group])
    if pdf.exists():
        st.download_button("Download this collection’s lookbook", pdf.read_bytes(),
                           file_name=pdf.name, mime="application/pdf")
