#!/usr/bin/env python3
import base64
import hashlib
import html
import json
import os
import re
import traceback
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("VLM_HOST", "0.0.0.0")
PORT = int(os.environ.get("VLM_PORT", "8091"))

APP_ROOT = os.environ.get("APP_ROOT", "/app")
RAW_ROOT = os.environ.get("RAW_ROOT", "/raw")
DATA_ROOT = os.environ.get("DATA_ROOT", "/data")
RUNTIME_ROOT = os.environ.get("RUNTIME_ROOT", "/runtime")
LOG_ROOT = os.environ.get("LOG_ROOT", "/logs")
WORK_ROOT = os.environ.get("WORK_ROOT", "/work")
TMP_ROOT = os.environ.get("TMP_ROOT", "/tmp")
CACHE_ROOT = os.environ.get("CACHE_ROOT", "/cache")
CONFIG_ROOT = os.environ.get("CONFIG_ROOT", "/config")
DB_PATH = os.environ.get("DB_PATH", f"{RUNTIME_ROOT}/pipeline.db")

VLM_BACKEND = os.environ.get("VLM_BACKEND", "ollama")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://astromanager-ollama:11434")
TEXT_MODEL = os.environ.get("TEXT_MODEL", os.environ.get("VLM_MODEL", "qwen2.5-coder:7b"))
CODE_MODEL = os.environ.get("CODE_MODEL", os.environ.get("VLM_MODEL", "qwen2.5-coder:7b"))
VISION_MODEL = os.environ.get("VISION_MODEL", os.environ.get("VLM_VISION_MODEL", "llava:7b"))
VLM_TIMEOUT = int(os.environ.get("VLM_TIMEOUT", "300"))
VLM_MAX_FILE_READ = int(os.environ.get("VLM_MAX_FILE_READ", "60000"))
VLM_MAX_EXAMPLES = int(os.environ.get("VLM_MAX_EXAMPLES", "5"))
VLM_WEB_TIMEOUT = int(os.environ.get("VLM_WEB_TIMEOUT", "45"))
VLM_MAX_FETCH_CHARS = int(os.environ.get("VLM_MAX_FETCH_CHARS", "120000"))
VLM_MAX_KNOWLEDGE_RESULTS = int(os.environ.get("VLM_MAX_KNOWLEDGE_RESULTS", "5"))

TRAIN_ROOT = os.environ.get("VLM_TRAIN_ROOT", f"{RUNTIME_ROOT}/vlm")
TRAIN_EXAMPLES_FILE = os.path.join(TRAIN_ROOT, "training_examples.jsonl")
KNOWLEDGE_FILE = os.path.join(TRAIN_ROOT, "knowledge_docs.jsonl")

ALLOWED_ROOTS = [
    APP_ROOT,
    RAW_ROOT,
    DATA_ROOT,
    RUNTIME_ROOT,
    LOG_ROOT,
    WORK_ROOT,
    TMP_ROOT,
    CACHE_ROOT,
    CONFIG_ROOT,
]

os.makedirs(TRAIN_ROOT, exist_ok=True)


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def json_bytes(data) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def norm_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_/-]{2,}", (text or "").lower()))


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()


def is_allowed_path(path_str: str) -> bool:
    try:
        p = Path(path_str).resolve()
    except Exception:
        return False
    for root in ALLOWED_ROOTS:
        try:
            if str(p).startswith(str(Path(root).resolve())):
                return True
        except Exception:
            continue
    return False
def read_text_file(path_str: str) -> dict:
    if not path_str:
        return {"ok": False, "error": "empty path"}
    if not is_allowed_path(path_str):
        return {"ok": False, "error": "path not allowed", "path": path_str}

    p = Path(path_str)
    if not p.exists():
        return {"ok": False, "error": "file not found", "path": path_str}
    if not p.is_file():
        return {"ok": False, "error": "not a file", "path": path_str}

    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"ok": False, "error": f"read failed: {exc}", "path": path_str}

    if len(text) > VLM_MAX_FILE_READ:
        text = text[:VLM_MAX_FILE_READ]

    return {
        "ok": True,
        "path": str(p),
        "size_chars": len(text),
        "content": text,
    }


