import json
import secrets
from flask import Flask, render_template, request, session, abort
from engine import ReconEngine

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)
app.config.update(MAX_CONTENT_LENGTH=16384, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict')
engine = ReconEngine()


@app.before_request
def protect():
    # Prevent DNS rebinding against the loopback-only development UI.
    if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
        abort(400)
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    if request.method == 'POST' and not secrets.compare_digest(request.form.get('csrf', ''), session['csrf']):
        abort(403)


@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; frame-ancestors 'none'; form-action 'self'"
    return response


@app.get('/')
def index():
    return render_template('index.html', csrf=session['csrf'])


@app.post('/scan')
def scan():
    try:
        result = engine.run(target=request.form.get('target', ''), ports=request.form.get('ports', ''),
            mode=request.form.get('mode', 'all'), protocol=request.form.get('protocol', 'tcp'),
            rate=float(request.form.get('rate', '10')), subnet=request.form.get('subnet') or None,
            technique=request.form.get('technique', 'connect'), email=request.form.get('email', '').strip())
        return render_template('result.html', result=result, raw=json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        return render_template('index.html', error=str(exc), csrf=session['csrf']), 400


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
