from typing import Dict, Optional
from .base import CodeRunner
from .python import PythonRunner
from .kotlin import KotlinRunner
from .csharp import CSharpRunner

_runners: Dict[str, CodeRunner] = {
    "python": PythonRunner(),
    "kotlin": KotlinRunner(),
    "csharp": CSharpRunner()
}

def get_runner(lang: str) -> Optional[CodeRunner]:
    return _runners.get(lang)
