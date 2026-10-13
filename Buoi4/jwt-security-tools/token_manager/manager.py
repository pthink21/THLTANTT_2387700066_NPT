"""Refresh-token rotation/revocation, serialized atomically with SQLite."""
import hashlib
import secrets
import sqlite3
import threading
import time
import jwt
from jwt_validator.validator import JWTValidator


class TokenManager:
    def __init__(self, secret, algorithm='HS256', access_exp=15, refresh_exp=1440,
                 db_path=':memory:'):
        if algorithm != 'HS256' or len(secret.encode()) < 32:
            raise ValueError('Cần khóa HS256 tối thiểu 32 bytes')
        if access_exp <= 0 or refresh_exp <= 0:
            raise ValueError('Thời hạn phải dương')
        self.secret, self.algorithm = secret, algorithm
        self.access_exp, self.refresh_exp = access_exp, refresh_exp
        self.validator = JWTValidator(secret)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self.db.execute('CREATE TABLE IF NOT EXISTS refresh (digest TEXT PRIMARY KEY, expires INTEGER NOT NULL)')

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate(self, user_id, kind, minutes):
        now = int(time.time())
        return jwt.encode({'sub': user_id, 'type': kind, 'iat': now, 'nbf': now,
                           'exp': now + max(1, int(minutes * 60)), 'iss': 'lab04',
                           'aud': 'lab04-api', 'jti': secrets.token_hex(16)},
                          self.secret, algorithm=self.algorithm)

    def _pair(self, user_id):
        access = self._generate(user_id, 'access', self.access_exp)
        refresh = self._generate(user_id, 'refresh', self.refresh_exp)
        exp = self.validator.validate(refresh, 'refresh')['payload']['exp']
        self.db.execute('INSERT INTO refresh VALUES (?, ?)', (self.digest(refresh), exp))
        return access, refresh

    def generate_tokens(self, user_id):
        if not isinstance(user_id, str) or not user_id:
            raise ValueError('user_id không được rỗng')
        with self.lock:
            return self._pair(user_id)

    def rotate_refresh_token(self, refresh_token):
        result = self.validator.validate(refresh_token, 'refresh')
        if not result['valid']:
            return None
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                deleted = self.db.execute('DELETE FROM refresh WHERE digest=? AND expires>?',
                                          (self.digest(refresh_token), int(time.time()))).rowcount
                if not deleted:
                    self.db.execute('ROLLBACK')
                    return None
                pair = self._pair(result['payload']['sub'])
                self.db.execute('COMMIT')
                return pair
            except Exception:
                self.db.execute('ROLLBACK')
                raise

    def refresh_access_token(self, refresh_token):
        """PDF-compatible single-use refresh; use rotate_refresh_token for new pair."""
        pair = self.rotate_refresh_token(refresh_token)
        return pair[0] if pair else None

    def revoke_refresh_token(self, refresh_token):
        with self.lock:
            return bool(self.db.execute('DELETE FROM refresh WHERE digest=?',
                                        (self.digest(refresh_token),)).rowcount)

    def close(self):
        self.db.close()
