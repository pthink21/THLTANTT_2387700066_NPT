import unittest
from scanners.csrf_detector import CSRFDetector


class TestCSRF(unittest.TestCase):
    def test_token_present(self):
        self.assertTrue(CSRFDetector().scan('<form method="post"><input value="abc" name="csrf_token"></form>')['csrf_protected'])

    def test_missing(self):
        self.assertFalse(CSRFDetector().scan('<form method="POST"><input name="value"></form>')['csrf_protected'])

    def test_empty_token(self):
        self.assertFalse(CSRFDetector().scan('<form method="post"><input name="_csrf" value=""></form>')['csrf_protected'])

    def test_one_of_two_forms_missing(self):
        html = '<form method="post"><input name="_csrf" value="abc"></form><form method="post"></form>'
        self.assertEqual(CSRFDetector().scan(html)['missing_forms'], [1])

    def test_no_state_changing_form(self):
        self.assertIsNone(CSRFDetector().scan('<form method="get"></form>')['csrf_protected'])
