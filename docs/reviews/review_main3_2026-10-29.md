# Review of main(3) — Related Work & Method

(See `review_main3_highlighted.html` for the same points shown on the actual paragraphs,
with the change-spots highlighted.)

## Related Work — one clunky sentence

The last sentence reads a bit clunky:

> …EBV instead gives fields and tables a shared accept-or-route decision, using document
> evidence suited to each output type **and, for fields, historical priors,** without another
> generative-model call.

Suggested rewrite (puts the aside in parentheses so it stops interrupting the sentence):

> **EBV instead gives fields and tables a shared accept-or-route decision, computed from
> document evidence (and, for fields, historical priors) without another generative-model call.**

## Method — this section reads rough; please take it from my version

The method prose is the one section that still needs work. Specific points:

**§3.1 Accept or route**
1. "A pipeline **returns units**." reads awkward → "An extraction pipeline **returns its
   outputs as units**."
2. The accept/route decision is buried in "EBV **outputs** accept… or route…" — make the
   two-way choice explicit: "For each unit, EBV **returns one of two decisions: accept**
   (processed automatically) **or route** (sent to a reviewer)."
3. "A document is accepted only if all its units **are**," is **missing a word** → "…only if
   all its units **are accepted**."
4. Verb mismatch: "so one doubtful value **sends** the whole document for review" → "**routes**
   the whole document" (match the "route" decision).
5. "An upstream label says whether a document is structured, and EBV does no classification of
   its own. **Tables go to** Table-Trust, fields… **go to** ROI and all other fields **go to**
   Signal." reads as separate systems and buries the point. Restructure — lead with the
   no-classification point and frame routing as one verifier picking a mode: "**EBV does no
   classification of its own; an upstream label marks each document as structured or not, and
   that label determines how each unit is routed: tables to Table-Trust, fields in structured
   documents to ROI, and all other fields to Signal.**"

**§3.3 Unstructured fields (Signal)**
6. "…statistics learned from labelled history. **None needs** a generative model or another
   OCR pass." → combine into one sentence: "…statistics learned from labelled history,
   **none of which needs** a generative model or another OCR pass."
7. The signals start abruptly ("Format validity checks that…"). Add a lead-in and list them
   cleanly: "**The signals are:** format validity, that the value has the right form for its
   field; value-in-text, that it appears on the page; keyword context, source context and
   label–value distance, that the surrounding words and position fit the field; and
   cross-field copy, that a value is repeated from another field." Also tighten the emptiness
   bit: "Two more features describe emptiness. One says whether the value is empty, and the
   other is the field's historical empty rate, the field prior." → "**Two features describe
   emptiness: whether the value is empty, and the field's historical empty rate (the field
   prior).**"
8. "…the one with higher accuracy on a held-out part of the labelled training data is used,
   **so test data play no part in the choice**." — the last clause is unnecessary; "a
   held-out part of the labelled training data" already says that. **Remove it.**

**I've already made all of these method fixes in my version (`_best.md`).** The method there
is mostly yours, with these manual fixes applied — so the cleanest path is to take the Method
section from `_best.md` directly rather than re-editing main(3).

## Experimental Setup

**Datasets & Extractors — same, fine.** (One tiny thing: Extractors still says "Their
**mistakes** are the **errors** EBV must catch" — mistakes/errors is a touch redundant;
"Their errors are what EBV must catch" is cleaner. Minor.)

**Correctness labels (ground truth) — the wording is fine, but the ordering is clumsy.** The
paragraph jumps around. The issues (the same ones I raised before):
1. The scoring method (exact match / containment) is **common to both public and proprietary**
   data — so state it once up front, then give the gold source for each. Your opening
   ("comparing it with the dataset's gold value") reads as if the dataset label is the gold for
   everything, and then the proprietary sentence quietly contradicts it.
2. Make public vs proprietary gold an **explicit parallel**: "On the public benchmarks the gold
   value is the dataset label; on the proprietary corpus it is the production system's finalised
   value, human-corrected where needed."
3. The **FATURA** exact-match caveat should sit with the public-benchmark discussion (**before**
   the proprietary sentence). Right now it comes after proprietary, so the paragraph jumps
   public → proprietary → back to public (FATURA).
4. "On the unstructured benchmarks we evaluate scalar key–value fields" lands abruptly — give a
   **reason** ("the single values a containment check can score") and keep it in the fields group.
