"""
VisJPEG Python - Main entry point
"""

import sys
import os
import subprocess
import socket
import threading
import webbrowser


def _find_free_port(start=8501):
    """Findet den naechsten freien Port ab start."""
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    return start


def _open_browser(port):
    """Oeffnet den Browser nach kurzer Verzoegerung."""
    import time
    time.sleep(2)
    webbrowser.open(f"http://localhost:{port}")


def main():
    """Startet die VisJPEG Streamlit-App."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        print("FEHLER: Streamlit ist nicht installiert.")
        print("Installiere es mit:  pip install -e .")
        print("Oder manuell:        pip install streamlit Pillow numpy")
        sys.exit(1)

    app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")

    # Pruefe ob --server.port in den Argumenten steht
    user_args = sys.argv[1:]
    has_port_arg = any(
        arg == "--server.port" or arg.startswith("--server.port=")
        for arg in user_args
    )

    if not has_port_arg:
        port = _find_free_port(8501)
    else:
        # Port aus Argumenten extrahieren
        port = 8501
        for i, arg in enumerate(user_args):
            if arg == "--server.port" and i + 1 < len(user_args):
                port = int(user_args[i + 1])
            elif arg.startswith("--server.port="):
                port = int(arg.split("=")[1])

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        app_path,
        "--server.headless", "true",
        "--server.port", str(port),
        "--browser.gatherUsageStats", "false",
        *user_args,
    ]

    print("=" * 50)
    print("  VisJPEG - JPEG-Kompressions-Visualisierung")
    print("=" * 50)
    print("")
    print("Starte Streamlit-App...")
    print(f"Oeffne deinen Browser unter: http://localhost:{port}")
    print("Druecke Ctrl+C zum Beenden.")
    print("")

    # Browser oeffnen (im Hintergrund)
    threading.Thread(target=_open_browser, args=(port,), daemon=True).start()

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nVisJPEG beendet.")


if __name__ == "__main__":
    main()
