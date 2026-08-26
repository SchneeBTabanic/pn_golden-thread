# A working guide to pn_golden-thread

**Status of this document.** Written 2026-08-26 for the person who cloned
`pn_golden-thread` plus `scribe-workbench-gforth`, can start the two
servers, and can read the gForth user guide — but has no map of how to
*move* inside a conversation so the human stays the source of the
question and the judge of the tags. It is a posture guide, not a second
README. Setup, pins, and seams stay in the repo README and
`DEPENDENCIES.md`.

The long discourse at the end is **purely speculative**. It was not run
against a live Granite, Dango, or patched llama-server. It is a
trajectory you can try, not a transcript you can trust as evidence.

The bind seat (`/sheet` then bind on `:8081`; LOOK on `:8081`) is the
intended tree after the B+C build. If a clone still has `/sheet` as
proposal-only and LOOK on the face, the timing below will name a
refusal or a missing bind — treat that as the seat not yet occupied,
not as a reason to `/keep` on syntax alone.

This guide does not replace
`scribe-workbench-gforth/user-guide_pn-gf-scribe.md` or `TAGS-gforth.md`.
Those are the tag lab, the identity physics, and the exact Forth lines.
Section 6a says *when* to open them and *which* parts the talk path
depends on. Do not copy that lab into a project pile — point at it
(`@watches:` + `@quoting:`).

---

## 0. What you are sitting in

You are not in a chatbot. You are in three rooms that must stay distinct,
and a turn that *breathes*.

**Room A — the face.**  
Granite on the first llama-server (`GT_LLAMA`, default `:8080`). You
speak. It answers. The answer prints first, whole, on stdout. That first
answer is what counts. Nothing in Room A retrieves, ranks, embeds, or
picks which of the 48 clauses apply. Law is off until `/withlaw`, and
then the *whole* file is placed, file order, nothing selected.

**Room B — the beneath (the small lung).**  
Granite 2B on the second llama-server (`GT_WALK`, `PORT=8081 CTX=8192`).
This is not a second personality. It is the seat that holds the whole
tag sheet and is asked two different questions:

1. **Propose** — `/sheet`: hyphenated `@act` / `@path` (and only the
   seats the turn needs). Still generation. Not a reading.
2. **Bind** — immediately after, same process: ordinary sentences.
   Does this `@act` still name a doing *in this face answer*? Does this
   `@path` still reach *from this answer*? If it cannot tell, it must
   say so. Speech, not a score, not a filing, not “you should keep.”

LOOK after `!path` also POSTs here, so leftover speech vs a path *you*
declared sees the whole sheet. Inquire and bearings stay on the face;
they are not this seat.

If `:8081` is down, `/sheet` and LOOK refuse by name. A live-core is not
the sheet; the summons will not amputate the blood.

**Room C — the clerk and the pile.**  
Python stamps what can be decided without interpretation (stderr).
gForth keeps the diary: append-only blocks, byte-offset identity,
declared extent. The pile is the truth after the window has forgotten.
The clerk copies a tag you have judged. It does not invent one. It
records bind speech, or names that bind did not speak. It is not
Executor, Whistleblower, or Proxy. Those names are not in this runtime.

If you treat Room B as “the smarter assistant,” or treat bind speech as
permission to `/keep`, or treat Room C as memory the face may silently
reuse, the architecture has already failed in the way commercial UIs
fail.

This tree is not GTPS-Agent and not Vessel. It does not retrieve, rank,
embed, or inject the 48 clauses. `file:` places a file you named, whole,
or refuses.

---

## 0b. How a turn breathes (this changes timing)

