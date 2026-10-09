import colorsys
import difflib
import io
import os
import sys
import threading
import time

import pyperclip
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import ANSI, FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    BufferControl, ConditionalContainer, Dimension, FormattedTextControl, HSplit, Layout, VSplit, Window, WindowAlign,
)
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.styles import DynamicStyle, Style as PtStyle

import ai
from features import core

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

state = {"model": ai.DEFAULT_MODEL, "mode": "enhance", "busy": False, "cancel": False, "online": True,
         "picker": None, "scroll": 0, "result": None, "fname": None, "last": None}
APP = None
log = []
version = [0]
cache = {}

COMMANDS = [
    ("enhanceprompt", "enhance", "Enhance a prompt", ["enhance", "prompt"]),
    ("projectspec", "spec", "Make a project spec", ["spec"]),
    ("architect", "architect", "Architect planner", ["plan"]),
    ("aiskill", "skill", "Make an AI skill", ["skill"]),
    ("humanize", "humanize", "Humanize text", ["human"]),
    ("fixgrammar", "grammar", "Fix grammar", ["grammar"]),
    ("auto", "auto", "Run full pipeline", ["pipeline", "all"]),
    ("copy", "copy", "Copy last result", []),
    ("save", "save", "Save last result to file", []),
    ("retry", "retry", "Run the last task again", ["again"]),
    ("clear", "clear", "Clear the screen", ["cls"]),
    ("model", "model", "Choose AI model", ["models"]),
    ("theme", "theme", "Change color theme", ["color", "colors", "tint"]),
    ("help", "help", "Show commands", ["?"]),
    ("quit", "quit", "Exit LARP", ["exit"]),
]
FEATURE_ACTIONS = list(core.FEATURES)
MODE_NAMES = {"enhance": "Enhance", "spec": "Spec", "architect": "Architect",
              "skill": "Skill", "humanize": "Humanize", "grammar": "Grammar"}
MARKDOWN = ("spec", "architect", "skill")
AUTO_STEPS = [("enhance", "enhanced_prompt.md"), ("spec", "SPEC.md"), ("architect", "ARCHITECTURE.md"), ("skill", "SKILL.md")]


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


GLYPHS = {
    "l": ["██   ", " █   ", " █   ", " █   ", " █   ", " ███ "],
    "a": ["     ", " ███ ", "    █", " ████", "█   █", " ████"],
    "r": ["     ", "█ ██ ", "██  █", "█    ", "█    ", "█    "],
    "p": ["     ", "████ ", "█   █", "█   █", "████ ", "█    "],
}
LOGO_HEIGHT = 6
COL_W = 88
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
        "busy": f"bg:{BOX} #fbbf24",
        "pop": f"bg:{BOX} {_hex(h, .72, .2)}",
        "pop.sel": f"bg:{BLUE} #0a0a0a bold",
    })
    state["theme"] = name
    version[0] += 1
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


# ---------------------------------------------------------------- output log

def bump():
    version[0] += 1
    if APP:
        APP.invalidate()


def add(item):
    log.append(item)
    state["scroll"] = 0
    bump()


def render_log(width):
    key = (version[0], width, len(log))
    if cache.get("key") != key:
        buf = io.StringIO()
        c = Console(file=buf, force_terminal=True, width=width, color_system="truecolor", legacy_windows=False)
        for e in log:
            c.print(e() if callable(e) else e)
        out = buf.getvalue().rstrip("\n")
        cache.update(key=key, ansi=ANSI(out), lines=out.count("\n") + 1)
    return cache["ansi"], cache["lines"]


def log_width():
    try:
        return min(COL_W, APP.output.get_size().columns) - 1
    except Exception:
        return 80


def log_text():
    return render_log(log_width())[0]


def log_cursor():
    n = render_log(log_width())[1]
    return Point(0, max(0, n - 1 - state["scroll"]))


# ---------------------------------------------------------------- jobs

class Cancelled(Exception):
    pass


