#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate data/queries.jsonl: schema, closed intent set, gold recompute
(gold letter must point to the row's own intent among its options), clean/noisy
coverage per intent. Do NOT pass by deleting rows or editing golds."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "queries.jsonl")
KEYS = {"id", "intent", "noise", "noise_label", "text", "probe", "gold"}
NOISES = {"clean", "typo", "homophone", "ramble", "dialect", "voice"}
OPT_RE = re.compile(r"([ABC])\.\s*([^ ]+?)(?:\s{2,}|。只输出)")

def main():
    rows, prob = [], []
    by_intent = {}
    for ln, l in enumerate(open(DATA, encoding="utf-8"), 1):
        l = l.strip()
        if not l: continue
        try: r = json.loads(l)
        except Exception as ex: prob.append(f"L{ln} bad json {ex}"); continue
        rows.append(r)
        i = r.get("id")
        if set(r) != KEYS: prob.append(f"{i} keys {sorted(r)}")
        if r.get("noise") not in NOISES: prob.append(f"{i} bad noise {r.get('noise')}")
        if r.get("gold") not in ("A", "B", "C"): prob.append(f"{i} bad gold {r.get('gold')}")
        opts = dict(OPT_RE.findall(r.get("probe", "")))
        if len(opts) != 3: prob.append(f"{i} expected 3 options, parsed {len(opts)}")
        elif opts.get(r["gold"]) != r["intent"]:
            prob.append(f"{i} gold points to '{opts.get(r['gold'])}' but intent is '{r['intent']}'")
        if r["text"] not in r.get("probe", ""): prob.append(f"{i} probe does not quote text")
        by_intent.setdefault(r.get("intent"), set()).add(r.get("noise"))
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)): prob.append("dup id")
    if len(rows) < 30: prob.append(f"too few rows ({len(rows)} < 30)")
    for it, ns in by_intent.items():
        if "clean" not in ns: prob.append(f"intent '{it}' missing a clean variant")
        if len(ns - {"clean"}) < 2: prob.append(f"intent '{it}' needs >=2 noisy variants")
    nnoise = {r["noise"] for r in rows}
    if len(nnoise & (NOISES - {"clean"})) < 4: prob.append(f"need >=4 noise types, has {sorted(nnoise)}")
    nc = sum(1 for r in rows if r["noise"] == "clean")
    print(f"checked {len(rows)} queries ({nc} clean / {len(rows)-nc} noisy) | intents {len(by_intent)} | noise types {sorted(nnoise)}")
    if prob:
        print(f"\nFAIL — {len(prob)}:")
        for p in prob[:40]: print("  -", p)
        print("\nFix the real gap; do NOT pass by deleting rows or editing golds.")
        return 1
    print("PASS — schema ok, gold recompute clean, clean+noisy coverage per intent.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
