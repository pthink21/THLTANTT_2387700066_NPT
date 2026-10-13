def test_valid(client, manager):
    token, _ = manager.generate_tokens('2387700066')
    result = client.get('/protected', headers={'Authorization':'Bearer ' + token})
    assert result.status_code == 200
    assert result.json['user'] == '2387700066'


def test_missing(client):
    assert client.get('/protected').status_code == 401


def test_invalid(client):
    assert client.get('/protected', headers={'Authorization':'Bearer invalid'}).status_code == 401


def test_wrong_scheme(client, manager):
    access, _ = manager.generate_tokens('user')
    assert client.get('/protected', headers={'Authorization':'Basic ' + access}).status_code == 401


def test_refresh_not_access(client, manager):
    _, refresh = manager.generate_tokens('user')
    assert client.get('/protected', headers={'Authorization':'Bearer ' + refresh}).status_code == 401


def test_rotate_and_replay(client, manager):
    _, refresh = manager.generate_tokens('user')
    assert client.post('/refresh', json={'refresh_token':refresh}).status_code == 200
    assert client.post('/refresh', json={'refresh_token':refresh}).status_code == 401


def test_bad_json_shape(client):
    assert client.post('/refresh', json=['invalid']).status_code == 401


def test_rate_limit(manager):
    from api_gateway.gateway import APIGateway
    client = APIGateway(manager.secret, rate_limit=2).app.test_client()
    assert client.get('/health').status_code == 200
    assert client.get('/health').status_code == 200
    assert client.get('/health').status_code == 429


def test_audit_excludes_token_and_query(manager, tmp_path):
    import json
    from api_gateway.gateway import APIGateway
    path = tmp_path / 'audit.jsonl'
    client = APIGateway(manager.secret, audit_path=path).app.test_client()
    access, _ = manager.generate_tokens('user')
    response = client.get('/protected?private=lab', headers={'Authorization':'Bearer ' + access})
    assert response.status_code == 200
    text = path.read_text(encoding='utf-8')
    assert access not in text and manager.secret not in text and 'private' not in text
    assert json.loads(text)['status'] == 200
