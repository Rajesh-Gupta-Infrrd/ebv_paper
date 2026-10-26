# Evidence-Based Verification for Document AI — Explainer Companion (v3)

**Purpose:** your personal reference. For each part of the spec it gives *what it is*, *why it's there*, and answers to the questions that came up while we worked through it. When a concept feels fuzzy again, read the matching section here.
**Pairs with:** `evidence_based_document_ai_verification_research_spec_v3.md`
**Date:** 2026-09-28

---

## How to read this document

Every section maps to a section of the spec. Format:
- **What it is** — plain definition.
- **Why it's there** — what it buys the paper.
- **Q&A** — the specific confusions we cleared up, in question form.

---

## 1. Framing — "one system, three modes"

**What it is.** We stopped calling this "NTP" and reframed it as *checking whether a document-AI answer is trustworthy, using only cheap evidence in the document (no second AI)*. The three systems you built (ROI, Signal, Table Trust) are **three modes of one system**, chosen by a router based on input type.

**Why it's there.** A paper about "three NTP systems" reads as engineering and gets rejected. A paper about *one method that maps which errors document evidence can and cannot catch* is science. The reframe is what makes it publishable.

**Q&A**
- *Are we showing three separate systems or one?* **One system, three modes.** Not one program that merges everything (they work on different inputs), but one **method + one output + one evaluation**, with a router picking the mode. Analogy: one lab that runs a blood test, an X-ray, or a urine test depending on the sample — one lab, three tests.
- *What makes it "one system" if the modes differ?* The shared **formulation** (evidence → decision), shared **output** (corroborated/contradicted/insufficient → accept/review), and shared **evaluation**. Not a shared model.
- *Where do semi-structured / checkbox docs go?* Semi-structured (paystubs, statements) → **unstructured mode**. Checkboxes/signatures → **out of scope** (stated as a coverage gap).
- *Is "verify if correct" the right phrase?* Say **"supported or contradicted by evidence,"** not "correct" — the system never truly knows correctness; it reads evidence.

---

## 2. Research object

**What it is.** The notation for "one thing we evaluate": `x` (document), `y` (the AI output), `c` (is it actually correct — known only offline), `E` (evidence readings), `A` (which channels were available), `F` (error family), `decision`.

**Why it's there.** It forces every experiment to separate *evidence*, *availability*, and *cost* — and to keep ground truth out of the decision.

**The one formula to remember:**
```
decision = f(E, A)      ← uses only evidence + availability, NEVER c (correctness)
```
`c` is used *only later, offline*, to grade how well `f` did.

**Q&A**
- *Is the JSON record a contribution?* No — it's bookkeeping. Don't let it look like a contribution in the paper.
- *Why log per-channel continuous scores?* Because the constructs need each channel's output per item. If you only save the final label, you'd have to re-run everything. Logging turns "re-run" into cheap "re-score."

---

## 3. The constructs — what they are and why

> Constructs are **offline measurements** (metrics) that turn "our system works" into a generalizable finding. They are the *analysis lens*, **not** the runtime routing logic. Tier-1 metrics (accuracy, coverage) say *how well*; the constructs say *why and where*.

### 3.1 Detectability (core)
**What.** For each error type and each channel: if the output is wrong, does the channel flag it? Every error is *catchable / partly / invisible*. The **frontier** = errors no channel can catch.
**Why.** This is the finding that makes it a paper, not a product report. Produces the quotable line: "misreads are invisible, row-omissions are catchable."

### 3.2 Complementarity (core)
**What.** Not "which channel is best," but "does channel B catch errors A *missed*?" Measured by unique capture and marginal utility.
**Why.** Justifies *why you combine channels*, and gives the claim "a weak channel that fails *differently* beats a strong one that repeats the AI's mistakes." It's the general form of your Table-Trust witness-independence rule.

### 3.3 Oracle ceiling + decomposition (core; the frontier)
**What.** An imaginary perfect combiner catches an error if *any* channel could (at a fixed 5% false-alarm rate). Splits errors into *caught / could-have-caught-but-missed / impossible*.
**Why.** Separates "we need a better model" (fixable) from "no model could do better" (the frontier). This is your headline (H5).

