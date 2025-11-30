import os
import sys
import subprocess
from typing import Any
from .base import CodeRunner

class PythonRunner(CodeRunner):
    def get_version_info(self) -> str:
        return f"Python {sys.version}"

    def run(self, working_dir: str, code_filename: str, solution_code: str) -> subprocess.CompletedProcess:
        file_path = os.path.join(working_dir, code_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(solution_code)

        return subprocess.run(
            [sys.executable, code_filename],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
