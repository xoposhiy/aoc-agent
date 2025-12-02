from typing import Dict, Optional
from .base import CodeRunner
from .python import PythonRunner
from .kotlin import KotlinRunner
from .csharp import CSharpRunner
from .lean4 import Lean4Runner

_runners: Dict[str, CodeRunner] = {
    "python": PythonRunner(),
    "kotlin": KotlinRunner(),
    "csharp": CSharpRunner(),
    "lean4": Lean4Runner()
}

def get_runner(lang: str) -> Optional[CodeRunner]:
    return _runners.get(lang)
