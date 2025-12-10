import os
import json
import shutil
from pathlib import Path
import glob
import re

def sanitize_filename(name):
    # Replace invalid characters with underscores
    # Allow alphanumeric, underscores, hyphens, dots
    s = re.sub(r'[^\w\-\.]', '_', str(name))
    return s.strip('_')

def preprocess_markdown(content):
    lines = content.splitlines()
    processed = []
    in_code_block = False
    list_pattern = re.compile(r'^\s*([-*+]|\d+\.)\s+')
    
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            
        if not in_code_block and i > 0:
            if list_pattern.match(line):
                prev_line = lines[i-1]
                # If previous line is not empty, not a list item, and not a header
                if (prev_line.strip() and 
                    not list_pattern.match(prev_line) and 
                    not prev_line.lstrip().startswith('#')):
                    processed.append("")
        
        processed.append(line)
        
    return "\n".join(processed)

# Configuration
# We look for any directory starting with 'data' to include all runs
DATA_DIRS_PATTERN = "data"
OUTPUT_DIR = Path("report_site")
SITE_NAME = "AoC Agent Reports"

def load_metadata(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading metadata {path}: {e}")
        return {}

def format_duration(seconds):
    if seconds is None:
        return "N/A"
    return f"{float(seconds):.2f}s"

def generate_site():
    # Clean up output directory
    if OUTPUT_DIR.exists():
        try:
            shutil.rmtree(OUTPUT_DIR)
        except OSError:
            print("Warning: Could not remove report_site directory completely. Cleaning contents instead.")
            # If we can't delete the root, try deleting contents
            for item in OUTPUT_DIR.glob('*'):
                try:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                except OSError:
                    pass
    
    docs_dir = OUTPUT_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    runs = []
    
    # 1. Scan for runs
    # Find all directories matching the pattern in the current working directory
    data_dirs = glob.glob(DATA_DIRS_PATTERN)
    
    for data_dir in data_dirs:
        base_path = Path(data_dir)
        if not base_path.exists():
            continue
            
        print(f"Scanning {base_path}...")
        
        # Collect run directories: direct subdirs AND subdirs of 'run' folder
        run_candidates = list(base_path.glob("*"))
        if (base_path / "run").exists():
            run_candidates.extend((base_path / "run").glob("*"))

        for run_dir in run_candidates:
            if not run_dir.is_dir():
                continue
                
            meta_file = run_dir / "metadata.json"
            report_file = run_dir / "final_report.md"
            
            if meta_file.exists() and report_file.exists():
                meta = load_metadata(meta_file)
                if not meta:
                    continue
                    
                runs.append({
                    "meta": meta,
                    "path": run_dir,
                    "report_file": report_file,
                    "source_root": base_path.name
                })

    if not runs:
        print("No runs found with valid metadata.json and final_report.md")
        return

    # Sort runs by year, day, time (descending)
    runs.sort(key=lambda x: (
        x["meta"].get("year", 0), 
        x["meta"].get("day", 0), 
        x["meta"].get("start_time", "")
    ), reverse=True)
    
    print(f"Found {len(runs)} runs. Generating site...")

    # Track used slugs per day to ensure uniqueness
    # Key: (year, day), Value: set of used slugs
    used_slugs = {}

    # 2. Generate pages
    for run in runs:
        meta = run["meta"]
        year = meta.get("year", "Unknown")
        day = meta.get("day", "Unknown")
        run_id = meta.get("run_id", "unknown_run")
        model = meta.get("model", "unknown_model")

        # Determine directory name (slug)
        base_slug = sanitize_filename(model)
        slug = base_slug
        counter = 1
        
        day_key = (year, day)
        if day_key not in used_slugs:
            used_slugs[day_key] = set()
            
        while slug in used_slugs[day_key]:
            slug = f"{base_slug}_{counter}"
            counter += 1
            
        used_slugs[day_key].add(slug)
        run["slug"] = slug

        if slug == base_slug:
            run["display_model"] = model
        else:
            run["display_model"] = f"{model} ({counter-1})"
        
        # Create target directory
        # Structure: docs/YYYY/day_DD/MODEL_SLUG/
        target_dir = docs_dir / str(year) / f"day_{day:02d}" / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy assets (images, gifs)
        for asset in run["path"].glob("*"):
            if asset.name in ["final_report.md", "metadata.json", "history.json", "input.txt"]:
                continue
            # Copy likely media files
            if asset.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
                shutil.copy(asset, target_dir / asset.name)
                
        # Process Report
        try:
            with open(run["report_file"], "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading report {run['report_file']}: {e}")
            continue
            
        # Preprocess content to fix list rendering
        content = preprocess_markdown(content)
            
        # Header augmentation
        p1_solved = "✅" if meta.get("part1_solved") else "❌"
        p2_solved = "✅" if meta.get("part2_solved") else "❌"
        
        # Create a geeky header using standard markdown list
        header = f"""
# {meta.get('year')} Day {meta.get('day')} - {run['display_model']}

-   :robot: **Agent**: {meta.get('agent_name')} ({run['display_model']})
-   :flag_ru: **Language**: {meta.get('lang')}
-   :stopwatch: **Duration**: {format_duration(meta.get('part12_duration', 0))}
-   :star: **Stars**: P1: {p1_solved} | P2: {p2_solved}

"""     
        # Append code execution info
        code_report = ""
        
        # Find run info files matching pattern: filename.timestamp.json (LEGACY) or coderun-{n}/result.json (NEW)
        run_infos = []

        # 1. New format: coderun-{n} directories
        for d in run["path"].glob("coderun-*"):
            if d.is_dir():
                result_file = d / "result.json"
                if result_file.exists():
                    try:
                        with open(result_file, "r", encoding="utf-8") as f:
                            info = json.load(f)
                        # Store as (timestamp, info, directory_path, "new")
                        run_infos.append({
                            "timestamp": info.get('timestamp', ''),
                            "info": info,
                            "path": d,
                            "type": "new"
                        })
                    except Exception as e:
                        print(f"Error reading result.json in {d}: {e}")

        # 2. Legacy format: filename.timestamp.json
        run_info_pattern = re.compile(r"^(.+)\.(\d+)\.json$")
        for f in run["path"].glob("*.json"):
            if f.name in ["metadata.json", "history.json"]:
                continue
            if run_info_pattern.match(f.name):
                try:
                    with open(f, "r", encoding="utf-8") as json_f:
                        info = json.load(json_f)
                    run_infos.append({
                        "timestamp": info.get('timestamp', ''),
                        "info": info,
                        "path": f,
                        "type": "legacy"
                    })
                except Exception as e:
                    print(f"Error reading legacy run info {f}: {e}")

        # Sort by timestamp
        run_infos.sort(key=lambda x: x['timestamp'])
        
        if run_infos:
            code_report += "\n\n# Code Executions\n"
            for item in run_infos:
                info = item["info"]
                path = item["path"]
                
                try:
                    code_content = ""
                    code_file_name = "unknown"
                    
                    if item["type"] == "new":
                        # Look for code in the coderun directory
                        code_file_name = info.get("original_filename")
                        code_file = None
                        
                        if code_file_name:
                             code_file = path / code_file_name
                        
                        # Fallback: find any code file in the dir
                        if not code_file or not code_file.exists():
                             for f in path.iterdir():
                                 if f.suffix in ['.py', '.kt', '.cs', '.js', '.rs', '.go'] and f.name != "result.json":
                                     code_file = f
                                     code_file_name = f.name
                                     break
                        
                        if code_file and code_file.exists():
                            with open(code_file, "r", encoding="utf-8") as f:
                                code_content = f.read()
                        else:
                            code_content = "Code file not found in run directory."

                    else: # legacy
                        match = run_info_pattern.match(path.name)
                        if match:
                            code_file_name = match.group(1)
                            code_file = path.parent / code_file_name
                            if code_file.exists():
                                with open(code_file, "r", encoding="utf-8") as f:
                                    code_content = f.read()
                            else:
                                code_content = "Code file not found."

                    duration = f"{info.get('duration', 0):.2f}s"
                    exit_code = info.get('exit_code', 'N/A')
                    error = info.get('error')
                    timestamp = info.get('timestamp', '')
                    
                    status_icon = "✅" if str(exit_code) == "0" else "❌"
                    
                    # Infer language from extension
                    ext = Path(code_file_name).suffix.lower()
                    lang_md = "text"
                    if ext == ".py": lang_md = "python"
                    elif ext == ".kt": lang_md = "kotlin"
                    elif ext == ".cs": lang_md = "csharp"
                    elif ext == ".js": lang_md = "javascript"
                    elif ext == ".rs": lang_md = "rust"
                    elif ext == ".go": lang_md = "go"
                    
                    code_report += f"\n## {status_icon} {code_file_name}\n"
                    code_report += f"- **Timestamp**: {timestamp}\n"
                    code_report += f"- **Duration**: {duration}\n"
                    code_report += f"- **Exit Code**: {exit_code}\n"
                    
                    if error:
                        code_report += f"- **Error**: {error}\n"
                        
                    stdout = info.get('stdout', '').strip()
                    stderr = info.get('stderr', '').strip()
                    
                    if stdout:
                        code_report += f"\n### Stdout\n```text\n{stdout}\n```\n"
                    if stderr:
                        code_report += f"\n### Stderr\n```text\n{stderr}\n```\n"
                        
                    code_report += f"\n### Code\n```{lang_md}\n{code_content}\n```\n"
                    
                except Exception as e:
                    print(f"Error processing run info {path}: {e}")

        final_content = header + "\n\n" + content + code_report
        
        with open(target_dir / "index.md", "w", encoding="utf-8") as f:
            f.write(final_content)
            
    # 3. Generate Dashboard (index.md)
    
    # Handle Global Report
    report_source = Path("data/reports/report.html")
    report_dest = docs_dir / "report.html"
    has_report = False
    
    if report_source.exists():
        try:
            shutil.copy(report_source, report_dest)
            has_report = True
            print(f"Included global report: {report_source}")
        except Exception as e:
            print(f"Failed to copy global report: {e}")

    index_content = f"""
# Mission Control Center

Overview of all agent operations.

"""
    if has_report:
        index_content += "- [**Global Analysis Report**](report.html)\n\n"
    for run in runs:
        meta = run["meta"]
        year = meta.get("year", 0)
        day = meta.get("day", 0)
        slug = run.get("slug", meta.get("run_id"))
        agent = f"{meta.get('model')}"
        lang = meta.get('lang')
        
        p1 = "★" if meta.get("part1_solved") else "☆"
        p2 = "★" if meta.get("part2_solved") else "☆"
        solved = f"{p1}{p2}"
        
        duration = format_duration(meta.get('part12_duration', 0))
        
        link_text = f"{year} Day {day} - {run['display_model']}"
        link_url = f"{year}/day_{day:02d}/{slug}/index.md"
        
        index_content += f"- [{link_text}]({link_url}) | Lang: {lang} | Stars: {solved} | Time: {duration}\n"

    with open(docs_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index_content)
        
    # 4. Generate mkdocs.yml

    # Create javascripts directory and mathjax config
    js_dir = docs_dir / "javascripts"
    js_dir.mkdir(exist_ok=True)
    
    with open(js_dir / "mathjax.js", "w", encoding="utf-8") as f:
        f.write("""
window.MathJax = {
  tex: {
    inlineMath: [["\\\\(", "\\\\)"]],
    displayMath: [["\\\\[", "\\\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};
""")

    mkdocs_yml = f"""
site_name: {SITE_NAME}
theme:
  name: material
  palette:
    scheme: slate
    primary: indigo
    accent: cyan
  features:
    - navigation.indexes
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - attr_list
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.arithmatex:
      generic: true

extra_javascript:
  - javascripts/mathjax.js
  - https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js

plugins:
  - search
"""
    with open(OUTPUT_DIR / "mkdocs.yml", "w", encoding="utf-8") as f:
        f.write(mkdocs_yml)
        
    print(f"Site generated in: {OUTPUT_DIR.absolute()}")
    print("-" * 40)
    print("INSTRUCTIONS:")
    print("1. Ensure you have mkdocs-material installed:")
    print("   pip install mkdocs-material")
    print("2. Go to the generated site directory:")
    print(f"   cd {OUTPUT_DIR}")
    print("3. Serve the site locally:")
    print("   mkdocs serve")
    print("-" * 40)

if __name__ == "__main__":
    generate_site()
