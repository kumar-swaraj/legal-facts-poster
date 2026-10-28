import io
import sys

from legal_facts_poster.wizard import get_masked_input, mask_secret


def test_mask_secret_full():
    # Passwords (show_first=0, show_last=0)
    assert mask_secret("mypassword", show_first=0, show_last=0) == "**********"
    assert mask_secret("", show_first=0, show_last=0) == "(empty)"


def test_mask_secret_partial():
    # API keys (show_first=4, show_last=4)
    key = "AIzaSyABC1234567XYZ"
    res = mask_secret(key, show_first=4, show_last=4)
    assert res.startswith("AIza")
    assert res.endswith("7XYZ")
    assert "********" in res


def test_mask_secret_short():
    assert mask_secret("short", show_first=4, show_last=4) == "*****"


def test_get_masked_input_non_tty(monkeypatch):
    dummy_input = io.StringIO("secret_token_123\n")
    monkeypatch.setattr(sys, "stdin", dummy_input)
    val = get_masked_input("Enter token: ")
    assert val == "secret_token_123"
