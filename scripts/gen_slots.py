#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2: 开放式槽位抽取（data/slots.jsonl）。老年口语噪声文本 → 模型须自己产出
intent + 具体槽位值（哪个科/哪月/哪种费），不给选项。这是选择题测不出、
需要模型『生成』而非『选择』的任务，用来逼出强模型的真实无障碍缺口。
gold = {intent, slot_name, slot_value}，程序化断言评分（归一化 contains）。"""
import json, os, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "slots.jsonl")
SEED = 20260712

# (intent, slot_name, slot_value, noise, 文本——槽位以噪声/埋点/方言形式出现)
ITEMS = [
 ("挂号看病","科室","骨科","typo","我腰疼腿也疼想在手机上挂个骨可的号，那个骨头的科"),
 ("挂号看病","科室","眼科","ramble","我这眼睛最近看东西模模糊糊的想去医院看看眼睛挂号挂哪个我也不懂就是眼睛的那个科"),
 ("挂号看病","科室","心内科","dialect","我这心口窝老是发慌，想挂个看心脏的科，心内那个"),
 ("挂号看病","科室","皮肤科","misleading","降压药我一会儿再买，主要是我这胳膊上起了好多疹子痒得很，想挂个看皮肤的号"),
 ("查养老金","月份","上个月","ramble","我这养老金这个月的我看着到了我就想查查上个月那笔到底到了没有我记不清了"),
 ("查养老金","月份","三月","typo","帮我看看我三月份的样老金到帐了没有，就三月那一笔"),
 ("查养老金","月份","这个月","dialect","俺这退休钱这月来了没得，就问这个月的"),
 ("缴水电费","费种","电费","misleading","挂号的事我弄完了，现在就想单独把这个月的电费交了，水费上回交过了不用"),
 ("缴水电费","费种","水费","ramble","那个费用我想交一下就是水的那个费，电费物业代扣了我就交个水费"),
 ("缴水电费","费种","燃气费","typo","我想交个燃气费，就是烧饭那个然气的费用"),
 ("买药","药名","降压药","dialect","我想网上整点降压药，就是管血压高的那个药"),
 ("买药","药名","感冒药","ramble","我这两天有点头疼脑热的想买点药就那种治感冒的感冒药"),
 ("买药","药名","胃药","misleading","天气我不看了，我胃不舒服想买点养胃的胃药，就这一样"),
 ("查公交","线路","三路","typo","我想查下工交三路车啥时候到，就3路"),
 ("查公交","线路","十六路","voice","公交 十六路 几点来 我等的那个 16路"),
 ("查公交","线路","五路","dialect","那个五路巴士还有好久来哦，就5路"),
 ("联系子女","对象","女儿","misleading","视频我不弄了，我就想打电话给我闺女，就我女儿"),
 ("联系子女","对象","儿子","ramble","我想给我娃打个电话就是我那个儿子号码找不着了"),
 ("联系子女","对象","孙子","dialect","我寻思给俺大孙子打个电话，就孙子"),
 ("查天气","时间","后天","ramble","明天我知道了不下雨我就想问问后天的天气咋样后天冷不冷"),
 ("查天气","时间","明天","typo","我想看看明天天汽怎么样"),
 ("视频通话","对象","孙女","dialect","我要跟俺孙女视频拉呱，能瞅见脸那个，孙女"),
 ("防诈咨询","风险类型","转账","misleading","中奖的事我没理，就是有人打电话说我涉嫌洗钱让我把钱转到安全账户我拿不准这转账能不能弄"),
 ("防诈咨询","风险类型","中奖","ramble","有人发短信说我中了大奖让我先交个税才能领我这不知道这中奖是不是真的"),
]
NOISE_LABEL = {"typo":"错别字","ramble":"口语啰嗦","dialect":"方言词",
               "voice":"语音转写","misleading":"误导埋点"}

def gen():
    rows = []
    for i, (intent, sname, sval, noise, text) in enumerate(ITEMS, 1):
        rows.append({"id": f"s{i:03d}", "intent": intent, "slot_name": sname,
                     "slot_value": sval, "noise": noise, "noise_label": NOISE_LABEL[noise],
                     "text": text,
                     "prompt": (f"用户说：“{text}”。请抽取用户意图和关键信息，"
                                f"严格输出 JSON：{{\"intent\":\"意图\",\"{sname}\":\"具体值\"}}。"
                                f"只输出 JSON。")})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} slot queries -> {OUT}")

if __name__ == "__main__":
    gen()
