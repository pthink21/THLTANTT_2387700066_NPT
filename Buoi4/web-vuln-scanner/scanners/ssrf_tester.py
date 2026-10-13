import ipaddress
from urllib.parse import parse_qs, urlsplit, urlencode, urlunsplit
from scanners.policy import LabHTTP


class SSRFTester:
    def __init__(self, http=None):
        self.http = http or LabHTTP()

    def scan(self, url):
        findings = []
        for param, values in parse_qs(urlsplit(url).query).items():
            for value in values:
                p = urlsplit(value)
                host = p.hostname or ''
                try:
                    internal = not ipaddress.ip_address(host).is_global
                except ValueError:
                    internal = host.lower() == 'localhost'
                if p.scheme in {'http', 'https'} and internal:
                    findings.append(dict(type='SSRF', param=param, value=value, risk='HIGH',
                                         confidence='indicator', desc='Potential SSRF: URL nội bộ trong tham số.',
                                         remediation='Allowlist đích, kiểm tra IP sau DNS và mọi redirect, chặn metadata.'))
        return findings

    def probe(self, url):
        self.http.validate(url)
        p = urlsplit(url)
        query = parse_qs(p.query, keep_blank_values=True)
        # This nonce marker exists only on the isolated internal fixture.
        param = 'url'
        query[param] = ['http://127.0.0.1:5103/internal-proof']
        response = self.http.get(urlunsplit(p._replace(query=urlencode(query, doseq=True))))
        if 'LAB04-INTERNAL-PROOF-2387700066' in response.text:
            return [dict(type='SSRF', param=param, risk='HIGH', confidence='behavioral',
                         desc='Server đã lấy được marker từ dịch vụ nội bộ 5103.',
                         evidence='LAB04-INTERNAL-PROOF-2387700066',
                         remediation='Không cho phép loopback/private/link-local; allowlist URL và không follow redirect.')]
        return []
