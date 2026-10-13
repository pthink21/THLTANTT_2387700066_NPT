import unittest
from scanners.ssrf_tester import SSRFTester


class TestSSRF(unittest.TestCase):
    def test_internal(self):
        self.assertEqual(SSRFTester().scan('http://example.invalid/?url=http://127.0.0.1/admin')[0]['type'], 'SSRF')

    def test_metadata(self):
        self.assertTrue(SSRFTester().scan('http://example.invalid/?url=http://169.254.169.254/'))

    def test_ipv6(self):
        self.assertTrue(SSRFTester().scan('http://example.invalid/?url=http://[::1]/'))

    def test_hostname_substring_not_internal(self):
        self.assertEqual(SSRFTester().scan('http://example.invalid/?url=http://localhost.evil.invalid/'), [])

    def test_public(self):
        self.assertEqual(SSRFTester().scan('http://example.invalid/?url=https://example.com/'), [])
