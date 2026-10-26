# EBV Paper — Related Work, Prior-Art Threats & Novelty Positioning

**Purpose:** the related-work foundation for the paper, plus an adversarial prior-art review (researcher-vs-reviewer debate) that stress-tests our novelty. Produced from two reviewer-persona passes + the researcher's own search.
**Date:** 2026-10-01 · **Status:** for team review — *the novelty verdict below is consequential; read §0 first.*
**Companion docs:** `…_research_spec_v3.md`, `…_explainer_v3.md`, `…_dataset_exploration.md`

> ⚠️ **Citation caveat:** foundational citations (§2) were web-verified. Several 2026 "threat" papers (§3) use this-year arXiv numbering gathered via search; a few have *partial/unverified metadata* (flagged). **Verify every threat-paper citation against the actual PDF before the paper goes out.**

---

## 0. Executive summary — the honest novelty verdict

> **Post-read update (2026-10-05):** the five closest papers were since **read in full** (§3a) — all confirmed real. The deep-read *improved* our position on two axes: **(1) every document competitor spends at least one extra model call** (ExtractConf: 2 GPT-4o calls; Perception/Layout/Validation: extra VLM passes; RaV-IDP: VLM fallback; ConfBench: verbalized call), so our **zero-extra-model-call** claim is genuinely differentiated; **(2) none measures a detectability ceiling for documents.** So the defensible contribution = **zero-extra-model-call + the first document detectability-floor measurement + fields-and-tables**. The fields *concept* remains occupied (demote fields work to supporting engineering, not headline). See §3a.

**The 2024–2026 neighbourhood is crowded, and our novelty is more exposed than we assumed.**

- The **"detectability frontier"** (oracle decomposition: caught / observable-but-missed / undetectable at a fixed false-review rate) is **not a new concept.** It is the **selective-classification gap vs. a perfect-ordering oracle**, given a finite-sample decomposition — with an irreducible **Bayes-noise** term — by **Rabanser et al., NeurIPS 2025 (arXiv:2510.20242)**. Our "undetectable" = Bayes noise; "observable-but-missed" = ranking/approximation error; "oracle" = perfect ordering. A reviewer can call the three-way split a re-labelling.
- **Each of the five pillars is anticipated by ≥1 recent paper** (see §3). As written, pillar #1 is the *weakest*, #2 and #4 are each one citation from "incremental," #3 is the most salvageable.
- **The defensible residual is a COMBINATION + MEASUREMENT, not a concept:** no single paper computes the detectability ceiling **as "catchable by ≥1 document-evidence channel vs. none," across BOTH fields and tables, at strict zero-extra-cost, with per-channel complementarity.** Each piece exists; the intersection does not.

