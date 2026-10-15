"""Visual squad roster with escaped player metadata."""
from html import escape
import math

from squad_builder import QUOTAS


def age_label(value):
    try:
        age = float(value)
        return str(int(age)) if math.isfinite(age) and age > 0 else "—"
    except (TypeError, ValueError):
        return "—"


def roster_html(players):
    sections = []
    for role in QUOTAS:
        members = [p for p in players if p["assigned_role"] == role]
        if not members:
            continue
        cards = []
        for p in members:
            name = str(p.get("player") or f"Player {p['player_id']}")
            initials = "".join(part[0] for part in name.split()[:2])
            portrait = f"https://d13e14gtps4iwl.cloudfront.net/players/v2/{int(p['player_id'])}/photo.webp"
            cards.append(f'<article class="squad-player"><div class="squad-photo"><span>{escape(initials)}</span>'
                f'<span class="squad-face" role="img" aria-label="{escape(name, quote=True)}" style="background-image:url({portrait})"></span></div>'
                f'<div class="squad-player-info"><div class="squad-player-name">{escape(name)}</div>'
                f'<div class="squad-meta"><span class="squad-position">{escape(str(p.get("position") or "—"))}</span>'
                f'<span>Age {age_label(p.get("age"))}</span></div>'
                f'<div class="squad-club">{escape(str(p.get("club") or "—"))}</div></div>'
                f'<div class="squad-rating">{float(p["current_ovr"]):g}<small>OVR</small></div></article>')
        sections.append(f'<div class="squad-role">{role}s <span>{len(members)}</span></div><div class="squad-card-grid">{"".join(cards)}</div>')
    return '<div class="squad-roster">'+"".join(sections)+'</div>'


STYLE = """<style>
.squad-roster{margin:10px 0 24px}.squad-role{color:#8ea9b4;text-transform:uppercase;font-size:.69rem;font-weight:800;letter-spacing:.14em;margin:20px 0 10px}.squad-role span{color:#25deb3;margin-left:9px}.squad-card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}.squad-player{display:flex;align-items:center;gap:12px;position:relative;overflow:hidden;min-height:116px;padding:14px;border:1px solid #1c3a46;border-radius:14px;background:radial-gradient(ellipse at top left,#123c3b80,transparent 75%),linear-gradient(135deg,#0d202a,#09151d);box-shadow:0 5px 18px #0002}.squad-player:hover{border-color:#24bd9c;transform:translateY(-2px);transition:.18s}.squad-photo{width:68px;height:82px;flex-shrink:0;position:relative;background:linear-gradient(145deg,#204f51,#0e2b35);border-radius:11px;overflow:hidden;display:grid;place-items:center}.squad-photo span{font-size:1.3rem;color:#7db8ae;font-weight:800}.squad-photo .squad-face{position:absolute;width:100%;height:100%;background-size:cover;background-position:top center;inset:0}.squad-player-info{flex:1;min-width:0}.squad-player-name{font-size:.94rem;font-weight:800;color:#f0f7f8;line-height:1.3}.squad-meta{display:flex;flex-wrap:wrap;gap:7px;align-items:center;font-size:.7rem;color:#9fb4bf;margin-top:8px}.squad-position{background:#143b3b;color:#5aefcb;border:1px solid #226258;border-radius:4px;padding:2px 5px;font-weight:750}.squad-club{font-size:.69rem;color:#829aa6;margin-top:7px;line-height:1.3}.squad-rating{font-size:1.7rem;line-height:1;font-weight:900;color:#39e9bd;text-align:center}.squad-rating small{display:block;font-size:.5rem;color:#779b9b;letter-spacing:.12em;margin-top:5px}@media(max-width:600px){.squad-card-grid{grid-template-columns:1fr}}
</style>"""
