import os
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest
import wallet_cache_backend as shared

APP = Path(__file__).resolve().parents[1] / "app.py"


class SquadBuilderPageTests(unittest.TestCase):
    def setUp(self):
        self.previous = os.getcwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)

    def tearDown(self):
        os.chdir(self.previous)
        self.temp.cleanup()

    def page(self, wallet=""):
        at = AppTest.from_file(str(APP), default_timeout=30)
        at.query_params["page"] = "Squad Builder"
        at.session_state["wallet"] = wallet
        return at.run()

    def test_no_wallet_and_empty_wallet(self):
        for wallet in ["", "0x1234567890abcdef"]:
            at = self.page(wallet)
            self.assertFalse(at.exception)
            self.assertTrue(at.info)
            self.assertFalse(at.dataframe)

    def test_build_and_reassign_sixty_rated_squad(self):
        wallet = "0x1234567890abcdef"
        with shared.db() as c:
            c.executemany(
                "INSERT INTO roster(wallet,player_id,player_name,position,overall,club) VALUES(?,?,?,?,?,?)",
                [(wallet,i,f"Player {i}",pos,60,"Test Club") for i,pos in enumerate(["GK"]*2+["LB"]*2+["CB"]*4+["RB"]*2+["CDM"]*2+["CM"]*3+["LW"]*2+["RW"]*2+["ST"]*6)],
            )
            c.execute("INSERT INTO roster(wallet,player_id,player_name,position,overall) VALUES(?,?,?,?,?)",
                      (wallet,999,"Retired player","GK",60))
        at = self.page(wallet)
        self.assertFalse(at.exception)
        self.assertTrue(any(m.label == "Complete squads" and m.value == "1" for m in at.metric))
        self.assertEqual(len(at.dataframe[0].value),25)
        self.assertTrue(any(m.label == "Retired players excluded" and m.value == "1" for m in at.metric))
        self.assertTrue(any("Spark squad 1" in h.value for h in at.subheader))
        control = next(r for r in at.radio if r.label == "Assign 60-rated players to")
        control.set_value("Flint").run()
        self.assertFalse(at.exception)
        self.assertTrue(any("Flint squad 1" in h.value for h in at.subheader))
        self.assertFalse(any("Spark squad 1" in h.value for h in at.subheader))
