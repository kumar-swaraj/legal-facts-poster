import datetime
import json
import urllib.error
import urllib.request

from .config import (
    BASE_URL,
    HEALTHCHECK_URL,
    MAX_RETRIES,
    NOTIFY_ON,
    POST_INTERVAL_HOURS,
    TEAMS_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WEBHOOK_URL,
)


def _mask_url(url: str) -> str:
    """Masks secret tokens from webhook and bot URLs to prevent credential leakage in logs."""
    import re

    # Discord: https://discord.com/api/webhooks/<id>/<token>
    if "discord.com/api/webhooks" in url:
        return re.sub(r"(webhooks/\d+/)[^/?#]+", r"\1********", url)
    # Telegram: https://api.telegram.org/bot<token>/<method>
    if "api.telegram.org/bot" in url:
        return re.sub(r"(bot)[^/]+(/)", r"\1********\2", url)
    # Microsoft Teams / Azure Logic Apps: sig query parameter or webhookb2 token
    if any(host in url for host in ("logic.azure.com", "webhook.office.com", "office.com/webhook")):
        url = re.sub(r"([?&]sig=)[^&]+", r"\1********", url)
        url = re.sub(r"(IncomingWebhook/)[^/]+(/)", r"\1********\2", url)
        return url
    # Slack / generic long secret path
    parts = url.split("://", 1)
    if len(parts) == 2:
        scheme, rest = parts
        domain_and_path = rest.split("/", 1)
        if len(domain_and_path) == 2:
            domain, path = domain_and_path
            if len(path) > 16:
                return f"{scheme}://{domain}/{path[:6]}...********"
    return url


def _send_http_post(url: str, payload: dict) -> bool:
    """Dispatches a JSON POST request with a safe timeout bound."""
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "LegalFactsPoster/0.1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return bool(resp.status in (200, 202, 204))
    except Exception as exc:
        safe_url = _mask_url(url)
        print(f"  \033[33mNotice: Could not dispatch webhook to {safe_url}: {exc}\033[0m")
        return False


