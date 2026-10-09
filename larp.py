import colorsys
import difflib
import os
import sys

import pyperclip
import questionary
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    BufferControl, ConditionalContainer, Dimension, FormattedTextControl, HSplit, Layout, VSplit, Window, WindowAlign,
)
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.styles import Style as PtStyle

import ai
from features import core

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console()
state = {"model": ai.DEFAULT_MODEL, "mode": "enhance"}

ACTIONS = {
    "enhance": "Enhance a prompt",
    "spec": "Make a project spec",
    "architect": "Architect planner",
    "skill": "Make an AI skill",
    "humanize": "Humanize text",
    "grammar": "Fix grammar",
    "settings": "Settings (choose AI model)",
    "quit": "Quit",
}
COMMANDS = [
    ("enhanceprompt", "enhance", "Enhance a prompt", ["enhance", "prompt"]),
    ("projectspec", "spec", "Make a project spec", ["spec"]),
    ("architect", "architect", "Architect planner", ["plan"]),
    ("aiskill", "skill", "Make an AI skill", ["skill"]),
    ("humanize", "humanize", "Humanize text", ["human"]),
    ("fixgrammar", "grammar", "Fix grammar", ["grammar"]),
    ("auto", "auto", "Run full pipeline", ["pipeline", "all"]),
    ("model", "settings", "Choose AI model", ["models", "settings"]),
    ("theme", "theme", "Change color theme", ["color", "colors", "tint"]),
    ("help", "help", "Show commands", ["?"]),
    ("quit", "quit", "Exit LARP", ["exit"]),
]


def matches(text):
    q = text[1:].lower()
    return [c for c in COMMANDS if any(n.startswith(q) for n in [c[0], *c[3]])]


def find_command(name):
    name = name.lower()
    for c in COMMANDS:
        if name == c[0] or name in c[3]:
            return c
    m = matches("/" + name)
    return m[0] if len(m) == 1 else None


MODES = [k for k in ACTIONS if k not in ("settings", "quit")]
MODE_NAMES = {"enhance": "Enhance", "spec": "Spec", "architect": "Architect",
              "skill": "Skill", "humanize": "Humanize", "grammar": "Grammar"}

GLYPHS = {
    "l": ["██   ", " █   ", " █   ", " █   ", " █   ", " ███ "],
    "a": ["     ", " ███ ", "    █", " ████", "█   █", " ████"],
    "r": ["     ", "█ ██ ", "██  █", "█    ", "█    ", "█    "],
    "p": ["     ", "████ ", "█   █", "█   █", "████ ", "█    "],
}
LOGO_HEIGHT = 6
LOCAL_MODELS = {"llama3.2:3b": "2.0 GB, fast", "qwen2.5:7b": "4.7 GB, high quality", "mistral:7b": "4.1 GB, balanced", "phi3:mini": "2.2 GB, light"}

PLACEHOLDER = 'Ask anything... "Make my prompt better"'

THEMES = {"green": (0.40, "#3ddc84"), "blue": (0.60, "#4d8dff"), "purple": (0.75, "#a970ff"),
          "red": (0.00, "#ff5a5f"), "orange": (0.08, "#ff9f43")}
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".larp_theme")


def _hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def apply_theme(name):
    global BG, BOX, BLUE, STYLE
    h, BLUE = THEMES[name]
    BG, BOX = _hex(h, .04, .3), _hex(h, .11, .25)
    text, dim, bright = _hex(h, .9, .25), _hex(h, .45, .15), _hex(h, .96, .2)
    STYLE = PtStyle.from_dict({
        "": f"bg:{BG} {text}",
        "logo.dim": f"bg:{BG} {_hex(h, .5, .15)} bold",
        "logo.bright": f"bg:{BG} {bright} bold",
        "box": f"bg:{BOX} {text}",
        "bar": f"bg:{BOX} {BLUE}",
        "placeholder": f"bg:{BOX} {dim}",
        "mode": f"bg:{BOX} {BLUE} bold",
        "model": f"bg:{BOX} {bright} bold",
        "dim": f"bg:{BOX} {dim}",
        "foot.dim": f"bg:{BG} {dim}",
        "foot.key": f"bg:{BG} {bright} bold",
        "ok": f"bg:{BOX} #4ade80",
        "bad": f"bg:{BOX} #f87171",
        "pop": f"bg:{BOX} {_hex(h, .72, .2)}",
        "pop.sel": f"bg:{BLUE} #0a0a0a bold",
    })
    state["theme"] = name
    try:
        open(CONFIG, "w").write(name)
    except OSError:
        pass


