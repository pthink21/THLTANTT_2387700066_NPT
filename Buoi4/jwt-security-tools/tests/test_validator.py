import time
import secrets
import jwt
import pytest
from jwt_validator.validator import JWTValidator


def mutate(manager, **changes):
    access, _ = manager.generate_tokens('test')
    claims = jwt.decode(access, manager.secret, algorithms=['HS256'], audience='lab04-api')
    claims.update(changes)
    return jwt.encode(claims, manager.secret, algorithm='HS256')


def test_valid(manager):
    access, _ = manager.generate_tokens('test')
    assert manager.validator.validate(access)['valid']


def test_wrong_signature(manager):
    token = jwt.encode({'sub':'test'}, secrets.token_urlsafe(48), algorithm='HS256')
    assert not manager.validator.validate(token)['valid']


@pytest.mark.parametrize('claims', [dict(exp=int(time.time())-10), dict(iss='wrong'), dict(aud='wrong'),
                                   dict(nbf=int(time.time())+300), dict(iat=int(time.time())+300),
                                   dict(type='refresh'), dict(jti=''), dict(sub=''), dict(exp='9999999999')])
def test_invalid_claims(manager, claims):
    assert not manager.validator.validate(mutate(manager, **claims))['valid']


def test_none_algorithm(manager):
    token = jwt.encode({'sub':'test'}, key=None, algorithm='none')
    assert not manager.validator.validate(token)['valid']


def test_missing_exp(manager):
    token = jwt.encode({'sub':'test'}, manager.secret, algorithm='HS256')
    assert not manager.validator.validate(token)['valid']


def test_disallow_algorithm_confusion(manager):
    with pytest.raises(ValueError):
        JWTValidator(manager.secret, ['HS256','RS256'])
