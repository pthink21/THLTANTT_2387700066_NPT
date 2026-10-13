import unittest
from unittest.mock import patch, Mock
from scanners.policy import LabHTTP


class TestPolicy(unittest.TestCase):
    def test_local_target(self):
        self.assertEqual(LabHTTP().validate('http://127.0.0.1:5102/page'), 'http://127.0.0.1:5102/page')

    def test_external_blocked(self):
        for url in ['http://example.com/', 'http://127.0.0.1:5101/', 'file:///C:/Windows',
                    'http://127.0.0.1.evil.invalid:5102/', 'http://user:pass@127.0.0.1:5102/']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                LabHTTP().validate(url)

    def test_redirect_blocked(self):
        http = LabHTTP()
        response = Mock(status_code=302)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch.object(http.session, 'get', return_value=response):
            with self.assertRaises(ValueError):
                http.get('http://127.0.0.1:5102/redirect')