def stream_into(feature, inp, option=None):
    t = {"v": ""}
    md = feature in MARKDOWN
    title = core.FEATURES[feature]["title"]
    add(lambda: Panel(Markdown(t["v"]) if md and t["v"] else (t["v"] or "..."), title=title, border_style="green"))
    last = 0
    for chunk in core.run_stream(feature, inp, state["model"], option):
        if state["cancel"]:
            raise Cancelled()
        t["v"] += chunk
        if time.time() - last > 0.08:
            bump()
            last = time.time()
    bump()
    return t["v"].strip()


def bar(n):
    return "[" + "=" * round(n) + " " * (10 - round(n)) + "]"


def diff_text(a, b):
    t = Text()
    for tok in difflib.ndiff(a.split(), b.split()):
        if tok.startswith("- "):
            t.append(tok[2:] + " ", style="red strike")
        elif tok.startswith("+ "):
            t.append(tok[2:] + " ", style="green")
        elif tok.startswith("  "):
            t.append(tok[2:] + " ")
    return t


def run_single(feature, text, option):
    info = core.FEATURES[feature]
    if feature in ("enhance", "humanize", "grammar"):
        add(Panel(text, title="Original", border_style="red"))
    else:
        add(Text("> " + text.replace("\n", " ")[:160], style="dim"))
    result = stream_into(feature, text, option)
    state["result"] = result
    state["fname"] = option if feature == "skill" and option else info["file"]
    if info["diff"]:
        add(Panel(diff_text(text, result), title="Diff", border_style="blue"))
    if info["score"]:
        s = {"v": "Scoring..."}
        add(lambda: Text(s["v"], style="dim"))
        b, a = core.score(feature, text, state["model"]), core.score(feature, result, state["model"])
        if b and a:
            s["v"] = f"Before {bar(b)} {b:g}/10\nAfter  {bar(a)} {a:g}/10  ({a - b:+g})"
            bump()
        else:
            log.remove(log[-1])
            bump()
    add(Text("/copy  /save  /retry", style="dim"))


def run_auto(idea):
    out_dir, res = "larp_output", {"idea": idea}
    os.makedirs(out_dir, exist_ok=True)
    plan = {"enhance": ("idea", None), "spec": ("enhance", None), "architect": ("spec", None), "skill": ("spec", "SKILL.md")}
    add(Text("> " + idea.replace("\n", " ")[:160], style="dim"))
    for i, (feature, fname) in enumerate(AUTO_STEPS, 1):
        add(Text(f"Step {i}/{len(AUTO_STEPS)}: {core.FEATURES[feature]['title']}", style="bold"))
        src, option = plan[feature]
        inp = res[src] if feature != "skill" else "Create project rules for an AI coding assistant building this project:\n\n" + res[src]
        res[feature] = stream_into(feature, inp, option)
        open(os.path.join(out_dir, fname), "w", encoding="utf-8").write(res[feature])
    state["result"], state["fname"] = res["spec"], "SPEC.md"
    add(Text(f"Done. Saved {', '.join(f for _, f in AUTO_STEPS)} in the {out_dir} folder.", style="bold green"))


def job(feature, text, option):
    try:
        run_auto(text) if feature == "auto" else run_single(feature, text, option)
    except Cancelled:
        add(Text("Cancelled.", style="yellow"))
    except Exception as e:
        add(Text(f"Error talking to Ollama: {e}", style="red"))
    finally:
        state["busy"] = state["cancel"] = False
        state["online"] = ai.is_online()
        bump()


def parse_option(feature, text):
    first, _, rest = text.partition(" ")
    if feature == "humanize" and first.lower() in core.TONES:
        return first.lower(), rest.strip()
    if feature == "skill" and first in core.SKILL_FORMATS:
        return first, rest.strip()
    return None, text


def start_job(feature, text):
    if "\n" not in text and os.path.isfile(text):
        text = open(text, encoding="utf-8", errors="replace").read()
    option, text = parse_option(feature, text)
    if not text:
        add(Text(f"Mode: {MODE_NAMES.get(feature, feature)}. Type your text and press Enter.", style="dim"))
        return
    state["last"] = (feature, text, option)
    state["busy"], state["cancel"] = True, False
    threading.Thread(target=job, args=(feature, text, option), daemon=True).start()
    bump()


