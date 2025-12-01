import os
import json
import shutil
from pathlib import Path
import glob
import re

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
DATA_DIRS_PATTERN = "data*" 
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
        
        # Search for metadata.json one level deep
        # Assuming structure: data_dir/run_id/metadata.json
        for meta_file in base_path.glob("*/metadata.json"):
            run_dir = meta_file.parent
            report_file = run_dir / "final_report.md"
            
            if report_file.exists():
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

    # 2. Generate pages
    for run in runs:
        meta = run["meta"]
        year = meta.get("year", "Unknown")
        day = meta.get("day", "Unknown")
        run_id = meta.get("run_id", "unknown_run")
        
        # Create target directory
        # Structure: docs/YYYY/day_DD/run_ID/
        target_dir = docs_dir / str(year) / f"day_{day:02d}" / run_id
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
# {meta.get('year')} Day {meta.get('day')} - {meta.get('lang')}

-   :robot: **Agent**: {meta.get('agent_name')} ({meta.get('model')})
-   :flag_ru: **Language**: {meta.get('lang')}
-   :stopwatch: **Duration**: {format_duration(meta.get('part12_duration', 0))}
-   :star: **Stars**: P1: {p1_solved} | P2: {p2_solved}

"""     
        final_content = header + "\n\n" + content
        
        with open(target_dir / "index.md", "w", encoding="utf-8") as f:
            f.write(final_content)
            
    # 3. Generate Dashboard (index.md)
    index_content = f"""
# Mission Control Center

Overview of all agent operations.

"""
    for run in runs:
        meta = run["meta"]
        year = meta.get("year", 0)
        day = meta.get("day", 0)
        run_id = meta.get("run_id", "")
        agent = f"{meta.get('model')}"
        lang = meta.get('lang')
        
        p1 = "★" if meta.get("part1_solved") else "☆"
        p2 = "★" if meta.get("part2_solved") else "☆"
        solved = f"{p1}{p2}"
        
        duration = format_duration(meta.get('part12_duration', 0))
        
        link_text = f"{year} Day {day} - {agent}"
        link_url = f"{year}/day_{day:02d}/{run_id}/"
        
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
      emoji_index: !!python/name:materialx.emoji.twemoji
      emoji_generator: !!python/name:materialx.emoji.to_svg
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
