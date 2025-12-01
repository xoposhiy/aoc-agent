from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any, Set, cast
from collections import defaultdict

from .miniagent import MiniAgent, Lang
from .report_builder import ReportBuilder
from rich import print
import json

class AgentRunner:
    def __init__(self, year: int, days_region: str, languages: List[str], models: List[str], n_repeats: int, no_report: bool = False):
        self.year = year
        self.days = self._parse_days(days_region)
        self.languages = languages
        self.models = models
        self.n_repeats = n_repeats
        self.no_report = no_report

    def _parse_days(self, region: str) -> List[int]:
        days: Set[int] = set()
        parts = region.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                start, end = map(int, part.split('-'))
                days.update(range(start, end + 1))
            else:
                days.add(int(part))
        return sorted(list(days))

    def run(self) -> None:
        agent = MiniAgent()
        total_runs = len(self.days) * len(self.languages) * len(self.models) * self.n_repeats
        current_run = 0

        print(f"[bold green]Starting AgentRunner for {total_runs} runs...[/bold green]")
        print(f"Year: {self.year}")
        print(f"Days: {self.days}")
        print(f"Languages: {self.languages}")
        print(f"Models: {self.models}")
        print(f"Repeats: {self.n_repeats}")

        for day in self.days:
            for lang in self.languages:
                for model in self.models:
                    for i in range(self.n_repeats):
                        current_run += 1
                        print(f"\n[bold cyan]Run {current_run}/{total_runs}[/bold cyan]: Day {day}, {lang}, {model}, Repeat {i+1}")
                        agent.run_agent(self.year, day, cast(Lang, lang), model_name=model, no_report=self.no_report)

