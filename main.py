import sys
import os

# Add 'src' directory to path for local development and direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from legal_facts_poster.cli import main

if __name__ == "__main__":
    main()
