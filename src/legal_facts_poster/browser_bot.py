import contextlib
import json
import os
import time

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    TimeoutError,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)

from .ai_generator import sanitize_tags
from .config import BASE_URL, BROWSER_CHANNEL, HEADLESS, PASSWORD, SESSION_FILE, USERNAME


def _validate_and_get_session(path: str) -> str | None:
    """
    Verifies that the session file exists, is non-empty, and contains valid JSON.
    If corrupted or invalid, automatically quarantines it to avoid crashing Playwright.
    """
    if not os.path.exists(path):
        return None
    try:
        if os.path.getsize(path) == 0:
            raise ValueError("Session file is empty (0 bytes)")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Session JSON root is not an object")
        return path
    except Exception as exc:
        print(
            f"  \033[33m⚡ Corrupted session detected in '{path}': {exc}. Quarantining and resetting...\033[0m"
        )
        with contextlib.suppress(OSError):
            backup = f"{path}.corrupted.{int(time.time())}"
            os.rename(path, backup)
            print(f"  \033[33mQuarantined corrupted session to '{backup}'.\033[0m")
        return None


def _save_session_state(context, path: str) -> None:
    """Saves session storage state and enforces owner-only permissions (0600) on Unix."""
    try:
        context.storage_state(path=path)
        with contextlib.suppress(OSError):
            os.chmod(path, 0o600)
        print(f"Session saved to '{path}' (permissions: 0600).")
    except Exception as e:
        print(f"Notice: Could not save session state: {e}")


def _detect_and_handle_cloudflare(page: Page, is_headless: bool, timeout_seconds: int = 60) -> bool:
    """
    Inspects page for Cloudflare Turnstile or security challenge interstitials.
    If in visible mode, informs the user and grants time to click the verification checkbox.
    If in headless mode, warns user and recommends running with visible browser once to save session.
    """
    title = (page.title() or "").lower()
    cf_titles = ["just a moment", "attention required", "security check", "cloudflare"]
    has_cf = any(t in title for t in cf_titles)
    if not has_cf:
        with contextlib.suppress(Exception):
            if (
                page.locator(
                    "iframe[src*='challenges.cloudflare.com'], #challenge-stage, #turnstile-wrapper, div.cf-turnstile"
                ).count()
                > 0
            ):
                has_cf = True

    if not has_cf:
        return True

    if not is_headless:
        print("\n  \033[33m⚡ Cloudflare verification / human challenge detected on page.\033[0m")
        print(
            "  \033[36m👉 Please click the verification checkbox in the opened browser window...\033[0m"
        )
        print(
            f"  \033[36m⏳ Waiting up to {timeout_seconds}s for verification to complete...\033[0m"
        )
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            page.wait_for_timeout(2000)
            cur_title = (page.title() or "").lower()
            if not any(t in cur_title for t in cf_titles):
                with contextlib.suppress(Exception):
                    if (
                        page.locator(
                            "iframe[src*='challenges.cloudflare.com'], #challenge-stage, #turnstile-wrapper, div.cf-turnstile"
                        ).count()
                        == 0
                    ):
                        print(
                            "  \033[32m✓ Cloudflare challenge cleared! Resuming navigation...\033[0m\n"
                        )
                        return True
        print("  \033[31m[Notice] Timed out waiting for Cloudflare challenge resolution.\033[0m\n")
        return False
    else:
        print(
            "\n  \033[33m⚡ Cloudflare human verification / Turnstile challenge detected in headless mode.\033[0m"
        )
        print(
            "  \033[36m👉 Actionable Tip: Run once with a visible browser window: 'post-once --no-headless'\033[0m"
        )
        print(
            "  \033[36m   Complete the login / checkbox once; session cookies will be saved to session.json and reused automatically.\033[0m\n"
        )
        return False


