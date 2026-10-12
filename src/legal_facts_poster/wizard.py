import contextlib
import getpass
import os

from .config import PROVIDER_DEFAULTS, reload_config

# ANSI Color Codes
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"

PROVIDERS = [
    ("gemini", "Google Gemini", "https://aistudio.google.com/"),
    ("openai", "OpenAI (GPT-4o-mini, GPT-4o)", "https://platform.openai.com/api-keys"),
    ("claude", "Anthropic Claude (Claude 3.5 Haiku / Sonnet)", "https://console.anthropic.com/"),
    ("deepseek", "DeepSeek (deepseek-chat)", "https://platform.deepseek.com/"),
    ("grok", "xAI Grok (grok-2-latest)", "https://console.x.ai/"),
    ("kimi", "Moonshot AI / Kimi (moonshot-v1-8k)", "https://platform.moonshot.cn/"),
    ("groq", "Groq (llama-3.3-70b - ultra fast)", "https://console.groq.com/keys"),
    ("openrouter", "OpenRouter (Claude, GPT, DeepSeek, etc.)", "https://openrouter.ai/keys"),
    ("custom", "Custom / Local (Ollama, vLLM, private proxy)", "Local / Private endpoint"),
]


def run_wizard() -> None:
    """
    Interactive terminal setup wizard for configuring Legal Facts Poster.
    Prompts for credentials, AI model provider, and saves securely.
    """
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║           Legal Facts Poster — Interactive Setup             ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════╝{RESET}\n")
    print(f"{DIM}Configure your credentials once. Settings are saved to:{RESET}")
    config_dir = os.path.expanduser("~/.config/legal-facts-poster")
    env_file = os.path.join(config_dir, ".env")
    print(f"{CYAN}→ {env_file}{RESET}\n")

    # Read existing values if any
    existing_username = os.getenv("MY_SITE_USERNAME", "")
    existing_base_url = os.getenv("BASE_URL", "")
    existing_provider = os.getenv("AI_PROVIDER", "gemini").lower()
    existing_ai_key = os.getenv("AI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

    # 1. Platform Username
    u_prompt = f"{BOLD}1. Platform Email / Username{RESET}"
    if existing_username:
        u_prompt += f" {DIM}[{existing_username}]{RESET}"
    u_prompt += ": "
    username = input(u_prompt).strip() or existing_username
    while not username:
        print(f"  {RED}✕ Username cannot be empty.{RESET}")
        username = input(u_prompt).strip()

    # 2. Platform Password
    p_prompt = f"{BOLD}2. Platform Password{RESET} {DIM}(hidden while typing){RESET}: "
    password = getpass.getpass(p_prompt).strip()
    if not password:
        password = os.getenv("MY_SITE_PASSWORD") or ""
    while not password:
        print(f"  {RED}✕ Password cannot be empty.{RESET}")
        password = getpass.getpass(p_prompt).strip()

    # 3. AI Provider Selection
    print(f"\n{BOLD}3. Choose your AI Provider:{RESET}")
    default_idx = 1
    for i, (p_id, p_name, p_url) in enumerate(PROVIDERS, 1):
        if p_id == existing_provider:
            default_idx = i
        marker = f"{GREEN}▶{RESET} " if p_id == existing_provider else "  "
        print(f"{marker}{CYAN}[{i}]{RESET} {BOLD}{p_name}{RESET} {DIM}({p_url}){RESET}")

    sel_prompt = f"\nSelect provider {DIM}[1-9, default: {default_idx}]{RESET}: "
    sel_input = input(sel_prompt).strip()
    try:
        chosen_idx = int(sel_input) if sel_input else default_idx
        if not (1 <= chosen_idx <= len(PROVIDERS)):
            chosen_idx = default_idx
    except ValueError:
        chosen_idx = default_idx

    chosen_provider, chosen_name, chosen_url = PROVIDERS[chosen_idx - 1]
    print(f"  {GREEN}✓ Selected: {BOLD}{chosen_name}{RESET}\n")

    # 4. AI API Key
    ai_key = ""
    ai_base_url = ""
    ai_model = ""

    if chosen_provider == "custom":
        url_prompt = f"{BOLD}Custom Base URL{RESET} {DIM}(e.g., http://localhost:11434/v1){RESET}: "
        ai_base_url = input(url_prompt).strip()
        while not ai_base_url:
            print(f"  {RED}✕ Base URL cannot be empty for custom provider.{RESET}")
            ai_base_url = input(url_prompt).strip()

        model_prompt = f"{BOLD}Model Name{RESET} {DIM}(e.g., llama3.2, mistral){RESET}: "
        ai_model = input(model_prompt).strip()
        while not ai_model:
            print(f"  {RED}✕ Model name cannot be empty for custom provider.{RESET}")
            ai_model = input(model_prompt).strip()

        key_prompt = f"{BOLD}API Key{RESET} {DIM}(press Enter if not required / local){RESET}: "
        ai_key = getpass.getpass(key_prompt).strip() or "none"
    else:
        key_label = f"{chosen_name} API Key"
        if existing_ai_key and chosen_provider == existing_provider:
            masked = existing_ai_key[:6] + "..." + existing_ai_key[-4:]
            k_prompt = f"{BOLD}{key_label}{RESET} {DIM}[{masked}]{RESET}: "
        else:
            k_prompt = f"{BOLD}{key_label}{RESET} {DIM}(from {chosen_url}){RESET}: "

        ai_key = getpass.getpass(k_prompt).strip()
        if not ai_key and chosen_provider == existing_provider and existing_ai_key:
            ai_key = existing_ai_key
        while not ai_key:
            print(f"  {RED}✕ API Key cannot be empty.{RESET}")
            ai_key = getpass.getpass(k_prompt).strip()

        # Optional model override
        def_models = PROVIDER_DEFAULTS.get(chosen_provider, {}).get("models", [])
        def_model = def_models[0] if def_models else "default"
        m_prompt = (
            f"{BOLD}Model Name Override{RESET} {DIM}[Enter for default: {def_model}]{RESET}: "
        )
        m_resp = input(m_prompt).strip()
        ai_model = m_resp if m_resp else ""

    # 5. Target Platform Base URL
    default_url = existing_base_url or "https://your-platform-domain.com"
    url_prompt = f"\n{BOLD}4. Platform Base URL{RESET} {DIM}[{default_url}]{RESET}: "
    base_url = input(url_prompt).strip() or default_url
    base_url = base_url.rstrip("/")

    # 6. Headless mode preference
    h_prompt = f"{BOLD}5. Run browser in background (headless)?{RESET} {DIM}[y/N]{RESET}: "
    headless_resp = input(h_prompt).strip().lower()
    headless_val = "true" if headless_resp in ("y", "yes") else "false"

    # Save to ~/.config/legal-facts-poster/.env
    os.makedirs(config_dir, exist_ok=True)
    with open(env_file, "w", encoding="utf-8") as f:
        f.write("# Legal Facts Poster — User Configuration\n")
        f.write(f'MY_SITE_USERNAME="{username}"\n')
        f.write(f'MY_SITE_PASSWORD="{password}"\n')
        f.write(f'AI_PROVIDER="{chosen_provider}"\n')
        f.write(f'AI_API_KEY="{ai_key}"\n')
        if ai_model:
            f.write(f'AI_MODEL="{ai_model}"\n')
        if ai_base_url:
            f.write(f'AI_BASE_URL="{ai_base_url}"\n')
        f.write(f'BASE_URL="{base_url}"\n')
        f.write(f"HEADLESS={headless_val}\n")
        f.write("POST_INTERVAL_HOURS=4.0\n")
        f.write("ENABLE_JITTER=true\n")
        f.write("JITTER_MAX_MINUTES=10\n")
        f.write("MAX_RETRIES=2\n")
        f.write("RETRY_DELAY_SECONDS=60\n")

    # Set secure permissions (read/write only by owner)
    with contextlib.suppress(Exception):
        os.chmod(env_file, 0o600)

    reload_config(env_file)

    print(f"\n{BOLD}{GREEN}✓ Configuration saved successfully!{RESET}")
    print(f"{DIM}Saved to: {env_file} (secured with 0600 permissions){RESET}\n")
    print(f"{BOLD}Configured AI Provider:{RESET} {CYAN}{chosen_name}{RESET}")
    print(f"{BOLD}You can now run:{RESET}")
    print(
        f"  {CYAN}post-once{RESET}       {DIM}# Publish a single legal insight immediately{RESET}"
    )
    print(f"  {CYAN}legal-post{RESET}      {DIM}# Start autonomous recurring posting loop{RESET}\n")


if __name__ == "__main__":
    run_wizard()
