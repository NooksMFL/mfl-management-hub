"""One retired-player rule for displays, using the latest shared roster first."""
import pandas as pd
from squad_builder import has_current_club
import wallet_cache_backend as shared


def filter_frame(frame,wallet,show_retired=False,update_clubs=False):
    if frame.empty:return frame.copy()
    result=frame.copy()
    latest={int(r['player_id']):r.get('club') for r in shared.roster_rows(wallet)} if wallet else {}
    def current(row):
        try:pid=int(row['player_id'])
        except (KeyError,ValueError,TypeError):return row.get('club')
        # None is authoritative: never fall back to a stale historic club.
        return latest[pid] if pid in latest else row.get('club')
    clubs=result.apply(current,axis=1)
    if update_clubs:result['club']=clubs
    return result if show_retired else result[clubs.map(has_current_club)].copy()
