from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from typing import Literal

from dotenv import load_dotenv

from aoc_agent.agent.report_builder import ReportBuilder
from .agent.agent_runner import AgentRunner

print(os.environ.get("AOC_SESSION"))
load_dotenv()
print(os.environ.get("AOC_SESSION"))
Lang = Literal["python", "kotlin", "csharp"]
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_PROJECT"] = "aoc-agent"

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="aoc-agent",
        description="Advent of Code Autonomous Agent (stub)",
    )
    parser.add_argument("--year", type=int, required=False, help="AoC year, e.g. 2024")
    parser.add_argument("--days", type=str, required=False, help="AoC days, e.g. '1-5, 7'")
    parser.add_argument(
        "--langs",
        type=str,
        nargs="+",
        required=False,
        default=["python"],
        choices=["python", "kotlin", "csharp"],
        help="Languages to use for generated solutions",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["gemini-2.5-flash"],
        help="Models to use (default: gemini-2.5-flash)",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repeats for each combination",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        default=False,
        help="Skip creating final report and exit after successful submission",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        required=False,
        help="Time to start the agent, format HH:MM (24h)",
    )
    return parser.parse_args(argv)


def wait_for_start_time(start_time_str: str) -> None:
    now = datetime.datetime.now()
    try:
        target_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
    except ValueError:
        print(f"Invalid time format: {start_time_str}. Expected HH:MM.")
        sys.exit(1)

    target_datetime = datetime.datetime.combine(now.date(), target_time)

    if target_datetime <= now:
        target_datetime += datetime.timedelta(days=1)

    wait_seconds = (target_datetime - now).total_seconds()
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target time: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Waiting {wait_seconds:.2f} seconds...")
    time.sleep(wait_seconds)


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv)
    if ns.start_time:
        wait_for_start_time(ns.start_time)

    if ns.days:
        runner = AgentRunner(
            year=ns.year,
            days_region=ns.days,
            languages=ns.langs,
            models=ns.models,
            n_repeats=ns.repeats,
            no_report=ns.no_report,
        )
        runner.run()
    ReportBuilder().build_report()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
