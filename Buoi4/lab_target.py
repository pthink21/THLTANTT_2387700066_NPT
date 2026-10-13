"""Deliberately vulnerable fixtures. Loopback only, synthetic data, bounded SSRF."""
import base64
import hashlib
import hmac
import secrets
import sqlite3
import threading
import time
from urllib.parse import urlencode
import requests
from flask import Flask, request, jsonify, redirect, session, render_template_string


def target_app():
    app = Flask('lab04-target')
    app.secret_key = secrets.token_bytes(32)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    state = {'changes': 0}

    @app.get('/page')
    def page():
        # Intentionally unescaped, isolated XSS fixture.
        return '<h1>Lab 04 — vulnerable fixture</h1>' + request.args.get('q', '') + '''
        <form method="post" action="/change"><input name="value" value="lab"><button>Change</button></form>'''

    @app.get('/safe')
    def safe():
        session['csrf'] = session.get('csrf') or secrets.token_urlsafe(32)
        return render_template_string('''<h1>Safe fixture</h1><p>{{ q }}</p>
        <form method="post" action="/safe-change"><input type="hidden" name="csrf_token" value="{{ csrf }}">
        <input name="value"><button>Change</button></form>''', q=request.args.get('q', ''), csrf=session['csrf'])

    @app.post('/change')
    def change():
        state['changes'] += 1
        return jsonify(changes=state['changes'], csrf_checked=False)

    @app.post('/safe-change')
    def safe_change():
        provided, expected = request.form.get('csrf_token', ''), session.get('csrf', '')
        if not expected or not hmac.compare_digest(provided, expected):
            return jsonify(error='CSRF rejected'), 403
        return jsonify(csrf_checked=True)

    @app.get('/items')
    @app.get('/safe-items')
    def items():
        value = request.args.get('id', '1')
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE TABLE items(id INTEGER, name TEXT)')
            db.executemany('INSERT INTO items VALUES (?, ?)', [(1, 'Lab Alpha'), (2, 'Lab Beta')])
            try:
                if request.path == '/safe-items':
                    rows = db.execute('SELECT * FROM items WHERE id=?', (value,)).fetchall()
                else:
                    # Intentional SQLi against disposable in-memory fixture, never production data.
                    rows = db.execute('SELECT * FROM items WHERE id=' + value).fetchall()  # nosec B608
                return jsonify(rows)
            except sqlite3.Error as exc:
                return 'sqlite3.OperationalError: ' + str(exc)

    @app.get('/fetch')
    @app.get('/safe-fetch')
    def fetch():
        url = request.args.get('url', '')
        if request.path == '/safe-fetch':
            return jsonify(error='Internal URLs blocked'), 200
        # Deliberately permits an internal destination, but only the lab proof endpoint.
        if url != 'http://127.0.0.1:5103/internal-proof':
            return jsonify(error='Fixture permits only the internal lab proof'), 200
        with requests.Session() as client:
            client.trust_env = False
            response = client.get(url, timeout=2, allow_redirects=False)
            return response.text

    @app.get('/redirect')
    def redirect_fixture():
        return redirect('http://192.0.2.1/')

    return app


def internal_app():
    app = Flask('internal-proof')

    @app.get('/internal-proof')
    def proof():
        return 'LAB04-INTERNAL-PROOF-2387700066'

    return app


def oauth_provider():
    """Local Authorization Code + PKCE server fixture; not a production IdP."""
    app = Flask('oauth-fixture')
    codes, lock = {}, threading.Lock()
    callback = 'http://127.0.0.1:5104/callback'

    @app.get('/authorize')
    def authorize():
        args = request.args
        if (args.get('client_id') != 'lab04-client' or args.get('redirect_uri') != callback
                or args.get('response_type') != 'code' or args.get('code_challenge_method') != 'S256'
                or not args.get('state') or not args.get('code_challenge')):
            return jsonify(error='invalid_request'), 400
        code = secrets.token_urlsafe(32)
        with lock:
            codes[code] = (args['code_challenge'], time.monotonic() + 60)
        return redirect(callback + '?' + urlencode({'code': code, 'state': args['state']}))

    @app.post('/token')
    def token():
        data = request.form
        challenge = base64.urlsafe_b64encode(hashlib.sha256(data.get('code_verifier', '').encode()).digest()).rstrip(b'=').decode()
        with lock:
            item = codes.pop(data.get('code', ''), None)
        if (not item or item[1] < time.monotonic() or not secrets.compare_digest(item[0], challenge)
                or data.get('client_id') != 'lab04-client' or data.get('redirect_uri') != callback
                or data.get('grant_type') != 'authorization_code'):
            return jsonify(error='invalid_grant'), 400
        # Bearer is the OAuth token-type name, not a credential.
        return jsonify({'access_token': secrets.token_urlsafe(32), 'token_type': 'Bearer', 'expires_in': 300})  # nosec B105

    return app
