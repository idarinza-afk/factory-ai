import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from improvise import web


class FakeAgent:
    def __init__(self, session):
        self.session = session

    def ask(self, text):
        self.session._on_tool("takt_from_rate", {"rate_per_hour": 8000}, {"takt_s": 0.45})
        allowed = self.session.confirm("run_python", {"path": "x.py"})
        return f"answer to {text}; allowed={allowed}"


@pytest.fixture()
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPROVISE_HOME", str(tmp_path))
    from improvise.config import load
    cfg = load()
    cfg.ensure_dirs()
    (cfg.output_dir / "line.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("no", encoding="utf-8")
    s = web.Session(cfg)
    s.agent = FakeAgent(s)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(s, "tok", {"output": cfg.output_dir}))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", s
    httpd.shutdown()


def call(base, path, body=None, token="tok", host=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"X-Improvise-Token": token, "Content-Type": "application/json"})
    if host:
        req.add_header("Host", host)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read()


def test_page_has_token_and_api_needs_it(server):
    base, _ = server
    status, page = call(base, "/")
    assert status == 200 and b'"tok"' in page
    with pytest.raises(urllib.error.HTTPError) as e:
        call(base, "/api/files", token="wrong")
    assert e.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as e:  # DNS-rebinding style host
        call(base, "/", host="evil.example")
    assert e.value.code == 403


def test_files_served_only_inside_output(server):
    base, _ = server
    files = json.loads(call(base, "/api/files")[1])
    assert files[0]["name"] == "line.svg"
    assert call(base, "/files/output/line.svg?token=tok")[0] == 200
    with pytest.raises(urllib.error.HTTPError) as e:
        call(base, "/files/output/..%2Fsecret.txt?token=tok")
    assert e.value.code == 404


def test_ask_shows_tools_and_waits_for_approval(server):
    base, s = server
    job = json.loads(call(base, "/api/ask", {"text": "hi"})[1])["job"]
    for _ in range(50):
        j = json.loads(call(base, f"/api/job/{job}")[1])
        confirms = [e for e in j["events"] if e["kind"] == "confirm"]
        if confirms:
            break
        time.sleep(0.05)
    assert j["events"][0]["name"] == "takt_from_rate"
    assert call(base, "/api/confirm", {"id": confirms[0]["id"], "allow": True})[0] == 200
    for _ in range(50):
        j = json.loads(call(base, f"/api/job/{job}")[1])
        if j["done"]:
            break
        time.sleep(0.05)
    assert j["answer"] == "answer to hi; allowed=True"


def test_rules_from_the_screen(server):
    base, _ = server
    rid = json.loads(call(base, "/api/rules", {"topic": "prices", "rule": "never estimate prices"})[1])["id"]
    rules = json.loads(call(base, "/api/rules")[1])
    assert any(r["id"] == rid for r in rules)
    assert json.loads(call(base, "/api/rules/delete", {"id": rid})[1])["ok"]