def load_theme():
    try:
        name = open(CONFIG).read().strip()
    except OSError:
        name = "green"
    apply_theme(name if name in THEMES else "green")


def logo_fragments():
    out = []
    for r in range(LOGO_HEIGHT):
        for i, ch in enumerate("larp"):
            out.append(("class:logo.dim" if i < 2 else "class:logo.bright", GLYPHS[ch][r] + "  "))
        out.append(("", "\n"))
    return FormattedText(out[:-1])


class Placeholder(Processor):
    def apply_transformation(self, ti):
        if ti.lineno == 0 and not ti.document.text:
            return Transformation([("class:placeholder", PLACEHOLDER)])
        return Transformation(ti.fragments)


def spacer(weight=1):
    return Window(height=Dimension(weight=weight))


def build_app():
    buf = Buffer(multiline=True)
    sel = [0]
    visible = Condition(lambda: buf.text.startswith("/") and " " not in buf.text and bool(matches(buf.text)))
    online = ai.is_online()

    def mode_line():
        return FormattedText([
            ("class:mode", MODE_NAMES[state["mode"]]),
            ("class:dim", " · "),
            ("class:model", state["model"]),
            ("class:dim", "  local / LARP"),
        ])

    def status_line():
        return FormattedText([("class:ok" if online else "class:bad", "● offline-ready" if online else "● ollama not running")])

    def footer_left():
        return FormattedText([])

    def footer_right():
        return FormattedText([
            ("class:foot.key", "/"), ("class:foot.dim", " commands"),
        ])

    def popup():
        ms = matches(buf.text)
        sel[0] = max(0, min(sel[0], len(ms) - 1))
        out = []
        for i, (cmd, _, desc, _a) in enumerate(ms):
            st = "class:pop.sel" if i == sel[0] else "class:pop"
            out += [(st, f" /{cmd:<16}{desc:<30}"), ("", "\n" if i < len(ms) - 1 else "")]
        return FormattedText(out)

    popup_box = ConditionalContainer(Window(FormattedTextControl(popup), height=Dimension(max=len(COMMANDS)), style="class:pop"), filter=visible)

    inner = HSplit([
        Window(height=1, style="class:box"),
        Window(BufferControl(buf, input_processors=[Placeholder()]), wrap_lines=True, style="class:box",
               height=lambda: Dimension(min=1, max=8, preferred=max(1, buf.document.line_count))),
        Window(height=1, style="class:box"),
        VSplit([
            Window(FormattedTextControl(mode_line), height=1, style="class:box"),
            Window(FormattedTextControl(status_line), height=1, width=22, align=WindowAlign.RIGHT, style="class:box"),
        ]),
        Window(height=1, style="class:box"),
    ])
    box = VSplit([
        Window(width=1, style="class:bar", char="┃"),
        Window(width=2, style="class:box"),
        inner,
        Window(width=2, style="class:box"),
    ])
    footer = VSplit([
        Window(FormattedTextControl(footer_left), height=1),
        Window(FormattedTextControl(footer_right), height=1, align=WindowAlign.RIGHT),
    ])
    column = HSplit([box, popup_box, footer], width=Dimension(min=40, max=84, preferred=84))
    logo = Window(FormattedTextControl(logo_fragments), height=LOGO_HEIGHT, align=WindowAlign.CENTER)

    root = HSplit([
        spacer(2),
        logo,
        Window(height=2),
        VSplit([spacer_w(), column, spacer_w()]),
        spacer(3),
    ])

    kb = KeyBindings()

    @kb.add("enter")
    def _(e):
        if e.app.key_processor.input_queue:
            buf.insert_text("\n")
        else:
            e.app.exit(result=("run", buf.text.strip()))

    @kb.add("c-j")
    def _(e):
        buf.insert_text("\n")

    @kb.add("up", filter=visible)
    def _(e):
        sel[0] = max(0, sel[0] - 1)

    @kb.add("down", filter=visible)
    def _(e):
        sel[0] = min(len(matches(buf.text)) - 1, sel[0] + 1)

    @kb.add("tab", filter=visible)
    def _(e):
        buf.text = "/" + matches(buf.text)[sel[0]][0] + " "
        buf.cursor_position = len(buf.text)

    @kb.add("enter", filter=visible)
    def _(e):
        e.app.exit(result=("run", "/" + matches(buf.text)[sel[0]][0]))

    @kb.add("escape", filter=visible)
    def _(e):
        buf.reset()

    @kb.add("c-c")
    @kb.add("c-d")
    def _(e):
        e.app.exit(result=("quit", ""))

    return Application(layout=Layout(root, focused_element=buf), key_bindings=kb,
                       style=STYLE, full_screen=True, erase_when_done=True)


