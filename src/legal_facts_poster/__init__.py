"""
Automated Legal Poster Package
"""

__version__ = "0.1.1"

from .ai_generator import GeneratedFact, generate_new_fact
from .browser_bot import (
    PostResult,
    detect_system_browser,
    install_browser,
    is_browser_installed,
    login_and_post,
)
from .cli import main
from .runner import run_schedule_loop, run_single_post

__all__ = [
    "__version__",
    "main",
    "run_single_post",
    "run_schedule_loop",
    "generate_new_fact",
    "GeneratedFact",
    "login_and_post",
    "PostResult",
    "detect_system_browser",
    "install_browser",
    "is_browser_installed",
]