def _ensure_authenticated(page: Page, context, is_headless: bool = False) -> bool:
    """
    Checks if session is authenticated. If not, performs login and saves storage state.
    Returns False if login fails or credentials could not be authenticated.
    """
    community_url = f"{BASE_URL}/community"
    login_url = f"{BASE_URL}/login"

    # Check if existing session is already active
    valid_session = _validate_and_get_session(SESSION_FILE)
    if valid_session:
        print("Existing session found. Checking authentication status...")
        try:
            page.goto(community_url, wait_until="networkidle", timeout=20000)
        except TimeoutError:
            page.goto(community_url, wait_until="domcontentloaded")

        _detect_and_handle_cloudflare(page, is_headless)
        page.wait_for_timeout(2000)

        # If we are not redirected to /login, the session is active!
        if "/login" not in page.url:
            print("  \033[32m✓ Session restored successfully! Skipping login.\033[0m")
            return True
        print("  \033[33m⚡ Session expired or redirected to login. Re-authenticating...\033[0m")

    # Perform login
    print(f"Navigating to login page: {login_url}...")
    try:
        page.goto(login_url, wait_until="networkidle", timeout=20000)
    except TimeoutError:
        page.goto(login_url, wait_until="domcontentloaded")

    _detect_and_handle_cloudflare(page, is_headless)

    print("Submitting login credentials...")
    try:
        page.wait_for_selector("input#identifier, input[name='identifier']", timeout=15000)
        page.fill("input#identifier, input[name='identifier']", USERNAME)
        page.fill("input#password, input[name='password']", PASSWORD)
        page.click("button[type='submit']:has-text('Log In')", timeout=5000)
    except TimeoutError:
        print("Could not autofill login. Checking for login form...")

    print("Waiting for login to complete...")
    try:
        page.wait_for_url(lambda u: "/login" not in u, timeout=45000)
        page.wait_for_timeout(2000)
    except TimeoutError:
        print("  \033[31m[Error] Login verification timed out. Still on login endpoint.\033[0m")
        err_messages = page.locator(
            "[role='alert'], div[class*='error'], p[class*='error']"
        ).all_inner_texts()
        if err_messages:
            print(f"  \033[31mLogin errors on page: {err_messages}\033[0m")
        return False

    if "/login" in page.url:
        print("  \033[31m[Error] Authentication incomplete: page remains on login endpoint.\033[0m")
        return False

    # Save session storage state only upon confirmed authentication
    _save_session_state(context, SESSION_FILE)

    # Navigate to community if not already there
    if "/community" not in page.url:
        print(f"Navigating to {community_url}...")
        try:
            page.goto(community_url, wait_until="networkidle", timeout=15000)
        except TimeoutError:
            page.goto(community_url, wait_until="domcontentloaded")
    return True


def _select_tags(page: Page, target_tags: list[str], min_tags: int = 2) -> tuple[int, list[str]]:
    """
    Selects at least `min_tags` from the platform's combobox listbox.
    Ensures input field is always completely cleared before typing each candidate
    and prevents concatenated multi-tag selection.
    Returns a tuple of (selected_count, applied_tags_list).
    """
    tag_combobox = page.locator("input[role='combobox']").first
    tag_combobox.scroll_into_view_if_needed()

    # Pre-clean candidates so no concatenated hashtags or compound strings are ever passed
    clean_targets = sanitize_tags(target_tags)
    fallback_pool = [
        "Law",
        "Legal",
        "Justice",
        "RuleOfLaw",
        "LegalAwareness",
        "Constitution",
        "SupremeCourt",
    ]
    candidates = clean_targets + [
        f for f in fallback_pool if f.lower() not in [t.lower() for t in clean_targets]
    ]

    selected_count = 0
    selected_tags: list[str] = []
    tried = set()

    for candidate in candidates:
        clean_cand = candidate.strip().lstrip("#")
        if not clean_cand or clean_cand.lower() in tried:
            continue
        tried.add(clean_cand.lower())

        if selected_count >= min_tags:
            break

        # Click and explicitly clear the combobox input so text never accumulates across attempts
        tag_combobox.click()
        tag_combobox.fill("")
        page.wait_for_timeout(200)

        tag_combobox.press_sequentially(clean_cand, delay=30)
        page.wait_for_timeout(700)

        options = page.locator("ul[role='listbox'] button[role='option']").all()
        selected_opt = None
        if options:
            matching_opt = None
            for opt in options:
                opt_name = opt.inner_text().strip().lstrip("#")
                if opt_name.lower() == clean_cand.lower():
                    matching_opt = opt
                    break

            if matching_opt:
                selected_opt = matching_opt
            else:
                # Only use fallback options[0] if it is a clean, single-word tag
                first_text = options[0].inner_text().strip().lstrip("#")
                if first_text and "#" not in first_text and len(first_text) <= 25:
                    selected_opt = options[0]

        if selected_opt:
            opt_text = selected_opt.inner_text().strip().lstrip("#")
            print(
                f"    \033[35m🏷 Selected tag ({selected_count + 1}/{min_tags}):\033[0m \033[1m'#{opt_text}'\033[0m"
            )
            selected_opt.click()
            page.wait_for_timeout(600)
            selected_count += 1
            if opt_text not in selected_tags:
                selected_tags.append(opt_text)
            # Immediately clear the input field so subsequent tags start from a clean slate
            with contextlib.suppress(Exception):
                tag_combobox.fill("")
                page.wait_for_timeout(150)
        else:
            # Revert/clear typed characters if no tag matched
            with contextlib.suppress(Exception):
                tag_combobox.fill("")
                page.wait_for_timeout(150)

    # Blur tag combobox by clicking the editor
    page.locator("div.jodit-wysiwyg, div[contenteditable='true']").first.click()
    page.wait_for_timeout(500)
    return selected_count, selected_tags


