import contextlib
import os

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

from .config import BASE_URL, HEADLESS, PASSWORD, SESSION_FILE, USERNAME


def _save_session_state(context, path: str) -> None:
    """Saves session storage state and enforces owner-only permissions (0600) on Unix."""
    try:
        context.storage_state(path=path)
        with contextlib.suppress(OSError):
            os.chmod(path, 0o600)
        print(f"Session saved to '{path}' (permissions: 0600).")
    except Exception as e:
        print(f"Notice: Could not save session state: {e}")


def _ensure_authenticated(page: Page, context) -> bool:
    """
    Checks if session is authenticated. If not, performs login and saves storage state.
    """
    community_url = f"{BASE_URL}/community"
    login_url = f"{BASE_URL}/login"

    # Check if existing session is already active
    if os.path.exists(SESSION_FILE):
        print("Existing session found. Checking authentication status...")
        try:
            page.goto(community_url, wait_until="networkidle", timeout=20000)
        except TimeoutError:
            page.goto(community_url, wait_until="domcontentloaded")

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

    print("Submitting login credentials...")
    try:
        page.wait_for_selector("input#identifier, input[name='identifier']", timeout=15000)
        page.fill("input#identifier, input[name='identifier']", USERNAME)
        page.fill("input#password, input[name='password']", PASSWORD)
        page.click("button[type='submit']:has-text('Log In')", timeout=5000)
    except TimeoutError:
        print("Could not autofill login. Waiting for manual login...")

    print("Waiting for login to complete...")
    try:
        page.wait_for_url(lambda u: "/login" not in u, timeout=60000)
        page.wait_for_timeout(2000)
    except TimeoutError:
        print("Notice: URL wait timed out, continuing...")

    # Save session storage state for subsequent runs
    _save_session_state(context, SESSION_FILE)

    # Navigate to community if not already there
    if "/community" not in page.url:
        print(f"Navigating to {community_url}...")
        page.goto(community_url, wait_until="networkidle")
    return True


def _select_tags(page: Page, target_tags: list[str], min_tags: int = 2) -> tuple[int, list[str]]:
    """
    Selects at least `min_tags` from the platform's combobox listbox.
    Consecutively appends comma-separated tags without clearing earlier ones.
    Returns a tuple of (selected_count, applied_tags_list).
    """
    tag_combobox = page.locator("input[role='combobox']").first
    tag_combobox.scroll_into_view_if_needed()
    tag_combobox.click()
    page.wait_for_timeout(300)

    candidates = list(target_tags) + [
        "Law",
        "Legal",
        "Justice",
        "RuleOfLaw",
        "LegalAwareness",
        "Constitution",
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

        val_before = tag_combobox.input_value()
        tag_combobox.press_sequentially(clean_cand, delay=30)
        page.wait_for_timeout(700)

        options = page.locator("ul[role='listbox'] button[role='option']").all()
        if options:
            matching_opt = None
            for opt in options:
                if opt.inner_text().strip().lower() == clean_cand.lower():
                    matching_opt = opt
                    break
            selected_opt = matching_opt if matching_opt else options[0]
            opt_text = selected_opt.inner_text().strip()
            print(
                f"    \033[35m🏷 Selected tag ({selected_count + 1}/{min_tags}):\033[0m \033[1m'{opt_text}'\033[0m"
            )
            selected_opt.click()
            page.wait_for_timeout(600)
            selected_count += 1
            if opt_text not in selected_tags:
                selected_tags.append(opt_text)
        else:
            # Revert typed characters if no tag matched
            tag_combobox.fill(val_before)
            page.wait_for_timeout(200)

    # Blur tag combobox by clicking the editor
    page.locator("div.jodit-wysiwyg, div[contenteditable='true']").first.click()
    page.wait_for_timeout(500)
    return selected_count, selected_tags


def _launch_browser(p: Playwright, is_headless: bool) -> Browser | None:
    """
    Attempts to launch Playwright Chromium.
    If the browser binary is missing, automatically downloads it via
    'playwright install chromium' as a self-healing bootstrap, while honoring
    security opt-outs and timeout bounds.
    """
    try:
        return p.chromium.launch(headless=is_headless)
    except PlaywrightError as exc:
        err_msg = str(exc)
        if "Executable doesn't exist" in err_msg or "playwright install" in err_msg:
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
            try:
                import subprocess
                import sys

                # Invokes strictly within current interpreter; no shell=True; 5-minute timeout bound
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                    timeout=300,
                )
                print(
                    "  \033[32m✓ Chromium installed successfully! Resuming browser launch...\033[0m\n"
                )
                return p.chromium.launch(headless=is_headless)
            except subprocess.TimeoutExpired:
                print(
                    "\n\033[31m[Error] Timed out waiting for Playwright Chromium download (5 min limit).\033[0m\n"
                    "\033[33mPlease run 'playwright install chromium' manually.\033[0m\n"
                )
                return None
            except Exception as install_err:
                print(
                    f"\n\033[31m[Error] Automatic Chromium installation failed: {install_err}\033[0m\n"
                    "\033[33mPlease manually run: 'playwright install chromium'\033[0m\n"
                )
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

            # Load stored session if available
            storage_path = SESSION_FILE if os.path.exists(SESSION_FILE) else None
            context = browser.new_context(storage_state=storage_path)
            page = context.new_page()

            # 1. Authenticate and go to community
            _ensure_authenticated(page, context)

            # 2. Open the "Create Post" modal
            trigger = page.get_by_role(
                "button", name="Share your legal insights with the community."
            )
            if trigger.count() > 0:
                trigger.first.click()
            else:
                with contextlib.suppress(TimeoutError):
                    page.locator(
                        "button:has-text('Share your legal insights'), div:has-text('Share your legal insights')"
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
