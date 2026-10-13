import jwt


class JWTValidator:
    def __init__(self, secret, algorithms=None, issuer='lab04', audience='lab04-api'):
        self.secret = secret
        self.algorithms = algorithms or ['HS256']
        if self.algorithms != ['HS256']:
            raise ValueError('Lab sử dụng duy nhất HS256; không lấy thuật toán từ token')
        self.issuer, self.audience = issuer, audience

    def validate(self, token, expected_type='access'):
        try:
            payload = jwt.decode(token, self.secret, algorithms=self.algorithms,
                                 issuer=self.issuer, audience=self.audience,
                                 options={'require': ['sub', 'exp', 'iat', 'nbf', 'iss', 'aud', 'jti', 'type']})
            if payload['type'] != expected_type:
                return {'valid': False, 'reason': 'Wrong token type'}
            if not isinstance(payload['sub'], str) or not payload['sub']:
                return {'valid': False, 'reason': 'Invalid subject'}
            if not isinstance(payload['jti'], str) or not payload['jti']:
                return {'valid': False, 'reason': 'Invalid jti'}
            if (not all(type(payload[k]) is int for k in ['iat', 'nbf', 'exp'])
                    or payload['exp'] <= payload['iat'] or payload['nbf'] > payload['exp']):
                return {'valid': False, 'reason': 'Invalid time claims'}
            return {'valid': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'reason': 'Token expired'}
        except jwt.InvalidSignatureError:
            return {'valid': False, 'reason': 'Invalid signature'}
        except jwt.InvalidTokenError as exc:
            return {'valid': False, 'reason': str(exc)}
