import json, re
from collections import Counter

vision = {
 0:1,1:1,2:1,3:1,4:1,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:0,13:1,14:1,15:1,16:1,17:1,18:1,19:1,
 20:1,21:1,22:1,23:0,24:0,25:1,26:1,27:1,28:1,29:0,30:1,32:1,33:1,34:1,35:0,36:1,37:1,38:1,
 39:1,40:1,41:1,42:1,43:1,44:1,45:1,46:1,47:1,48:1,49:1,50:1,51:0,52:1,53:1,54:1,55:1,56:1,57:1,58:1,59:1}

m = {r['i']: r for r in json.load(open('pb_manifest.json'))}

def toks(html):
    if not html: return Counter()
    t = re.sub(r'(?is)<(script|style).*?</\1>', ' ', html)
    t = re.sub(r'<[^>]+>', ' ', t)          # strip tags
    t = (t.replace('&amp;','&').replace('&#x27;',"'").replace('&quot;','"')
          .replace('&lt;','<').replace('&gt;','>').replace('&#39;',"'"))
    t = t.lower()
    raw = re.findall(r'[a-z0-9]+(?:[.,%/\-][a-z0-9]+)*|[%$]', t)
    return Counter(x for x in raw if x.strip())

def nums(html):
    c = toks(html)
    return Counter({k:v for k,v in c.items() if re.search(r'\d', k)})

def prf(pred, gt):
    if not gt: return (1.0,1.0,1.0)
    inter = sum((pred & gt).values())
    p = inter/max(sum(pred.values()),1)
    r = inter/max(sum(gt.values()),1)
    f = 2*p*r/(p+r) if (p+r) else 0.0
    return p,r,f

rows=[]
for i,v in vision.items():
    r = m[i]
    if r.get('trust') is None: continue
    ph, gh = r.get('html'), r.get('gt_md')
    pt, gt = toks(ph), toks(gh)
    p,rc,f = prf(pt,gt)
    np_,nr,nf = prf(nums(ph), nums(gh))
    rows.append(dict(i=i, trust=r['trust'], vision=v, teds=r.get('teds') or 0.0,
                     cf1=f, crec=rc, cprec=p, numrec=nr, numf1=nf))

def auroc(scores, labels):  # P(score|good > score|bad)
    pos=[s for s,l in zip(scores,labels) if l==1]; neg=[s for s,l in zip(scores,labels) if l==0]
    c=0.0
    for a in pos:
        for b in neg:
            c += 1 if a>b else 0.5 if a==b else 0
    return c/(len(pos)*len(neg))

trust=[r['trust'] for r in rows]; vis=[r['vision'] for r in rows]
nbad_vis=sum(1 for x in vis if x==0)
print(f"n={len(rows)}  vision BAD={nbad_vis}")
print(f"AUROC(trust, VISION) = {auroc(trust,vis):.3f}   <-- target\n")
print(f"{'label':28s} {'nbad':>4s} {'agree':>6s} {'bad_recall':>10s} {'bad_prec':>8s} {'AUROC(trust|lbl)':>16s}")
def evallabel(name, key, thr, ge=True):
    lab=[]
    for r in rows:
        val=r[key]
        good = (val>=thr) if ge else (val<=thr)
        lab.append(1 if good else 0)
    # agreement with vision
    agree=sum(1 for a,b in zip(lab,vis) if a==b)/len(vis)
    # bad = label 0; recall/prec of catching vision-bad
    lb=set(i for i,l in enumerate(lab) if l==0); vb=set(i for i,l in enumerate(vis) if l==0)
    brec = len(lb&vb)/len(vb) if vb else 0
    bprec= len(lb&vb)/len(lb) if lb else 0
    nb=sum(1 for l in lab if l==0)
    try: a=auroc(trust,lab)
    except: a=float('nan')
    print(f"{name:28s} {nb:4d} {agree:6.2f} {brec:10.2f} {bprec:8.2f} {a:16.3f}")

for thr in (0.9,0.8,0.7,0.6,0.5):
    evallabel(f"TEDS>={thr}", 'teds', thr)
print()
for thr in (0.95,0.9,0.85,0.8,0.7):
    evallabel(f"content-F1>={thr}", 'cf1', thr)
print()
for thr in (0.98,0.95,0.9,0.85,0.8):
    evallabel(f"content-recall>={thr}", 'crec', thr)
print()
for thr in (0.98,0.95,0.9,0.85,0.8):
    evallabel(f"numeric-recall>={thr}", 'numrec', thr)
