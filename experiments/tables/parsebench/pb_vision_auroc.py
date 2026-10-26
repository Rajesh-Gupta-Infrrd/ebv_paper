import json, itertools

# vision label per idx: 1=GOOD (extraction faithful to the crop), 0=BAD (content dropped/garbled/misaligned)
# derived by reading every crop vs its predicted HTML this session.
vision = {
 0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1,
 12:0, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:1, 22:1,
 23:0, 24:0, 25:1, 26:1, 27:1, 28:1, 29:0, 30:1, 32:1, 33:1, 34:1,
 35:0, 36:1, 37:1, 38:1, 39:1, 40:1, 41:1, 42:1, 43:1, 44:1, 45:1,
 46:1, 47:1, 48:1, 49:1, 50:1, 51:0, 52:1, 53:1, 54:1, 55:1, 56:1,
 57:1, 58:1, 59:1,
 # 31 excluded (scorer returned no trust)
}
# borderline cases I was least sure about (reported separately)
borderline = {1,4,37,47,50,52,54,41,16,18,22,13,8,7,20,21,51,24}

m = {r['i']: r for r in json.load(open('pb_manifest.json'))}
rows=[]
for i,v in vision.items():
    t = m[i].get('trust')
    if t is None: continue
    rows.append((i, t, v, m[i].get('teds')))

good = [t for _,t,v,_ in rows if v==1]
bad  = [t for _,t,v,_ in rows if v==0]
n_g, n_b = len(good), len(bad)

def auroc(pos, neg):
    # P(pos_score > neg_score), ties=0.5
    c=0.0
    for p in pos:
        for n in neg:
            if p>n: c+=1
            elif p==n: c+=0.5
    return c/(len(pos)*len(neg))

A_vision = auroc(good, bad)

# vs TEDS label at tau=0.9
teds_good=[t for _,t,_,td in rows if td is not None and td>=0.9]
teds_bad =[t for _,t,_,td in rows if td is not None and td<0.9]
A_teds = auroc(teds_good, teds_bad)

# accept@85 confusion vs vision
TP=FP=TN=FN=0  # accept=positive(predict good)
for _,t,v,_ in rows:
    acc = t>=85
    if acc and v==1: TP+=1
    elif acc and v==0: FP+=1
    elif (not acc) and v==0: TN+=1
    else: FN+=1
# catch rate (of BAD, how many rejected), false-alarm (of GOOD, how many rejected)
catch = TN/n_b if n_b else 0
false_alarm = FN/n_g if n_g else 0

print(f"usable tables: {len(rows)}  GOOD={n_g}  BAD={n_b} ({n_b/len(rows)*100:.0f}% bad)")
print(f"AUROC(trust, VISION good/bad) = {A_vision:.3f}")
print(f"AUROC(trust, TEDS>=0.9)       = {A_teds:.3f}   (TEDS good={len(teds_good)} bad={len(teds_bad)})")
print()
print(f"accept@85 vs vision:  TP={TP} FP={FP} TN={TN} FN={FN}")
print(f"  bad-catch (rejected bad / all bad)      = {TN}/{n_b} = {catch:.2f}")
print(f"  false-alarm (rejected good / all good)  = {FN}/{n_g} = {false_alarm:.2f}")
print()
print("BAD tables (vision) and their trust:")
for i,t,v,td in sorted(rows, key=lambda r:r[1]):
    if v==0: print(f"  idx{i:2d} trust={t:5.1f} teds={td}")
print("GOOD tables with LOW trust (<85) = scorer false-rejects:")
fr=[(i,t,td) for i,t,v,td in rows if v==1 and t<85]
for i,t,td in sorted(fr, key=lambda r:r[1]):
    bl = " [borderline]" if i in borderline else ""
    print(f"  idx{i:2d} trust={t:5.1f} teds={td}{bl}")
print(f"  -> {len(fr)} good tables rejected")

# coverage@fixed risk: sort by trust desc, accept top-k, measure error (bad fraction) in accepted
order = sorted(rows, key=lambda r:-r[1])
for risk in (0.05,0.10,0.20):
    best_cov=0
    for k in range(len(order),0,-1):
        acc=order[:k]
        bad_in=sum(1 for r in acc if r[2]==0)
        if bad_in/k <= risk:
            best_cov=k; break
    print(f"coverage@{int(risk*100)}%risk = {best_cov}/{len(rows)} = {best_cov/len(rows):.2f}")
