import json
import urllib.error
from unittest.mock import MagicMock, patch

from legal_facts_poster import notifier


def test_notifications_disabled_by_default(monkeypatch):
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(notifier, "TELEGRAM_CHAT_ID", "")
    # Should safely return False (noop) without raising errors
    assert notifier.notify_success("Test Topic") is False
    assert notifier.notify_failure("Some error") is False


def test_failures_only_filter(monkeypatch):
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")
    monkeypatch.setattr(notifier, "NOTIFY_ON", "failures_only")

    # Success should be suppressed
    assert notifier.notify_success("Ignored Topic") is True


def test_send_discord_success(monkeypatch):
    discord_url = "https://discord.com/api/webhooks/999/xyz"
    monkeypatch.setattr(notifier, "WEBHOOK_URL", discord_url)
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")

    mock_resp = MagicMock()
    mock_resp.status = 204
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_success("Right to Privacy", tags=["Law", "Constitution"])
        assert result is True
        assert mock_urlopen.called

        # Verify payload sent to Discord
        req = mock_urlopen.call_args[0][0]
        data = json.loads(req.data.decode("utf-8"))
        assert "embeds" in data
        assert len(data["embeds"]) == 1
        embed = data["embeds"][0]
        assert embed["color"] == 3066993  # Green
        assert "Right to Privacy" in embed["description"]


def test_send_discord_failure(monkeypatch):
    discord_url = "https://discord.com/api/webhooks/999/xyz"
    monkeypatch.setattr(notifier, "WEBHOOK_URL", discord_url)
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_failure("Timeout waiting for publish", topic="Cyber Crime")
        assert result is True

        req = mock_urlopen.call_args[0][0]
        data = json.loads(req.data.decode("utf-8"))
        embed = data["embeds"][0]
        assert embed["color"] == 15158332  # Red
        assert "Timeout waiting for publish" in embed["fields"][0]["value"]


def test_send_telegram_success(monkeypatch):
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "12345:TOKEN")
    monkeypatch.setattr(notifier, "TELEGRAM_CHAT_ID", "999888")
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_success("Consumer Protection", tags=["Consumer"])
        assert result is True

        req = mock_urlopen.call_args[0][0]
        assert "api.telegram.org/bot12345:TOKEN/sendMessage" in req.full_url
        data = json.loads(req.data.decode("utf-8"))
        assert data["chat_id"] == "999888"
        assert "Consumer Protection" in data["text"]


def test_webhook_network_error_handled_gracefully(monkeypatch):
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "https://discord.com/api/webhooks/123/bad")
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        # Should not raise any unhandled exception, returns False
        result = notifier.notify_success("Failing Network Post")
        assert result is False


def test_healthcheck_ping(monkeypatch):
    monkeypatch.setattr(notifier, "HEALTHCHECK_URL", "https://hc-ping.com/fake-uuid")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        assert notifier.ping_healthcheck() is True
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.get_method() == "GET"
        assert req.full_url == "https://hc-ping.com/fake-uuid"
