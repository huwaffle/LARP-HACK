# LARP (Local AI Refinement Platform)

An offline, terminal-based AI toolbox. Everything runs on your own computer through [Ollama](https://ollama.com). No cloud, no accounts, no data leaving your machine.

## Quick start (Windows)

1. Install **Python 3.10+** from https://python.org (tick "Add Python to PATH").
2. Install **Ollama** from https://ollama.com and download a model once (needs internet):
   ```
   ollama pull gemma3:4b
   ```
3. Download this project, then **double-click `larp.bat`**.

`larp.bat` installs the Python packages, starts Ollama if needed, and opens LARP. Wi-Fi can be off after step 2.

Manual run (any OS):
```
pip install -r requirements.txt
python larp.py
```

## Commands

Type `/` to see the list. Use Up/Down, Tab to complete, Enter to run.

| Command | What it does |
|---|---|
| `/enhanceprompt` | Rewrites a vague prompt, with before/after score |
| `/projectspec` | Turns an idea into a project spec |
| `/architect` | Builds an architecture blueprint |
| `/aiskill` | Writes a reusable rules file (SKILL.md, CLAUDE.md, .cursorrules) |
| `/humanize` | Makes text sound natural, with score and diff |
| `/fixgrammar` | Fixes spelling and grammar, with score and diff |
| `/auto` | Runs the whole pipeline from one idea and saves files in `larp_output/` |
| `/model` | Pick from the models installed on your machine |
| `/theme` | Change colors (green, blue, purple, red, orange) |
| `/help`, `/quit` | Help and exit |

Example: `/enhanceprompt make me a good portfolio`

Tips: Enter sends, Ctrl+J adds a new line, and you can pass a file path instead of text.

One-shot mode (no UI): `python larp.py grammar "some text"`

## Models

LARP detects the models installed in Ollama automatically. Use `/model` to switch. If none are found it shows where to get one: https://ollama.com/library

Good picks: `gemma3:4b` (fast), `llama3.2:3b`, `qwen2.5:7b` or `mistral:7b` (better quality).

## Project layout

```
larp.py         app, screen and slash commands
ai.py           Ollama client (chat, streaming, model list)
features/core.py  the six features
prompts/        instructions used by each feature
larp.bat        one-click launcher for Windows
```

## License

MIT
>>>>>>> c91ca08 (Organize codebase, add launcher, and update documentation for local AI setup)
