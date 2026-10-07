"""Reproducible loopback lab services, checks, and browser evidence capture."""
import argparse
import json
import logging
import os
import socket
import sys
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
if (BASE / '.deps').exists():
    sys.path.insert(0, str(BASE / '.deps'))
sys.path.insert(0, str(BASE / 'secure-chat'))
sys.path.insert(0, str(BASE / 'netrecon'))


def start_services():
    from aiosmtpd.controller import Controller
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from werkzeug.serving import make_server
    from flask import Flask, render_template_string
    from server import SecureChatServer
    from make_certs import generate
    from message_encryption import MessageEncryption

    certs = BASE / 'secure-chat/certs'
    if not certs.exists():
        generate(certs)
    keyfile = BASE / 'secure-chat/room-keys/general.key'
    keyfile.parent.mkdir(parents=True, exist_ok=True)
    if not keyfile.exists():
        keyfile.write_bytes(MessageEncryption.generate_key())
    out = BASE / 'evidence'
    out.mkdir(exist_ok=True)
    logs = BASE / 'secure-chat/logs'
    logs.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
        handlers=[logging.FileHandler(logs / 'server.log', encoding='utf-8'), logging.StreamHandler()])
    logging.getLogger('mail.log').setLevel(logging.WARNING)
    chat = SecureChatServer()
    threading.Thread(target=chat.serve_forever, daemon=True).start()

    class HTTPHandler(BaseHTTPRequestHandler):
        server_version = 'LabHTTP/1.0'
        sys_version = ''

        def do_HEAD(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()

        def do_GET(self):
            self.do_HEAD()
            self.wfile.write('Nguyễn Phúc Thịnh — 2387700066 — local HTTP target'.encode('utf-8'))

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(('127.0.0.1', 8080), HTTPHandler)
    threading.Thread(target=http.serve_forever, daemon=True).start()

    def ssh_greeting():
        listener = socket.socket()
        listener.bind(('127.0.0.1', 8022))
        listener.listen()
        while True:
            connection, _ = listener.accept()
            with connection:
                try:
                    connection.sendall(b'SSH-2.0-LabSSH_1.0\r\n')
                except OSError:
                    pass

    def udp_echo():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
            listener.bind(('127.0.0.1', 9998))
            while True:
                data, address = listener.recvfrom(512)
                listener.sendto(b'LAB-UDP ' + data, address)

    threading.Thread(target=ssh_greeting, daemon=True).start()
    threading.Thread(target=udp_echo, daemon=True).start()
    inbox = []

    class MailSink:
        async def handle_DATA(self, server, session, envelope):
            inbox.append({'sender': envelope.mail_from, 'to': envelope.rcpt_tos,
                          'message': envelope.content.decode('utf-8', errors='replace')})
            (out / 'smtp-delivery.json').write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding='utf-8')
            return '250 Message accepted for delivery'

    mail = Controller(MailSink(), hostname='127.0.0.1', port=1025)
    mail.start()
    # Real SMTP delivery into a loopback inbox; no Gmail account is assumed.
    os.environ.update(SMTP_MODE='local', SMTP_HOST='127.0.0.1', SMTP_PORT='1025')
    nmap = BASE / 'runtime/nmap/nmap.exe'
    if nmap.exists():
        os.environ.setdefault('NMAP_PATH', str(nmap))
    from app import app
    web = make_server('127.0.0.1', 5000, app, threaded=True)
    threading.Thread(target=web.serve_forever, daemon=True).start()
    evidence_app = Flask('lab-evidence')
    page = '''<!doctype html><meta charset="utf-8"><title>Lab 03 — Evidence</title><style>
body{background:#101719;color:#e7eeec;font:16px/1.6 Segoe UI,sans-serif;margin:45px auto;max-width:1100px}h1{font-size:36px}h2{color:#baf36b}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#182225;border:1px solid #344448;border-radius:12px;padding:25px;font:14px/1.7 Consolas,monospace}small{color:#9aafab}.pill{color:#baf36b}a{color:#baf36b}</style>
<small>THỰC HÀNH LẬP TRÌNH AN NINH THÔNG TIN / LAB 03</small><h1>NGUYỄN PHÚC THỊNH · 2387700066</h1>
<p class="pill">{{ title }}</p>{% for heading, text in sections %}<h2>{{ heading }}</h2><pre>{{ text }}</pre>{% endfor %}
<small>Evidence from running loopback services. Captured at {{ now }}.</small>'''

    @evidence_app.get('/chat')
    def chat_evidence():
        transcript = (out / 'securechat-transcript.txt').read_text(encoding='utf-8') if (out / 'securechat-transcript.txt').exists() else 'Chat check has not run yet.'
        serverlog = (logs / 'server.log').read_text(encoding='utf-8')[-9000:]
        return render_template_string(page, title='SecureChat · mTLS / E2EE / Rooms',
            sections=[('Live client verification', transcript), ('Actual server log — encrypted relay', serverlog)], now=time.strftime('%Y-%m-%d %H:%M:%S'))

    @evidence_app.get('/mail')
    def mail_evidence():
        from email import policy
        from email.parser import BytesParser
        sections = []
        for index, item in enumerate(inbox, 1):
            message = BytesParser(policy=policy.default).parsebytes(item['message'].encode('utf-8'))
            text = f"From: {message['From']}\nTo: {message['To']}\nSubject: {message['Subject']}\n\n{message.get_content()}"
            sections.append((f'Email {index} · Received through local SMTP :1025', text))
        return render_template_string(page, title='SMTP Inbox · real loopback delivery (not Gmail)', sections=sections, now=time.strftime('%Y-%m-%d %H:%M:%S'))

    @evidence_app.get('/checks')
    def check_evidence():
        text = (out / 'test-results.txt').read_text(encoding='utf-8') if (out / 'test-results.txt').exists() else 'Tests pending'
        return render_template_string(page, title='Verification · automated integration and security tests',
            sections=[('Actual pytest output', text)], now=time.strftime('%Y-%m-%d %H:%M:%S'))

    evidence_web = make_server('127.0.0.1', 8090, evidence_app, threaded=True)
    threading.Thread(target=evidence_web.serve_forever, daemon=True).start()
    time.sleep(.5)
    return chat, web, http, evidence_web, mail


