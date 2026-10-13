import unittest
from unittest.mock import patch
from ui.app import create_app


class TestUI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_index_template(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Bắt đầu kiểm thử', response.get_data(as_text=True))

    def test_missing_csrf(self):
        self.assertEqual(self.client.post('/', data={'url':'http://127.0.0.1:5102/page'}).status_code, 403)

    def test_result_template_escapes_payload(self):
        self.client.get('/')
        with self.client.session_transaction() as s:
            token = s['csrf']
        report = dict(count=1, target='lab', generated_at='now', complete=True, errors=[],
                      vulnerabilities=[dict(type='XSS', risk='HIGH', confidence='candidate', desc='lab',
                                            payload='<script>alert(1)</script>', remediation='escape')])
        with patch('ui.app.scan', return_value=report):
            response = self.client.post('/', data={'url':'http://127.0.0.1:5102/page', 'csrf_token':token, 'scanner':'xss'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('&lt;script&gt;', response.get_data(as_text=True))
        self.assertNotIn('<script>alert', response.get_data(as_text=True))
