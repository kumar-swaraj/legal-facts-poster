import json
from unittest.mock import MagicMock

from legal_facts_poster.browser_bot import (
    PostResult,
    _ensure_authenticated,
    _validate_and_get_session,
)


def test_post_result_bool_and_unpacking():
    res_success = PostResult(True, ["Law", "Legal"])
    assert bool(res_success) is True
    success, tags = res_success
    assert success is True
    assert tags == ["Law", "Legal"]

    res_fail = PostResult(False, [])
    assert bool(res_fail) is False
    success_f, tags_f = res_fail
    assert success_f is False
    assert tags_f == []


def test_validate_and_get_session_valid(tmp_path):
    sess_file = tmp_path / "session.json"
    sess_file.write_text(json.dumps({"cookies": [{"name": "auth", "value": "xyz"}]}))
    valid = _validate_and_get_session(str(sess_file))
    assert valid == str(sess_file)


def test_validate_and_get_session_corrupted_quarantine(tmp_path):
    sess_file = tmp_path / "session.json"
    sess_file.write_text("{broken json syntax: missing close bracket")

    valid = _validate_and_get_session(str(sess_file))
    assert valid is None
    # Original corrupted file should be removed/quarantined
    assert not sess_file.exists()
    # Check that a .corrupted backup was created in directory
    files = list(tmp_path.glob("session.json.corrupted.*"))
    assert len(files) == 1


def test_validate_and_get_session_empty_file(tmp_path):
    sess_file = tmp_path / "session.json"
    sess_file.write_text("")  # 0 bytes

    valid = _validate_and_get_session(str(sess_file))
    assert valid is None
    assert not sess_file.exists()


def test_ensure_authenticated_fails_when_stuck_on_login(monkeypatch):
    mock_page = MagicMock()
    mock_page.url = "https://example.com/login"
    mock_context = MagicMock()

    # If wait_for_url times out on login
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    mock_page.wait_for_url.side_effect = PlaywrightTimeoutError("Timed out waiting for login")
    mock_page.locator.return_value.all_inner_texts.return_value = ["Invalid credentials"]

    result = _ensure_authenticated(mock_page, mock_context)
    assert result is False
