# golden-thread — a thin local runtime

You talk to a local model. The answer prints first, whole, on stdout. Python
stamps what can be decided without interpretation, on stderr. Each turn is
captured into a scribe pile.

This is not GTPS-Agent. It is not Vessel. It does not retrieve, rank, embed, or
inject the 48 clauses. `file:` places a file you named, whole, or refuses.

## Setting it up

**Read `DEPENDENCIES.md` first.** This runtime reaches outside its own directory
in three different ways, and a clone that has not been configured will fail six
guards in the test suite. That is expected, and the failure names what is
missing.

```sh
cp env.example.sh env.sh     # edit the paths in it
source env.sh
python3 run_tests.py         # 29 guards; all pass once the seams are set
```

The short version of what you must supply: two scribe repos, gForth 0.7.3, a
patched `llama-server` (the patch is in `patches/`), a handful of Python
packages, and at least one Granite GGUF.

## Run

Needs a local model. Default engine: `llama-server` at `:8080`. Ollama is a
permitted client for unmasked talk, not the architecture.

```sh
./scripts/run_llama_server.sh          # starts the engine
python3 run.py                         # the doorway
python3 talk_tui.py                    # optional TUI shell
python3 prove_the_outside.py           # proof of the outside
```

`run.py` remains the doorway; the TUI is a shell over the same session.

## Law

`law.py` loads the ratified clause file **verbatim, in file order, never
summarised, never embedded, and by default not placed at all**. `/withlaw` or
`GT_PLACE_LAW=1` places the whole file. There is no `applies_when`, and nothing
selects a subset of clauses for you — a selector inventing which clause is
relevant is the failure this runtime exists to prevent.

The file ships here as `law/GoldenThread-v1.6.2-Triune-Cathedral.json` and is
found via `GT_LAW`. `law/declared.txt` is displayed and never acted on: a
declaration that quietly acquired a trigger would be that same failure.

## What is in here

```
run.py            the doorway            web.py       url:/search:/html:
talk_tui.py       optional TUI           strip.py     boundary reduction
model.py          the local backends     file_read.py file: places or refuses
turn_record.py    the turn record        pile_io.py   the gForth pile runtime
path_stack.py     !path, Dango + tags    law.py       the clause ledger
relied.py         RELIED attention mass  tape.py      the tape
checks/           arithmetic, echo, quantities, scan
tests/            the suite — 29 guards, run from inside this tree
llama-hook/       gt-relied.cpp/.h, the server patch as standalone units
patches/          the exact llama.cpp diff, pinned to upstream b8461
```

## Documentation

Two derived guides ship because `show_docs.py` reads them:

```sh
python3 show_docs.py start     # which file to run
python3 show_docs.py talk      # how a turn works
```

The canon is a pile (`piles/docs.txt`), which is **not published** — it is
regenerable with `python3 piles/_seed_docs.py` once `GT_SCRIBE` is set. Until
then `show_docs.py` refuses by name rather than showing you a partial book.

`DEPENDENCIES.md` closes with a full list of what is absent from this tree and
why, including files the text above refers to.

## Licence

See `LICENSE`.
