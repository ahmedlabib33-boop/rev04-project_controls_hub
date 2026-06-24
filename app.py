"""
SAMCO Project Controls Intelligence Hub - Entry Point
Developed & Created | Engr. Ahmed Labib
"""
import subprocess
import sys
import os

def main():
    """Run the SAMCO Streamlit dashboard."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Ensure assets directory exists for logo
    assets_dir = os.path.join(script_dir, "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print("📁 Created assets/ folder — place your SAMCO logo here as 'logo.png' or 'logo.svg'")

    # Run Streamlit on port 7688
    cmd = [
        sys.executable, "-m", "streamlit", "run", "dashboard.py",
        "--server.port", "7688",
        "--server.headless", "true"
    ]

    subprocess.run(cmd)

if __name__ == "__main__":
    main()