# ---------------------------------------------------------------- commands

def open_picker(title, items, on_select):
    state["picker"] = {"title": title, "items": items, "on_select": on_select}
    bump()


def set_model(m):
    state["model"] = m
    add(Text(f"Model set to {m}", style="dim"))


def set_theme(t):
    apply_theme(t)
    bump()


def show_help():
    t = Text()
    for cmd, _, desc, _a in COMMANDS:
        t.append(f"/{cmd:<15}", style="bold green")
        t.append(desc + "\n")
    t.append("\nEnter sends, Ctrl+J = new line, PgUp/PgDn scroll, Ctrl+C cancels.\n", style="dim")
    t.append("Tip: /humanize casual|professional <text>  and  /aiskill SKILL.md|CLAUDE.md|.cursorrules <text>", style="dim")
    add(Panel(t, title="Commands", border_style="green"))


def run_command(action, rest):
    if action in FEATURE_ACTIONS:
        state["mode"] = action
        return start_job(action, rest) if rest else add(Text(f"Mode: {MODE_NAMES[action]}. Type your text and press Enter.", style="dim"))
    if action == "auto":
        return start_job("auto", rest) if rest else add(Text("Usage: /auto <your project idea>", style="dim"))
    if action == "copy":
        if not state["result"]:
            return add(Text("Nothing to copy yet.", style="yellow"))
        try:
            pyperclip.copy(state["result"])
            add(Text("Copied to clipboard.", style="green"))
        except Exception as e:
            add(Text(f"Copy failed: {e}", style="red"))
    elif action == "save":
        if not state["result"]:
            return add(Text("Nothing to save yet.", style="yellow"))
        name = rest or state["fname"] or "output.md"
        open(name, "w", encoding="utf-8").write(state["result"])
        add(Text(f"Saved to {name}", style="green"))
    elif action == "retry":
        if state["last"]:
            f, t, o = state["last"]
            state["busy"], state["cancel"] = True, False
            threading.Thread(target=job, args=(f, t, o), daemon=True).start()
            bump()
        else:
            add(Text("Nothing to retry yet.", style="yellow"))
    elif action == "clear":
        log.clear()
        bump()
    elif action == "model":
        try:
            models = ai.list_models()
        except Exception as e:
            return add(Text(f"Cannot reach Ollama: {e}", style="red"))
        if not models:
            return add(Text("No models found on this device.\nDownload one: https://ollama.com/library\nThen run, for example: ollama pull llama3.2:3b\nRun /model again and LARP will detect it.", style="yellow"))
        open_picker("Choose model (all run offline)", [((" * " if m == state["model"] else "   ") + m, m) for m in models], set_model)
    elif action == "theme":
        if rest.lower() in THEMES:
            return set_theme(rest.lower())
        open_picker("Choose theme", [((" * " if t == state["theme"] else "   ") + t, t) for t in THEMES], set_theme)
    elif action == "help":
        show_help()
    elif action == "quit":
        APP.exit()


def submit(text):
    if state["busy"]:
        return
    if not text.startswith("/"):
        return start_job(state["mode"], text)
    name, _, rest = text[1:].partition(" ")
    cmd = find_command(name)
    if not cmd:
        return add(Text(f"Unknown command /{name}. Type / to see commands.", style="yellow"))
    run_command(cmd[1], rest.strip())


# ---------------------------------------------------------------- UI

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


def spacer_w():
    return Window(width=Dimension(weight=1))


