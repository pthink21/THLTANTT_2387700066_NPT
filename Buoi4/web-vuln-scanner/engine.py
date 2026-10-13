from scanners.policy import LabHTTP
from scanners.xss_scanner import XSSScanner
from scanners.sql_injection_tester import SQLInjectionTester
from scanners.csrf_detector import CSRFDetector
from scanners.ssrf_tester import SSRFTester
from report.report_generator import ReportGenerator


def scan(url, options=('xss', 'sql', 'csrf', 'ssrf')):
    http = LabHTTP()
    http.validate(url)
    if len(url) > 4096:
        raise ValueError('URL quá dài')
    results, errors = [], []
    jobs = {
        'xss': lambda: XSSScanner(http).scan(url),
        'sql': lambda: [SQLInjectionTester(http).scan(url), SQLInjectionTester(http).probe(url)],
        'csrf': lambda: CSRFDetector().scan(http.get(url).text),
        'ssrf': lambda: [SSRFTester(http).scan(url), SSRFTester(http).probe(url)],
    }
    try:
        for name in dict.fromkeys(options):
            if name not in jobs:
                raise ValueError('Scanner không hợp lệ')
            try:
                results.append(jobs[name]())
            except (ValueError, OSError) as exc:
                errors.append({'scanner': name, 'error': str(exc)})
    finally:
        http.session.close()
    report = ReportGenerator().generate(results)
    report.update(target=url, errors=errors, complete=not errors)
    return report
