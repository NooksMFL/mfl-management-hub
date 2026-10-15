import unittest

from squad_builder import QUOTAS, build_squads, league_for


def player(pid, position, rating=70):
    return {"player_id": pid, "player": f"Player {pid}", "position": position, "current_ovr": rating, "club": "Test Club"}


class SquadBuilderTests(unittest.TestCase):
    def test_boundaries_and_sixty_overlap(self):
        self.assertEqual([league_for(x) for x in [59,60,66,67,72,73,99]],
                         ["Flint","Spark","Spark","Ice","Ice","Stone","Stone"])
        self.assertEqual(league_for(60,"Flint"),"Flint")
        for value in [None,"unknown",float("nan"),float("inf"),-1]:
            self.assertIsNone(league_for(value))

    def test_two_complete_squads_with_no_duplicates(self):
        records=[]
        for position,count in [("GK",4),("LB",4),("CB",8),("RB",4),("CDM",4),("CM",6),("LW",4),("RW",4),("ST",12)]:
            start=len(records)
            records.extend(player(start+i,position,71 if i%2 else 68) for i in range(count))
        built,excluded=build_squads(records)
        self.assertFalse(excluded)
        self.assertEqual(len(built["Ice"]),2)
        for squad in built["Ice"]:
            self.assertEqual(len(squad["players"]),25)
            self.assertFalse(squad["shortages"])
            for role,count in QUOTAS.items():
                self.assertEqual(sum(p["assigned_role"]==role for p in squad["players"]),count)
        ids=[p["player_id"] for squad in built["Ice"] for p in squad["players"]]
        self.assertEqual(len(set(ids)),50)
        totals=[sum(p["current_ovr"] for p in squad["players"]) for squad in built["Ice"]]
        self.assertGreater(totals[0],totals[1])

    def test_versatile_player_preserves_specialist_slot(self):
        records=[player(0,"CB / CM",72)]
        for pos,count in [("GK",2),("LB",2),("CB",4),("RB",2),("CDM",2),("CM",2),("LW",4),("ST",6)]:
            start=len(records)
            records.extend(player(start+i,pos) for i in range(count))
        squad=build_squads(records)[0]["Ice"][0]
        self.assertFalse(squad["shortages"])
        self.assertEqual(next(p for p in squad["players"] if p["player_id"]==0)["assigned_role"],"CM")

    def test_shortages_are_not_filled_out_of_position(self):
        built,_=build_squads([player(i,"CB") for i in range(25)])
        self.assertEqual([len(s["players"]) for s in built["Ice"]],[10,10,5])
        self.assertEqual(built["Ice"][0]["shortages"],{"Goalkeeper":2,"LB":2,"RB":2,"CDM":2,"CM":3,"Winger":4})

    def test_required_positions_take_priority_over_flexible_places(self):
        built,_=build_squads([player(1,"LB",70),player(2,"CM",70),player(3,"ST",72)])
        assigned={p["player_id"]:p["assigned_role"] for p in built["Ice"][0]["players"]}
        self.assertEqual(assigned,{1:"LB",2:"CM",3:"Additional outfield"})

    def test_position_aliases(self):
        from squad_builder import position_groups
        for position,role in [("LWB","LB"),("RWB","RB"),("DM","CDM"),("LM","Winger"),("RW","Winger")]:
            self.assertIn(role,position_groups(position))

    def test_deduplicates_excludes_unknown_and_separates_leagues(self):
        built,excluded=build_squads([player(1,"GK",73),player(1,"GK",73),player(2,"???"),player(3,"CM",None),player(4,"ST",60)])
        self.assertFalse(built["Stone"])
        self.assertEqual(len(excluded),2)
        self.assertEqual(len(built["Spark"][0]["players"]),2)
        self.assertFalse(built["Flint"])

    def test_empty_input(self):
        built,excluded=build_squads([])
        self.assertTrue(all(not squads for squads in built.values()))
        self.assertFalse(excluded)

    def test_goalkeepers_cross_bands_and_surplus_is_filtered(self):
        records=[player(1,"CB",75),player(2,"CB",69)]
        records += [player(i+10,"GK",rating) for i,rating in enumerate([72,70,66,63,55])]
        built,excluded=build_squads(records)
        stone=[p["current_ovr"] for p in built["Stone"][0]["players"] if p["assigned_role"]=="Goalkeeper"]
        ice=[p["current_ovr"] for p in built["Ice"][0]["players"] if p["assigned_role"]=="Goalkeeper"]
        self.assertEqual(stone,[72,66])
        self.assertEqual(ice,[70,63])
        self.assertEqual(len(excluded),1)
        self.assertIn("Surplus goalkeeper",excluded[0]["reason"])
        self.assertFalse(built["Spark"])
        self.assertFalse(built["Flint"])

    def test_scarce_keepers_cover_starters_before_backups(self):
        built,_=build_squads([player(1,"CB",75),player(2,"CB",69),player(3,"GK",72),player(4,"GK",70)])
        for league in ["Stone","Ice"]:
            self.assertEqual(sum(p["assigned_role"]=="Goalkeeper" for p in built[league][0]["players"]),1)
            self.assertEqual(built[league][0]["shortages"]["Goalkeeper"],1)

    def test_retired_players_are_excluded_from_every_league(self):
        records=[{**player(i,"GK",rating),"club":club} for i,(rating,club) in enumerate([
            (75,None),(70,""),(63,"   "),(55,float("nan")),(70,"Retired"),(70,"No club")])]
        records.extend([player(99,"GK",70),player(100,"CB",70)])
        built,excluded=build_squads(records)
        self.assertEqual(len(excluded),6)
        self.assertTrue(all(p["reason"]=="Retired / no current club" for p in excluded))
        self.assertEqual([p["player_id"] for s in built["Ice"] for p in s["players"]],[99,100])


if __name__ == "__main__":
    unittest.main()
