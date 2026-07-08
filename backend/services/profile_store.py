import os
import json
from datetime import datetime, timezone
from backend.config import get_settings
from backend.db.database import get_session
from backend.db.models import ProfileRow
from backend.schemas.profile import Profile


def save_profile(profile: Profile) -> None:
    settings = get_settings()
    path = os.environ.get("PROFILE_PATH", settings.profile_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = profile.model_dump_json()
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)
    now = datetime.now(timezone.utc).isoformat()
    with get_session() as s:
        row = s.get(ProfileRow, 1)
        if row is None:
            s.add(ProfileRow(id=1, data=payload, updated_at=now))
        else:
            row.data = payload
            row.updated_at = now
        s.commit()


def load_profile() -> Profile | None:
    with get_session() as s:
        row = s.get(ProfileRow, 1)
        if row is None:
            return None
        return Profile.model_validate(json.loads(row.data))
