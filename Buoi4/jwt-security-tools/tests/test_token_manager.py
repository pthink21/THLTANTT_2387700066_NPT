from concurrent.futures import ThreadPoolExecutor
import secrets
import pytest
from token_manager.manager import TokenManager


def test_rotate(manager):
    access, refresh = manager.generate_tokens('user')
    next_pair = manager.rotate_refresh_token(refresh)
    assert next_pair and next_pair[0] != access
    assert manager.rotate_refresh_token(refresh) is None


def test_revoke(manager):
    _, refresh = manager.generate_tokens('user')
    assert manager.revoke_refresh_token(refresh)
    assert manager.rotate_refresh_token(refresh) is None


def test_access_not_refresh(manager):
    access, _ = manager.generate_tokens('user')
    assert manager.refresh_access_token(access) is None


def test_race(manager):
    _, refresh = manager.generate_tokens('user')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: manager.rotate_refresh_token(refresh), range(8)))
    assert sum(result is not None for result in results) == 1


def test_persist_across_restart(tmp_path):
    key = secrets.token_urlsafe(48)
    db = str(tmp_path / 'tokens.sqlite')
    first = TokenManager(key, db_path=db)
    _, refresh = first.generate_tokens('user')
    first.close()
    second = TokenManager(key, db_path=db)
    assert second.rotate_refresh_token(refresh)
    second.close()


def test_weak_key_rejected():
    with pytest.raises(ValueError):
        TokenManager(secrets.token_hex(2))
