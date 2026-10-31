"""Focused Hub UI, safe rate-limit recovery and progression correctness."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from streamlit.testing.v1 import AppTest
import agency_full_sync as full
import hub_progression as hub
import wallet_cache_backend as shared
from test_entire_agency_sync import FakeClient, WALLET, player

APP=Path(__file__).resolve().parents[1]/'app.py'
PAGES=['Agency progression','Club progression','Transfer Bargains']

class FocusedHubTests(unittest.TestCase):
    def setUp(self):
        self.previous=os.getcwd();self.temp=tempfile.TemporaryDirectory();os.chdir(self.temp.name)
    def tearDown(self):
        os.chdir(self.previous);self.temp.cleanup()
    def page(self,page='',wallet=''):
        at=AppTest.from_file(str(APP),default_timeout=30)
        at.query_params['page']=page;at.session_state['wallet']=wallet
        return at.run()
    def test_only_three_sections_and_old_links_redirect(self):
        for old in ['Home','Design Studio','Squad Builder','Agency / Player Valuation','Sync Centre']:
            at=self.page(old)
            self.assertFalse(at.exception)
            self.assertEqual(at.title[0].value,PAGES[0])
            self.assertEqual(at.radio(key='hub_page').options,PAGES)
            self.assertFalse(at.toggle)
        at.radio(key='hub_page').set_value('Transfer Bargains').run()
        self.assertEqual(at.title[0].value,'Transfer Bargains')
        self.assertFalse(at.exception)
        self.assertTrue(any(b.label=='Find bargains' for b in at.button))
    def test_aliases_and_no_network_on_page_load(self):
        with patch.object(full.Client,'get',side_effect=AssertionError('Unexpected API call')):
            for page,target in [('Agency Development',PAGES[0]),('Club Development',PAGES[1])]:
                at=self.page(page,WALLET)
                self.assertFalse(at.exception)
                self.assertEqual(at.title[0].value,target)
    def test_all_players_and_unknown_gains_stay_visible(self):
        full.sync(WALLET,FakeClient({1:player(1),2:player(2,None)}),delay=0)
        at=self.page(PAGES[0],WALLET)
        self.assertFalse(at.exception)
        frame=next(d.value for d in at.dataframe if 'Current OVR' in d.value)
        self.assertEqual(len(frame),2)
        self.assertIn('No club recorded',frame.Club.tolist())
        self.assertTrue(frame['OVR gain'].isna().all())
        self.assertTrue(any(m.label=='OVR gained' and m.value=='—' for m in at.metric))
    def test_bargain_failure_keeps_previous_results(self):
        import transfer_bargains_backend as bargains
        frame=pd.DataFrame([{'Player':'Test','Discount %':25,'Asking Price':10,'Comparable Asking Median':20}])
        at=self.page(PAGES[2])
        with patch.object(bargains,'scan',return_value=(frame,{'listings':30})):
            at.button(key='find_bargains').click().run()
        self.assertFalse(at.exception);self.assertEqual(len(at.dataframe[0].value),1)
        with patch.object(bargains,'scan',side_effect=full.SyncError('Rate limited')):
            at.button(key='find_bargains').click().run()
        self.assertFalse(at.exception);self.assertTrue(at.error)
        self.assertEqual(len(at.dataframe[0].value),1)
    def test_429_sets_shared_cooldown_without_repeated_requests(self):
        response=Mock(status_code=429,headers={'Retry-After':'120'})
        session=Mock();session.get.return_value=response
        with patch.object(full.requests,'Session',return_value=session):
            for _ in range(2):
                with self.assertRaises(full.SyncError) as error:full.Client().get('/players')
                self.assertEqual(error.exception.status,429)
            session.get.assert_called_once()
        self.assertGreater(float(shared._meta_get('__api__','retry_until')),time.time())
    def test_continue_button_unlocks_when_cooldown_expires(self):
        import agency_full_sync_ui as ui
        full._save(WALLET,{'status':'paused','retry_until':time.time()+120,'ids':[1],'checked':0})
        at=self.page(PAGES[0],WALLET)
        self.assertFalse(at.exception)
        self.assertTrue(at.button(key='hub_sync').disabled)
        with patch.object(ui.time,'time',return_value=time.time()+121):
            at.run()
        self.assertFalse(at.exception)
        self.assertFalse(at.button(key='hub_sync').disabled)
        self.assertEqual(at.button(key='hub_sync').label,'Continue sync')

    def test_json_403_refreshes_auth_once(self):
        denied=Mock(status_code=403,headers={'content-type':'application/json'})
        good=Mock(status_code=200,ok=True);good.json.return_value=[]
        auth=Mock(ok=True);auth.json.return_value={'access':{'token':'test-access'}}
        session=Mock();session.get.side_effect=[denied,good];session.post.return_value=auth
        with patch.dict(os.environ,{'MFL_REFRESH_TOKEN':'test-refresh'}),patch.object(full.requests,'Session',return_value=session):
            self.assertEqual(full.Client().get('/players'),[])
        session.post.assert_called_once()
        self.assertEqual(session.get.call_args.kwargs['headers']['Authorization'],'Bearer test-access')
    def test_paused_sync_respects_wait_and_can_resume_after_player_is_sold(self):
        client=FakeClient({1:player(1),2:player(2)})
        first=full.sync(WALLET,client,delay=0,max_profiles=1)
        self.assertEqual(first['status'],'paused')
        first['retry_until']=time.time()+120;full._save(WALLET,first)
        count=len(client.calls)
        self.assertTrue(full.sync(WALLET,client,delay=0)['cooldown'])
        self.assertEqual(len(client.calls),count)
        first['retry_until']=0;full._save(WALLET,first)
        del client.players[1]
        result=full.sync(WALLET,client,delay=0)
        self.assertEqual(result['status'],'complete')
        self.assertEqual([r['player_id'] for r in shared.roster_rows(WALLET)],[2])
    def test_season_baseline_never_uses_post_start_state(self):
        profile={f:70 for f in hub.FIELDS};profile['cached_at']='2026-11-10T00:00:00+00:00'
        event={'date':'2026-11-06T00:00:00Z','values':{f:65 for f in hub.FIELDS}}
        measured=hub.season_measure([event],profile,hub.SEASONS['Season 18'])
        self.assertIsNone(measured['baseline_at'])
        self.assertIsNone(measured['gains']['overall'])
        event['date']='2026-11-03T00:00:00Z'
        measured=hub.season_measure([event],profile,hub.SEASONS['Season 18'])
        self.assertEqual(measured['gains']['overall'],5)
        self.assertEqual(measured['attribute_gain'],30)
    def test_club_progression_resume_skips_completed_players(self):
        full.sync(WALLET,FakeClient({1:player(1),2:player(2)}),delay=0)
        client=Mock();client.get.side_effect=[[],full.SyncError('Wait',status=429,retry_after=120)]
        result=hub.update(WALLET,'club',hub.SEASONS['Season 18'],client=client,delay=0)
        self.assertEqual(result['status'],'paused');self.assertEqual(len(result['done']),1)
        hub.update(WALLET,'club',hub.SEASONS['Season 18'],client=client,delay=0)
        self.assertEqual(client.get.call_count,2)
        result['retry_until']=0;hub.save_job(WALLET,'club:'+hub.SEASONS['Season 18'],result)
        client.get.side_effect=None;client.get.return_value=[]
        result=hub.update(WALLET,'club',hub.SEASONS['Season 18'],client=client,delay=0)
        self.assertEqual(result['status'],'complete');self.assertEqual(client.get.call_count,3)

if __name__=='__main__':unittest.main()
