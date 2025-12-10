from __future__ import annotations

import os
import time
import uuid
import json
from datetime import datetime
from typing import List, Set, cast, Any
from rich import print

from aoc_agent.core.aoc_client import AocClient
from .context import AgentContext
from .tools import Lang
from .miniagent import MiniAgent

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
        agent_def = MiniAgent()
        total_runs = len(self.days) * len(self.languages) * len(self.models) * self.n_repeats
        current_run = 0

        print(f"[bold green]Starting AgentRunner for {total_runs} runs...[/bold green]")
        
        for day in self.days:
            for lang in self.languages:
                for model in self.models:
                    for i in range(self.n_repeats):
                        current_run += 1
                        print(f"\n[bold cyan]Run {current_run}/{total_runs}[/bold cyan]: Day {day}, {lang}, {model}, Repeat {i+1}")
                        self._run_single_case(agent_def, self.year, day, cast(Lang, lang), model)

    def _run_single_case(self, agent_def: MiniAgent, year: int, day: int, lang: Lang, model_name: str):
        
        start_time_friendly = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_id = f"{start_time_friendly}_{year}_{day}_{lang}_{model_name.replace(':','-')}_{str(uuid.uuid4())[:8]}"
        run_dir = os.path.join("data", "run", run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        print(f"[bold green]AoC Agent starting[/bold green]: year={year}, day={day}, lang={lang}, run_id={run_id} model={model_name}")

        client = AocClient()
        context = AgentContext(
            run_id=run_id, 
            start_time=(time.time()), 
            year=year, 
            day=day, 
            language=lang, 
            model_name=model_name,
            working_dir=run_dir
        )
        
        history_file = os.path.join(run_dir, "history.json")
        history = []
        
        no_report_flag = self.no_report
        if lang != "python":
            no_report_flag = True

        try:
            for chunk in agent_def.execute(client, context):
                history.append(chunk)
                with open(history_file, "w") as f:
                    json.dump(history, f, indent=2, default=str)

                if context.final_report_written:
                    print("[green]Final report written. Stopping agent.[/green]")
                    break

                if no_report_flag and (context.part2_finished or (day == 25 and context.part1_finished)):
                    print("[green]All parts solved. Skipping final report and stopping agent.[/green]")
                    break
            print("Writing metadata.json...")
            self._write_metadata(context, run_dir, model_name, lang, year, day, run_id)
        except Exception as e:
            print(f"[red]Unexpected error running agent. Ignore metadata!:\n{e}[/red]")

    def _write_metadata(self, context: AgentContext, run_dir: str, model_name: str, lang: str, year: int, day: int, run_id: str):
         metadata = {
            "run_id": run_id,
            "year": year,
            "day": day,
            "lang": lang,
            "model": model_name,
            "agent_name": "MiniAgent",
            "start_time": datetime.fromtimestamp(context.start_time).isoformat(),
            "part1_duration": context.part1_duration,
            "part1_output_tokens": context.part1_output_tokens,
            "part1_solved": context.part1_finished,
            "part2_solved": context.part2_finished or day == 25,
            "part12_output_tokens": context.part2_output_tokens,
            "part12_duration": context.part2_duration,
            "report_output_tokens": context.output_tokens - context.part1_output_tokens,
            "part1_incorrect": context.part1_incorrect,
            "part2_incorrect": context.part2_incorrect,
            "part1_run_code_errors": context.part1_run_code_errors,
            "part2_run_code_errors": context.part2_run_code_errors,
            "part1_run_code_success": context.part1_run_code_success,
            "part2_run_code_success": context.part2_run_code_success,
            "final_report_path": context.final_report_path,
            "final_report_images": context.final_report_images
        }
         with open(os.path.join(run_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
