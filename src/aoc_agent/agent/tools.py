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

        runner = get_runner(self.context.language)
        if runner and self.run_code.__doc__ and "Environment version" not in self.run_code.__doc__:
             version_info = runner.get_version_info()
             self.run_code.__func__.__doc__ += f"\n\n        Environment version: {version_info}"

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
        The input is saved to `input.txt` in your working directory.

        Args:
            year: The year of the puzzle.
            day: The day of the puzzle.

        Returns:
            A log message indicating whether the download was successful or if the file already existed.
        """
        file_path = data_path(year, day, "input.txt")
        
        if not os.path.exists(file_path):
            try:
                text = self.client.get_input(year, day)
                with open(file_path, "w") as f:
                    f.write(text)
            except Exception as e:
                return log_error(f"Error downloading input: {e}")
        
        # Copy to working directory
        working_dir = self.context.working_dir
        dest_path = os.path.join(working_dir, "input.txt")
        shutil.copy(file_path, dest_path)

        return log_info(f"puzzle input is downloaded to input.txt.")

    def _get_next_run_number(self, working_dir: str) -> int:
        """Finds the next available run number."""
        if not os.path.exists(working_dir):
            return 1
            
        existing = [d for d in os.listdir(working_dir) if os.path.isdir(os.path.join(working_dir, d)) and d.startswith("coderun-")]
        if not existing:
            return 1
        
        numbers = []
        for d in existing:
            try:
                num = int(d.split("-")[1])
                numbers.append(num)
            except (IndexError, ValueError):
                continue
        
        return max(numbers) + 1 if numbers else 1

    def _save_run_info(self, working_dir: str, code_filename: str, 
                       stdout: str, stderr: str, duration: float, 
                       exit_code: int | str, error: Optional[str] = None):
        
        run_number = self._get_next_run_number(working_dir)
        run_dir_name = f"coderun-{run_number}"
        run_dir_path = os.path.join(working_dir, run_dir_name)
        os.makedirs(run_dir_path, exist_ok=True)
        
        run_info = {
            "error": error,
            "stdout": stdout,
            "stderr": stderr,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "original_filename": code_filename
        }
        
        with open(os.path.join(run_dir_path, "result.json"), "w") as f:
            json.dump(run_info, f, indent=2)

        # Copy code file
        src_code_path = os.path.join(working_dir, code_filename)
        if os.path.exists(src_code_path):
             shutil.copy(src_code_path, os.path.join(run_dir_path, code_filename))

    def run_code(self, code_filename: str) -> str:
        """
        Executes the provided source code file.

        code_filename.out.txt — full output of the execution.
        code_filename.err.txt — full error output of the execution.

        Constraints:
            - Execution time limit: 60 seconds.
            - No network access.
            - Output (stdout/stderr) is truncated to 3000 characters.
            - No command line arguments provided to your program

        Args:
            code_filename: Filename in the working directory to execute. Executor will be determined by file extension.

        Returns:
            The truncated standard output (stdout) if execution is successful (exit code 0).
            The truncated standard error (stderr) if execution fails (non-zero exit code).
        """
        print(f"Run code: {code_filename}")

        working_dir = self.context.working_dir
        language = self.context.language

        try:
            runner = get_runner(language)
            if not runner:
                return log_error(f"Error: Unsupported language {language}")

            start_time = time.time()
            result = runner.run(working_dir, code_filename)
            duration = time.time() - start_time

            if result.returncode != 0:
                self.context.record_run_code_error()
                stderr = truncate_output(result.stderr)
                stdout = truncate_output(result.stdout)
                
                self._save_run_info(working_dir, code_filename, result.stdout, result.stderr, duration, result.returncode, "Non-zero exit code")

                return log_error(f"stderr:\n{stderr}\nstdout:\n{stdout}\n\nEnvironment:\n{runner.get_version_info()}")
            
            self.context.record_run_code_success()
            log_output = f"stdout: {truncate_output(result.stdout)}"
            
            # Save run info
            self._save_run_info(working_dir, code_filename, result.stdout, result.stderr, duration, result.returncode)
                
            return log_info(log_output)

        except subprocess.TimeoutExpired as e:
            self.context.record_run_code_error()
            stdout = truncate_output(e.stdout) if e.stdout else ""
            
            self._save_run_info(working_dir, code_filename, e.stdout if e.stdout else "", e.stderr if e.stderr else "", 60.0, "timeout", "TimeoutExpired")

            return log_error(f"Error: Execution was interrupted because it ran longer than 60 seconds. stdout:\n{stdout}")
        except Exception as e:
            self._save_run_info(working_dir, code_filename, "", "", 0.0, "exception", str(e))
            return log_error(f"Exception: {str(e)}")

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

    def submit_report(self, report_md_file: str, image_files: List[str]) -> str:
        """
        Signals the completion of the report preparation.

        The agent MUST create the report file and any image files using filesystem tools BEFORE calling this tool.

        Args:
            report_md_file: The filename of the Markdown report (must exist in working directory).
            image_files: A list of filenames for images included in the report.

        Returns:
            A success message if the report file exists.
        """
        working_dir = self.context.working_dir
        report_path = os.path.join(working_dir, report_md_file)
        
        if not os.path.exists(report_path):
             return log_error(f"Error: Report file '{report_md_file}' not found. Please create it first using write_file.")
        
        for img in image_files:
             img_path = os.path.join(working_dir, img)
             if not os.path.exists(img_path):
                 log_error(f"Warning: Image file '{img}' not found.")

        self.context.final_report_path = report_md_file
        self.context.final_report_images = image_files
        self.context.final_report_written = True
        
        return log_success(f"Report submitted: {report_md_file}. Agent loop will be finished.")

    def make_tools(self, language: Optional[Lang] = None) -> List[Callable]:
        tools = [
            self.get_task_statement,
            self.download_puzzle_input,
            self.run_code,
            self.submit_result,
            self.complain,
            self.submit_report
        ]
        return tools
