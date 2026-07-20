import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from backend.services import embeddings
from backend.schemas.profile import Profile, Personal, Skills, Experience


def _vec(*values) -> bytes:
    return np.asarray(values, dtype=np.float32).tobytes()


def _fake_model(*vectors):
    model = MagicMock()
    model.encode.return_value = [np.asarray(v, dtype=np.float32) for v in vectors]
    return model


def test_embed_text_returns_roundtrippable_bytes():
    with patch.object(embeddings, "_get_model", return_value=_fake_model([0.5, 0.25])):
        blob = embeddings.embed_text("python engineer")
    assert isinstance(blob, bytes)
    assert np.frombuffer(blob, dtype=np.float32).tolist() == [0.5, 0.25]


def test_cosine_similarity_identical_vectors():
    v = _vec(1.0, 0.0, 0.0)
    assert embeddings.cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert embeddings.cosine_similarity(_vec(1.0, 0.0), _vec(0.0, 1.0)) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_does_not_divide_by_zero():
    assert embeddings.cosine_similarity(_vec(0.0, 0.0), _vec(1.0, 1.0)) == 0.0


def test_prefilter_returns_top_n_ranked_by_similarity():
    profile_emb = _vec(1.0, 0.0)
    jobs = [
        {"title": "unrelated", "company": "A"},
        {"title": "perfect match", "company": "B"},
        {"title": "partial match", "company": "C"},
    ]
    model = _fake_model([0.0, 1.0], [1.0, 0.0], [1.0, 1.0])   # cos = 0, 1, ~0.707
    with patch.object(embeddings, "_get_model", return_value=model):
        out = embeddings.prefilter_jobs(jobs, profile_emb, top_n=2)

    assert [j["title"] for j in out] == ["perfect match", "partial match"]
    assert out[0]["prefilter_score"] > out[1]["prefilter_score"]
    assert out[0]["embedding"]


def test_prefilter_encodes_every_job_in_one_batch():
    """355 jobs one-at-a-time on CPU would be painfully slow — must batch."""
    jobs = [{"title": f"job {i}", "company": "X"} for i in range(4)]
    model = _fake_model([1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [1.0, 0.0])
    with patch.object(embeddings, "_get_model", return_value=model):
        embeddings.prefilter_jobs(jobs, _vec(1.0, 0.0), top_n=10)
    assert model.encode.call_count == 1
    assert len(model.encode.call_args[0][0]) == 4


def test_prefilter_empty_list():
    assert embeddings.prefilter_jobs([], _vec(1.0, 0.0)) == []


def test_embed_profile_uses_skills_and_experience_not_contact_details():
    profile = Profile(
        personal=Personal(name="Manan Kumar", email="secret@example.com"),
        skills=Skills(languages=["Python"], ai_ml=["LangGraph"]),
        experience=[Experience(company="IndiaMART", role="AI Engineer", tech_used=["RAG"])],
        keywords=["vector search"],
    )
    model = _fake_model([1.0, 0.0])
    with patch.object(embeddings, "_get_model", return_value=model):
        blob = embeddings.embed_profile(profile)

    assert isinstance(blob, bytes)
    text = model.encode.call_args[0][0][0]
    assert "Python" in text and "LangGraph" in text
    assert "AI Engineer" in text and "RAG" in text and "vector search" in text
    assert "secret@example.com" not in text     # contact details are noise for matching
