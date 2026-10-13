import json
import urllib.error
from unittest.mock import MagicMock, patch

from legal_facts_poster import notifier


def test_notifications_disabled_by_default(monkeypatch):
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "")
    monkeypatch.setattr(notifier, "TEAMS_WEBHOOK_URL", "")
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


def test_send_discord_rich_metadata(monkeypatch):
    discord_url = "https://discord.com/api/webhooks/999/xyz"
    monkeypatch.setattr(notifier, "WEBHOOK_URL", discord_url)
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")

    mock_resp = MagicMock()
    mock_resp.status = 204
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_success(
            topic="RERA Refund",
            tags=["Law", "LegalAwareness"],
            headline="Can a builder delay refund?",
            takeaway="Consumers are entitled to full compensation.",
            category="Citizen & Civil Rights",
            model_name="Gemini 3.8",
            attempt=1,
        )
        assert result is True
        req = mock_urlopen.call_args[0][0]
        data = json.loads(req.data.decode("utf-8"))
        embed = data["embeds"][0]

        assert "Can a builder delay refund?" in embed["description"]
        assert "Consumers are entitled to full compensation." in embed["description"]
        field_names = [f["name"] for f in embed["fields"]]
        assert "📌 Topic" in field_names
        assert "📂 Category" in field_names
        assert "🏷️ Tags Applied" in field_names
        assert "🤖 AI Model" in field_names
        assert "🎯 Attempt" in field_names
        # Ensure only the 2 passed tags appear
        tag_field = next(f for f in embed["fields"] if f["name"] == "🏷️ Tags Applied")
        assert "`#Law`" in tag_field["value"]
        assert "`#LegalAwareness`" in tag_field["value"]
        assert "SupremeCourt" not in tag_field["value"]


def test_send_teams_success(monkeypatch):
    teams_url = (
        "https://prod-1.westus.logic.azure.com:443/workflows/123/triggers/manual/paths/invoke"
        "?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=secret_sig"
    )
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "")
    monkeypatch.setattr(notifier, "TEAMS_WEBHOOK_URL", teams_url)
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")

    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_success(
            topic="Consumer Rights",
            tags=["Consumer", "LegalAid"],
            headline="Know your consumer protection rights",
            takeaway="Consumers can claim compensation within 2 years.",
            category="Citizen & Civil Rights",
            model_name="Gemini 3.8",
            attempt=1,
        )
        assert result is True
        assert mock_urlopen.called

        req = mock_urlopen.call_args[0][0]
        data = json.loads(req.data.decode("utf-8"))
        assert data["type"] == "message"
        assert len(data["attachments"]) == 1
        attachment = data["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"

        card = attachment["content"]
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"

        # Verify card body
        body_texts = [b.get("text", "") for b in card["body"] if "text" in b]
        assert any("⚖️ Legal Fact Published Successfully" in t for t in body_texts)
        assert any("Know your consumer protection rights" in t for t in body_texts)
        assert any("Consumers can claim compensation within 2 years." in t for t in body_texts)

        # Verify FactSet
        fact_set = next(b for b in card["body"] if b.get("type") == "FactSet")
        fact_titles = [f["title"] for f in fact_set["facts"]]
        assert "📌 Topic" in fact_titles
        assert "📂 Category" in fact_titles
        assert "🏷️ Tags" in fact_titles
        assert "🤖 AI Model" in fact_titles
        assert "🎯 Attempt" in fact_titles

        tag_fact = next(f for f in fact_set["facts"] if f["title"] == "🏷️ Tags")
        assert "#Consumer" in tag_fact["value"]
        assert "#LegalAid" in tag_fact["value"]


def test_send_teams_failure(monkeypatch):
    teams_url = "https://contoso.webhook.office.com/webhookb2/uuid/IncomingWebhook/token/tenant"
    monkeypatch.setattr(notifier, "WEBHOOK_URL", "")
    monkeypatch.setattr(notifier, "TEAMS_WEBHOOK_URL", teams_url)
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_failure(
            "Timeout waiting for publish", topic="Cyber Law", attempt=2
        )
        assert result is True

        req = mock_urlopen.call_args[0][0]
        data = json.loads(req.data.decode("utf-8"))
        card = data["attachments"][0]["content"]

        body_texts = [b.get("text", "") for b in card["body"] if "text" in b]
        assert any("🚨 Post Publication Failed" in t for t in body_texts)
        assert any("Cyber Law" in t for t in body_texts)

        fact_set = next(b for b in card["body"] if b.get("type") == "FactSet")
        error_fact = next(f for f in fact_set["facts"] if f["title"] == "⚠️ Error Details")
        assert "Timeout waiting for publish" in error_fact["value"]


def test_webhook_url_autodetects_teams(monkeypatch):
    teams_url = (
        "https://prod-1.westus.logic.azure.com:443/workflows/123/triggers/manual/paths/invoke"
        "?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=sig"
    )
    monkeypatch.setattr(notifier, "WEBHOOK_URL", teams_url)
    monkeypatch.setattr(notifier, "TEAMS_WEBHOOK_URL", "")
    monkeypatch.setattr(notifier, "NOTIFY_ON", "all")
    monkeypatch.setattr(notifier, "TELEGRAM_BOT_TOKEN", "")

    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = notifier.notify_success("Constitutional Law")
        assert result is True
        req = mock_urlopen.call_args[0][0]
        data = json.loads(req.data.decode("utf-8"))
        assert data.get("type") == "message"
        assert data["attachments"][0]["contentType"] == "application/vnd.microsoft.card.adaptive"


def test_mask_url_sanitizes_tokens():
    discord = "https://discord.com/api/webhooks/123456789/SuperSecretTokenHere"
    masked_discord = notifier._mask_url(discord)
    assert "SuperSecretTokenHere" not in masked_discord
    assert "123456789/********" in masked_discord

    telegram = "https://api.telegram.org/bot987654:SecretBotToken/sendMessage"
    masked_telegram = notifier._mask_url(telegram)
    assert "SecretBotToken" not in masked_telegram
    assert "bot********/sendMessage" in masked_telegram

    teams_azure = "https://prod-01.westus.logic.azure.com/workflows/123/triggers/manual/paths/invoke?api-version=2016-06-01&sig=VerySecretSignatureValue&other=1"
    masked_teams_azure = notifier._mask_url(teams_azure)
    assert "VerySecretSignatureValue" not in masked_teams_azure
    assert "sig=********" in masked_teams_azure

    teams_classic = "https://contoso.webhook.office.com/webhookb2/uuid/IncomingWebhook/SecretIncomingWebhookToken/tenant-uuid"
    masked_teams_classic = notifier._mask_url(teams_classic)
    assert "SecretIncomingWebhookToken" not in masked_teams_classic
    assert "IncomingWebhook/********/" in masked_teams_classic
