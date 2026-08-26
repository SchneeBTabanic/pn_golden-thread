# tagging-lab — Leipzig gloss for `/walk`

This is the real glosser. It is not a stub and not a passthrough.
Leipzig is the middle of the hop, not a display extra.

`/walk` is Japanese (Dango) then this line then proposed tags. The
stems here are the shape of hyphenated `@act` / `@path`. A missing
gloss is a missing hop. `/walk` refuses by name. Do not write a
placeholder that echoes the sentence so the command “completes.”

`gloss.py` walks Japanese morphemes in Japanese order (SudachiPy) and
maps lemmas from `jmdict-lemmas.tsv` (JMdict / EDRDG, CC BY-SA 4.0).
A missing lemma is printed in Japanese and marked `?`. It is never
guessed. Fluent English translation is the thing this step exists to
prevent.

Do not swap Dango for an instruction-tuned Japanese model because the
gloss line is missing. Those are different organs.

## What `/walk` needs besides this directory

In the talk venv (the same `deps/venv` `env.example.sh` already names):

```sh
deps/venv/bin/pip install sudachipy sudachidict_core
```

`env.sh`:

```sh
export GT_GLOSS_PY="$ROOT/tagging-lab/gloss.py"
export GT_GLOSS_PYTHON="$ROOT/deps/venv/bin/python"
```

Talk can start without Sudachi. `/walk` cannot. Same sentence as Dango.

Check:

```sh
"$GT_GLOSS_PYTHON" "$GT_GLOSS_PY" '空越えていく'
# expect a line: → sky cross-SEQ-go
```
