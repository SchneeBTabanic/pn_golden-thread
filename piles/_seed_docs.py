#!/usr/bin/env python3
"""One-shot that birthed piles/docs.txt. Kept as a worked example.

Reusable converter (any markdown → pile):

    python3 ../../pn_scribe-wb/md_to_pile.py notes.md --append pile.txt \\
        --source self --tag aspect:manifested --name-from-heading

This file is the custom capture (hand-chosen @act/@path/@part per block).
md_to_pile.py is the generic split-and-capture. Do not overwrite docs.txt
with this script — it refuses if the pile already exists.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs.txt")
SCRIBE = os.path.normpath(os.path.join(
    os.path.dirname(HERE), "..", "pn_scribe-wb", "scribe.py"))


def cap(body, tags):
    cmd = [sys.executable, SCRIBE, "capture", "--append", DOCS, "--source", "grok"]
    for k, v in tags:
        cmd.extend(["--tag", f"{k}:{v}"])
    p = subprocess.run(cmd, input=body if body.endswith("\n") else body + "\n",
                       text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr or p.stdout or "capture failed")
    print(p.stderr.strip().splitlines()[0] if p.stderr else "ok")


if os.path.exists(DOCS):
    raise SystemExit("piles/docs.txt already exists — will not overwrite")

common = [
    ("origin", "ai"),
    ("aspect", "manifested"),
    ("continues", "user-docs"),
    ("defers", "sovereign"),
    ("topic", "guide"),
]

cap(
    "USER DOCS. This pile is the booklet. Flat .md copies, if any, are "
    "derived views — disposable. Read with:\n\n"
    "  python3 show_docs.py start\n"
    "  python3 show_docs.py talk\n"
    "  python3 show_docs.py toc\n\n"
    "Or: scribe view part:how-to-talk piles/docs.txt\n\n"
    "Do not grow a second canon in README prose. Amend a block, or capture "
    "a new one with @part: and @continues:user-docs.",
    common + [
        ("act", "hold-the-user-docs"),
        ("path", "toward-text-driving-the-record"),
        ("part", "doorway"),
        ("name", "docs-charter"),
        ("enables", "find-the-booklet"),
        ("carries", "the-user-docs"),
        ("kept", "foundation"),
    ],
)

cap(
    "ONE PROGRAM. You talk in run.py. That is the main program we built.\n\n"
    "prove_the_outside.py is a self-test. It pretends to be you for half a "
    "minute, then exits. Never leave it running next to run.py. They do not "
    "talk to each other. run.py writes piles/turns.txt. The self-test writes "
    "a throwaway diary and leaves it.\n\n"
    "This part (how-to-start) is which file to start. The other part "
    "(how-to-talk) is what a turn feels like versus the old agent.py.\n\n"
    "Room A: ordinary talk. No costume on the model's mouth.",
    common + [
        ("act", "show-which-program-to-run"),
        ("path", "toward-one-conversation"),
        ("part", "how-to-start"),
        ("name", "one-program"),
        ("enables", "start-the-right-file"),
    ],
)

cap(
    "OPTIONAL SELF-TEST. Server must already be up.\n\n"
    "  cd pn_golden-thread\n"
    "  python3 prove_the_outside.py\n\n"
    "You want the last lines to say PROOF HELD.\n\n"
    "That script: (1) a bare question → FETCHED: none (2) file: of a small "
    "test file → FETCHED: that path (last good run also quoted ALPHA-PLACED) "
    "(3) /shape → a scar-note that is not the next answer.\n\n"
    "FAIL — no local model means start the server first.\n"
    "This is not 'the model is wise.' It is 'the diary and the clock work "
    "without you being the clerk.' Then go back to run.py.",
    common + [
        ("act", "show-the-self-test"),
        ("path", "toward-a-proof-he-can-rerun"),
        ("part", "how-to-start"),
        ("name", "self-test"),
        ("enables", "press-the-proof"),
    ],
)

cap(
    "START THE MODEL, THEN THE TALK.\n\n"
    "The engine is a compiled binary at\n"
    "/mnt/data/Codeberg/llama_server_build/bin/llama-server\n"
    "It is not on PATH and it is not in this directory. Typing `llama-server`\n"
    "here fails with command not found. That is the whole mystery.\n\n"
    "From this directory:\n\n"
    "  ./scripts/run_llama_server.sh\n\n"
    "Default: granite-3.3-2b-Q4_K_M, port 8080 (what run.py looks for).\n\n"
    "Pick a model and a port (CLI flags or env vars; both work):\n\n"
    "  ./scripts/run_llama_server.sh -m /mnt/data/models/granite-3.3-8b-Q4_K_M.gguf --port 8080 -c 4096\n\n"
    "  MODEL=/mnt/data/models/granite-3.3-8b-Q4_K_M.gguf CTX=4096 ./scripts/run_llama_server.sh\n\n"
    "Stop the 2B first. One card, one model. The 8B Q4 is ~4.7 GB on a 6 GB\n"
    "P3000; 4096 context is the safer start. CUDA OOM → drop -c or NGL.\n\n"
    "Optional: export PATH=\"/mnt/data/Codeberg/llama_server_build/bin:\$PATH\"\n"
    "and then the bare name works from any directory. Not required.\n"
    "Also fine: ollama serve (and a model pulled).\n\n"
    "Then in another terminal:\n"
    "  cd /mnt/data/project-namirha_grok-build/pn_golden-thread\n"
    "  python3 run.py\n\n"
    "You should see: Room A — unmasked. FETCHED is a clock. you @ turn 1 ›\n"
    "Type there. Leave with /exit.\n"
    "If nothing is listening, it refuses to pretend.",
    common + [
        ("act", "show-how-to-start-the-talk"),
        ("path", "toward-the-front-door"),
        ("part", "how-to-start"),
        ("name", "start-the-talk"),
        ("enables", "reach-the-prompt"),
    ],
)

cap(
    "JUST TALK.\n\n"
    "  you @ turn 1 › What is 2 + 2?\n\n"
    "The answer prints in the main window. On the side, one line:\n"
    "  FETCHED: none\n\n"
    "This turn, no file was placed. Clock, not a warning. Do nothing.\n"
    "The model may ramble. That is Room A being honest. Say 'stop after "
    "one sentence' or type /forget (the diary is not deleted).",
    common + [
        ("act", "show-a-bare-turn"),
        ("path", "toward-ordinary-talk"),
        ("part", "how-to-start"),
        ("name", "just-talk"),
        ("enables", "read-the-clock"),
    ],
)

cap(
    "PUT A REAL FILE IN FRONT OF IT.\n\n"
    "  you @ turn 2 › file: tests/fixture_place.txt What is the first line?\n"
    "  you @ turn 2 › file: /home/schnee/notes/meeting.txt Summarise what we decided.\n\n"
    "The whole file is placed, or the program REFUSES (missing, too big, "
    "a folder, binary). Nothing is silently half-read.\n"
    "Clock: FETCHED: /full/path/to/that/file\n"
    "If the answer ignores the file, you can see it: looked up, then not used.\n"
    "Paths with spaces: file: \"/home/schnee/My Notes/draft.txt\" What is the title?",
    common + [
        ("act", "show-how-to-place-a-file"),
        ("path", "toward-live-evidence-in-the-window"),
        ("part", "how-to-start"),
        ("name", "place-a-file"),
        ("enables", "put-evidence-in"),
    ],
)

cap(
    "ASK FOR SHAPE (optional).\n\n"
    "  you @ turn 4 › /shape\n\n"
    "The model looks at the last turn and piles/story.txt (you may edit "
    "that file). Testimony, not a verdict. Do not treat 'none' as a green "
    "light.\n\n"
    "  you @ turn 5 › /shape topic:turn\n"
    "  you @ turn 6 › /shape act:place-a-file\n\n"
    "You named the group. The program glued. The model only spoke.\n"
    "A group that does not exist is refused. Nothing sneaky.",
    common + [
        ("act", "show-how-to-ask-for-shape"),
        ("path", "toward-spoken-form-when-asked"),
        ("part", "how-to-start"),
        ("name", "ask-for-shape"),
        ("enables", "summon-shape"),
    ],
)

cap(
    "THE DIARY. Written for you to piles/turns.txt. You can ignore the file.\n\n"
    "/pile — where it is, and its birth name (辻…)\n"
    "/views — contents by what each entry does and reaches toward\n"
    "/history — what the model will be shown (a view, not the diary)\n"
    "/forget — fresh window for the next answers; diary not erased\n"
    "/model — which server, asked of the machine\n"
    "/help — the short list\n"
    "/exit — stop\n\n"
    "/forget is start-the-window-fresh, not burn-the-notebook.",
    common + [
        ("act", "show-the-diary-commands"),
        ("path", "toward-minutes-without-bookkeeping"),
        ("part", "how-to-start"),
        ("name", "diary-commands"),
        ("enables", "peek-at-the-minutes"),
    ],
)

cap(
    "A TINY WORKED AFTERNOON.\n\n"
    "1. Start llama-server or Ollama.\n"
    "2. cd pn_golden-thread && python3 run.py\n"
    "3. What did we decide about backups? → FETCHED: none\n"
    "4. file: /path/to/your/notes.txt Answer only from this file. → FETCHED: that path\n"
    "5. /shape if you want the scar-reading\n"
    "6. /views if you want the minutes grouped\n"
    "7. /exit\n\n"
    "Three things: talk; file: when it must be this document; FETCHED: is the clock.",
    common + [
        ("act", "show-a-worked-afternoon"),
        ("path", "toward-using-it-today"),
        ("part", "how-to-start"),
        ("name", "worked-afternoon"),
        ("enables", "copy-a-session"),
    ],
)

cap(
    "WHAT YOU DO NOT HAVE TO DO.\n\n"
    "You do not start scribe by hand for ordinary work.\n"
    "You do not tag turns.\n"
    "You do not run run_tests.py for daily use. Daily use is run.py only.\n"
    "prove_the_outside.py is an optional self-test.\n"
    "You do not turn /skin on. Room A is the conversation.\n\n"
    "WHEN TO STILL USE YOUR EYES. The clock says whether something was "
    "looked up, not whether the answer is true. Still read the sentence "
    "when a quote will matter, when live weather was not placed, when the "
    "model sounds sure and FETCHED: none.\n\n"
    "You stop being unable to see that nothing was looked up. You do not "
    "retire thinking.",
    common + [
        ("act", "show-what-he-need-not-do"),
        ("path", "away-from-being-the-clerk"),
        ("part", "how-to-start"),
        ("name", "need-not-do"),
        ("preserves", "his-own-eye"),
    ],
)

cap(
    "IS IT BROKEN?\n\n"
    "FETCHED: none after a chat question — normal. No file this turn.\n"
    "FETCHED: /some/path after file: — normal. That file was placed whole.\n"
    "file: REFUSED … does not exist — wrong path. Nothing half-read.\n"
    "Model invents extra questions — Room A. /forget or tell it to stop.\n"
    "PROOF HELD — the outside worked.\n"
    "FAIL — no local model — start llama-server or Ollama.\n"
    "/shape produced nothing — that key:value matches no diary entry yet.",
    common + [
        ("act", "show-what-broken-usually-is"),
        ("path", "away-from-false-alarms"),
        ("part", "how-to-start"),
        ("name", "is-it-broken"),
        ("enables", "name-the-symptom"),
    ],
)

# --- how-to-talk ---
cap(
    "HOW YOU ENGAGE. This part is the conversation, not which file to start.\n\n"
    "  python3 run.py\n\n"
    "you @ turn 1 › is the whole front door.",
    common + [
        ("act", "open-the-engagement-booklet"),
        ("path", "toward-a-different-kind-of-talk"),
        ("part", "how-to-talk"),
        ("name", "engagement-door"),
        ("enables", "begin-the-talk-booklet"),
    ],
)

cap(
    "THE OLD AGENT, IN ONE PICTURE.\n\n"
    "agent.py (GTPS-Agent) tried to be a governed partner:\n"
    "- clause text or skills stuffed into the window ('behave like this')\n"
    "- file: often went through a picker of passages, not always the whole file\n"
    "- a second voice (Proxy) often sat in the chair, or its notes were saved "
    "as if they were the answer\n"
    "- extra meters (fatigue, health, 'clear') spoke a lot and went numb\n"
    "- continuity was partly a hope that the model 'still had the thread'\n\n"
    "A lot of machinery between you and the sentence.",
    common + [
        ("act", "name-the-old-engagement"),
        ("path", "away-from-the-nanny-between-you"),
        ("part", "how-to-talk"),
        ("name", "old-agent-picture"),
        ("rejected", "proxy-as-the-face"),
        ("rejected", "clause-injection-as-talk"),
    ],
)

cap(
    "THIS PROGRAM, IN ONE PICTURE.\n\n"
    "run.py is you and one model, plus a clerk who does not speak in the answer.\n\n"
    "  you type\n"
    "      → the model answers   (the conversation — the main window)\n"
    "      → one clock line      FETCHED: none  or  FETCHED: /the/file\n"
    "      → the clerk files the minutes  (you do not)\n\n"
    "No clause pack. No Proxy as the face. No picker on file:. No dashboard.\n"
    "/shape is a second glance at form. That glance is not the next answer.",
    common + [
        ("act", "name-this-engagement"),
        ("path", "toward-talk-plus-a-clock"),
        ("part", "how-to-talk"),
        ("name", "this-program-picture"),
        ("enables", "see-the-three-steps"),
    ],
)

cap(
    "A BARE TURN. you @ turn 1 › What did we say about the backup last week?\n\n"
    "You get an answer. The clock says FETCHED: none.\n"
    "Read that as: nothing from disk was placed; this is the model talking. "
    "Same kind of fact as 'no attachment on this email.' Not a scolding.\n"
    "The model may wander. Say 'one sentence only' or /forget (diary kept).",
    common + [
        ("act", "show-what-a-bare-turn-feels-like"),
        ("path", "toward-believing-the-clock"),
        ("part", "how-to-talk"),
        ("name", "bare-turn-feel"),
    ],
)

cap(
    "EVIDENCE IN THE ROOM. When it must be this document:\n\n"
    "  you @ turn 2 › file: /home/schnee/notes/backup.txt What did we decide?\n\n"
    "The whole file is placed, or the program refuses. Clock: FETCHED: that path.\n"
    "The model can still ignore the file. Now you can see the mismatch.\n"
    "You are not hoping a retriever chose the right paragraph. You pointed.",
    common + [
        ("act", "show-what-placing-evidence-feels-like"),
        ("path", "toward-pointing-not-hoping"),
        ("part", "how-to-talk"),
        ("name", "evidence-in-the-room"),
        ("enables", "place-when-it-counts"),
    ],
)

cap(
    "THREE JOBS. Only one is the chat.\n\n"
    "Talk / meaning — the model — type questions; read the answer as talk.\n"
    "Look-up — you + file: — when it must be a real document; watch the clock.\n"
    "Minutes — the clerk — nothing. The diary writes itself. /views if curious.\n\n"
    "The old agent tried to make the model do all three at once. That is why "
    "it felt like sparring.\n"
    "Here: meaning stays in the talk; evidence enters when you place it; "
    "memory that does not fade into the weights is the diary.\n"
    "Benefit: file: when the sentence will matter; believe the clock more "
    "than a confident tone.",
    common + [
        ("act", "split-the-three-jobs"),
        ("path", "away-from-one-voice-doing-everything"),
        ("part", "how-to-talk"),
        ("name", "three-jobs"),
        ("carries", "the-engagement"),
    ],
)

cap(
    "COMMANDS YOU WILL ACTUALLY USE.\n\n"
    "Daily: a normal sentence; file: /path/to/file.txt plus a question; "
    "/shape; /forget; /exit.\n"
    "Sometimes: /history; /views; /pile; /help.\n"
    "Drawer unless you have a reason: /skin /law /raw.",
    common + [
        ("act", "list-the-daily-commands"),
        ("path", "toward-a-small-mouth"),
        ("part", "how-to-talk"),
        ("name", "daily-commands"),
        ("enables", "type-without-a-manual"),
    ],
)

cap(
    "SIDE BY SIDE WITH agent.py.\n\n"
    "Who you talk to — old: often a Proxy / mixed voices — now: the model answering.\n"
    "Law in the window — old: clauses/skills pasted — now: none unless you file: a document.\n"
    "A file — old: often picked-apart — now: whole or refused.\n"
    "After the answer — old: long brief, meters, clear — now: one line FETCHED:\n"
    "Memory — old: easy to confuse with 'the model remembers' — now: diary on disk; "
    "window is last few answers.\n"
    "After a break — old: easy to lose or fake — now: open run.py; /history is a view.\n"
    "Second look — old: built into the face — now: /shape only if you ask.",
    common + [
        ("act", "compare-the-two-engagements"),
        ("path", "away-from-the-old-chair"),
        ("part", "how-to-talk"),
        ("name", "side-by-side"),
        ("enables", "feel-the-difference"),
    ],
)

cap(
    "A FIRST REAL SESSION (copy this).\n\n"
    "  you @ turn 1 › In one sentence: what is this program for?\n"
    "  you @ turn 2 › file: piles/docs.txt What does FETCHED: none mean?\n"
    "  you @ turn 3 › /shape\n"
    "  you @ turn 4 › /views\n"
    "  you @ turn 5 › /exit\n\n"
    "Turn 1: talk, clock none.\n"
    "Turn 2: you may instead file: a derived view "
    "(python3 show_docs.py export) or your own notes. The pile is the booklet.\n"
    "Turn 3: optional form-reading.\n"
    "Turn 4: peek at the minutes.\n"
    "You did not tag anything. You did not start a second program.",
    common + [
        ("act", "give-a-copyable-first-session"),
        ("path", "toward-using-it-today"),
        ("part", "how-to-talk"),
        ("name", "first-session"),
        ("enables", "copy-the-first-session"),
    ],
)

cap(
    "WHAT THIS WILL NOT FEEL LIKE.\n\n"
    "Not a nanny. Not three personas introducing themselves. Not a disclaimer "
    "on every line.\n"
    "It will feel quieter. Put the file in when it counts, read the answer, "
    "glance at FETCHED:. That is the engagement.\n"
    "If you treat every confident paragraph as 'looked up,' you are back in "
    "the old vortex — this program cannot stop that, it can only make the miss "
    "visible.",
    common + [
        ("act", "name-the-quiet"),
        ("path", "away-from-expecting-a-nanny"),
        ("part", "how-to-talk"),
        ("name", "will-not-feel-like"),
        ("preserves", "his-own-eye"),
    ],
)

print("seeded", DOCS)
