#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a model over the queries; record its intent-choice letter per row.
默认走本地 Ollama（http://localhost:11434/v1，无需 key）；云端用
OPENAI_BASE_URL + OPENAI_API_KEY 显式覆盖。
Usage: run_model.py --model <name> [--base-url <url>] [--out f.jsonl]"""
import argparse, json, os, re, ssl, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SSL = ssl.create_default_context(); _SSL.check_hostname = False; _SSL.verify_mode = ssl.CERT_NONE
SYS = "你是面向老年人的智能助手。用户表达可能有错别字、方言、口语或语音转写噪声。请判断用户想做什么，只输出一个选项字母（A/B/C），不要解释。"

def call(base, key, model, msgs, mx=256):
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": mx, "messages": msgs}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for r in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120, context=_SSL) as resp:
                m = json.loads(resp.read())["choices"][0]["message"]
                return m.get("content") or (m.get("reasoning_content") or "")[-80:]
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
    out = a.out or os.path.join(ROOT, f"predictions_{re.sub(r'[^a-zA-Z0-9._-]','_',a.model)}.jsonl")
    w = open(out, "w", encoding="utf-8")
    for l in open(os.path.join(ROOT, "data", "queries.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": r["probe"]}]
        ans = call(a.base_url, key, a.model, msgs)
        w.write(json.dumps({"id": r["id"], "answer": ans}, ensure_ascii=False) + "\n"); w.flush()
    w.close(); print(f"wrote {out}")

if __name__ == "__main__":
    main()
