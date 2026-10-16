import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from streamlit.testing.v1 import AppTest
import valuation_backend as v
import wallet_cache_backend as shared


def listing(pid, price, age=24, ovr=70, currency='USD'):
    return {'player_id':str(pid),'player':f'Comparable {pid}','age':age,'overall':ovr,
            'position':'CM','price':price,'currency':currency,'listing_id':str(pid)}


def player(pid=1, **changes):
    return {'player_id':pid,'player':'Agency player','age':24,'current_ovr':70,'position':'CM','club':'Test Club',**changes}


class ValuationTests(unittest.TestCase):
    def test_median_range_and_agency_asks_excluded(self):
        refs=[listing(i+10,price) for i,price in enumerate([10,20,30,40,50])]
        refs.append(listing(1,99999))
        rows,evidence=v.value_agency([player(),player()],refs,'USD')
        self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]['Estimate'],rows[0]['Lower ask'],rows[0]['Upper ask']),(30,20,40))
        self.assertEqual(rows[0]['Comparables'],5)
        self.assertEqual(len(evidence['1']),5)

    def test_unpriced_not_zero_and_currency_separation(self):
        refs=[listing(i+10,100,currency='EUR') for i in range(10)]
        rows,_=v.value_agency([player()],refs,'USD')
        self.assertIsNone(rows[0]['Estimate'])
        self.assertEqual(rows[0]['Comparables'],0)

    def test_broader_comparisons_labelled(self):
        rows,_=v.value_agency([player()],[listing(i+10,100+i,age=28,ovr=74) for i in range(5)],'USD')
        self.assertEqual(rows[0]['Match'],'Broader')
        self.assertEqual(rows[0]['Estimate'],102)

    def test_retired_missing_metadata_and_position_mismatch(self):
        refs=[listing(i+10,100) for i in range(10)]
        rows,_=v.value_agency([player(club=None),player(2,age=None),player(3,position='GK')],refs,'USD')
        self.assertEqual(rows[0]['Status'],'Retired / no current club')
        self.assertEqual(rows[1]['Status'],'Missing age, rating or position')
        self.assertTrue(all(r['Estimate'] is None for r in rows))

    def test_normalization_deduplicates_and_rejects_invalid_prices(self):
        def raw(pid,price,status='AVAILABLE'):
            return {'id':pid,'status':status,'price':price,'player':{'id':pid,'metadata':{'age':24,'overall':70,'positions':['CM']}}}
        normalized=v.normalize_listings([raw(1,10),raw(1,20),raw(2,float('nan')),raw(3,0),raw(4,10,'BOUGHT')])
        self.assertEqual(len(normalized),1)
        self.assertEqual(normalized[0]['currency'],'MARKET UNITS')

    def test_fetch_saves_snapshot_and_failure_preserves_it(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(v,'DB',str(Path(temp)/'cache.db')):
            self.assertIsNone(v.load_market())
            response=Mock(ok=True)
            response.json.return_value=[{'id':10,'status':'AVAILABLE','price':100,'player':{'id':10,'metadata':{'age':24,'overall':70,'positions':['CM']}}}]
            with patch.object(v.requests,'get',return_value=response):
                snapshot=v.fetch_market(pages=1)
            self.assertEqual(v.load_market(),snapshot)
            with patch.object(v.requests,'get',return_value=Mock(ok=False,status_code=403)):
                with self.assertRaisesRegex(RuntimeError,'403'):
                    v.fetch_market(pages=1)
            self.assertEqual(v.load_market(),snapshot)

    def test_ui_from_saved_market_and_partial_total(self):
        previous=os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            os.chdir(temp)
            try:
                wallet='0x1234567890abcdef'
                with shared.db() as conn:
                    conn.executemany('INSERT INTO roster(wallet,player_id,player_name,age,position,overall,club) VALUES(?,?,?,?,?,?,?)',
                                     [(wallet,1,'Priced player',24,'CM',70,'Test Club'),(wallet,2,'Unpriced keeper',24,'GK',70,'Test Club')])
                snapshot={'captured_at':'2026-10-16T12:00:00+00:00','records_scanned':5,'listings':[listing(i+10,100+i) for i in range(5)]}
                with patch.object(v,'load_market',return_value=snapshot):
                    at=AppTest.from_file(str(Path(v.__file__).with_name('app.py')),default_timeout=30)
                    at.query_params['page']='Agency / Player Valuation';at.session_state['wallet']=wallet;at.run()
                    self.assertFalse(at.exception)
                    self.assertTrue(any(m.label=='Priced-player subtotal' and m.value=='102.00' for m in at.metric))
                    self.assertTrue(any(m.label=='Valuation coverage' and m.value=='1/2 active players' for m in at.metric))
                    select=next(s for s in at.selectbox if s.label=='Player to inspect')
                    select.set_value('Unpriced keeper · 2').run()
                    self.assertFalse(at.exception)
                    self.assertTrue(any('Insufficient comparables' in i.value for i in at.info))
            finally:
                os.chdir(previous)