DEFAULT_STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-infobars",
    "--disable-dev-shm-usage",
]


def detect_system_browser() -> str | None:
    """Checks if an existing system browser (Google Chrome or Microsoft Edge) is installed.

    Returns 'chrome', 'msedge', or None.
    """
    import shutil
    import sys

    if sys.platform == "darwin":
        mac_apps = [
            ("/Applications/Google Chrome.app", "chrome"),
            (os.path.expanduser("~/Applications/Google Chrome.app"), "chrome"),
            ("/Applications/Microsoft Edge.app", "msedge"),
            (os.path.expanduser("~/Applications/Microsoft Edge.app"), "msedge"),
        ]
        for path, channel in mac_apps:
            if os.path.isdir(path):
                return channel
    elif sys.platform == "win32":
        win_paths = [
            (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "chrome"),
            (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "chrome"),
            (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "msedge"),
            (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "msedge"),
        ]
        for path, channel in win_paths:
            if os.path.exists(path):
                return channel
    elif sys.platform.startswith("linux"):
        for binary, channel in [
            ("google-chrome", "chrome"),
            ("google-chrome-stable", "chrome"),
            ("microsoft-edge", "msedge"),
            ("chromium-browser", "chromium"),
            ("chromium", "chromium"),
        ]:
            if shutil.which(binary):
                return channel
    return None


def install_browser(retries: int = 3, timeout_seconds: int = 600) -> bool:
    """
    Downloads Playwright Chromium with automatic retry resilience.
    Protects against slow downloads, packet loss, or mid-stream terminations.
    """
    import subprocess
    import sys
    import time

    print("\n\033[36m⬇ Preparing Playwright Chromium installation...\033[0m")
    for attempt in range(1, retries + 1):
        print(
            f"  \033[36m[Attempt {attempt}/{retries}] Downloading Playwright Chromium binary...\033[0m"
        )
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
                timeout=timeout_seconds,
            )
            print("  \033[32m✓ Playwright Chromium installed and verified successfully!\033[0m\n")
            return True
        except subprocess.TimeoutExpired:
            print(
                f"  \033[33m⚡ Download attempt {attempt} timed out after {timeout_seconds}s.\033[0m"
            )
        except subprocess.CalledProcessError as err:
            print(f"  \033[33m⚡ Download attempt {attempt} interrupted: {err}\033[0m")
        except Exception as exc:
            print(f"  \033[33m⚡ Download attempt {attempt} failed: {exc}\033[0m")

        if attempt < retries:
            print(
                "  \033[36m🔄 Waiting 3 seconds before reconnecting and retrying download...\033[0m"
            )
            time.sleep(3)

    print(
        "\n\033[31m[Error] Playwright Chromium installation failed after multiple retries.\033[0m\n"
        "\033[33m💡 Quick Alternatives:\033[0m\n"
        "  1. If you already have Google Chrome installed, set BROWSER_CHANNEL=chrome in your .env to skip the download entirely!\n"
        "  2. Or run manually in your terminal with a stable connection: 'playwright install chromium'\n"
    )
    return False


