import pytest

from backend.llm import router


@pytest.fixture(autouse=True)
def _reset_llm_breaker():
    """The router's circuit breaker is module-level state; one test tripping it
    must not change how the next test routes."""
    router.reset_primary_breaker()
    yield
    router.reset_primary_breaker()