### 3.4 Sufficiency (OPTIONAL)
**What.** A per-item score: given the clues available for *this* item, how much of the likely error space could we inspect?
**Why.** Distinguishes "checked and clean" from "couldn't really check." An honesty layer.

**Q&A**
- *Do the constructs add value / do we even need them?* Yes — without at least one construct you have a system report, not a paper. But you need the *minimum* set: **detectability + complementarity are essential; sufficiency is optional.** More constructs ≠ better paper.
- *Do we use these constructs to route/label at runtime?* **No.** The runtime routes using channels + fusion + evidence state. The constructs are computed *offline* to study the system. (Sufficiency is the only partial exception — its INSUFFICIENT state can feed a runtime escalation.)
- *So they're just metrics?* Yes — specifically the *diagnostic/explanatory* metrics (how much was detected, of what kind, by what, and what's impossible).
- *Detectability vs sufficiency — same thing?* Not identical, but sufficiency is **built from** detectability. Detectability = a general average across the data; sufficiency = that average applied to one item using *which channels were available for it*. The only new ingredient in sufficiency is per-item channel availability — which is why it's nearly redundant and kept optional.
- *Why is sufficiency "hard" — is it a time issue?* Not time. It's (a) it may just repeat the risk score (you only find out after testing), (b) it needs error-type prevalence counts (annotation), (c) channels overlap so you can't just add them up, (d) it only matters if it varies per item, (e) proving it works needs its own dropout experiment. So: keep it only if it beats risk-alone.
- *"NTP for NTP"?* Yes — sufficiency is a confidence-check on the confidence-check: "we said this looks fine, but were we even in a position to check?"

---

## 4. Hypotheses — what each proves and our verdicts

| ID | Plain meaning | Verdict & why |
|---|---|---|
| **H1** | Zero-LLM evidence beats equal-cost baselines and is *cheaper for the coverage it gives* than LLM verification. | **Keep.** We softened part (b): don't promise "match the LLM" (it might win) — promise a **better cost/coverage trade-off**. That can't be lost. |
| **H2** | Different clues catch different error types (the detectability map). | **Keep.** Core. |
| **H3** | A clue's *unique* catch predicts its stack value better than its standalone accuracy. | **Keep, but not as novelty.** It's a *known* ensemble idea (diversity > accuracy) shown in a new setting. It justifies combining channels. |
| **H4** | Risk + sufficiency beats risk alone. | **Optional.** Tied to sufficiency. Include only if it helps. |
| **H5** | A real share of errors is undetectable by any clue; saying so avoids false "verified" claims. | **Keep — the novelty pillar.** |
| **H6** | Clues that read the document survive shift better than learned priors. | **Optional analysis.** Frame around *what survives* — ROI failing on unseen templates is near-definitional, so don't over-claim it. |

**Q&A**
- *If H5 shows the system misses catchable errors, won't people think it's useless?* No — the "observable-but-missed" bucket is **recoverable headroom**, not a flaw. You *use* it to improve fusion and report the better version. An honest split (caught / fixable / impossible) is *more* credible than claiming 100%.
- *Do H3 and H5 contradict?* No — different levels. H3 = channels *could* add value (potential). H5 = how much the fusion *actually* captured. One is ingredients, the other is cooking.
- *Why keep H6 — just to admit ROI breaks on new templates?* Partly honesty, but the useful part is *which clues survive*. It's nearly free if the shift test runs; frame it around survival, not ROI's expected failure.

---

## 5. Evaluation protocol — each piece explained

### 5.1 Error definitions (defines `c`)
**Fields — "normalised prediction ≠ normalised GT; empty vs empty = correct."**
- **Prediction** = what the AI pulled; **GT** = the true answer.
- **Normalise** = clean both to a standard form before comparing, so `10/24/2025` and `10-24-25` (same date, different text) don't count as an error. Per-type normalisers = a date cleaner, a currency cleaner, etc.
- **Empty vs empty = correct** = if the field is genuinely blank and the AI returned blank, that's right.
- **Why:** every number in the paper sits on this definition, so it's frozen early.

**Tables — "TEDS < 0.9."** TEDS = a 0–1 table-similarity score (structure + content). Below 0.9 = error. Threshold fixed before scoring so it can't be gamed. Secondary "any cell mismatch" shows it's not threshold-tuned.

**Document-level:** a document passes only if all its fields pass — because production routes whole documents.

