"""
Serveur local Digest Matin
Lance : python3 server.py
Ouvre : http://localhost:8765
Le bouton "Actualiser" de la page déclenche une nouvelle veille.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess, threading, json, os
from pathlib import Path

BASE_DIR = Path(__file__).parent
PORT     = 8765
_running = False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/refresh":
            global _running
            if not _running:
                _running = True
                threading.Thread(target=self._run_digest, daemon=True).start()
                self._json({"status": "started"})
            else:
                self._json({"status": "already_running"})

        elif self.path == "/status":
            self._json({"running": _running})

        else:
            # Sert feed.html comme page d'index
            if self.path in ("/", "/index.html"):
                self.path = "/feed.html"
            super().do_GET()

    def _run_digest(self):
        global _running
        try:
            subprocess.run(
                ["python3", str(BASE_DIR / "digest.py")],
                cwd=str(BASE_DIR),
            )
        finally:
            _running = False

    def _json(self, data: dict):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        path = args[0] if args else ""
        if any(x in path for x in ["/refresh", "/status"]):
            print(f"  {path.split()[0]}")


if __name__ == "__main__":
    print(f"\nDigest Matin — Serveur local")
    print(f"  URL  : http://localhost:{PORT}")
    print(f"  Stop : Ctrl+C\n")
    HTTPServer(("", PORT), Handler).serve_forever()