| Phase | Breath | What happens | Your move |
|---|---|---|---|
| Outer out-breath | Face speaks | First answer, whole. RELIED series may listen *while* it speaks (mass on spans you placed — melody, not a mean). | Read that answer as what counts. Do not immediately ask it to improve itself. |
| Inner in-breath *during* that speech | The hook listens | Per-token retrieval-mass on *your* words. Tape makes one blunt cut (answer / sequel). The curve audits the cut. | `/raw` / `/sequel` if the cut or the leftover matters. Do not argue with the face about the leftover yet. |
| Pause before the inner out-breath | You decide if the turn should *live* | Not every turn deserves blood. | Joke, probe, discarded outline: leave it. Living work: go to `/sheet`. |
| Inner out-breath *during* the coming in-breath | 2B proposes, then binds | `/sheet` prints **proposal first, bind speech second**. Optional `/walk` (Dango) is a *reveal*, not a verdict; talk does not wait for it. `/bind` re-asks only the second question. | Read bind *against the face paragraph*. Strip-test (scribe guide §6). `/comment` if bind says it cannot tell. |
| Outer in-breath | The record takes the turn in | `/keep` files judged tags **and** the bind paragraph (or `BIND: not spoken this keep — syntactic proposal only`). | You are still the judge. Bind that flatters is still speech. |
| Sequel breath | Leftover vs a path you name | `!path …` → LOOK on `:8081`. | If LOOK says the leftover sits off the path, `/forget` rather than feeding it back as accepted context. |

**Timing that follows from this:**

- Do not `/keep` in the same motion as `/sheet` without reading the bind.
  The inner out-breath has to happen *in you* as well as in the 2B.
- Do not `/walk` as a substitute for `/sheet`. Dango reveals verb/path
  in another language; it does not bind the English face. If you walk,
  walk *before* or *beside* sheet so bind may be shown the walk as
  `[WALK — reveal, not a verdict]` for the same turn — not after keep.
- Do not `/comment` *instead of* bind. Comment asks what the *record*
  is for (no tag). Bind asks whether the *proposed tags* still touch
  *this answer*. Different questions. Comment is useful when bind says
  it cannot tell.
- Do not `!path` until you have seen `/sequel`. The leftover is the
  inner remainder of the out-breath; LOOK is the small lung on that
  remainder.
- Do not `/forget` before you have decided whether the leftover should
  be looked at. Forget clears what the *next* face out-breath will hold;
  LOOK does not need the face window.
- Do not `/withlaw`, `/dial`, or `/press` in the same breath as first
  speech. Those change the outer out-breath. See the un-pressed answer
  first.
- `/revises` / `/inquire` / `/bearings` belong after several outer
  in-breaths have already landed in the pile. They are about edges
  between records, not about tagging the last sentence.

A bind that tells you to keep has occupied `/keep`. Read it as a
malformed inner out-breath. File only what you still judge.

---

## 1. The stance that protects creativity

Public complaints about LLMs on tasks and making things:

1. The model completes before you have finished intending.
2. Outputs from different people converge on the same fluent average.
3. Ownership of the idea thins; the struggle that builds judgment is
   skipped.
4. Context windows forget; you re-prompt and get a slightly different
   average.
5. Provenance of “who said this, human or machine” dissolves.
6. Confidence is performed. Incompleteness is hidden.

This runtime does not fix the model. It gives you *phases* in which
those failures can be seen and interrupted.

The live core of the gForth tag sheet is the blood of those moves
(full tests and lineage: scribe guide §§6–8):

- `@act:` — an open, continuous verb-phrase that transforms from within
  (`protect-against-bit-rot`, `extend-the-insight`). Not a closed,
  terminating verb (`decide`, `choose`, `define`, `review`) — those
  name a moment already over. Strip the verb. If a tidy noun-bucket
  remains, it was filing.
- `@path:` — a direction word plus at least two real words. Fifteen
  directions are live. Two named empties only: `not-yet-discerned` (I
  feel it matters; I have not looked) and `ruled-none` (I looked; the
  body must carry the search). Only you may assert which empty it is.
  The tools report those as **held** — a third verdict.

A topic label is a coffin. An act-and-path pair is still in motion.
Bind is allowed to say “this act is clothing,” “this path is
sheet-atmosphere,” or “I cannot tell.” It is not allowed to keep for
you. The strip test is still yours, now with a second mouth pointed at
the same paragraph.

**Rhythm.**  
Talk (outer out-breath) → read → `/sequel` if needed → if the turn
should live: `/sheet` (propose + bind) → read both → optional `/walk`
before or with sheet, not after keep → `/comment` if bind is fog →
`/keep` or refuse → `hold:` / `!ask` for what must not melt into the
next out-breath → `!path` only on leftover you refuse to treat as
accepted.

