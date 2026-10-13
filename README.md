# Legal Facts Poster (`legal-facts-poster`)
> **An Autonomous AI Agent & Browser Automation Worker for Legal Community Feeds**

[![CI](https://github.com/kumar-swaraj/legal-facts-poster/actions/workflows/ci.yml/badge.svg)](https://github.com/kumar-swaraj/legal-facts-poster/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`legal-facts-poster` is an autonomous AI agent worker that bridges large language model intelligence with headless browser automation. It continuously synthesizes educational legal insights across Indian jurisprudence and publishes them directly to community platforms with native rich HTML formatting, persistent sessions, duplicate prevention memory, and humanized jitter scheduling.

---

### What Is This Tool?

`legal-facts-poster` is an **Autonomous AI Agent Worker** that unifies three core capabilities:

1. **The Brain (AI Reasoning Agent)**: Evaluates past posting history (`posted_history.txt`), rotates across core legal domains, and prompts your choice of LLM (Google Gemini, OpenAI, Claude, DeepSeek, Grok, Kimi, Groq, OpenRouter, or local models) to synthesize concise, structured legal insights.
2. **The Hands (Browser Automation Bot)**: Uses Playwright to authenticate, persist login sessions (`session.json`), navigate dynamic platform UIs, insert rich HTML (`<strong>`, `<ul><li>`, `<em>`) into WYSIWYG editors, and select community tags from interactive comboboxes.
3. **The Engine (Autonomous Scheduler & CLI)**: Operates either as an immediate single-post runner (`post-once`) or an autonomous recurring daemon (`legal-post`) with anti-bot randomized timing jitter (±5–10 min) and auto-retry resilience.

> 📖 **Need a quick cheat-sheet?** Check out the complete [**Command Reference Guide (COMMANDS.md)**](COMMANDS.md).

---

## Features

- **Jurisprudence Domain Rotation**: Rotates through core branches of Indian law (Constitutional Law, Criminal Law, Consumer Protection, Cyber Law, Citizen Rights, and Commercial Law).
- **Rich Text Formatting**: Emits native HTML (`<strong>`, `<ul><li>`, `<em>`) into the platform's WYSIWYG editor so headlines, bullet lists, and takeaways render with true typography.
- **Interactive Multi-Tag Selection**: Selects at least 2 relevant community tags via the platform's combobox with automatic fallback.
- **Session Persistence**: Stores authenticated session state (`session.json`) after initial login, eliminating repetitive logins and accelerating subsequent post cycles.
- **Configurable Scheduling with Jitter**: Supports custom hourly post intervals with optional humanized jitter (±5–10 minutes) to avoid predictable robot-like posting times.
- **Reliability & Auto-Retry**: Automatically retries on network hiccups before falling back to the schedule loop.
- **Pip-Installable CLI**: Clean package structure supporting direct command line invocation (`legal-post` or `legal-facts-poster`).

---

## Installation & Quick Start

### 1. Isolated CLI Install (Recommended)
Install the standalone CLI globally in an isolated environment without polluting your system Python:
```bash
uv tool install git+https://github.com/kumar-swaraj/legal-facts-poster.git
uv run playwright install chromium
```
Check your installed version:
```bash
legal-post --version
```

### 2. Ephemeral Zero-Install (On-Demand via `uvx`)
Run directly without installing any packages:
```bash
uvx --from git+https://github.com/kumar-swaraj/legal-facts-poster.git post-once --help
```

### 3. Local Development (`uv` / `pip`)
```bash
# Clone and install with dev tools
git clone https://github.com/kumar-swaraj/legal-facts-poster.git
cd legal-facts-poster
uv pip install -e ".[dev]"
uv run playwright install chromium
```

---

## Configuration

When a user downloads and installs `legal-facts-poster`, credentials can be supplied via any of the following methods:

### Method 1: Interactive Setup Wizard (Recommended)
Run the guided terminal setup wizard with hidden password masking:
```bash
legal-config
# or
legal-post config
```
This prompts for your username, password, Gemini API key, and platform URL, and saves them securely to `~/.config/legal-facts-poster/.env` with strict `0600` permissions. Once configured, you can run `legal-post` from anywhere on your machine!

### Method 2: Generate Local `.env`
Run the template generator in your project folder:
```bash
legal-post --init-env
```
This creates a local `.env` file template ready for your credentials.

### Method 3: Shell Environment Variables
Export variables in your `~/.zshrc` or `~/.bashrc`:
```bash
export MY_SITE_USERNAME="your-email@example.com"
export MY_SITE_PASSWORD="your-password"
export GEMINI_API_KEY="your-gemini-api-key"
export BASE_URL="https://your-platform.com"
```

### Method 4: Custom File Path via `--env-file`
Pass any custom `.env` file explicitly at runtime:
```bash
legal-post --env-file /path/to/my-secrets.env
```

---

### Configuration Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `MY_SITE_USERNAME` | Platform account email / username | *Required* |
| `MY_SITE_PASSWORD` | Platform account password | *Required* |
| `AI_PROVIDER` | AI provider (`gemini`, `openai`, `claude`, `deepseek`, `grok`, `kimi`, `groq`, `openrouter`, `custom`) | `gemini` |
| `AI_API_KEY` | API key for your chosen AI provider | *Required* |
| `AI_MODEL` | Optional model name override | Provider default |
| `AI_BASE_URL` | Optional custom OpenAI-compatible endpoint URL (for Ollama, vLLM, etc.) | Provider default |
| `BASE_URL` | Target platform base URL (e.g. `https://your-platform-domain.com`) | *Required* |
| `HEADLESS` | Run browser in background (`true` or `false`) | `false` |
| `POST_INTERVAL_HOURS`| Interval in hours between automated posts | `4.0` |
| `ENABLE_JITTER` | Apply random delay (±5-10m) before posting | `true` |
| `JITTER_MAX_MINUTES` | Maximum jitter minutes | `10` |
| `SESSION_FILE` | File to save authenticated session state | `session.json` |
| `HISTORY_FILE` | File to track posted topics to prevent duplicates | `posted_history.txt` |
| `MAX_RETRIES` | Retry attempts on network/browser failures | `2` |
| `RETRY_DELAY_SECONDS`| Delay in seconds between retries | `60` |
| `WEBHOOK_URL` | Discord, MS Teams, Slack, or generic webhook URL for alerts | `""` (Disabled) |
| `TEAMS_WEBHOOK_URL` | Dedicated Microsoft Teams webhook URL (Adaptive Cards v1.4) | `""` (Disabled) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token for direct alert messages | `""` (Disabled) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID to receive alert messages | `""` (Disabled) |
| `NOTIFY_ON` | Alert level: `all` (posts + errors) or `failures_only` | `all` |
| `HEALTHCHECK_URL` | Dead-man's switch ping URL (Healthchecks.io) | `""` (Disabled) |

### Supported AI Providers

You can use any of the following AI providers by setting `AI_PROVIDER` and your API key:

| Provider | `AI_PROVIDER` | Default Model | Get API Key |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | `gemini` | `gemini-2.5-flash` | [Google AI Studio](https://aistudio.google.com/) |
| **OpenAI** | `openai` | `gpt-4o-mini` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Anthropic Claude** | `claude` | `claude-3-5-haiku-20241022` | [Anthropic Console](https://console.anthropic.com/) |
| **DeepSeek** | `deepseek` | `deepseek-chat` | [DeepSeek Platform](https://platform.deepseek.com/) |
| **xAI Grok** | `grok` | `grok-2-latest` | [xAI Console](https://console.x.ai/) |
| **Moonshot AI (Kimi)** | `kimi` | `moonshot-v1-8k` | [Moonshot Platform](https://platform.moonshot.cn/) |
| **Groq** | `groq` | `llama-3.3-70b-versatile` | [Groq Console](https://console.groq.com/keys) |
| **OpenRouter** | `openrouter` | `anthropic/claude-3.5-haiku` | [OpenRouter](https://openrouter.ai/keys) |
| **Custom / Ollama** | `custom` | *Specified in `AI_MODEL`* | Local or Self-Hosted |


---

## Usage

### 1. Publishing a Single Post (Post Once & Exit)

**Via direct script:**
```bash
python post_once.py
# Or headless in background:
python post_once.py --headless
```

**Via CLI command:**
```bash
post-once
# Or using the flag:
legal-post --once
```

---

### 2. Scheduled Autonomous Posting

Run continuously on default 4-hour schedule (with random jitter):
```bash
legal-post
```

Run in headless mode (background):
```bash
legal-post --headless
```

Run on a custom 2-hour interval:
```bash
legal-post -i 2.0
```

Run N posts then exit:
```bash
legal-post -n 5
```

Show all CLI options:
```bash
legal-post --help
```

---

## Docker & Cloud Deployment

Deploy the autonomous posting daemon 24/7 on a VPS, server, or cloud VM with zero local Python or browser installation:

```bash
# 1. Start daemon in background (auto-restarts on reboot)
docker compose up -d

# 2. View live execution logs
docker compose logs -f

# 3. Stop container
docker compose down
```

> **Security Hardened**: The container image drops root privileges and runs under the unprivileged `pwuser` account with persistent volume mounts for `session.json` and `posted_history.txt`. Pre-built images are published to `ghcr.io/kumar-swaraj/legal-facts-poster:latest`.

---

## Developer Tooling & Quality Checks

This project uses the modern **Astral** toolchain (`uv`, `pytest`, `Ruff`, `MyPy`) for zero-friction quality assurance:

```bash
# Run automated unit test suite
uv run pytest

# Check code style & linter rules (Ruff)
uv run ruff check . --fix

# Format code (Ruff)
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .

# Static type checking across source and tests (MyPy)
uv run mypy src/ tests/

# Full verification suite
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ tests/ && uv run pytest
```

---

## Project Architecture

```
legal-facts-poster/
├── .github/
│   ├── dependabot.yml       # Automated dependency security scanning
│   └── workflows/
│       ├── ci.yml            # Automated CI linting, typing & unit tests
│       └── release.yml       # Auto-release & GHCR Docker publish on v* tags
├── Dockerfile                # Production non-root container with Playwright
├── docker-compose.yml        # Docker service definition with volume persistence
├── COMMANDS.md               # Categorized command cheat-sheet
├── SECURITY.md               # Security architecture & vulnerability policy
├── LICENSE                   # MIT Open Source License
├── README.md                 # Project documentation & guides
├── pyproject.toml            # PEP 517/621 package metadata & quality configs
├── .env.example              # Environment variables template
├── tests/                    # Automated pytest suite (CLI, config, history, categories)
└── src/
    └── legal_facts_poster/
        ├── __init__.py       # Package interface & version export (__version__)
        ├── config.py         # Multi-provider environment loading & validation
        ├── categories.py     # Indian law domain definitions & rotation logic
        ├── history.py        # History persistence manager
        ├── ai_generator.py   # Multi-model structured fact generation & HTML formatting
        ├── browser_bot.py    # Playwright browser automation & session persistence (0600)
        ├── notifier.py       # Observability & alerts (Discord embeds, Teams Adaptive Cards, Telegram, webhooks)
        ├── runner.py         # Task orchestration, SIGTERM handling & schedule loop
        ├── wizard.py         # Interactive terminal setup wizard
        └── cli.py            # CLI argument parsing (argparse) & command dispatcher
```

---

## Security

Please see [**SECURITY.md**](SECURITY.md) for supported versions, our defense-in-depth security model, and how to report vulnerabilities responsibly.
