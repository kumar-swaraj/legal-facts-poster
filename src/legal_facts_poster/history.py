import os
import time
from .config import HISTORY_FILE

def get_history() -> list[str]:
    """Retrieves list of previously posted topics from history file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    topics = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Parse '[YYYY-MM-DD HH:MM:SS] Topic Name' or fallback to raw topic
            if line.startswith("[") and "]" in line:
                topic = line.split("]", 1)[1].strip()
                if topic:
                    topics.append(topic)
            else:
                topics.append(line)
    return topics

def save_to_history(topic: str) -> None:
    """Appends a newly published topic with a timestamp to the history file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {topic.strip()}\n")