Do not `/withlaw` on a first hello. Do not `/sheet` every joke. The
small lung is for turns you mean to accumulate. The protection is the
gap you keep, not the number of commands you fire.

---

## 2. Boot posture (once per sitting)

From the clone, after `source env.sh`:

```
# terminal 1 — face (outer out-breath)
./scripts/run_llama_server.sh

# terminal 2 — beneath (inner out-breath: sheet, bind, LOOK)
PORT=8081 CTX=8192 MODEL="$MODEL" ./scripts/run_llama_server.sh

# terminal 3 — talk
python3 run.py
```

CPU-only: `NGL=0` on both servers. Flash attention must stay off
(`-fa off` is already in the launch script). If FA is on, talk still
works; every RELIED reading is a named refusal — the inner in-breath
during speech is then mute.

TUI: Enter makes a new line; Ctrl+Enter / Ctrl+S / Ctrl+J sends; Esc
returns to the talk tab; summons open other tabs. Kill the shell and
only prettiness is lost. The pile remains.

First commands:

```
/model
/pile
/law
/declared
/held
/open
```

You are checking: which GGUF is loaded on the face, whether a diary
already exists, that law is titles-only until you choose otherwise,
that no hold and no burning question survived unseen. `/sheet` will
tell you whether the beneath is actually up.

---

## 3. Command atlas — grouped by what they protect

### 3.1 Ordinary speech (outer out-breath)

A normal sentence asks the face. The first answer is what counts.
`/raw` shows the whole unsplit model output — what the splitter held
back. `/sequel` shows leftover extra speech from the last answer.

`!path words` files that leftover and summons LOOK on **`:8081`**:
does the leftover still sit on the path you declared, in the sheet’s
meanings. Python does not score a match.

Use this when the face over-spoke. Leftover tidy paragraphs are where
flattening hides: a second paragraph that turns your question into a
blog post.

### 3.2 Placement without retrieval

Nothing is looked up for you. You type the path or the URL.

| sigil | what happens |
|---|---|
| `file: path question` | whole file, or refuse |
| `html: path question` | saved HTML, reduced by the Python scribe, or refuse |
| `url:` / `fetch: URL question` | trafilatura main text, whole, or refuse |
| `search: query` | hit list only (title, url, snippet). No page fetched |

This is the answer to “the model went and got something I did not ask
it to get.” If you want a page, you name it with `url:` after you have
seen the hit list.

`file:` / `url:` also give RELIED something of *yours* to listen to
during the out-breath. Place first, then ask.

### 3.3 Stasis — things that must not enter the next prompt as “context”

```
hold: testimony
/held
/release ref reason
/probe
/probe ref
```

A hold is testimony in stasis. No model call when you place it. It is
not edited when released; the reason is required. `/probe` is a
measurement of the last turn *under* the active holds, never a second
face answer.

Use holds for: a constraint you refuse to let the model paraphrase, a
source sentence that must stay verbatim, a moral line that should not
be “summarised into the vibe.” In the tag lab this is the pod grown
into a mechanism (`@aspect:prospective` + `@awaits:` / `@dissolves:`).

### 3.4 Questions that only you may close

```
!ask question
/open
!closed n|ref
```

A burning question is not a hold and is not put in the face window.
Commercial UIs treat every user sentence as a prompt to complete.
`!ask` keeps a question *open* without feeding it to the completer.
`n` is the `/open` index.

### 3.5 Memory you can see (outer in-breath, later)

```
/history
/history key:value
^
^^
/fold
/fold a b
/forget
/reset [reason]
/pile
/views
```

`/history` is a derived view of last-N for you. Standing default also
places last-N in the face (raw, divider family) unless you are in a lab
setting that turns that off. `/history key:value` keeps only turns
carrying that tag.

`^` places a clerk fold of last-N into *this* turn. `^^` places raw
ASKED/ANSWERED. `/fold` prints a clerk recap with no model call.
`/fold a b` articulates seats `a` to `b` after `/forget` (asks,
revises, isolated); `a` and `b` are 1-based seats in that list.

`/forget` starts the *next* face out-breath fresh; the diary is kept.
`/reset [reason]` mints a new empty pile; the old file is not
destroyed. `/pile` shows path, genesis, and block count.

