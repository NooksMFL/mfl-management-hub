import unittest
from wallet_connection import restore_wallet, valid_address


class WalletConnectionTests(unittest.TestCase):
    def test_late_browser_storage_restores_empty_wallet(self):
        session={}
        restore_wallet(session,'',None)
        self.assertEqual(session['wallet'],'')
        session['edit_wallet']=True
        restore_wallet(session,'','0x65cc0e72dd71ad80')
        self.assertEqual(session['wallet'],'0x65cc0e72dd71ad80')
        self.assertFalse(session['edit_wallet'])

    def test_url_takes_precedence_over_saved_wallet_on_load(self):
        session={}
        restore_wallet(session,'0x1111111111111111','0x2222222222222222')
        self.assertEqual(session['wallet'],'0x1111111111111111')

    def test_existing_selection_and_forget_are_respected(self):
        session={'wallet':'0x1111111111111111'}
        restore_wallet(session,'','0x2222222222222222')
        self.assertEqual(session['wallet'],'0x1111111111111111')
        session={'wallet':'','wallet_forgotten':True}
        restore_wallet(session,'','0x2222222222222222')
        self.assertEqual(session['wallet'],'')

    def test_only_flow_addresses_are_accepted_from_wallet_provider(self):
        self.assertTrue(valid_address('0x65CC0E72DD71AD80'))
        for invalid in [None,{},'0x1234','javascript:alert(1)','0x'+'1'*40]:
            self.assertFalse(valid_address(invalid))
