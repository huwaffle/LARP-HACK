# LARP (Local AI Refinement Platform)

An offline, keyboard-driven AI refinement platform and developer workspace. Operating 100% locally through Ollama, LARP provides structured prompt engineering, technical specification drafting, system architecture blueprints, and AI agent rule compilation with zero cloud telemetry.

---

## Pitch & Presentation Guide

This section outlines the core narrative and talking points for presenting LARP to judges and panelists.

### The 30-Second Pitch (Stage Script)

> "Every engineering team wants to leverage AI for prompt engineering and system design, but corporate security policies strictly forbid sending proprietary source code and confidential architecture to cloud APIs. Meanwhile, running raw local models produces unstructured, inconsistent answers.
> 
> LARP solves this by turning small local language models into an offline developer workbench. Disconnect your machine from Wi-Fi: LARP takes a single concept, enhances the prompt, generates a full functional specification, drafts an architecture blueprint, and exports production-ready `.cursorrules` and `SKILL.md` agent files directly to your repo in under 60 seconds. Zero API costs, zero telemetry, 100% offline."

### The 3 Core Pain Points Solved

1. **Enterprise IP & Data Sovereignty**: Defense, healthcare, finance, and enterprise developers cannot paste proprietary requirements into ChatGPT or Claude. LARP executes 100% on localhost with zero data egress.
2. **Context Budgeting for Small Models**: Small local models (3B to 7B) have limited context windows and lower reasoning thresholds. LARP uses internal prompt structuring and automated context condensation to prevent small models from hallucinating or crashing.
3. **Immediate Developer Utility**: Unlike generic chatbots, LARP produces concrete software deliverables: `SPEC.md`, `ARCHITECTURE.md`, `.cursorrules` (Cursor / Windsurf), and `SKILL.md` (Claude Code / Antigravity).

### Panelist Q&A Defense

- **"Why not just use ChatGPT or Claude?"**
  - Data privacy and cost. Enterprise policy prohibits leaking trade secrets to third-party model providers. LARP runs offline with zero subscription fees and zero cloud latency.
- **"Can a small 4B local model actually generate software architecture?"**
  - LARP is an 80% baseline scaffolding engine. It bootstraps the heavy initial structure, technical constraints, component breakdowns, and data models locally so the human engineer can refine it without starting from a blank page.
- **"Is the UI inspired by OpenCode?"**
  - Yes. We adopted the keyboard-driven TUI design language popularized by modern developer tools like OpenCode and Claude Code, but built our own native Python terminal engine with background multithreading, live token streaming, and zero cloud dependencies.

---

## Technical Disclosures

Mandatory hackathon technical specifications and disclosures:

### 1. Models Used
- **Primary / Default SLM**: `gemma3:4b` (Google Gemma 3 4B parameters, instruction-tuned, 4-bit quantized via Ollama).
- **Supported Local Models**:
  - `llama3.2:3b` (Meta Llama 3.2 3B, low resource, fast execution)
  - `qwen2.5:7b` / `qwen2.5-coder:7b` (Alibaba Qwen 2.5, optimized for technical specifications and coding)
  - `mistral:7b` (Mistral AI 7B v0.3, balanced general reasoning)
- **Embeddings & Vision**: None. Pure local generative SLM text inference.

### 2. Technologies & Frameworks
- **Language & Runtime**: Python 3.10+ (Standard library: `urllib.request`, `json`, `threading`, `difflib`, `colorsys`, `ctypes`).
- **Local Inference Engine**: Ollama (runs locally on `http://127.0.0.1:11434`, utilizing a llama.cpp C/C++ backend with GPU/CPU acceleration).
- **Terminal User Interface (TUI)**:
  - `prompt_toolkit`: Full-screen layout engine, custom buffer processor, keybinding event loop, and live autocomplete popup.
  - `rich`: Markdown parsing, terminal ANSI color engine, and inline visual diff renderer.
- **System Utilities**: `pyperclip` (operating system clipboard access).
- **Packaging**: `setuptools` / `pyproject.toml` (exposes console script entrypoint `larp = larp.app:main`).
- **Database & Persistence**: Local filesystem only (`larp_output/`, `.larp_theme`). Zero external databases.

### 3. APIs & Cloud Services
- **None (0 Cloud APIs / 0 External Endpoints)**.
- LARP has zero remote network dependencies. All inference calls are strictly routed to `http://127.0.0.1:11434` on localhost.

### 4. Existing Code, Assets & AI Development Tools
- **AI Development Tools**: Devin, Antigravity IDE, Cursor (utilized for pair programming and code generation assistance during the hackathon sprint).
- **Open-Source Libraries**: `prompt_toolkit`, `rich`, `pyperclip`, `setuptools`.
- **Pre-Existing Codebases / Starter Templates**: None. Core application architecture, terminal engine, and feature pipelines were built from scratch during the hackathon sprint.
- **UI Design Paradigm**: Inspired by developer CLI tools including OpenCode and Claude Code.

---

## 60-Second Quickstart

### 1. Prerequisites

Ensure you have installed:
- **Python 3.10+**: https://python.org (Check "Add Python to PATH" during installation)
- **Ollama**: https://ollama.com