5. Group all the **field** content first (scoring → gold → FATURA → scalar), **then tables**.
   Right now they're interleaved.

Fix: either reorder yours along these lines (keep your wording), **or take the GT paragraph from
`_best.md`** — it uses the **same simple wording (close to main(2)), I only changed the ordering
to make it read more professionally.**

**Splits and training — two things to fix:**
- **Split it into "Splits." and "Training."** The two are different things — how the data is
  divided (splits) vs. how the models are trained — so splitting them reads cleaner and more
  professional. (Deepak also advised not to combine different things into one block.)
- "…set on production mortgage tables **and applied to RD-TableBench unchanged**." Words like
  "**unchanged**" (and "without re-tuning") carry a **defensive, negative** tone — drop it
  (just "…set on production mortgage tables"). **Please apply this everywhere such negative
  wording appears**, not only here.

**Baselines & Metrics — same, fine.** (Metrics protocol and numbers are correct; only a tiny
comma polish differs.)

### Setup components — what I flagged vs. done in main(3)

| Component | Flagged | Done in main(3)? |
|---|---|---|
| Datasets | (same) | n/a — unchanged, fine |
| Extractors | "mistakes/errors" redundancy | No (minor) |
| Correctness labels (GT) | reorder for flow (5 points above) | **No** — wording changed, ordering still clumsy |
| Splits + Training | split into two; drop "unchanged" | **No** on both |
| Baselines | "has" → "exposes" (minor) | No (minor) |
| Metrics | comma polish only | n/a — correct as is |

## Results

Numbers, tables and figures are all correct — these are prose/readability fixes only.

**§5.1 Fields**
1. First sentence: "…better than the signals the pipeline **has** without an extra model call"
   → "…the signals the pipeline **exposes** without an extra model call." (minor)
2. "The strongest such baseline reaches **0.63, the per-field prior on S-1,** and value-in-source
   reaches 0.53–0.59." — the commas make this read like a three-item list (0.63 / the prior on
   S-1 / value-in-source). Use a bracket: "…reaches **0.63 (the per-field prior, on S-1)**, and
   value-in-source reaches 0.53–0.59."

**§5.2 Tables**
3. "…the threshold of 85 set on production mortgage tables**, without re-tuning**." — "without
   re-tuning" is the same defensive/negative wording; drop it (just "…set on production mortgage
   tables"). Same "apply everywhere" point as §Splits.

**§5.3 Proprietary production data**
4. Add the introductory commas: "On fields**,** the extractor is wrong…" and "On loan
   applications**,** 86%…". (minor)
5. "Ranking stays strong there, yet little can be auto-accepted**, the gap between capability and
   coverage**." — the trailing "the gap…" dangles → "…yet little can be auto-accepted,
   **opening a gap between capability and coverage**."

Worth prioritising: **#2** (the 0.63 bracket — real ambiguity) and **#3** ("without re-tuning").
**#5** is a quick clunk fix. #1 and #4 are trivial.

## Analysis (§6)

Numbers are all correct and paras 1 and 3 are fine. The one thing worth changing is **para 2**
("On free-form fields, the empty-field prior carries the most weight"). The content is good —
the empty-field-prior ablation (removing it drops AUROC 0.957 → 0.654, Δ0.30) — but the
**ordering is a bit poor**:
- It gives the **result before the method**: "Removing the empty-field prior lowers AUROC from
  0.957 to 0.654 (Δ0.30)…" comes first, and only two sentences later does the reader learn
  where that number came from — "This comes from a drop-one ablation on a surrogate tabular
  classifier…". The number lands before we know what produced it.
- The **scope caveat dangles**: "About 95% of its instances are S-1, so the result describes
  S-1." sits on its own, detached from the method it belongs to.
- Two choppy sentence pairs: "…overlap heavily. Dropping any single one…" and "The claim has
  limits. On FCC…" — better joined with a colon.

Better order (method → scope → result → interpretation): open with the ablation and its S-1
scope, **then** give the Δ0.30 result (causally linked, "…because many errors are empty
outputs…"), then the content-redundancy point, then the scoped limit — and join the choppy
pairs.

**My `_best.md` para 2 is already reordered this way** — same facts, same numbers, just
method-first and less choppy. If you agree it reads better, take it from `_best.md`; if not,
ignore — it's flow only, not correctness.
