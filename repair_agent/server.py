"""HTTP server and JSON API built only from the Python standard library.

Endpoints
  GET  /                  static single-page interface
  GET  /api/state         current BlockWorld snapshot
  GET  /api/transcript    full episodic transcript
  POST /api/turn          {utterance, deictic_target, deictic_modality}
  POST /api/reset         start a new session
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agent import RepairAgent

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    agent = RepairAgent()  # one shared session across requests

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            if path == "/api/state":
                self._send_json(self.agent.world.snapshot())
            elif path == "/api/transcript":
                self._send_json(
                    {"transcript": self.agent.memory.transcript_as_list()})
            else:
                self._send_json({"error": "not found"}, 404)
            return

        relative = "index.html" if path == "/" else path.lstrip("/")
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR)) or not target.is_file():
            self.send_error(404)
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",
                         CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"}, 400)
            return

        if path == "/api/turn":
            self._send_json(self.agent.handle(
                payload.get("utterance", ""),
                payload.get("deictic_target"),
                payload.get("deictic_modality", "point")))
        elif path == "/api/reset":
            self.agent.reset()
            self._send_json({"reset": True, "state": self.agent.world.snapshot()})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt: str, *args) -> None:
        return  # keep the console clean


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"RepairAgent running at http://{host}:{port} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
