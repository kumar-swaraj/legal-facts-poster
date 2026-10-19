"""
Automated Legal Poster Package
"""

__version__ = "0.1.1"

from .ai_generator import GeneratedFact, generate_new_fact
from .browser_bot import PostResult, login_and_post
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
]
