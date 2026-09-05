"""
VisJPEG Python - Main entry point
"""

import sys
import os
import subprocess


def main():
    """Startet die VisJPEG Streamlit-App."""
    app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        app_path,
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ]
    print("=" * 50)
    print("  VisJPEG - JPEG-Kompressions-Visualisierung")
    print("=" * 50)
    print("")
    print("Starte Streamlit-App...")
    print("Oeffne deinen Browser unter: http://localhost:8501")
    print("Druecke Ctrl+C zum Beenden.")
    print("")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nVisJPEG beendet.")


if __name__ == "__main__":
    main()
