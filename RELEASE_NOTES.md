# Legal Facts Poster v0.1.0 — Initial Official Release ⚖️🤖

Autonomous AI agent and browser automation worker that continuously generates and publishes Indian legal awareness insights with rich WYSIWYG HTML, humanized scheduling, and multi-channel alerting.

---

### ✨ Features & Capabilities

- 🤖 **Universal AI Intelligence**: Out-of-the-box support for Google Gemini, OpenAI (GPT-4o), Anthropic Claude, DeepSeek, xAI Grok, Moonshot Kimi, Groq (Llama 3.3), and local models (Ollama, vLLM).
- ⚖️ **Curated Jurisprudence**: Built-in rotating knowledge domains (Constitutional Rights, Consumer Protection, Digital & Cyber Law, Criminal Law & Police Powers, Property & Tenancy, Employment & Labor, and Family Law).
- 🏷️ **Intelligent Tag Sanitizer**: Automatically cleans, formats, and deduplicates community hashtags, preventing run-on compound tag pills.
- ⏰ **Single-Run & Scheduled Daemon**: Supports single runs (`post-once`, `legal-post --once`) as well as 24/7 background scheduled loops with humanized jitter.
- 🔔 **Observability & Alerts**: Rich color-coded notifications for Discord embeds, Microsoft Teams Adaptive Cards (v1.4), Telegram Bot API, and generic webhooks with token masking.
- 🛡️ **Defensive Security**: Automatic session token isolation (`0600` permissions), quarantine of corrupted sessions, POSIX 130/143 signal handling, and zero credential leakage.
- 🧙‍♂️ **Interactive CLI Setup Wizard**: Run `legal-post --config` to interactively configure credentials with masked inputs and 0600 security.

---

### 📦 Installation

#### From PyPI:
```bash
pip install legal-facts-poster
```

#### From Docker (GHCR):
```bash
docker pull ghcr.io/kumar-swaraj/legal-facts-poster:latest
```

---

### 🚀 Quick Start

1. **Configure Credentials**:
   ```bash
   legal-post --config
   ```
2. **Publish a Single Post**:
   ```bash
   post-once
   ```
3. **Start the Autonomous Background Daemon**:
   ```bash
   legal-post
   ```
