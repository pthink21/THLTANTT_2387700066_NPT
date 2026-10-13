"""Real CMD windows and visible Chrome; capture live executed commands/pages."""
import hashlib
import json
from pathlib import Path
import sys
import time
from PIL import ImageGrab
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_cmd import launch, BASE, USER, window


def main():
    (BASE / 'working').mkdir(exist_ok=True)
    (BASE / 'screenshots').mkdir(exist_ok=True)
    python = f'"{sys.executable}" -X utf8'
    launch('FIVE LIVE LAB SERVICES', python + ' -u run_lab.py serve', '01', '01-cmd-services.png', live=True)
    launch('WEB SCANNER UNITTEST', python + ' -m unittest discover -s web-vuln-scanner\\tests -t web-vuln-scanner', '02', '02-cmd-scanner-unittest.png')
    launch('JWT PYTEST', python + ' -m pytest jwt-security-tools\\tests -q -c jwt-security-tools\\pytest.ini --basetemp working\\cmd-pytest-' + str(time.time_ns()), '03', '03-cmd-jwt-pytest.png')
    launch('SCANNER CLI SQL INJECTION', python + ' web-vuln-scanner\\main.py --url "http://127.0.0.1:5102/items?id=1" --scanners sql --summary --output evidence\\cmd-sql-report.json', '04', '04-cmd-scanner-cli.png')
    launch('JWT OAUTH CSRF RACE INTEGRATION', python + ' run_lab.py demo', '05', '05-cmd-integration.png')
    curl = 'curl.exe -sS -w " HTTP_STATUS=%{http_code}\\n"'
    launch('CURL JWT AUTHENTICATION', '\n'.join([
        'echo Valid access token from local excluded config:',
        'echo curl.exe --config runtime\\access.curl http://127.0.0.1:5101/protected',
        curl + ' --config runtime\\access.curl http://127.0.0.1:5101/protected',
        'echo.', 'echo Missing token:',
        'echo curl.exe http://127.0.0.1:5101/protected',
        curl + ' http://127.0.0.1:5101/protected',
        'echo.', 'echo Invalid token:',
        'echo curl.exe -H "Authorization: Bearer invalid-lab-token" http://127.0.0.1:5101/protected',
        curl + ' -H "Authorization: Bearer invalid-lab-token" http://127.0.0.1:5101/protected',
        'echo.', 'echo CSRF vulnerable fixture without token:',
        'echo curl.exe -X POST -d "value=lab" http://127.0.0.1:5102/change',
        curl + ' -X POST -d "value=lab" http://127.0.0.1:5102/change',
        'echo.', 'echo CSRF protected fixture without token:',
        'echo curl.exe -X POST -d "value=lab" http://127.0.0.1:5102/safe-change',
        curl + ' -X POST -d "value=lab" http://127.0.0.1:5102/safe-change',
    ]).replace('%{http_code}', '%%{http_code}'), '06', '06-cmd-curl-auth-csrf.png')
    launch('VALIDATION AND SECURITY REVIEW', python + ' tools\\validate.py', '07', '07-cmd-validation-bandit.png')
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=False, args=['--start-maximized'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.goto('http://127.0.0.1:5100/')
        page.screenshot(path=str(BASE / 'screenshots/08-web-scanner.png'), full_page=True)

        def submit(url, options, filename):
            page.goto('http://127.0.0.1:5100/')
            page.locator('[name=url]').fill(url)
            for name in ['xss', 'sql', 'csrf', 'ssrf']:
                box = page.locator(f'input[name=scanner][value={name}]')
                box.set_checked(name in options)
            page.get_by_role('button', name='Bắt đầu kiểm thử').click()
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(BASE / 'screenshots' / filename), full_page=True)
            return page.content()

        html = submit('http://127.0.0.1:5102/page?id=1', ['xss','csrf'], '09-web-xss-csrf.png')
        results['web_xss_csrf_report'] = 'CSRF' in html and 'Payload được phản chiếu' in html
        html = submit('http://127.0.0.1:5102/items?id=1', ['sql'], '10-web-sql-injection.png')
        results['web_sqli_report'] = 'boolean_differential' in html
        html = submit('http://127.0.0.1:5102/fetch?url=', ['ssrf'], '11-web-ssrf.png')
        results['web_ssrf_report'] = 'LAB04-INTERNAL-PROOF' in html
        html = submit('http://127.0.0.1:5102/safe?id=1', ['xss','csrf'], '12-web-safe-fixture.png')
        results['web_safe_fixture'] = '0 phát hiện' in html
        html = submit('http://192.0.2.1/', ['xss'], '13-web-scope-blocked.png')
        results['web_scope_blocked'] = 'Chỉ cho phép' in html
        page.goto('http://127.0.0.1:5100/evidence')
        page.screenshot(path=str(BASE / 'screenshots/14-web-jwt-oauth-results.png'), full_page=True)
        page.bring_to_front()
        hwnd = window(page.title())
        if not hwnd:
            raise RuntimeError('Không tìm thấy cửa sổ Chrome để chụp desktop')
        USER.ShowWindow(hwnd, 3)
        USER.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
        USER.SetForegroundWindow(hwnd)
        time.sleep(0.8)
        ImageGrab.grab().save(BASE / 'screenshots/15-desktop-live-browser.png')
        USER.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)
        # Verify actual execution, not just reflection.
        xss = context.new_page()
        xss.on('dialog', lambda dialog: (results.update(xss_browser_dialog=dialog.message), dialog.accept()))
        xss.goto('http://127.0.0.1:5102/page?q=%3Cscript%3Ealert(1)%3C/script%3E')
        xss.wait_for_timeout(500)
        results['xss_browser_executed'] = results.get('xss_browser_dialog') == '1'
        safe = context.new_page()
        safe_dialogs = []
        safe.on('dialog', lambda dialog: (safe_dialogs.append(dialog.message), dialog.accept()))
        safe.goto('http://127.0.0.1:5102/safe?q=%3Cscript%3Ealert(1)%3C/script%3E')
        safe.wait_for_timeout(500)
        results['safe_xss_no_execution'] = not safe_dialogs
        safe.close()
        xss.close()
        results['scanner_ui_csrf_missing_rejected'] = context.request.post('http://127.0.0.1:5100/', form={'url':'http://127.0.0.1:5102/page'}).status == 403
        (BASE / 'evidence/browser-checks.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        browser.close()
    if not all(value for key,value in results.items() if key != 'xss_browser_dialog'):
        raise RuntimeError(results)
    manifest = []
    for file in sorted((BASE / 'screenshots').glob('*.png')):
        from PIL import Image
        with Image.open(file) as shot:
            manifest.append({'file': file.name, 'width': shot.width, 'height': shot.height,
                             'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    (BASE / 'evidence/screenshot-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Captured {len(manifest)} real screenshots. Browser verification PASS.')


if __name__ == '__main__':
    main()
