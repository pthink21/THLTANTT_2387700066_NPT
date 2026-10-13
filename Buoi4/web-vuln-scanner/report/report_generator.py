from datetime import datetime, timezone


class ReportGenerator:
    def generate(self, findings_list):
        findings = []
        def flatten(value):
            if isinstance(value, list):
                for item in value:
                    flatten(item)
            elif isinstance(value, dict):
                if value.get('type') == 'CSRF' and value.get('csrf_protected') is not False:
                    return
                findings.append(value)
        flatten(findings_list)
        return {'generated_at': datetime.now(timezone.utc).isoformat(),
                'student': 'Nguyễn Phúc Thịnh', 'student_id': '2387700066',
                'vulnerabilities': findings, 'count': len(findings)}
