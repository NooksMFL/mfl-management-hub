import json
import os
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
import club_tenure
import wallet_cache_backend as shared
import transfer_window_backend as tw

class ClubJoiningTests(unittest.TestCase):
    def test_history_baseline_is_joining_not_season(self):
        history=[{'date':'2026-09-22T00:00:00Z','values':{'overall':65,'pace':60}},
                 {'date':'2026-10-21T00:00:00Z','values':{'overall':69,'pace':64}},
                 {'date':'2026-10-25T00:00:00Z','values':{'overall':70,'pace':66}}]
        record=club_tenure.measure(history,'2026-10-22T00:00:00Z')
        self.assertEqual(club_tenure.changes(record)['overall'],1)
        self.assertEqual(club_tenure.changes(record)['pace'],2)
        self.assertIsNone(club_tenure.changes(record)['defense'])
        self.assertEqual(record['baseline_at'],'2026-10-21T00:00:00+00:00')

    def test_missing_pre_join_baseline_does_not_invent_zero(self):
        record=club_tenure.measure([{'date':'2026-10-25','values':{'overall':70}}],'2026-10-22')
        self.assertIn('Baseline unavailable',record['status'])
        self.assertIsNone(club_tenure.changes(record)['overall'])

    def test_joining_dates_persist_and_reset_on_change(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(shared,'DB',os.path.join(tmp,'test.db')):
            club_tenure.track('wallet',1,'Club','2026-10-22')
            self.assertEqual(len(club_tenure.tracked('wallet')),1)
            club_tenure.track('wallet',1,'Club','2026-10-23')
            record=club_tenure.tracked('wallet')[0]
            self.assertIn('2026-10-23',record['joined_at'])
            self.assertIsNone(record['baseline_json'])
            self.assertFalse(club_tenure.tracked('other'))

class TransferFixTests(unittest.TestCase):
    def record(self,name,matches,season=18):
        return {'competition':{'name':name,'season':{'name':f'Season {season}'}},'stats':{'nbMatches':matches}}

    def test_public_competition_counts_exclude_friendlies_and_other_seasons(self):
        records=[self.record('Ice League',2),self.record('Cup',1),self.record('Friendly',15),self.record('Pre-season',4),self.record('Ice League',20,17)]
        with patch.object(shared,'_public_get',return_value=records),patch.object(tw.agency,'token',side_effect=AssertionError('Login must not be required')):
            self.assertEqual(tw.player_apps(1,season=18)[0],3)
            self.assertEqual(tw.player_apps(1,season=17)[0],20)

    def test_unknown_stats_are_errors_not_zero(self):
        with patch.object(shared,'_public_get',return_value=[{'stats':{'nbMatches':2}}]):
            with self.assertRaises(ValueError):tw.player_apps(1)
        with patch.object(shared,'_public_get',return_value={'unexpected':'payload'}):
            with self.assertRaises(ValueError):tw.player_apps(1)

    def test_scanner_works_without_auth_refresh_and_retains_errors(self):
        roster=[{'player_id':1,'player_name':'One','club':'Club','overall':70},{'player_id':2,'player_name':'Two','club':'Club','overall':71}]
        with patch.object(shared,'roster_rows',return_value=roster),patch.object(shared,'fetch_clubs',return_value=[{'name':'Club'}]),patch.object(tw.agency,'token',side_effect=AssertionError('No auth')),patch.object(tw,'player_apps',side_effect=[(2,[]),RuntimeError('Read failed')]):
            data,errors,total=tw.candidates('wallet',delay=0,season=18)
            self.assertEqual(total,2);self.assertEqual(len(data),1);self.assertEqual(len(errors),1)
            self.assertEqual(int(data.iloc[0]['Apps']),2)

class RankedTableTests(unittest.TestCase):
    def test_numeric_columns_and_safe_embedding(self):
        from ranked_table import table_html
        markup=table_html(pd.DataFrame([{'Club':'</script>','OVR ↑':2,'PAC':4}]))
        self.assertIn('"sortBy": "OVR ↑"',markup)
        self.assertIn('"numeric": ["OVR ↑", "PAC"]',markup)
        self.assertIn('\\u003c/script>',markup)
