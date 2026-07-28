import pytest

from backend.llm import router
from backend.middleware import auth


@pytest.fixture(autouse=True)
def _ungated(monkeypatch):
    """Whether the developer set APP_PASSWORD in their own .env must not decide
    whether the API tests can reach the API. Gate behaviour is covered by
    tests/test_auth.py, which sets a password explicitly."""
    monkeypatch.setattr(auth, "_password", lambda: "")


@pytest.fixture(autouse=True)
def _reset_llm_breaker():
    """The router's circuit breaker is module-level state; one test tripping it
    must not change how the next test routes."""
    router.reset_primary_breaker()
    yield
    router.reset_primary_breaker()
