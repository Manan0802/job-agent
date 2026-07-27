"""Serving the built UI from the backend, so one command runs the whole app."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_the_api_still_answers():
    assert client.get("/health").json() == {"status": "ok"}


def test_an_unknown_api_path_is_a_404_not_the_app_shell():
    """A typo'd endpoint must fail loudly rather than silently returning HTML."""
    response = client.get("/api/v1/nope")

    assert response.status_code == 404
    assert "text/html" not in response.headers.get("content-type", "")


def test_the_docs_are_still_reachable():
    assert client.get("/docs").status_code == 200
