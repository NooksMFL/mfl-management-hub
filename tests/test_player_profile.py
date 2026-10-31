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
