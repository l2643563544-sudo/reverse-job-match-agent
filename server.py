import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
sys.path.insert(0, str(ROOT / "src"))

from reverse_job_match.collector_adapter import CollectorUnavailableError
from reverse_job_match.pipeline import run_pipeline


class AppHandler(BaseHTTPRequestHandler):
    server_version = "ReverseJobMatch/0.1"

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {"ok": True, "service": "reverse-job-match"})
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/run":
            self._send_json(404, {"ok": False, "error": "not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "error": "invalid JSON"})
            return

        mode = payload.get("mode", "demo")
        if mode not in {"demo", "live"}:
            self._send_json(400, {"ok": False, "error": "mode must be demo or live"})
            return

        resume = str(payload.get("resume", "")).strip()
        direction = str(payload.get("direction", "")).strip()
        reference_jd = str(payload.get("jd", "")).strip()
        if not resume or not direction or not reference_jd:
            self._send_json(
                400,
                {
                    "ok": False,
                    "error": "简历、目标方向和参考 JD 不能为空",
                },
            )
            return

        resume_path = ROOT / "data" / "web_resume.md"
        direction_path = ROOT / "data" / "web_direction.txt"
        jd_path = ROOT / "data" / "web_reference_jd.md"
        resume_path.write_text(resume, encoding="utf-8")
        direction_path.write_text(direction, encoding="utf-8")
        jd_path.write_text(reference_jd, encoding="utf-8")

        try:
            result = run_pipeline(
                mode=mode,
                resume_path=resume_path,
                direction_path=direction_path,
                reference_jd_path=jd_path,
                output_path=ROOT / "output" / "recommendations.md",
                project_root=ROOT,
                min_score=float(payload.get("min_score", 55)),
                top_n=int(payload.get("top", 5)),
            )
        except CollectorUnavailableError as exc:
            self._send_json(409, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        self._send_json(
            200,
            {
                "ok": True,
                "source_label": "live" if mode == "live" else "fixture-demo",
                "target_role": result.profile.target.target_role,
                "cities": result.profile.target.cities,
                "count": len(result.scored_jobs),
                "jobs": [item.to_dict() for item in result.scored_jobs],
                "report_path": str(result.report_path),
            },
        )

    def _serve_static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"

        candidate = (STATIC_DIR / path.lstrip("/")).resolve()
        if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
            self._send_json(403, {"ok": False, "error": "forbidden"})
            return

        if not candidate.exists() or not candidate.is_file():
            self._send_json(404, {"ok": False, "error": "not found"})
            return

        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type += "; charset=utf-8"

        body = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> int:
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Reverse job matching demo: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
