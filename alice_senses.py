"""Instruments: browser, image header, audio container, SVG drawing.

Each one reports what it read. A missing model stays a named gap.
"""

from __future__ import annotations

import base64
import ipaddress
import json
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.request import urlopen

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
AUDIO_EXT = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}

COLORS = {
    "red": "#c0392b",
    "blue": "#2471a3",
    "green": "#1e8449",
    "black": "#1c1c1c",
    "white": "#f7f7f7",
    "gold": "#b7950b",
    "gray": "#7f8c8d",
    "grey": "#7f8c8d",
    "orange": "#d35400",
    "purple": "#6c3483",
}


def _inet_aton(name: str):
    """Browser-style IPv4: 127.1, 2130706433, and dotted quads. Leading zeros are refused by the caller."""
    parts = name.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    if any(len(part) > 1 and part.startswith("0") for part in parts):
        return "ambiguous"
    nums = [int(part) for part in parts]
    if len(nums) == 1:
        value = nums[0]
    elif len(nums) == 2 and nums[1] <= 0xFFFFFF:
        value = (nums[0] << 24) | nums[1]
    elif len(nums) == 3 and nums[1] <= 0xFF and nums[2] <= 0xFFFF:
        value = (nums[0] << 24) | (nums[1] << 16) | nums[2]
    elif len(nums) == 4 and all(num <= 0xFF for num in nums):
        value = (nums[0] << 24) | (nums[1] << 16) | (nums[2] << 8) | nums[3]
    else:
        return None
    if value > 0xFFFFFFFF:
        return None
    return ipaddress.IPv4Address(value)


def _blocked_ip(ip) -> bool:
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped
    if isinstance(ip, ipaddress.IPv4Address) and int(ip) & 0xFFC00000 == 0x64400000:
        return True
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _private_host(host: str) -> bool:
    name = host.lower().rstrip(".").strip("[]")
    if not name or name in {"localhost", "localhost.localdomain"} or name.endswith(".local") or name.endswith(".localhost"):
        return True
    try:
        return _blocked_ip(ipaddress.ip_address(name))
    except ValueError:
        parsed = _inet_aton(name)
        if parsed == "ambiguous":
            return True
        if isinstance(parsed, ipaddress.IPv4Address):
            return _blocked_ip(parsed)
    return False


