import os
import sys
import subprocess
from typing import Any
from .base import CodeRunner

class PythonRunner(CodeRunner):
    def get_version_info(self) -> str:
        return f"Python {sys.version}"

    def run(self, working_dir: str, code_filename: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, code_filename],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
