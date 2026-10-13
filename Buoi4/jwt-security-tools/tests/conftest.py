import secrets
import pytest
from token_manager.manager import TokenManager
from api_gateway.gateway import APIGateway


@pytest.fixture
def manager():
    value = TokenManager(secrets.token_urlsafe(48))
    yield value
    value.close()


@pytest.fixture
def client(manager):
    return APIGateway(manager.secret, manager=manager).app.test_client()
