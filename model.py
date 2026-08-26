"""
model.py — talks to a local model. Nothing else.

Backends, in order when GT_BACKEND=auto:
  llama-server  http://127.0.0.1:8080   (the engine: grammar can bind)
  ollama        http://127.0.0.1:11434  (a permitted client for unmasked talk)

This is a local vessel. It does not call a cloud API.
A server that is down raises. It does not degrade to a canned answer.

Executor sees the question. Shape, if summoned, sees this turn plus the
story card. Whistleblower is not here. It is Python.
"""
import json
import os
import urllib.error
import urllib.request

OLLAMA = os.environ.get("GT_OLLAMA", "http://127.0.0.1:11434").rstrip("/")
LLAMA = os.environ.get("GT_LLAMA", "http://127.0.0.1:8080").rstrip("/")
WALK = os.environ.get("GT_WALK", "http://127.0.0.1:8081").rstrip("/")
OLLAMA_MODEL = os.environ.get("GT_OLLAMA_MODEL", "granite33-8b")
EXECUTOR_MAX_TOKENS = int(os.environ.get("GT_EXECUTOR_TOKENS", "512"))
EXECUTOR_TEMPERATURE = float(os.environ.get("GT_EXECUTOR_TEMP", "0.3"))
PROBE_MAX_TOKENS = int(os.environ.get(
    "GT_PROBE_TOKENS", os.environ.get("GT_EXECUTOR_TOKENS", "512")))
PROBE_TEMPERATURE = 0.0
PROBE_SEED = int(os.environ.get("GT_PROBE_SEED", "0"))
SHAPE_MAX_TOKENS = int(os.environ.get("GT_SHAPE_TOKENS", "220"))
COMMENT_MAX_TOKENS = int(os.environ.get("GT_COMMENT_TOKENS", "280"))
SHEET_MAX_TOKENS = int(os.environ.get("GT_SHEET_TOKENS", "400"))
WALK_TOKENS = int(os.environ.get("GT_WALK_TOKENS", "400"))


class ServerDown(RuntimeError):
    pass


def _http_json(url, payload=None, timeout=180):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            body = ""
        extra = (" — " + body.strip()) if body.strip() else ""
        raise ServerDown(
            f"{url} did not answer (HTTP {e.code}: {e.reason}{extra})"
        ) from e
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as e:
        raise ServerDown(f"{url} did not answer ({e})") from e


def _ollama_up():
    try:
        urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _url_up(base):
    try:
        urllib.request.urlopen(f"{base}/health", timeout=2)
        return True
    except Exception:
        return False


def _llama_up():
    return _url_up(LLAMA)


def walk_up():
    return _url_up(WALK)


def backend():
    want = os.environ.get("GT_BACKEND", "auto").strip().lower()
    if want == "ollama":
        return "ollama" if _ollama_up() else None
    if want in ("llama", "llama-server"):
        return "llama" if _llama_up() else None
    # auto: the engine first, the client second.
    if _llama_up():
        return "llama"
    if _ollama_up():
        return "ollama"
    return None


def health():
    return backend() is not None


def walk_props():
    """Asked of the beneath server (:8081), never of the face."""
    if not walk_up():
        return {"backend": None, "n_ctx": None, "model": None}
    try:
        d = _http_json(f"{WALK}/props", timeout=5)
    except ServerDown:
        return {"backend": "llama-server", "model": "(props failed)",
                "n_ctx": None}
    path = (d.get("model_path")
            or d.get("default_generation_settings", {}).get("model"))
    n_ctx = d.get("default_generation_settings", {}).get("n_ctx")
    return {"backend": "llama-server", "model": path, "n_ctx": n_ctx}


def loaded_model():
    """Asked of the SERVER, never of the model."""
    b = backend()
    if b == "ollama":
        try:
            tags = _http_json(f"{OLLAMA}/api/tags", timeout=5)
        except ServerDown:
            return {"backend": "ollama", "model": "(tags failed)"}
        names = [m.get("name") for m in tags.get("models", []) if m.get("name")]
        return {"backend": "ollama", "model": OLLAMA_MODEL,
                "available": ", ".join(names) or "(none listed)"}
    if b == "llama":
        try:
            d = _http_json(f"{LLAMA}/props", timeout=5)
        except ServerDown:
            return {"backend": "llama-server", "model": "(props failed)"}
        path = (d.get("model_path")
                or d.get("default_generation_settings", {}).get("model"))
        n_ctx = d.get("default_generation_settings", {}).get("n_ctx")
        return {"backend": "llama-server", "model": path, "n_ctx": n_ctx}
    return {"backend": None, "model": None}


def _complete(prompt, max_tokens, grammar=None, temperature=0.3, seed=None):
    b = backend()
    if b == "ollama":
        options = {
            "temperature": temperature,
            "top_p": 0.9 if temperature else 1.0,
            "num_predict": max_tokens,
        }
        if seed is not None:
            options["seed"] = int(seed)
        body = _http_json(f"{OLLAMA}/api/generate", {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": options,
        })
        return body.get("response") or ""
    if b == "llama":
        return _complete_llama(
            LLAMA, prompt, max_tokens, grammar, temperature, seed=seed)
    raise ServerDown(
        f"No local model is answering. Start llama-server at {LLAMA} "
        f"(preferred) or `ollama serve` (model {OLLAMA_MODEL}). "
        f"Nothing was generated.")


