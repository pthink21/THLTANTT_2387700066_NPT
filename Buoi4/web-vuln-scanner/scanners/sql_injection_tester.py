from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from scanners.policy import LabHTTP


class SQLInjectionTester:
    payloads = ["' OR '1'='1", "' OR 1=1--", "' UNION SELECT NULL--"]
    dbms_payloads = {
        'SQLite': ["' OR 1=1--", "' UNION SELECT NULL--"],
        'MySQL': ["' OR 1=1#"],
        'PostgreSQL': ["' OR TRUE--"],
        'MSSQL': ["' OR 1=1--"],
    }
    error_markers = ['sqlite3.operationalerror', 'sql syntax', 'unterminated quoted string',
                     'unclosed quotation mark', 'you have an error in your sql']

    def __init__(self, http=None):
        self.http = http or LabHTTP()

    def scan(self, url):
        """Static indicators, matching the PDF interface; never proves execution."""
        findings = []
        for param, values in parse_qs(urlsplit(url).query).items():
            for value in values:
                for payload in self.payloads:
                    if payload.lower() in value.lower():
                        findings.append(dict(type='SQLi', param=param, payload=payload,
                                             desc='Potential SQL Injection: mẫu SQL trong đầu vào.',
                                             risk='CRITICAL', confidence='indicator',
                                             remediation='Dùng parameterized queries; không ghép chuỗi SQL.'))
        return findings

    def probe(self, url):
        self.http.validate(url)
        p = urlsplit(url)
        params = parse_qs(p.query, keep_blank_values=True) or {'id': ['1']}
        findings = []
        for param in list(params)[:8]:
            def response_for(value):
                query = dict(params)
                query[param] = [value]
                return self.http.get(urlunsplit(p._replace(query=urlencode(query, doseq=True))))
            baseline = self.http.get(url)
            yes, no = response_for('1 OR 1=1'), response_for('1 AND 1=2')
            try:
                b, y, n = baseline.json(), yes.json(), no.json()
                differential = (isinstance(b, list) and isinstance(y, list) and isinstance(n, list)
                                and len(y) > len(b) > len(n))
            except ValueError:
                differential = False
            quote = response_for("'")
            errors = [m for m in self.error_markers if m in quote.text.lower()
                      and m not in baseline.text.lower()]
            if differential or errors:
                findings.append(dict(type='SQLi', param=param, risk='CRITICAL',
                                     confidence='behavioral', payload='1 OR 1=1 / 1 AND 1=2',
                                     desc='SQL Injection: khác biệt true/false hoặc lỗi SQL mới xuất hiện.',
                                     evidence={'boolean_differential': differential, 'errors': errors},
                                     remediation='Dùng prepared statements, hạn chế quyền DB, ẩn lỗi SQL.'))
        return findings
