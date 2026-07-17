# elderly-accessibility-bench-zh

中文**老年人数字无障碍**评测：AI 助手能不能听懂老年人？（可机器评分 · 种子化可复现）

[![CI](https://github.com/uninhibited-scholar/elderly-accessibility-bench-zh/actions/workflows/validate.yml/badge.svg)](https://github.com/uninhibited-scholar/elderly-accessibility-bench-zh/actions/workflows/validate.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

老年人用 AI 助手时，表达往往带错别字、同音字、方言、口语啰嗦、语音转写断句。**同一个意图，用清晰表达和老年口语噪声表达，模型的意图识别准确率差多少？** 这个差距（accessibility gap）就是数字无障碍的量化指标。与 [fraud-detect-bench-zh](https://github.com/uninhibited-scholar/fraud-detect-bench-zh) 联动——老人是电信诈骗的主要受害者，本基准含"防诈咨询"意图。

## 怎么测
10 个高频老年数字生活意图（挂号看病 / 视频通话 / 缴水电费 / 查养老金 / 调大字体 / 买药 / 查公交 / 防诈咨询 / 查天气 / 联系子女），每个 1 条 clean + 3 条 noisy（共 40 条）。noisy 覆盖 5 类噪声：错别字、同音混淆、口语啰嗦、方言词、语音转写。探针为三选一意图识别，gold 封闭字母 → 纯机器评分。

## 指标
`accessibility_gap` = `clean_accuracy` − `noisy_accuracy`（↓ 越小越无障碍）· 按噪声类型细分定位最难的一类 · `overall_accuracy`

## 基线：keyword_match（崩塌线）
```
clean 1.0 / noisy 0.867 / gap 0.133 · 错别字 4/8(0.5) 最难
```
朴素关键词匹配对方言/口语其实还行（意图词仍在），但**错别字**（手几/水店/样老金）直接击穿——正是需要语义理解而非表面匹配的证据。

## 排行榜（v1 全量 52 条，含 12 条误导埋点题）
| 模型/基线 | clean ↑ | noisy ↑ | gap ↓ | 误导埋点 ↑ | overall ↑ |
|---|---:|---:|---:|---:|---:|
| keyword_match (崩塌线) | 1.0 | 0.833 | 0.167 | 9/12 (0.75) | 0.865 |
| qwen2.5:0.5b (本地) | 0.600 | 0.500 | 0.100 | 5/12 (0.417) | 0.519 |
| glm-5.2 | 1.0 | 1.0 | **0.0** | 12/12 (1.0) | **1.0** |
| deepseek-v4-flash | 1.0 | 1.0 | **0.0** | 12/12 (1.0) | **1.0** |

**v1 结论（比 v0 更硬的诚实）**：v1 专门加了 12 条**误导埋点题**（文本表面词指向错误意图、真实需求埋在啰嗦里），想逼出强模型的无障碍缺口——结果两个强模型**依旧 52/52 全对，误导题 12/12**。这说明问题不在"题不够难"，而在**题型**：3 选 1 的意图分类，对强推理模型太容易，无论怎么加噪声/误导都挡不住。**要测出强模型的真实无障碍缺口，必须换成开放式槽位抽取**（让模型自己产出"挂哪个科""查哪个月养老金"，而非从 3 个选项里挑），这是 v2 的方向。

区分力仍在：误导埋点题上 keyword 掉到 0.75、qwen0.5b 掉到 0.417（弱模型确实被误导），强模型 1.0——基准能拉开弱模型与强模型、表面匹配与语义理解，只是当前题型触不到强模型的天花板。

## 跑真实模型
默认走本地 Ollama（`http://localhost:11434/v1`，无需 key）；云端可选 `OPENAI_BASE_URL` + `OPENAI_API_KEY`。
```bash
ollama serve && python3 scripts/run_model.py --model qwen2.5
python3 scripts/score.py predictions_qwen2.5.jsonl
```

## 质量保证
`scripts/check_bench.py` + CI：schema、封闭意图集、**gold 重算**（gold 字母须指向本行意图）、每意图 clean+noisy 覆盖；CI 另跑确定性锁（重跑生成器 + `git diff --exit-code`）。

## 诚实边界
v0、40 条、单人构建、**确定性公开 gold**（非隐藏测试集、不抗污染、基准内结论）；噪声为人工模拟的老年表达，**非真实老年人语料**（真实语音转写涉伦理与版权，见 PLAN 路线图）；样本小、CI 宽。许可 CC BY 4.0。

## v2 排行榜：开放式槽位抽取（24 条，`data/slots.jsonl`）
不给选项，模型须自己从老年口语噪声里**产出**意图 + 具体槽位值（哪个科/哪月/哪种费/几路车）。评分：intent 关键词命中 + slot 值归一化命中（含中文↔阿拉伯数字、同义词），joint = 两者都对。

| 模型 | intent ↑ | slot ↑ | joint ↑ |
|---|---:|---:|---:|
| qwen2.5:0.5b (本地) | 0.625 | 0.792 | 0.583 |
| glm-5.2 | 0.958 | 0.958 | **0.917** |
| deepseek-v4-flash | 0.958 | 0.958 | **0.917** |

**v2 结论（三轮验证后的诚实版）**：换成开放式抽取后，强模型终于从选择题的 100% 掉到 ~0.917（22/24）——但逐条核查那 2 个"失败"：一个是模型答"3"而 gold 要"三路"（缺"路"字单位），一个是防诈题槽位定义本身有歧义（模型答"冒充公检法洗钱"、gold 写"转账"，都说得通）。**即：公平评分后，强模型对老年中文的意图+槽位理解依然接近饱和，残余是 gold 设计边界而非模型失败。** 真正的能力差距仍在弱模型（qwen0.5b joint 0.583）。

> **方法论诚实记录（本项目最有价值的一条）**：v2 评分先后暴露 3 处评分器死板——意图措辞不同（"挂号"vs"挂号看病"）、中文/阿拉伯数字（"三路"vs"3路"）、"十六"被逐字换成"106"的数字解析 bug、同义词（"本月"vs"这个月"）。每一处都曾让强模型看起来"错一片"，人工核查后全是评分问题。**教训：对强模型，评测的瓶颈往往是评分 harness 的公平性，不是任务本身。** 修复过程见 commit 历史与 `scripts/score_slots.py`。
