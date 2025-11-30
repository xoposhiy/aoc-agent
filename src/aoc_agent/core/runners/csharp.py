import os
import subprocess
from pathlib import Path
from typing import Any
from .base import CodeRunner

class CSharpRunner(CodeRunner):
    def get_version_info(self) -> str:
        try:
            res = subprocess.run(["dotnet", "--version"], capture_output=True, text=True)
            version = res.stdout.strip()
            return f"Dotnet {version}; TargetFramework: net9.0"
        except Exception:
            return "Unknown Dotnet version"

    def run(self, working_dir: str, code_filename: str, solution_code: str) -> subprocess.CompletedProcess:
        file_path = os.path.join(working_dir, code_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(solution_code)

        project_filename = Path(code_filename).stem + ".csproj"
        project_path = os.path.join(working_dir, project_filename)

        csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
    <WarningLevel>0</WarningLevel>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="{code_filename}" />
  </ItemGroup>
</Project>"""

        with open(project_path, "w", encoding="utf-8") as f:
            f.write(csproj_content)

        return subprocess.run(
            ["dotnet", "run", "--project", project_filename],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
