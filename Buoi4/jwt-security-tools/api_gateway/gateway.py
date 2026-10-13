import collections
import threading
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from jwt_validator.validator import JWTValidator


class APIGateway:
    def __init__(self, secret, algorithm='HS256', manager=None, rate_limit=60, audit_path=None):
        self.app = Flask(__name__)
        self.validator = JWTValidator(secret, [algorithm])
        self.manager = manager
        self.rate_limit = rate_limit
        self.hits = collections.defaultdict(collections.deque)
        self.lock = threading.Lock()
        self.audit_path = Path(audit_path) if audit_path else None
        if self.audit_path:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.routes()

    def routes(self):
        @self.app.before_request
        def limit():
            now = time.monotonic()
            with self.lock:
                hits = self.hits[request.remote_addr]
                while hits and hits[0] <= now - 60:
                    hits.popleft()
                if len(hits) >= self.rate_limit:
                    return jsonify(error='Rate limit exceeded'), 429, {'Retry-After': '60'}
                hits.append(now)

        @self.app.after_request
        def headers(response):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            if self.audit_path:
                event = {'time': datetime.now(timezone.utc).isoformat(), 'method': request.method,
                         'path': request.path, 'status': response.status_code}
                with self.lock, self.audit_path.open('a', encoding='utf-8') as handle:
                    handle.write(json.dumps(event) + '\n')
            return response

        @self.app.get('/health')
        def health():
            return jsonify(status='ok', service='JWTSecure')

        @self.app.get('/protected')
        def protected():
            header = request.headers.get('Authorization', '')
            parts = header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify(message='Access denied'), 401
            result = self.validator.validate(parts[1])
            if not result['valid']:
                return jsonify(message='Access denied'), 401
            return jsonify(message='Access granted', user=result['payload']['sub'])

        @self.app.post('/refresh')
        def refresh():
            data = request.get_json(silent=True) or {}
            token = data.get('refresh_token') if isinstance(data, dict) else None
            pair = self.manager.rotate_refresh_token(token) if self.manager and isinstance(token, str) else None
            if not pair:
                return jsonify(error='Invalid refresh token'), 401
            # Bearer is the authentication scheme, not a hard-coded token.
            return jsonify({'access_token': pair[0], 'refresh_token': pair[1], 'token_type': 'Bearer'})  # nosec B105

        @self.app.post('/revoke')
        def revoke():
            data = request.get_json(silent=True) or {}
            token = data.get('refresh_token') if isinstance(data, dict) else None
            if self.manager and isinstance(token, str):
                self.manager.revoke_refresh_token(token)
            return '', 204

    def run(self, port=5000):
        self.app.run(host='127.0.0.1', port=port, debug=False)
