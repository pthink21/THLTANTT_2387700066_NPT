"""Offline, bounded wordlist test for user-owned HS256 laboratory tokens."""
import base64
import hashlib
import hmac
import jwt


class JWTCracker:
    def __init__(self, token, wordlist_path, max_candidates=10000):
        self.token, self.wordlist_path = token, wordlist_path
        if jwt.get_unverified_header(token).get('alg') != 'HS256':
            raise ValueError('Chỉ thử chữ ký HS256 offline')
        self.max_candidates = max_candidates

    def crack(self):
        header, payload, signature = self.token.split('.')
        message = f'{header}.{payload}'.encode()
        with open(self.wordlist_path, encoding='utf-8') as handle:
            for index, line in enumerate(handle):
                if index >= self.max_candidates:
                    break
                candidate = line.rstrip('\r\n')
                if not candidate or len(candidate) > 1024:
                    continue
                digest = hmac.new(candidate.encode(), message, hashlib.sha256).digest()
                encoded = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
                if hmac.compare_digest(encoded, signature):
                    return candidate
        return None
