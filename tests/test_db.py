from backend.db.database import init_db, get_session
from backend.db.models import ProfileRow


def test_insert_and_read_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()
    with get_session() as s:
        s.add(ProfileRow(id=1, data='{"name": "Manan"}', updated_at="2026-06-28"))
        s.commit()
    with get_session() as s:
        row = s.get(ProfileRow, 1)
        assert row is not None
        assert '"Manan"' in row.data
