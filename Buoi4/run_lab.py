"""Start real loopback services, execute reproducible demos and save evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import secrets
import sys
import threading
import time
from urllib.parse import parse_qs, urlsplit
import requests
import jwt
from werkzeug.serving import make_server
from lab_target import target_app, internal_app, oauth_provider

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'web-vuln-scanner'))
sys.path.insert(0, str(BASE / 'jwt-security-tools'))
from engine import scan
from jwt_cracker.cracker import JWTCracker
from oauth_client.client import OAuthClient
from token_manager.manager import TokenManager
from api_gateway.gateway import APIGateway


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def serve():
    gateway = load(BASE / 'jwt-security-tools/main.py', 'jwt_main').build(5101)
    ui = load(BASE / 'web-vuln-scanner/ui/app.py', 'scanner_ui').create_app()
    servers = []
    for port, app in [(5100, ui), (5101, gateway.app), (5102, target_app()),
                      (5103, internal_app()), (5104, oauth_provider())]:
        server = make_server('127.0.0.1', port, app, threaded=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        print(f'RUNNING http://127.0.0.1:{port} — {app.name}', flush=True)
    print('Nguyễn Phúc Thịnh — 2387700066 | Ctrl+C to stop', flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for server in servers:
            server.shutdown()


def demo():
    dest = BASE / 'evidence'
    dest.mkdir(exist_ok=True)
    runtime = BASE / 'runtime'
    tokens = json.loads((runtime / 'tokens.json').read_text(encoding='utf-8'))
    checks = {}
    with requests.Session() as client:
        client.trust_env = False
        root = 'http://127.0.0.1:5101'
        checks['jwt_valid_access'] = client.get(root + '/protected', headers={'Authorization': 'Bearer ' + tokens['access_token']}, timeout=3).status_code
        checks['jwt_missing_token'] = client.get(root + '/protected', timeout=3).status_code
        checks['jwt_invalid_signature'] = client.get(root + '/protected', headers={'Authorization': 'Bearer ' + tokens['access_token'][:-4] + 'AAAA'}, timeout=3).status_code
        checks['jwt_refresh_as_access'] = client.get(root + '/protected', headers={'Authorization': 'Bearer ' + tokens['refresh_token']}, timeout=3).status_code
        key = (runtime / 'jwt-key.txt').read_text(encoding='utf-8')
        claims = jwt.decode(tokens['access_token'], key, algorithms=['HS256'], audience='lab04-api')
        claims.update(iat=int(time.time())-120, nbf=int(time.time())-120, exp=int(time.time())-60)
        expired = jwt.encode(claims, key, algorithm='HS256')
        checks['jwt_expired'] = client.get(root + '/protected', headers={'Authorization': 'Bearer ' + expired}, timeout=3).status_code
        refreshed = client.post(root + '/refresh', json={'refresh_token': tokens['refresh_token']}, timeout=3)
        checks['refresh_rotation'] = refreshed.status_code
        checks['refresh_replay_rejected'] = client.post(root + '/refresh', json={'refresh_token': tokens['refresh_token']}, timeout=3).status_code
        fresh = refreshed.json()
        client.post(root + '/revoke', json={'refresh_token': fresh['refresh_token']}, timeout=3)
        checks['revoked_refresh_rejected'] = client.post(root + '/refresh', json={'refresh_token': fresh['refresh_token']}, timeout=3).status_code
        # Save a new local pair for subsequent CMD curl demonstration.
        local = TokenManager(key, db_path=str(runtime / 'tokens.sqlite'))
        access, refresh = local.generate_tokens('2387700066')
        local.close()
        (runtime / 'tokens.json').write_text(json.dumps(dict(access_token=access, refresh_token=refresh)), encoding='utf-8')
        (runtime / 'access.curl').write_text(f'header = "Authorization: Bearer {access}"\n', encoding='utf-8')
        checks['csrf_unsafe_post_no_token'] = client.post('http://127.0.0.1:5102/change', data={'value': 'lab'}, timeout=3).status_code
        client.get('http://127.0.0.1:5102/safe', timeout=3)
        checks['csrf_safe_post_no_token'] = client.post('http://127.0.0.1:5102/safe-change', data={'value': 'lab'}, timeout=3).status_code
        oauth = OAuthClient('lab04-client', '', 'http://127.0.0.1:5104/authorize',
                            'http://127.0.0.1:5104/token', 'http://127.0.0.1:5104/callback')
        auth = client.get(oauth.get_auth_url(), allow_redirects=False, timeout=3)
        params = parse_qs(urlsplit(auth.headers['Location']).query)
        grant = oauth.get_token(params['code'][0], params['state'][0])
        checks['oauth_code_pkce_exchange'] = bool(grant.get('access_token'))
        try:
            oauth.get_token(params['code'][0], params['state'][0])
        except ValueError:
            checks['oauth_callback_replay_rejected'] = True
    weak = secrets.choice(['lab-word-a', 'lab-word-b', 'lab-word-c'])
    wordlist = runtime / 'lab-wordlist.txt'
    wordlist.write_text('\n'.join(['wrong', 'lab-word-a', 'lab-word-b', 'lab-word-c']), encoding='utf-8')
    weak_token = jwt.encode({'sub': 'lab-only'}, weak, algorithm='HS256')
    checks['offline_weak_key_found'] = JWTCracker(weak_token, wordlist).crack() == weak
    manager = TokenManager(secrets.token_urlsafe(48))
    _, refresh = manager.generate_tokens('race-test')
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(lambda _: manager.rotate_refresh_token(refresh), range(8)))
    checks['refresh_race_successes_of_8'] = sum(x is not None for x in outcomes)
    manager.close()
    findings, safe_counts = [], {}
    for path, options in [('page?id=1', ['xss','csrf']), ('items?id=1', ['sql']), ('fetch?url=', ['ssrf'])]:
        report = scan('http://127.0.0.1:5102/' + path, options)
        if not report['complete']:
            raise RuntimeError(report['errors'])
        findings.extend(report['vulnerabilities'])
    for path, options in [('safe?id=1', ['xss','csrf']), ('safe-items?id=1', ['sql']), ('safe-fetch?url=', ['ssrf'])]:
        report = scan('http://127.0.0.1:5102/' + path, options)
        if not report['complete']:
            raise RuntimeError(report['errors'])
        safe_counts[path] = report['count']
    checks['scanner_types'] = sorted({f['type'] for f in findings})
    checks['safe_fixture_findings'] = safe_counts
    expected = dict(zip(['jwt_valid_access', 'jwt_missing_token', 'jwt_invalid_signature',
                         'jwt_refresh_as_access', 'jwt_expired', 'refresh_rotation',
                         'refresh_replay_rejected', 'revoked_refresh_rejected',
                         'csrf_unsafe_post_no_token', 'csrf_safe_post_no_token'],
                        [200, 401, 401, 401, 401, 200, 401, 401, 200, 403]))
    expected.update({
                'oauth_code_pkce_exchange':True, 'oauth_callback_replay_rejected':True,
                'offline_weak_key_found':True, 'refresh_race_successes_of_8':1})
    for name, value in expected.items():
        if checks[name] != value:
            raise RuntimeError((name, checks[name]))
    if checks['scanner_types'] != ['CSRF','SQLi','SSRF','XSS'] or any(safe_counts.values()):
        raise RuntimeError({'scanner_types': checks['scanner_types'], 'safe': safe_counts})
    from report.report_generator import ReportGenerator
    (dest / 'scanner-report.json').write_text(json.dumps(ReportGenerator().generate(findings), ensure_ascii=False, indent=2), encoding='utf-8')
    (dest / 'integration.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    audit = runtime / 'gateway-audit.jsonl'
    if audit.exists():
        (dest / 'gateway-audit.jsonl').write_text(audit.read_text(encoding='utf-8'), encoding='utf-8')
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    print('All real HTTP integration checks PASS. No tokens saved in evidence.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['serve','demo'])
    args = parser.parse_args()
    {'serve': serve, 'demo': demo}[args.command]()