`/views` is gForth `g-toc` on this pile — text driving, tag values that
gathered more than one block versus values that stand alone. A pile
where everything stands alone is telling you either that every reach is
distinct, or that you have spelled one thing three ways. Read the
scribe guide’s “NOT shown by this index” habit: the line names keys
you did *not* ask about.

This is the answer to “the window rolled and now the model is
re-inventing last Tuesday.” You do not re-prompt for memory. You fold,
view, or place.

### 3.6 Revision without silent overwrite

```
/revises n|ref
/inquire a b
/bearings a b
```

`/revises` marks that the *next* turn re-frames a named turn. Optional
keys, and only these four: `rejected:"…"` `expanded:"…"`
`narrowed:"…"` `invariant:"…"`.

`/inquire a b` walks asserted revises-edges backward in seats a..b.
One model pick per step from a Python menu. No invented edge. Reply is
a number or STOP. This call stays on the **face**.

`/bearings a b` is one face call on the `/fold a b` recap only. Five
labeled parts: Current bearings; Living thread; Most recent revision;
Outstanding uncertainty; One next question. Never a chain. Never fed
`/inquire`’s speech.

This is the answer to “I accepted a fluent draft and now I cannot find
the thought I started with.” Revision is a recorded edge, not a
backspace. In the tag lab: `@replaces:` / `@superseded:` on the pile
side; `/revises` on the talk side. Do these after several records
exist. They are not part of sheet/bind.

### 3.7 The small lung and the pile (inner out-breath → outer in-breath)

```
/walk
/sheet
/bind
/keep
/comment
/shape
/shape key:value
```

`/walk` — last turn into Japanese + Leipzig gloss (Dango). Reveal.
Proposed tags on that path are shown and not filed. Slow the first
time. Talk does not wait. Cold Dango while `:8081` binds. If Dango is
unset, `/walk` refuses by name rather than inventing a Japanese line.

`/sheet` — last turn + whole tag sheet to `:8081`. Proposes, **then
binds**. Print order: proposal, then bind speech. Shown, not filed.
`@act` is a doing; `@path` is a reaching. Propose only the seats this
turn needs, as `@key:hyphenated-value` (no spaces). If no seat fits,
it must say so. Invent a witness key only then, and say it invented
it.

`/bind` — second question only, on the last proposal. Use when bind
refused (beneath was down) and you brought `:8081` up, or when you
want another reading of the same lines. Needs `/sheet` first.

`/keep` — you are the judge. The clerk copies accepted `@key:value`
lines **and** files the bind paragraph, or names `BIND: not spoken
this keep — syntactic proposal only`. Needs `/sheet` first.

`/comment` — ordinary sentences: what is this record for. No tag. You
are not asked to write one.

`/shape` — spoken resemblance to a short story of scars plus one turn
(or `/shape key:value` on a gather you named). If none, say none. Not
a verdict. Face, not the binder.

**How to read a bind before `/keep`.**  
Hold the face paragraph in one hand and the `@act` in the other. If
bind says clothing or sheet-atmosphere, believe the suspicion until
you can find the doing *in the answer*. If bind says it cannot tell,
that is a complete result — `/comment` or a named empty, not a fluent
`/keep`. If bind tells you to keep, ignore that sentence; the prompt
forbade it.

**Strip test before `/keep`** (scribe guide §6, yours alone for the
third test): remove the verb from the proposed `@act:`. If a
subject-label remains (`storage-filesystem`, `creativity-enhancement`),
refuse and write the act yourself. For `@path:`, demand a live
direction and two real words, or a named empty you are willing to
assert. Bind can *suspect* clothing; only you close the test.

### 3.8 Law, skin, force — they change the outer out-breath

```
/withlaw
/law
/declared
/skin
/dial α
/dial off
/press strength span
/press off
```

Law default is off. `/law` lists titles only. `/withlaw` places all 48
clauses in the system prompt, file order, nothing selected. That is a
heavy transfusion. Use it when the sitting is already a governance
sitting, not when you are trying to keep a story alive. An injected
obligation is performed, not obeyed — the amendment in the clause file
says this in plain language.

