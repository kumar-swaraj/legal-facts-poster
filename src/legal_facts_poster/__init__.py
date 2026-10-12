"""
Automated Legal Poster Package
"""

__version__ = "0.1.0"

from .ai_generator import generate_new_fact
from .browser_bot import login_and_post
from .cli import main
from .runner import run_schedule_loop, run_single_post

__all__ = [
    "__version__",
    "main",
    "run_single_post",
    "run_schedule_loop",
    "generate_new_fact",
    "login_and_post",
]
