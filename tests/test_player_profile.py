import os
from pathlib import Path
import tempfile
import unittest
from streamlit.testing.v1 import AppTest
import wallet_cache_backend as shared
from player_profile import attributes,profile_html
from command_dashboard import roster_html

APP=Path(__file__).resolve().parents[1]/'app.py'

class ProfileDataTests(unittest.TestCase):
    def test_missing_attributes_are_unknown_and_zero_is_valid(self):
        result=attributes({'pace':0,'shooting':None,'passing':float('nan')})
        self.assertEqual(result[0]['value'],0)
        self.assertTrue(all(a['value'] is None for a in result[1:]))
        self.assertEqual([a['value'] for a in attributes({'current_pac':64,'current_sho':61,'current_pas':76,'current_dri':69,'current_def':57,'current_phy':49})],[64,61,76,69,57,49])

    def test_card_link_preserves_wallet_and_profile_is_escaped(self):
        player={'player_id':7,'player_name':'<script>Bad</script>','position':'CM / CDM','overall':69,'club':'Club & City','pace':64}
        markup=roster_html([player],'0x1234567890abcdef')
        self.assertIn('wallet=0x1234567890abcdef&amp;player=7',markup)
        self.assertIn('aria-label="View &lt;script&gt;',markup)
        profile=profile_html(player)
        self.assertNotIn('<script>',profile)
        self.assertIn('Club &amp; City',profile)
        self.assertEqual(profile.count('No saved measurement'),5)

class ProfilePageTests(unittest.TestCase):
    def setUp(self):
        self.previous=os.getcwd();self.temp=tempfile.TemporaryDirectory();os.chdir(self.temp.name)
        self.wallet='0x1234567890abcdef'
        with shared.db() as c:
            c.execute('INSERT INTO roster(wallet,player_id,player_name,position,overall,club,pace,passing,position_ratings) VALUES(?,?,?,?,?,?,?,?,?)',(self.wallet,7,'Habibou','CM / CDM',69,'Club',64,76,'{"CM":69,"CDM":62}'))
    def tearDown(self):os.chdir(self.previous);self.temp.cleanup()
    def page(self,pid):
        at=AppTest.from_file(str(APP),default_timeout=30);at.session_state['wallet']=self.wallet;at.query_params.update(page='Home',player=str(pid));return at.run()
    def test_selected_profile_shows_attributes_and_secondary_rating(self):
        at=self.page(7);self.assertFalse(at.exception)
        self.assertTrue(any('ops-profile-name' in m.value and 'Habibou' in m.value for m in at.markdown))
        self.assertNotIn('player',at.query_params) # Consumed open request cannot reopen after dismissal.
        data=next(d.value for d in at.dataframe if 'Position' in d.value.columns and 'Source' in d.value.columns)
        self.assertEqual(dict(zip(data.Position,data.Rating)),{'CM':'69','CDM':'62'})
        at.run();self.assertFalse(at.exception)
        self.assertTrue(any('class="ops-profile-name"' in m.value for m in at.markdown))
        at.button(key='close_player_profile').click().run();self.assertFalse(at.exception)
        self.assertNotIn('active_player_profile',at.session_state.filtered_state)
        self.assertNotIn('player',at.query_params)
    def test_invalid_or_other_roster_player_never_opens_a_profile(self):
        for pid in ['not-an-id',9999]:
            at=self.page(pid);self.assertFalse(at.exception)
            self.assertTrue(any('not available' in w.value for w in at.warning))
            self.assertFalse(any('class="ops-profile-name"' in m.value for m in at.markdown))
