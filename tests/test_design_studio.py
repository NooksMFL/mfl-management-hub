import json
import os
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest
from design_studio import ROOT, embedded_concept


class DesignStudioTests(unittest.TestCase):
    def test_thirty_one_self_contained_concepts(self):
        concepts = json.loads((ROOT / "concepts.json").read_text())
        self.assertEqual(len(concepts), 31)
        self.assertEqual(sum(c.get("collection") == "Fresh fifteen" for c in concepts),15)
        self.assertEqual(sum(c.get("collection") == "Wild collection" for c in concepts), 10)
        for concept in concepts:
            html = embedded_concept(concept["slug"])
            self.assertIn("data:font/ttf;base64,", html)
            self.assertNotIn("url(assets/", html)
            self.assertIn('id="league"', html)
            self.assertNotIn('href="index.html"', html)
            self.assertNotIn('href="wild-index.html"', html)
            self.assertNotIn('href="fresh-index.html"', html)
        with self.assertRaises(ValueError):
            embedded_concept("../app")
