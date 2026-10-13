import unittest
from scanners.sql_injection_tester import SQLInjectionTester


class TestSQL(unittest.TestCase):
    def test_indicator(self):
        results = SQLInjectionTester().scan("http://example.invalid/?id=' OR '1'='1")
        self.assertEqual(results[0]['param'], 'id')
        self.assertEqual(results[0]['confidence'], 'indicator')

    def test_clean(self):
        self.assertEqual(SQLInjectionTester().scan('http://example.invalid/?id=normal'), [])

    def test_dbms_catalog(self):
        self.assertEqual(len(SQLInjectionTester.dbms_payloads), 4)
