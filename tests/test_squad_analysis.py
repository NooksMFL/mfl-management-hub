import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import agency_full_sync as full
import browser_persistence as browser
import squad_analysis as analysis
import wallet_cache_backend as shared
from test_entire_agency_sync import FakeClient, WALLET, player

APP=Path(__file__).resolve().parents[1]/'app.py'

def p(pid,pos='CM',ovr=65,club='FCN Test',**kw):
    return {'player_id':pid,'player_name':f'Player {pid}','position':pos,'overall':ovr,'club':club,**kw}

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.previous=os.getcwd();self.temp=tempfile.TemporaryDirectory();os.chdir(self.temp.name)
    def tearDown(self):os.chdir(self.previous);self.temp.cleanup()
    def stage_452(self):
        full.ensure()
        ids=list(range(1,461))
        state={'run_id':'keep-this-run','status':'paused','ids':ids,'checked':452,'heartbeat':full.now(),'clubs':None}
        full._save(WALLET,state)
        with shared.db() as c:
            for pid in ids[:452]:
                profile=full.normalise(player(pid,club=None if pid==1 else 'FCN Test'),pid)
                c.execute('INSERT INTO agency_full_profiles VALUES(?,?,?,?,?)',(WALLET,state['run_id'],pid,json.dumps(profile),profile['cached_at']))
        return state
    def test_452_checkpoint_unchanged_after_analysis_filter_and_browser_recovery(self):
        state=self.stage_452()
        before=full.staged(WALLET,state['run_id'])
        with patch.object(full.Client,'get',side_effect=AssertionError('Analysis must never call MFL')):
            rows,coverage=analysis.snapshot(WALLET)
            self.assertEqual(coverage,{'checked':452,'total':460,'partial':True})
            report,_=analysis.analyse(rows)
            self.assertTrue(report)
            self.assertEqual(len([r for r in rows if analysis.is_active(r)]),451)
            self.assertEqual(analysis.club_names(WALLET,rows),['FCN Test'])
        self.assertEqual(full.state(WALLET),state)
        self.assertEqual(full.staged(WALLET,state['run_id']),before)
        backup=browser.dump_wallet(WALLET)
        with tempfile.TemporaryDirectory() as folder:
            os.chdir(folder)
            try:
                browser.restore_wallet(backup['value'],WALLET)
                self.assertEqual(full.state(WALLET),state)
                self.assertEqual(full.staged(WALLET,state['run_id']),before)
                client=FakeClient({pid:player(pid) for pid in range(1,461)})
                result=full.sync(WALLET,client,delay=0)
                self.assertEqual(result['status'],'complete')
                called=[int(path.split('/')[-1]) for path,params in client.calls if path.startswith('/players/')]
                self.assertEqual(called,list(range(453,461)))
            finally:os.chdir(self.temp.name)
    def test_one_versatile_player_cannot_fill_multiple_positions(self):
        report,allocation=analysis.analyse([p(1,'LB / RB',position_ratings='{"LB":65,"RB":65}')],target=65)
        used=[v['player_id'] for r in allocation.values() for group in r.values() for v in group]
        self.assertEqual(used,[1])
        self.assertEqual(sum(r['Starters'] for r in report),1)
        self.assertEqual(sum(r['Cover'] for r in report),0)
    def test_secondary_unknown_is_flagged_and_not_falsely_rated(self):
        report,allocation=analysis.analyse([p(1,'CF / ST',ovr=80)],target=70)
        row=next(r for r in report if r['Position']=='ST')
        self.assertEqual(row['Priority'],'Check ratings')
        self.assertIn('(?)',row['Starting players'])
        self.assertIsNone(allocation['ST']['starters'][0]['rating'])
    def test_weak_starter_cover_shortage_and_retired_exclusion(self):
        report,_=analysis.analyse([p(1,'GK',55),p(2,'GK',90,club=None),p(3,'CB',65,is_retired=True)],target=65)
        gk=next(r for r in report if r['Position']=='GK')
        self.assertEqual(gk['Priority'],'Strengthen')
        self.assertIn('Upgrade 1 starter',gk['Action']);self.assertIn('Add 1 cover',gk['Action'])
        cb=next(r for r in report if r['Position']=='CB')
        self.assertEqual(cb['Starters'],0);self.assertEqual(cb['Starting places'],2)
    def test_complete_squad_has_no_false_gaps(self):
        import tactics_engine
        positions=[tactics_engine.canonical(role) for role,_,_ in tactics_engine.FORMATIONS['4-3-3']]*2
        report,_=analysis.analyse([p(i,pos,70) for i,pos in enumerate(positions,1)],target=65)
        self.assertTrue(all(r['Priority']=='Covered' for r in report))
        self.assertEqual(sum(r['Starters'] for r in report),11);self.assertEqual(sum(r['Cover'] for r in report),11)
    def test_partial_analyser_page_works_without_api_or_finishing_sync(self):
        state=self.stage_452()
        at=AppTest.from_file(str(APP),default_timeout=30)
        at.session_state['wallet']=WALLET;at.query_params['page']='Squad analyser'
        with patch.object(full.Client,'get',side_effect=AssertionError('No requests')):at.run()
        self.assertFalse(at.exception)
        self.assertTrue(any('452 of 460' in w.value for w in at.warning))
        self.assertTrue(any('Positions to review' in m.value for m in at.markdown))
        self.assertEqual(full.state(WALLET),state)
        self.assertEqual(len(full.staged(WALLET,state['run_id'])),452)
    def test_startup_never_overwrites_browser_backup_before_reading_it(self):
        import streamlit_js_eval as js
        self.stage_452()
        at=AppTest.from_file(str(APP),default_timeout=30)
        at.session_state['wallet']=WALLET;at.query_params['page']='Squad analyser'
        with patch.object(js,'streamlit_js_eval',return_value=None),patch.object(js,'set_local_storage') as write:
            at.run()
        self.assertFalse(at.exception)
        keys=[call.args[0] for call in write.call_args_list]
        self.assertNotIn('mfl_hub_wallet_'+WALLET[2:],keys)
        self.assertEqual(len(full.staged(WALLET,'keep-this-run')),452)

    def test_older_browser_checkpoint_does_not_replace_server_progress(self):
        import streamlit_js_eval as js
        self.stage_452()
        old=browser.dump_wallet(WALLET)
        with shared.db() as c:
            profile=full.normalise(player(453),453)
            c.execute('INSERT INTO agency_full_profiles VALUES(?,?,?,?,?)',(WALLET,'keep-this-run',453,json.dumps(profile),profile['cached_at']))
        at=AppTest.from_file(str(APP),default_timeout=30)
        at.session_state['wallet']=WALLET;at.query_params['page']='Squad analyser'
        with patch.object(js,'streamlit_js_eval',return_value={'ready':True,'value':old['value']}),patch.object(js,'set_local_storage'):
            at.run()
        self.assertFalse(at.exception)
        self.assertEqual(len(full.staged(WALLET,'keep-this-run')),453)

    def test_owned_club_scope_excludes_other_loan_clubs(self):
        with shared.db() as c:c.execute('INSERT INTO clubs VALUES(?,?,?,?)',(WALLET,1,'Owned Club',full.now()))
        rows=[p(1,club='FCN Test'),p(2,club='Owned Club'),p(3,club='Other Club')]
        self.assertEqual(analysis.club_names(WALLET,rows),['FCN Test'])
        self.assertEqual(analysis.club_names(WALLET,rows,False),['FCN Test','Owned Club'])

if __name__=='__main__':unittest.main()
