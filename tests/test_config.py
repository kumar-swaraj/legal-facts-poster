from legal_facts_poster.config import (
    PROVIDER_DEFAULTS,
    _to_bool,
    _to_float,
    _to_int,
)


def test_to_bool_parsing():
    assert _to_bool("true") is True
    assert _to_bool("True") is True
    assert _to_bool("1") is True
    assert _to_bool("yes") is True
    assert _to_bool("false") is False
    assert _to_bool("0") is False
    assert _to_bool("no") is False
    assert _to_bool(None, default=True) is True
    assert _to_bool(None, default=False) is False


def test_to_float_parsing():
    assert _to_float("4.5", default=1.0) == 4.5
    assert _to_float("invalid", default=2.0) == 2.0
    assert _to_float(None, default=3.0) == 3.0


def test_to_int_parsing():
    assert _to_int("10", default=1) == 10
    assert _to_int("invalid", default=5) == 5
    assert _to_int(None, default=7) == 7


def test_provider_defaults_structure():
    assert "gemini" in PROVIDER_DEFAULTS
    assert "openai" in PROVIDER_DEFAULTS
    assert "claude" in PROVIDER_DEFAULTS
    assert "deepseek" in PROVIDER_DEFAULTS
    assert "grok" in PROVIDER_DEFAULTS

    for data in PROVIDER_DEFAULTS.values():
        assert "name" in data
        assert "base_url" in data
        assert "models" in data
        assert "key_env" in data
