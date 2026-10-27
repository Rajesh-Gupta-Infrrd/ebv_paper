"""
Shared library for EBV indirect experiments (channel-level, family-free).
Computes, from a per-item table of channel scores + a binary correctness label:
  - 5%-FRR per-channel thresholds (flag <=5% of CORRECT items)
  - Oracle observability + error decomposition (frontier, H5)
  - Channel ablation (drop-one AUROC), complementarity / unique capture (H3)
  - Placebo (permuted channels must collapse observability) (validity)
  - Document/item bootstrap CIs
A "channel" is a continuous score with a direction: 'low' = low value contradicts
(evidence against the output), or 'high' = high value contradicts. NaN = channel
inapplicable for that item (does not flag; contributes to INSUFFICIENT).
No ground-truth family labels are needed here; the per-family map is separate.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score as _sk_roc_auc

def _flag_mask(vals, thr, direction):
    v = np.asarray(vals, float)
    out = np.zeros(len(v), bool)
    ok = ~np.isnan(v)
    if direction == 'low':
        out[ok] = v[ok] < thr
    else:
        out[ok] = v[ok] > thr
    return out

def frr_threshold(vals, correct, direction, frr=0.05):
    """Threshold placed so that <= frr of CORRECT items are flagged."""
    v = np.asarray(vals, float); c = np.asarray(correct, bool)
    cv = v[c & ~np.isnan(v)]
    if len(cv) == 0:
        return (-np.inf if direction == 'low' else np.inf)
    if direction == 'low':
        return np.quantile(cv, frr)          # flag values below the 5th pct of correct
    else:
        return np.quantile(cv, 1 - frr)      # flag values above the 95th pct of correct

def build_flags(df, channels, frr=0.05):
    """channels: dict name->'low'/'high'. Returns (flags dict name->bool array, thresholds)."""
    correct = df['correct'].values.astype(bool)
    flags, thr = {}, {}
    for name, direction in channels.items():
        t = frr_threshold(df[name].values, correct, direction, frr)
        thr[name] = t
        flags[name] = _flag_mask(df[name].values, t, direction)
    return flags, thr

def decompose(df, channels, accept_col='accept', frr=0.05):
    """
    Frontier decomposition on ERRORS (correct==False):
      caught            = fusion rejected it (accept==False)
      observable_missed = fusion accepted, but >=1 channel flags at 5%-FRR
      undetectable      = fusion accepted AND no channel flags at 5%-FRR
    Also OracleCapture = frac of errors flagged by >=1 channel (fusion-independent).
    """
    correct = df['correct'].values.astype(bool)
    err = ~correct
    flags, thr = build_flags(df, channels, frr)
    anyflag = np.zeros(len(df), bool)
    for f in flags.values(): anyflag |= f
    n_err = int(err.sum())
    oracle = int((anyflag & err).sum())
    if accept_col in df:
        accepted = df[accept_col].values.astype(bool)
    else:
        accepted = np.ones(len(df), bool)
    caught = int((err & ~accepted).sum())
    obs_missed = int((err & accepted & anyflag).sum())
    undet = int((err & accepted & ~anyflag).sum())
    # per-correct false-flag rate of the union (the realized FRR)
    union_frr = float((anyflag & correct).sum() / max(correct.sum(), 1))
    return dict(n_err=n_err,
                oracle_capture=oracle / max(n_err, 1), oracle_n=oracle,
                caught=caught, caught_frac=caught / max(n_err, 1),
                observable_missed=obs_missed, observable_missed_frac=obs_missed / max(n_err, 1),
                undetectable=undet, undetectable_frac=undet / max(n_err, 1),
                union_false_flag_rate=union_frr, thresholds={k: float(v) for k, v in thr.items()})

def frontier_report(df, channels, fused_col=None, fused_dir='low', frr=0.05):
    """Clean frontier: EVERY detector (channels + optional fused score) at the SAME 5%-FRR budget.
    detectable = flagged by >=1 channel OR the fused verifier; undetectable = the frontier."""
    correct = df['correct'].values.astype(bool); err = ~correct
    flags, thr = build_flags(df, channels, frr)
    any_ch = np.zeros(len(df), bool)
    for f in flags.values(): any_ch |= f
    det = any_ch.copy(); fflag = None
    if fused_col is not None:
        t = frr_threshold(df[fused_col].values, correct, fused_dir, frr)
        fflag = _flag_mask(df[fused_col].values, t, fused_dir)
        det = det | fflag
    ne = int(err.sum()); nc = int(correct.sum())
    rep = dict(n_err=ne,
               oracle_channels=float((any_ch & err).sum() / max(ne, 1)),
               detectable=float((det & err).sum() / max(ne, 1)),
               undetectable=float((err & ~det).sum() / max(ne, 1)),
               undetectable_n=int((err & ~det).sum()),
               channel_false_flag=float((any_ch & correct).sum() / max(nc, 1)),
               union_false_flag=float((det & correct).sum() / max(nc, 1)))
    if fflag is not None:
        rep['fusion_capture'] = float((fflag & err).sum() / max(ne, 1))
        rep['fusion_false_flag'] = float((fflag & correct).sum() / max(nc, 1))
    return rep

def placebo_frontier(df, channels, fused_col=None, fused_dir='low', frr=0.05, n=200, seed=0):
    rng = np.random.default_rng(seed)
    real = frontier_report(df, channels, fused_col, fused_dir, frr)['detectable']
    cols = list(channels) + ([fused_col] if fused_col else [])
    vals = []
    for _ in range(n):
        d2 = df.copy()
        for c in cols: d2[c] = rng.permutation(df[c].values)
        vals.append(frontier_report(d2, channels, fused_col, fused_dir, frr)['detectable'])
    return dict(real=real, placebo_mean=float(np.mean(vals)), placebo_std=float(np.std(vals)))

def oracle_decompose(df, channels, fused_col, fused_dir, accept_col, frr=0.05):
    """E4c: split errors into (a) caught by fusion, (b) observable by >=1 single channel at 5% FRR
    but MISSED by fusion, (c) caught by fusion though no single channel flags (fusion>channels),
    (d) TRUE frontier = no channel AND fusion both miss. Separates evidence-limit from fusion-limit."""
    correct = df['correct'].values.astype(bool); err = ~correct
    flags, _ = build_flags(df, channels, frr)
    anych = np.zeros(len(df), bool)
    for f in flags.values(): anych |= f
    accepted = df[accept_col].values.astype(bool)
    ne = int(err.sum())
    caught = err & ~accepted
    obs = err & anych
    out = dict(n_err=ne,
               fusion_caught=int(caught.sum()), fusion_caught_rate=int(caught.sum()) / max(ne, 1),
               observable_by_channel=int(obs.sum()), observable_rate=int(obs.sum()) / max(ne, 1),
               obs_and_caught=int((err & anych & ~accepted).sum()),
               obs_but_missed=int((err & anych & accepted).sum()),
               fusiononly_caught=int((err & ~anych & ~accepted).sum()),
               true_frontier_n=int((err & ~anych & accepted).sum()),
               true_frontier_rate=int((err & ~anych & accepted).sum()) / max(ne, 1))
    return out

def deployed_report(df, fused_col, fused_dir='low', accept_col=None, thr=None, indist_pct=50):
    """Honest operating-point view (replaces the 5%-FRR 'undetectable' proxy).
      caught      = errors the verifier rejects at the DEPLOYED decision
      slip_through = errors accepted (false accepts) -> the operational miss
      frontier_confidently_wrong = accepted errors whose fused score is at least as
        'clean' as the median (indist_pct) correct output -> indistinguishable from a
        typical correct output = the genuine detectability frontier (H5).
    Give either accept_col (a bool decision) or an explicit numeric thr on fused_col."""
    correct = df['correct'].values.astype(bool); err = ~correct
    fused = df[fused_col].values.astype(float)
    if accept_col is not None:
        accepted = df[accept_col].values.astype(bool)
    else:
        if fused_dir == 'low':
            accepted = fused >= thr
        else:
            accepted = fused <= thr
    ne = int(err.sum())
    caught = int((err & ~accepted).sum())
    slip = int((err & accepted).sum())
    # indistinguishable cut from the CORRECT distribution
    cv = fused[correct & ~np.isnan(fused)]
    cut = np.percentile(cv, indist_pct) if len(cv) else np.nan
    if fused_dir == 'low':
        indist = err & accepted & (fused >= cut)   # error scored >= median correct = looks clean
    else:
        indist = err & accepted & (fused <= cut)
    return dict(n_err=ne,
                caught=caught, caught_rate=caught / max(ne, 1),
                slip_through=slip, slip_rate=slip / max(ne, 1),
                frontier_confidently_wrong=int(indist.sum()),
                frontier_rate=float(indist.sum()) / max(ne, 1),
                indist_cut=float(cut) if cut == cut else None)

def complementarity(df, channels, frr=0.05):
    """Per-channel: coverage of errors, and UNIQUE capture (errors only this channel flags)."""
    err = ~df['correct'].values.astype(bool)
    flags, _ = build_flags(df, channels, frr)
    names = list(channels)
    out = {}
    for n in names:
        f = flags[n] & err
        others = np.zeros(len(df), bool)
        for m in names:
            if m != n: others |= flags[m]
        uniq = f & ~others
        out[n] = dict(covers=int(f.sum()), covers_frac=float(f.sum() / max(err.sum(), 1)),
                      unique=int(uniq.sum()), unique_frac=float(uniq.sum() / max(err.sum(), 1)))
    return out

def auroc(score, correct):
    """AUROC of score predicting CORRECT (higher score = more trustworthy).

    Uses sklearn roc_auc_score, which averages tied ranks (the Mann-Whitney statistic
    handles ties correctly). The earlier hand-rolled version assigned *sequential* ranks
    to ties, making results order-dependent for heavily-tied / binary channels (review #1).
    """
    s = np.asarray(score, float); c = np.asarray(correct, bool)
    ok = ~np.isnan(s); s, c = s[ok], c[ok]
    if len(np.unique(c)) < 2:
        return float('nan')
    return float(_sk_roc_auc(c, s))

def placebo_oracle(df, channels, frr=0.05, n=200, seed=0):
    """Permute each channel's values across items; oracle_capture should collapse ~ union of per-channel 5%."""
    rng = np.random.default_rng(seed)
    err = ~df['correct'].values.astype(bool)
    base = decompose(df, channels, frr=frr)['oracle_capture']
    vals = []
    for _ in range(n):
        d2 = df.copy()
        for name in channels:
            d2[name] = rng.permutation(df[name].values)
        flags, _ = build_flags(d2, channels, frr)
        anyflag = np.zeros(len(d2), bool)
        for f in flags.values(): anyflag |= f
        vals.append((anyflag & err).sum() / max(err.sum(), 1))
    return dict(real=base, placebo_mean=float(np.mean(vals)), placebo_std=float(np.std(vals)))

def bootstrap_ci(df, fn, group=None, n=1000, seed=0, alpha=0.05):
    """Bootstrap CI for scalar metric fn(df_sample). Resample by `group` col (doc/table) if given."""
    rng = np.random.default_rng(seed)
    vals = []
    if group and group in df:
        groups = df[group].unique()
        by = {g: df[df[group] == g] for g in groups}      # rows of each cluster
        for _ in range(n):
            pick = rng.choice(groups, len(groups), replace=True)
            # proper cluster bootstrap: a group drawn k times contributes its rows k times
            sub = pd.concat([by[g] for g in pick], ignore_index=True)
            vals.append(fn(sub))
    else:
        idx = np.arange(len(df))
        for _ in range(n):
            sub = df.iloc[rng.choice(idx, len(idx), replace=True)]
            vals.append(fn(sub))
    vals = np.array([v for v in vals if v == v])
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))
