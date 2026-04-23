"""Smoke tests for the minimal Phase 0 API surface."""


def test_health_endpoint(client):
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_endpoint(client):
    response = client.get("/api/info/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "avk-backend"
    assert payload["phase"] == "phase-0"
    assert payload["language_code"] == "tr-tr"
    assert payload["time_zone"] == "Europe/Istanbul"
    assert payload["version"] == "0.1.0-phase0"