def spacer_w():
    return Window(width=Dimension(weight=1))


def select_style():
    return questionary.Style([
        ("qmark", f"fg:{BLUE} bold"), ("question", "bold"), ("answer", f"fg:{BLUE} bold"),
        ("pointer", f"fg:{BLUE} bold"), ("highlighted", f"fg:{BLUE} bold"),
        ("selected", f"fg:{BLUE}"), ("instruction", "fg:#6b8574"),
    ])


def bar(n):
    return "[" + "=" * round(n) + " " * (10 - round(n)) + "]"


def show_diff(a, b):
    t = Text()
    for tok in difflib.ndiff(a.split(), b.split()):
        if tok.startswith("- "):
            t.append(tok[2:] + " ", style="red strike")
        elif tok.startswith("+ "):
            t.append(tok[2:] + " ", style="green")
        elif tok.startswith("  "):
            t.append(tok[2:] + " ")
    console.print(Panel(t, title="Diff", border_style="green"))


def stream_panel(feature, text, model, option=None):
    acc = ""
    md = feature in ("spec", "architect", "skill")

    def render():
        body = Markdown(acc) if md and acc else (acc or "...")
        return Panel(body, title=core.FEATURES[feature]["title"], border_style="green")

    with Live(render(), console=console, refresh_per_second=10, vertical_overflow="visible") as live:
        for chunk in core.run_stream(feature, text, model, option):
            acc += chunk
            live.update(render())
    return acc.strip()


AUTO_STEPS = [("enhance", "enhanced_prompt.md"), ("spec", "SPEC.md"), ("architect", "ARCHITECTURE.md"), ("skill", "SKILL.md")]


def run_auto(idea):
    if os.path.isfile(idea):
        idea = open(idea, encoding="utf-8", errors="replace").read()
    model, out_dir, res = state["model"], "larp_output", {"idea": idea}
    os.makedirs(out_dir, exist_ok=True)
    plan = {"enhance": ("idea", None), "spec": ("enhance", None), "architect": ("spec", None), "skill": ("spec", "SKILL.md")}
    try:
        for i, (feature, fname) in enumerate(AUTO_STEPS, 1):
            console.print(f"\n[bold {BLUE}]Step {i}/{len(AUTO_STEPS)}: {core.FEATURES[feature]['title']}[/]")
            src, option = plan[feature]
            inp = res[src] if feature != "skill" else "Create project rules for an AI coding assistant building this project:\n\n" + res[src]
            res[feature] = stream_panel(feature, inp, model, option)
            open(os.path.join(out_dir, fname), "w", encoding="utf-8").write(res[feature])
    except Exception as e:
        console.print(f"[red]Error talking to Ollama: {e}[/]")
        questionary.press_any_key_to_continue().ask()
        return
    console.print(f"\n[bold green]Done.[/] Saved {', '.join(f for _, f in AUTO_STEPS)} in the [bold]{out_dir}[/] folder.")
    questionary.press_any_key_to_continue().ask()


