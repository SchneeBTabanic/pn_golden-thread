# DERIVED VIEW — disposable. The pile is the truth.
# piles/docs.txt  part:how-to-start
# Regenerate: python3 show_docs.py export
# Edit the pile (scribe), not this file.

ONE PROGRAM. You talk in run.py. That is the main program we built.

prove_the_outside.py is a self-test. It pretends to be you for half a minute, then exits. Never leave it running next to run.py. They do not talk to each other. run.py writes piles/turns.txt. The self-test writes a throwaway diary and leaves it.

This part (how-to-start) is which file to start. The other part (how-to-talk) is what a turn feels like versus the old agent.py.

Room A: ordinary talk. No costume on the model's mouth.

OPTIONAL SELF-TEST. Server must already be up.

  cd pn_golden-thread
  python3 prove_the_outside.py

You want the last lines to say PROOF HELD.

That script: (1) a bare question → FETCHED: none (2) file: of a small test file → FETCHED: that path (last good run also quoted ALPHA-PLACED) (3) /shape → a scar-note that is not the next answer.

FAIL — no local model means start the server first.
This is not 'the model is wise.' It is 'the diary and the clock work without you being the clerk.' Then go back to run.py.

START THE MODEL, THEN THE TALK.

The engine is a compiled binary at
/mnt/data/Codeberg/llama_server_build/bin/llama-server
It is not on PATH and it is not in this directory. Typing `llama-server`
here fails with command not found. That is the whole mystery.

From this directory:

  ./scripts/run_llama_server.sh

Default: granite-3.3-2b-Q4_K_M, port 8080 (what run.py looks for).

Pick a model and a port (CLI flags or env vars; both work):

  ./scripts/run_llama_server.sh -m /mnt/data/models/granite-3.3-8b-Q4_K_M.gguf --port 8080 -c 4096

  MODEL=/mnt/data/models/granite-3.3-8b-Q4_K_M.gguf CTX=4096 ./scripts/run_llama_server.sh

Stop the 2B first. One card, one model. The 8B Q4 is ~4.7 GB on a 6 GB
P3000; 4096 context is the safer start. CUDA OOM → drop -c or NGL.

Optional: export PATH="/mnt/data/Codeberg/llama_server_build/bin:$PATH"
and then the bare name works from any directory. Not required.
Also fine: ollama serve (and a model pulled).

Then in another terminal:
  cd /mnt/data/project-namirha_grok-build/pn_golden-thread
  python3 run.py

You should see: Room A — unmasked. FETCHED is a clock. you @ turn 1 ›
Type there. Leave with /exit.
If nothing is listening, it refuses to pretend.

JUST TALK.

  you @ turn 1 › What is 2 + 2?

The answer prints in the main window. On the side, one line:
  FETCHED: none

This turn, no file was placed. Clock, not a warning. Do nothing.
The model may ramble. That is Room A being honest. Say 'stop after one sentence' or type /forget (the diary is not deleted).

PUT A REAL FILE IN FRONT OF IT.

  you @ turn 2 › file: tests/fixture_place.txt What is the first line?
  you @ turn 2 › file: /home/schnee/notes/meeting.txt Summarise what we decided.

The whole file is placed, or the program REFUSES (missing, too big, a folder, binary). Nothing is silently half-read.
Clock: FETCHED: /full/path/to/that/file
If the answer ignores the file, you can see it: looked up, then not used.
Paths with spaces: file: "/home/schnee/My Notes/draft.txt" What is the title?

ASK FOR SHAPE (optional).

  you @ turn 4 › /shape

The model looks at the last turn and piles/story.txt (you may edit that file). Testimony, not a verdict. Do not treat 'none' as a green light.

  you @ turn 5 › /shape topic:turn
  you @ turn 6 › /shape act:place-a-file

You named the group. The program glued. The model only spoke.
A group that does not exist is refused. Nothing sneaky.

THE DIARY. Written for you to piles/turns.txt. You can ignore the file.

/pile — where it is, and its birth name (辻…)
/views — contents by what each entry does and reaches toward
/history — what the model will be shown (a view, not the diary)
/forget — fresh window for the next answers; diary not erased
/model — which server, asked of the machine
/help — the short list
/exit — stop

/forget is start-the-window-fresh, not burn-the-notebook.

A TINY WORKED AFTERNOON.

1. Start llama-server or Ollama.
2. cd pn_golden-thread && python3 run.py
3. What did we decide about backups? → FETCHED: none
4. file: /path/to/your/notes.txt Answer only from this file. → FETCHED: that path
5. /shape if you want the scar-reading
6. /views if you want the minutes grouped
7. /exit

Three things: talk; file: when it must be this document; FETCHED: is the clock.

WHAT YOU DO NOT HAVE TO DO.

You do not start scribe by hand for ordinary work.
You do not tag turns.
You do not run run_tests.py for daily use. Daily use is run.py only.
prove_the_outside.py is an optional self-test.
You do not turn /skin on. Room A is the conversation.

WHEN TO STILL USE YOUR EYES. The clock says whether something was looked up, not whether the answer is true. Still read the sentence when a quote will matter, when live weather was not placed, when the model sounds sure and FETCHED: none.

You stop being unable to see that nothing was looked up. You do not retire thinking.

IS IT BROKEN?

FETCHED: none after a chat question — normal. No file this turn.
FETCHED: /some/path after file: — normal. That file was placed whole.
file: REFUSED … does not exist — wrong path. Nothing half-read.
Model invents extra questions — Room A. /forget or tell it to stop.
PROOF HELD — the outside worked.
FAIL — no local model — start llama-server or Ollama.
/shape produced nothing — that key:value matches no diary entry yet.
