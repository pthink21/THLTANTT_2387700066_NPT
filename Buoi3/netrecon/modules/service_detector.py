import re


class ServiceDetector:
    def detect(self, port, banner):
        if banner.startswith('SSH-'):
            return {'name': 'ssh', 'version': banner.strip().splitlines()[0], 'evidence': 'SSH greeting'}
        if banner.startswith('HTTP/'):
            match = re.search(r'^Server:\s*(.+)$', banner, re.I | re.M)
            return {'name': 'http', 'version': match.group(1).strip() if match else 'undisclosed',
                    'evidence': 'HTTP status line and headers'}
        if banner.startswith('220'):
            name = 'smtp' if re.search(r'SMTP|ESMTP', banner, re.I) else 'ftp' if re.search(r'FTP', banner, re.I) else 'unknown'
            return {'name': name, 'version': banner.strip().splitlines()[0], 'evidence': '220 service greeting'}
        return {'name': 'unknown', 'version': '', 'evidence': 'No recognizable application response'}