def _send_discord(
    webhook_url: str,
    event: str,
    topic: str | None,
    tags: list[str] | None,
    error: str | None,
    headline: str | None = None,
    takeaway: str | None = None,
    category: str | None = None,
    model_name: str | None = None,
    attempt: int | None = None,
) -> bool:
    """Builds and delivers a rich color-coded embed to Discord."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if event == "post_success":
        clean_tags = "  ".join(f"`#{t}`" for t in (tags or [])) if tags else "None"
        description_parts = []
        if headline:
            description_parts.append(f"**{headline}**")
        if takeaway:
            description_parts.append(f"> *{takeaway}*")
        desc = (
            "\n\n".join(description_parts)
            if description_parts
            else f"**Topic**: {topic or 'Unknown Topic'}"
        )

        community_url = f"{BASE_URL.rstrip('/')}/community" if BASE_URL else None
        fields = [
            {"name": "📌 Topic", "value": topic or "General Law", "inline": True},
        ]
        if category:
            fields.append({"name": "📂 Category", "value": category, "inline": True})
        fields.append({"name": "🏷️ Tags Applied", "value": clean_tags, "inline": True})
        if model_name:
            fields.append({"name": "🤖 AI Model", "value": model_name, "inline": True})
        if attempt is not None:
            fields.append(
                {"name": "🎯 Attempt", "value": f"{attempt} of {MAX_RETRIES + 1}", "inline": True}
            )
        fields.append(
            {"name": "⏰ Next Post", "value": f"In ~{POST_INTERVAL_HOURS} hours", "inline": True}
        )

        embed = {
            "title": "⚖️ Legal Fact Published Successfully",
            "url": community_url,
            "description": desc,
            "color": 3066993,  # Green (#2ecc71)
            "fields": fields,
            "footer": {"text": "Legal Facts Poster • Autonomous Agent"},
            "timestamp": now_iso,
        }
    else:
        err_msg = error[:600] if error else "Unknown error encountered"
        fields = [
            {"name": "Error Details", "value": f"```{err_msg}```", "inline": False},
        ]
        if attempt is not None:
            fields.append(
                {
                    "name": "Attempts Exhausted",
                    "value": f"{attempt} of {MAX_RETRIES + 1}",
                    "inline": True,
                }
            )
        embed = {
            "title": "🚨 Post Publication Failed",
            "description": f"**Topic**: {topic or 'N/A'}\n\nAll automated retry attempts were exhausted.",
            "color": 15158332,  # Red (#e74c3c)
            "fields": fields,
            "footer": {"text": "Legal Facts Poster • Error Alert"},
            "timestamp": now_iso,
        }

    return _send_http_post(webhook_url, {"username": "Legal Facts Poster", "embeds": [embed]})


def _send_telegram(
    token: str,
    chat_id: str,
    event: str,
    topic: str | None,
    tags: list[str] | None,
    error: str | None,
    headline: str | None = None,
    category: str | None = None,
    model_name: str | None = None,
) -> bool:
    """Dispatches a clean Markdown formatted notification via Telegram Bot API."""
    if event == "post_success":
        clean_tags = " ".join(f"#{t}" for t in (tags or [])) if tags else ""
        lines = [
            "⚖️ *Legal Fact Published Successfully*\n",
            f"📌 *Topic:* {topic or 'Unknown'}",
        ]
        if headline:
            lines.append(f"💡 *Headline:* {headline}")
        if category:
            lines.append(f"📂 *Category:* {category}")
        if clean_tags:
            lines.append(f"🏷 *Tags Applied:* {clean_tags}")
        if model_name:
            lines.append(f"🤖 *Model:* {model_name}")
        lines.append(f"⏱ *Next Post:* In ~{POST_INTERVAL_HOURS} hour(s)")
        text = "\n".join(lines)
    else:
        err_msg = error[:500] if error else "Unknown error"
        text = (
            "🚨 *Post Publication Failed*\n\n"
            f"📌 *Topic:* {topic or 'N/A'}\n"
            f"⚠️ *Error:* `{err_msg}`\n\n"
            "All automated retry attempts have failed."
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    return _send_http_post(url, payload)


def _send_generic_webhook(
    url: str,
    event: str,
    topic: str | None,
    tags: list[str] | None,
    error: str | None,
    headline: str | None = None,
    takeaway: str | None = None,
    category: str | None = None,
    model_name: str | None = None,
    attempt: int | None = None,
) -> bool:
    """Dispatches a standard JSON payload to any custom webhook endpoint."""
    payload = {
        "event": event,
        "topic": topic,
        "headline": headline,
        "takeaway": takeaway,
        "category": category,
        "model": model_name,
        "tags": tags or [],
        "attempt": attempt,
        "error": error,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    return _send_http_post(url, payload)


def _is_teams_webhook(url: str) -> bool:
    """Detects whether a URL points to a Microsoft Teams incoming webhook or Azure Logic Apps workflow."""
    return any(
        host in url for host in ("webhook.office.com", "logic.azure.com", "office.com/webhook")
    )


def _send_teams(
    webhook_url: str,
    event: str,
    topic: str | None,
    tags: list[str] | None,
    error: str | None,
    headline: str | None = None,
    takeaway: str | None = None,
    category: str | None = None,
    model_name: str | None = None,
    attempt: int | None = None,
) -> bool:
    """Builds and delivers a native Adaptive Card (v1.4) to Microsoft Teams."""
    if event == "post_success":
        clean_tags = "  ".join(f"#{t}" for t in (tags or [])) if tags else "None"
        card_body: list[dict[str, object]] = [
            {
                "type": "TextBlock",
                "size": "Medium",
                "weight": "Bolder",
                "color": "Good",
                "text": "⚖️ Legal Fact Published Successfully",
            }
        ]

        if headline:
            card_body.append(
                {
                    "type": "TextBlock",
                    "text": f"**{headline}**",
                    "wrap": True,
                    "weight": "Bolder",
                }
            )

        if takeaway:
            card_body.append(
                {
                    "type": "TextBlock",
                    "text": f"_{takeaway}_",
                    "wrap": True,
                    "isSubtle": True,
                }
            )

        facts: list[dict[str, str]] = [
            {"title": "📌 Topic", "value": topic or "General Law"},
        ]
        if category:
            facts.append({"title": "📂 Category", "value": category})
        facts.append({"title": "🏷️ Tags", "value": clean_tags})
        if model_name:
            facts.append({"title": "🤖 AI Model", "value": model_name})
        if attempt is not None:
            facts.append({"title": "🎯 Attempt", "value": f"{attempt} of {MAX_RETRIES + 1}"})
        facts.append({"title": "⏰ Next Post", "value": f"In ~{POST_INTERVAL_HOURS} hours"})

        card_body.append({"type": "FactSet", "facts": facts})
        card_body.append(
            {
                "type": "TextBlock",
                "size": "Small",
                "isSubtle": True,
                "text": "Legal Facts Poster • Autonomous Agent",
            }
        )

        actions: list[dict[str, str]] = []
        if BASE_URL:
            community_url = f"{BASE_URL.rstrip('/')}/community"
            actions.append(
                {
                    "type": "Action.OpenUrl",
                    "title": "🌐 View Community",
                    "url": community_url,
                }
            )

        adaptive_card: dict[str, object] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": card_body,
        }
        if actions:
            adaptive_card["actions"] = actions
    else:
        err_msg = error[:600] if error else "Unknown error encountered"
        failure_facts = [
            {"title": "⚠️ Error Details", "value": err_msg},
        ]
        if attempt is not None:
            failure_facts.append(
                {"title": "🎯 Attempts Exhausted", "value": f"{attempt} of {MAX_RETRIES + 1}"}
            )

        card_body = [
            {
                "type": "TextBlock",
                "size": "Medium",
                "weight": "Bolder",
                "color": "Attention",
                "text": "🚨 Post Publication Failed",
            },
            {
                "type": "TextBlock",
                "text": f"**Topic**: {topic or 'N/A'}\n\nAll automated retry attempts were exhausted.",
                "wrap": True,
            },
            {"type": "FactSet", "facts": failure_facts},
            {
                "type": "TextBlock",
                "size": "Small",
                "isSubtle": True,
                "text": "Legal Facts Poster • Error Alert",
            },
        ]
        adaptive_card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": card_body,
        }

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": adaptive_card,
            }
        ],
    }
    return _send_http_post(webhook_url, payload)


def send_notification(
    event: str,
    topic: str | None = None,
    tags: list[str] | None = None,
    error: str | None = None,
    headline: str | None = None,
    takeaway: str | None = None,
    category: str | None = None,
    model_name: str | None = None,
    attempt: int | None = None,
) -> bool:
    """
    Dispatches alerts to configured targets (Discord, Teams, Telegram, or generic webhooks).
    Suppresses success notifications if NOTIFY_ON is set to 'failures_only'.
    Never raises an uncaught exception.
    """
    if event == "post_success" and NOTIFY_ON == "failures_only":
        return True

    delivered = False

    # 1. Deliver to TEAMS_WEBHOOK_URL if explicitly configured
    if TEAMS_WEBHOOK_URL:
        delivered = (
            _send_teams(
                TEAMS_WEBHOOK_URL,
                event,
                topic,
                tags,
                error,
                headline=headline,
                takeaway=takeaway,
                category=category,
                model_name=model_name,
                attempt=attempt,
            )
            or delivered
        )

    # 2. Deliver to Webhook URL (Discord, Teams auto-detect, or Generic)
    if WEBHOOK_URL and WEBHOOK_URL != TEAMS_WEBHOOK_URL:
        if "discord.com/api/webhooks" in WEBHOOK_URL:
            delivered = (
                _send_discord(
                    WEBHOOK_URL,
                    event,
                    topic,
                    tags,
                    error,
                    headline=headline,
                    takeaway=takeaway,
                    category=category,
                    model_name=model_name,
                    attempt=attempt,
                )
                or delivered
            )
        elif _is_teams_webhook(WEBHOOK_URL):
            delivered = (
                _send_teams(
                    WEBHOOK_URL,
                    event,
                    topic,
                    tags,
                    error,
                    headline=headline,
                    takeaway=takeaway,
                    category=category,
                    model_name=model_name,
                    attempt=attempt,
                )
                or delivered
            )
        else:
            delivered = (
                _send_generic_webhook(
                    WEBHOOK_URL,
                    event,
                    topic,
                    tags,
                    error,
                    headline=headline,
                    takeaway=takeaway,
                    category=category,
                    model_name=model_name,
                    attempt=attempt,
                )
                or delivered
            )

    # 2. Deliver to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        delivered = (
            _send_telegram(
                TELEGRAM_BOT_TOKEN,
                TELEGRAM_CHAT_ID,
                event,
                topic,
                tags,
                error,
                headline=headline,
                category=category,
                model_name=model_name,
            )
            or delivered
        )

    return delivered


def notify_success(
    topic: str,
    tags: list[str] | None = None,
    headline: str | None = None,
    takeaway: str | None = None,
    category: str | None = None,
    model_name: str | None = None,
    attempt: int | None = None,
) -> bool:
    """Helper to dispatch successful post publication notifications."""
    return send_notification(
        event="post_success",
        topic=topic,
        tags=tags,
        headline=headline,
        takeaway=takeaway,
        category=category,
        model_name=model_name,
        attempt=attempt,
    )


def notify_failure(
    error: str,
    topic: str | None = None,
    attempt: int | None = None,
) -> bool:
    """Helper to dispatch fatal publication failure alerts."""
    return send_notification(event="post_failure", topic=topic, error=error, attempt=attempt)


def ping_healthcheck() -> bool:
    """
    Sends an HTTP GET heartbeat ping to dead-man's switch services (e.g., Healthchecks.io / Uptime Kuma).
    """
    if not HEALTHCHECK_URL:
        return True
    if not (HEALTHCHECK_URL.startswith("http://") or HEALTHCHECK_URL.startswith("https://")):
        return False
    try:
        req = urllib.request.Request(  # noqa: S310
            HEALTHCHECK_URL,
            headers={"User-Agent": "LegalFactsPoster/0.1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return bool(resp.status == 200)
    except Exception as exc:
        print(f"  \033[33mNotice: Healthcheck ping failed: {exc}\033[0m")
        return False
