"""
Post a single legal insight to the community feed and exit immediately.

Usage:
    python post_once.py
    python post_once.py --headless
"""

import os
import sys

# Add 'src' directory to path for local development and direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from legal_facts_poster.cli import post_once_cli

if __name__ == "__main__":
    post_once_cli()
