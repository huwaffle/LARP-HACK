# LARP (Local AI Refinement Platform)

An offline, keyboard-driven AI refinement platform and developer workspace. Operating 100% locally through Ollama, LARP provides structured prompt engineering, technical specification drafting, system architecture blueprints, and AI agent rule compilation with zero cloud telemetry.

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

## Core Features & Prompting Guide

LARP provides 8 core developer workflows. You can trigger them either by selecting them with `Tab` mode switching, typing the slash command, or using one-shot CLI execution.

### 1. Enhance Prompt (`/enhanceprompt` or `/enhance`)
Transforms brief or underspecified instructions into production-grade prompts containing clear system roles, contextual constraints, technical requirements, and output schemas.
- **How to prompt:** Give your raw, rough idea or a one-line request.
- **Example:**
  ```text
  /enhanceprompt build an asynchronous job queue worker in python with redis
  ```

### 2. Project Specification (`/projectspec` or `/spec`)
Expands a high-level product concept into a structured functional specification (`SPEC.md`) complete with user stories, technical requirements, acceptance criteria, and edge-case handling.
- **How to prompt:** State the product name, core purpose, and key functional requirements.
- **Example:**
  ```text
  /projectspec offline markdown note-taking desktop application with local fuzzy search and sqlite storage
  ```

### 3. Architecture Blueprint (`/architect` or `/plan`)
Generates comprehensive software system architectures (`ARCHITECTURE.md`) detailing component topology, data models, API boundaries, technology stack trade-offs, and security posture.
- **How to prompt:** Describe the system, target scale, and requirements or constraints.
- **Example:**
  ```text
  /architect distributed event-driven payment processing backend using golang, postgresql, and kafka
  ```

### 4. AI Skill & Rules Compiler (`/aiskill` or `/skill`)
Compiles project conventions into standardized AI coding rulebooks for modern developer IDEs. Supports output formatting for `SKILL.md` (Antigravity), `CLAUDE.md` (Claude Code), and `.cursorrules` (Cursor/Windsurf).
- **How to prompt:** State the rules or prefix with the target format (`SKILL.md`, `CLAUDE.md`, or `.cursorrules`).
- **Examples:**
  ```text
  /aiskill enforce conventional commits, strict typescript types, and zero any policy
  /aiskill .cursorrules mobile-first responsive styling with vanilla css and no external frameworks
  ```

### 5. Humanize Text (`/humanize` or `/human`)
Rewrites stiff, bureaucratic, or machine-generated text into a natural human voice. Displays an inline colored diff highlighting word removals in red and additions in green.
- **How to prompt:** Paste the text directly, or prefix with a tone choice (`casual` or `professional`).
- **Examples:**
  ```text
  /humanize Our revolutionary paradigm shift synergizes cross-functional workflows to maximize velocity.
  /humanize professional We are pleased to announce our updated platform capabilities for enterprise clients.
  ```

### 6. Grammar & Syntax Fixer (`/fixgrammar` or `/grammar`)
Corrects typographical errors, punctuation mistakes, and awkward grammatical phrasing while strictly preserving the author's original meaning and technical terms. Shows an inline diff.
- **How to prompt:** Paste text or code comments containing errors.
- **Example:**
  ```text
  /fixgrammar The users doesnt receives there confirmation emails when they registers yesterday.
  ```

### 7. Full Automated Pipeline (`/auto` or `/pipeline`)
LARP's end-to-end orchestration command. Feeds a single concept sequentially through all four technical stages: **Enhance Prompt -> Project Spec -> Architecture -> Skill Rules**. Streams all four stages live and automatically saves the resulting files into `larp_output/`.
- **How to prompt:** Provide a single-sentence product or system concept.
- **Example:**
  ```text
  /auto lightweight peer-to-peer file transfer CLI tool in rust with end-to-end encryption
  ```

### 8. Project Artifact Installer (`/install` or `/export`)
Installs the generated output files directly into a target folder on your filesystem (e.g. current project root, Desktop, Documents, or any custom path) with automatic collision protection.
- **How to use:**
  ```text
  /install
  /install ./my-project
  ```

---

## Utility Commands

| Command | Shortcut | Purpose |
|---|---|---|
| `/copy` | - | Copies the most recent result to your system clipboard |
| `/save` | - | Saves the most recent result to a specified file name |
| `/retry` | `/again` | Re-executes the last operation |
| `/clear` | `/cls` | Clears the terminal output log |
| `/model` | `/models` | Opens interactive picker to switch installed Ollama models |
| `/theme` | `/color` | Cycles or picks color themes (green, blue, purple, red, orange) |
| `/developers` | `/team` | Displays the developer roster and team credits |
| `/help` | `/?` | Shows the quick command reference panel |
| `/quit` | `/exit` | Exits the application and closes the terminal session |

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
