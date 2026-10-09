"""Deeper reading: orchestration stays cited, instruments run, knowledge is a shelf."""

import shutil
import struct
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alice_interpret import interpret
from alice_senses import _browse_chrome, _navigation_result, _serve_fetch, public_https
from alice_session import run_turn


def test_swarm_is_cited_and_not_a_sample():
    turn = run_turn("summon a swarm to review the lattice")
    assert turn["act"] == "cite"
    assert turn["route"] == "ORCHESTRATE"
    assert turn["frame"] == "swarm"
    assert "hydra swarm" in turn["answer"]
    assert "architect,coder,auditor" in turn["answer"]
    assert "review the lattice" in turn["answer"]
    assert any(line.startswith("authority: cited-command") for line in turn["layers"])
    assert turn["next"]


def test_agent_command_keeps_the_voice():
    turn = run_turn("run the agent to inspect the tree", personality="researcher")
    assert turn["route"] == "ORCHESTRATE"
    assert turn["answer"].startswith("hydra agent --personality researcher ")
    assert "inspect the tree" in turn["answer"]


def test_private_browse_abstains():
    turn = run_turn("browse http://127.0.0.1:7777/secret")
    assert turn["act"] == "silence-gap"
    assert turn["route"] == "ABSTAIN"
    assert "Private" in turn["answer"]
    assert public_https("http://10.1.2.3/") is None
    assert public_https("http://192.168.0.5/a") is None
    assert public_https("http://[::1]/secret") is None
    assert public_https("http://127.1/") is None
    assert public_https("http://2130706433/") is None
    assert public_https("http://100.64.0.1/") is None
    assert public_https("http://8.8.8.8/") == "http://8.8.8.8/"
    assert public_https("https://example.com/docs") == "https://example.com/docs"


def test_redirect_to_loopback_is_not_read():
    state = {}
    assert _serve_fetch("http://public.example/go", "Document", "main", state) == "continue"
    for url in ("http://127.0.0.1/secret", "http://127.1/", "http://[::1]/secret", "http://2130706433/"):
        assert _serve_fetch(url, "Document", "main", state) == "abort"
    assert _navigation_result(state) == "silence"


def test_private_subresource_does_not_hide_a_public_page():
    state = {}
    assert _serve_fetch("https://example.com/", "Document", "main", state) == "continue"
    assert _serve_fetch("http://10.1.2.3/pixel.gif", "Image", "child", state) == "abort"
    assert _serve_fetch("http://127.0.0.1/", "Document", "child", state) == "abort"
    assert _navigation_result(state) == "read"


def _chrome_bin() -> str:
    return (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or ""
    )


def _page_server():
    body = b"<html><head><title>Public Page</title></head><body>hello alice</body></html>"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/go"):
                port = self.server.server_address[1]
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{port}/secret")
                self.end_headers()
                return
            payload = b"<html><title>secret</title><body>PRIVATE-BODY-TOKEN</body></html>"
            if self.path.startswith("/page"):
                payload = body
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_chrome_reads_a_public_page_and_drops_a_private_redirect():
    chrome = _chrome_bin()
    if not chrome:
        pytest.skip("chrome is not installed")
    server = _page_server()
    port = server.server_address[1]
    rules = ["--host-resolver-rules=MAP public.example 127.0.0.1"]
    try:
        page = _browse_chrome(chrome, f"http://public.example:{port}/page", 20, rules)
        secret = _browse_chrome(chrome, f"http://public.example:{port}/go", 20, rules)
    finally:
        server.shutdown()
        server.server_close()
    assert page["ok"] is True
    assert page["act"] == "say"
    assert "Public Page" in page["answer"]
    assert "hello alice" in page["answer"]
    assert secret["ok"] is False
    assert secret["act"] == "silence-gap"
    assert "left the public web" in secret["answer"]
    assert "PRIVATE-BODY-TOKEN" not in secret["answer"]


def test_public_browse_command_is_playwright():
    reading = interpret("look at https://example.com/docs")
    assert reading.frame == "browse"
    assert reading.command == "playwright open https://example.com/docs"
    assert reading.authority == "instrument"


def test_whisper_card_for_a_library_question():
    turn = run_turn("what library transcribes speech")
    assert turn["act"] == "cite"
    assert turn["source"] == "oss:whisper"
    assert "ffprobe" in turn["answer"]
    assert turn["frame"] == "procedure"


def test_draw_writes_a_red_circle(tmp_path: Path):
    turn = run_turn("draw a red circle", drawing_dir=tmp_path)
    assert turn["act"] == "say"
    assert turn["route"] == "SENSE"
    assert "<circle" in turn["answer"]
    assert "#c0392b" in turn["answer"]
    written = (tmp_path / "drawing.svg").read_text(encoding="utf-8")
    assert "<circle" in written


def test_see_reads_a_png_header(tmp_path: Path):
    image = tmp_path / "dot.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 1, 1))
    turn = run_turn(f"look at {image}")
    assert turn["route"] == "SENSE"
    assert "png 1x1" in turn["answer"]
    assert "Object names were not read" in turn["answer"]


def test_hear_reports_the_container(tmp_path: Path):
    audio = tmp_path / "tone.wav"
    with wave.open(str(audio), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00" * 800)
    turn = run_turn(f"listen to {audio}")
    assert turn["route"] == "SENSE"
    assert "codec_name=pcm_s16le" in turn["answer"] or "pcm_s16le" in turn["answer"]
    assert "No words were transcribed" in turn["answer"]


def test_code_search_reads_the_tree(tmp_path: Path):
    (tmp_path / "note.py").write_text("TOKEN_ALICE_MIND = 1\n", encoding="utf-8")
    turn = run_turn('search the code for "TOKEN_ALICE_MIND"', workspace=tmp_path)
    assert turn["route"] == "SENSE"
    assert "TOKEN_ALICE_MIND" in turn["answer"]
    assert "note.py" in turn["answer"]


def test_math_and_stacks_still_outrank_the_new_shelves():
    math_turn = run_turn("simplify 3/4 + 1/6")
    assert math_turn["route"] == "COMPUTE"
    assert "11/12" in math_turn["answer"]
    fact = run_turn("what is the speed of light in vacuum")
    assert fact["source"].startswith("stack:")
    how = run_turn("how do I use the stacks")
    assert how["source"] == "feature:stacks"
    gap = run_turn("who won the 1998 world series")
    assert gap["act"] == "silence-gap"
    assert gap["layers"]


def test_house_stack_card():
    turn = run_turn("what is vercel")
    assert turn["source"] == "house:vercel"
    assert "easylm.app" in turn["answer"]
