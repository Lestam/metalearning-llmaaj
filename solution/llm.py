"""Gemma 4 client: one interface over Vertex AI, the Gemini API and any OpenAI-compatible host.

Every call is retried, cached on disk by (provider, model, messages, params) and metered.
"""
import hashlib
import random
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROVIDER = os.environ.get("GEMMA_PROVIDER", "vertex")  # vertex | gemini | openai
FALLBACK = os.environ.get("GEMMA_FALLBACK", "")  # optional second provider used when the first is rate-limited
MODEL = os.environ.get("GEMMA_MODEL", "")
DEFAULT_MODELS = {
    "vertex": "google/gemma-4-26b-a4b-it-maas",
    "gemini": "gemma-4-26b-a4b-it",
    "openai": "google/gemma-4-26b-a4b-it",
}
CACHE_DIR = Path(os.environ.get("LLM_CACHE_DIR", ".cache/llm"))
MAX_WORKERS = int(os.environ.get("LLM_WORKERS", "24"))
TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "180"))
THINKING_TIMEOUT = float(os.environ.get("LLM_THINKING_TIMEOUT", "900"))
RETRIES = int(os.environ.get("LLM_RETRIES", "10"))
CONCURRENCY = int(os.environ.get("LLM_CONCURRENCY", "5"))  # simultaneous requests across all threads

_lock = threading.Lock()
_slots = threading.BoundedSemaphore(CONCURRENCY)
STATS = {"calls": 0, "cached": 0, "errors": 0, "prompt_tokens": 0, "completion_tokens": 0, "seconds": 0.0}


def model_name(provider=None):
    provider = provider or PROVIDER
    return (MODEL if provider == PROVIDER else "") or DEFAULT_MODELS[provider]


class _Vertex:
    def __init__(self):
        import google.auth
        import google.auth.transport.requests
        from openai import OpenAI
        self.project = os.environ["VERTEX_PROJECT"]
        location = os.environ.get("VERTEX_LOCATION", "global")
        host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
        self.creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"],
                                            quota_project_id=self.project)
        self.request = google.auth.transport.requests.Request()
        self.base_url = f"https://{host}/v1/projects/{self.project}/locations/{location}/endpoints/openapi"
        self.OpenAI = OpenAI
        self.client = None
        self.token = None

    def _client(self):
        with _lock:
            if not self.creds.valid or self.client is None or self.token != self.creds.token:
                self.creds.refresh(self.request)
                self.token = self.creds.token
                self.client = self.OpenAI(base_url=self.base_url, api_key=self.token, timeout=TIMEOUT,
                                          max_retries=0, default_headers={"x-goog-user-project": self.project})
            return self.client

    def chat(self, messages, temperature, max_tokens, thinking, json_mode):
        kw = dict(model=model_name("vertex"), messages=messages, temperature=temperature, max_tokens=max_tokens)
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
        if thinking:
            kw["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}
        r = self._client().with_options(timeout=THINKING_TIMEOUT if thinking else TIMEOUT).chat.completions.create(**kw)
        return r.choices[0].message.content or "", r.usage.prompt_tokens, r.usage.completion_tokens


class _OpenAICompat:
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"],
                             timeout=TIMEOUT, max_retries=0)

    def chat(self, messages, temperature, max_tokens, thinking, json_mode):
        kw = dict(model=model_name("openai"), messages=messages, temperature=temperature, max_tokens=max_tokens)
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
        if thinking:
            kw["extra_body"] = {"reasoning": {"enabled": True}}
        r = self.client.with_options(timeout=THINKING_TIMEOUT if thinking else TIMEOUT).chat.completions.create(**kw)
        u = r.usage
        return r.choices[0].message.content or "", getattr(u, "prompt_tokens", 0), getattr(u, "completion_tokens", 0)


class _Gemini:
    def __init__(self):
        from google import genai
        from google.genai import types
        self.types = types
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                                   http_options=types.HttpOptions(timeout=int(TIMEOUT * 1000)))

    def chat(self, messages, temperature, max_tokens, thinking, json_mode):
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system") or None
        contents = [self.types.Content(role="model" if m["role"] == "assistant" else "user",
                                       parts=[self.types.Part(text=m["content"])])
                    for m in messages if m["role"] != "system"]
        cfg = self.types.GenerateContentConfig(system_instruction=system, temperature=temperature,
                                               max_output_tokens=max_tokens)
        if json_mode:  # response_schema times out for Gemma on this API; plain JSON mime type works
            cfg.response_mime_type = "application/json"
        r = self.client.models.generate_content(model=model_name("gemini"), contents=contents, config=cfg)
        u = r.usage_metadata
        return r.text or "", u.prompt_token_count or 0, u.candidates_token_count or 0


_backends = {}


def _get_backend(provider=None):
    provider = provider or PROVIDER
    with _lock:
        if provider not in _backends:
            _backends[provider] = {"vertex": _Vertex, "gemini": _Gemini, "openai": _OpenAICompat}[provider]()
        return _backends[provider]


def chat(messages, temperature=0.0, max_tokens=2048, thinking=False, json_mode=False, seed=0, use_cache=True):
    """Return the model's text. `seed` only separates cache entries for repeated samples."""
    key = hashlib.sha256(json.dumps([PROVIDER, model_name(), messages, temperature, max_tokens, thinking,
                                     json_mode, seed], ensure_ascii=False).encode()).hexdigest()
    path = CACHE_DIR / key[:2] / f"{key}.json"
    if use_cache and path.exists():
        with _lock:
            STATS["cached"] += 1
        return json.loads(path.read_text())["text"]
    delay = 2.0
    use_fallback = False
    think_now = thinking  # switched off after an empty reply: the reasoning ate the whole token budget
    for attempt in range(RETRIES):
        start = time.time()
        provider = FALLBACK if use_fallback else PROVIDER
        try:
            with _slots:
                text, pt, ct = _get_backend(provider).chat(messages, temperature, max_tokens, think_now, json_mode)
            if not text.strip():
                if think_now:
                    think_now = False
                raise RuntimeError("empty response (retrying without thinking)")
            with _lock:
                STATS["calls"] += 1
                STATS["prompt_tokens"] += pt
                STATS["completion_tokens"] += ct
                STATS["seconds"] += time.time() - start
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"text": text}, ensure_ascii=False))
            return text
        except Exception as error:  # noqa: BLE001 - network/provider errors are retried
            with _lock:
                STATS["errors"] += 1
            if attempt == RETRIES - 1:
                raise RuntimeError(f"Gemma call failed after {RETRIES} attempts: {error}") from error
            rate_limited = "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error)
            print(f"[llm] {provider} attempt {attempt + 1}/{RETRIES} failed after {time.time() - start:.0f}s "
                  f"(thinking={thinking}): {str(error)[:120]}", file=sys.stderr, flush=True)
            if FALLBACK and FALLBACK != PROVIDER:
                use_fallback = rate_limited and not use_fallback  # alternate providers while rate-limited
                if use_fallback:
                    continue
            time.sleep(delay * (3 if rate_limited else 1) + random.uniform(0, 2))
            delay = min(delay * 2, 40)


def parse_json(text):
    """Extract the first JSON object from a model reply (handles ``` fences and stray prose)."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise ValueError(f"No JSON object in model reply: {text[:200]!r}")


def pmap(fn, items, workers=None):
    with ThreadPoolExecutor(workers or MAX_WORKERS) as pool:
        return list(pool.map(fn, items))
