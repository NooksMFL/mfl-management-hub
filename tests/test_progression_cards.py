import io
import unittest
from PIL import Image
from progression_cards import create_card, delta

class ProgressionCardTests(unittest.TestCase):
    def test_signed_changes_and_missing_values(self):
        self.assertEqual(delta(0), '+0')
        self.assertEqual(delta(3), '+3')
        self.assertEqual(delta(-2), '-2')
        for missing in (None, float('nan'), float('inf'), 'unknown'):
            self.assertEqual(delta(missing), '—')

    def test_export_is_high_resolution_transparent_png_without_photo(self):
        card=create_card({'player':'A very long player name for readable fitting','ovr_gain':2,'pac':1,'sho':None,'dri':-1})
        image=Image.open(io.BytesIO(card))
        self.assertEqual(image.size,(720,1080))
        self.assertEqual(image.mode,'RGBA')
        self.assertEqual(image.getpixel((0,0))[3],0)

    def test_invalid_portrait_still_exports(self):
        self.assertTrue(create_card({'player':'Test'},b'invalid image').startswith(b'\x89PNG'))
