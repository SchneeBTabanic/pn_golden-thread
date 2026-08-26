# golden-thread

Thin local runtime. You talk to a local model. The answer prints first,
whole, on stdout. Python stamps what can be decided without interpretation,
on stderr. Each turn is captured into a scribe pile.

Not GTPS-Agent. Not Vessel. Does not retrieve, rank, embed, or inject the
48 clauses. `file:` places a file you named, whole, or refuses.

## Setup

Read `DEPENDENCIES.md`. Seams are `GT_*` environment variables; do not edit
Python to relocate this build.

```sh
cp env.example.sh env.sh    # edit the paths
source env.sh
python3 run_tests.py        # no model, no server
python3 run.py              # needs patched llama-server at :8080
```

The clause file ships at `law/GoldenThread-v1.6.2-Triune-Cathedral.json`
(inoculated 2026-08-16; filename unchanged). `law.py` loads it via `GT_LAW`.
Default: not placed. `/withlaw` places the whole file.

The llama.cpp patch is in `patches/`. An unpatched server cannot serve
`relied.py`. Flash attention must be off (`-fa off`).