Pull a lightweight model to your local machine:
```bash
ollama pull gemma3:4b
```
*(Alternative supported models: `llama3.2:3b`, `qwen2.5:7b`, `mistral:7b`)*

### 2. Launch LARP

Choose the method that fits your environment:

#### Method A: Windows One-Click (Recommended for Judges)
Double-click `larp.bat`, or execute from PowerShell:
```powershell
.\larp.bat
```
*`larp.bat` automatically verifies Python packages, boots the local Ollama daemon if idle, and opens the interface.*

#### Method B: System-Wide Command Installation (Windows)
Double-click `install.bat` (or run `pip install -e .`). You can then open any terminal window and type:
```bash
larp
```

#### Method C: Cross-Platform (macOS / Linux / Windows)
```bash
pip install -r requirements.txt
python -m larp
```

---

## Key Controls

- `Enter`: Submit text
- `Ctrl + J`: Insert a new line in the input box
- `Tab` / `Shift + Tab`: Cycle active modes (`Enhance` -> `Spec` -> `Architect` -> `Skill` -> `Humanize` -> `Grammar`)
- `/`: Open the slash-command menu
- `PageUp` / `PageDown`: Scroll through the output log
- `Ctrl + C`: Cancel an in-progress generation or exit cleanly

---

## Command Reference

| Command | Shortcut | Purpose | Output |
|---|---|---|---|
| `/enhanceprompt` | `/enhance` | Expands vague prompts into production-grade instructions | Refined prompt with structure |
| `/projectspec` | `/spec` | Turns a raw project concept into a functional specification | `SPEC.md` |
| `/architect` | `/plan` | Generates system topologies, tech stack blueprints, and data models | `ARCHITECTURE.md` |
| `/aiskill` | `/skill` | Compiles reusable AI coding rules (`SKILL.md`, `CLAUDE.md`, `.cursorrules`) | IDE agent rules |
| `/humanize` | `/human` | Rewrites mechanical AI outputs into natural human voice | Refined text + colored diff |
| `/fixgrammar` | `/grammar` | Fixes spelling, punctuation, and syntax without altering intent | Corrected text + colored diff |
| `/auto` | `/pipeline` | Runs the full 4-stage chained pipeline from a single prompt | All 4 markdown docs |
| `/install` | `/export` | Installs generated artifacts directly to a chosen project folder | Saves files to disk |
| `/model` | `/models` | Switches between locally installed Ollama models | Changes active LLM |
| `/theme` | `/color` | Switches terminal UI themes (green, blue, purple, red, orange) | Dynamic re-theme |
| `/copy` | - | Copies the most recent result directly to your clipboard | System clipboard |
| `/save` | - | Saves the most recent result to a specified file | Local file |
| `/clear` | `/cls` | Clears terminal display buffer | Clean viewport |
| `/developers` | `/team` | Displays team roster and credits | Credits panel |
| `/help` | `/?` | Opens the command reference panel | Reference modal |
| `/quit` | `/exit` | Exits the application and cleanly terminates the terminal session | Exit |

---

## Non-Interactive CLI Mode (Scripting & Piping)

LARP also supports direct execution without the full-screen interface:

```bash
# Correct grammar directly
python -m larp grammar "This is an sample sentence with an mistake."

# Enhance a prompt directly
python -m larp enhance "build an authentication service in rust"
```

---

## System Architecture

- **Zero Cloud Egress**: All HTTP calls target `http://127.0.0.1:11434`. Disconnecting your machine from Wi-Fi will not affect functionality.
- **Multithreaded Non-Blocking Runtime**: LLM inference runs on a background daemon worker. The terminal interface remains responsive, allowing live token streaming and instantaneous cancellation.
- **Context Window Management**: Input exceeding small model context budgets is automatically parsed and condensed to preserve critical technical constraints without triggering token overflow errors.

---

## Project Structure

```
LARP-HACK/
|-- larp/
|   |-- app.py            # Terminal interface, layout engine, and keybindings
|   |-- ai.py             # Ollama local HTTP client (streaming & model discovery)
|   |-- core.py           # Feature orchestration, context budgeting, and prompts
|   |-- terminal.py       # Terminal session integration
|   `-- prompts/          # Task-specific system instruction templates
|-- pyproject.toml        # Standard package configuration for CLI installation
|-- requirements.txt      # Core Python dependencies
|-- larp.bat              # One-click Windows runner
|-- install.bat           # System-wide installer
`-- README.md             # Documentation
```

---

## Troubleshooting

- **"Cannot reach Ollama"**: Verify that Ollama is installed and running. Start it manually with `ollama serve` or run `larp.bat` which launches it automatically.
- **"No models found"**: Ensure you have pulled at least one model via `ollama pull gemma3:4b`. Use `/model` inside LARP to detect it.
- **Terminal Display Issues**: Recommended terminal environments include Windows Terminal, VS Code Integrated Terminal, Alacritty, or iTerm2 with UTF-8 encoding enabled.

---

## Team & Credits

**Team:** Grow A Garden Trading Hub

**Developers:**
- Carlos Alcantara
- Zian Kyle Piangco
- Paulo Mendoza
- Joshua Enriquez

---

## License

MIT License.