**Q&A (important — two kinds of "error"):**
- *Is §8.1 about our system's error, or the extraction's error?* It defines **Level 1 — the extraction's correctness** (`c`): using GT, is the extracted value right?
- *Then where is OUR system's error?* **Level 2** — the verifier's flag vs `c`. Measured by **escaped errors** (accepted a wrong one) and **false reviews** (reviewed a correct one) in the metrics.
- **The chain:** GT value → compare to extraction (§8.1) → `c` (correct/wrong) → compare to the verifier's flag → verifier right/wrong. §8.1 is the step *before* measuring your system's error, and one GT serves both.

### 5.2 Splits
- **Document-disjoint:** no document in both train and test (prevents the model leaning on memorised template patterns). Confirmed your test sets already do this — so the scores are genuine and reusable.
- **Calibration ≠ test; freeze before test:** tune thresholds on one set, measure on another, and lock every knob before touching the test set.
- **Q&A:** *held-out ≠ shift.* A held-out test = same kind of docs, unseen. A shift test = *deliberately different* docs (new template/vendor/time/extractor). Your held-out scores cover the first; the shift test is a separate thing.

### 5.3 Metrics
- **Risk-coverage curve:** coverage = share you auto-accept; risk = error rate among accepted. The curve shows the trade-off as you slide the threshold. **Why:** the core picture for accept/review systems.
- **AURC:** one number summarising the curve.
- **Coverage at risk ≤ 1/2/5%:** "if I allow ≤2% error, how much can I auto-accept?" How a business actually thinks.
- **Escaped errors / 10k accepted:** wrong ones that slipped through — an absolute, gut-level number.
- **False reviews / 10k correct:** wasted human effort.
- **Error capture at review budget:** "if I can review 10%, what share of errors do I catch?" Output + document level; incident-level optional (needs root-cause grouping so one OCR failure isn't counted ten times).
- **Cost + Pareto frontier:** LLM calls/tokens/latency; the frontier = the non-dominated methods in (cost, risk, coverage). This is where the softened H1(b) lives.
- **Certified risk (binomial bound):** not "observed 1.4%" but "95% confident it's ≤1.9%." Document-level (fields in a doc are correlated). *Conformal dropped* — it assumes new data looks like test data, which breaks under shift.
- **GT-quality double reporting:** report every headline number twice — all errors, and clean (certain + legible) GT only. **Why:** if the "undetectable" bucket is really bad GT, the frontier claim collapses; clean-GT reporting proves it's real.
- **Uncertainty:** 95% CIs by *document-level* bootstrap (field-level gives fake-tight bars because fields in a doc are correlated); count *errors*, not outputs; ≥200 errors per testbed.
- **Validity (placebo):** report headline gains *with* the placebo result (below).

### 5.4 Baselines
- **Equal cost (must beat):** extractor log-prob/confidence; your existing production rules.
- **Higher cost (show a better trade-off):** self-consistency, self-check, dual-LLM, second parser (tables), VLM judge.
- **OPEN:** do extractors expose log-probs? what's the VLM-judge budget? (Team to confirm.)

---

## 6. Experiments — each one, and reuse-vs-rerun

> **The key principle:** you do **not** re-run the extractor. Extractions + GT already exist. You **re-score the cheap channels** (with per-channel logging) on **clean splits**, then count. Logging is what makes this cheap.
>
> **Readiness:** most instrumentation is already done — Table Trust already logs per-signal scores and runs docTR; Signal's splits are already document-disjoint; ROI's components are logged where runs saved them. So the remaining real work is **error annotation (E3b)** plus the optional additions — not re-running or rebuilding the systems.

| ID | Plain description | Reuse or new? | Verdict |
|---|---|---|---|
| E0 | Load outputs + baselines into one format, with per-channel continuous logs | re-score + run baselines | Keep (refined) |
| E1 | Main comparison (risk-coverage + cost) | uses E0 | Keep |
| E2 | Turn each clue on/off | **recombine logs + re-fit the cheap fusion — NOT a re-run** | Keep |
| E3a | Inject known fake errors, see which clue catches each | new (mutate the *output*, re-score — not re-extract) | Optional gap-filler |
| E3b | Label *real* errors by type | **annotation** + re-score | Keep (critical) |
| E3c | Specificity disclosure | — | **Removed** |
| E4 | What each clue uniquely catches | re-score | Keep |
| E4b | Do same-OCR clues overlap | analysis | Optional (needs witness) |
| E4c | Caught / missed / impossible split (oracle) | re-score | Keep (headline) |
| E5 | Sufficiency + remove-clues-on-purpose | new + re-score | Optional (pilot-gated) |
| E5b | Feed shuffled evidence; advantage must collapse | **permute logs + re-score — cheap** | Keep (mandatory) |
| E6 | Test on genuinely different docs | rerun/re-score on a different slice | Keep (partly done) |
| E6b | 95% risk bound | stats calc | Refine (binomial only) |
| E7 | Auto-generate labels (GT-free) | — | **Removed** |
| E-cost | Free vs cheap-OCR vs LLM (catch vs cost) | independent-witness run | Added (optional) |
| P1 | Independent witness for fields (docTR on crops, offline) | independent-witness run | Optional (needs images) |

**Q&A**
- *E2 needs a re-run, surely?* No. If each clue's output was logged, you just **drop that clue's column and re-run the tiny fusion step** (seconds). You never re-run OCR or the extractor. This is the payoff of logging.
- *Do we have to do E3a (corruption)? It sounds hard.* You can get H2 and H5 from **natural errors alone (E3b)**. Corruption is a *gap-filler* for rare error types. Also, corruption ≠ re-extraction — you **mutate the stored output** (change a digit, drop a row) and re-score. The only work is writing the mutation functions.
- *Is E5b (placebo) hard like corruption?* No — it's **cheap**: shuffle the logged clue scores (give one field's ROI to another) and re-run the cheap fusion. Keep it — it's the anti-cheating proof.
- *Is E6 (shift) already done?* Partly. Confirm two things: (1) is your "new docs" test a *genuinely different distribution* or just held-out same-type? (2) do you have per-clue logs on it (for H6)? The **extractor-swap** version (verify outputs from a *different* extraction model) is probably new — worth one run.
- *Do we need the docTR (witness) run — isn't it in the list?* It's a **prep step (P1)**, not a hypothesis experiment. For **tables it's already inside E0** (Table Trust runs docTR). For **fields it's optional** — crop the field bbox, run docTR offline on stored images, compare, log. Not a production change.

