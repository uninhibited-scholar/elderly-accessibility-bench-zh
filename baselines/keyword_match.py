#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Keyword-match baseline: pick the option whose intent keywords best overlap the
raw text. Collapse line — brittle to typos/homophones/dialect, so its noisy
accuracy should crater while clean stays high. Emits predictions_keyword_match.jsonl."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT_RE = re.compile(r"([ABC])\.\s*([^ ]+?)(?:\s{2,}|。只输出)")
# intent -> discriminative surface keywords (exact chars, no fuzzy)
KW = {"挂号看病":["挂号","看病","医院"],"视频通话":["视频","通话","看见"],
      "缴水电费":["水电","水费","电费","交费"],"查养老金":["养老金","退休","到账"],
      "调大字体":["字","调大","大一点","小"],"买药":["买药","药"],
      "查公交":["公交","几点","到站","路"],"防诈咨询":["转账","转钱","退税","转帐"],
      "查天气":["天气","下雨","冷"],"联系子女":["儿子","打电话","号码","娃"]}
def main():
    out = os.path.join(ROOT, "predictions_keyword_match.jsonl")
    w = open(out, "w", encoding="utf-8")
    for l in open(os.path.join(ROOT, "data", "queries.jsonl"), encoding="utf-8"):
        r = json.loads(l); text = r["text"]
        opts = dict(OPT_RE.findall(r["probe"]))
        best, blet = -1, "A"
        for let, intent in opts.items():
            score = sum(1 for k in KW.get(intent, []) if k in text)
            if score > best: best, blet = score, let
        w.write(json.dumps({"id": r["id"], "answer": blet}, ensure_ascii=False) + "\n")
    w.close(); print(f"wrote {out}")
if __name__ == "__main__":
    main()
