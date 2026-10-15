import unittest

from squad_cards import age_label, roster_html
from formation_board import board_html


class PlayerCardTests(unittest.TestCase):
    def test_missing_age_and_escaped_player_data(self):
        player = {"player_id": 326522, "player": "<script>bad</script>",
                  "position": "GK", "age": 23, "club": "Club & City",
                  "current_ovr": 72, "assigned_role": "Goalkeeper"}
        markup = roster_html([player])
        self.assertIn("Age 23", markup)
        self.assertIn("/326522/photo.webp", markup)
        self.assertIn("&lt;script&gt;", markup)
        self.assertNotIn("<script>", markup)
        self.assertIn('"age": "23"', board_html([player], "test"))
        for age in [None, float("nan"), "", 0]:
            self.assertEqual(age_label(age), "—")
