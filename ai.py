import json
import urllib.request

HOST = "http://localhost:11434"
DEFAULT_MODEL = "gemma3:4b"


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


def generate(system, user, model=DEFAULT_MODEL, temperature=0.4):
    res = _call("/api/chat", {
        "model": model,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    })
    return res["message"]["content"].strip()


def pull(model):
    """Yield (status, completed, total) while Ollama downloads a model."""
    req = urllib.request.Request(HOST + "/api/pull", data=json.dumps({"model": model, "stream": True}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            d = json.loads(line)
            if "error" in d:
                raise RuntimeError(d["error"])
            yield d.get("status", ""), d.get("completed", 0), d.get("total", 0)


def stream(system, user, model=DEFAULT_MODEL, temperature=0.4):
    """Yield text chunks as the model writes them."""
    body = {"model": model, "stream": True, "options": {"temperature": temperature},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(HOST + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        for line in r:
            d = json.loads(line)
            if "error" in d:
                raise RuntimeError(d["error"])
            yield d.get("message", {}).get("content", "")
            if d.get("done"):
                break
