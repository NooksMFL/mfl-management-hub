"""Compact roster preview using saved agency data, with escaped HTML."""
from html import escape
from squad_cards import age_label
from tactics_engine import numeric, positions
from mfl_text import page_link


def sort_players(players):
    def key(player):
        rating=numeric(player.get('overall',player.get('current_ovr')))
        return (-(rating if rating is not None else -1),str(player.get('player_name') or player.get('player') or ''))
    return sorted(players,key=key)


def roster_html(players,wallet,total=None):
    count=len(players) if total is None else total
    cards=[]
    for player in players[:12]:
        pid=int(player['player_id'])
        name=str(player.get('player_name') or player.get('player') or f'Player {pid}')
        listed=positions(player.get('position'));position=listed[0] if listed else '—'
        kind='goalkeeper' if position=='GK' else 'defender' if position in {'LB','RB','CB','LWB','RWB','SW'} else 'forward' if position in {'ST','CF','LW','RW','SS'} else 'midfielder'
        value=numeric(player.get('overall',player.get('current_ovr')))
        rating=f'{value:g}' if value is not None else '—'
        initials=''.join(part[0] for part in name.split()[:2])
        cards.append(f'<article class="ops-player-card"><span class="ops-face"><span>{escape(initials)}</span><span class="ops-portrait" style="background-image:url(https://d13e14gtps4iwl.cloudfront.net/players/v2/{pid}/photo.webp)"></span></span>'
            f'<div class="ops-player-info"><div class="ops-player-name">{escape(name)}</div><div class="ops-player-meta"><span class="ops-position {kind}">{escape(position)}</span><span class="ops-ovr">{rating}</span><span class="ops-age">{age_label(player.get("age"))}y</span></div></div></article>')
    link=escape(page_link('Agency Development',wallet),quote=True)
    remaining=max(0,count-len(cards))
    return f'<section class="ops-roster-panel"><div class="ops-panel-head"><div><strong>Your players</strong><p>Showing {len(cards)} of {count} matching players from your saved roster</p></div><a href="{link}" target="_self">My agency ↗</a></div><div class="ops-player-grid">'+''.join(cards)+f'</div><a class="ops-panel-footer" href="{link}" target="_self">'+(f'{remaining} more in My agency' if remaining else 'Open My agency')+' ↗</a></section>'
