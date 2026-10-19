import argparse
import sys

from . import __version__
from .config import (
    POST_INTERVAL_HOURS,
    init_env_template,
    reload_config,
)
from .runner import run_schedule_loop, run_single_post


def parse_args():
    parser = argparse.ArgumentParser(
        prog="legal-post", description="Automated AI Legal Insights Poster for Community Feed."
    )
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--once", "-1", action="store_true", help="Publish a single post immediately and exit."
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Run the interactive setup wizard to configure credentials.",
    )
    parser.add_argument(
        "--env-file", type=str, default=None, help="Path to a custom .env configuration file."
    )
    parser.add_argument(
        "--init-env",
        action="store_true",
        help="Generate a sample .env template file in the current directory and exit.",
    )
    parser.add_argument(
        "-n",
        "--num-posts",
        type=int,
        default=None,
        help="Number of successful posts to make before exiting. Defaults to running indefinitely.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=POST_INTERVAL_HOURS,
        help=f"Hours between scheduled posts (default: {POST_INTERVAL_HOURS}h).",
    )

    headless_group = parser.add_mutually_exclusive_group()
    headless_group.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=None,
        help="Run browser in background without showing a window.",
    )
    headless_group.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        default=None,
        help="Display the browser window while running.",
    )

    parser.add_argument(
        "--skip-immediate",
        dest="run_immediately",
        action="store_false",
        default=True,
        help="Skip the immediate first post and wait directly for the scheduled interval.",
    )

    return parser.parse_args()


def post_once_cli():
    """Dedicated CLI entrypoint to publish exactly one post and exit."""
    parser = argparse.ArgumentParser(
        prog="post-once",
        description="Publish a single Indian legal insight to the community feed and exit.",
    )
    parser.add_argument(
        "--env-file", type=str, default=None, help="Path to a custom .env configuration file."
    )
    parser.add_argument(
        "--init-env",
        action="store_true",
        help="Generate a sample .env template file in the current directory and exit.",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Run the interactive setup wizard to configure credentials.",
    )
    headless_group = parser.add_mutually_exclusive_group()
    headless_group.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=None,
        help="Run browser in background without showing a window.",
    )
    headless_group.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        default=None,
        help="Display the browser window while running.",
    )

    if len(sys.argv) > 1 and sys.argv[1] in ("config", "setup"):
        from .wizard import run_wizard

        run_wizard()
        sys.exit(0)

    args = parser.parse_args()

    if getattr(args, "config", False):
        from .wizard import run_wizard

        run_wizard()
        sys.exit(0)

    if args.init_env:
        print(init_env_template())
        sys.exit(0)

    if args.env_file:
        reload_config(args.env_file)

    try:
        success = run_single_post(fail_fast=True, headless=args.headless, is_recurring=False)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\033[33m✕ Operation cancelled by user (Ctrl+C). Exiting.\033[0m")
        sys.exit(130)


def main():
    """Main CLI entrypoint."""
    if len(sys.argv) > 1 and sys.argv[1] in ("config", "setup"):
        from .wizard import run_wizard

        run_wizard()
        sys.exit(0)

    args = parse_args()

    if getattr(args, "config", False):
        from .wizard import run_wizard

        run_wizard()
        sys.exit(0)

    if args.init_env:
        print(init_env_template())
        sys.exit(0)

    if args.env_file:
        reload_config(args.env_file)

    max_posts = 1 if args.once else args.num_posts
    try:
        run_schedule_loop(
            interval_hours=args.interval,
            max_posts=max_posts,
            headless=args.headless,
            run_immediately=args.run_immediately,
        )
    except KeyboardInterrupt:
        print("\n\033[33m✕ Agent stopped by user (Ctrl+C). Exiting.\033[0m")
        sys.exit(130)


if __name__ == "__main__":
    main()
