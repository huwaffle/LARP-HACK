# LARP (Local AI Refinement Platform)

An offline, terminal-based AI refinement platform and developer toolbox. Operating entirely on your local machine through Ollama, LARP provides zero telemetry, zero cloud dependencies, and zero latency overhead from network calls.

---

## Prerequisites

1. **Python 3.10+**: Download from https://python.org (ensure "Add Python to PATH" is checked during installation).
2. **Ollama**: Download and install from https://ollama.com.
3. **Download a local model**: Run this once in your terminal (requires internet for the initial download):
   ```bash
   ollama pull gemma3:4b
   ```
   *(Alternative models: `llama3.2:3b`, `qwen2.5:7b`, or `mistral:7b`)*

Once the model is downloaded, your internet/Wi-Fi can be completely turned off.

---

## Installation & Running

### Option 1: Direct Run (Windows - No Installation Needed)
Double-click `larp.bat` or run from PowerShell:
```powershell
.\larp.bat
```
`larp.bat` automatically verifies dependencies, starts the local Ollama service if it is not already running, and launches LARP.

### Option 2: System-Wide CLI Command (Windows)
Double-click `install.bat` (or run `pip install -e .`). 
After installation, open a new terminal anywhere and type:
```bash
larp
```

### Option 3: Standard Python (Linux, macOS, Windows)
```bash
pip install -r requirements.txt
python -m larp
```

### Non-Interactive One-Shot CLI Mode
You can also run tasks directly without opening the interactive TUI:
```bash
python -m larp grammar "This is an sample text with an grammatical mistakes."
python -m larp enhance "build an authentication service in go"
```

---

## Commands & Workflows

Type `/` in the input bar to open the command palette. Navigate with Up/Down, complete with Tab, and run with Enter. You can also cycle through modes directly by pressing Tab or Shift+Tab.

| Command | Aliases | Description |
|---|---|---|
| `/enhanceprompt` | `/enhance`, `/prompt` | Expands vague prompts into structured, high-signal instructions. |
| `/projectspec` | `/spec` | Turns a raw project concept into a functional product specification. |
| `/architect` | `/plan` | Generates system architecture designs, tech stacks, and component blueprints. |
| `/aiskill` | `/skill` | Compiles reusable AI coding rules (`SKILL.md`, `CLAUDE.md`, `.cursorrules`). |
| `/humanize` | `/human` | Refines stiff or robotic writing into natural phrasing with an inline diff. |
| `/fixgrammar` | `/grammar` | Corrects spelling, punctuation, and syntax with an inline diff. |
| `/auto` | `/pipeline`, `/all` | Chained pipeline: turns 1 idea into an enhanced prompt, spec, architecture, and skill. |
| `/install` | `/export`, `/download` | Exports generated files to a directory (This folder, Desktop, Downloads, or custom path). |
| `/copy` | - | Copies the last generated output to your clipboard. |
| `/save` | - | Saves the last generated output to a designated file. |
| `/retry` | `/again` | Re-runs the previous task. |
| `/clear` | `/cls` | Clears the terminal output log. |
| `/model` | `/models` | Switches between locally installed Ollama models. |
| `/theme` | `/color`, `/tint` | Changes color themes (green, blue, purple, red, orange). |
| `/developers` | `/team`, `/about` | Displays team and contributor credits. |
| `/help` | `/?` | Opens the command reference panel. |
| `/quit` | `/exit` | Closes LARP and cleanly terminates the terminal session. |

---

## Key Features

- **100% Offline & Private**: Zero data leaves your machine. Safe for proprietary codebases, internal architectures, and confidential notes.
- **Multithreaded Background Inference**: Heavy LLM generation runs on a background worker thread. The interface never freezes, and you can cancel running generations instantly with `Ctrl+C`.
- **In-App Scroll Buffer**: Long outputs (specifications, blueprints) are rendered in full Markdown and can be scrolled in-place using `PageUp` and `PageDown`.
- **Smart Context Window Management**: Input that exceeds small local model limits is automatically budgeted and condensed without losing key technical constraints.
- **Format-Ready Exports**: One-click install to `.cursorrules` (Cursor/Windsurf), `CLAUDE.md` (Claude Code), and `SKILL.md` (Antigravity/Agentic tools).

---

## Project Structure

```
LARP-HACK/
|-- larp/
|   |-- __init__.py       # Package definition
|   |-- __main__.py       # Module entrypoint for python -m larp
|   |-- app.py            # Terminal user interface, layout, and event loop
|   |-- ai.py             # Local Ollama HTTP client (chat, streaming, model tags)
|   |-- core.py           # Feature orchestration, context budgeting, and chunking
|   |-- terminal.py       # Terminal session and process integration
|   `-- prompts/          # System instruction templates for each task
|-- pyproject.toml        # Standard packaging and CLI script entrypoint
|-- requirements.txt      # Python dependencies
|-- larp.bat              # One-click Windows runner
|-- install.bat           # System-wide CLI installer
`-- README.md             # Project documentation
```

---

## Team & Credits

**Team:** Grow A Garden Trading Hub

**Developers:**
- Carlos Alcantara
- Zian Kyle Piangco
- Paulo Mendoza
- Joshua Enriquez

UI design inspired by modern terminal developer tools including OpenCode and Claude Code.

---

## License

MIT License. See LICENSE for details.
