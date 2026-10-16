import json
import os
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest
from design_studio import ROOT, embedded_concept


class DesignStudioTests(unittest.TestCase):
    def test_six_self_contained_concepts(self):
        concepts = json.loads((ROOT / "concepts.json").read_text())
        self.assertEqual(len(concepts), 6)
        for concept in concepts:
            html = embedded_concept(concept["slug"])
            self.assertIn("data:font/ttf;base64,", html)
            self.assertNotIn("url(assets/", html)
            self.assertIn('id="league"', html)
            self.assertNotIn('href="index.html"', html)
        with self.assertRaises(ValueError):
            embedded_concept("../app")

    def test_page_previews_without_a_wallet(self):
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            os.chdir(temp)
            try:
                at = AppTest.from_file(str(Path(ROOT).parent / "app.py"), default_timeout=30)
                at.query_params["page"] = "Design Studio"
                at.session_state["wallet"] = ""
                at.run()
                self.assertFalse(at.exception)
                self.assertEqual(at.title[0].value, "Design Studio")
                selector = next(s for s in at.selectbox if s.label == "Design concept")
                self.assertEqual(len(selector.options), 6)
                for i in range(1, 6):
                    selector.set_value(i).run()
                    self.assertFalse(at.exception)
                    selector = next(s for s in at.selectbox if s.label == "Design concept")
            finally:
                os.chdir(previous)
