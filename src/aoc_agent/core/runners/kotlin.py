import os
import subprocess
from typing import Any
from .base import CodeRunner

class KotlinRunner(CodeRunner):
    def get_version_info(self) -> str:
        try:
            # kotlinc writes version to stderr
            res = subprocess.run(["kotlinc", "-version"], capture_output=True, text=True, shell=True)
            output = res.stderr.strip()
            if not output:
                output = res.stdout.strip()
            return output if output else "Unknown Kotlin version"
        except Exception:
            return "Unknown Kotlin version"

    def run(self, working_dir: str, code_filename: str, solution_code: str) -> subprocess.CompletedProcess:
        jar_filename = os.path.splitext(code_filename)[0] + ".jar"
        file_path = os.path.join(working_dir, code_filename)
        with open(file_path, "w", encoding="utf-8") as f:
             f.write(solution_code)

        # Compile
        compile_cmd = f"kotlinc {code_filename} -include-runtime -d {jar_filename}"
        compile_result = subprocess.run(
            compile_cmd,
            cwd=working_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        if compile_result.returncode != 0:
            # Prepend compilation failure message to stderr so the caller can see it
            compile_result.stderr = f"Compilation failed:\n{compile_result.stderr}\n{compile_result.stdout}"
            return compile_result

        # Run
        return subprocess.run(
            ["java", "-jar", jar_filename],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
