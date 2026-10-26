import os
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
import agency_backend as agency
import wallet_cache_backend as shared
from player_visibility import filter_frame

APP=Path(__file__).resolve().parents[1]/'app.py'

class RetiredVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.previous=os.getcwd();self.temp=tempfile.TemporaryDirectory();os.chdir(self.temp.name)
        self.wallet='0x1234567890abcdef'
        with shared.db() as c:
            c.executemany('INSERT INTO roster(wallet,player_id,player_name,club,position,overall) VALUES(?,?,?,?,?,?)',[(self.wallet,1,'Active Player','New Club','CM',70),(self.wallet,2,'Retired Player',None,'CM',69)])

    def tearDown(self):os.chdir(self.previous);self.temp.cleanup()

    def test_latest_null_club_overrides_stale_club_without_erasing_history(self):
        frame=pd.DataFrame([{'player_id':1,'club':'Old Club','ovr_gain':1},{'player_id':2,'club':'Old Club','ovr_gain':5}])
        visible=filter_frame(frame,self.wallet)
        self.assertEqual(visible.player_id.tolist(),[1])
        self.assertEqual(visible.iloc[0].club,'Old Club') # Historical grouping is preserved.
        all_players=filter_frame(frame,self.wallet,show_retired=True,update_clubs=True)
        self.assertEqual(len(all_players),2)
        self.assertEqual(all_players.iloc[0].club,'New Club')
        self.assertIsNone(all_players.iloc[1].club)
        self.assertEqual(len(frame),2)

    def test_seed_clears_old_club_when_latest_roster_says_retired(self):
        agency.seed_from_shared(self.wallet)
        c=agency.db();c.execute("UPDATE player_meta SET club='Stale Club' WHERE player_id=2");c.commit();c.close()
        agency.seed_from_shared(self.wallet)
        c=agency.db();club=c.execute('SELECT club FROM player_meta WHERE wallet=? AND player_id=2',(self.wallet,)).fetchone()[0];c.close()
        self.assertIsNone(club)

    def test_agency_hides_retired_by_default_and_toggle_restores_them(self):
        agency.seed_from_shared(self.wallet)
        # Simulate old analysis metadata surviving after a roster refresh.
        c=agency.db();c.execute("UPDATE player_meta SET club='Stale Club' WHERE player_id=2");c.commit();c.close()
        at=AppTest.from_file(str(APP),default_timeout=30);at.query_params['page']='Agency Development';at.session_state['wallet']=self.wallet;at.run()
        self.assertFalse(at.exception)
        data=next(d.value for d in at.dataframe if 'Player' in d.value.columns and 'Current' in d.value.columns)
        self.assertEqual(data.Player.tolist(),['Active Player'])
        at.toggle(key='show_retired_players').set_value(True).run()
        self.assertFalse(at.exception)
        data=next(d.value for d in at.dataframe if 'Player' in d.value.columns and 'Current' in d.value.columns)
        self.assertEqual(set(data.Player),{'Active Player','Retired Player'})

    def test_no_roster_uses_known_club_metadata(self):
        frame=pd.DataFrame([{'player_id':10,'club':'Active'},{'player_id':11,'club':'Retired'},{'player_id':12,'club':None}])
        self.assertEqual(filter_frame(frame,'unknown').player_id.tolist(),[10])