def build_app():
    global APP
    buf = Buffer(multiline=True)
    sel = [0]
    has_log = Condition(lambda: bool(log))
    no_log = Condition(lambda: not log)

    def items():
        if state["picker"]:
            return state["picker"]["items"]
        if buf.text.startswith("/") and " " not in buf.text:
            return [(f" /{c[0]:<16}{c[2]}", c[0]) for c in matches(buf.text)]
        return []

    visible = Condition(lambda: bool(items()))

    def mode_line():
        return FormattedText([
            ("class:mode", MODE_NAMES.get(state["mode"], state["mode"])),
            ("class:dim", " · "), ("class:model", state["model"]), ("class:dim", "  local / LARP"),
        ])

    def status_line():
        if state["busy"]:
            return FormattedText([("class:busy", "● working...")])
        ok = state["online"]
        return FormattedText([("class:ok" if ok else "class:bad", "● offline-ready" if ok else "● ollama not running")])

    def footer_right():
        out = []
        if state["busy"]:
            out += [("class:foot.key", "ctrl+c"), ("class:foot.dim", " cancel")]
        else:
            if log:
                out += [("class:foot.key", "pgup/pgdn"), ("class:foot.dim", " scroll  ")]
            out += [("class:foot.key", "/"), ("class:foot.dim", " commands")]
        return FormattedText(out)

    def popup():
        its = items()
        sel[0] = max(0, min(sel[0], len(its) - 1))
        out = []
        if state["picker"]:
            out.append(("class:pop", f" {state['picker']['title']}\n"))
        for i, (label, _v) in enumerate(its):
            out += [("class:pop.sel" if i == sel[0] else "class:pop", f"{label:<44}"), ("", "\n" if i < len(its) - 1 else "")]
        return FormattedText(out)

    popup_box = ConditionalContainer(
        Window(FormattedTextControl(popup), height=Dimension(max=len(COMMANDS) + 2), style="class:pop"), filter=visible)

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
    footer = Window(FormattedTextControl(footer_right), height=1, align=WindowAlign.RIGHT)
    column = HSplit([box, popup_box, footer], width=Dimension(min=40, max=COL_W, preferred=COL_W))

    log_window = Window(FormattedTextControl(log_text, get_cursor_position=log_cursor, show_cursor=False),
                        width=Dimension(min=40, max=COL_W, preferred=COL_W))
    splash = ConditionalContainer(HSplit([
        spacer(2),
        Window(FormattedTextControl(logo_fragments), height=LOGO_HEIGHT, align=WindowAlign.CENTER),
        Window(height=2),
    ]), filter=no_log)
    log_area = ConditionalContainer(VSplit([spacer_w(), log_window, spacer_w()]), filter=has_log)

    root = HSplit([
        splash,
        log_area,
        VSplit([spacer_w(), column, spacer_w()]),
        ConditionalContainer(spacer(3), filter=no_log),
    ])

    kb = KeyBindings()

    @kb.add("enter")
    def _(e):
        if e.app.key_processor.input_queue:
            return buf.insert_text("\n")
        text = buf.text.strip()
        buf.reset()
        if text:
            submit(text)

    @kb.add("enter", filter=visible)
    def _(e):
        its = items()
        value = its[sel[0]][1]
        if state["picker"]:
            cb = state["picker"]["on_select"]
            state["picker"] = None
            buf.reset()
            cb(value)
        else:
            buf.reset()
            submit("/" + value)
        sel[0] = 0

    @kb.add("c-j")
    def _(e):
        buf.insert_text("\n")

    @kb.add("up", filter=visible)
    def _(e):
        sel[0] = max(0, sel[0] - 1)

    @kb.add("down", filter=visible)
    def _(e):
        sel[0] = min(len(items()) - 1, sel[0] + 1)

    @kb.add("tab", filter=visible)
    def _(e):
        if not state["picker"]:
            buf.text = "/" + items()[sel[0]][1] + " "
            buf.cursor_position = len(buf.text)

    @kb.add("escape", filter=visible)
    def _(e):
        state["picker"] = None
        buf.reset()

    @kb.add("pageup")
    def _(e):
        state["scroll"] += 10

    @kb.add("pagedown")
    def _(e):
        state["scroll"] = max(0, state["scroll"] - 10)

    @kb.add("c-c")
    def _(e):
        if state["busy"]:
            state["cancel"] = True
        else:
            e.app.exit()

    @kb.add("c-d")
    def _(e):
        e.app.exit()

    APP = Application(layout=Layout(root, focused_element=buf), key_bindings=kb,
                      style=DynamicStyle(lambda: STYLE), full_screen=True, refresh_interval=0.25)
    return APP


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
    state["online"] = ai.is_online()
    build_app().run()


if __name__ == "__main__":
    main()