def run_feature(feature, text):
    if os.path.isfile(text):
        text = open(text, encoding="utf-8", errors="replace").read()
    info = core.FEATURES[feature]
    option = None
    if feature == "humanize":
        option = questionary.select("Tone:", choices=core.TONES, style=select_style()).ask()
    elif feature == "skill":
        option = questionary.select("Save format:", choices=list(core.SKILL_FORMATS), style=select_style()).ask()
    if feature in ("humanize", "skill") and not option:
        return
    model = state["model"]
    while True:
        if feature in ("enhance", "humanize", "grammar"):
            console.print(Panel(text, title="Original", border_style="red"))
        try:
            result = stream_panel(feature, text, model, option)
            before = after = None
            if info["score"]:
                with console.status("[cyan]Scoring..."):
                    before, after = core.score(feature, text, model), core.score(feature, result, model)
        except Exception as e:
            console.print(f"[red]Error talking to Ollama: {e}[/]")
            questionary.press_any_key_to_continue().ask()
            return
        if info["diff"]:
            show_diff(text, result)
        if before and after:
            console.print(f"Before {bar(before)} {before:g}/10\nAfter  {bar(after)} {after:g}/10  ([green]{after - before:+g}[/])\n")
        fname = option if feature == "skill" else info["file"]
        choice = questionary.select("What next?", choices=["Copy", "Save to file", "Try again", "Back to menu"], style=select_style()).ask()
        if choice == "Copy":
            try:
                pyperclip.copy(result)
                console.print("[green]Copied.[/]")
            except Exception as e:
                console.print(f"[red]Copy failed: {e}[/]")
        elif choice == "Save to file":
            path = questionary.text("File name:", default=fname).ask()
            if path:
                open(path, "w", encoding="utf-8").write(result)
                console.print(f"[green]Saved to {path}[/]")
        elif choice != "Try again":
            return


def run_settings():
    try:
        models = ai.list_models()
    except Exception as e:
        console.print(f"[red]Cannot reach Ollama: {e}[/]")
        return
    if not models:
        console.print("[yellow]No models found on this device.[/]")
        console.print("  Download one here: [bold]https://ollama.com/library[/]")
        console.print("  Then install it with, for example: [bold]ollama pull llama3.2:3b[/]")
        console.print("  Run /model again and LARP will detect it.")
        questionary.press_any_key_to_continue().ask()
        return
    choice = questionary.select("Choose model (all run offline):", choices=models, style=select_style(),
                                default=state["model"] if state["model"] in models else None).ask()
    if choice:
        state["model"] = choice


def show_help():
    for cmd, _, desc, _a in COMMANDS:
        console.print(f"  [bold {BLUE}]/{cmd:<16}[/]{desc}")
    questionary.press_any_key_to_continue().ask()


def dispatch(action, text=""):
    if action == "settings":
        return run_settings()
    if action == "help":
        return show_help()
    if action == "theme":
        name = text.lower() if text.lower() in THEMES else questionary.select(
            "Theme:", choices=list(THEMES), default=state["theme"], style=select_style()).ask()
        return apply_theme(name) if name else None
    if not text:
        label = "Describe your project idea" if action == "auto" else f"{core.FEATURES[action]['title']} - paste text or a file path"
        text = questionary.text(label + ":").ask()
    if text and text.strip():
        (run_auto if action == "auto" else lambda t: run_feature(action, t))(text.strip())


def handle(text):
    """Returns False to quit."""
    if not text.startswith("/"):
        dispatch(state["mode"], text)
        return True
    name, _, rest = text[1:].partition(" ")
    cmd = find_command(name)
    if not cmd:
        console.print(f"[yellow]Unknown command /{name}. Type / to see commands.[/]")
        questionary.press_any_key_to_continue().ask()
        return True
    action = cmd[1]
    if action == "quit":
        return False
    if action in MODES:
        state["mode"] = action
        if rest.strip():
            dispatch(action, rest.strip())
    else:
        dispatch(action, rest.strip())
    return True


def main():
    load_theme()
    try:
        models = ai.list_models()
        if models and state["model"] not in models:
            state["model"] = models[0]
    except Exception:
        pass
    if len(sys.argv) > 2 and sys.argv[1] in core.FEATURES:
        sys.stdout.write(core.run(sys.argv[1], " ".join(sys.argv[2:]), state["model"]) + "\n")
        return
    while True:
        kind, text = build_app().run()
        if kind == "quit":
            return
        if text and not handle(text):
            return


if __name__ == "__main__":
    main()
