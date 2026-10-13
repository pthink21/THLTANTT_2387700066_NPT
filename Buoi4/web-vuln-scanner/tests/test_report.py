import unittest
from report.report_generator import ReportGenerator


class TestReport(unittest.TestCase):
    def test_nested_and_dict(self):
        report = ReportGenerator().generate([[{'type':'XSS'}], {'type':'SQLi'}])
        self.assertEqual(report['count'], 2)

    def test_single_dict(self):
        self.assertEqual(ReportGenerator().generate({'type':'SSRF'})['count'], 1)

    def test_protected_csrf_not_vulnerability(self):
        self.assertEqual(ReportGenerator().generate([{'type':'CSRF','csrf_protected':True}])['count'], 0)
