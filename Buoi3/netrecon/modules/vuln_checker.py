class VulnChecker:
    """Evidence-based configuration checks; no CVE conclusion from port numbers."""
    def check(self, services):
        findings = []
        for service in services:
            port, name, banner = service['port'], service['name'], service.get('banner', '')
            if name in ('ftp', 'telnet') or port == 23:
                findings.append({'port': port, 'severity': 'medium', 'title': 'Potential plaintext protocol',
                    'evidence': service['evidence'], 'recommendation': 'Use SSH/SFTP or TLS and verify configuration.',
                    'confirmed_cve': False})
            if name == 'http':
                headers = banner.lower()
                if 'x-content-type-options:' not in headers:
                    findings.append({'port': port, 'severity': 'low', 'title': 'Missing X-Content-Type-Options',
                        'evidence': 'Header absent from sampled HEAD response',
                        'recommendation': 'Set X-Content-Type-Options: nosniff.', 'confirmed_cve': False})
                if service['version'] != 'undisclosed':
                    findings.append({'port': port, 'severity': 'info', 'title': 'Server version disclosed',
                        'evidence': service['version'], 'recommendation': 'Reduce unnecessary version information.',
                        'confirmed_cve': False})
        return findings
