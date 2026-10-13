import os

from dotenv import find_dotenv, load_dotenv

# Search locations: 1. Current directory / parents, 2. User home directory
load_dotenv(find_dotenv(usecwd=True))
_global_config = os.path.expanduser("~/.config/legal-facts-poster/.env")
if os.path.exists(_global_config):
    load_dotenv(_global_config)
_home_env = os.path.expanduser("~/.legal-facts-poster.env")
if os.path.exists(_home_env):
    load_dotenv(_home_env)


def _to_bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "t", "y")


def _to_float(val: str | None, default: float) -> float:
    try:
        return float(val) if val is not None else default
    except ValueError:
        return default


def _to_int(val: str | None, default: int) -> int:
    try:
        return int(val) if val is not None else default
    except ValueError:
        return default


PROVIDER_DEFAULTS = {
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"],
        "key_env": "GEMINI_API_KEY",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o"],
        "key_env": "OPENAI_API_KEY",
    },
    "claude": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-5-haiku-20241022", "claude-3-7-sonnet-20250219"],
        "key_env": "ANTHROPIC_API_KEY",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat"],
        "key_env": "DEEPSEEK_API_KEY",
    },
    "grok": {
        "name": "xAI Grok",
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-2-latest", "grok-beta"],
        "key_env": "GROK_API_KEY",
    },
    "kimi": {
        "name": "Moonshot AI (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k"],
        "key_env": "KIMI_API_KEY",
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        "key_env": "GROQ_API_KEY",
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["anthropic/claude-3.5-haiku", "openai/gpt-4o-mini", "deepseek/deepseek-chat"],
        "key_env": "OPENROUTER_API_KEY",
    },
    "custom": {
        "name": "Custom / OpenAI-Compatible",
        "base_url": "",
        "models": [],
        "key_env": "AI_API_KEY",
    },
}


def _resolve_ai_config():
    provider = os.getenv("AI_PROVIDER", "").lower()
    if not provider:
        if os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        elif os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"):
            provider = "grok"
        elif os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY"):
            provider = "kimi"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        elif os.getenv("OPENROUTER_API_KEY"):
            provider = "openrouter"
        elif os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY"):
            provider = "claude"
        else:
            provider = "gemini"

    key = os.getenv("AI_API_KEY", "")
    if not key:
        if provider == "gemini":
            key = os.getenv("GEMINI_API_KEY", "")
        elif provider == "openai":
            key = os.getenv("OPENAI_API_KEY", "")
        elif provider == "claude":
            key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("CLAUDE_API_KEY", "")
        elif provider == "deepseek":
            key = os.getenv("DEEPSEEK_API_KEY", "")
        elif provider == "grok":
            key = os.getenv("GROK_API_KEY", "") or os.getenv("XAI_API_KEY", "")
        elif provider == "kimi":
            key = os.getenv("KIMI_API_KEY", "") or os.getenv("MOONSHOT_API_KEY", "")
        elif provider == "groq":
            key = os.getenv("GROQ_API_KEY", "")
        elif provider == "openrouter":
            key = os.getenv("OPENROUTER_API_KEY", "")
        if not key:
            key = os.getenv("GEMINI_API_KEY", "")

    return provider, key, os.getenv("AI_MODEL", ""), os.getenv("AI_BASE_URL", "")


# AI Provider Configuration
AI_PROVIDER, AI_API_KEY, AI_MODEL, AI_BASE_URL = _resolve_ai_config()
GEMINI_API_KEY: str = AI_API_KEY  # Backwards compatibility

# Configuration values
USERNAME: str = os.getenv("MY_SITE_USERNAME", "")
PASSWORD: str = os.getenv("MY_SITE_PASSWORD", "")
BASE_URL: str = os.getenv("BASE_URL", "").rstrip("/")
HEADLESS: bool = _to_bool(os.getenv("HEADLESS"), default=False)
SESSION_FILE: str = os.getenv("SESSION_FILE", "session.json")
HISTORY_FILE: str = os.getenv("HISTORY_FILE", "posted_history.txt")

POST_INTERVAL_HOURS: float = _to_float(os.getenv("POST_INTERVAL_HOURS"), default=4.0)
ENABLE_JITTER: bool = _to_bool(os.getenv("ENABLE_JITTER"), default=True)
JITTER_MAX_MINUTES: int = _to_int(os.getenv("JITTER_MAX_MINUTES"), default=10)

MAX_RETRIES: int = _to_int(os.getenv("MAX_RETRIES"), default=2)
RETRY_DELAY_SECONDS: int = _to_int(os.getenv("RETRY_DELAY_SECONDS"), default=60)

