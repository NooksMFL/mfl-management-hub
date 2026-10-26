import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from tactics_engine import rating_at, recommend, payload_ratings, FORMATIONS
import wallet_cache_backend as cache
from formation_board import board_html
from squad_builder import build_squads

def p(pid,pos,ovr=70,**extra):return {'player_id':pid,'player':f'Player {pid}','position':pos,'current_ovr':ovr,'club':'Test',**extra}

class TacticsTests(unittest.TestCase):
    def test_habibou_secondary_does_not_inherit_69(self):
        player=p(1,'CM / CDM',69,position_ratings={'CM':69,'CDM':62})
        self.assertEqual(rating_at(player,'RCM')[0],69)
        self.assertEqual(rating_at(player,'CDM')[0],62)
        self.assertEqual(rating_at(player,'CAM')[0],None)
        player.pop('position_ratings')
        self.assertEqual(rating_at(player,'CM'),(69,'First-position OVR fallback'))
        self.assertIsNone(rating_at(player,'CDM')[0])

    def test_manual_priority_and_invalid_values(self):
        player=p(1,'CM / CDM',69,position_ratings='{"CDM":62}',manual_position_ratings={'CDM':64})
        self.assertEqual(rating_at(player,'CDM'),(64,'Entered rating'))
        for value in [None,float('nan'),float('inf'),-1,101,True]:
            self.assertIsNone(rating_at(p(1,'CM',value),'CM')[0])

    def test_explicit_payload_maps_and_lists(self):
        self.assertEqual(payload_ratings({'metadata':{'positionRatings':{'CM':69,'CDM':62}}}),{'CM':69,'CDM':62})
        self.assertEqual(payload_ratings({'positions':[{'position':'CM','rating':69},{'position':'CDM','rating':62}]}),{'CM':69,'CDM':62})
        self.assertEqual(payload_ratings({'positions':['CM','CDM'],'overall':69}),{})

    def test_optimizer_uses_secondary_rating_and_never_duplicates(self):
        players=[p(1,'CM / CDM',69,position_ratings={'CM':69,'CDM':62}),p(2,'CDM',67)]
        for pid,pos in enumerate(['GK','LB','CB','CB','RB','CM','LW','RW','ST'],3):players.append(p(pid,pos))
        result=next(r for r in recommend(players) if r['formation']=='4-3-3 D')
        self.assertEqual(result['lineup']['CDM'],'2')
        self.assertIn('1',result['lineup'].values())
        self.assertEqual(result['filled'],11)
        self.assertEqual(len(set(result['lineup'].values())),11)
        self.assertAlmostEqual(result['average'],(9*70+69+67)/11)

    def test_unknown_and_retired_never_fabricate_complete_xi(self):
        result=recommend([p(1,'CM / CDM',69),p(2,'ST',99,club=None)])
        self.assertEqual(len(result),8)
        for row in result:
            self.assertIsNone(row['average'])
            self.assertNotIn('2',row['lineup'].values())
            self.assertNotIn('CDM',row['lineup'])
        for slots in FORMATIONS.values():self.assertEqual(len(slots),11)

    def test_25_man_roles_use_verified_values(self):
        built,_=build_squads([p(1,'CM / CDM',69,position_ratings={'CM':69,'CDM':62}),p(2,'CDM',67)])
        players=built['Ice'][0]['players']
        self.assertEqual(next(r for r in players if r['player_id']==2)['assigned_role_rating'],67)
        self.assertEqual(next(r for r in players if r['player_id']==1)['assigned_role'],'CM')

    def test_board_payload_safe_and_positional(self):
        markup=board_html([p(1,'CM / CDM',69,position_ratings={'CDM':62},player='</script>')],'key',title='</script>')
        self.assertIn('"CDM": {"value": 62.0',markup)
        self.assertIn('\\u003c/script>',markup)
        self.assertNotIn('"title": "</script>"',markup)

class TacticsCacheTests(unittest.TestCase):
    def test_old_cache_migration_and_manual_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(cache,'DB',os.path.join(tmp,'cache.db')):
            with sqlite3.connect(cache.DB) as c:
                c.execute('CREATE TABLE roster(wallet TEXT, player_id INTEGER, player_name TEXT, club TEXT, age REAL, position TEXT, overall REAL, pace REAL, shooting REAL, passing REAL, dribbling REAL, defense REAL, physical REAL, cached_at TEXT,PRIMARY KEY(wallet,player_id))')
                c.execute("INSERT INTO roster(wallet,player_id,position,overall) VALUES('wallet',1,'CM / CDM',69)")
            rows=cache.roster_rows('wallet');self.assertEqual(rows[0]['overall'],69)
            self.assertIn('position_ratings',rows[0])
            cache.save_tactics_ratings('WALLET',1,{'CM':69,'CDM':62})
            self.assertEqual(cache.tactics_ratings('wallet')[1]['CDM']['rating'],62)
            cache.save_tactics_ratings('wallet',1,{})
            self.assertFalse(cache.tactics_ratings('wallet'))

    def test_refreshed_roster_retains_explicit_secondary_ratings(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(cache,'DB',os.path.join(tmp,'cache.db')):
            payload=[{'id':1,'name':'Habibou','metadata':{'positions':['CM','CDM'],'overall':69,'positionRatings':{'CM':69,'CDM':62}},'club':{'name':'Club'}}]
            with patch.object(cache,'_public_get',return_value=payload):
                restored=cache.roster_payload('wallet',force=True)
            self.assertEqual(json.loads(cache.roster_rows('wallet')[0]['position_ratings']),{'CM':69.0,'CDM':62.0})
            self.assertEqual(restored[0]['metadata']['positionRatings']['CDM'],62)
