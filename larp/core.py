import re
from pathlib import Path

from . import ai

PROMPTS = Path(__file__).parent / "prompts"

FEATURES = {
    "enhance": dict(title="Enhanced prompt", diff=False, file="enhanced_prompt.md"),
    "spec": dict(title="Project spec", diff=False, file="SPEC.md"),
    "architect": dict(title="Architecture blueprint", diff=False, file="ARCHITECTURE.md"),
    "skill": dict(title="AI skill", diff=False, file="SKILL.md"),
    "humanize": dict(title="Humanized text", diff=True, file="humanized.txt"),
    "grammar": dict(title="Corrected text", diff=True, file="corrected.txt"),
}

TONES = ["casual", "professional"]
SKILL_FORMATS = {
    "SKILL.md": "Target format: SKILL.md. Begin with YAML frontmatter containing `name` (kebab-case) and `description` (one sentence saying when to use it), then the Markdown body.",
    "CLAUDE.md": "Target format: CLAUDE.md, a Markdown project-instructions file with short headed sections.",
    ".cursorrules": "Target format: .cursorrules, plain text rules, one rule per line, no Markdown headings.",
}

SPLIT_RE = "(" + chr(10) + "+|(?<=[.!?])[ " + chr(9) + "]+)"
CTX_CAP = 16384
GENERATIVE_OUT = 3000
CONDENSE_SYSTEM = (
    "Condense the following text into a compact list that keeps every important requirement, fact, name, number and constraint. "
    "Do not add anything new. Output ONLY the condensed list."
)


def system_prompt(feature, option=None):
    s = (PROMPTS / f"{feature}.txt").read_text(encoding="utf-8")
    if feature == "humanize":
        s += f"\nRequested tone: {option or 'casual'}."
    elif feature == "skill":
        s += "\n" + SKILL_FORMATS[option or "SKILL.md"]
    return s


def tokens(s):
    return len(s) // 3 + 1


def limit(model):
    return min(CTX_CAP, ai.context_length(model))


def ctx_for(need, model):
    n = 4096
    while n < need and n < limit(model):
        n *= 2
    return min(n, limit(model))


def split_text(text, max_tokens):
    """Cut text into pieces that fit max_tokens, breaking after line/sentence ends. Concatenating the pieces gives the original text."""
    max_chars = max(200, max_tokens * 3)
    pieces, cur = [], ""
    for t in re.split(SPLIT_RE, text):
        while len(t) > max_chars:
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.append(t[:max_chars])
            t = t[max_chars:]
        if cur and len(cur) + len(t) > max_chars:
            pieces.append(cur)
            cur = ""
        cur += t
    if cur:
        pieces.append(cur)
    return pieces


def condense(text, model, status):
    """Shrink very long input so it fits in the model's context window."""
    budget = (limit(model) - GENERATIVE_OUT - 1500)
    while tokens(text) > budget:
        parts = split_text(text, max(500, (limit(model) - 1500) // 2))
        if len(parts) == 1:
            return text[: budget * 3]
        done = []
        for i, part in enumerate(parts, 1):
            status(f"Input is very long: condensing part {i}/{len(parts)}")
            done.append(ai.generate(CONDENSE_SYSTEM, part, model=model, temperature=0.2, num_ctx=ctx_for(tokens(part) * 2 + 800, model)))
        new = "\n".join(done)
        if len(new) >= len(text):
            return new[: budget * 3]
        text = new
    return text


def run_stream(feature, text, model=ai.DEFAULT_MODEL, option=None, status=lambda msg: None):
    """Yield text chunks. Long input is chunked (humanize/grammar) or condensed (others)."""
    system = system_prompt(feature, option)
    temp = 0.7 if feature == "humanize" else 0.3
    if feature in ("humanize", "grammar"):
        per_call = max(500, (limit(model) - tokens(system) - 600) // 2)
        parts = split_text(text, per_call) if tokens(text) > per_call else [text]
        for i, part in enumerate(parts, 1):
            if len(parts) > 1:
                status(f"Long text: part {i}/{len(parts)}")
            body = part.rstrip()
            if body:
                yield from ai.stream(system, body, model=model, temperature=temp, num_ctx=ctx_for(tokens(system) + tokens(body) * 2 + 400, model))
            yield part[len(body):]
        status("")
        return
    need = tokens(system) + tokens(text) + GENERATIVE_OUT
    if need > limit(model):
        text = condense(text, model, status)
        need = tokens(system) + tokens(text) + GENERATIVE_OUT
    status("")
    yield from ai.stream(system, text, model=model, temperature=temp, num_ctx=ctx_for(need, model))


def run(feature, text, model=ai.DEFAULT_MODEL, option=None):
    return "".join(run_stream(feature, text, model, option)).strip()
