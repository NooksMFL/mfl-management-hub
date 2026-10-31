import os
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest
import mfl_text

APP = Path(mfl_text.__file__).with_name("app.py")


class MFLTextTests(unittest.TestCase):


    def test_links_preserve_wallet_and_font_is_bundled(self):
        self.assertIn("wallet=0x1234567890", mfl_text.page_link("Squad Builder", "0x1234567890"))
        self.assertTrue(mfl_text.font_url().startswith("data:font/ttf;base64,"))
        self.assertEqual(len(set(mfl_text.PAGES.values())), len(mfl_text.PAGES))
