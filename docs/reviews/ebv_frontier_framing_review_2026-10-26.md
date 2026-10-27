
To credibly title the paper “The Detectability Frontier of Document Extraction Errors,” you need to establish a boundary that depends on the available evidence—not merely on one verifier’s
  score or threshold.

  A reviewer should be able to distinguish:

  1. Errors detected by the current EBV implementation.
  2. Errors missed by EBV but detectable from the same evidence.
  3. Errors that cannot be distinguished from correct outputs using that evidence.
  4. Errors that require additional evidence or another model call.

  Your current median-score definition does not make these distinctions.

  ## 1. A precise definition of detectability

  Define the available evidence for an extraction (u) as (E(u)): OCR text, boxes, field name, extracted value, table HTML, and any other artifacts allowed under the stated cost regime.

  An error is detectable under evidence set (E) if some decision rule using only (E) can distinguish it from correct outputs above a predefined statistical standard.

  Conceptually:

  [
  D_E(u)=1
  \quad\text{if evidence in }E(u)\text{ contains an observable contradiction or absence of required support.}
  ]

  Then separate:

  - Verifier-detected: EBV catches it.
  - Observable but missed: evidence contains a usable signal, but EBV fails to exploit it.
  - Evidence-indistinguishable: the permitted evidence is equivalent, or practically indistinguishable, to evidence associated with correct outputs.
  - Source-ambiguous: even a human inspecting the original document cannot determine correctness.

  This taxonomy is essential because “EBV assigned a high score” does not imply “the error was undetectable.”

  ## 2. Explicit evidence regimes

  A frontier is always relative to what evidence is permitted. Define a nested sequence such as:

  [
  E_0 \subset E_1 \subset E_2 \subset E_3
  ]

  For example:

  - (E_0): extracted output only.
  - (E_1): output plus structural and format signals.
  - (E_2): output plus upstream OCR text and geometry.
  - (E_3): output plus an independent OCR witness.
  - (E_4): source image plus a generative VLM judge.
  - (E_H): full human inspection.

  Then measure how the residual-error set shrinks as evidence increases.

  This would create an actual empirical frontier:

   Evidence regime           Cost    Errors detectable    Residual errors
  ━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━
   Output only            Minimal                    …                  …
  ─────────────────────  ─────────  ───────────────────  ─────────────────
   + upstream OCR             Low                    …                  …
  ─────────────────────  ─────────  ───────────────────  ─────────────────
   + independent OCR       Medium                    …                  …
  ─────────────────────  ─────────  ───────────────────  ─────────────────
   + generative judge        High                    …                  …
  ─────────────────────  ─────────  ───────────────────  ─────────────────
   Human source review    Highest                    …                  …

  The frontier would mean:

  > At a given evidence and cost budget, these errors remain inseparable or unresolved.

  That is much stronger than selecting the median of a fused score.

  ## 3. A strong oracle for each evidence regime

  For each regime, build the best reasonable detector permitted to use that evidence. Otherwise, a missed error could simply reflect a weak implementation.

  Possible approximations include:

  - A flexible supervised classifier trained on all permitted channels.
  - Cross-validated ensembles.
  - Rule-based contradiction detectors plus learned fusion.
  - Independent judges restricted to a particular evidence view.
  - Human evidence annotations.

  All hyperparameters and thresholds must be fitted outside the test set.

  You do not have to prove mathematical impossibility, but you must show that several sufficiently expressive detectors cannot separate the residual cases.

  A defensible formulation is:

  > We estimate an empirical detectability frontier rather than claiming a fundamental information-theoretic limit.

  ## 4. Matched or counterfactual cases

  The strongest evidence for indistinguishability is a pair consisting of:

  - One correct extraction.
  - One incorrect extraction.
  - The same—or nearly the same—observable evidence under regime (E).

  Examples:

  - The same field location and geometry, but one document contains a correct value and another contains an extractor substitution.
  - The same valid format and nearby label, but the extractor selects the wrong duplicate occurrence.
  - Identical table topology and token inventory, but cell assignments are permuted.

  Measure whether humans or classifiers restricted to (E) can distinguish the pair. If they cannot perform above chance, that supports an evidence-relative frontier.

  Without matched cases, high verifier confidence may simply indicate poor feature engineering.

  ## 5. Controlled corruptions

  Generate errors that preserve selected evidence while changing correctness.

  Examples:

  - Replace a value with another value of the same type from the same document.
  - Copy an adjacent field’s value.
  - Change one digit while retaining format and location.
  - Swap duplicate occurrences of the same value.
  - Permute table cells while preserving dimensions and token counts.
  - Drop a table row while preserving valid HTML structure.

  Each corruption should be associated with the evidence it preserves and destroys. This lets you test causal hypotheses:

   Corruption                 Format    Source presence            Geometry    Independent OCR agreement
  ━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Cross-field copy        Preserved          Preserved             Changed           Possibly preserved
  ──────────────────────  ───────────  ─────────────────  ──────────────────  ───────────────────────────
   In-place digit error    Preserved       Often broken           Preserved                       Broken
  ──────────────────────  ───────────  ─────────────────  ──────────────────  ───────────────────────────
   Table permutation       Preserved          Preserved    Partly preserved     Depends on reading order

  This would turn the detectability map into a controlled experiment instead of only a post-hoc taxonomy.

  ## 6. Independent human annotation

  For every candidate frontier error, annotators should answer questions such as:

  1. Is the extraction actually wrong?
  2. Is the source document legible?
  3. Which permitted evidence channel reveals the error?
  4. Could a verifier using only (E_k) detect it?
  5. What additional evidence is minimally required?

  Use:

  - At least two annotators.
  - Blinding to EBV scores and decisions.
  - A written rubric.
  - Overlap and agreement statistics.
  - Adjudication for disagreements.

  The important result is not merely “the correct answer is visible.” It is:

  > Under evidence (E_2), annotators found no observable contradiction; under (E_3), an independent OCR reading exposed one.

  That directly maps the frontier across evidence regimes.

  ## 7. Proper calibration and untouched testing

  All decisions that define the frontier must be frozen before test evaluation:

  - Evidence channels.
  - Signal directions.
  - Thresholds.
  - Risk budgets.
  - The definition of “indistinguishable.”
  - Failure-family taxonomy.
  - Corruption families.
  - Model selection.

  Use train/calibration/test separation, grouped by document or filing. Otherwise the frontier adapts to the observed test errors.

  ## 8. Uncertainty and sufficient error counts

  The unit of analysis is the error, but dependence occurs at the document, template, filing, and source levels.

  You need:

  - Document- or source-clustered confidence intervals.
  - Exact intervals for small failure families.
  - Enough natural errors in each major family.
  - Sensitivity to thresholds and evidence definitions.
  - Separate natural-error and controlled-corruption results.

  Six bad ParseBench tables cannot establish a table frontier. They can provide examples, but a frontier claim needs a materially larger error set.

  ## 9. Cost must be part of the frontier

  The most natural frontier for this paper is not purely detectability. It is:

  [
  \text{risk} \leftrightarrow \text{coverage} \leftrightarrow \text{inference cost}
  ]

  For each evidence regime, report:

  - Residual risk.
  - Automation coverage.
  - Error capture.
  - False-review rate.
  - Latency.
  - GPU/CPU requirements.
  - Monetary cost if applicable.

  This gives a credible industry interpretation:

  > Additional evidence moves the detectability frontier, but at increasing operational cost.

  The docTR table result already points in this direction: structural evidence is cheaper, while independent OCR catches additional content errors.

  ## Minimum version feasible for this paper

  To retain “detectability frontier” in the title, I would minimally require:

  1. Rename it empirical, evidence-relative detectability frontier.
  2. Define at least three nested evidence regimes.
  3. Freeze thresholds on calibration data.
  4. Correct AUROC and bootstrap computations.
  5. Add simple but strong oracle models for each regime.
  6. Run controlled corruptions targeting the main error families.
  7. Blindly annotate every residual error with two annotators.
  8. Report matched correct/error examples.
  9. Include confidence intervals and sensitivity to frontier definitions.
  10. Measure the cost of each evidence regime.

  Then the title could safely become:

  > The Evidence-Relative Detectability Frontier of Document Extraction Errors

  That wording matters: it does not claim errors are universally or fundamentally undetectable. It claims that detectability changes with the available evidence.

  Without those additions, “operational blind spots” is the more accurate term.