`/declared` displays your declarations. Never acted on. That is the
point.

`/skin` toggles the GBNF grammar mask (llama-server only). Default pair
unless `GT_HELD_SKIN=1` and a hold is in stasis.

`/dial` and `/press` bias attention toward a placed span or a hold.
Off by default. These are the closest things in the runtime to “make
the model obey the file.” Use them only after you have seen the
un-pressed answer. `/press off` refuses dial and press together.

See the un-pressed, un-skinned, law-off answer first. Then one change
at a time.

### 3.9 Housekeeping

```
/model
/help
/exit
```

`/model` shows which file is loaded on the face server. `/exit` leaves.
The diary is kept.

---

## 4. Which engine does which job

| Engine | Seat | Breath | Job |
|---|---|---|---|
| Granite on `:8080` (2B enough to talk; 8B if you have VRAM) | face | outer out-breath | First answer. Inquire, bearings, comment, shape. |
| RELIED hook on that server | inner in-breath | listens during speech | Mass on placed spans. Not truth. |
| Granite on `:8081` with `-c 8192` | beneath | inner out-breath | `/sheet` propose, then bind. LOOK after `!path`. Must fit the whole `TAGS-gforth.md`. |
| Dango (optional, `GT_DANGO`) | walk | side reveal | Japanese + gloss. Not bind. Cold during bind. |
| Optional L2 in `path_stack` | walk | side reveal | Propose `@act`/`@path` from Japanese + gloss + live core. Shown, not filed. |
| gForth 0.7.3 + scribe leaves | pile | outer in-breath | keep, read, index, toc. Identity = offset + formed + genesis. |
| Python clerk | stderr / diary | names | Form, splits, refusals, copies judged tags, files bind speech or names absence. |

8B on the face is for when the *question* is hard. It is not smarter
blood. Blood is the sheet plus bind plus your strip test. Putting 8B
on `:8080` and never `/sheet`-ing is the commercial habit in a local
box.

---

## 5. A wise sitting — short form, timed to the breath

1. Boot both servers. `/model` `/pile` `/held` `/open`.
2. Speak the originating question in your own words. Read the first
   answer (outer out-breath). Do not immediately ask it to improve
   itself.
3. `/sequel` if the cut left extra speech. Decide: look (`!path`) or
   drop (`/forget` on the *next* turn), not both in a muddle.
4. If the turn should live: `/sheet`. Wait for **two** blocks of
   speech. Read bind against the face. Strip-test. `/bind` only if the
   second mouth did not speak.
5. Optional `/walk` before a second `/sheet` on a hard turn — reveal
   for the binder, not a substitute for it.
6. `/comment` if bind cannot tell what the record is for.
7. `/keep` or refuse. Read the clerk line: `BIND spoken` or `BIND absent`.
8. If a constraint must not be paraphrased: `hold:` it. `/probe` later
   rather than “remind the model.”
9. If a question must stay open: `!ask`. Do not put it in the next
   prompt.
10. After several living turns: `/fold` `/views` `/shape`. Look at
    which `@path:` values gathered more than one block. Then
    `/revises` / `/inquire` / `/bearings` if edges exist.
11. `/withlaw` only when the sitting has become governance.
12. `/exit`. Tomorrow `/views` (and `g-keys` on the pile if you will
    hand-touch it) before speech.

---

## 6. Using the scribe in this breath

You do not need to drop into the gForth REPL during ordinary talk.
`pile_io.py` already shells to `pn-keep.fs`, `pn-gread.fs`,
`pn-gindex.fs`. `/views` is the toc. `/keep` is the in-breath of judged
tags plus bind speech.

Use the gForth guide when you:

- open the pile in an editor and need the anchors you must not touch;
- want `sift` / `gather` / `agree` / `echoes` / `since` on a pile that
  has grown past what `/history` should carry;
- need to write an act and a path *yourself* because bind and
  strip-test both failed;
- need to understand why a reference still resolves after a move.

The two pile formats are not mutually readable. Do not paste
Python-scribe headers (`@@ #`) into a gForth pile (`@@ @`). The fork
is deliberate.

---

## 6a. Richness that lives in the gForth guide — open it for these

