import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from streamlit.testing.v1 import AppTest

import agency_backend as agency
import agency_full_sync as full
import wallet_cache_backend as shared

WALLET = '0x1234567890abcdef'


def player(pid, club='FCN New Club', ovr=70):
    return {'id':pid,'parentClub':{'name':'FCN Stale Club'},
            'currentClub':{'name':club} if club else None,
            'metadata':{'firstName':'Player','lastName':str(pid),'age':22,
                        'positions':['CM','CDM'],'overall':ovr,
                        'attributes':{'pace':61,'shooting':62,'passing':72,'dribbling':65,'defense':60,'physical':63}}}


class FakeClient:
    def __init__(self, players):
        self.players = players
        self.calls = []
        self.fail_pid = None

    def get(self, path, params=None):
        self.calls.append((path,params))
        if path == '/players':
            before = (params or {}).get('beforePlayerId', 10**12)
            # Deliberately shorter than requested limit=100.
            ids = sorted((p for p in self.players if p < before), reverse=True)[:2]
            return [self.players[p] for p in ids]
        if path == '/clubs':
            return [{'title':'MFL_OWNER','club':{'id':7,'name':'FCN New Club'}}]
        pid = int(path.split('/')[-1])
        if pid == self.fail_pid:
            raise full.SyncError('MFL rate limit reached. Resume later.')
        return self.players[pid]


class EntireAgencyTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.previous)
        self.tmp.cleanup()

    def seed_old(self):
        with shared.db() as c:
            c.execute('INSERT INTO roster(wallet,player_id,player_name,club,position,overall,cached_at) VALUES(?,?,?,?,?,?,?)',
                      (WALLET,1,'Old name','Old club','ST',60,'2020-01-01T00:00:00+00:00'))
        agency.seed_from_shared(WALLET)
        c = agency.db()
        c.execute('UPDATE ownership_v65 SET start_ovr=55,confidence=?,source=? WHERE wallet=?',('VERIFIED','KNOWN',WALLET))
        c.commit()
        c.close()

    def test_short_pages_continue_until_empty_and_total_is_checked(self):
        client = FakeClient({p:player(p) for p in (1,2,3)})
        ids,pages = full.discover(WALLET,client)
        self.assertEqual(ids,[1,2,3])
        self.assertEqual(pages,3)
        bad = Mock()
        bad.get.side_effect = [{'players':[player(1)],'total':2},{'players':[],'total':2}]
        with self.assertRaisesRegex(full.SyncError,'reported 2 players but returned 1'):
            full.discover(WALLET,bad)

    def test_full_sync_refreshes_current_values_and_preserves_baselines(self):
        self.seed_old()
        result = full.sync(WALLET,FakeClient({1:player(1,ovr=74),2:player(2,club=None)}),delay=0)
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['checked'],2)
        roster = {p['player_id']:p for p in shared.roster_rows(WALLET)}
        self.assertEqual((roster[1]['club'],roster[1]['overall'],roster[1]['passing']),('FCN New Club',74,72))
        self.assertIsNone(roster[2]['club'])
        c = agency.db()
        c.row_factory = __import__('sqlite3').Row
        old = dict(c.execute('SELECT * FROM ownership_v65 WHERE player_id=1').fetchone())
        self.assertEqual((old['start_ovr'],old['current_ovr'],old['confidence'],old['source']),(55,74,'VERIFIED','KNOWN'))
        c.close()
        export = full.export_frame(WALLET)
        self.assertEqual(len(export),2)
        self.assertTrue(export['Profile checked (UTC)'].notna().all())
        self.assertTrue(export['Full sync completed (UTC)'].notna().all())
        self.assertTrue(export['Club verified'].all())
        self.assertEqual(export['Owned club'].sum(),1)

    def test_pause_and_resume_keep_old_snapshot_and_do_not_repeat_checked_profiles(self):
        self.seed_old()
        client = FakeClient({1:player(1),2:player(2),3:player(3)})
        client.fail_pid = 2
        result = full.sync(WALLET,client,delay=0)
        self.assertEqual(result['status'],'paused')
        self.assertEqual(result['checked'],1)
        self.assertEqual(shared.roster_rows(WALLET)[0]['club'],'Old club')
        self.assertTrue(full.export_frame(WALLET).empty)
        client.fail_pid = None
        result = full.sync(WALLET,client,delay=0)
        self.assertEqual(result['status'],'complete')
        self.assertEqual(sum(path=='/players/1' for path,_ in client.calls),1)
        self.assertEqual(len(shared.roster_rows(WALLET)),3)

    def test_roster_change_is_reconciled_before_publishing(self):
        client = FakeClient({1:player(1),2:player(2)})
        original = client.get
        def changing(path,params=None):
            if path == '/players/2':
                result = original(path,params)
                client.players.pop(1,None)
                client.players[3] = player(3)
                return result
            return original(path,params)
        client.get = changing
        result = full.sync(WALLET,client,delay=0)
        self.assertEqual(result['status'],'complete')
        self.assertEqual(set(full.export_frame(WALLET)['Player ID']),{2,3})

    def test_sold_player_history_is_retained_but_current_membership_is_filtered(self):
        self.seed_old()
        full.sync(WALLET,FakeClient({2:player(2)}),delay=0)
        c = agency.db()
        self.assertEqual(c.execute('SELECT count(*) FROM ownership_v65').fetchone()[0],2)
        c.close()
        visible = agency.current_members(pd.DataFrame([{'player_id':1},{'player_id':2}]),WALLET)
        self.assertEqual(visible.player_id.tolist(),[2])
        self.assertEqual(set(full.export_frame(WALLET)['Player ID']),{2})

    def test_failed_discovery_does_not_replace_old_roster_or_club_data(self):
        self.seed_old()
        client = Mock()
        client.get.return_value = {'unexpected':'not a player list'}
        result = full.sync(WALLET,client,delay=0)
        self.assertEqual(result['status'],'paused')
        self.assertEqual(shared.roster_rows(WALLET)[0]['club'],'Old club')
        repeating = Mock()
        repeating.get.return_value = [player(1)]
        with self.assertRaisesRegex(full.SyncError,'did not advance'):
            full.discover(WALLET,repeating)

    def test_failed_club_read_does_not_publish_a_false_empty_owned_club_list(self):
        self.seed_old()
        shared.save_clubs(WALLET,[{'id':1,'name':'Old club'}])
        client = FakeClient({1:player(1)})
        original = client.get
        def fail_clubs(path,params=None):
            if path == '/clubs':
                raise full.SyncError('Club service unavailable')
            return original(path,params)
        client.get = fail_clubs
        self.assertEqual(full.sync(WALLET,client,delay=0)['status'],'paused')
        self.assertEqual(shared.clubs_rows(WALLET)[0]['name'],'Old club')
        self.assertEqual(shared.roster_rows(WALLET)[0]['club'],'Old club')

    def test_explicit_null_current_club_beats_stale_parent_and_contract(self):
        p = player(1,club=None)
        p['contract']={'club':{'name':'Old contract'}}
        self.assertEqual(full.current_club(p),(None,True))
        self.assertIsNone(shared._club_name(p))
        p.pop('currentClub')
        p.pop('contract')
        self.assertEqual(full.current_club(p),(None,False))

    def test_completed_export_does_not_mix_in_a_later_quick_cache_refresh(self):
        full.sync(WALLET,FakeClient({1:player(1)}),delay=0)
        with shared.db() as c:
            c.execute('UPDATE roster SET club=? WHERE wallet=?',('Changed by quick cache',WALLET))
        export = full.export_frame(WALLET)
        self.assertEqual(export.iloc[0]['Club'],'FCN New Club')

    def test_browser_backup_restores_full_sync_snapshot_on_a_fresh_server(self):
        import browser_persistence as browser
        full.sync(WALLET,FakeClient({1:player(1)}),delay=0)
        backup = browser.dump_wallet(WALLET)
        with tempfile.TemporaryDirectory() as restored:
            os.chdir(restored)
            try:
                browser.restore_wallet(backup['value'],WALLET)
                self.assertEqual(full.state(WALLET)['status'],'complete')
                self.assertEqual(full.export_frame(WALLET).iloc[0]['Club'],'FCN New Club')
            finally:
                os.chdir(self.tmp.name)

    def test_empty_agency_and_wallet_isolation(self):
        self.seed_old()
        result = full.sync('0xother',FakeClient({}),delay=0)
        self.assertEqual(result['status'],'complete')
        self.assertEqual(len(shared.roster_rows(WALLET)),1)
        self.assertTrue(full.export_frame('0xother').empty)

    def test_reseeding_shared_cache_updates_existing_values_without_resetting_start(self):
        self.seed_old()
        with shared.db() as c:
            c.execute('UPDATE roster SET overall=75,club=? WHERE wallet=?',('FCN Correct Club',WALLET))
        agency.seed_from_shared(WALLET)
        c = agency.db()
        self.assertEqual(tuple(c.execute('SELECT start_ovr,current_ovr FROM ownership_v65').fetchone()),(55,75))
        self.assertEqual(c.execute('SELECT club FROM player_meta').fetchone()[0],'FCN Correct Club')
        c.close()

    def test_button_completes_and_offers_unfiltered_timestamped_export(self):
        import streamlit as st
        st.cache_data.clear()
        st.cache_resource.clear()
        app = Path(__file__).resolve().parents[1] / 'app.py'
        at = AppTest.from_file(str(app),default_timeout=30)
        at.session_state['wallet'] = WALLET
        with patch.object(full,'Client',return_value=FakeClient({1:player(1),2:player(2,club=None)})),patch.object(full.time,'sleep'):
            at.run()
            button = next(b for b in at.button if b.label=='Sync entire agency')
            button.click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('All 2 players updated' in s.value for s in at.caption))
        self.assertTrue(any('Download agency CSV' == b.label for b in at.get('download_button')))


if __name__=='__main__':
    unittest.main()
