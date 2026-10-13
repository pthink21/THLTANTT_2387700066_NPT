import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode, urlsplit, parse_qsl, urlunsplit
import requests


class OAuthClient:
    def __init__(self, client_id, client_secret, auth_url, token_url, redirect_uri):
        for url in (auth_url, token_url, redirect_uri):
            p = urlsplit(url)
            loopback = p.hostname in {'127.0.0.1', 'localhost', '::1'}
            if not p.hostname or p.username or p.password or p.fragment or (
                    p.scheme != 'https' and not (p.scheme == 'http' and loopback)):
                raise ValueError('OAuth yêu cầu HTTPS; HTTP chỉ cho loopback lab')
        self.client_id, self.client_secret = client_id, client_secret
        self.auth_url, self.token_url, self.redirect_uri = auth_url, token_url, redirect_uri
        self.pending = None

    def get_auth_url(self, scope='openid'):
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        self.pending = (state, verifier, time.monotonic() + 300)
        p = urlsplit(self.auth_url)
        params = dict(parse_qsl(p.query))
        params.update(response_type='code', client_id=self.client_id, redirect_uri=self.redirect_uri,
                      scope=scope, state=state, code_challenge=challenge, code_challenge_method='S256')
        return urlunsplit(p._replace(query=urlencode(params)))

    def get_token(self, code, state):
        if (not self.pending or time.monotonic() > self.pending[2]
                or not secrets.compare_digest(state, self.pending[0])):
            raise ValueError('OAuth state không hợp lệ hoặc đã hết hạn')
        _, verifier, _ = self.pending
        self.pending = None
        data = dict(grant_type='authorization_code', code=code,
                    redirect_uri=self.redirect_uri, client_id=self.client_id,
                    code_verifier=verifier)
        with requests.Session() as session:
            session.trust_env = False
            response = session.post(self.token_url, data=data,
                                    auth=(self.client_id, self.client_secret) if self.client_secret else None,
                                    timeout=(2, 5), allow_redirects=False)
            if 300 <= response.status_code < 400:
                raise ValueError('Token endpoint redirect bị chặn')
            response.raise_for_status()
            result = response.json()
        if not isinstance(result, dict) or not result.get('access_token'):
            raise ValueError('Token response không hợp lệ')
        return result