---

## 7. Failure families

**What.** A small set of error types (misread, wrong-but-plausible value, omission, row loss, merge/split, …), grouped so each has enough examples (~30+) for stable numbers. Grouped from ~15 flat down to ~7 field + ~5 table buckets. Added "partial/truncated value."

**Why.** They are the **rows of the detectability map**, the definition of the **frontier**, and the drivers of corruption. They organise the *miss side* (caught vs escaped), not false alarms.

**Q&A**
- *Is the list just a failure catalogue / about FP-FN?* More than that — it's the analytical unit for the whole detectability story. It relates to the **miss side (escaped errors / FN)**, not false reviews (which come from correct outputs and have no error family).
- *Did we remove any family?* No — we **grouped** them (nothing thrown away), because deleting a family loses a data point. The only merge was cell-shift/span/permutation → "structural corruption"; the only addition was "partial/truncated value."

---

## 8. Fusion (the combiner)

**What.** The step that combines the channel scores into one decision. You already have one per mode: ROI weighted vote, Signal tree model, Table-Trust weighted score.

**Why the decisions.** Keep each mode's **tuned combiner as primary** — replacing it with a generic one would degrade your genuine results. A single simple common fusion is an **optional back-pocket comparison** (to support "it's the evidence, not the model" and to answer any "not really one system" objection). Not a replacement, not a promise.

**Q&A**
- *Do we need one dedicated fusion model doing the same in all three?* No. "One system" comes from shared formulation/output/evaluation, not a shared combiner.
- *Won't a generic combiner give worse results?* Yes, possibly — which is exactly why you **keep your tuned combiners**. The generic one is optional and only reported if it helps.
- *Do the constructs depend on the fusion?* Mostly no — detectability, complementarity, and the oracle *ceiling* are computed at the channel level, independent of the combiner. (Only the caught/observable-but-missed split uses the combiner.)

---

## 9. Reproducibility (why we still care, without releasing private things)

