# Legal Facts Poster — Command Reference Guide

A complete, categorized cheat-sheet of all commands available in `legal-facts-poster`.

---

## 1. Quick Start / Daily Commands

| Task | Command |
| :--- | :--- |
| **Publish a single post immediately** | `post-once` *(or `python post_once.py`)* |
| **Publish silently in the background** | `post-once --headless` |
| **Start autonomous recurring posting** | `legal-post` *(or `python main.py`)* |
| **Run interactive setup wizard** | `legal-config` *(or `legal-post --config`)* |
| **Generate a `.env` template in current directory** | `legal-post --init-env` |

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

## 5. Development, Linting & Type Checking

Powered by the **Astral** ecosystem (`uv`, `Ruff`, `MyPy`):

```bash
# Install package with developer tools
uv pip install -e ".[dev]"

# Install Playwright browser dependencies
uv run playwright install chromium

# Check and auto-fix linting issues (Ruff)
uv run ruff check . --fix

# Format all code files (Ruff)
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .

# Run static type checking (MyPy)
uv run mypy src/

# Run complete linting + formatting + type check suite in one line
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

---

## 6. Diagnostics & Scratch Testing

```bash
# Test AI generation logic directly in terminal (without opening browser)
uv run python -c "from legal_facts_poster.ai_generator import generate_new_fact; t, h, tags = generate_new_fact(); print('Topic:', t); print('Tags:', tags)"

# Test config resolution (which provider and API key are active)
uv run python -c "from legal_facts_poster.config import AI_PROVIDER, AI_MODEL, USERNAME, BASE_URL; print(f'Provider: {AI_PROVIDER} | Model: {AI_MODEL} | User: {USERNAME} | URL: {BASE_URL}')"

# View topic history (preventing duplicates)
cat posted_history.txt

# Reset session cookies (force fresh login)
rm session.json
```

---

## 7. Git & Publishing Commands

```bash
# Check working tree status
git status

# Add remote GitHub repository
git remote add origin https://github.com/<your-username>/legal-facts-poster.git

# Set main branch and push
git branch -M main
git push -u origin main
```
