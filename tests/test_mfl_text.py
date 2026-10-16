import os
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest
import mfl_text

APP = Path(mfl_text.__file__).with_name("app.py")


class MFLTextTests(unittest.TestCase):
    def test_every_numbered_page_renders_without_a_wallet(self):
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            os.chdir(temp)
            try:
                for page, number in mfl_text.PAGES.items():
                    with self.subTest(page=page):
                        at = AppTest.from_file(str(APP), default_timeout=30)
                        at.query_params["page"] = page
                        at.session_state["wallet"] = ""
                        at.run()
                        self.assertFalse(at.exception)
                        markup = "".join(m.value for m in at.markdown)
                        self.assertIn(f'data-page="{number}"', markup)
            finally:
                os.chdir(previous)

    def test_page_number_and_radio_navigation(self):
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as temp:
            os.chdir(temp)
            try:
                at = AppTest.from_file(str(APP), default_timeout=30)
                at.session_state["wallet"] = ""
                at.run()
                at.text_input(key="tt_page_number").set_value("302").run()
                self.assertFalse(at.exception)
                self.assertEqual(at.radio(key="hub_nav").value, "Squad Builder")
                at.radio(key="hub_nav").set_value("Compare").run()
                self.assertEqual(at.query_params["page"], ["Compare"])
                at.text_input(key="tt_page_number").set_value("777").run()
                self.assertEqual(at.radio(key="hub_nav").value, "Compare")
                self.assertIn("PAGE NOT FOUND",at.session_state["tt_page_error"])
            finally:
                os.chdir(previous)

    def test_links_preserve_wallet_and_font_is_bundled(self):
        self.assertIn("wallet=0x1234567890", mfl_text.page_link("Squad Builder", "0x1234567890"))
        self.assertTrue(mfl_text.font_url().startswith("data:font/ttf;base64,"))
        self.assertEqual(len(set(mfl_text.PAGES.values())), len(mfl_text.PAGES))
