import contextlib
import io
import os
import sys

from .browser_bot import detect_system_browser, install_browser, is_browser_installed
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


def mask_secret(val: str, show_first: int = 4, show_last: int = 4) -> str:
    """Masks secret with asterisks, preserving prefix and suffix for identification if long enough."""
    if not val:
        return "(empty)"
    if show_first == 0 and show_last == 0:
        return "*" * min(len(val), 16)
    if len(val) <= (show_first + show_last):
        return "*" * len(val)
    return f"{val[:show_first]}{'*' * 8}{val[-show_last:]}"


def get_masked_input(prompt: str = "") -> str:
    """
    Reads sensitive input (e.g. password, API key) from the terminal while
    echoing '*' for each character entered (similar to Ubuntu's pwfeedback).

    Handles character typing, clipboard pasting (multi-character chunks),
    Backspace/Delete (erasing asterisks with \\b \\b), Enter (\\r or \\n),
    Ctrl+C (KeyboardInterrupt), and Ctrl+D (EOF).
    Falls back gracefully to standard readline/getpass if stdin is not a TTY.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    # Non-interactive / piped / non-TTY fallback
    if not sys.stdin.isatty():
        try:
            return sys.stdin.readline().rstrip("\r\n")
        except Exception:
            import getpass

            return getpass.getpass("")

    # Windows implementation via msvcrt
    if sys.platform == "win32":
        try:
            import msvcrt

            chars_win: list[str] = []
            while True:
                ch = msvcrt.getch()
                if ch in (b"\r", b"\n"):
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    return "".join(chars_win)
                elif ch == b"\x03":  # Ctrl+C
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                elif ch in (b"\x08", b"\x7f"):  # Backspace
                    if chars_win:
                        chars_win.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                else:
                    try:
                        char = ch.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    if char >= " " or char == "\t":
                        chars_win.append(char)
                        sys.stdout.write("*")
                        sys.stdout.flush()
        except ImportError:
            import getpass

            return getpass.getpass("").strip()

    # Unix (macOS, Linux) implementation via termios / tty
    try:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
    except (io.UnsupportedOperation, ValueError, Exception):
        import getpass

        return getpass.getpass("").strip()

    chars: list[str] = []
    try:
        tty.setraw(fd)
        while True:
            chunk = os.read(fd, 1024).decode("utf-8", errors="replace")
            if not chunk:
                break
            for c in chunk:
                if c in ("\r", "\n"):
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    return "".join(chars)
                elif c == "\x03":  # Ctrl+C
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                elif c == "\x04":  # Ctrl+D (EOF)
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    return "".join(chars)
                elif c in ("\x08", "\x7f"):  # Backspace / Delete
                    if chars:
                        chars.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                elif c >= " " or c == "\t":
                    chars.append(c)
                    sys.stdout.write("*")
                    sys.stdout.flush()
        sys.stdout.write("\r\n")
        sys.stdout.flush()
        return "".join(chars)
    finally:
        with contextlib.suppress(Exception):
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _run_wizard_interactive() -> None:
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
    existing_channel = os.getenv("BROWSER_CHANNEL", "").strip().lower()

    # 1. Platform Username
    u_prompt = f"{BOLD}1. Platform Email / Username{RESET}"
    if existing_username:
        u_prompt += f" {DIM}[{existing_username}]{RESET}"
    u_prompt += ": "
    username = input(u_prompt).strip() or existing_username
    while not username:
        print(f"  {RED}✕ Username cannot be empty.{RESET}")
        username = input(u_prompt).strip()

    # 2. Platform Password (masked with * pwfeedback)
    p_prompt = f"{BOLD}2. Platform Password{RESET} {DIM}(masked with *){RESET}: "
    password = get_masked_input(p_prompt).strip()
    if not password:
        password = os.getenv("MY_SITE_PASSWORD") or ""
    while not password:
        print(f"  {RED}✕ Password cannot be empty.{RESET}")
        password = get_masked_input(p_prompt).strip()

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

    # 4. AI API Key (masked with * pwfeedback)
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

        key_prompt = f"{BOLD}API Key{RESET} {DIM}(press Enter if not required / local, masked with *){RESET}: "
        ai_key = get_masked_input(key_prompt).strip() or "none"
    else:
        key_label = f"{chosen_name} API Key"
        if existing_ai_key and chosen_provider == existing_provider:
            masked = mask_secret(existing_ai_key, show_first=6, show_last=4)
            k_prompt = f"{BOLD}{key_label}{RESET} {DIM}[{masked}, masked with *]{RESET}: "
        else:
            k_prompt = f"{BOLD}{key_label}{RESET} {DIM}(from {chosen_url}, masked with *){RESET}: "

        ai_key = get_masked_input(k_prompt).strip()
        if not ai_key and chosen_provider == existing_provider and existing_ai_key:
            ai_key = existing_ai_key
        while not ai_key:
            print(f"  {RED}✕ API Key cannot be empty.{RESET}")
            ai_key = get_masked_input(k_prompt).strip()

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

    # 6. Headless mode preference with clear explanations
    print(f"\n{BOLD}5. Browser Mode (Headless vs Visible Window):{RESET}")
    print(
        f"   {CYAN}• Headless (true){RESET}  : Runs silently in the background with no window popups."
    )
    print(
        "                       Best for servers, VPS, Docker, cron jobs, and 24/7 background posting."
    )
    print(
        f"   {CYAN}• Visible  (false){RESET} : Opens a live browser window so you can watch login & typing in real-time."
    )
    print(
        f"                       {YELLOW}Recommended for first run, testing, or if Cloudflare checks appear!{RESET}"
    )
    h_prompt = f"Run in background (headless)? {DIM}[y/N, default: N]{RESET}: "
    headless_resp = input(h_prompt).strip().lower()
    headless_val = "true" if headless_resp in ("y", "yes") else "false"

    # 7. Browser Engine & Installation Verification
    print(f"\n{BOLD}6. Browser Engine & Setup Verification:{RESET}")
    sys_browser = detect_system_browser()
    channel_to_save = existing_channel

    if sys_browser:
        print(f"  {GREEN}✓ Detected installed system {sys_browser.title()} on your machine!{RESET}")
        print(
            f"  {DIM}Playwright can use this directly to skip downloading the ~200MB Chromium bundle.{RESET}"
        )
        use_sys = (
            input(
                f"Use system {sys_browser.title()} (skips 200MB download)? {DIM}[Y/n, default: Y]{RESET}: "
            )
            .strip()
            .lower()
        )
        if use_sys not in ("n", "no"):
            channel_to_save = sys_browser
            print(f"  {GREEN}✓ Configured BROWSER_CHANNEL='{sys_browser}'.{RESET}")
        else:
            channel_to_save = ""
    else:
        # Check if Playwright bundled browser is installed
        if not is_browser_installed():
            print(f"  {YELLOW}⚡ Playwright Chromium is not yet installed on this system.{RESET}")
            do_install = (
                input(
                    f"Would you like to download and install Chromium now? {DIM}[Y/n, default: Y]{RESET}: "
                )
                .strip()
                .lower()
            )
            if do_install not in ("n", "no"):
                install_browser(retries=3)
        else:
            print(f"  {GREEN}✓ Playwright Chromium browser binary is verified and ready.{RESET}")

    # 8. Optional Alerting Webhook URL (Discord / MS Teams / Slack / Generic)
    existing_webhook = os.getenv("TEAMS_WEBHOOK_URL", "") or os.getenv("WEBHOOK_URL", "")
    w_prompt = (
        f"\n{BOLD}7. Alert Webhook URL (Discord / MS Teams / Slack){RESET} "
        f"{DIM}(optional, press Enter to skip){RESET}: "
    )
    webhook_val = input(w_prompt).strip() or existing_webhook

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
        if channel_to_save:
            f.write(f'BROWSER_CHANNEL="{channel_to_save}"\n')
        f.write("POST_INTERVAL_HOURS=4.0\n")
        f.write("ENABLE_JITTER=true\n")
        f.write("JITTER_MAX_MINUTES=10\n")
        f.write("MAX_RETRIES=2\n")
        f.write("RETRY_DELAY_SECONDS=60\n")
        if webhook_val:
            if any(
                h in webhook_val
                for h in ("logic.azure.com", "webhook.office.com", "office.com/webhook")
            ):
                f.write(f'TEAMS_WEBHOOK_URL="{webhook_val}"\n')
            else:
                f.write(f'WEBHOOK_URL="{webhook_val}"\n')
            f.write('NOTIFY_ON="all"\n')

    # Set secure permissions (read/write only by owner)
    with contextlib.suppress(Exception):
        os.chmod(env_file, 0o600)

    reload_config(env_file)

    # Clean, comprehensive summary report
    print(f"\n{BOLD}{GREEN}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{GREEN}║             Configuration Saved & Verified!                  ║{RESET}")
    print(f"{BOLD}{GREEN}╚══════════════════════════════════════════════════════════════╝{RESET}\n")

    masked_pwd = mask_secret(password, show_first=0, show_last=0)
    masked_key = mask_secret(ai_key, show_first=6, show_last=4)
    masked_hook = (
        f"{webhook_val[:28]}...****"
        if len(webhook_val) > 30
        else (webhook_val if webhook_val else "None (Disabled)")
    )
    mode_label = (
        f"{CYAN}Background / Headless (HEADLESS=true){RESET}"
        if headless_val == "true"
        else f"{GREEN}Visible Window (HEADLESS=false){RESET}"
    )
    engine_label = (
        f"System {channel_to_save.title()} (BROWSER_CHANNEL={channel_to_save})"
        if channel_to_save
        else "Playwright Chromium"
    )

    print(f"{BOLD}Configuration Summary:{RESET}")
    print(
        f"  • {BOLD}Config File Location:{RESET} {CYAN}{env_file}{RESET} {DIM}(mode: 0600){RESET}"
    )
    print(f"  • {BOLD}Platform URL        :{RESET} {base_url}")
    print(f"  • {BOLD}Username / Email    :{RESET} {username}")
    print(f"  • {BOLD}Password            :{RESET} {DIM}{masked_pwd}{RESET}")
    print(
        f"  • {BOLD}AI Provider         :{RESET} {chosen_name} {DIM}({ai_model or 'default'}){RESET}"
    )
    print(f"  • {BOLD}AI API Key          :{RESET} {DIM}{masked_key}{RESET}")
    print(f"  • {BOLD}Browser Mode        :{RESET} {mode_label}")
    print(f"  • {BOLD}Browser Engine      :{RESET} {engine_label}")
    print(f"  • {BOLD}Alerting Webhook    :{RESET} {DIM}{masked_hook}{RESET}\n")

    print(f"{BOLD}{YELLOW}💡 Understanding Browser Modes & Cloudflare Verification:{RESET}")
    print(
        f"  {CYAN}HEADLESS=true{RESET}  : Runs invisibly in the background. Use for unattended servers or cron jobs."
    )
    print(
        f"  {CYAN}HEADLESS=false{RESET} : Opens a visible Chromium window. Use this for testing, initial login, or"
    )
    print(
        "                   if the community platform presents a Cloudflare human verification checkbox!"
    )
    print(
        f"                   {DIM}Once logged in visibly, cookies are saved to session.json and reused automatically.{RESET}\n"
    )

    print(f"{BOLD}🚀 Next Steps — Quick Commands:{RESET}")
    print(
        f"  {CYAN}post-once --no-headless{RESET}   {DIM}# Test publishing with a visible browser window{RESET}"
    )
    print(
        f"  {CYAN}post-once{RESET}                 {DIM}# Publish a single post using saved settings{RESET}"
    )
    print(
        f"  {CYAN}legal-post{RESET}                {DIM}# Start the continuous 24/7 autonomous loop{RESET}\n"
    )


def run_wizard() -> None:
    """Interactive terminal setup wizard for configuring Legal Facts Poster."""
    try:
        _run_wizard_interactive()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup wizard cancelled by user (Ctrl+C). Exiting.{RESET}")
        sys.exit(130)


if __name__ == "__main__":
    run_wizard()
