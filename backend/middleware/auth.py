"""Password gate for when the app is reachable from outside the laptop.

Off by default: on localhost a password is only friction. Setting APP_PASSWORD
turns it on, which is what you do before exposing the app over a tunnel — the
resume, connections export and drafts behind it are all personal.

Basic auth rather than a login page because it is the whole feature in ten
lines and every browser already implements the client half.
"""

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.config import get_settings

# Open, so a tunnel or uptime check can confirm the app is up without a secret.
_OPEN_PATHS = {"/health"}


def _password() -> str:
    return get_settings().app_password


async def require_password(request: Request, call_next):
    password = _password()
    if not password or request.url.path in _OPEN_PATHS:
        return await call_next(request)

    supplied = _supplied(request)
    # compare_digest, so a wrong guess takes the same time as a near-miss.
    if supplied is None or not secrets.compare_digest(supplied, password):
        return JSONResponse(
            status_code=401,
            content={"detail": "Password required."},
            # Without this the browser shows a bare 401 and never offers a box.
            headers={"WWW-Authenticate": 'Basic realm="job-agent"'},
        )
    return await call_next(request)


def _supplied(request: Request) -> str | None:
    import base64

    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(header[6:]).decode()
    except Exception:
        return None
    # The username is ignored; there is only one user.
    return decoded.partition(":")[2]
