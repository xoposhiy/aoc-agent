from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, List, Callable, Any
from langchain_core.runnables import RunnableConfig
from rich import print

from .context import AgentContext
from ..core.aoc_client import AocClient
from ..core.html_parsing import extract_task_articles, extract_puzzle_answers, parse_submission_message
from ..core.runners import get_runner

Lang = Literal["python", "kotlin", "csharp", "lean4"]


def log_success(text: str):
    print(f"[green]{text}[/green]")
    return text


def log_info(text: str):
    if text.strip().startswith("Success"):
        print(f"[green]{text}[/green]")
    else:
        print(text)
    return text


def log_error(error: str):
    print(f"[red]{error}[/red]")
    return error


def truncate_output(text: str, max_len: int = 3000) -> str:
    if len(text) <= max_len:
        return text

    trunc_msg = " ... (truncated) ... "
    if max_len < len(trunc_msg):
        return text[:max_len]

    keep_len = (max_len - len(trunc_msg)) // 2

    return text[:keep_len] + trunc_msg + text[-keep_len:]


def data_path(year: int, day: int, filename: str = "") -> str:
    working_dir = os.path.join("data", str(year), str(day))
    os.makedirs(working_dir, exist_ok=True)
    if not filename:
        return working_dir
    return os.path.join(working_dir, filename)