def granite_chat(user_text, history_pairs=None):
    """Wrap one user turn (and optional asked/answered pairs) in Granite roles.

    Raw /completion without this is not a conversation. It continues a document
    and will fill n_predict with training junk (the fox loop).
    """
    chunks = []
    for asked, answered in history_pairs or []:
        chunks.append(
            "<|start_of_role|>user<|end_of_role|>"
            + (asked or "")
            + "<|end_of_text|>")
        chunks.append(
            "<|start_of_role|>assistant<|end_of_role|>"
            + (answered or "")
            + "<|end_of_text|>")
    chunks.append(
        "<|start_of_role|>user<|end_of_role|>"
        + (user_text or "")
        + "<|end_of_text|>")
    chunks.append("<|start_of_role|>assistant<|end_of_role|>")
    return "\n".join(chunks)


def _complete_llama(base, prompt, max_tokens, grammar=None, temperature=0.3,
                    seed=None, cache_prompt=True):
    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": temperature,
        "top_p": 0.9 if temperature else 1.0,
        "stop": [
            "ANSWER_END",
            "<|end_of_text|>",
            "<|end_of_role|>",
            "<|start_of_role|>",
        ],
        "cache_prompt": bool(cache_prompt),
    }
    if seed is not None:
        payload["seed"] = int(seed)
    if grammar:
        payload["grammar"] = grammar
    return _http_json(f"{base}/completion", payload).get("content") or ""


def completion_raw(payload):
    """Full /completion JSON. Used by the RELIED hook, not by the face."""
    if backend() != "llama":
        raise ServerDown("RELIED /completion_raw binds on llama-server.")
    return _http_json(f"{LLAMA}/completion", payload)


def tokenize(content, add_special=False):
    if backend() != "llama":
        raise ServerDown("tokenize binds on llama-server.")
    body = _http_json(f"{LLAMA}/tokenize", {
        "content": content,
        "add_special": bool(add_special),
    })
    return body.get("tokens") or []


def probe(user_prompt, history_pairs=None, gt_relied=None):
    """A measurement under a placed premise. Not the face. Whole output.

    Temperature 0, fixed seed. Amendment 2026-08-20: a measurement is not
    a sample. The face (executor) is unchanged.
    """
    text, _meta = probe_measured(
        user_prompt, history_pairs=history_pairs, gt_relied=gt_relied)
    return text


def probe_measured(user_prompt, history_pairs=None, gt_relied=None):
    prompt = granite_chat(user_prompt or "", history_pairs)
    if backend() == "llama" and gt_relied:
        payload = {
            "prompt": prompt,
            "n_predict": PROBE_MAX_TOKENS,
            "temperature": PROBE_TEMPERATURE,
            "top_p": 1.0,
            "seed": PROBE_SEED,
            "stop": [
                "ANSWER_END",
                "<|end_of_text|>",
                "<|end_of_role|>",
                "<|start_of_role|>",
            ],
            "gt_relied": gt_relied,
        }
        resp = _http_json(f"{LLAMA}/completion", payload)
        return (resp.get("content") or ""), resp
    text = _complete(
        prompt, PROBE_MAX_TOKENS, grammar=None,
        temperature=PROBE_TEMPERATURE, seed=PROBE_SEED)
    return text, {}


def executor_prompt(system_prompt, user_prompt, history_pairs=None, grammar=None):
    """The exact string posted to /completion. Spans are mapped on this."""
    if grammar:
        if system_prompt:
            return system_prompt + "\n\n" + user_prompt + "\n\n"
        return (user_prompt or "") + "\n"
    current = user_prompt or ""
    if system_prompt:
        current = system_prompt + "\n\n" + current
    return granite_chat(current, history_pairs)


def executor(system_prompt, user_prompt, grammar=None, history_pairs=None,
             temperature=None, seed=None, gt_relied=None):
    """The answer. Grammar only if the caller passed one AND the backend is
    llama-server. Ollama here is free generation."""
    text, _meta = executor_measured(
        system_prompt, user_prompt, grammar=grammar,
        history_pairs=history_pairs, temperature=temperature,
        seed=seed, gt_relied=gt_relied)
    return text