def read_binary_b64(path_str: str) -> dict:
    if not path_str:
        return {"ok": False, "error": "empty path"}
    if not is_allowed_path(path_str):
        return {"ok": False, "error": "path not allowed", "path": path_str}

    p = Path(path_str)
    if not p.exists():
        return {"ok": False, "error": "file not found", "path": path_str}
    if not p.is_file():
        return {"ok": False, "error": "not a file", "path": path_str}

    try:
        raw = p.read_bytes()
    except Exception as exc:
        return {"ok": False, "error": f"read failed: {exc}", "path": path_str}

    return {
        "ok": True,
        "path": str(p),
        "size_bytes": len(raw),
        "content_b64": base64.b64encode(raw).decode("ascii"),
    }


def load_jsonl(path: str) -> list[dict]:
    items = []
    if not os.path.exists(path):
        return items
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def rewrite_jsonl(path: str, items: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def append_jsonl(path: str, item: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def load_examples() -> list[dict]:
    return load_jsonl(TRAIN_EXAMPLES_FILE)


def save_example(item: dict) -> dict:
    item = {
        "time": utc_now(),
        "mode": norm_text(item.get("mode", "")) or "general",
        "task": norm_text(item.get("task", "")),
        "input": item.get("input", ""),
        "output": item.get("output", ""),
        "tags": item.get("tags", []),
        "notes": item.get("notes", ""),
    }
    append_jsonl(TRAIN_EXAMPLES_FILE, item)
    return item
def find_relevant_examples(mode: str, text: str, max_items: int = VLM_MAX_EXAMPLES) -> list[dict]:
    mode = norm_text(mode).lower()
    wanted = tokenize(text)
    results = []

    for item in load_examples():
        item_mode = norm_text(item.get("mode", "")).lower()
        if mode and item_mode not in {"", "general", mode}:
            continue

        hay = " ".join([
            str(item.get("task", "")),
            str(item.get("input", "")),
            str(item.get("output", "")),
            " ".join(item.get("tags", []) if isinstance(item.get("tags", []), list) else []),
            str(item.get("notes", "")),
        ])
        score = len(wanted & tokenize(hay))
        if score > 0:
            results.append((score, item))

    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results[:max_items]]


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "noscript", "svg"}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "title":
            self._in_title = True
        if tag in self._skip_tags:
            self._skip_depth += 1
            return
        if tag in {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3", "h4", "pre", "code"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in self._skip_tags:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "pre", "code"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        data = html.unescape(data)
        if self._in_title:
            self.title += data
        self.parts.append(data)


def clean_extracted_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def fetch_url(url: str) -> dict:
    if not isinstance(url, str) or not url.lower().startswith(("http://", "https://")):
        return {"ok": False, "error": "only http/https allowed", "url": url}

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AstroManagerVLM/0.3",
            "Accept": "text/html, text/plain, application/json, text/markdown, */*",
        },
    )

    with urllib.request.urlopen(req, timeout=VLM_WEB_TIMEOUT) as resp:
        raw = resp.read(VLM_MAX_FETCH_CHARS + 1)
        content_type = (resp.headers.get("Content-Type") or "").lower()
        final_url = resp.geturl()

    truncated = len(raw) > VLM_MAX_FETCH_CHARS
    if truncated:
        raw = raw[:VLM_MAX_FETCH_CHARS]

    text = raw.decode("utf-8", errors="replace")
    title = ""

    if "html" in content_type:
        parser = TextExtractor()
        parser.feed(text)
        title = norm_text(parser.title)
        text = clean_extracted_text("".join(parser.parts))
    else:
        text = clean_extracted_text(text)

    return {
        "ok": True,
        "url": final_url,
        "content_type": content_type,
        "title": title,
        "text": text,
        "size_chars": len(text),
        "truncated": truncated,
    }
def load_knowledge_docs() -> list[dict]:
    return load_jsonl(KNOWLEDGE_FILE)


def save_knowledge_doc(item: dict) -> dict:
    docs = load_knowledge_docs()
    item_hash = item["hash"]

    replaced = False
    for i, doc in enumerate(docs):
        if doc.get("hash") == item_hash or (item.get("url") and doc.get("url") == item.get("url")):
            docs[i] = item
            replaced = True
            break

    if not replaced:
        docs.append(item)

    rewrite_jsonl(KNOWLEDGE_FILE, docs)
    return item


