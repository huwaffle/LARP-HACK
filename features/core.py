import re
from pathlib import Path

import ai

PROMPTS = Path(__file__).parent.parent / "prompts"

FEATURES = {
    "enhance": dict(title="Enhanced prompt", score="clarity, specificity and completeness as an instruction for an AI", diff=False, file="enhanced_prompt.md"),
    "spec": dict(title="Project spec", score=None, diff=False, file="SPEC.md"),
    "architect": dict(title="Architecture blueprint", score=None, diff=False, file="ARCHITECTURE.md"),
    "skill": dict(title="AI skill", score=None, diff=False, file="SKILL.md"),
    "humanize": dict(title="Humanized text", score="how natural and human it sounds (10 = clearly written by a person)", diff=True, file="humanized.txt"),
    "grammar": dict(title="Corrected text", score="spelling, grammar and punctuation correctness", diff=True, file="corrected.txt"),
}

TONES = ["casual", "professional"]
SKILL_FORMATS = {
    "SKILL.md": "Target format: SKILL.md. Begin with YAML frontmatter containing `name` (kebab-case) and `description` (one sentence saying when to use it), then the Markdown body.",
    "CLAUDE.md": "Target format: CLAUDE.md, a Markdown project-instructions file with short headed sections.",
    ".cursorrules": "Target format: .cursorrules, plain text rules, one rule per line, no Markdown headings.",
}


def system_prompt(feature, option=None):
    s = (PROMPTS / f"{feature}.txt").read_text(encoding="utf-8")
    if feature == "humanize":
        s += f"\nRequested tone: {option or 'casual'}."
    elif feature == "skill":
        s += "\n" + SKILL_FORMATS[option or "SKILL.md"]
    return s


def run(feature, text, model=ai.DEFAULT_MODEL, option=None):
    return ai.generate(system_prompt(feature, option), text, model=model, temperature=0.7 if feature == "humanize" else 0.3)


def score(feature, text, model=ai.DEFAULT_MODEL):
    criterion = FEATURES[feature]["score"]
    if not criterion:
        return None
    try:
        out = ai.generate(f"Rate the following text from 1 to 10 for {criterion}. Be strict. Reply with ONLY the number.", text, model=model, temperature=0)
        m = re.search(r"\d+(?:\.\d+)?", out)
        return max(1.0, min(10.0, float(m.group()))) if m else None
    except Exception:
        return None


def run_stream(feature, text, model=ai.DEFAULT_MODEL, option=None):
    return ai.stream(system_prompt(feature, option), text, model=model, temperature=0.7 if feature == "humanize" else 0.3)
