"""HTTP server for the GeoHazard News Locator dashboard."""

import argparse
import json
import sqlite3
import sys
import traceback
import webbrowser
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from dashboard.repository import (
    DEFAULT_DB_PATH,
    DashboardDataError,
    build_dashboard,
    build_event_detail,
    connect,
    parse_filters,
    parse_search_filters,
    search_news,
)

DASHBOARD_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = DASHBOARD_DIR / "templates"
STATIC_DIR = DASHBOARD_DIR / "static"

CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".ico": "image/x-icon",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
}


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "GeoHazardDashboard/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_file(TEMPLATE_DIR / "index.html")
            return
        if parsed.path.startswith("/static/"):
            self._serve_static(parsed.path)
            return
        if parsed.path == "/api/dashboard":
            self._serve_dashboard(parsed.query)
            return
        if parsed.path == "/api/search":
            self._serve_search(parsed.query)
            return
        if parsed.path.startswith("/api/events/"):
            self._serve_event_api(parsed.path)
            return
        if parsed.path.startswith("/event/"):
            self._serve_event_page(parsed.path)
            return
        if parsed.path == "/api/health":
            self._serve_health()
            return
        self._send_json(404, {"error": "Halaman tidak ditemukan"})

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_file(TEMPLATE_DIR / "index.html", head_only=True)
            return
        if parsed.path.startswith("/static/"):
            self._serve_static(parsed.path, head_only=True)
            return
        if parsed.path.startswith("/event/"):
            self._serve_event_page(parsed.path, head_only=True)
            return
        self._send_json(404, {"error": "Halaman tidak ditemukan"}, head_only=True)

    def _serve_static(self, request_path, head_only=False):
        relative = unquote(request_path[len("/static/") :])
        candidate = (STATIC_DIR / relative).resolve()
        static_root = STATIC_DIR.resolve()
        if (
            not candidate.is_file()
            or static_root not in candidate.parents
        ):
            self._send_json(404, {"error": "Aset tidak ditemukan"}, head_only=head_only)
            return
        self._serve_file(candidate, head_only=head_only)

    def _serve_file(self, path, head_only=False):
        try:
            content = path.read_bytes()
        except OSError:
            self._send_json(404, {"error": "File tidak ditemukan"}, head_only=head_only)
            return
        content_type = CONTENT_TYPES.get(
            path.suffix.lower(),
            "application/octet-stream",
        )
        self._send_bytes(
            200,
            content,
            content_type,
            head_only=head_only,
            cache_control="no-cache",
        )

    def _serve_dashboard(self, query):
        try:
            params = {
                key: values[-1]
                for key, values in parse_qs(query, keep_blank_values=True).items()
            }
            filters = parse_filters(params)
            data = build_dashboard(self.server.db_path, filters)
            self._send_json(200, data)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except DashboardDataError as exc:
            self._send_json(500, {"error": str(exc)})
        except Exception:
            traceback.print_exc()
            self._send_json(500, {"error": "Terjadi kesalahan internal dashboard"})

    def _serve_search(self, query):
        try:
            params = {
                key: values[-1]
                for key, values in parse_qs(query, keep_blank_values=True).items()
            }
            filters = parse_search_filters(params)
            data = search_news(self.server.db_path, filters)
            self._send_json(200, data)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except DashboardDataError as exc:
            self._send_json(500, {"error": str(exc)})
        except Exception:
            traceback.print_exc()
            self._send_json(500, {"error": "Terjadi kesalahan internal pencarian"})

    def _serve_event_api(self, request_path):
        event_id = unquote(request_path[len("/api/events/") :])
        if not event_id or "/" in event_id:
            self._send_json(404, {"error": "Kejadian tidak ditemukan"})
            return
        try:
            data = build_event_detail(self.server.db_path, event_id)
            if data is None:
                self._send_json(404, {"error": "Kejadian tidak ditemukan"})
                return
            self._send_json(200, data)
        except DashboardDataError as exc:
            self._send_json(500, {"error": str(exc)})
        except Exception:
            traceback.print_exc()
            self._send_json(500, {"error": "Terjadi kesalahan internal detail"})

    def _serve_event_page(self, request_path, head_only=False):
        event_id = unquote(request_path[len("/event/") :])
        if not event_id or "/" in event_id:
            self._send_json(
                404,
                {"error": "Kejadian tidak ditemukan"},
                head_only=head_only,
            )
            return
        self._serve_file(TEMPLATE_DIR / "event.html", head_only=head_only)

    def _serve_health(self):
        try:
            with closing(connect(self.server.db_path)) as connection:
                connection.execute("SELECT 1").fetchone()
        except (DashboardDataError, sqlite3.Error) as exc:
            self._send_json(503, {"status": "error", "error": str(exc)})
            return
        self._send_json(
            200,
            {
                "status": "ok",
                "database": str(Path(self.server.db_path or DEFAULT_DB_PATH)),
            },
        )

    def _send_json(self, status, payload, head_only=False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(
            status,
            body,
            "application/json; charset=utf-8",
            head_only=head_only,
            cache_control="no-store",
        )

    def _send_bytes(
        self,
        status,
        body,
        content_type,
        head_only=False,
        cache_control="no-cache",
    ):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def log_message(self, format, *args):
        sys.stderr.write(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), format % args)
        )


def create_server(host="127.0.0.1", port=8000, db_path=None):
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    server.db_path = str(db_path or DEFAULT_DB_PATH)
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Jalankan dashboard GeoHazard News Locator."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port, args.db)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"GeoHazard News Locator dashboard: {url}")
    print(f"Database: {Path(args.db).resolve()}")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard dihentikan.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
