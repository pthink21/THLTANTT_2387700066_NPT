from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from scanners.policy import LabHTTP


class XSSScanner:
    payloads = ['<script>alert(1)</script>', '"><svg/onload=alert(1)>']

    def __init__(self, http=None):
        self.http = http or LabHTTP()

    def scan(self, url):
        self.http.validate(url)
        p = urlsplit(url)
        params = parse_qs(p.query, keep_blank_values=True) or {'q': ['']}
        params.setdefault('q', [''])
        results = []
        for param in list(params)[:8]:
            for payload in self.payloads:
                probe = dict(params)
                probe[param] = [payload]
                test_url = urlunsplit(p._replace(query=urlencode(probe, doseq=True)))
                response = self.http.get(test_url)
                if 'text/html' in response.headers.get('Content-Type', '') and payload in response.text:
                    results.append(dict(type='XSS', param=param, payload=payload,
                                        url=test_url, risk='HIGH', confidence='candidate',
                                        desc='Payload được phản chiếu nguyên dạng trong HTML; cần xác minh thực thi trong trình duyệt.',
                                        remediation='Escape đầu ra theo ngữ cảnh, dùng textContent và CSP.'))
        return results
