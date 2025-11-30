import os
import re
import time
import requests
from rich import print
from .html_parsing import parse_wait_time

class AocClient:
    def __init__(self):
        self.session = os.environ.get("AOC_SESSION")
        if not self.session:
            raise ValueError("AOC_SESSION environment variable is not set")
        self.base_url = "https://adventofcode.com"
        self.headers = {"User-Agent": "aoc-agent/0.1.0"}
        self.cookies = {"session": self.session}

    def get_task_html(self, year: int, day: int) -> str:
        url = f"{self.base_url}/{year}/day/{day}"
        response = requests.get(url, cookies=self.cookies, headers=self.headers)
        response.raise_for_status()
        return response.text

    def get_input(self, year: int, day: int) -> str:
        url = f"{self.base_url}/{year}/day/{day}/input"
        response = requests.get(url, cookies=self.cookies, headers=self.headers)
        response.raise_for_status()
        return response.text

    def submit_answer(self, year: int, day: int, part: int, answer: str) -> str:
        url = f"{self.base_url}/{year}/day/{day}/answer"
        data = {"level": str(part), "answer": answer}
        
        print(f"Submitting to {url} with data {data}")
        response = requests.post(url, cookies=self.cookies, headers=self.headers, data=data)
        response.raise_for_status()
        
        text = response.text
        
        if "You gave an answer too recently" in text:
            total_seconds = parse_wait_time(text)
            
            if total_seconds > 0:
                wait_time = total_seconds + 1
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                return self.submit_answer(year, day, part, answer)
        
        return text
