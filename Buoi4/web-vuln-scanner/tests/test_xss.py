import unittest
from unittest.mock import Mock
from scanners.xss_scanner import XSSScanner
from urllib.parse import parse_qs, urlsplit


class TestXSS(unittest.TestCase):
    def test_reflection_preserves_query(self):
        http = Mock()
        def reflect(url):
            params = parse_qs(urlsplit(url).query)
            return Mock(text=params.get('q', [''])[0], headers={'Content-Type':'text/html'})
        http.get.side_effect = reflect
        result = XSSScanner(http).scan('http://127.0.0.1:5102/page?id=1&q=normal')
        self.assertEqual(len(result), 2)
        self.assertEqual(parse_qs(urlsplit(result[0]['url']).query)['id'], ['1'])

    def test_escaped_no_finding(self):
        http = Mock()
        http.get.return_value = Mock(text='&lt;script&gt;', headers={'Content-Type':'text/html'})
        self.assertEqual(XSSScanner(http).scan('http://127.0.0.1:5102/page'), [])

    def test_non_html_no_finding(self):
        http = Mock()
        http.get.return_value = Mock(text='<script>alert(1)</script>', headers={'Content-Type':'application/json'})
        self.assertEqual(XSSScanner(http).scan('http://127.0.0.1:5102/page'), [])
