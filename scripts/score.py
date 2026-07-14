#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score predictions for elderly-accessibility-bench-zh.
pred line: {"id":.., "answer":".."}
Usage: score.py <pred.jsonl> [queries.jsonl]

Headline metric — accessibility_gap = clean_accuracy − noisy_accuracy：
清晰表达 vs 老年口语噪声，同一意图集下的准确率落差。gap 越大＝越"听不懂老人"。
另按噪声类型细分（typo/homophone/ramble/dialect/voice），定位最难的一类。"""
import json, os, re, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def norm(s):
    s = str(s).strip()
    first = next((ln.strip() for ln in s.splitlines() if ln.strip()), "")
    m = re.search(r"[ABC]", first.upper())
    if m and len(first) <= 20: return m.group(0)
    m = re.search(r"[ABC]", s.upper())
    return m.group(0) if m else s

def main():
    if len(sys.argv) < 2:
        print("usage: score.py <pred.jsonl> [queries.jsonl]"); return 2
    preds = {}
    for l in open(sys.argv[1], encoding="utf-8"):
        l = l.strip()
        if l:
            o = json.loads(l); preds[o["id"]] = o.get("answer", "")
    qpath = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "queries.jsonl")
    clean = [0, 0]; noisy = [0, 0]; miss = 0
    by_noise = defaultdict(lambda: [0, 0])
    for l in open(qpath, encoding="utf-8"):
        r = json.loads(l)
        if r["id"] not in preds: miss += 1; continue
        ok = norm(preds[r["id"]]) == r["gold"]
        if r["noise"] == "clean": clean[0] += ok; clean[1] += 1
        else: noisy[0] += ok; noisy[1] += 1
        by_noise[r["noise_label"]][0] += ok; by_noise[r["noise_label"]][1] += 1
    acc = lambda p: round(p[0]/p[1], 3) if p[1] else None
    ca, na = acc(clean), acc(noisy)
    rep = {"missing": miss,
           "clean_accuracy": ca, "noisy_accuracy": na,
           "accessibility_gap": round(ca - na, 3) if (ca is not None and na is not None) else None,
           "by_noise": {k: f"{v[0]}/{v[1]} ({acc(v)})" for k, v in sorted(by_noise.items())},
           "overall_accuracy": acc([clean[0]+noisy[0], clean[1]+noisy[1]])}
    json.dump(rep, open(os.path.join(ROOT, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