Full text: `deps/scribe-workbench-gforth/user-guide_pn-gf-scribe.md`
and `TAGS-gforth.md`. What follows is orientation, not a substitute.

### Live core (guide §§6–7) — what `/sheet` and bind are talking about

A good block has at least `@act:` and `@path:`. The writer at `keep`
*discloses* failed tests and still writes the block as you gave it.
Disclosure without governance — the same bargain as bind then `/keep`.

Closed classes you will see on filed turns: `@aspect:`
(`manifesting` / `manifested` / `prospective`), `@origin:`
(`human` / `ai`), `@because:` (four Debian override reasons),
`@kept:` (`evidence` / `specimen` / `pedagogy` / `resonance`).
Witness keys (`@topic:`, `@source:`, anything you invent) are free
text; they do not gather unless values repeat exactly. **No space in a
value** — the header parser reads to the next whitespace.

`@topic:` is the demoted one: a drawer label beside the live core,
dead as a block’s only meaning. If bind is foggy, do not retreat to
`@topic:`.

Provenance is three questions, never one: `@source:` whose saying,
`@origin:` which kind of mind, `@attests:` who stands behind it.
`@origin:ai @attests:self` is the mixed-pile chord.

### Identity (guide §5) — why the diary survives the window

A block has three coordinates: which pile (genesis `辻…`), where (byte
offset), when-formed (`@formed:` microsecond — the survivor when
offsets shift). Inside one pile, offset + formed. Across piles, the
three-part form `辻genesis#offset/formed`. Point **backwards only** —
write the target first, then the block that cites it. Presence is
belonging; `@ref:` is salience. A block with no incoming ref is a
**pod**, not an orphan.

Hand-edit neither breaks a `@ref:` nor a cross-pile link by itself.
What hand-edit *can* break is the **extent chain** — how tools walk
the file at all.

### Extent ritual (guide §9 + the founded remainder)

`@extent:` is that block’s own body byte count — not cumulative.
Edit a body without changing length: nothing else is affected.
Change length: fix **that one** block’s `@extent:`, then
`s" pile.pn" check` until clean. No cascade. Three things the hand
must not touch: `@formed:` on a block, `@genesis:` on the first
block, `@@` at column zero of a body line. `amend-last` is the
lawful length-change on the tail; older blocks get a new block with
`@replaces:`.

### Chords that show up in a golden-thread sitting (guide §8)

| Chord | When you need it |
|---|---|
| Pod: `@aspect:prospective` + `@awaits:` + `@dissolves:` | A hold, a named empty, a truth in suspension |
| Vouching: `@origin:ai @attests:self` | Bind speech and sheet proposals are AI-origin; you attest at `/keep` |
| Dead-road specimen: `@rejected:` + `@kept:specimen` | A path the face offered that you will not resell yourself later |
| Standing vs dated | Procedure in one block; token/deadline in another that `@ref:`s home |
| Named empty + exit door | `@path:not-yet-discerned @awaits:…` |

`g-keys` on a pile you have not touched in a while shows conventions
you invented and forgot. `since` after `mark` is how you resume after
time away — talk’s `/history` is the thin cousin.

Forth at the prompt (only if you leave talk and load the dictionary):
strings are `s" …"` with a space after `s"`; tick a body with `'` at
the prompt, never `[']`; arguments before the verb. Exact lines:
guide §10 quick card.

---

## 7. Speculative discourse trajectory

*Invented sitting. No server was called. Bind paragraphs are plausible
shapes, not measurements.*

### The work

A children’s myth: a harbour boy who hears when a net is *lying*, not
torn. Fear: Joseph Campbell in granite.

### Turn 1 — outer out-breath, then the small lung

```
you @ turn 1 › I am writing a children’s myth. A harbour boy hears when
a fishing net is lying — not torn, lying. Do not give me a three-act
outline. Give me three images only, each one a doing.
```

Face: three images that still lean on “the sea tests him.” Closed
verbs.

Do **not** say “try again, more original.”

```
/sequel
```

Leftover is a tidy moral. Leave `!path` for a moment — first decide
whether the *answer* should live.

```
/walk
/sheet
```

Walk (optional reveal): hear-as-discernment, not hear-as-sound.

