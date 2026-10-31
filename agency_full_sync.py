"""Verified whole-agency snapshots, staged safely until every player is read."""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

import agency_backend as agency
import wallet_cache_backend as shared
from tactics_engine import payload_ratings


class SyncError(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def ensure():
    with shared.db() as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS agency_full_sync(wallet TEXT PRIMARY KEY,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS agency_full_profiles(
                wallet TEXT,run_id TEXT,player_id INTEGER,payload TEXT NOT NULL,checked_at TEXT NOT NULL,
                PRIMARY KEY(wallet,run_id,player_id));
        ''')


def state(wallet):
    ensure()
    with shared.db() as c:
        row = c.execute('SELECT payload FROM agency_full_sync WHERE wallet=?', (wallet.lower(),)).fetchone()
    return json.loads(row[0]) if row else {}


def _save(wallet, value):
    value['heartbeat'] = now()
    with shared.db() as c:
        c.execute('INSERT OR REPLACE INTO agency_full_sync VALUES(?,?)', (wallet, json.dumps(value)))


def items(payload, kind):
    if isinstance(payload, list):
        if not all(isinstance(x, dict) for x in payload):
            raise SyncError(f'MFL returned invalid {kind} records.')
        return payload
    if isinstance(payload, dict):
        for key in (kind, 'data', 'items', 'results'):
            if key in payload and isinstance(payload[key], (dict, list)):
                return items(payload[key], kind)
    raise SyncError(f'MFL returned an unrecognised {kind} response; saved data was not replaced.')


def player_id(player):
    p = shared._unwrap(player)
    m = p.get('metadata') or {}
    value = p.get('id', p.get('playerId', m.get('id')))
    try:
        pid = int(value)
        if isinstance(value, bool) or pid <= 0:
            raise ValueError
        return pid
    except (ValueError, TypeError):
        raise SyncError('MFL returned a player without a valid ID.') from None


class Client:
    def __init__(self):
        self.access = None
        self.auth_attempted = False

    def get(self, path, params=None):
        headers = dict(shared.H)
        headers['Cache-Control'] = 'no-cache'
        if self.access:
            headers['Authorization'] = 'Bearer ' + self.access
        try:
            response = requests.get(shared.BASE + path, params=params, headers=headers, timeout=(6, 25))
            if response.status_code == 401 and not self.auth_attempted:
                self.auth_attempted = True
                refresh = os.getenv('MFL_REFRESH_TOKEN', '').strip()
                if not refresh:
                    raise SyncError('MFL requires authentication. Set MFL_REFRESH_TOKEN in app Secrets.')
                auth = requests.post(shared.BASE + '/auth/refresh', headers=shared.H,
                                     json={'refreshToken': refresh}, timeout=(6, 20))
                if not auth.ok:
                    raise SyncError(f'MFL authentication returned HTTP {auth.status_code}.')
                data = auth.json()
                access = data.get('access') or (data.get('data') or {}).get('access')
                self.access = access.get('token') if isinstance(access, dict) else access
                if not self.access:
                    raise SyncError('MFL authentication did not return an access token.')
                return self.get(path, params)
            if response.status_code == 429:
                raise SyncError('MFL rate limit reached. Wait a few minutes, then resume the sync.')
            if response.status_code == 403 and 'text/html' in response.headers.get('content-type', ''):
                raise SyncError('MFL security service blocked this server (HTTP 403).')
            if not response.ok:
                raise SyncError(f'MFL returned HTTP {response.status_code} for {path}. Resume to retry.')
            return response.json()
        except requests.RequestException:
            raise SyncError('MFL could not be reached. Resume to retry; saved profiles are retained.') from None
        except (ValueError, TypeError, AttributeError):
            raise SyncError('MFL returned an unexpected response. Saved data was not replaced.') from None


def discover(wallet, client, progress=None):
    """Continue to an explicit empty page, even when a page is shorter than limit."""
    seen = set()
    before = None
    expected = None
    for page in range(1, 1001):
        if progress:
            progress(len(seen), 0, f'Reading agency roster, page {page}…')
        params = {'ownerWalletAddress': wallet, 'limit': 100}
        if before is not None:
            params['beforePlayerId'] = before
        payload = client.get('/players', params)
        batch = items(payload, 'players')
        if isinstance(payload, dict):
            sources = [payload, payload.get('pagination'), payload.get('meta'), payload.get('data')]
            for source in sources:
                if not isinstance(source, dict):
                    continue
                for key in ('total', 'totalCount', 'totalPlayers'):
                    value = source.get(key)
                    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                        expected = value
        if not batch:
            if expected is not None and len(seen) != expected:
                raise SyncError(f'MFL reported {expected} players but returned {len(seen)}. The roster is incomplete; saved data was not replaced.')
            return sorted(seen), page
        ids = [player_id(p) for p in batch]
        fresh = set(ids) - seen
        if not fresh or (before is not None and min(fresh) >= before):
            raise SyncError('MFL pagination did not advance. The agency roster is incomplete; saved data was not replaced.')
        if before is not None and any(pid > before for pid in ids):
            raise SyncError('MFL returned out-of-order agency pages. Saved data was not replaced.')
        seen.update(fresh)
        before = min(ids)
    raise SyncError('Agency pagination exceeded the safety limit. The sync is incomplete.')


def owned_clubs(wallet, client):
    payload = client.get('/clubs', {'walletAddress': wallet})
    rows = items(payload, 'clubs')
    found = {}
    for row in rows:
        if str(row.get('title') or '').upper() != 'MFL_OWNER':
            continue
        club = row.get('club') if isinstance(row.get('club'), dict) else row
        name = club.get('name') or club.get('clubName')
        cid = club.get('id') or club.get('clubId')
        if not name or cid is None:
            raise SyncError('An owned-club record was incomplete. Saved club data was not replaced.')
        found[str(cid)] = {'id': cid, 'name': str(name)}
    # Unknown objects are not an authoritative empty ownership list.
    if rows and not any('title' in r for r in rows):
        raise SyncError('MFL club ownership format was not recognised.')
    return list(found.values())


def current_club(player):
    p = shared._unwrap(player)
    meta = p.get('metadata') if isinstance(p.get('metadata'), dict) else {}
    for key in ('currentClub', 'activeContract', 'club', 'contract'):
        for source in (p, meta):
            if key not in source:
                continue
            value = source[key]
            if value is None:
                return None, True
            if key in ('activeContract', 'contract'):
                if not isinstance(value, dict) or 'club' not in value:
                    continue
                value = value['club']
                if value is None:
                    return None, True
            if isinstance(value, str):
                return value.strip() or None, True
            if isinstance(value, dict):
                name = value.get('name') or value.get('clubName')
                if name:
                    return str(name), True
    return None, False


def normalise(payload, pid):
    p = shared._unwrap(payload)
    if not isinstance(p, dict) or not p:
        raise SyncError(f'Player {pid}: empty profile response.')
    if any(k in p for k in ('id', 'playerId')) and player_id(p) != pid:
        raise SyncError(f'Player {pid}: MFL returned a different player ID.')
    m = p.get('metadata') if isinstance(p.get('metadata'), dict) else {}
    name = p.get('name') or m.get('name') or ' '.join(str(m.get(k) or p.get(k) or '') for k in ('firstName', 'lastName')).strip()
    if not name:
        raise SyncError(f'Player {pid}: no player name returned.')
    club, verified = current_club(p)
    sources = [m, p, m.get('attributes') or {}, p.get('attributes') or {}]
    aliases = {'overall': ('overall', 'overallRating', 'ovr'), 'pace': ('pace', 'PAC'),
               'shooting': ('shooting', 'SHO'), 'passing': ('passing', 'PAS'),
               'dribbling': ('dribbling', 'DRI'), 'defense': ('defense', 'defending', 'DEF'),
               'physical': ('physical', 'physicality', 'PHY')}
    stats = {key: next((source[k] for source in sources if isinstance(source, dict)
                       for k in names if source.get(k) is not None), None) for key, names in aliases.items()}
    return {'player_id': pid, 'player_name': str(name), 'club': club, 'club_verified': verified,
            'age': m.get('age', p.get('age')), 'position': shared._position(p),
            **stats, 'position_ratings': json.dumps(payload_ratings(p)), 'cached_at': now()}


def staged(wallet, run_id):
    with shared.db() as c:
        return {r['player_id']: json.loads(r['payload']) for r in c.execute(
            'SELECT player_id,payload FROM agency_full_profiles WHERE wallet=? AND run_id=?', (wallet, run_id))}


def _publish(wallet, run, profiles):
    """Commit current membership, clubs and agency current values together."""
    c = agency.db()
    agency.init(c)
    agency.ensure_v2(c)
    c.close()
    completed = now()
    columns = ('wallet', 'player_id', 'player_name', 'club', 'age', 'position', 'overall', 'pace', 'shooting', 'passing', 'dribbling', 'defense', 'physical', 'cached_at', 'position_ratings')
    c = shared.db()
    try:
        c.execute('ATTACH DATABASE ? AS agency_live', (str(Path(agency.DB).resolve()),))
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM roster WHERE wallet=?', (wallet,))
        for pid in run['ids']:
            row = profiles[pid]
            c.execute('INSERT INTO roster (' + ','.join(columns) + ') VALUES(' + ','.join('?' for _ in columns) + ')',
                      tuple(wallet if k == 'wallet' else row.get(k) for k in columns))
            values = [row.get(k) for k in ('overall', 'pace', 'shooting', 'passing', 'dribbling', 'defense', 'physical')]
            c.execute('''INSERT INTO agency_live.ownership_v65(
                wallet,player_id,player_name,source,confidence,
                start_ovr,start_pac,start_sho,start_pas,start_dri,start_def,start_phy,
                current_ovr,current_pac,current_sho,current_pas,current_dri,current_def,current_phy,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(wallet,player_id) DO UPDATE SET player_name=excluded.player_name,
                current_ovr=excluded.current_ovr,current_pac=excluded.current_pac,current_sho=excluded.current_sho,
                current_pas=excluded.current_pas,current_dri=excluded.current_dri,current_def=excluded.current_def,
                current_phy=excluded.current_phy,updated_at=excluded.updated_at''',
                (wallet,pid,row['player_name'],'SHARED WALLET CACHE','BASELINE PENDING',*values,*values,row['cached_at']))
            c.execute('''INSERT INTO agency_live.player_meta VALUES(?,?,?,?,?)
                ON CONFLICT(wallet,player_id) DO UPDATE SET age=excluded.age,position=excluded.position,club=excluded.club''',
                (wallet,pid,row['age'],row['position'],row['club']))
        c.execute('DELETE FROM clubs WHERE wallet=?', (wallet,))
        for club in run['clubs']:
            c.execute('INSERT INTO clubs VALUES(?,?,?,?)', (wallet,club['id'],club['name'],completed))
        for key, value in {'roster_updated': completed, 'clubs_updated': completed,
                           'agency_membership_verified': 'true', 'agency_full_sync_completed_at': completed,
                           'agency_full_sync_run_id': run['run_id'],
                           'agency_full_snapshot': json.dumps({'ids':run['ids'],'clubs':run['clubs']})}.items():
            c.execute('INSERT OR REPLACE INTO meta VALUES(?,?,?)', (wallet,key,value))
        run.update(status='complete', completed_at=completed, checked=len(profiles), error=None)
        c.execute('INSERT OR REPLACE INTO agency_full_sync VALUES(?,?)', (wallet,json.dumps(run)))
        c.execute('DELETE FROM agency_full_profiles WHERE wallet=? AND run_id<>?', (wallet,run['run_id']))
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def sync(wallet, client=None, progress=None, restart=False, delay=.25, max_profiles=None):
    wallet = wallet.strip().lower()
    ensure()
    client = client or Client()
    with shared.db() as c:
        c.execute('BEGIN IMMEDIATE')
        row = c.execute('SELECT payload FROM agency_full_sync WHERE wallet=?', (wallet,)).fetchone()
        run = json.loads(row[0]) if row else {}
        if run.get('status') == 'running':
            heartbeat = datetime.fromisoformat(run['heartbeat'])
            if (datetime.now(timezone.utc) - heartbeat).total_seconds() < 120:
                return {**run, 'busy': True}
        if restart or not run or run.get('status') == 'complete':
            run = {'run_id': uuid.uuid4().hex, 'started_at': now(), 'ids': None, 'clubs': None, 'checked': 0}
        run.update(status='running', heartbeat=now(), error=None)
        c.execute('INSERT OR REPLACE INTO agency_full_sync VALUES(?,?)', (wallet,json.dumps(run)))
    try:
        if run['ids'] is None:
            run['ids'], run['pages'] = discover(wallet, client, progress)
            _save(wallet, run)
        checked_this_call = 0
        for reconciliation in range(3):
            profiles = {pid:p for pid,p in staged(wallet, run['run_id']).items() if pid in set(run['ids'])}
            for pid in run['ids']:
                if pid in profiles:
                    continue
                if max_profiles is not None and checked_this_call >= max_profiles:
                    raise SyncError('Sync paused. Resume to check the remaining players.')
                if progress:
                    progress(len(profiles), len(run['ids']), f'Checking player #{pid}…')
                profile = normalise(client.get(f'/players/{pid}'), pid)
                with shared.db() as c:
                    c.execute('INSERT OR REPLACE INTO agency_full_profiles VALUES(?,?,?,?,?)',
                              (wallet,run['run_id'],pid,json.dumps(profile),profile['cached_at']))
                profiles[pid] = profile
                checked_this_call += 1
                run['checked'] = len(profiles)
                _save(wallet, run)
                if progress:
                    progress(len(profiles), len(run['ids']), f"Checked {profile['player_name']}")
                if delay:
                    time.sleep(delay)
            if progress:
                progress(len(profiles), len(run['ids']), 'Verifying agency membership and owned clubs…')
            final_ids, pages = discover(wallet, client)
            run['pages'] = pages
            if final_ids != run['ids']:
                run['ids'] = final_ids
                _save(wallet, run)
                continue
            run['clubs'] = owned_clubs(wallet, client)
            profiles = {pid: profiles[pid] for pid in run['ids']}
            run['unverified_clubs'] = sum(not p['club_verified'] for p in profiles.values())
            run['missing_squad_fields'] = sum(not p.get('position') or p.get('overall') is None for p in profiles.values())
            _publish(wallet, run, profiles)
            return run
        raise SyncError('Agency membership changed repeatedly during this sync. Resume to verify the latest roster.')
    except (SyncError, requests.RequestException) as exc:
        run.update(status='paused', error=str(exc))
        _save(wallet, run)
        return run
    except Exception:
        run.update(status='paused', error='The sync could not finish. Saved data is retained; resume to retry.')
        _save(wallet, run)
        raise


def export_frame(wallet):
    ensure()
    wallet = wallet.lower()
    run_id = shared._meta_get(wallet, 'agency_full_sync_run_id')
    if not run_id:
        return pd.DataFrame()
    completed = shared._meta_get(wallet, 'agency_full_sync_completed_at')
    snapshot = json.loads(shared._meta_get(wallet, 'agency_full_snapshot') or '{}')
    owned = {c['name'].casefold() for c in snapshot.get('clubs', [])}
    ids = set(snapshot.get('ids', []))
    rows = []
    for pid, p in staged(wallet, run_id).items():
        # Only export membership from the committed snapshot, not obsolete staged IDs.
        if pid not in ids:
            continue
        rows.append({'Player ID': pid, 'Player': p['player_name'], 'Age': p['age'], 'Position': p['position'],
                     'Club': p['club'], 'Club verified': p['club_verified'],
                     'Owned club': bool(p['club'] and p['club'].casefold() in owned),
                     'Current OVR': p['overall'], 'PAC': p['pace'], 'SHO': p['shooting'], 'PAS': p['passing'],
                     'DRI': p['dribbling'], 'DEF': p['defense'], 'PHY': p['physical'],
                     'Position ratings': p['position_ratings'], 'Profile checked (UTC)': p['cached_at'],
                     'Full sync completed (UTC)': completed, 'Sync run': run_id})
    return pd.DataFrame(rows).sort_values(['Club','Player'], na_position='last') if rows else pd.DataFrame()
