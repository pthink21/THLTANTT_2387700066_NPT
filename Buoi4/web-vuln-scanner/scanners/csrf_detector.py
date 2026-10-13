from bs4 import BeautifulSoup


class CSRFDetector:
    token_names = {'csrf_token', '_csrf', 'csrfmiddlewaretoken'}

    def scan(self, html_content):
        forms = BeautifulSoup(html_content, 'html.parser').find_all('form')
        missing = []
        checked = 0
        for index, form in enumerate(forms):
            if form.get('method', 'get').lower() not in {'post', 'put', 'patch', 'delete'}:
                continue
            checked += 1
            token = any(i.get('name', '').lower() in self.token_names and i.get('value')
                        for i in form.find_all('input'))
            if not token:
                missing.append(index)
        return dict(type='CSRF', csrf_protected=(not missing if checked else None),
                    forms_checked=checked, missing_forms=missing, risk='MEDIUM',
                    confidence='indicator',
                    desc=('No CSRF token found: potentially vulnerable to CSRF; cần kiểm tra server, cookie và Origin.'
                          if missing else 'Có token trên form thay đổi trạng thái.' if checked
                          else 'Không có form thay đổi trạng thái; chưa đủ dữ kiện.'),
                    remediation='Xác thực CSRF token phía server, SameSite cookie, kiểm tra Origin.')