`/sheet` now prints two mouths:

```
PROPOSAL
@act:hear-the-net-lying
@path:away-from-the-hero-template
@aspect:prospective

BIND
The first image still does a hearing. The verb is not clothing there.
The path names a refusal the answer only half-performed: the second
image still “tests him.” I cannot tell whether "lying" in the answer
is the net's doing or the boy's. If you cannot tell either, leave
the empty to yourself.
```

This is the inner out-breath. The human does **not** `/keep` the path
as if the template were already gone. Strip-test: “hear” survives.
Path is a direction, but bind caught the half-performance.

```
/comment
```

Comment (no tag): this record is for catching the template in the
second image before it is filed as a refusal of the template.

```
/keep
!ask What does a lying net do that a torn net does not?
hold: A torn net fails the fisherman. A lying net fails the sea.
```

Clerk should say `KEEP: proposal filed · BIND spoken`. The pile now
holds a reading next to the labels — vouching chord available:
proposal and bind are `@origin:ai`; `/keep` is your attestation.
That is the outer in-breath.

### Turn 2 — place so RELIED has something to hear

```
you @ turn 2 › file: ./notes/harbour-words.txt Name only the verbs in
that file that can still be done by a child who has not yet been
taught a moral.
```

`harbour-words.txt` is the human’s own list (mend, wait, coil, spit
salt, count gulls). Inner in-breath during speech: mass on the placed
list, not on “hero.” `/probe` under the hold. No `/sheet` unless those
verbs should live as their own block. Comment if you want the record’s
purpose named without a tag.

### Turn 3 — sequel breath (LOOK on :8081)

Face, asked for one harbour image, adds “trust your inner voice.”

```
/sequel
!path toward-the-net-not-the-voice
```

LOOK (2B, whole sheet, not the face): leftover sits *off* the declared
path; “inner voice” is a noun-bucket. Not a verdict.

```
/forget
```

Next out-breath does not carry the leftover as accepted context. If
the leftover was a road you refuse to walk again, a later hand-written
block `@rejected:inner-voice-as-the-lesson @kept:specimen` is the
anti-resale chord from the tag lab.

### Turn 4 — search, name, sheet+bind again

```
search: harbour net folklore lying cloth
url: https://example.org/net-charms-note What image in this page is
not already a lesson?
```

```
/sheet
```

```
PROPOSAL
@act:keep-the-image-unmoralised
@path:out-of-the-folklore-average

BIND
The answer points at one image and stops. The act names that stopping.
The path reaches from this answer, not only from the sheet.
```

Strip-test passes; bind agrees the stopping is in the paragraph.
`/keep`. Two `@path:` values now exist in the pile to `/views` later.

### Turn 5 — edges after records exist

```
/revises 1 rejected:"the sea tests him" invariant:"the net can lie"
```

`/inquire` and `/bearings` stay on the face. They are not bind. Bind
already did its work on turns 1 and 4.

### Turn 6 — listen to the pile before another out-breath

```
/views
/fold
/shape
```

Toc (speculative): `@path:away-from-the-hero-template` gathered two
blocks; `@path:out-of-the-folklore-average` stands alone; one
`not-yet-discerned` still HELD. Shape: resemblance to the scar-story
“do not let the average finish the sentence.” Not a verdict.

The human now writes the three images *himself*:

```
file: ./draft/three-images.txt Do not improve this. Name one verb that
is still missing.
```

Face points at an absence. That is collaboration that does not flatten.

If that turn should live, `/sheet` again — propose + bind — before
`/keep`. Do not file the draft’s tags on syntax because the sitting
feels finished.

### Law

This sitting never needed `/withlaw`. The originating question was
sacred and small. Law would enter on another evening, about whether
anything but `/keep` may file tags. Then `/law` first (titles), then
`/withlaw` if the whole file is the right weight, then `/declared`.

### Close

```
!closed 1
/release <hold-ref> The distinction is now in the draft.
/exit
```

Diary kept. Tomorrow `/pile` `/views` `/open` before any new speech.

