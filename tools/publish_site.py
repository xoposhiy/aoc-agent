import subprocess
import sys
from pathlib import Path

def publish():
    """
    Generates the site and deploys it to GitHub Pages using mkdocs gh-deploy.
    """
    root_dir = Path(__file__).parent.parent
    generate_script = root_dir / "tools" / "generate_site.py"
    config_file = root_dir / "report_site" / "mkdocs.yml"

    # 1. Generate the site
    print(f"Generating site using {generate_script}...")
    try:
        subprocess.run([sys.executable, str(generate_script)], cwd=root_dir, check=True)
    except subprocess.CalledProcessError:
        print("Error: Site generation failed.")
        sys.exit(1)

    if not config_file.exists():
        print(f"Error: Configuration file {config_file} not found after generation.")
        sys.exit(1)

    # 2. Deploy to gh-pages
    print("Deploying to GitHub Pages...")
    # We use --force to overwrite the remote branch if needed
    cmd = ["mkdocs", "gh-deploy", "--config-file", str(config_file), "--force"]
    
    try:
        subprocess.run(cmd, cwd=root_dir, check=True)
        print("\n? Successfully deployed to GitHub Pages!")
        print("Check your repository settings to ensure GitHub Pages is enabled for the \u0027gh-pages\u0027 branch.")
    except subprocess.CalledProcessError:
        print("\n? Error deploying site.")
        print("Ensure you have git configured and write access to the repository.")
        sys.exit(1)
    except FileNotFoundError:
        print("\n? Error: \u0027mkdocs\u0027 command not found.")
        print("Please install it: pip install mkdocs mkdocs-material")
        sys.exit(1)

if __name__ == "__main__":
    publish()