# Observability & Alerting
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
TEAMS_WEBHOOK_URL: str = os.getenv("TEAMS_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
NOTIFY_ON: str = os.getenv("NOTIFY_ON", "all").lower()
HEALTHCHECK_URL: str = os.getenv("HEALTHCHECK_URL", "")


def reload_config(custom_env_path: str | None = None) -> None:
    """Reloads environment variables, optionally from a custom .env file."""
    global USERNAME, PASSWORD, GEMINI_API_KEY, BASE_URL, HEADLESS, SESSION_FILE, HISTORY_FILE
    global POST_INTERVAL_HOURS, ENABLE_JITTER, JITTER_MAX_MINUTES, MAX_RETRIES, RETRY_DELAY_SECONDS
    global AI_PROVIDER, AI_API_KEY, AI_MODEL, AI_BASE_URL
    global \
        WEBHOOK_URL, \
        TEAMS_WEBHOOK_URL, \
        TELEGRAM_BOT_TOKEN, \
        TELEGRAM_CHAT_ID, \
        NOTIFY_ON, \
        HEALTHCHECK_URL

    if custom_env_path and os.path.exists(custom_env_path):
        load_dotenv(custom_env_path, override=True)

    AI_PROVIDER, AI_API_KEY, AI_MODEL, AI_BASE_URL = _resolve_ai_config()
    GEMINI_API_KEY = AI_API_KEY

    USERNAME = os.getenv("MY_SITE_USERNAME", "")
    PASSWORD = os.getenv("MY_SITE_PASSWORD", "")
    BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
    HEADLESS = _to_bool(os.getenv("HEADLESS"), default=False)
    SESSION_FILE = os.getenv("SESSION_FILE", "session.json")
    HISTORY_FILE = os.getenv("HISTORY_FILE", "posted_history.txt")
    POST_INTERVAL_HOURS = _to_float(os.getenv("POST_INTERVAL_HOURS"), default=4.0)
    ENABLE_JITTER = _to_bool(os.getenv("ENABLE_JITTER"), default=True)
    JITTER_MAX_MINUTES = _to_int(os.getenv("JITTER_MAX_MINUTES"), default=10)
    MAX_RETRIES = _to_int(os.getenv("MAX_RETRIES"), default=2)
    RETRY_DELAY_SECONDS = _to_int(os.getenv("RETRY_DELAY_SECONDS"), default=60)

    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    NOTIFY_ON = os.getenv("NOTIFY_ON", "all").lower()
    HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL", "")


def validate_config() -> None:
    """Validates that necessary configuration is present."""
    import sys

    missing = []
    if not USERNAME:
        missing.append("MY_SITE_USERNAME")
    if not PASSWORD:
        missing.append("MY_SITE_PASSWORD")
    if not AI_API_KEY:
        missing.append(f"AI API Key (AI_API_KEY or {AI_PROVIDER.upper()}_API_KEY)")
    if not BASE_URL:
        missing.append("BASE_URL")

    if missing:
        if sys.stdin.isatty():
            print(f"\n\033[33mNotice: Missing required settings: {', '.join(missing)}\033[0m")
            try:
                resp = (
                    input(
                        "\033[1mWould you like to run the interactive setup wizard now? [Y/n]: \033[0m"
                    )
                    .strip()
                    .lower()
                )
                if resp in ("", "y", "yes"):
                    from .wizard import run_wizard

                    run_wizard()
                    return
            except (KeyboardInterrupt, EOFError):
                print()
                sys.exit(0)

        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}.\n"
            "Provide them via:\n"
            "  1. Run the interactive setup wizard: 'legal-post --config'\n"
            "  2. A local '.env' file: 'legal-post --init-env'\n"
            "  3. Global config at '~/.config/legal-facts-poster/.env'\n"
            "  4. Standard shell environment variables (export KEY=value)"
        )


ENV_TEMPLATE = """# ==========================================
# Legal Facts Poster Configuration
# ==========================================

# 1. Platform Account Credentials (Required)
MY_SITE_USERNAME="your-email@example.com"
MY_SITE_PASSWORD="your-password"

# 2. AI Intelligence Provider (Required)
# Supported: gemini | openai | claude | deepseek | grok | kimi | groq | openrouter | custom
AI_PROVIDER="gemini"
AI_API_KEY="your-api-key"

# Optional AI model & endpoint overrides:
# AI_MODEL="gemini-2.5-flash"   # e.g. "gpt-4o-mini", "claude-3-5-haiku-20241022", "deepseek-chat", "grok-2-latest", "llama-3.3-70b-versatile"
# AI_BASE_URL=""                # Custom endpoint for Ollama (http://localhost:11434/v1), vLLM, or private proxy

# 3. Target Platform URL (Required)
BASE_URL="https://your-target-platform.com"

# 4. Browser Options
HEADLESS=false
SESSION_FILE=session.json
HISTORY_FILE=posted_history.txt

# 5. Scheduling (for continuous loop)
POST_INTERVAL_HOURS=4.0
ENABLE_JITTER=true
JITTER_MAX_MINUTES=10

# 6. Retry & Reliability
MAX_RETRIES=2
RETRY_DELAY_SECONDS=60

# 7. Observability & Alerts (Optional)
# Webhook URL for Discord, Slack, or generic POST
# WEBHOOK_URL="https://discord.com/api/webhooks/..."
# Dedicated Microsoft Teams webhook (Workflows or Office 365 Connector)
# TEAMS_WEBHOOK_URL="https://prod-XX.logic.azure.com/workflows/..."
# Or Telegram credentials:
# TELEGRAM_BOT_TOKEN="123456789:ABCDEF..."
# TELEGRAM_CHAT_ID="987654321"
# Notification mode: "all" (posts + failures) or "failures_only"
NOTIFY_ON="all"
# Passive liveness ping URL (Healthchecks.io / Uptime Kuma)
# HEALTHCHECK_URL="https://hc-ping.com/..."
"""


def init_env_template(target_path: str = ".env") -> str:
    """Creates a sample .env file if one does not already exist."""
    if os.path.exists(target_path):
        return f"File '{target_path}' already exists. Skipping."
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(ENV_TEMPLATE)
    return f"Created template configuration at '{target_path}'. Please fill in your credentials."