def chat_demo():
    from client import SecureChatClient
    from message_encryption import MessageEncryption
    from protocol import send
    from cryptography.fernet import InvalidToken
    key = (BASE / 'secure-chat/room-keys/general.key').read_bytes()
    transcript = []
    alice = SecureChatClient('alice', key)
    bob = SecureChatClient('bob', key)
    charlie = SecureChatClient('charlie', MessageEncryption.generate_key(), room='private')
    try:
        transcript.append(f"alice authenticated: {alice.ready['tls']} / {alice.ready['cipher']}")
        transcript.append(f"bob authenticated: {bob.ready['tls']} / {bob.ready['cipher']}")
        transcript.append('Client identities come from distinct CA-signed certificates.')
        text = 'Xin chào Bob! Nguyễn Phúc Thịnh — MSSV 2387700066'
        alice.send_message(text)
        response = bob.receive_message()
        assert response['text'] == text and response['sender'] == 'alice'
        transcript.append('alice -> general: ' + text)
        transcript.append('bob decrypted: ' + response['text'])
        transcript.append('On the wire / relay payload: ' + response['ciphertext'])
        charlie.sock.settimeout(.35)
        try:
            charlie.receive_message()
            raise AssertionError('Room isolation broken')
        except socket.timeout:
            transcript.append('PASS: charlie in private receives no general-room message.')
        time.sleep(.06)
        bob.send_message('Đã nhận tin nhắn qua TLS và giải mã đầu-cuối thành công.')
        transcript.append('alice decrypted reply: ' + alice.receive_message()['text'])
        try:
            MessageEncryption(MessageEncryption.generate_key()).decrypt(response['ciphertext'])
            raise AssertionError('Wrong key accepted')
        except InvalidToken as _error:
            transcript.append('PASS: wrong room key cannot decrypt the ciphertext.')
        send(alice.sock, {'type': 'rooms'})
        transcript.append('RoomManager: ' + json.dumps(alice.receive_message()['rooms']))
        transcript.append('PASS: two-way Unicode chat, mTLS, E2EE, room isolation, wrong-key rejection.')
    finally:
        alice.close()
        bob.close()
        charlie.close()
    (BASE / 'evidence/securechat-transcript.txt').write_text('\n'.join(transcript), encoding='utf-8')
    print('\n'.join(transcript))