def ingest_url(url: str, tags: list | None = None, notes: str = "") -> dict:
    fetched = fetch_url(url)
    if not fetched.get("ok"):
        return fetched

    text = fetched["text"]
    title = fetched.get("title") or url
    item = {
        "time": utc_now(),
        "source": "web",
        "url": fetched["url"],
        "title": title,
        "content_type": fetched.get("content_type", ""),
        "text": text,
        "size_chars": len(text),
        "hash": sha256_text(text),
        "tokens": sorted(list(tokenize(f"{title}\n{text}")))[:5000],
        "tags": tags or [],
        "notes": notes or "",
    }
    save_knowledge_doc(item)
    return {
        "ok": True,
        "ingested": {
            "url": item["url"],
            "title": item["title"],
            "size_chars": item["size_chars"],
            "hash": item["hash"],
            "tags": item["tags"],
        },
    }


def search_knowledge(query: str, limit: int = VLM_MAX_KNOWLEDGE_RESULTS) -> list[dict]:
    wanted = tokenize(query)
    results = []

    for doc in load_knowledge_docs():
        hay = " ".join([
            doc.get("title", ""),
            doc.get("text", ""),
            " ".join(doc.get("tags", []) if isinstance(doc.get("tags", []), list) else []),
            doc.get("notes", ""),
            doc.get("url", ""),
        ])
        score = len(wanted & tokenize(hay))
        if score > 0:
            results.append((score, doc))

    results.sort(key=lambda x: x[0], reverse=True)

    out = []
    for score, doc in results[:limit]:
        out.append({
            "score": score,
            "title": doc.get("title", ""),
            "url": doc.get("url", ""),
            "tags": doc.get("tags", []),
            "notes": doc.get("notes", ""),
            "size_chars": doc.get("size_chars", 0),
            "snippet": (doc.get("text", "")[:3000]).strip(),
            "hash": doc.get("hash", ""),
        })
    return out
def build_system_prompt(mode: str) -> str:
    base = [
        "Du bist AstroManager VLM.",
        "Arbeite präzise, knapp und technisch sauber.",
        "Nutze Projektkontext und Wissensquellen gezielt.",
        "Wenn Informationen fehlen, sage es klar.",
        "Wenn Knowledge-Treffer mitgegeben werden, priorisiere diese als Referenz.",
    ]
    if mode == "code":
        base.append("Fokus: Codeanalyse, Refactoring, Fehlerursachen, robuste Lösungen.")
    elif mode == "image":
        base.append("Fokus: Bildanalyse und technische Qualitätsbewertung.")
    else:
        base.append("Fokus: technische Assistenz, Textanalyse und Dokumentation.")
    return "\n".join(base)


def build_messages(mode: str, prompt: str, input_text: str, input_code: str, context_items: list, examples: list, knowledge_items: list) -> list:
    user_parts = []
    if prompt:
        user_parts.append(f"AUFGABE:\n{prompt}")
    if input_text:
        user_parts.append(f"TEXT:\n{input_text}")
    if input_code:
        user_parts.append(f"CODE:\n{input_code}")

    if context_items:
        ctx_parts = []
        for item in context_items:
            if item.get("ok"):
                ctx_parts.append(f"DATEI: {item['path']}\n{item['content']}")
        if ctx_parts:
            user_parts.append("KONTEXTDATEIEN:\n" + "\n\n".join(ctx_parts))

    if knowledge_items:
        k_parts = []
        for item in knowledge_items:
            k_parts.append(
                f"TITEL: {item.get('title','')}\n"
                f"URL: {item.get('url','')}\n"
                f"SNIPPET:\n{item.get('snippet','')}"
            )
        user_parts.append("WISSENSBASIS:\n" + "\n\n".join(k_parts))

    if examples:
        ex_parts = []
        for ex in examples:
            ex_parts.append(
                f"BEISPIEL mode={ex.get('mode','')}\n"
                f"task={ex.get('task','')}\n"
                f"input={ex.get('input','')}\n"
                f"output={ex.get('output','')}\n"
            )
        user_parts.append("GELERNTE BEISPIELE:\n" + "\n".join(ex_parts))

    return [
        {"role": "system", "content": build_system_prompt(mode)},
        {"role": "user", "content": "\n\n".join(user_parts).strip()},
    ]


