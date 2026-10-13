from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch, Mock
import pytest
from oauth_client.client import OAuthClient


def client():
    return OAuthClient('lab-client', '', 'https://auth.example/authorize', 'https://auth.example/token', 'http://localhost/callback')


def test_state_pkce():
    c = client()
    params = parse_qs(urlsplit(c.get_auth_url()).query)
    assert params['code_challenge_method'] == ['S256']
    assert len(params['state'][0]) >= 32
    assert 'client_secret' not in params


def test_wrong_state_no_network():
    c = client()
    c.get_auth_url()
    with patch('requests.Session.post') as post, pytest.raises(ValueError):
        c.get_token('code', 'wrong')
    post.assert_not_called()


def test_exchange_one_use():
    c = client()
    state = parse_qs(urlsplit(c.get_auth_url()).query)['state'][0]
    response = Mock(status_code=200)
    response.json.return_value = {'access_token':'synthetic-test-token'}
    with patch('requests.Session.post', return_value=response) as post:
        assert c.get_token('code', state)['access_token']
        assert post.call_args.kwargs['data']['code_verifier']
    with pytest.raises(ValueError):
        c.get_token('code', state)


def test_http_external_rejected():
    with pytest.raises(ValueError):
        OAuthClient('lab', '', 'http://external.example/', 'https://external.example/token', 'http://localhost/')
