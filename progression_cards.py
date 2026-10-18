"""High-resolution collectible cards backed only by season progression records."""
import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import streamlit as st

ATTRIBUTES = (("pac", "PAC"), ("dri", "DRI"), ("sho", "SHO"), ("defn", "DEF"), ("pas", "PAS"), ("phy", "PHY"))


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def delta(value):
    value = number(value)
    return "—" if value is None else f"{value:+g}"


@st.cache_data(ttl=3600, show_spinner=False)
def portrait(player_id):
    try:
        response = requests.get(f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(player_id)}/photo.webp", timeout=8)
        response.raise_for_status()
        return response.content
    except requests.RequestException:
        return None


def create_card(player, photo=None, season="Season 17"):
    """Render a 3x-resolution shield. Missing measurements remain unknown."""
    im = Image.new("RGBA", (720, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fonts = Path(__file__).with_name("design-concepts") / "assets"
    def font(size, bold=False):
        return ImageFont.truetype(str(fonts / ("sans-bold.ttf" if bold else "sans.ttf")), size)
    def text(x, y, value, size, fill="#eff5ff", bold=False, anchor=None):
        d.text((x,y), str(value), font=font(size,bold), fill=fill, anchor=anchor)
    shield = [(25,180),(165,180),(190,105),(530,105),(555,180),(695,180),(695,925),(360,1048),(25,925)]
    d.polygon(shield, fill="#101d35", outline="#45b9ff", width=5)
    inner = [(39,194),(176,194),(201,119),(519,119),(544,194),(681,194),(681,915),(360,1032),(39,915)]
    d.line(inner+[inner[0]],fill="#4d5de0",width=5)
    for x in range(210,670,22):
        for y in range(210,900,22):
            d.ellipse((x,y,x+4,y+4),fill="#234474")
    if photo:
        try:
            face = Image.open(io.BytesIO(photo)).convert("RGBA")
            face = ImageOps.contain(face,(530,550),Image.Resampling.LANCZOS)
            im.alpha_composite(face, (int(385-face.width/2), 40+550-face.height))
        except (OSError, ValueError):
            photo = None
    if not photo:
        d.ellipse((280,245,450,415),fill="#344967")
        d.rounded_rectangle((215,400,515,590),radius=75,fill="#344967")
        text(365,470,"MFL",50,"#90a8ce",True,"mm")
    # A deliberate dark name/stats plate preserves legibility over every portrait.
    d.rounded_rectangle((58,580,662,910),radius=8,fill="#0c172d")
    text(65,235,delta(player.get("ovr_gain")),64,"#48baff",True)
    text(65,315,"OVR GAIN",20,bold=True)
    text(65,370,player.get("position") or "—",28,bold=True)
    text(65,429,"AGE",17)
    age=number(player.get("age"));text(65,453,f"{age:g}" if age is not None else "—",29,bold=True)
    name=str(player.get("player") or "MFL PLAYER").upper()
    size=37
    while d.textlength(name,font=font(size,True))>570 and size>17: size-=1
    text(360,625,name,size,"#59beff",True,"mm")
    text(360,669,f"{season.upper()} · ATTRIBUTE PROGRESSION",19,"#adbcda",True,"mm")
    for i,(key,label) in enumerate(ATTRIBUTES):
        x=105 if i%2==0 else 395;y=717+(i//2)*58
        val=number(player.get(key));colour="#77efcb" if val is not None and val>0 else "#ffadad" if val is not None and val<0 else "#eff5ff"
        text(x,y,delta(val),35,colour,True);text(x+98,y+6,label,26)
    text(360,945,"MFL MANAGEMENT HUB",22,"#59beff",True,"mm")
    text(360,978,"SEASON DEVELOPMENT CARD",15,"#b0bedc",False,"mm")
    out=io.BytesIO();im.save(out,format="PNG");return out.getvalue()


def render(season_players, roster):
    st.subheader("Season progression cards")
    st.caption("A collectible card showing each attribute’s change this season. +0 means unchanged; — means no measurement. Agency ownership gains are not used as season gains.")
    if season_players.empty:
        st.info("Sync Club Development to load season progression records, then create a card here.")
        return
    players=season_players.copy()
    if "error" in players: players=players[players.error.isna()]
    if players.empty:
        st.info("No valid season progression records yet. Refresh Club Development.")
        return
    choices={f'{r.player} · {int(r.player_id)}':int(r.player_id) for _,r in players.sort_values("player").iterrows()}
    chosen=st.selectbox("Player for progression card",list(choices),key="progression_card_player")
    pid=choices[chosen];player=players[players.player_id==pid].iloc[0].to_dict()
    meta=next((r for r in roster if int(r["player_id"])==pid),{})
    player.update(age=meta.get("age"),position=meta.get("position") or meta.get("positions"))
    if isinstance(player["position"],list):player["position"]=" / ".join(str(x) for x in player["position"])
    card=create_card(player,portrait(pid))
    left,right=st.columns([1,1])
    with left:st.image(card,width=360)
    with right:
        st.markdown(f'**{player["player"]}**')
        st.caption(f'Club: {player.get("club") or "Unknown"}')
        st.caption(f'Baseline: {player.get("baseline_at") or "Unknown"} · Latest progression: {player.get("last_progression") or "Unknown"}')
        st.download_button("Download progression card PNG",card,file_name=f"mfl_{pid}_season_progression.png",mime="image/png",key="download_progression_card")
        st.caption("720 × 1080 PNG · transparent background · full-resolution export")
