"""A password gate, for when the app is reachable from outside the laptop.

Everything here is personal: the resume, the connections export, the drafts.
Exposing it over a tunnel without this would hand all of it to anyone with the
link.

Off by default, because on localhost a password is only friction.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.middleware import auth


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "a.db"))
    return TestClient(app)


def _password(monkeypatch, value):
    monkeypatch.setattr(auth, "_password", lambda: value)


def test_no_password_set_means_no_gate(client, monkeypatch):
    """On localhost a password is only friction."""
    _password(monkeypatch, "")
    assert client.get("/api/v1/setup").status_code == 200


def test_a_set_password_locks_the_api(client, monkeypatch):
    _password(monkeypatch, "hunter2")
    assert client.get("/api/v1/setup").status_code == 401


def test_the_right_password_gets_through(client, monkeypatch):
    _password(monkeypatch, "hunter2")

    resp = client.get("/api/v1/setup", auth=("jba", "hunter2"))

    assert resp.status_code == 200


def test_a_wrong_password_does_not(client, monkeypatch):
    _password(monkeypatch, "hunter2")
    assert client.get("/api/v1/setup", auth=("jba", "nope")).status_code == 401


def test_the_browser_is_asked_to_prompt(client, monkeypatch):
    """Without this header the browser shows a bare 401 page and never offers
    a login box."""
    _password(monkeypatch, "hunter2")

    assert "Basic" in client.get("/api/v1/setup").headers.get("www-authenticate", "")


def test_health_stays_open_so_a_tunnel_can_check_it(client, monkeypatch):
    _password(monkeypatch, "hunter2")
    assert client.get("/health").status_code == 200


def test_the_ui_is_gated_too(client, monkeypatch):
    """The built UI holds the same data as the API behind it."""
    _password(monkeypatch, "hunter2")

    assert client.get("/").status_code == 401
