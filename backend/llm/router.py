from openai import OpenAI
from backend.config import get_settings

_settings = get_settings()
_client = OpenAI(api_key=_settings.llm_api_key or "missing", base_url=_settings.llm_base_url)
_groq_client = OpenAI(api_key=_settings.groq_api_key or "missing", base_url=_settings.groq_base_url)


def complete(prompt: str, system: str = "", model: str | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = _client.chat.completions.create(
            model=model or _settings.llm_model,
            messages=messages,
            temperature=0.2,
            max_tokens=_settings.llm_max_tokens,
        )
    except Exception:
        resp = _groq_client.chat.completions.create(
            model=_settings.groq_model,
            messages=messages,
            temperature=0.2,
            max_tokens=_settings.groq_max_tokens,
        )
    return resp.choices[0].message.content.strip()
