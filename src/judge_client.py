"""Cached multimodal judge calls for OpenAI (internal gateway), Claude (Bedrock proxy) and Gemini (Vertex gateway).

Every call is cached on disk by sha256(model_id + prompt_id + prompt text + image bytes + settings), so reruns cost nothing.
Usage (tokens) is stored with each cached response so spend can be totalled from files.
"""
import base64
import hashlib
import http.client
import json
import os
import threading
import time
import urllib.error
import urllib.request

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "judges", "cache")
GATEWAY = "http://127.0.0.1:19193"
MAX_OUTPUT_TOKENS = 400

# USD per 1M tokens (input, output). Sources recorded in LOG.md.
PRICES = {
    "gpt-5": (1.25, 10.00),
    "gpt-5.4": (2.50, 15.00),
    "gpt-5.4-mini": (0.75, 4.50),
    "global.anthropic.claude-sonnet-5-5": (2.00, 10.00),
    "global.anthropic.claude-haiku-4-5-20251001-v1:0": (1.00, 5.00),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.30, 2.50),
}
BUDGET_USD = 30.00
HARD_STOP_USD = 29.20
SPEND_REFRESH_EVERY = 50


class BudgetExceeded(Exception):
    pass


def cost_usd(rec: dict) -> float:
    pin, pout = PRICES[rec["model"]]
    return (rec["input_tokens"] * pin + rec["output_tokens"] * pout) / 1e6


def total_spend() -> float:
    total = 0.0
    if not os.path.isdir(CACHE_DIR):
        return total
    for sub in os.listdir(CACHE_DIR):
        for name in os.listdir(os.path.join(CACHE_DIR, sub)):
            with open(os.path.join(CACHE_DIR, sub, name)) as f:
                total += cost_usd(json.load(f))
    return total


_spend = {"usd": None, "since_refresh": 0}
_spend_lock = threading.Lock()


def provider(model: str) -> str:
    if "anthropic" in model:
        return "claude"
    if model.startswith("gemini"):
        return "gemini"
    return "openai"


class TransientError(Exception):
    pass


