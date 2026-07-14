#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically generate data/queries.jsonl — 中文老年人数字无障碍评测.

核心问题：AI 助手能不能听懂老年人？同一个意图，用【清晰】和【老年口语噪声】
两种方式表达，模型的意图识别准确率差多少（accessibility gap）。

每条：intent（封闭意图集）+ 一种表达（clean / noisy），噪声类型标注。
探针为单选（选项含真意图+2 个近似干扰意图），gold=字母 → 纯机器评分。
noisy 变体覆盖：错别字、同音混淆、口语啰嗦、方言词、语音转写断句。
配对设计：每个 intent 有 1 条 clean + 若干 noisy，可算 clean−noisy 差距。"""
import json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "queries.jsonl")
SEED = 20260712

# 意图集（封闭）：老年人高频数字生活场景
INTENTS = {
    "挂号看病": "我想在手机上挂号看病",
    "视频通话": "我想跟家里人视频通话",
    "缴水电费": "我想交水电费",
    "查养老金": "我想查我的养老金到账了没有",
    "调大字体": "我想把手机字调大一点",
    "买药": "我想在网上买点药",
    "查公交": "我想查一下公交车什么时候来",
    "防诈咨询": "有人打电话让我转账我拿不准要不要转",
    "查天气": "我想看看明天天气怎么样",
    "联系子女": "我想给我儿子打个电话但是找不到",
}
# 每个 intent 的 clean 与 noisy 变体（noisy 标注噪声类型）
VARIANTS = {
 "挂号看病": [("clean","我想在手机上挂号看病"),
   ("typo","我想在手几上挂个号看病，那个院怎么弄啊"),
   ("ramble","哎那个我这两天腰不舒服想去医院看看，听说现在都手机上先弄个啥号是吧，我不会整"),
   ("voice","就是那个 挂号 我想挂号 在这手机上 看病挂号 怎么弄")],
 "视频通话": [("clean","我想跟家里人视频通话"),
   ("homophone","我想跟俺家闺女是频通话，能看见人那种"),
   ("dialect","我寻思跟娃儿视频拉呱，就能瞅见脸的那个"),
   ("ramble","那个能看见人说话的那个咋弄，我孙子教过我一回我又忘了")],
 "缴水电费": [("clean","我想交水电费"),
   ("typo","我想交水店费，这个月的还没交呢"),
   ("voice","交费 水费电费 那个 在手机上交 怎么交"),
   ("ramble","以前都是去营业厅交的现在说手机上就能交水电那个费我不太会")],
 "查养老金": [("clean","我想查我的养老金到账了没有"),
   ("typo","我想查查我的样老金这个月到帐了没"),
   ("dialect","俺那退休钱这月来了没得，咋个查嘛"),
   ("homophone","养老金 到帐没 我想查一下 就是每月那个钱")],
 "调大字体": [("clean","我想把手机字调大一点"),
   ("ramble","这手机字咋这么小我眼睛花看不清能不能弄大点那个字"),
   ("typo","手机上的自太小了我想调大点看不清"),
   ("voice","字 太小 看不见 调大 手机字 大一点")],
 "买药": [("clean","我想在网上买点药"),
   ("typo","我想在网上买点要，降压的那种",),
   ("dialect","我想网上整点药，降压药，咋买嘛"),
   ("ramble","那个药店远我腿脚不好听说手机上也能买药是吧我想买点常吃的")],
 "查公交": [("clean","我想查一下公交车什么时候来"),
   ("voice","公交车 几点来 那个几路 我想查 还有多久到"),
   ("typo","我想查下工交车啥时候到站，等半天了"),
   ("dialect","那个巴士还有好久来哦，咋个看嘛")],
 "防诈咨询": [("clean","有人打电话让我转账我拿不准要不要转"),
   ("ramble","刚才接个电话说我孙子出事了让我赶紧转钱过去我这心里慌不知道真的假的"),
   ("typo","有人叫我转帐说是退税还是啥的我不敢弄这靠谱不"),
   ("voice","电话 让转钱 说是 公检法 我要不要 转账")],
 "查天气": [("clean","我想看看明天天气怎么样"),
   ("typo","我想看看明天天汽怎么样，要不要穿厚点"),
   ("dialect","明儿个天气咋样哦，冷不冷嘛"),
   ("voice","天气 明天 下雨不 我想看看")],
 "联系子女": [("clean","我想给我儿子打个电话但是找不到"),
   ("ramble","我想给我儿子打电话这手机里头找来找去找不着他号码了咋办"),
   ("homophone","我想给俺儿子打个店话，号码找不到了"),
   ("dialect","我要跟我娃打电话，号码寻不到咯")],
}
NOISE_LABEL = {"clean":"清晰","typo":"错别字","homophone":"同音混淆",
               "ramble":"口语啰嗦","dialect":"方言词","voice":"语音转写",
               "misleading":"误导埋点"}
# v1 误导型：表面词指向 trap 意图，真实需求(intent)埋在啰嗦里；trap 作为干扰项
HARD = [
 # (真实intent, 文本, trap误导意图)
 ("缴水电费","我孙子跟我说这个微信上就能弄那个费用，我点来点去净是些挂号买药的，我就想把这个月的水费电费给交咯，那个交费的地儿在哪啊","挂号看病"),
 ("联系子女","刚才那个视频我也不想视频了，我就是想直接打个电话给我闺女，语音那种，可这号码咋翻都翻不着","视频通话"),
 ("查养老金","不是买药也不是交费，我就想看看我那个退休金这个月到我卡上没有，别的都不弄","缴水电费"),
 ("防诈咨询","有人发消息说我中奖了让我先交手续费才能领，还有个说是我养老金要重新认证让我转账，我这拿不准到底能不能转钱","查养老金"),
 ("调大字体","这个买药的页面我也不买了，主要是字太小我看不清，你能不能先教我把手机字弄大点","买药"),
 ("查公交","医院我一会儿再去，我现在就想知道我在这站等的那个公交车还有几分钟到，别的先不管","挂号看病"),
 ("视频通话","电话我打过了没人接，我就想那种能看见孙子脸的那个功能，视频的，怎么开","联系子女"),
 ("买药","天气我不看了，我就想在网上把我常吃的降压药买了，家里快没了","查天气"),
 ("挂号看病","养老金我查过了，现在主要是我腰疼想在这手机上先约个号去骨科看看，别的不弄","查养老金"),
 ("查天气","公交我不查了，我就想看看明天下不下雨，要下雨我就不出门了","查公交"),
 ("联系子女","那个转账的事我没弄不敢弄，我就是想给我儿子打个电话问问他这事靠不靠谱，号码找不着","防诈咨询"),
 ("缴水电费","养老金到了我知道了，现在是这个月水电费还没交，我想用手机交了它，就这一件事","查养老金"),
]

def gen():
    rng = random.Random(SEED)
    intents = list(INTENTS)
    rows = []
    qid = 0
    for it in intents:
        for noise, text in VARIANTS[it]:
            qid += 1
            distract = rng.sample([x for x in intents if x != it], 2)
            opts = [it] + distract; rng.shuffle(opts)
            letter = "ABC"[opts.index(it)]
            body = "  ".join(f"{'ABC'[k]}. {o}" for k, o in enumerate(opts))
            rows.append({"id": f"q{qid:03d}", "intent": it,
                         "noise": noise, "noise_label": NOISE_LABEL[noise],
                         "text": text,
                         "probe": f"用户说：“{text}”。请判断用户想做什么？{body}。只输出选项字母。",
                         "gold": letter})
    # v1 误导型：真实 intent + trap 干扰项 + 1 随机干扰
    for it, text, trap in HARD:
        qid += 1
        third = rng.choice([x for x in intents if x not in (it, trap)])
        opts = [it, trap, third]; rng.shuffle(opts)
        letter = "ABC"[opts.index(it)]
        body = "  ".join(f"{'ABC'[k]}. {o}" for k, o in enumerate(opts))
        rows.append({"id": f"q{qid:03d}", "intent": it,
                     "noise": "misleading", "noise_label": NOISE_LABEL["misleading"],
                     "text": text,
                     "probe": f"用户说：“{text}”。请判断用户想做什么？{body}。只输出选项字母。",
                     "gold": letter})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    nc = sum(1 for r in rows if r["noise"] == "clean")
    print(f"wrote {len(rows)} queries ({nc} clean / {len(rows)-nc} noisy), {len(intents)} intents -> {OUT}")

if __name__ == "__main__":
    gen()
