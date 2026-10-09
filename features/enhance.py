from pathlib import Path

import ai

SYSTEM = (Path(__file__).parent.parent / "prompts" / "enhance.txt").read_text(encoding="utf-8")


def run(text, model=ai.DEFAULT_MODEL):
    return ai.generate(SYSTEM, text, model=model)