def executor_measured(system_prompt, user_prompt, grammar=None,
                      history_pairs=None, temperature=None, seed=None,
                      gt_relied=None, gt_dial=None, gt_press=None):
    """Answer plus the raw completion JSON (for RELIED). Never computed here."""
    temp = EXECUTOR_TEMPERATURE if temperature is None else float(temperature)
    prompt = executor_prompt(
        system_prompt, user_prompt, history_pairs=history_pairs,
        grammar=grammar)
    b = backend()
    if b == "llama":
        payload = {
            "prompt": prompt,
            "n_predict": EXECUTOR_MAX_TOKENS,
            "temperature": temp,
            "top_p": 0.9 if temp else 1.0,
            "stop": [
                "ANSWER_END",
                "<|end_of_text|>",
                "<|end_of_role|>",
                "<|start_of_role|>",
            ],
        }
        if seed is not None:
            payload["seed"] = int(seed)
        if grammar:
            payload["grammar"] = grammar
        if gt_relied:
            payload["gt_relied"] = gt_relied
        if gt_dial:
            payload["gt_dial"] = gt_dial
        if gt_press:
            payload["gt_press"] = gt_press
        resp = _http_json(f"{LLAMA}/completion", payload)
        return (resp.get("content") or ""), resp
    if b == "ollama":
        if gt_relied:
            raise ServerDown(
                "RELIED binds on llama-server. This backend is ollama. "
                "Computing it here would be a costume. Refusing.")
        if gt_dial or gt_press:
            raise ServerDown(
                "dial and press bind on llama-server. This backend is ollama. "
                "Turning them ON would be a costume, not a constraint. "
                "Refusing.")
        text = _complete(prompt, EXECUTOR_MAX_TOKENS, grammar=None,
                         temperature=temp, seed=seed)
        return text, {}
    raise ServerDown(
        f"No local model is answering. Start llama-server at {LLAMA} "
        f"(preferred) or `ollama serve` (model {OLLAMA_MODEL}). "
        f"Nothing was generated.")


def _as_chat(system_prompt, user_prompt):
    """One chat turn. Raw /completion on a template continues the template."""
    current = user_prompt or ""
    if system_prompt:
        current = system_prompt + "\n\n" + current
    return granite_chat(current)


def shape(system_prompt, user_prompt):
    """Spoken form. Grammar-free. The caller must not parse this into a stop."""
    prompt = _as_chat(system_prompt, user_prompt)
    return _complete(prompt, SHAPE_MAX_TOKENS, grammar=None, temperature=0.1).strip()


def comment(system_prompt, user_prompt):
    """What a record is for. Grammar-free. Not a tag. Not a walk."""
    prompt = _as_chat(system_prompt, user_prompt)
    return _complete(prompt, COMMENT_MAX_TOKENS, grammar=None,
                     temperature=0.2).strip()


def face(system_prompt, user_prompt, max_tokens=None, temperature=0.2):
    """Face only. Inquire and bearings. Not LOOK, not sheet, not bind, not hop."""
    prompt = _as_chat(system_prompt, user_prompt)
    return _complete(prompt, max_tokens or COMMENT_MAX_TOKENS, grammar=None,
                     temperature=temperature).strip()


def hop(system_prompt, user_prompt):
    """Option A translation. Hits GT_WALK. Never the talk face.

    Talk's :8080 slot still holds last-N / divider chrome. A hop that
    reuses that mouth continues the wrap. Beneath is a second process.
    """
    if not walk_up():
        raise ServerDown(
            f"No beneath server at {WALK}. Start the CPU 2B there. "
            f"The face at {LLAMA} was not asked to hop.")
    prompt = _as_chat(system_prompt, user_prompt)
    return _complete_llama(
        WALK, prompt, COMMENT_MAX_TOKENS, grammar=None,
        temperature=0.1, cache_prompt=False).strip()


def look(system_prompt, user_prompt):
    """Leftover speech against a declared path. Hits GT_WALK. Never the face."""
    if not walk_up():
        raise ServerDown(
            f"No beneath server at {WALK}. Start the CPU 2B there. "
            f"The face at {LLAMA} was not asked to look.")
    prompt = _as_chat(system_prompt, user_prompt)
    return _complete_llama(WALK, prompt, COMMENT_MAX_TOKENS, grammar=None,
                           temperature=0.2).strip()


def sheet(system_prompt, user_prompt):
    """Summoned sheet-reading. Hits GT_WALK (:8081). Never the face."""
    if not walk_up():
        raise ServerDown(
            f"No beneath server at {WALK}. Start the CPU 2B there. "
            f"The face at {LLAMA} was not asked to sheet.")
    prompt = _as_chat(system_prompt, user_prompt)
    return _complete_llama(WALK, prompt, SHEET_MAX_TOKENS, grammar=None,
                           temperature=0.2).strip()


def walker(system_prompt, user_prompt):
    """Second POST. Hits GT_WALK (:8081). Never silently uses the face."""
    if not walk_up():
        raise ServerDown(
            f"No walk server at {WALK}. Start the CPU 2B there. "
            f"The face at {LLAMA} was not asked to walk.")
    prompt = f"{system_prompt}\n\n{user_prompt}\n"
    return _complete_llama(WALK, prompt, WALK_TOKENS, grammar=None,
                           temperature=0.1).strip()


def bind(system_prompt, user_prompt):
    """Bind a /sheet proposal to the face turn. Same HTTP as walker. Never the face."""
    return walker(system_prompt, user_prompt)