def is_browser_installed() -> bool:
    """Returns True if Playwright can launch either bundled Chromium or an installed system browser."""
    try:
        with sync_playwright() as p:
            channel = BROWSER_CHANNEL or None
            try:
                b = p.chromium.launch(headless=True, channel=channel, args=DEFAULT_STEALTH_ARGS)
                b.close()
                return True
            except PlaywrightError:
                if not channel:
                    sys_b = detect_system_browser()
                    if sys_b:
                        b = p.chromium.launch(
                            headless=True, channel=sys_b, args=DEFAULT_STEALTH_ARGS
                        )
                        b.close()
                        return True
                return False
    except Exception:
        return False


def _launch_browser(p: Playwright, is_headless: bool) -> Browser | None:
    """
    Attempts to launch Playwright Chromium or an installed system browser (e.g. Chrome/Edge).
    If missing, automatically detects existing system Chrome to avoid 200MB download, or
    falls back to the resilient auto-installer with retries.
    """
    channel = BROWSER_CHANNEL or None

    # 1. If explicit channel is configured, launch it directly
    if channel:
        try:
            return p.chromium.launch(
                headless=is_headless, channel=channel, args=DEFAULT_STEALTH_ARGS
            )
        except PlaywrightError as exc:
            print(
                f"  \033[33mNotice: Could not launch configured BROWSER_CHANNEL='{channel}': {exc}\033[0m"
            )

    # 2. Try launching bundled Chromium
    try:
        return p.chromium.launch(headless=is_headless, args=DEFAULT_STEALTH_ARGS)
    except PlaywrightError as exc:
        err_msg = str(exc)
        if "Executable doesn't exist" in err_msg or "playwright install" in err_msg:
            # Check if user already has Google Chrome or Edge installed
            sys_browser = detect_system_browser()
            if sys_browser:
                print(
                    f"  \033[33m⚡ Bundled Chromium binary not found, but detected system {sys_browser.title()}!\033[0m"
                )
                print(
                    f"  \033[36m🚀 Launching using system {sys_browser.title()} (channel='{sys_browser}') — skipping 200MB download!\033[0m"
                )
                try:
                    return p.chromium.launch(
                        headless=is_headless, channel=sys_browser, args=DEFAULT_STEALTH_ARGS
                    )
                except Exception as sys_err:
                    print(
                        f"  \033[33mNotice: System browser launch failed: {sys_err}. Proceeding with download...\033[0m"
                    )

            # Respect environment opt-outs for air-gapped or restricted security policies
            skip_download = os.getenv("PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD", "").lower() in (
                "1",
                "true",
            )
            auto_install = os.getenv("AUTO_INSTALL_PLAYWRIGHT", "true").lower() in (
                "1",
                "true",
                "yes",
            )

            if skip_download or not auto_install:
                print(
                    "\n\033[31m[Security Policy] Automatic browser binary download is disabled.\033[0m\n"
                    "\033[33mPlaywright Chromium binary must be pre-installed.\033[0m\n"
                    "\033[33mPlease run 'playwright install chromium' before running.\033[0m\n"
                )
                return None

            print(
                "\n\033[33m⚡ Chromium browser binary not found.\033[0m\n"
                "\033[36m⬇ Automatically downloading Chromium via Playwright (one-time setup)...\033[0m"
            )
            installed = install_browser(retries=3, timeout_seconds=600)
            if installed:
                return p.chromium.launch(headless=is_headless, args=DEFAULT_STEALTH_ARGS)
            return None
        raise


