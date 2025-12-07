import subprocess
import os
from typing import Any
from .base import CodeRunner

class Lean4Runner(CodeRunner):
    def get_version_info(self) -> str:
        try:
            res = subprocess.run(["lean", "--version"], capture_output=True, text=True)
            return res.stdout.strip()
        except FileNotFoundError:
            return "Lean executable not found. Please install Lean 4."
        except Exception as e:
            return f"Error getting Lean version: {e}"

    def run(self, working_dir: str, code_filename: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["lean", "--run", code_filename],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
