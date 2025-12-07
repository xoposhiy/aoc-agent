from abc import ABC, abstractmethod
import subprocess
from typing import Any

class CodeRunner(ABC):
    @abstractmethod
    def run(self, working_dir: str, code_filename: str) -> subprocess.CompletedProcess:
        """
        Runs the solution code in the specified working directory.
        
        Args:
            working_dir: The directory where the code should be executed.
            code_filename: The name of the source code file to execute (must exist in working_dir).

        Returns:
            subprocess.CompletedProcess: The result of the execution.
        """
        pass

    @abstractmethod
    def get_version_info(self) -> str:
        """
        Returns information about the language version and standard library.
        """
        pass
