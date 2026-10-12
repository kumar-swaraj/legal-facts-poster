# Legal Facts Poster — Command Reference Guide

A complete, categorized cheat-sheet of all commands available in `legal-facts-poster`.

---

## 1. Quick Start / Daily Commands

| Task | Command |
| :--- | :--- |
| **Install CLI globally (isolated sandbox)** | `uv tool install git+https://github.com/kumar-swaraj/legal-facts-poster.git` |
| **Run ephemerally (zero install)** | `uvx --from git+https://github.com/kumar-swaraj/legal-facts-poster.git post-once --help` |
| **Publish a single post immediately** | `post-once` *(or `python post_once.py`)* |
| **Publish silently in the background** | `post-once --headless` |
| **Start autonomous recurring posting** | `legal-post` *(or `python main.py`)* |
| **Check installed version** | `legal-post --version` |
| **Run unit test suite** | `uv run pytest` |
| **Run in Docker (background daemon)** | `docker compose up -d` |
| **View Docker daemon logs** | `docker compose logs -f` |
| **Stop Docker daemon** | `docker compose down` |
| **Run interactive setup wizard** | `legal-config` *(or `legal-post --config`)* |
| **Generate a `.env` template in current directory** | `legal-post --init-env` |

### Standalone Installation (`uv tool` / `pipx`)

```bash
# 1. Install CLI in an isolated sandbox with global PATH access
uv tool install git+https://github.com/kumar-swaraj/legal-facts-poster.git

# 2. Install Playwright browser binary (one-time requirement)
uv run playwright install chromium

# 3. Check version
legal-post --version

# 4. Update to latest commit anytime
uv tool upgrade legal-facts-poster
```

---

## 2. CLI Executables & Aliases

The package installs the following command-line aliases into your PATH:

- **`post-once`**: Dedicated entrypoint to publish exactly one legal insight and immediately terminate.
- **`legal-post`**: Main entrypoint for autonomous scheduled posting loops with jitter and auto-retry.
- **`legal-config`**: Guided terminal setup wizard for entering login credentials and selecting an AI provider.
- **`legal-facts-poster`**: Mirror alias for `legal-post`.
- **`poster`**: Short convenience alias for `legal-post`.

---

## 3. Command Line Options & Flags

### Single-Post Runner (`post-once`)
```bash
# Basic run (opens browser window)
post-once

# Headless mode (runs silently in background)
post-once --headless

# Display package version
post-once --version

# Use a specific .env file
post-once --env-file /path/to/.env

# Launch setup wizard before posting
post-once --config
```

### Scheduled Daemon (`legal-post`)
```bash
# Standard scheduled loop (posts immediately, then every 4 hours)
legal-post

# Custom schedule interval (e.g., every 6 hours)
legal-post -i 6.0

# Run in background (headless)
legal-post --headless

# Post exactly 3 times, then stop
legal-post -n 3

# Skip immediate first post; wait directly for the scheduled interval
legal-post --skip-immediate

# Run once and exit (identical to post-once)
legal-post --once

# Display package version
legal-post --version
```

---

## 4. Configuration & Credentials

```bash
# 1. Interactive setup wizard (masked passwords, saves to ~/.config/legal-facts-poster/.env)
legal-config

# 2. Generate sample .env file in the current working directory
legal-post --init-env

# 3. Specify custom configuration file at runtime
legal-post --env-file ./production.env
```

---

## 5. Development, Testing, Linting & Type Checking

Powered by the **Astral** ecosystem (`uv`, `pytest`, `Ruff`, `MyPy`):

```bash
# Install package with developer tools
uv pip install -e ".[dev]"

# Install Playwright browser dependencies
uv run playwright install chromium

# Run automated unit test suite
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Check and auto-fix linting issues (Ruff)
uv run ruff check . --fix

# Format all code files (Ruff)
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .

# Run static type checking (MyPy)
uv run mypy src/ tests/

# Run complete linting + formatting + type check + test suite in one line
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ tests/ && uv run pytest
```

---

## 6. Docker & Container Deployment

Run 24/7 autonomously on a VPS, server, or local Docker daemon without installing Python or browser binaries on the host:

```bash
# 1. Build and run the daemon in the background
docker compose up -d

# 2. Stream live execution and posting logs
docker compose logs -f

# 3. Check container status
docker compose ps

# 4. Stop the container
docker compose down

# Optional: Run a single post directly via Docker
docker compose run --rm poster post-once --headless
```

---

## 7. Diagnostics & Scratch Testing

```bash
# Test AI generation logic directly in terminal (without opening browser)
uv run python -c "from legal_facts_poster.ai_generator import generate_new_fact; t, h, tags = generate_new_fact(); print('Topic:', t); print('Tags:', tags)"

# Test config resolution (which provider and API key are active)
uv run python -c "from legal_facts_poster.config import AI_PROVIDER, AI_MODEL, USERNAME, BASE_URL; print(f'Provider: {AI_PROVIDER} | Model: {AI_MODEL} | User: {USERNAME} | URL: {BASE_URL}')"

# Test webhook alert dispatch (sends test card to Discord / Telegram)
uv run python -c "from legal_facts_poster.notifier import notify_success; notify_success('Test Alert: Connectivity Verified', tags=['Test', 'Alert'])"

# View topic history (preventing duplicates)
cat posted_history.txt

# Reset session cookies (force fresh login)
rm session.json
```

---

## 8. Releases & Version Publishing

Publishing new releases is fully automated through GitHub Actions:

```bash
# 1. Ensure all changes are committed and pushed
git status

# 2. Tag a new semantic version
git tag -s v0.1.0 -m "Release v0.1.0: unit tests, containerization, and release automation"

# 3. Push the tag to trigger GitHub Release workflow (.github/workflows/release.yml)
git push origin v0.1.0
```