class RateLimiter:
    """Sliding-window limiter: at most `per_minute` request starts in any 60 s window."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.starts: list[float] = []
        self.lock = threading.Lock()

    def wait(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                self.starts = [t for t in self.starts if now - t < 60]
                if len(self.starts) < self.per_minute:
                    self.starts.append(now)
                    return
                sleep_for = 60 - (now - self.starts[0]) + 0.05
            time.sleep(sleep_for)


LIMITERS = {"openai.pinadmin.com": RateLimiter(45), "vertexai.pinadmin.com": RateLimiter(45), "bedrock": RateLimiter(45)}


def _post(url: str, body: dict, headers: dict, timeout: int = 180) -> dict:
    LIMITERS.get(headers.get("Host", ""), LIMITERS["bedrock"]).wait()
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            detail = e.read()[:500].decode(errors="replace")
        except Exception:
            detail = ""
        if e.code in (408, 409, 429) or e.code >= 500:
            raise TransientError(f"{e.code} {detail}") from e
        raise RuntimeError(f"{e.code} {detail}") from e
    except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
        raise TransientError(repr(e)) from e


def _claude_headers() -> dict:
    h = {}
    for line in os.environ.get("ANTHROPIC_CUSTOM_HEADERS", "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            h[k.strip()] = v.strip()
    return h


Part = str | bytes


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _call_openai(model: str, parts: list[Part], settings: dict) -> dict:
    content = [
        {"type": "text", "text": p} if isinstance(p, str)
        else {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + _b64(p), "detail": "high"}}
        for p in parts
    ]
    body = {"model": model, "messages": [{"role": "user", "content": content}], "max_completion_tokens": settings.get("max_tokens", MAX_OUTPUT_TOKENS)}
    for k in ("reasoning_effort", "temperature"):
        if k in settings:
            body[k] = settings[k]
    r = _post(f"{GATEWAY}/v1/chat/completions", body, {"Host": "openai.pinadmin.com"})
    u = r.get("usage", {})
    return {
        "text": r["choices"][0]["message"].get("content") or "",
        "finish": r["choices"][0].get("finish_reason"),
        "input_tokens": u.get("prompt_tokens", 0),
        "output_tokens": u.get("completion_tokens", 0),
        "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
    }


def _call_claude(model: str, parts: list[Part], settings: dict) -> dict:
    content = [
        {"type": "text", "text": p} if isinstance(p, str)
        else {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _b64(p)}}
        for p in parts
    ]
    body = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": settings.get("max_tokens", MAX_OUTPUT_TOKENS), "messages": [{"role": "user", "content": content}]}
    for k in ("thinking", "temperature"):
        if k in settings:
            body[k] = settings[k]
    if "effort" in settings:
        body["output_config"] = {"effort": settings["effort"]}
    r = _post(f"{os.environ['ANTHROPIC_BEDROCK_BASE_URL']}/model/{model}/invoke", body, _claude_headers())
    u = r.get("usage", {})
    return {
        "text": "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text"),
        "finish": r.get("stop_reason"),
        "input_tokens": u.get("input_tokens", 0),
        "output_tokens": u.get("output_tokens", 0),
        "reasoning_tokens": 0,
    }


def _call_gemini(model: str, parts: list[Part], settings: dict) -> dict:
    gparts = [{"text": p} if isinstance(p, str) else {"inline_data": {"mime_type": "image/jpeg", "data": _b64(p)}} for p in parts]
    gen = {"maxOutputTokens": settings.get("max_tokens", MAX_OUTPUT_TOKENS)}
    if "temperature" in settings:
        gen["temperature"] = settings["temperature"]
    if "thinking_budget" in settings:
        gen["thinkingConfig"] = {"thinkingBudget": settings["thinking_budget"]}
    url = f"{GATEWAY}/v1/projects/pin-dev-helix/locations/global/publishers/google/models/{model}:generateContent"
    r = _post(url, {"contents": [{"role": "user", "parts": gparts}], "generationConfig": gen}, {"Host": "vertexai.pinadmin.com"})
    cand = (r.get("candidates") or [{}])[0]
    u = r.get("usageMetadata", {})
    return {
        "text": "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought")),
        "finish": cand.get("finishReason"),
        "input_tokens": u.get("promptTokenCount", 0),
        "output_tokens": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0),
        "reasoning_tokens": u.get("thoughtsTokenCount", 0),
    }


CALLERS = {"openai": _call_openai, "claude": _call_claude, "gemini": _call_gemini}


def cache_key(model: str, prompt_id: str, parts: list[Part], settings: dict) -> str:
    h = hashlib.sha256()
    for field in (model, prompt_id, json.dumps(settings, sort_keys=True)):
        h.update(field.encode())
        h.update(b"\x00")
    for p in parts:
        h.update(hashlib.sha256(p.encode() if isinstance(p, str) else p).digest())
    return h.hexdigest()


@retry(retry=retry_if_exception(lambda e: isinstance(e, TransientError)), wait=wait_exponential(min=5, max=90), stop=stop_after_attempt(8), reraise=True)
def _call(model: str, parts: list[Part], settings: dict) -> dict:
    return CALLERS[provider(model)](model, parts, settings)


def judge(model: str, prompt_id: str, parts: list[Part], settings: dict | None = None) -> dict:
    settings = settings or {}
    key = cache_key(model, prompt_id, parts, settings)
    path = os.path.join(CACHE_DIR, key[:2], key + ".json")
    if os.path.exists(path):
        with open(path) as f:
            return {**json.load(f), "cached": True}
    with _spend_lock:
        if _spend["usd"] is None or _spend["since_refresh"] >= SPEND_REFRESH_EVERY:
            _spend["usd"] = total_spend()
            _spend["since_refresh"] = 0
        _spend["since_refresh"] += 1
    if _spend["usd"] >= HARD_STOP_USD:
        raise BudgetExceeded(f"spend ${_spend['usd']:.2f} reached hard stop ${HARD_STOP_USD:.2f}")
    out = {"model": model, "prompt_id": prompt_id, "settings": settings, **_call(model, parts, settings)}
    _spend["usd"] += cost_usd(out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f)
    return {**out, "cached": False}
