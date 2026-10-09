import colorsys
import difflib
import io
import os
import re
import sys
import threading
import time
from pathlib import Path

import pyperclip
from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import ANSI, FormattedText, to_formatted_text
from prompt_toolkit.formatted_text.utils import split_lines
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    BufferControl, ConditionalContainer, Dimension, FormattedTextControl, HSplit, Layout, VSplit, Window, WindowAlign,
)
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.layout.processors import HighlightSelectionProcessor, Processor, Transformation
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.mouse_events import MouseButton, MouseEventType
from prompt_toolkit.styles import DynamicStyle, Style as PtStyle

from . import ai, core, terminal

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

state = {"model": ai.DEFAULT_MODEL, "mode": "enhance", "busy": False, "cancel": False, "online": True,
         "picker": None, "files": None, "scroll": 0, "result": None, "fname": None, "last": None}
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
    ("install", "install", "Install result to a folder", ["export", "download"]),
    ("copy", "copy", "Copy last result", []),
    ("save", "save", "Save last result to file", []),
    ("retry", "retry", "Run the last task again", ["again"]),
    ("clear", "clear", "Clear the screen", ["cls"]),
    ("model", "model", "Choose AI model", ["models"]),
    ("theme", "theme", "Change color theme", ["color", "colors", "tint"]),
    ("developers", "developers", "Meet the team", ["devs", "team", "credits", "about"]),
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
CONFIG = os.path.join(os.path.expanduser("~"), ".larp_theme")


