import json
import urllib.request

HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma3:4b"
_ctx_cache = {}


def _call(path, payload=None, timeout=300):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(HOST + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def is_online():
    try:
        _call("/api/tags", timeout=3)
        return True
    except Exception:
        return False


def list_models():
    models = _call("/api/tags", timeout=5).get("models", [])
    return [m["name"] for m in models if "embedding" not in m.get("capabilities", [])]


def context_length(model):
    """Maximum context window the model supports (tokens). Falls back to 8192."""
    if model not in _ctx_cache:
        n = 8192
        try:
            info = _call("/api/show", {"model": model}, timeout=10).get("model_info", {})
            n = next((v for k, v in info.items() if k.endswith(".context_length")), n)
        except Exception:
            pass
        _ctx_cache[model] = int(n)
    return _ctx_cache[model]


def _body(system, user, model, temperature, num_ctx, stream):
    options = {"temperature": temperature}
    if num_ctx:
        options["num_ctx"] = num_ctx
    return {"model": model, "stream": stream, "options": options,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}


def generate(system, user, model=DEFAULT_MODEL, temperature=0.4, num_ctx=None):
    res = _call("/api/chat", _body(system, user, model, temperature, num_ctx, False), timeout=1800)
    return res["message"]["content"].strip()


def stream(system, user, model=DEFAULT_MODEL, temperature=0.4, num_ctx=None):
    """Yield text chunks as the model writes them."""
    body = _body(system, user, model, temperature, num_ctx, True)
    req = urllib.request.Request(HOST + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        for line in r:
            d = json.loads(line)
            if "error" in d:
                raise RuntimeError(d["error"])
            yield d.get("message", {}).get("content", "")
            if d.get("done"):
                break
