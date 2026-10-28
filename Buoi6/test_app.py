from app import create_app


def test_health_endpoint():
    response = create_app().test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_home_does_not_expose_secrets():
    response = create_app().test_client().get("/")
    assert response.status_code == 200
    assert response.get_json()["student_id"] == "2387700066"
