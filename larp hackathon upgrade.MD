# LARP v3: Menu Version (Hackathon Plan)

> Same five features, but now you just **pick options from a menu**, like OpenCode. No commands to remember. The local AI does the rest.

---

## 1. The idea in one sentence

**LARP is an offline, menu-driven AI toolbox. Open it, pick what you want to do with the arrow keys, paste your text, and a local AI improves it. It also shows a score so you can see the improvement.**

---

## 2. How it feels to use

You type one word to open it:

```
larp
```

Then you see a menu:

```
  LARP: Local AI Refinement Platform      🔒 Offline

  What do you want to do?

   ❯ ✨ Enhance a prompt
     📋 Make a project spec
     🧩 Make an AI skill
     🗣️  Humanize text
     ✍️  Fix grammar
     ⚙️  Settings (choose AI model)
     ❌ Quit
```

You press **Enter** on one, and it walks you through:

1. **Give your text:** type or paste it, or load it from the clipboard or a file
2. **Pick options** (only when needed): tone (casual / professional), length (short / detailed), save format for skills
3. **Wait a few seconds** while a spinner shows the AI working
4. **See the result** with a before/after score and a colored diff
5. **Pick what to do next:** Copy · Save to file · Try again · Back to menu

That's the whole product.

---

## 3. The five features (all in the menu)

| Menu option | What it does in plain words |
|---|---|
| ✨ **Enhance a prompt** | Rewrites a weak, vague prompt so the AI knows exactly what you want |
| 📋 **Make a project spec** | Turns a one-line idea into a proper project plan |
| 🧩 **Make an AI skill** | Creates a reusable rulebook an AI can follow every time, and saves it as a real file |
| 🗣️ **Humanize text** | Makes stiff, robotic text sound like a real person wrote it |
| ✍️ **Fix grammar** | Fixes spelling, grammar and punctuation without changing the meaning |

**Bonus for power users:** the same things also work as direct commands (`larp enhance "..."`) if someone prefers typing.

---

## 4. What makes it demo-worthy

1. **The menu itself:** looks like a real product, not a script
2. **Before/after score:** "3/10 → 9/10" with bars, so judges see the value instantly
3. **Colored diff:** removed words in red, added words in green
4. **Skill export:** saves a real file (`SKILL.md`, `CLAUDE.md` or `.cursorrules`) that works in AI coding tools
5. **Offline proof:** a 🔒 badge on screen, and Wi-Fi turned off live during the demo

*Note: small local models can be unreliable at scoring. Ask for a number only and use a fallback if the answer isn't a number.*

---

## 5. Built with (simple version)

- **Python:** runs everything
- **Ollama:** runs the AI on your laptop
- **A small local model** (like Llama or Mistral)
- **`questionary`:** the arrow-key menus
- **`rich`:** colors, score bars, spinner, nice-looking output
- **`difflib`:** the colored before/after diff (built into Python)
- **`pyperclip`:** copy to clipboard (optional)

How it flows:

```
Open larp → pick an option from the menu
        ↓
Paste your text (+ pick any options)
        ↓
LARP adds hidden instructions for that feature
        ↓
Local AI (Ollama) does the work
        ↓
Result + score + diff → Copy / Save / Retry / Back
```

Each feature is the same program with a **different set of hidden instructions**. The prompt writer's job decides how good the results are.

---

## 6. Folder layout

```
larp/
├── larp.py            ← starts the app, shows the main menu
├── menu.py            ← arrow-key menus and the "what next?" screen
├── ai.py              ← talks to Ollama
├── features/
│   ├── enhance.py
│   ├── spec.py
│   ├── skill.py
│   ├── humanize.py
│   └── grammar.py
├── prompts/           ← hidden instructions for each feature
├── ui.py              ← score bars, diff, spinner, offline badge
└── README.md
```

---

## 7. Priority order

| Priority | Item | Why |
|---|---|---|
| 1 | Ollama connection + `enhance` working | Everything depends on it |
| 2 | Main menu + the "what next?" screen | Makes it feel like a product |
| 3 | Before/after score | The wow factor |
| 4 | `spec` and `skill` (with file save) | Shows range and real value |
| 5 | Colored diff | Makes results visible |
| 6 | `humanize` and `grammar` | Quick wins, just new instructions |
| 7 | Offline badge + settings (pick model) | Cheap and convincing |

If time runs short, cut the settings screen, never the score.

---

## 8. 3-hour schedule

| Time | What to do |
|---|---|
| **0:00 to 0:30** | Install Python + Ollama, download a small model, confirm it answers |
| **0:30 to 1:00** | Build `enhance` as a plain function, then wrap it in the menu |
| **1:00 to 1:30** | Add before/after score + spinner + "what next?" screen |
| **1:30 to 2:10** | Add `spec` and `skill` (with file export) |
| **2:10 to 2:30** | Add `humanize` and `grammar` + colored diff |
| **2:30 to 2:50** | Offline badge, then test everything with Wi-Fi OFF |
| **2:50 to 3:00** | Rehearse the demo once |

---

## 9. Team of four

1. **Builder:** Ollama connection and the feature functions
2. **Menu + polish person:** menus, score bars, diff, spinner, offline badge
3. **Prompt writer:** hidden instructions for all five features, plus the scoring prompt
4. **Tester + presenter:** offline testing, demo inputs, the pitch

---

## 10. 2-minute demo script

1. **(10 sec) Hook:** "Most people get bad AI answers because they write bad prompts."
2. **(15 sec) Turn Wi-Fi OFF** on screen. "Everything runs on this laptop."
3. **(30 sec) Open LARP, pick Enhance:** paste "make me a good portfolio". Show the score jump and the diff.
4. **(20 sec) Spec:** one-line idea becomes a project plan.
5. **(20 sec) Skill:** generate a rules file and save it.
6. **(15 sec) Humanize + Grammar:** quick before/after.
7. **(10 sec) Close:** "Private, free, offline. Your ideas never leave your laptop."

**Tip:** pre-test your demo inputs and don't improvise on stage.

---

## 11. 30-second pitch

> "Everyone uses AI, but most people get weak results because their instructions are weak and their writing sounds robotic. LARP is a private AI toolbox that runs fully offline. Open it, pick an option, and it enhances your prompts, writes project specs, builds reusable AI skills, humanizes text and fixes grammar, and it shows you a score so you can see the improvement. No internet, no accounts, no data leaving your laptop."

---

## 12. Possible judge questions

- **"Why not just use ChatGPT?"** → Privacy, offline use, no cost, and it exports ready-to-use files.
- **"Is this like OpenCode?"** → Similar style of menu-driven interface, but OpenCode is a coding agent. LARP is focused on improving text and instructions, and works fully offline.
- **"Is the score accurate?"** → It's a quick guide from the local model, not a scientific measure. Say so honestly.
- **"What's next?"** → Saved history, more models, a desktop app, shared skill libraries for teams.

---

## 13. Final checklist

- [ ] Wi-Fi OFF and everything still works
- [ ] All five menu options work
- [ ] Score bars and diff show up
- [ ] `skill` saves a real file
- [ ] Copy / Save / Retry / Back all work
- [ ] Demo inputs tested ahead of time
- [ ] One person runs the demo, everyone knows the pitch

---

## 14. Golden rule

**Build the menu around one feature that works perfectly (Enhance) first. Then add the others one at a time.**
