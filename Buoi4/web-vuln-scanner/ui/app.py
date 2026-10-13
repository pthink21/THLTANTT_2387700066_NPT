from pathlib import Path
import sys
import secrets
import hmac
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import Flask, render_template, request, session, jsonify
from engine import scan


def create_app():
    app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / 'templates'))
    app.secret_key = secrets.token_bytes(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', MAX_CONTENT_LENGTH=8192)

    @app.after_request
    def secure(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'none'; frame-ancestors 'none'; form-action 'self'"
        return response

    @app.route('/', methods=['GET', 'POST'])
    def index():
        session['csrf'] = session.get('csrf') or secrets.token_urlsafe(32)
        if request.method == 'POST':
            if not hmac.compare_digest(request.form.get('csrf_token', ''), session['csrf']):
                return 'CSRF rejected', 403
            try:
                report = scan(request.form.get('url', ''), request.form.getlist('scanner'))
                return render_template('result.html', report=report)
            except ValueError as exc:
                return render_template('index.html', error=str(exc)), 400
        return render_template('index.html')

    @app.get('/evidence')
    def evidence():
        path = Path(__file__).resolve().parents[2] / 'evidence' / 'integration.json'
        data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'status': 'Chưa chạy demo'}
        return render_template('evidence.html', data=data)

    @app.get('/report.json')
    def report_json():
        path = Path(__file__).resolve().parents[2] / 'evidence' / 'scanner-report.json'
        return jsonify(json.loads(path.read_text(encoding='utf-8'))) if path.exists() else ({'error': 'No report'}, 404)

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5100, debug=False)
