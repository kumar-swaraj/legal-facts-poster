import sys
import time
import random
import schedule
from .config import (
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    POST_INTERVAL_HOURS,
    ENABLE_JITTER,
    JITTER_MAX_MINUTES,
    validate_config,
)
from .ai_generator import generate_new_fact
from .browser_bot import login_and_post
from .history import save_to_history

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

def run_single_post(fail_fast: bool = False, headless: bool | None = None) -> bool:
    """
    Executes a single end-to-end posting cycle with automatic retry on temporary failures.
    """
    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}[{time.strftime('%Y-%m-%d %H:%M:%S')}]{RESET} {CYAN}Starting Legal Fact Posting Task{RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════{RESET}")

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            print(f"\n{BOLD}[Attempt {attempt}/{MAX_RETRIES + 1}]{RESET} Generating AI legal fact...")
            topic, post_html, tags = generate_new_fact()
            print(f"{BOLD}Topic:{RESET} '{topic}' | {BOLD}Tags:{RESET} {tags}")

            success = login_and_post(post_html, tags, headless=headless)
            if success:
                save_to_history(topic)
                print(f"\n{BOLD}{GREEN}✓ Successfully posted and logged '{topic}' to history!{RESET}")
                return True
            else:
                raise RuntimeError("Browser automation could not confirm publication.")

        except Exception as e:
            print(f"{RED}✕ Post attempt {attempt} failed: {e}{RESET}")
            if attempt <= MAX_RETRIES:
                print(f"{YELLOW}Retrying in {RETRY_DELAY_SECONDS} seconds...{RESET}")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"{RED}All retry attempts exhausted for this cycle.{RESET}")
                if fail_fast:
                    sys.exit(1)
                return False
    return False

def run_schedule_loop(
    interval_hours: float | None = None,
    max_posts: int | None = None,
    headless: bool | None = None,
    run_immediately: bool = True
) -> None:
    """
    Runs the posting scheduler loop with optional post limits, intervals, and humanized jitter.
    """
    validate_config()
    interval = interval_hours if interval_hours is not None else POST_INTERVAL_HOURS
    posts_completed = 0

    print(f"\n{BOLD}{GREEN}✓ Legal Facts Poster Initialized.{RESET}")
    print(f"{CYAN}Interval:{RESET} every {interval} hour(s) | {CYAN}Max posts:{RESET} {max_posts or 'Infinite'} | {CYAN}Headless:{RESET} {headless}")

    if run_immediately:
        print(f"\n{DIM}Executing immediate initial post...{RESET}")
        if run_single_post(fail_fast=True, headless=headless):
            posts_completed += 1

        if max_posts is not None and posts_completed >= max_posts:
            print(f"\n{BOLD}{GREEN}✓ Reached requested post count ({max_posts}). Exiting cleanly.{RESET}")
            return

    def scheduled_job():
        nonlocal posts_completed
        
        # Apply humanized jitter if enabled
        if ENABLE_JITTER and JITTER_MAX_MINUTES > 0:
            jitter_seconds = random.randint(0, JITTER_MAX_MINUTES * 60)
            print(f"{YELLOW}Applying jitter delay: waiting {jitter_seconds // 60}m {jitter_seconds % 60}s before posting...{RESET}")
            time.sleep(jitter_seconds)

        if run_single_post(fail_fast=False, headless=headless):
            posts_completed += 1
            if max_posts is not None and posts_completed >= max_posts:
                print(f"\n{BOLD}{GREEN}✓ Reached requested post count ({max_posts}). Exiting cleanly.{RESET}")
                sys.exit(0)

    # Schedule the recurring job
    schedule.every(interval).hours.do(scheduled_job)
    print(f"\n{DIM}Agent is now active and waiting for the next scheduled interval ({interval}h)...{RESET}")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Exiting agent gracefully upon user request (Ctrl+C). Goodbye!{RESET}")
        sys.exit(0)
