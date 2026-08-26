# golden-thread

Thin local runtime. You talk to a local model. The answer prints first,
whole, on stdout. Python stamps what can be decided without interpretation,
on stderr. Each turn is captured into a scribe pile.

Not GTPS-Agent. Not Vessel. Does not retrieve, rank, embed, or inject the
48 clauses. `file:` places a file you named, whole, or refuses.

## Setup

Seams are `GT_*` environment variables. Do not edit Python to relocate
this build. Packages, scribes, gForth, and models: `DEPENDENCIES.md`.

```sh
cp env.example.sh env.sh    # edit the paths
source env.sh
python3 run_tests.py        # no model, no server
```

The clause file ships at `law/GoldenThread-v1.6.2-Triune-Cathedral.json`
(inoculated 2026-08-16; filename unchanged). `law.py` loads it via `GT_LAW`.
Default: not placed. `/withlaw` places the whole file.

## Engine — pin, patch, copy, `-fa off`

Do **not** use the latest llama.cpp. Pin tag **b8461**
(`cea560f483f0f03e828a6c76e78821debdecbe06`).

The patch in `patches/` edits four existing files under `tools/server/`.
It does **not** add the two new translation units. After `git apply`,
copy them from `llama-hook/` or cmake will fail:

```sh
mkdir -p deps && cd deps
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp && git checkout cea560f4
git apply ../../patches/llama.cpp-b8461-gt-relied.patch
cp ../../llama-hook/gt-relied.cpp ../../llama-hook/gt-relied.h tools/server/
cmake -B build -DGGML_CUDA=ON && cmake --build build -j --target llama-server
```

Point `LLAMA_SERVER` at that binary (`env.example.sh` already does, once
`deps/` is that path). Then:

```sh
./scripts/run_llama_server.sh
python3 run.py
```

Flash attention must be **off** at runtime (`-fa off`). The launch script
passes it. If FA stays on, talk still works; every RELIED reading is a
named refusal (`saw_softmax` never becomes true). An unpatched server
likewise talks; it cannot serve `relied.py`.