**Consequence — reposition (don't abandon):**
1. **Reframe the headline** from *"we define a detectability frontier"* → *"we **measure** the undetectable floor of document-extraction errors across evidence channels and granularities."* The empirical measurement is the honest novelty; the concept is not.
2. **Cite Rabanser et al. (2510.20242) + the aleatoric/Bayes-noise decomposition up front**, and explicitly position our frontier as *their* oracle gap specialized to document-evidence channels. Pretending it is new invites a novelty rejection.
3. **Lead with the combination**: cross-granularity (fields+tables) + strict zero-extra-cost + complementarity-beyond-correlation. Demote the frontier to the *analysis lens*.

*(Calibration: the threat reviewer was instructed to be maximally harsh; real reviews would be less uniform. But the Rabanser precedent and the crowded space are real and must be engaged.)*

---

## 1. The debate (researcher ⇄ reviewer)

| Pillar | Reviewer attack (prior art) | Researcher rebuttal | Honest residual |
|---|---|---|---|
| **#1 Frontier** | = selective-classification gap vs. oracle; undetectable = Bayes noise (Rabanser 2025, 2510.20242) | Concept conceded. But nobody computes the ceiling as *"catchable by ≥1 document-evidence channel vs. none,"* nor across fields+tables, nor at a human-routing-budget operating point. | **Partial.** Novelty = the *measurement over document channels + cross-granularity*, not the concept. |
| **#2 Complementarity** | ExtractConf's Hunter/Mapper "fail-differently → disagreement informative" (2606.24420) | Conceded for *fields with two reads*. Ours spans *more channel types*, *fields AND tables*, and at *zero extra read* (ExtractConf spends an extra read). | **Partial.** Differentiator = cross-granularity + zero-cost, not the principle. |
| **#3 Cross-granularity** | RaV-IDP unifies validation across tables/text/images + re-OCR witness (2604.23644) | RaV-IDP does *not* compute a detectability ceiling, and triggers a **VLM call** on low-fidelity items (not strict zero-cost). | **Win-ish.** Our ceiling + strict zero-cost over a unified framework is a real gap. |
| **#4 Zero-extra-cost** | ConfBench benchmarks no-extra-call doc-KIE confidence under review budget (2608.01792); Per-Field Selective Risk Control gives validity guarantees (2608.14639) | Conceded that no-extra-call confidence is established. We go beyond a *benchmark* to the ceiling + cross-granularity + method; but we **lack their finite-sample guarantees** — weakness. | **Weak.** Must beat ConfBench's curves (and cite them) + consider borrowing their risk-control guarantees. |
| **#5 Honesty** | "Confidently Wrong, Silently So" — undetectable-failure audit + cost ladder + "flag, don't claim verified" (2608.23663) | Conceded as the thesis; theirs is *not* document-extraction-specific. | **Minor.** Honesty is table-stakes, not a contribution; frame as a property, not a pillar. |

**Net:** after the debate, the surviving contribution is **the cross-granularity, strict-zero-extra-cost, per-channel measurement of the document-evidence detectability ceiling** — a *synthesis + empirical study*, not a new construct. Publishable, but the novelty claim must be narrow and honest.

---

## 2. Must-cite related work (the constructive citing list)

*Web-verified. Group = related-work subsection.*

**A. Selective prediction / learning-to-reject / risk-coverage** (our methodological backbone)
- Chow (1970), *On optimum recognition error and reject tradeoff*, IEEE IT — origin of error-reject tradeoff.
- El-Yaniv & Wiener (2010), *Foundations of Noise-free Selective Classification*, JMLR — defines risk-coverage.
- Geifman & El-Yaniv (2017), *Selective Classification for Deep Neural Networks*, NeurIPS — modern anchor.
- Geifman & El-Yaniv (2019), *SelectiveNet*, ICML (arXiv:1901.09192).
- **Geifman, Uziel & El-Yaniv (2019), AURC/E-AURC, ICLR (arXiv:1805.08206) — MANDATORY if we report AURC/risk-coverage (we do).**
- **Rabanser et al. (2025), *What Does It Take to Build a Performant Selective Classifier?*, NeurIPS (arXiv:2510.20242) — the oracle-gap decomposition our frontier specializes. CITE UP FRONT.**

**B. Conformal prediction & risk control**
- Vovk, Gammerman & Shafer (2005), *Algorithmic Learning in a Random World* — canonical.
- Angelopoulos & Bates (2023), *Gentle Introduction to Conformal Prediction / DFUQ* (arXiv:2107.07511).
- Angelopoulos et al. (2024), *Conformal Risk Control*, ICLR (arXiv:2208.02814).
- Angelopoulos et al. (2025), *Learn Then Test*, Ann. Appl. Stat. (arXiv:2110.01052).
- *(We use a simple binomial bound; position against conformal, noting exchangeability breaks under shift.)*

**C. LLM uncertainty & hallucination detection** (our LLM baselines + nearest detection analogues)
- Kadavath et al. (2022), *Language Models (Mostly) Know What They Know* — P(True) (arXiv:2207.05221).
- Kuhn, Gal & Farquhar (2023), *Semantic Uncertainty*, ICLR (arXiv:2302.09664) + **Farquhar et al. (2024), *Detecting hallucinations… semantic entropy*, Nature 630 — headline GT-free detector.**
- Manakul et al. (2023), *SelfCheckGPT*, EMNLP (arXiv:2303.08896) — the sampling-consistency analogue of our independent-witness channel.
- Lin, Hilton & Evans (2022), *Teaching Models to Express Uncertainty in Words*, TMLR (arXiv:2205.14334); Tian et al. (2023), *Just Ask for Calibration*, EMNLP (arXiv:2305.14975).

**D. Fact verification & attribution** (our corroborated/contradicted/insufficient framing)
- Thorne et al. (2018), *FEVER*, NAACL — SUPPORTED/REFUTED/NEI origin.
- Rashkin et al. (2023), *Measuring Attribution in NLG* (AIS), Comp. Ling. (arXiv:2112.12870).
- Gao et al. (2023), *RARR*, ACL (arXiv:2210.08726).

**E. Reference-free quality estimation** (closest cross-field analogue)
- Rei et al. (2020), *COMET*, EMNLP; Rei et al. (2022), *CometKiwi*, WMT — reference-free QE. **Cite — omission signals we missed our nearest prior art.** Plus one WMT QE shared-task findings paper (note its **Critical Error Detection** track — close to our error detection).

**F. Ensemble diversity / correlated errors** (basis for complementarity)
- Kuncheva & Whitaker (2003), *Measures of Diversity in Classifier Ensembles*, Mach. Learn. — Q-statistic/double-fault; the formal basis for "diverse channels catch different errors."
- Dietterich (2000), *Ensemble Methods in ML*, MCS.

**G. Document KIE / VRDU extractors** (systems whose outputs we check)
- Xu et al. (2020) LayoutLM; Huang et al. (2022) LayoutLMv3 (arXiv:2204.08387); Kim et al. (2022) Donut (arXiv:2111.15664); Perot et al. (2023) LMDX (arXiv:2309.10952); Wang et al. (2024) DocLLM (arXiv:2401.00908).

**H. Document & table evaluation** (our metrics/benchmarks)
- Zhong et al. (2020), **TEDS** (PubTabNet), ECCV (arXiv:1911.10683) — table-structure metric, mandatory.
- Smock et al. (2023), **GriTS**, ICDAR (arXiv:2203.12555).
- Wang et al. (2023), VRDU, KDD (arXiv:2211.15421); Šimsa et al. (2023), DocILE, ICDAR (arXiv:2302.05658); Ouyang et al. (2024), OmniDocBench (arXiv:2412.07626); RD-TableBench (Reducto, repo-cite, no paper).

**Top-5 embarrassing-to-omit:** (1) Selective-classification + AURC/E-AURC; (2) Conformal intro + risk control; (3) Semantic Entropy (Nature 2024); (4) CometKiwi/COMET-QE; (5) TEDS + GriTS. **Add: Rabanser et al. 2025 — now mandatory given it anticipates our pillar.**

---

## 3. Prior-art threats (ranked) + how we position against each

*Cite each, and state our differentiation explicitly in the paper.*

### CRITICAL
1. **Rabanser et al. (2025), NeurIPS — selective-classifier gap vs oracle (2510.20242).** *Threatens #1 (concept).* **Position:** cite as the decomposition we specialize to document-evidence channels; our contribution is the *per-channel, cross-granularity measurement*, not the decomposition.
2. **Perception, Layout, Validation — Calibrated Confidence for STP of Financial Documents (2609.20110, 2026).** Decomposed confidence channels + conformal STP; closest architectural twin (fields only). *Threatens #2, #4.* **Position:** we add tables, the detectability ceiling, and strict zero-cost; they claim "verified at target risk," we flag undetectable.
3. **ExtractConf — Beyond Logprobs (2606.24420, 2026).** Hunter/Mapper disagreement = complementarity (fields, DocILE). *Threatens #2.* **Position:** our complementarity spans more channels + fields AND tables + zero extra read (ExtractConf spends an extra read — it's an *equal-cost baseline we must beat*).

### HIGH
4. **Valid Per-Field Selective Risk Control (2608.14639, 2026).** Accept/route with selective-risk ≤ α + validity ladder (CORD). *Threatens #4.* **Position:** we lack their finite-sample guarantees — *consider adopting them*; we add cross-granularity + the ceiling.
5. **ConfBench (2608.01792, AWS, 2026).** No-extra-call doc-KIE confidence benchmark + ECARB (error-capture-at-review-budget ≈ our fixed-FRR curve). *Threatens #4.* **Position:** must cite and beat their curves; we go beyond a benchmark to method + ceiling + tables.
6. **RaV-IDP — Reconstruction-as-Validation (2604.23644, 2026).** Unified label-free validation across tables/text/images + re-OCR witness. *Threatens #3.* **Position:** they don't compute a ceiling and trigger a VLM call on low-fidelity (not strict zero-cost); our ceiling + strict zero-cost differentiate.
7. **"Confidently Wrong, Silently So" (2608.23663, 2026).** Undetectable-failure audit + cost ladder + honesty thesis (QA/reasoning, not documents). *Threatens #5.* **Position:** reframe honesty as a *property*, not a pillar; cite as precedent, specialize to documents.
8. **MSCE — Multi-Signal Confidence Calibration for Business Doc Field Extraction (ResearchSquare rs-10721490).** Five-signal (OCR/layout/model-uncertainty/semantic/image) no-extra-call per-field correctness. *Threatens #1-field, #2, #4.* ⚠️ **metadata unverified — chase authors/venue/year before relying on it.**

### MEDIUM
- HYCEDIS (2206.02628, 2021) — confidence engine for doc IE, no host-model change (prior-art existence).
- SIEVES (2604.25855, 2026) — evidence-based selective prediction, no extra call (unstructured side).
- IJDAR *Beyond Accuracy: Conformal KIE confidence* (10.1007/s10032-026-00572-y, 2026) — archival "done in a journal." ⚠️ scope unverified (paywalled).
- Table-side: *Diagnosis→Correction table parsing* (2608.09842 — ⚠️ the "ceiling" wording is likely a summarizer artifact; verify against PDF); Table-structure UQ (2407.01731 TTA; 2507.02009 conformal).
- Framing-level (adjacent fields): *Why Language Models Hallucinate* / detection-impossibility (2509.04664); reference-free QE ceiling literature (xCOMET/CometKiwi).

---

## 3a. Verified deep-read of the five closest papers (full text, 2026-10-05)

All five confirmed **real and read in full** (ar5iv/arXiv). The two columns that decide our novelty:

| Paper | Domain | Extra model call at inference? | Detectability ceiling / undetectable bucket? |
|---|---|---|---|
| Rabanser & Papernot 2025 (2510.20242) | **General ML** (CIFAR, StanfordCars; *not* documents) | n/a | **Yes** — oracle + 5-term gap incl. irreducible Bayes-noise floor |
| Perception/Layout/Validation (2609.20110) | doc **fields only** (financial) | **Yes** — extra VLM passes | No (conformal risk *bound*, not a ceiling) |
| ExtractConf / Beyond Logprobs (2606.24420) | doc **fields only** (invoices/receipts) | **Yes** — 2 GPT-4o calls/doc (Hunter+Mapper) | No |
| ConfBench (2608.01792) | doc fields/KIE — **benchmark, not method** | partial (verbalized = 1 call) | No |
| RaV-IDP (2604.23644) | **tables + text + images** | **Yes** — GPT-4.1 vision fallback | No |
| **OURS** | **fields + tables** | **No — zero extra model call** | **Yes, for documents (would be first)** |

**Per-paper confirmation (from full text):**
- **Rabanser & Papernot (2510.20242):** general selective classification; defines the perfect-ordering oracle and the gap decomposition (Bayes-noise *irreducible* + approx + ranking + stat + misc). *This is our frontier concept in general form — cite and specialize to documents; do not claim it as new.* Never applied to documents/tables.
- **ExtractConf (2606.24420):** Nitesh Kumar (Perfios). Hunter + Mapper = **two extra GPT-4o calls per document** (not trained models, not cheap). Fields only. No ceiling. → confirms our zero-extra-call differentiator; complementarity principle anticipated for fields.
- **ConfBench (2608.01792):** AWS. A **benchmark** of cheap confidence on doc KIE; introduces **ECARB** (error-capture-at-review-budget ≈ our risk-coverage). Not a method; no ceiling; fields only.
- **Perception/Layout/Validation (2609.20110):** Jin et al. Three channels (perception = VLM, layout, validation) + conformal risk gate for STP; **extra VLM passes**; fields only; no ceiling. Closest architectural twin for fields.
- **RaV-IDP (2604.23644):** Pritesh Jha (single author, code-only). Reconstruction-as-validation across tables/text/images + **GPT-4.1 vision fallback**; spans granularities but via a *different mechanism*; no ceiling; not strictly cheap.

**What the deep-read changed (in our favour):** all four document competitors spend ≥1 extra model call, and none measures a detectability ceiling for documents → our **zero-extra-model-call** + **document detectability floor** (+ fields+tables) are genuinely unoccupied.

**Refined fields-side positioning (honest):** the *concept* "decompose into signals → fuse → route by risk" is occupied (esp. 2609.20110). Our fields differences — **structured/unstructured routing, the ROI blueprint channel, and non-vision/non-LLM signals** — are **real but implementation-level**; they do not overturn the concept. **Frame them as the engineering that makes the zero-extra-model-call result possible (support), not as the headline.** The defensible claim is the *combination* **non-vision AND non-LLM AND zero-extra-call**, which none of the four achieves — not "non-vision signals" alone (ConfBench and others also use non-vision signals).

---

## 4. Repositioned novelty claims (honest, defensible)

State the contribution as **measurement + synthesis**, not invention:

1. **An empirical detectability floor for document extraction.** We measure, across real document-evidence channels, the share of extraction errors that *no* channel can catch — specializing the selective-classifier oracle gap (Rabanser 2025) to the document-evidence setting. *(Novelty = the measurement over document channels, not the concept.)*
2. **Cross-granularity.** The same detectability/complementarity analysis for *fields and tables* under one formulation — no prior work computes the ceiling across both. *(Most salvageable claim.)*
3. **Strict zero-extra-cost operating point.** Unlike the extra-read / VLM-fallback methods (ExtractConf, RaV-IDP) and benchmark-only works (ConfBench), we study detection at *no additional model call* and compare on cost/risk/coverage.
4. **Complementarity beyond correlation**, across channel *types* and granularities (grounded in Kuncheva), with unique-capture / marginal-utility.

Honesty property (not a pillar): we flag the undetectable floor instead of claiming "verified."

---

## 5. Recommended positioning strategy

- **Lead the intro with the combination (claims 2–3–4), frontier as the analysis lens (claim 1).** Do not open with "we define the detectability frontier."
- **Cite Rabanser (2510.20242) in the first page of related work** and explicitly specialize it; same for ConfBench, ExtractConf, RaV-IDP, Per-Field Risk Control — treat them as the equal-cost baselines/related methods we beat or differentiate from, not surprises.
- **Consider borrowing finite-sample guarantees** (conformal risk control / Learn-Then-Test) to answer the Per-Field-Risk-Control / ConfBench "no guarantees" critique.
- **Decide venue realistically:** given the crowding, a **Resources & Evaluation / analysis framing** (we *measure* the floor + provide the cross-granularity protocol) may be safer than a "novel method" main-track claim. Worth a team decision.

---

## 6. Verification to-do before citing
- [ ] Resolve **MSCE** (rs-10721490) authors/venue/year — or drop it.
- [ ] Confirm **IJDAR 10.1007/s10032-026-00572-y** exact scope (paywalled).
- [ ] Verify **2608.09842** "ceiling/upper-bound" wording against the PDF (likely a summarizer artifact).
- [ ] Re-confirm all 2026 arXiv IDs (2609.20110, 2606.24420, 2608.14639, 2608.01792, 2604.23644, 2608.23663, 2604.25855) against arXiv listings.
- [ ] Pin one canonical WMT QE shared-task findings paper.

---

## 7. Bottom line
The related-work *coverage* is solid (§2). The *novelty* is the issue (§0): the frontier concept is not ours, and every pillar is anticipated. The paper remains viable **only if repositioned** around the honest residual — *the cross-granularity, strict-zero-cost, per-channel measurement of the document-evidence detectability floor* — with the precedents cited up front rather than discovered by a reviewer. This is the single most important thing to settle with the team before writing.