def public_https(url: str) -> Optional[str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if _private_host(parsed.hostname):
        return None
    return parsed.geturl()


def _strip_html(html: str) -> tuple[str, str]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
    body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    body = re.sub(r"(?is)<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return title, body[:1500]


def browse(url: str, timeout: int = 25) -> dict:
    """Open a public page. Playwright if it is installed, otherwise system Chrome."""
    target = public_https(url)
    if not target:
        return {
            "ok": False,
            "act": "silence-gap",
            "source": "tool:browse",
            "answer": "Browse takes a public http or https URL. Private hosts are refused.",
            "next": "give a public https URL",
        }
    if shutil.which("python3") and _playwright_importable():
        return _browse_playwright(target, timeout)
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
    if not chrome:
        return {
            "ok": False,
            "act": "silence-instrument",
            "source": "tool:browse",
            "answer": "No browser instrument. Install Playwright or Chrome.",
            "next": "pip install playwright, or install google-chrome",
        }
    return _browse_chrome(chrome, target, timeout)


def _playwright_importable() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


def _browse_playwright(url: str, timeout: int) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page()

            def _allow(route):
                if public_https(route.request.url):
                    route.continue_()
                else:
                    route.abort()

            page.route("**/*", _allow)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            if not public_https(page.url):
                return _left_public_web("tool:playwright")
            title = page.title()
            text = page.inner_text("body")[:1500]
        finally:
            browser.close()
    shown = re.sub(r"\s+", " ", text).strip()
    return {
        "ok": True,
        "act": "say",
        "source": "tool:playwright",
        "answer": f"Page: {title or url}\n{shown}",
        "next": "",
    }


def _kill_process_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        proc.kill()
    try:
        proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _serve_fetch(url: str, resource_type: str, frame_id: str, state: dict) -> str:
    """Continue a public request. Abort the rest. A main-frame abort is not read."""
    action = "continue" if public_https(url) else "abort"
    if resource_type == "Document":
        main = state.get("main_frame")
        if main is None:
            state["main_frame"] = frame_id
            main = frame_id
        if frame_id == main:
            if action == "abort":
                state["document_blocked"] = True
            else:
                state["document_url"] = url
    return action


def _navigation_result(state: dict) -> str:
    if state.get("document_blocked"):
        return "silence"
    if not public_https(state.get("document_url") or ""):
        return "silence"
    return "read"


def _left_public_web(source: str) -> dict:
    return {
        "ok": False,
        "act": "silence-gap",
        "source": source,
        "answer": "The page left the public web. The body was not read.",
        "next": "give a public https URL that stays public",
    }


def _chrome_miss() -> dict:
    return {
        "ok": False,
        "act": "silence-instrument",
        "source": "tool:chrome",
        "answer": "The browser did not return a page.",
        "next": "retry the public URL, or install Playwright",
    }


class _Cdp:
    """Small Chrome DevTools client. Enough to pause a request and read the DOM."""

    def __init__(self, sock: socket.socket, leftover: bytes = b""):
        self.sock = sock
        self.buf = leftover
        self.next_id = 0

    def send(self, method: str, params: Optional[dict] = None) -> int:
        self.next_id += 1
        msg = {"id": self.next_id, "method": method}
        if params is not None:
            msg["params"] = params
        self._send_frame(0x1, json.dumps(msg).encode())
        return self.next_id

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        length = len(payload)
        header = bytearray([0x80 | opcode])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", length))
        mask = os.urandom(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def recv_json(self, deadline: float) -> Optional[dict]:
        parts: list[bytes] = []
        while True:
            frame = self._recv_frame(deadline)
            if frame is None:
                return None
            fin, opcode, payload = frame
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0x8:
                return None
            if opcode == 0x1:
                parts = [payload]
            elif opcode == 0x0 and parts:
                parts.append(payload)
            else:
                continue
            if fin:
                return json.loads(b"".join(parts).decode("utf-8"))

    def _recv_exact(self, size: int, deadline: float) -> Optional[bytes]:
        if size == 0:
            return b""
        while len(self.buf) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            self.sock.settimeout(remaining)
            try:
                chunk = self.sock.recv(max(4096, size - len(self.buf)))
            except (TimeoutError, socket.timeout):
                return None
            if not chunk:
                return None
            self.buf += chunk
        data = self.buf[:size]
        self.buf = self.buf[size:]
        return data

    def _recv_frame(self, deadline: float):
        header = self._recv_exact(2, deadline)
        if header is None:
            return None
        fin = bool(header[0] & 0x80)
        opcode = header[0] & 0x0F
        masked = bool(header[1] & 0x80)
        length = header[1] & 0x7F
        if length == 126:
            raw = self._recv_exact(2, deadline)
            if raw is None:
                return None
            length = struct.unpack(">H", raw)[0]
        elif length == 127:
            raw = self._recv_exact(8, deadline)
            if raw is None:
                return None
            length = struct.unpack(">Q", raw)[0]
        mask = b""
        if masked:
            mask = self._recv_exact(4, deadline) or b""
            if len(mask) != 4:
                return None
        payload = self._recv_exact(length, deadline)
        if payload is None:
            return None
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return fin, opcode, payload


def _ws_connect(port: int, path: str, timeout: float) -> tuple[socket.socket, bytes]:
    sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    try:
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.sendall(request.encode())
        data = b""
        deadline = time.monotonic() + timeout
        sock.settimeout(timeout)
        while b"\r\n\r\n" not in data:
            if time.monotonic() > deadline:
                raise TimeoutError("cdp handshake timed out")
            piece = sock.recv(4096)
            if not piece:
                raise ConnectionError("cdp handshake closed")
            data += piece
        header, rest = data.split(b"\r\n\r\n", 1)
        status = header.split(b"\r\n", 1)[0]
        if b" 101 " not in status:
            raise ConnectionError(status.decode("utf-8", "replace"))
        return sock, rest
    except Exception:
        sock.close()
        raise


def _page_socket_path(port: int) -> str:
    with urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as resp:
        targets = json.loads(resp.read().decode("utf-8"))
    for target in targets:
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return urlparse(target["webSocketDebuggerUrl"]).path
    raise ConnectionError("no page target")


def _devtools_port(profile: Path, proc: subprocess.Popen, timeout: int) -> Optional[int]:
    deadline = time.monotonic() + min(timeout, 10)
    port_file = profile / "DevToolsActivePort"
    while time.monotonic() < deadline:
        if port_file.is_file():
            lines = port_file.read_text(encoding="utf-8").splitlines()
            if lines and lines[0].isdigit():
                return int(lines[0])
        if proc.poll() is not None:
            return None
        time.sleep(0.05)
    return None


def _answer_fetch(cdp: _Cdp, params: dict, state: dict) -> Optional[str]:
    request = params.get("request") or {}
    action = _serve_fetch(
        request.get("url") or "",
        params.get("resourceType") or "",
        params.get("frameId") or "",
        state,
    )
    if action == "continue":
        cdp.send("Fetch.continueRequest", {"requestId": params["requestId"]})
    else:
        cdp.send(
            "Fetch.failRequest",
            {"requestId": params["requestId"], "errorReason": "Aborted"},
        )
    if state.get("document_blocked"):
        return "silence"
    return None


def _evaluate_html(cdp: _Cdp, state: dict, deadline: float) -> str:
    call_id = cdp.send(
        "Runtime.evaluate",
        {
            "expression": (
                "document.documentElement ? "
                "document.documentElement.outerHTML.slice(0, 200000) : ''"
            ),
            "returnByValue": True,
        },
    )
    while True:
        msg = cdp.recv_json(deadline)
        if msg is None:
            return ""
        if msg.get("method") == "Fetch.requestPaused":
            if _answer_fetch(cdp, msg["params"], state) == "silence":
                return ""
            continue
        if msg.get("method") == "Fetch.authRequired":
            cdp.send(
                "Fetch.failRequest",
                {"requestId": msg["params"]["requestId"], "errorReason": "Aborted"},
            )
            continue
        if msg.get("id") == call_id:
            return ((msg.get("result") or {}).get("result") or {}).get("value") or ""


def _cdp_public_html(port: int, url: str, timeout: int) -> tuple[str, str]:
    sock, leftover = _ws_connect(port, _page_socket_path(port), timeout)
    try:
        cdp = _Cdp(sock, leftover)
        deadline = time.monotonic() + timeout
        pending = {
            cdp.send("Fetch.enable", {"patterns": [{"urlPattern": "*"}]}),
            cdp.send("Page.enable"),
        }
        while pending:
            msg = cdp.recv_json(deadline)
            if msg is None:
                return "fail", ""
            if msg.get("id") in pending:
                if msg.get("error"):
                    return "fail", ""
                pending.discard(msg["id"])
        cdp.send("Page.navigate", {"url": url})
        state: dict = {}
        while time.monotonic() < deadline:
            msg = cdp.recv_json(deadline)
            if msg is None:
                break
            method = msg.get("method")
            if method == "Fetch.requestPaused":
                if _answer_fetch(cdp, msg["params"], state) == "silence":
                    return "silence", ""
                continue
            if method == "Fetch.authRequired":
                cdp.send(
                    "Fetch.failRequest",
                    {"requestId": msg["params"]["requestId"], "errorReason": "Aborted"},
                )
                continue
            if method in {"Page.domContentEventFired", "Page.loadEventFired"} and state.get("document_url"):
                if _navigation_result(state) != "read":
                    return "silence", ""
                html = _evaluate_html(cdp, state, deadline)
                if _navigation_result(state) != "read":
                    return "silence", ""
                return "read", html
        if state.get("document_blocked"):
            return "silence", ""
        return "fail", ""
    finally:
        sock.close()


def _browse_chrome(
    chrome: str,
    url: str,
    timeout: int,
    launch_args: Optional[list[str]] = None,
) -> dict:
    """Open a page in system Chrome. Abort any request that is not public, including a redirect."""
    profile = Path(tempfile.mkdtemp(prefix="alice-chrome-"))
    proc = None
    try:
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile}",
            "--remote-debugging-port=0",
            "--remote-debugging-address=127.0.0.1",
            "--remote-allow-origins=*",
            *(launch_args or []),
            "about:blank",
        ]
        proc = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        port = _devtools_port(profile, proc, timeout)
        if port is None:
            return _chrome_miss()
        status, html = _cdp_public_html(port, url, timeout)
        if status == "silence":
            return _left_public_web("tool:chrome")
        if status != "read" or "<html" not in html.lower():
            return _chrome_miss()
        title, text = _strip_html(html)
        return {
            "ok": True,
            "act": "say",
            "source": "tool:chrome",
            "answer": f"Page: {title or url}\n{text}",
            "next": "",
        }
    except (OSError, json.JSONDecodeError, TimeoutError, ValueError):
        return _chrome_miss()
    finally:
        if proc is not None and proc.poll() is None:
            _kill_process_group(proc)
        shutil.rmtree(profile, ignore_errors=True)


def image_header(path: Path) -> Optional[dict]:
    data = path.read_bytes()[:64]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return {"format": "png", "width": width, "height": height}
    if data.startswith(b"\xff\xd8"):
        # Scan the file for a SOF marker. Enough for a size, not a caption.
        blob = path.read_bytes()
        index = 2
        while index + 9 < len(blob):
            if blob[index] != 0xFF:
                break
            marker = blob[index + 1]
            if marker in {0xC0, 0xC1, 0xC2}:
                height, width = struct.unpack(">HH", blob[index + 5 : index + 9])
                return {"format": "jpeg", "width": width, "height": height}
            if index + 4 > len(blob):
                break
            size = struct.unpack(">H", blob[index + 2 : index + 4])[0]
            if size < 2:
                break
            index += 2 + size
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        width, height = struct.unpack("<HH", data[6:10])
        return {"format": "gif", "width": width, "height": height}
    return None


def see_image(path: Path) -> dict:
    if not path.is_file():
        return {
            "ok": False,
            "act": "silence-gap",
            "source": "tool:see",
            "answer": f"No image at {path}.",
            "next": "give a png, jpg, gif, or webp path",
        }
    if path.suffix.lower() not in IMAGE_EXT:
        return {
            "ok": False,
            "act": "silence-gap",
            "source": "tool:see",
            "answer": "See reads png, jpg, gif, or webp.",
            "next": "give an image path",
        }
    header = image_header(path)
    if not header:
        return {
            "ok": False,
            "act": "silence-instrument",
            "source": "tool:see",
            "answer": "The file does not have a png, jpeg, or gif header I can read.",
            "next": "export the picture as png",
        }
    tesseract = shutil.which("tesseract")
    ocr = ""
    if tesseract:
        proc = subprocess.run(
            [tesseract, str(path), "stdout"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        ocr = re.sub(r"\s+", " ", proc.stdout).strip()[:400]
    lines = [
        f"{header['format']} {header['width']}x{header['height']}",
    ]
    next_shelf = "a vision model for object names"
    if ocr:
        lines.append(f"Printed text: {ocr}")
    else:
        lines.append("No OCR instrument. Object names were not read.")
        if not tesseract:
            next_shelf = "tesseract for printed text, then a vision model for objects"
    return {
        "ok": True,
        "act": "say",
        "source": "tool:see",
        "answer": " ".join(lines),
        "next": next_shelf,
    }


def hear_audio(path: Path) -> dict:
    if not path.is_file() or path.suffix.lower() not in AUDIO_EXT:
        return {
            "ok": False,
            "act": "silence-gap",
            "source": "tool:hear",
            "answer": "Hear reads a wav, mp3, ogg, flac, or m4a file.",
            "next": "give an audio path",
        }
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {
            "ok": False,
            "act": "silence-instrument",
            "source": "tool:hear",
            "answer": "ffprobe is not installed.",
            "next": "install ffmpeg",
        }
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,sample_rate,channels",
            "-of",
            "default=noprint_wrappers=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "act": "silence-instrument",
            "source": "tool:ffprobe",
            "answer": (proc.stderr or "ffprobe failed").strip()[:300],
            "next": "confirm the file is audio",
        }
    summary = re.sub(r"\s+", " ", proc.stdout).strip()
    whisper = shutil.which("whisper")
    if whisper:
        return {
            "ok": True,
            "act": "say",
            "source": "tool:ffprobe",
            "answer": summary + " Whisper is installed; run it on this file for words.",
            "next": f"whisper {path}",
        }
    return {
        "ok": True,
        "act": "say",
        "source": "tool:ffprobe",
        "answer": summary + " No words were transcribed.",
        "next": "install whisper or whisper.cpp for the transcript",
    }


def draw_svg(prompt: str) -> str:
    lower = prompt.lower()
    color = "#1c2833"
    for name, hex_color in COLORS.items():
        if re.search(rf"\b{name}\b", lower):
            color = hex_color
            break
    label_match = re.search(r"[\"']([^\"']{1,80})[\"']", prompt)
    label = label_match.group(1) if label_match else ""
    if not label:
        word = re.search(r"\blabel\s+([a-z0-9][a-z0-9 -]{0,40})", prompt, flags=re.I)
        label = word.group(1).strip() if word else ""
    if re.search(r"\b(square|rectangle|box)\b", lower):
        shape = f'<rect x="48" y="48" width="160" height="160" rx="8" fill="{color}"/>'
    elif re.search(r"\b(line|stroke)\b", lower):
        shape = f'<line x1="32" y1="200" x2="288" y2="56" stroke="{color}" stroke-width="8"/>'
    else:
        shape = f'<circle cx="160" cy="128" r="72" fill="{color}"/>'
    text = ""
    if label:
        safe = (
            label.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        text = f'<text x="160" y="250" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#1c1c1c">{safe}</text>'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="280" viewBox="0 0 320 280">\n'
        '<rect width="320" height="280" fill="#fbfbfb"/>\n'
        f"{shape}\n{text}\n</svg>\n"
    )


def search_code(pattern: str, root: Path, timeout: int = 8) -> dict:
    rg = shutil.which("rg")
    if not rg:
        return {
            "ok": False,
            "act": "silence-instrument",
            "source": "tool:rg",
            "answer": "ripgrep is not installed.",
            "next": "install rg",
        }
    if not pattern.strip():
        return {
            "ok": False,
            "act": "silence-gap",
            "source": "tool:rg",
            "answer": "A code search needs a quoted pattern.",
            "next": 'rg "pattern"',
        }
    proc = subprocess.run(
        [rg, "-n", "--max-count", "20", "-g", "!*.jsonl", "-g", "!.git", pattern, str(root)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode not in {0, 1}:
        return {
            "ok": False,
            "act": "silence-instrument",
            "source": "tool:rg",
            "answer": (proc.stderr or "rg failed").strip()[:300],
            "next": "narrow the pattern",
        }
    lines = [line for line in proc.stdout.splitlines() if line.strip()][:20]
    if not lines:
        return {
            "ok": True,
            "act": "say",
            "source": "tool:rg",
            "answer": f"No matches for {pattern} under {root}.",
            "next": "",
        }
    return {
        "ok": True,
        "act": "say",
        "source": "tool:rg",
        "answer": "\n".join(lines),
        "next": "",
    }


def write_drawing(prompt: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    svg = draw_svg(prompt)
    dest.write_text(svg, encoding="utf-8")
    return {
        "ok": True,
        "act": "say",
        "source": "tool:draw",
        "answer": f"Wrote {dest} ({dest.stat().st_size} bytes).",
        "next": "",
        "svg": svg,
    }