class PostResult:
    """Result object supporting boolean checks, tuple unpacking, and attribute access."""

    def __init__(self, success: bool, applied_tags: list[str] | None = None) -> None:
        self.success = success
        self.applied_tags = applied_tags or []

    def __bool__(self) -> bool:
        return self.success

    def __iter__(self):
        return iter((self.success, self.applied_tags))

    def __repr__(self) -> str:
        return f"PostResult(success={self.success}, applied_tags={self.applied_tags})"


def login_and_post(
    post_content: str, tags: list[str] | None = None, headless: bool | None = None
) -> PostResult:
    """
    Automates publishing a rich legal post to the community feed.
    Returns a PostResult containing success status and actually applied tags.
    """
    is_headless = HEADLESS if headless is None else headless
    print(f"  \033[34m🌐 Launching browser agent (headless={is_headless})...\033[0m")

    try:
        with sync_playwright() as p:
            browser = _launch_browser(p, is_headless)
            if browser is None:
                return PostResult(False)

            # Load stored session if valid
            storage_path = _validate_and_get_session(SESSION_FILE)
            context = browser.new_context(
                storage_state=storage_path,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            # 1. Authenticate and go to community
            if not _ensure_authenticated(page, context, is_headless):
                print(
                    "  \033[31m[Error] Authentication failed or credentials rejected. Aborting post attempt.\033[0m"
                )
                browser.close()
                return PostResult(False)

            # 2. Open the "Create Post" modal with fallback locators
            trigger = page.get_by_role(
                "button", name="Share your legal insights with the community."
            )
            if trigger.count() > 0 and trigger.first.is_visible():
                trigger.first.click()
            else:
                modal_selectors = [
                    "button:has-text('Share your legal insights')",
                    "div:has-text('Share your legal insights')",
                    "button:has-text('Create Post')",
                    "button:has-text('New Post')",
                    "button:has-text('Share insight')",
                ]
                clicked = False
                for sel in modal_selectors:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        loc.click()
                        clicked = True
                        break
                if not clicked:
                    with contextlib.suppress(TimeoutError):
                        page.locator(
                            "button:has-text('Share your legal insights'), button:has-text('Create Post')"
                        ).first.click(timeout=8000)

            page.wait_for_timeout(1000)

            # 3. Insert rich HTML into Jodit WYSIWYG
            print("  \033[36m✍ Injecting rich HTML into WYSIWYG editor...\033[0m")
            editor = page.locator("div.jodit-wysiwyg, div[contenteditable='true']").first
            editor.click()
            page.wait_for_timeout(300)

            page.evaluate(
                """(html) => {
                const ed = document.querySelector('div.jodit-wysiwyg') || document.querySelector("div[contenteditable='true']");
                if (ed) {
                    ed.focus();
                    document.execCommand('insertHTML', false, html);
                }
            }""",
                post_content,
            )

            page.wait_for_timeout(1000)

            # 4. Add at least two valid tags
            applied_tags: list[str] = []
            if tags:
                print(f"  \033[36m🏷 Selecting tags from combobox (target: {tags})...\033[0m")
                count, applied_tags = _select_tags(page, tags, min_tags=2)
                print(f"  \033[32m✓ Tag selection complete ({count} tags active).\033[0m")

            page.wait_for_timeout(1000)

            # 5. Click Publish and verify
            print("  \033[36m🚀 Submitting post...\033[0m")
            publish_button = page.get_by_role("button", name="Publish", exact=True)
            publish_button.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

            if not publish_button.is_enabled():
                editor.click()
                page.wait_for_timeout(1000)

            publish_button.click()

            try:
                page.locator("text='Create Post'").wait_for(state="hidden", timeout=15000)
                print("  \033[32m✓ Create Post modal confirmed! Post is now live.\033[0m")
                # Save fresh session state after successful post
                _save_session_state(context, SESSION_FILE)
                page.wait_for_timeout(3000)
                browser.close()
                return PostResult(True, applied_tags)
            except TimeoutError:
                print("Modal did not close after clicking Publish! Checking for error...")
                errors = page.locator("[role='alert'], div[class*='error']").all_inner_texts()
                if errors:
                    print(f"Errors on page: {errors}")
                browser.close()
                return PostResult(False, applied_tags)

    except Exception as e:
        print(f"Browser automation error: {e}")
        return PostResult(False)
