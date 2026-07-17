#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score v2 slot-extraction predictions.
pred line: {"id":.., "answer":"<模型原始输出>"}
判分（程序化断言，归一化 contains）：
  intent_hit    抽取意图正确
  slot_hit      槽位值正确（gold slot_value 归一化后出现在模型抽取的对应字段/文本里）
  joint_acc     intent 和 slot 都对（最终指标）
按噪声类型细分。头条：joint_acc（开放式抽取，比选择题狠得多）。"""
import json, os, re, sys
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_D={"零":0,"一":1,"二":2,"两":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
def _cn2int(t):
    # 处理 十/十X/X十/X十Y (<100)，够本基准线路/月份用
    if t=="十": return "10"
    if "十" in t:
        a,_,b=t.partition("十")
        tens=_D.get(a,1) if a else 1
        ones=_D.get(b,0) if b else 0
        return str(tens*10+ones)
    return "".join(str(_D[c]) if c in _D else c for c in t)
def _num(s):
    return re.sub(r"[零一二两三四五六七八九十]+", lambda m:_cn2int(m.group()), str(s))
_SYN=[{"这个月","本月","当月"},{"上个月","上月"}]
def norm(s):
    return re.sub(r"[\s\W_]+","",_num(str(s))).lower()
def slot_ok(gold, blob_raw):
    b=norm(blob_raw)
    if norm(gold) in b: return True
    for grp in _SYN:
        if gold in grp and any(norm(x) in b for x in grp): return True
    return False

# 意图核心词：模型意图字段含核心词即算意图命中（模型常用不同措辞表达同一意图）
INTENT_KW = {"挂号看病":"挂号","查养老金":"养老金","缴水电费":["水电","缴费","交费","水费","电费","燃气"],
             "买药":"药","查公交":["公交","路"],"联系子女":["打电话","电话","联系"],
             "查天气":"天气","视频通话":"视频","调大字体":"字","防诈咨询":["诈","转账","风险","可疑"]}
def intent_ok(gold_intent, blob):
    kws = INTENT_KW.get(gold_intent, gold_intent)
    if isinstance(kws, str): kws = [kws]
    return any(norm(k) in blob for k in kws)

def extract_json(t):
    m = re.search(r"\{.*\}", t, re.S)
    if not m: return {}
    try: return json.loads(m.group())
    except: return {}

def main():
    if len(sys.argv) < 2:
        print("usage: score_slots.py <pred.jsonl> [slots.jsonl]"); return 2
    preds = {}
    for l in open(sys.argv[1], encoding="utf-8"):
        l = l.strip()
        if l:
            o = json.loads(l); preds[o["id"]] = o.get("answer", "")
    dpath = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "slots.jsonl")
    intent_hit = [0, 0]; slot_hit = [0, 0]; joint = [0, 0]; miss = 0
    by_noise = defaultdict(lambda: [0, 0])
    for l in open(dpath, encoding="utf-8"):
        r = json.loads(l)
        if r["id"] not in preds: miss += 1; continue
        raw = preds[r["id"]]; obj = extract_json(raw)
        blob_raw = (json.dumps(obj, ensure_ascii=False) if obj else raw)
        blob = norm(blob_raw)
        ih = intent_ok(r["intent"], blob)
        sh = slot_ok(r["slot_value"], blob_raw)
        intent_hit[0] += ih; intent_hit[1] += 1
        slot_hit[0] += sh; slot_hit[1] += 1
        j = ih and sh; joint[0] += j; joint[1] += 1
        by_noise[r["noise_label"]][0] += j; by_noise[r["noise_label"]][1] += 1
    acc = lambda p: round(p[0]/p[1], 3) if p[1] else None
    rep = {"missing": miss,
           "intent_accuracy": acc(intent_hit),
           "slot_accuracy": acc(slot_hit),
           "joint_accuracy": acc(joint),
           "by_noise_joint": {k: f"{v[0]}/{v[1]} ({acc(v)})" for k, v in sorted(by_noise.items())}}
    json.dump(rep, open(os.path.join(ROOT, "report_slots.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