class AocToolbox:
    def __init__(self, client: AocClient, context: AgentContext):
        self.client = client
        self.context = context

        # Append environment info to run_code docstring so LLM knows versions
        lang_tools = {
            "python": AocToolbox.run_python,
            "kotlin": AocToolbox.run_kotlin,
            "csharp": AocToolbox.run_csharp,
            "lean4": AocToolbox.run_lean4
        }

        for lang, tool_method in lang_tools.items():
            runner = get_runner(lang)
            if runner and tool_method.__doc__ and "Environment version" not in tool_method.__doc__:
                 version_info = runner.get_version_info()
                 tool_method.__doc__ += f"\n\n        Environment version: {version_info}"

    def get_task_statement(self, year: int, day: int, part: int) -> str:
        """
        Retrieves the task statement for the given year, day, and part.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            part: The part number (1 or 2).

        Returns:
            The HTML content of the task statement.

        Note:
            Part 2 is typically only available after Part 1 is successfully solved.
            If you request Part 2 before solving Part 1, this might return an error.
        """
        if part < 1 or part > 2:
            raise ValueError("Part number must be 1 or 2.")
        print(f"Get task statement year={year} day={day} part={part}")

        task_path = data_path(year, day, f"task_{part}.html")
        if os.path.exists(task_path):
            with open(task_path, "r", encoding="utf-8") as f:
                return f.read()

        # Use client to get HTML
        try:
            text = self.client.get_task_html(year, day)
        except Exception as e:
             return log_error(f"Error fetching task: {e}")

        articles = extract_task_articles(text)
        
        if not articles:
            return log_error(f"Error: Could not find task statement in response")

        # Save all available parts
        for i, article in enumerate(articles):
            p = i + 1
            with open(data_path(year, day, f"task_{p}.html"), "w", encoding="utf-8") as f:
                f.write(article)

        if len(articles) > 2:
            return log_error(f"Error: Found more than 2 parts in the statement.")

        # Extract and save answers (logic from original tools.py)
        answers = extract_puzzle_answers(text)
        for i, answer in enumerate(answers):
            p = i + 1
            with open(data_path(year, day, f"part_{p}.ans"), "w", encoding="utf-8") as f:
                f.write(answer)

        if part <= len(articles):
            return articles[part - 1]
        else:
            return log_error(f"Error: Part 2 is not available yet. Solve Part 1 first, and query part 2 statement again.")

    def download_puzzle_input(self, year: int, day: int) -> str:
        """
        Downloads the puzzle input for the specified year and day.
        The input is saved to `input.txt` in the task's working directory.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.

        Returns:
            A log message indicating whether the download was successful or if the file already existed.
        """
        file_path = data_path(year, day, "input.txt")
        if os.path.exists(file_path):
            return log_info(f"puzzle input is in input.txt")

        try:
            text = self.client.get_input(year, day)
        except Exception as e:
            return log_error(f"Error downloading input: {e}")
        
        with open(file_path, "w") as f:
            f.write(text)
        return log_info(f"puzzle input is downloaded to input.txt.")

    def _run_code(self, year: int, day: int, language: Lang, code_filename: str, solution_code: str) -> str:
        """
        Executes the provided solution code.

        The code runs without command-line arguments or stdin input.
        It should read the puzzle input from `./input.txt` (ensure `download_puzzle_input` is called first).

        Constraints:
            - Execution time limit: 60 seconds.
            - No network access.
            - Output (stdout/stderr) is truncated to 3000 characters.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            language: The programming language ('python', 'kotlin', 'csharp', 'lean4').
            code_filename: A descriptive name for the code file (e.g., 'solve_part2_bfs.py'). Avoid generic names.
            solution_code: The actual source code to execute.

        Returns:
            The standard output (stdout) if execution is successful (exit code 0).
            The standard error (stderr) if execution fails (non-zero exit code).
        """
        print(f"Run code: {code_filename}")

        run_id = self.context.run_id
        run_dir = os.path.join("data", "run", run_id)
        os.makedirs(run_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)
        fn = Path(code_filename)
        run_code_path = f"{fn.stem}_{timestamp}{fn.suffix}"
        input_src = data_path(year, day, "input.txt")
        if os.path.exists(input_src):
            shutil.copy(input_src, run_dir)

        working_dir = run_dir
        try:
            runner = get_runner(language)
            if not runner:
                return log_error(f"Error: Unsupported language {language}")

            start_time = time.time()
            result = runner.run(working_dir, run_code_path, solution_code)

            if result.returncode != 0:
                self.context.record_run_code_error()
                stderr = truncate_output(result.stderr)
                stdout = truncate_output(result.stdout)
                
                run_info = {
                    "error": "Non-zero exit code",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "duration": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "exit_code": result.returncode
                }
                with open(os.path.join(working_dir, f"{run_code_path}.run_info.json"), "w") as f:
                    json.dump(run_info, f, indent=2)

                return log_error(f"stderr:\n{stderr}\nstdout:\n{stdout}\n\nEnvironment:\n{runner.get_version_info()}")
            
            self.context.record_run_code_success()
            log_output = f"stdout: {truncate_output(result.stdout)}"
            
            # Save run info
            run_info = {
                "error": None,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "exit_code": result.returncode
            }
            with open(os.path.join(working_dir, f"{run_code_path}.run_info.json"), "w") as f:
                json.dump(run_info, f, indent=2)
                
            return log_info(log_output)

        except subprocess.TimeoutExpired as e:
            self.context.record_run_code_error()
            stdout = truncate_output(e.stdout) if e.stdout else ""
            
            run_info = {
                "error": "TimeoutExpired",
                "stdout": e.stdout if e.stdout else "",
                "stderr": e.stderr if e.stderr else "",
                "duration": 60.0, # Timeout limit
                "timestamp": datetime.now().isoformat(),
                "exit_code": "timeout"
            }
            with open(os.path.join(working_dir, f"{run_code_path}.run_info.json"), "w") as f:
                json.dump(run_info, f, indent=2)

            return log_error(f"Error: Execution was interrupted because it ran longer than 60 seconds. stdout:\n{stdout}")
        except Exception as e:
            run_info = {
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "duration": 0.0,
                "timestamp": datetime.now().isoformat(),
                "exit_code": "exception"
            }
            with open(os.path.join(working_dir, f"{run_code_path}.run_info.json"), "w") as f:
                json.dump(run_info, f, indent=2)
            return log_error(f"Exception: {str(e)}")

    def run_python(self, year: int, day: int, code_filename: str, solution_code: str) -> str:
        """
        Executes the provided Python solution code.

        The code runs without command-line arguments or stdin input.
        It should read the puzzle input from `./input.txt` (ensure `download_puzzle_input` is called first).

        Constraints:
            - Execution time limit: 60 seconds.
            - No network access.
            - Output (stdout/stderr) is truncated to 3000 characters.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            code_filename: A descriptive name for the code file (e.g., 'solve_part2_bfs.py'). Avoid generic names.
            solution_code: The actual source code to execute.

        Returns:
            The standard output (stdout) if execution is successful (exit code 0).
            The standard error (stderr) if execution fails (non-zero exit code).
        """
        return self._run_code(year, day, "python", code_filename, solution_code)

    def run_kotlin(self, year: int, day: int, code_filename: str, solution_code: str) -> str:
        """
        Executes the provided Kotlin solution code.

        The code runs without command-line arguments or stdin input.
        It should read the puzzle input from `./input.txt` (ensure `download_puzzle_input` is called first).

        Constraints:
            - Execution time limit: 60 seconds.
            - No network access.
            - Output (stdout/stderr) is truncated to 3000 characters.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            code_filename: A descriptive name for the code file (e.g., 'Solution.kt'). Avoid generic names.
            solution_code: The actual source code to execute.

        Returns:
            The standard output (stdout) if execution is successful (exit code 0).
            The standard error (stderr) if execution fails (non-zero exit code).
        """
        return self._run_code(year, day, "kotlin", code_filename, solution_code)

    def run_csharp(self, year: int, day: int, code_filename: str, solution_code: str) -> str:
        """
        Executes the provided C# solution code.

        The code runs without command-line arguments or stdin input.
        It should read the puzzle input from `./input.txt` (ensure `download_puzzle_input` is called first).

        Constraints:
            - Execution time limit: 60 seconds.
            - No network access.
            - Output (stdout/stderr) is truncated to 3000 characters.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            code_filename: A descriptive name for the code file (e.g., 'Solution.cs'). Avoid generic names.
            solution_code: The actual source code to execute.

        Returns:
            The standard output (stdout) if execution is successful (exit code 0).
            The standard error (stderr) if execution fails (non-zero exit code).
        """
        return self._run_code(year, day, "csharp", code_filename, solution_code)

    def run_lean4(self, year: int, day: int, code_filename: str, solution_code: str) -> str:
        """
        Executes the provided Lean 4 solution code.

        The code runs without command-line arguments or stdin input.
        It should read the puzzle input from `./input.txt` (ensure `download_puzzle_input` is called first).

        Constraints:
            - Execution time limit: 60 seconds.
            - No network access.
            - Output (stdout/stderr) is truncated to 3000 characters.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            code_filename: A descriptive name for the code file (e.g., 'Solution.lean'). Avoid generic names.
            solution_code: The actual source code to execute.

        Returns:
            The standard output (stdout) if execution is successful (exit code 0).
            The standard error (stderr) if execution fails (non-zero exit code).
        """
        return self._run_code(year, day, "lean4", code_filename, solution_code)

    def complain(self, what_is_wrong: str) -> None:
        """
        Reports a critical issue or an unrecoverable error.

        Use this tool when the agent is stuck, encounters a fundamental problem, or cannot proceed.

        Args:
            what_is_wrong: A description of the problem.
        """
        print(f"[red]Complain: {what_is_wrong}[/red]", file=sys.stderr)

    def report_progress(self, current_progress: str) -> str:
        """
        Reports the current progress to the user.

        Use this to inform the user about ongoing steps, especially during long-running operations.

        Args:
            current_progress: A concise, one-line message describing the current action or status.
        """
        print(f"[blue]{current_progress}[/blue]")
        return "OK. Noted!"

    def submit_result(self, year: int, day: int, part: int, answer: str) -> str:
        """
        Submits the calculated answer to the Advent of Code server.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.
            part: The part number (1 or 2).
            answer: The calculated answer to submit.

        Returns:
            The server's response message, or a success/failure log message.
            Common responses include "That's the right answer", "That's not the right answer".
        """
        print(f"Submitting answer for Year {year}, Day {day}, Part {part}: {answer}")
        ans_file = data_path(year, day, f"part_{part}.ans")
        if os.path.exists(ans_file):
            with open(ans_file, "r") as f:
                saved_answer = f.read().strip()
            if saved_answer == str(answer).strip():
                self.context.record_success(part)
                return log_success(f"  Success! Answer {answer} matches the saved correct answer.")
            else:
                self.context.record_incorrect_submission(part)
                return log_error(f"  Incorrect! Answer {answer} does not match the saved answer.")

        try:
            response_text = self.client.submit_answer(year, day, part, answer)
        except Exception as e:
            return log_error(f"  Submission error: {e}")

        # Simple parsing of the response
        text = parse_submission_message(response_text)
        if text:
            if "That's the right answer" in text:
                with open(ans_file, "w") as f:
                    f.write(str(answer).strip())
                self.context.record_success(part)
                log_success(f"  Success: Answer {answer} saved and marked as correct.")
            else:
                self.context.record_incorrect_submission(part)
                log_error(f"  Incorrect! Response: {text.strip()}")

            return text

        return log_error(f"  Error: Could not parse response. raw: {response_text}")

    def write_final_report(self, content: str) -> str:
        """
        Writes a final educational report about the task and solution.
        
        The report should be written in Markdown and include:
        - A summary of the problem.
        - The algorithmic approach used for Part 1 and Part 2.
        - Key insights or "gotchas" encountered.
        - Why this solution is efficient/interesting.
        """
        run_id = self.context.run_id
        run_dir = os.path.join("data", "run", run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        report_path = os.path.join(run_dir, "final_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        self.context.final_report_written = True
        return log_success(f"Final report saved to {report_path}")

    def make_tools(self, language: Optional[Lang]) -> List[Callable]:
        tools = [
            self.get_task_statement,
            self.download_puzzle_input,
            self.submit_result,
            self.complain,
            self.report_progress,
            self.write_final_report
        ]

        run_tool = None
        if language == "python":
            run_tool = self.run_python
        elif language == "kotlin":
            run_tool = self.run_kotlin
        elif language == "csharp":
            run_tool = self.run_csharp
        elif language == "lean4":
            run_tool = self.run_lean4
        
        if run_tool:
            tools.append(run_tool)
            
        return tools
