#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a model over v2 slot-extraction queries; record raw output per row.
默认本地 Ollama；云端用 OPENAI_BASE_URL + OPENAI_API_KEY。"""
import argparse, json, os, re, ssl, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SSL = ssl.create_default_context(); _SSL.check_hostname = False; _SSL.verify_mode = ssl.CERT_NONE
SYS = "你是面向老年人的助手。用户表达可能有错别字/方言/口语/误导。请抽取意图和关键槽位，严格按要求输出 JSON，不要多余文字。"
def call(base, key, model, msgs, mx=512):
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": mx, "messages": msgs}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for r in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120, context=_SSL) as resp:
                m = json.loads(resp.read())["choices"][0]["message"]
                return m.get("content") or (m.get("reasoning_content") or "")[-200:]
        except Exception:
            time.sleep(2 * (r + 1))
    return ""
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"))
    ap.add_argument("--out")
    a = ap.parse_args()
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key and "localhost" not in a.base_url and "127.0.0.1" not in a.base_url:
        print("ERROR: 云端端点需 set OPENAI_API_KEY（本地 Ollama 无需 key）"); return 2
    out = a.out or os.path.join(ROOT, f"slots_pred_{re.sub(r'[^a-zA-Z0-9._-]','_',a.model)}.jsonl")
    w = open(out, "w", encoding="utf-8")
    for l in open(os.path.join(ROOT, "data", "slots.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": r["prompt"]}]
        w.write(json.dumps({"id": r["id"], "answer": call(a.base_url, key, a.model, msgs)}, ensure_ascii=False) + "\n"); w.flush()
    w.close(); print(f"wrote {out}")
if __name__ == "__main__":
    main()