| Complaint | Phase that makes it visible |
|---|---|
| Completion before intention | `!ask` + first answer left standing |
| Fluent average | `/sequel` + LOOK + bind saying “half-performed” |
| Skipped struggle | human writes the images; face names a missing verb |
| Window forgets | pile + `/fold` + `/views` + scribe `since` / `g-keys` |
| Provenance dissolves | judged tags + bind block + `@attests:` + verbatim hold |
| Performed confidence | bind may say it cannot tell; `/keep` names absence; named empties |

---

## 8. Speculative full-command circuit

*Map of instruments in a lawful order, not a daily ritual. Bind sits
where the inner out-breath sits. Do not copy this as a checklist.*

0. `/help` `/model` `/pile` `/law` `/declared` `/held` `/open`
1. Ordinary sentence — outer out-breath
2. `/raw` — see the unsplit completion once; learn what `/sequel` holds
3. `/sequel`
4. `hold: …`
5. `!ask …`
6. `search: …`
7. `url: …` (a page you named from the hit list)
8. `file: …`
9. `html: …` (saved page + Python scribe seam)
10. `/probe` then `/probe <hold-ref>`
11. `/history` then `/history act:hear-the-net-lying` (once a tag exists)
12. `^` when the fold must enter this turn; `^^` for raw ASKED/ANSWERED
13. `/fold` then `/fold a b` after `/forget`
14. `/walk` — reveal (optional; before sheet if it should feed bind)
15. `/sheet` — propose **then** bind
16. `/bind` — only if bind did not speak
17. `/comment` — if bind cannot tell
18. `/keep` — outer in-breath of judged lines + bind speech
19. `!path toward-…` — LOOK on leftover (small lung, sequel)
20. `/shape` then `/shape path:away-from-the-hero-template`
21. `/revises 1 invariant:"…" rejected:"…"`
22. `/inquire a b`
23. `/bearings a b`
24. `/views`
25. `/skin` on, one constrained answer, `/skin` off
26. `/dial` toward the placed file, one answer, `/dial off`
27. `/press` on the hold, one answer, `/press off`
28. `/withlaw` only if this has become a governance sitting
29. `/release <ref> reason`
30. `!closed 1`
31. `/forget` or `/reset reason`
32. `/exit`

If a sitting uses every command because the list exists, the work has
been replaced by the circuit. Poverty: do not `/sheet` a turn you do
not mean to accumulate; do not `/bind` a proposal you have already
understood. Do not build a cathedral where a doorway is needed.

---

## 9. Ways this guide can fail you

- Reading bind as permission to `/keep`.
- `/keep` in the same gesture as `/sheet`, unread.
- Treating `/sheet` proposals as already true even after bind — both
  are speech until you judge.
- Treating `/walk` as the binding pass.
- LOOK expected on the face — after B+C it is on `:8081`; if LOOK
  refuses the window, start the 2B with `-c 8192`, do not amputate
  the sheet.
- Filing `@topic:` because bind was foggy.
- Putting 8B on the face and never opening Room B.
- `/withlaw` as a personality pack. Injected, clauses are performed.
- `/dial` and `/press` as obedience. You will not see the un-pressed
  out-breath.
- Letting last-N become an invisible second author. `/forget` exists.
- Hand-editing a body length and skipping `check` / `@extent:`.
- Copying the tag lab into the project pile instead of pointing at it.
- Putting Executor / Whistleblower / Proxy into this runtime. You +
  answer + quieter clerk + a small lung that proposes then binds.

---

## 10. After the sitting

Open `user-guide_pn-gf-scribe.md` §§5–9 and `TAGS-gforth.md` as format
and live core, not as a menu. Read §§6–8 before you invent keys you
intend to share with another hand.

If you hand-edit the pile: fix that block’s `@extent:` if the body
length changed; `check` until clean; never touch `@formed:`,
`@genesis:`, or `@@` at column zero. Truncation is named per block.
That is a gift. Do not spend it by silent surgery.

`g-keys` and the “NOT shown by this index” line are the reader’s half
of disclosure. A date without its question (`g-toc` on the dated key
at the start of a sitting) is a tripwire with no bell.

The originating question remains sacred. No command in this file is
allowed to dissolve it through momentum, a fluent proposal, a bind
that sounds sure, or the comfort of a technically complete circuit.