def http_post_json(url: str, payload: dict, timeout: int) -> dict:
    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def ollama_chat(model: str, messages: list, image_b64: str | None = None) -> dict:
    payload_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    if image_b64:
        payload_messages[-1]["images"] = [image_b64]
    payload = {"model": model, "messages": payload_messages, "stream": False}
    data = http_post_json(f"{OLLAMA_BASE_URL}/api/chat", payload, VLM_TIMEOUT)
    content = (((data or {}).get("message") or {}).get("content") or "").strip()
    return {"backend": "ollama", "model": model, "raw": data, "content": content}
def summarize_text(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"summary": "", "length": 0}
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return {
        "summary": "\n".join(lines[:12]),
        "length": len(text),
        "line_count": len(lines),
    }


def analyze_code_meta(text: str) -> dict:
    lines = text.splitlines()
    hints = []
    if "TODO" in text:
        hints.append("Enthält TODO-Kommentare.")
    if "except Exception" in text:
        hints.append("Verwendet generisches except Exception.")
    if "sqlite3" in text:
        hints.append("Arbeitet mit SQLite.")
    if "subprocess" in text:
        hints.append("Verwendet subprocess.")
    return {
        "line_count": len(lines),
        "char_count": len(text),
        "hints": hints,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "AstroManagerVLM/0.3"

    def log_message(self, fmt, *args):
        return

    def _send_json(self, status: int, data: dict):
        body = json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8", errors="replace"))

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "ok": True,
                "service": "astromanager-vlm",
                "backend": VLM_BACKEND,
                "text_model": TEXT_MODEL,
                "code_model": CODE_MODEL,
                "vision_model": VISION_MODEL,
                "time": utc_now(),
                "paths": {
                    "app": APP_ROOT,
                    "raw": RAW_ROOT,
                    "data": DATA_ROOT,
                    "runtime": RUNTIME_ROOT,
                    "logs": LOG_ROOT,
                    "work": WORK_ROOT,
                    "tmp": TMP_ROOT,
                    "cache": CACHE_ROOT,
                    "config": CONFIG_ROOT,
                    "db": DB_PATH,
                    "train_root": TRAIN_ROOT,
                    "knowledge_file": KNOWLEDGE_FILE,
                },
                "knowledge_count": len(load_knowledge_docs()),
            })
            return

        if self.path == "/api/train/list":
            self._send_json(200, {
                "ok": True,
                "count": len(load_examples()),
                "items": load_examples()[-50:],
            })
            return

        if self.path == "/api/knowledge/list":
            docs = load_knowledge_docs()
            self._send_json(200, {
                "ok": True,
                "count": len(docs),
                "items": [
                    {
                        "time": d.get("time", ""),
                        "title": d.get("title", ""),
                        "url": d.get("url", ""),
                        "tags": d.get("tags", []),
                        "size_chars": d.get("size_chars", 0),
                        "hash": d.get("hash", ""),
                    }
                    for d in docs[-100:]
                ],
            })
            return

        self._send_json(404, {"ok": False, "error": "not found", "path": self.path})
    def do_POST(self):
        try:
            payload = self._read_json()

            if self.path == "/api/train/example":
                saved = save_example(payload)
                self._send_json(200, {"ok": True, "saved": saved})
                return

            if self.path == "/api/web/fetch":
                result = fetch_url(payload.get("url", ""))
                self._send_json(200 if result.get("ok") else 400, result)
                return

            if self.path == "/api/web/ingest":
                result = ingest_url(
                    payload.get("url", ""),
                    tags=payload.get("tags", []),
                    notes=payload.get("notes", ""),
                )
                self._send_json(200 if result.get("ok") else 400, result)
                return

            if self.path == "/api/knowledge/search":
                query = payload.get("query", "")
                limit = int(payload.get("limit", VLM_MAX_KNOWLEDGE_RESULTS))
                self._send_json(200, {
                    "ok": True,
                    "query": query,
                    "results": search_knowledge(query, limit=limit),
                })
                return

            prompt = payload.get("prompt", "")
            input_text = payload.get("input_text", "")
            input_code = payload.get("input_code", "")
            image_path = payload.get("image_path", "")
            context_paths = payload.get("context_paths", [])
            use_knowledge = bool(payload.get("use_knowledge", False))
            knowledge_query = payload.get("knowledge_query", "") or prompt or input_text or input_code
            knowledge_limit = int(payload.get("knowledge_limit", VLM_MAX_KNOWLEDGE_RESULTS))

            context_items = []
            for path in context_paths:
                if isinstance(path, str):
                    context_items.append(read_text_file(path))

            knowledge_items = search_knowledge(knowledge_query, limit=knowledge_limit) if use_knowledge else []

            if self.path == "/api/text":
                examples = find_relevant_examples("text", f"{prompt}\n{input_text}")
                messages = build_messages("text", prompt, input_text, "", context_items, examples, knowledge_items)
                result = ollama_chat(TEXT_MODEL, messages) if VLM_BACKEND == "ollama" else {"backend": "stub", "model": "stub", "content": "Stub-Antwort."}
                self._send_json(200, {
                    "ok": True,
                    "mode": "text",
                    "time": utc_now(),
                    "summary": summarize_text(input_text),
                    "examples_used": examples,
                    "knowledge_used": knowledge_items,
                    "context": context_items,
                    "result": result,
                })
                return

            if self.path == "/api/code":
                examples = find_relevant_examples("code", f"{prompt}\n{input_code}")
                messages = build_messages("code", prompt, "", input_code, context_items, examples, knowledge_items)
                result = ollama_chat(CODE_MODEL, messages) if VLM_BACKEND == "ollama" else {"backend": "stub", "model": "stub", "content": "Stub-Antwort."}
                self._send_json(200, {
                    "ok": True,
                    "mode": "code",
                    "time": utc_now(),
                    "analysis": analyze_code_meta(input_code),
                    "examples_used": examples,
                    "knowledge_used": knowledge_items,
                    "context": context_items,
                    "result": result,
                })
                return
            if self.path == "/api/image":
                image_info = read_binary_b64(image_path)
                if not image_info.get("ok"):
                    self._send_json(400, image_info)
                    return
                examples = find_relevant_examples("image", prompt)
                messages = build_messages("image", prompt, input_text, "", context_items, examples, knowledge_items)
                result = ollama_chat(VISION_MODEL, messages, image_b64=image_info["content_b64"]) if VLM_BACKEND == "ollama" else {"backend": "stub", "model": "stub", "content": "Stub-Antwort."}
                self._send_json(200, {
                    "ok": True,
                    "mode": "image",
                    "time": utc_now(),
                    "image": {"path": image_info["path"], "size_bytes": image_info["size_bytes"]},
                    "examples_used": examples,
                    "knowledge_used": knowledge_items,
                    "context": context_items,
                    "result": result,
                })
                return

            if self.path == "/api/chat":
                examples = find_relevant_examples("general", f"{prompt}\n{input_text}\n{input_code}")
                image_info = None
                model = TEXT_MODEL
                image_b64 = None

                if image_path:
                    image_info = read_binary_b64(image_path)
                    if image_info.get("ok"):
                        image_b64 = image_info["content_b64"]
                        model = VISION_MODEL
                elif input_code:
                    model = CODE_MODEL

                messages = build_messages("general", prompt, input_text, input_code, context_items, examples, knowledge_items)
                result = ollama_chat(model, messages, image_b64=image_b64) if VLM_BACKEND == "ollama" else {"backend": "stub", "model": "stub", "content": "Stub-Antwort."}

                self._send_json(200, {
                    "ok": True,
                    "mode": "chat",
                    "time": utc_now(),
                    "examples_used": examples,
                    "knowledge_used": knowledge_items,
                    "context": context_items,
                    "image": None if not image_info or not image_info.get("ok") else {
                        "path": image_info["path"],
                        "size_bytes": image_info["size_bytes"],
                    },
                    "result": result,
                })
                return

            self._send_json(404, {"ok": False, "error": "not found", "path": self.path})

        except Exception as exc:
            self._send_json(500, {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            })

def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[{utc_now()}] astromanager-vlm listening on {HOST}:{PORT} backend={VLM_BACKEND}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