**What.** Keep private data and production code private. Make the **public RD-TableBench result a first-class headline**, and describe the method fully (as normal).

**Why.** Reproducibility is not just for competitions — reviewers distrust results they can't check. But it does **not** require releasing private data/code. The middle path (standard for industry papers): one public-data result + full method description + optionally the generic artifacts (taxonomy, corruption generator, eval harness).

**Q&A**
- *Why disclose anything — it's private?* You disclose **nothing sensitive.** You lean on the public RD-TableBench leg and describe the method (which you do anyway). A paper that is 100% on secret data with nothing checkable gets "can't verify / unclear generalisation" — a real acceptance risk, not a rule.

---

## 10. The end-to-end flow (how the approach works, start to finish)

**Layer A — Runtime (a real document; NO ground truth):**
```
1. INPUT: an AI output (field or table) + the source document
2. ROUTER: pick the mode by input type (structured field / unstructured field / table)
3. GATHER EVIDENCE: run the channels for that mode
4. EACH CHANNEL: support / contradict / neutral + a continuous score (logged)
5. FUSION (the mode's tuned combiner): channel scores → one trust score
6. EVIDENCE STATE: corroborated / contradicted / conflicted / insufficient
7. DECISION: accept (NTP) / send to review  (+ optional escalate when insufficient)
```
**Layer B — Offline evaluation (ground truth lives ONLY here):**
```
1. GT labels each output correct/wrong (§8.1) — the label the verifier should predict
2. Use the logged channel scores + annotate real errors by family
3. Compute: performance (H1), detectability map (H2), complementarity (H3),
   oracle decomposition/frontier (H5), placebo (validity), shift (H6)
```
**The rule that ties it together:** the verifier (Layer A) never sees GT; GT (Layer B) only grades it and measures what is undetectable.

---

## 11. Quick decision ledger (what we changed and why)

| Area | Decision | Why |
|---|---|---|
| Framing | One system, three modes; drop "NTP" as the framing | Turns engineering into science |
| Constructs | Detectability + complementarity core; **sufficiency optional** | Sufficiency ≈ per-item re-mix of detectability |
| H1 | Soften (b) to a cost trade-off | LLM might win on coverage; trade-off can't be lost |
| H3 | Keep as *supporting*, not novelty | Diversity-beats-accuracy is a known idea |
| H4, H6 | Optional | Secondary; frame H6 around survival |
| H5 | Novelty pillar | The frontier is the distinctive result |
| Eval | Promote oracle decomposition; require per-channel logging; tie placebo to headlines; drop conformal; incident-level optional | Rigor + honesty; keep the strong core |
| Experiments | Remove E3c, E7; E3a optional gap-filler; E4b/E5/E-cost/P1 optional | Cut scope to one clean story |
| Failure families | Group to ~7+5; add partial/truncated | Statistical density |
| Scope | Semi-structured → unstructured; checkbox/signature out | Clear boundaries |
| Reproducibility | Private stays private; public RD-TableBench first-class | Credibility without disclosure |
| Fusion | Keep tuned combiners; simple common fusion optional | Don't sacrifice real results |
| Ablations | Core: family (via E2) + support-vs-contradiction; conditional: OCR-swap (tables), sufficiency, corruption-calibration; **drop** dependency/provenance, native-vs-common-fusion, typed-generic-experiment | Feasibility + focus |
| Paper structure | Standard NAACL skeleton — abstract + mandatory Limitations + advisable Ethics; channels before system; ablations/robustness/reliability/validity grouped under Analysis; held-out = main results | Reviewer expectations |
| Novelty | Keep the novelty statement + guardrails; defer the citation list to writing | A planning spec isn't a lit review |
| Scope reasons | GT-free out (claim would be *false*); repair out (a *different* research question) | Truthfulness + focus |
| Risk register | Kept but refined — overfit row removed, trimmed to core risks; labelled internal-planning | Useful for planning, not paper content |
| Table Trust | Not tuned to RD-TableBench (only wrong computations were corrected) — no "overfit" framing | Accuracy about the system |

---

*If a concept still feels unclear after reading its section here, the shortest anchor is: **the verifier reads document evidence to reach ground truth's conclusion without seeing ground truth — and the paper's job is to measure which errors that evidence can and cannot catch.***
