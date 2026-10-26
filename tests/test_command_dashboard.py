import unittest
from command_dashboard import roster_html, sort_players

class DashboardTests(unittest.TestCase):
    def test_roster_uses_actual_data_and_escapes_names(self):
        markup=roster_html([{'player_id':7,'player_name':'<script>Example</script>','position':'CM / CDM','overall':69,'age':26}],'wallet',total=15)
        self.assertIn('&lt;script&gt;',markup)
        self.assertNotIn('<script>',markup)
        self.assertIn('/7/photo.webp',markup)
        self.assertIn('14 more in My agency',markup)
        self.assertIn('midfielder',markup)
        self.assertIn('>69<',markup)

    def test_limit_and_sort_missing_values(self):
        players=[{'player_id':i,'player_name':str(i),'overall':i,'position':'CB'} for i in range(20)]
        self.assertEqual(roster_html(players,'wallet').count('<article'),12)
        players=[{'player_id':1,'overall':None},{'player_id':2,'overall':float('nan')},{'player_id':3,'overall':71}]
        self.assertEqual(sort_players(players)[0]['player_id'],3)
