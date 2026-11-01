"""Read-only squad coverage from completed or checkpointed agency profiles."""
import re
from collections import Counter
from statistics import median

import agency_full_sync as full
import tactics_engine as tactics
import wallet_cache_backend as shared
from squad_builder import has_current_club


def is_active(player):
    return not player.get('is_retired') and has_current_club(player.get('club'))


def snapshot(wallet):
    """Never resume/reset a sync or request the API to produce a report."""
    run=full.state(wallet)
    if run.get('status') in ('paused','running') and run.get('run_id'):
        profiles=full.staged(wallet,run['run_id'])
        ids=run.get('ids')
        if ids is not None:
            rows=[profiles[pid] for pid in ids if pid in profiles]
            return rows,{'checked':len(rows),'total':len(ids),'partial':True}
    rows=shared.roster_rows(wallet)
    return rows,{'checked':len(rows),'total':len(rows),'partial':False}


def club_names(wallet,rows,fcn_only=True):
    names={str(p['club']).strip() for p in rows if is_active(p)}
    if fcn_only:
        return sorted(n for n in names if re.search(r'\bFCN\b',n,re.I))
    owned={str(c['name']).casefold() for c in shared.clubs_rows(wallet)}
    run=full.state(wallet)
    owned.update(str(c['name']).casefold() for c in run.get('clubs') or [])
    return sorted(n for n in names if n.casefold() in owned or re.search(r'\bFCN\b',n,re.I))


def target_rating(players):
    values=[tactics.numeric(p.get('overall')) for p in players]
    return round(median(v for v in values if v is not None)) if any(v is not None for v in values) else 60


def analyse(players,formation='4-3-3',target=65):
    """Allocate starters before cover; never double-count a versatile player.

    Listed secondary positions with no measured rating can provide provisional
    cover, but their strength is explicitly unknown. No OOP ratings are invented.
    """
    unique={int(p['player_id']):p for p in players if is_active(p)}
    players=[unique[k] for k in sorted(unique)]
    starters=[tactics.canonical(role) for role,_,_ in tactics.FORMATIONS[formation]]
    quotas=Counter(starters)
    slots=[(role,False) for role in starters]+[(role,True) for role in starters]
    costs=[]
    for role,cover in slots:
        row=[]
        for p in players:
            value,source=tactics.rating_at(p,role)
            eligible=value is not None or role in tactics.positions(p.get('position'))
            # The priority of one starting slot exceeds the sum of every bench slot.
            benefit=(10000000 if not cover else 100000)+((100000 if not cover else 1000) if value is not None else 0)+(value or 0)*(100 if not cover else 1)
            row.append(-benefit if eligible else 1000000000)
        costs.append(row+[0]*len(slots))
    assigned=tactics.assignment(costs)
    allocation={role:{'starters':[],'cover':[]} for role in quotas}
    for i,j in assigned.items():
        if j>=len(players) or costs[i][j]>=0:continue
        p=players[j];role,cover=slots[i];rating,source=tactics.rating_at(p,role)
        allocation[role]['cover' if cover else 'starters'].append({**p,'rating':rating,'rating_source':source})
    report=[]
    for role,needed in quotas.items():
        start=allocation[role]['starters'];bench=allocation[role]['cover']
        missing=needed-len(start);missing_cover=needed-len(bench)
        weak=[p for p in start if p['rating'] is not None and p['rating']<target]
        unknown=[p for p in start if p['rating'] is None]
        weak_cover=[p for p in bench if p['rating'] is not None and p['rating']<max(0,target-5)]
        unknown_cover=[p for p in bench if p['rating'] is None]
        actions=[]
        if missing:actions.append(f'Add {missing} starter'+('s' if missing!=1 else ''))
        if weak:actions.append(f'Upgrade {len(weak)} starter'+('s' if len(weak)!=1 else ''))
        if unknown:actions.append(f'Check {len(unknown)} starting rating'+('s' if len(unknown)!=1 else ''))
        if missing_cover:actions.append(f'Add {missing_cover} cover player'+('s' if missing_cover!=1 else ''))
        if weak_cover:actions.append(f'Improve {len(weak_cover)} cover player'+('s' if len(weak_cover)!=1 else ''))
        if unknown_cover:actions.append(f'Check {len(unknown_cover)} cover rating'+('s' if len(unknown_cover)!=1 else ''))
        priority='Urgent' if missing else 'Strengthen' if weak else 'Check ratings' if unknown else 'Add cover' if missing_cover else 'Improve cover' if weak_cover else 'Check ratings' if unknown_cover else 'Covered'
        def names(rows):
            return ', '.join(f"{p['player_name']} ({p['rating']:g})" if p['rating'] is not None else f"{p['player_name']} (?)" for p in rows) or '—'
        report.append({'Position':role,'Priority':priority,'Starting places':needed,'Starters':len(start),'Cover':len(bench),
                       'Missing players':missing+missing_cover,'Starting players':names(start),'Cover players':names(bench),
                       'Action':'; '.join(actions) or 'Covered at your target rating'})
    order={'Urgent':0,'Strengthen':1,'Add cover':2,'Improve cover':3,'Check ratings':4,'Covered':5}
    report.sort(key=lambda r:(order[r['Priority']],r['Position']))
    return report,allocation
