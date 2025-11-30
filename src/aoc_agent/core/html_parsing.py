import re
from typing import List, Optional


def extract_task_articles(html: str) -> List[str]:
    """Extracts the task description articles from the HTML."""
    return re.findall(r'<article class="day-desc">(.*?)</article>', html, re.DOTALL)


def extract_puzzle_answers(html: str) -> List[str]:
    """Extracts the puzzle answers from the HTML."""
    return re.findall(r'Your puzzle answer was <code>(.*?)</code>', html)


def parse_submission_message(html: str) -> Optional[str]:
    """
    Parses the submission response HTML to extract the main message.
    Removes HTML tags and cleans up whitespace.
    """
    matches = re.findall(r'<article>(.*?)</article>', html, re.DOTALL)
    if matches:
        article_content = matches[0]
        # Remove HTML tags for cleaner output
        text = re.sub(r'<[^>]+>', '', article_content).strip()
        # Collapse multiple newlines
        text = re.sub(r'\n+', '\n', text)
        return text
    return None


def parse_wait_time(text: str) -> int:
    """
    Parses the 'You have ... left to wait' message to get the wait time in seconds.
    Returns 0 if the message is not found.
    """
    wait_match = re.search(r"You have (.+) left to wait", text)
    if wait_match:
        time_str = wait_match.group(1)
        minutes = 0
        seconds = 0

        min_match = re.search(r"(\d+)m", time_str)
        if min_match:
            minutes = int(min_match.group(1))

        sec_match = re.search(r"(\d+)s", time_str)
        if sec_match:
            seconds = int(sec_match.group(1))

        return minutes * 60 + seconds
    return 0