def capture():
    from playwright.sync_api import sync_playwright
    folder = BASE / 'screenshots'
    folder.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1050}, device_scale_factor=1)
        page.goto('http://127.0.0.1:8090/chat')
        page.screenshot(path=str(folder / '01-securechat-mtls-e2ee.png'), full_page=True)
        page.goto('http://127.0.0.1:5000/')
        page.screenshot(path=str(folder / '02-netrecon-configuration.png'), full_page=True)
        page.locator('[name=email]').fill('thinh@localhost')
        page.locator('button[type=submit]').click()
        page.wait_for_url('**/scan')
        page.wait_for_selector('text=Kết quả khám phá.')
        page.screenshot(path=str(folder / '03-netrecon-tcp-results.png'), full_page=True)
        page.goto('http://127.0.0.1:8090/mail')
        page.screenshot(path=str(folder / '04-smtp-delivery.png'), full_page=True)
        page.goto('http://127.0.0.1:5000/')
        page.locator('[name=ports]').fill('9998,9999')
        page.locator('[name=protocol]').select_option('udp')
        page.locator('[name=mode]').select_option('scan')
        page.locator('button[type=submit]').click()
        page.wait_for_url('**/scan')
        page.screenshot(path=str(folder / '05-netrecon-udp-results.png'), full_page=True)
        page.goto('http://127.0.0.1:5000/')
        page.locator('[name=target]').fill('192.0.2.1')
        page.locator('button[type=submit]').click()
        page.wait_for_selector('[role=alert]')
        page.screenshot(path=str(folder / '06-whitelist-blocked.png'), full_page=True)
        page.goto('http://127.0.0.1:8090/checks')
        page.screenshot(path=str(folder / '07-tests.png'), full_page=True)
        if (BASE / 'runtime/nmap/nmap.exe').exists() or os.getenv('NMAP_PATH'):
            page.goto('http://127.0.0.1:5000/')
            page.locator('[name=ports]').fill('8022,8080,9999')
            page.locator('[name=technique]').select_option('nmap-connect')
            page.locator('button[type=submit]').click()
            page.wait_for_url('**/scan', timeout=60000)
            page.wait_for_selector('text=Kết quả khám phá.')
            page.screenshot(path=str(folder / '09-nmap-service-detection.png'), full_page=True)
        browser.close()
    print('Saved actual browser screenshots to', folder)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['serve', 'demo', 'capture', 'test', 'all'])
    args = p.parse_args()
    if args.action in ('serve', 'all'):
        services = start_services()
        print('SERVICES READY: chat :8443, netrecon :5000, evidence :8090, HTTP :8080, SSH greeting :8022, UDP :9998, SMTP :1025', flush=True)
    if args.action in ('demo', 'all'):
        chat_demo()
    if args.action in ('test', 'all'):
        import subprocess
        environment = dict(os.environ, PYTHONPATH=str(BASE / '.deps'), PYTHONIOENCODING='utf-8')
        testtemp = BASE / 'working' / ('pytest-' + str(time.time_ns()))
        process = subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-v', '--tb=short', '--basetemp', str(testtemp)], cwd=BASE,
                                 env=environment, capture_output=True, text=True, encoding='utf-8')
        (BASE / 'evidence').mkdir(exist_ok=True)
        (BASE / 'evidence/test-results.txt').write_text(process.stdout + process.stderr, encoding='utf-8')
        print(process.stdout, process.stderr)
        if process.returncode:
            raise SystemExit(process.returncode)
    if args.action in ('capture', 'all'):
        capture()
    if args.action in ('serve', 'all'):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            for service in services:
                if hasattr(service, 'close'):
                    service.close()
                elif hasattr(service, 'stop'):
                    service.stop()
                else:
                    service.shutdown()


if __name__ == '__main__':
    main()