def _hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def apply_theme(name):
    global BG, BOX, BLUE, STYLE
    h, BLUE = THEMES[name]
    BG, BOX = _hsv(h, .46, .051), _hsv(h, .40, .137)
    text, dim, bright = _hsv(h, .054, .925), _hsv(h, .27, .52), _hsv(h, .016, .968)
    STYLE = PtStyle.from_dict({
        "": f"bg:{BG} {text}",
        "logo.dim": f"bg:{BG} {_hsv(h, .25, .57)} bold",
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
        "pop": f"bg:{BOX} {_hsv(h, .145, .776)}",
        "pop.sel": f"bg:{BLUE} #0a0a0a bold",
        "selected": f"bg:{BLUE} #0a0a0a",
        "scrollbar.background": f"bg:{_hsv(h, .30, .22)}",
        "scrollbar.button": f"bg:{BLUE}",
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


seg_cache = {}


def render_log(width):
    key = (version[0], width, len(log))
    if cache.get("key") != key:
        parts = []
        for e in log:
            static = not callable(e) or getattr(e, "done", False)
            hit = seg_cache.get(id(e))
            if static and hit and hit[0] == (width, state.get("theme")):
                parts.append(hit[1])
                continue
            buf = io.StringIO()
            c = Console(file=buf, force_terminal=True, width=width, color_system="truecolor", legacy_windows=False)
            c.print(e() if callable(e) else e)
            if static:
                seg_cache[id(e)] = ((width, state.get("theme")), buf.getvalue())
            parts.append(buf.getvalue())
        out = "".join(parts).rstrip("\n")
        ansi = ANSI(out)
        cache.update(key=key, ansi=ansi, lines=max(1, len(list(split_lines(to_formatted_text(ansi))))))
    return cache["ansi"], cache["lines"]


def log_width():
    try:
        return min(COL_W, APP.output.get_size().columns) - 1
    except Exception:
        return 80


frame = {"lines": 1}


def log_text():
    ansi, frame["lines"] = render_log(log_width())
    return ansi


view = {"win": None, "dir": 1}


def view_height():
    info = view["win"].render_info if view["win"] else None
    return info.window_height if info else 20


def scroll_by(delta):
    state["scroll"] = max(0, state["scroll"] + delta)
    view["dir"] = 1 if delta > 0 else -1
    bump()


def log_cursor():
    n, h = frame["lines"], view_height()
    state["scroll"] = s = min(state["scroll"], max(0, n - h))
    if s == 0:
        y = n - 1
    else:
        top = n - h - s
        y = top if view["dir"] > 0 else top + h - 1
    return Point(0, max(0, min(y, n - 1)))


def paste_clipboard():
    if time.time() - view.get("pasted", 0) < 0.4 or state["busy"] or not view.get("buf"):
        return
    view["pasted"] = time.time()
    try:
        text = pyperclip.paste()
    except Exception:
        return
    text = text.replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    if text:
        view["buf"].insert_text(text)
        bump()


def is_right_click(mouse_event):
    return mouse_event.button == MouseButton.RIGHT and mouse_event.event_type == MouseEventType.MOUSE_DOWN


class PasteText(FormattedTextControl):
    def mouse_handler(self, mouse_event):
        if is_right_click(mouse_event):
            return paste_clipboard()
        return NotImplemented


class PasteBuffer(BufferControl):
    def mouse_handler(self, mouse_event):
        if is_right_click(mouse_event):
            return paste_clipboard()
        return super().mouse_handler(mouse_event)


class LogControl(FormattedTextControl):
    def mouse_handler(self, mouse_event):
        if is_right_click(mouse_event):
            return paste_clipboard()
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            scroll_by(3)
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            scroll_by(-3)
        else:
            return NotImplemented


# ---------------------------------------------------------------- jobs

class Cancelled(Exception):
    pass


def stream_into(feature, inp, option=None):
    t = {"v": "", "note": ""}
    md = feature in MARKDOWN
    title = core.FEATURES[feature]["title"]

    def entry():
        rich_md = md and t["v"] and (entry.done or len(t["v"]) < 12000)
        return Panel(Markdown(t["v"]) if rich_md else (t["v"] or "..."), title=title, subtitle=t["note"] or None, border_style=BLUE)

    entry.done = False

    def status(msg):
        t["note"] = msg
        bump()

    add(entry)
    last = 0
    for chunk in core.run_stream(feature, inp, state["model"], option, status):
        if state["cancel"]:
            raise Cancelled()
        t["v"] += chunk
        if time.time() - last > min(1.0, 0.12 + len(t["v"]) / 60000):
            bump()
            last = time.time()
    t["note"] = ""
    entry.done = True
    bump()
    return t["v"].strip()


def preview(text, lines=12, chars=1200):
    nl = chr(10)
    shown = nl.join(text.splitlines()[:lines])[:chars]
    if len(shown) < len(text.rstrip()):
        shown += f"{nl}... ({len(text) - len(shown):,} more characters, {len(text.split()):,} words in total)"
    return shown


def diff_text(a, b):
    wa, wb = a.split(), b.split()
    if max(len(wa), len(wb)) > 4000:
        return Text("Diff skipped: the text is too long to compare word by word.", style="dim")
    t = Text()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes():
        if tag == "equal":
            t.append(" ".join(wa[i1:i2]) + " ")
            continue
        if tag in ("delete", "replace"):
            t.append(" ".join(wa[i1:i2]) + " ", style="red strike")
        if tag in ("insert", "replace"):
            t.append(" ".join(wb[j1:j2]) + " ", style="green")
    return t


def run_single(feature, text, option):
    info = core.FEATURES[feature]
    if feature in ("enhance", "humanize", "grammar"):
        add(Panel(preview(text), title=f"Original ({len(text):,} characters)" if len(text) > 1200 else "Original", border_style="red"))
    else:
        add(Text("> " + " ".join(text.split())[:160], style="dim"))
    result = stream_into(feature, text, option)
    state["result"] = result
    state["fname"] = option if feature == "skill" and option else info["file"]
    if info["diff"]:
        d = diff_text(text, result)
        add(lambda: Panel(d, title="Diff", border_style=BLUE))
    state["files"] = [(state["fname"], result)]
    add(Text("/install  /copy  /save  /retry", style="dim"))


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
    state["files"] = [(fname, res[feature]) for feature, fname in AUTO_STEPS]
    add(lambda: Text(f"Done. Saved {', '.join(f for _, f in AUTO_STEPS)} in the {out_dir} folder.", style=f"bold {BLUE}"))


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


WORD_LIMIT = 3000


def trim_words(text, limit=None):
    """Return (text cut after `limit` words, whether it was cut)."""
    limit = limit or WORD_LIMIT
    for i, m in enumerate(re.finditer(r"\S+", text), 1):
        if i == limit + 1:
            return text[:m.start()].rstrip(), True
    return text, False


def enforce_limit(b):
    if len(b.text) > WORD_LIMIT:
        cut, trimmed = trim_words(b.text)
        if trimmed:
            b.document = Document(cut, len(cut))
            view["limit_hit"] = time.time()


def word_count(text):
    return len(text.split())


def start_job(feature, text):
    if "\n" not in text and os.path.isfile(text):
        text = open(text, encoding="utf-8", errors="replace").read()
    text, trimmed = trim_words(text)
    if trimmed:
        add(Text(f"Input trimmed to the first {WORD_LIMIT:,} words.", style="yellow"))
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


def unique_path(p):
    i = 2
    cand = p
    while cand.exists():
        cand = p.with_name(f"{p.stem}-{i}{p.suffix}")
        i += 1
    return cand


def install_files(dest):
    files = state["files"]
    base = Path(os.path.expanduser(str(dest).strip().strip('"')))
    is_file = len(files) == 1 and (base.suffix or base.name.startswith(".")) and not base.is_dir()
    try:
        for fname, text in files:
            target = unique_path((base if is_file else base / fname).absolute())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text + chr(10), encoding="utf-8")
            add(Text(f"Installed to {target}", style="green"))
    except OSError as e:
        add(Text(f"Could not install there: {e}", style="red"))


def open_install(rest=""):
    if not state["files"]:
        return add(Text("Nothing to install yet. Run a feature first, like /enhanceprompt or /aiskill.", style="yellow"))
    if rest:
        return install_files(rest)
    home = Path.home()
    spots = [("This folder", Path.cwd()), ("Desktop", home / "Desktop"), ("Downloads", home / "Downloads"), ("Documents", home / "Documents")]
    items = [(f"   {name:<12}{path}", str(path)) for name, path in spots if path.is_dir()]
    names = ", ".join(f for f, _ in state["files"])
    open_picker(f"Install {names} to... (or type /install <any folder>)", items, install_files)


def set_model(m):
    state["model"] = m
    add(Text(f"Model set to {m}", style="dim"))


def set_theme(t):
    apply_theme(t)
    bump()


TEAM = "Grow A Garden Trading Hub"
DEVELOPERS = ["Carlos Alcantara", "Zian Kyle Piangco", "Paulo Mendoza", "Joshua Enriquez"]


def show_developers():
    def build():
        t = Text(justify="center")
        t.append("LARP\n", style=f"bold {BLUE}")
        t.append("Local AI Refinement Platform\n\n", style="dim")
        t.append("TEAM\n", style="dim")
        t.append(f"{TEAM}\n\n", style=f"bold {BLUE}")
        t.append("DEVELOPERS\n", style="dim")
        for name in DEVELOPERS:
            t.append("- ", style=BLUE)
            t.append(f"{name}\n", style="bold")
        t.rstrip()
        return Panel(Align.center(t), title="Developers", border_style=BLUE, padding=(1, 4))
    add(build)


def show_help():
    def build():
        t = Text()
        for cmd, _, desc, _a in COMMANDS:
            t.append(f"/{cmd:<15}", style=f"bold {BLUE}")
            t.append(desc + "\n")
        t.append("\nEnter sends, Ctrl+J = new line, Tab completes, PgUp/PgDn scroll, Ctrl+C cancels.\n", style="dim")
        t.append("Tip: /humanize casual|professional <text>  and  /aiskill SKILL.md|CLAUDE.md|.cursorrules <text>", style="dim")
        return Panel(t, title="Commands", border_style=BLUE)
    add(build)


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
        add(Text(f"Saved to {os.path.abspath(name)}", style="green"))
    elif action == "retry":
        if state["last"]:
            f, t, o = state["last"]
            state["busy"], state["cancel"] = True, False
            threading.Thread(target=job, args=(f, t, o), daemon=True).start()
            bump()
        else:
            add(Text("Nothing to retry yet.", style="yellow"))
    elif action == "install":
        open_install(rest)
    elif action == "clear":
        log.clear()
        seg_cache.clear()
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
    elif action == "developers":
        show_developers()
    elif action == "help":
        show_help()
    elif action == "quit":
        state["close_terminal"] = True
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
            return Transformation([("class:placeholder", f"{PLACEHOLDER}  (max {WORD_LIMIT:,} words)")])
        return Transformation(ti.fragments)


def spacer(weight=1):
    return Window(height=Dimension(weight=weight))


def spacer_w():
    return Window(width=Dimension(weight=1))


def build_app():
    global APP
    buf = Buffer(multiline=True, on_text_changed=enforce_limit)
    view["buf"] = buf
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

    def counter_parts():
        n = word_count(buf.text)
        if not n:
            return None
        full = n >= WORD_LIMIT or time.time() - view.get("limit_hit", 0) < 3
        style = "class:bad" if full else ("class:busy" if n >= WORD_LIMIT * 0.9 else "class:dim")
        return style, f"{n:,} / {WORD_LIMIT:,} words" + ("  limit reached" if full else "") + "  "

    def counter_line():
        parts = counter_parts()
        return FormattedText([parts] if parts else [])

    def counter_width():
        parts = counter_parts()
        return Dimension.exact(len(parts[1]) if parts else 0)

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
                out += [("class:foot.key", "wheel/pgup/pgdn"), ("class:foot.dim", " scroll  ")]
            out += [("class:foot.key", "tab"), ("class:foot.dim", " switch mode  "),
                    ("class:foot.key", "/"), ("class:foot.dim", " commands")]
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
        Window(PasteBuffer(buf, input_processors=[HighlightSelectionProcessor(), Placeholder()]), wrap_lines=True, style="class:box",
               right_margins=[ScrollbarMargin(display_arrows=False)],
               height=lambda: Dimension(min=1, max=8, preferred=max(1, buf.document.line_count))),
        Window(height=1, style="class:box"),
        VSplit([
            Window(FormattedTextControl(mode_line), height=1, style="class:box"),
            Window(FormattedTextControl(counter_line), height=1, width=counter_width, align=WindowAlign.RIGHT, style="class:box"),
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

    log_window = Window(LogControl(log_text, get_cursor_position=log_cursor, show_cursor=False),
                        right_margins=[ScrollbarMargin(display_arrows=False)],
                        width=Dimension(min=40, max=COL_W, preferred=COL_W))
    view["win"] = log_window
    splash = ConditionalContainer(HSplit([
        spacer(2),
        Window(PasteText(logo_fragments), height=LOGO_HEIGHT, align=WindowAlign.CENTER),
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

    selecting = Condition(lambda: buf.selection_state is not None)

    @kb.add("c-a")
    def _(e):
        buf.exit_selection()
        buf.cursor_position = 0
        buf.start_selection(selection_type=SelectionType.CHARACTERS)
        buf.cursor_position = len(buf.text)

    @kb.add("backspace", filter=selecting, eager=True)
    @kb.add("c-h", filter=selecting, eager=True)
    @kb.add("delete", filter=selecting, eager=True)
    def _(e):
        buf.cut_selection()

    @kb.add("<any>", filter=selecting)
    def _(e):
        data = e.data
        if len(data) == 1 and data.isprintable():
            buf.cut_selection()
            buf.insert_text(data)

    def move_clearing(action):
        def handler(e):
            buf.exit_selection()
            action()
        return handler

    kb.add("left", filter=selecting)(move_clearing(lambda: buf.cursor_left()))
    kb.add("right", filter=selecting)(move_clearing(lambda: buf.cursor_right()))
    kb.add("up", filter=selecting)(move_clearing(lambda: buf.cursor_up()))
    kb.add("down", filter=selecting)(move_clearing(lambda: buf.cursor_down()))

    @kb.add("escape", filter=selecting, eager=True)
    def _(e):
        buf.exit_selection()

    @kb.add("c-j")
    def _(e):
        buf.insert_text("\n")

    def cycle(step):
        def handler(e):
            if not state["busy"]:
                state["mode"] = FEATURE_ACTIONS[(FEATURE_ACTIONS.index(state["mode"]) + step) % len(FEATURE_ACTIONS)]
        return handler

    kb.add("tab")(cycle(1))
    kb.add("s-tab")(cycle(-1))

    def move(step):
        sel[0] = (sel[0] + step) % len(items())

    @kb.add("up", filter=visible)
    @kb.add("s-tab", filter=visible)
    def _(e):
        move(-1)

    @kb.add("down", filter=visible)
    def _(e):
        move(1)

    def complete(e):
        if state["picker"]:
            return move(1)
        buf.document = Document("/" + items()[sel[0]][1] + " ")
        buf.cursor_position = len(buf.text)
        sel[0] = 0

    kb.add("tab", filter=visible)(complete)
    kb.add("c-i", filter=visible)(complete)
    kb.add("right", filter=visible & Condition(lambda: not state["picker"] and buf.cursor_position >= len(buf.text)))(complete)

    @kb.add("escape", filter=visible)
    def _(e):
        state["picker"] = None
        buf.reset()

    @kb.add("pageup")
    def _(e):
        scroll_by(max(3, view_height() - 2))

    @kb.add("pagedown")
    def _(e):
        scroll_by(-max(3, view_height() - 2))

    @kb.add("c-up")
    def _(e):
        scroll_by(1)

    @kb.add("c-down")
    def _(e):
        scroll_by(-1)

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
                      style=DynamicStyle(lambda: STYLE), full_screen=True, mouse_support=True, refresh_interval=0.25)
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
    if state.get("close_terminal"):
        terminal.close_terminal()


if __name__ == "__main__":
    main()
