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

## 排行榜（v0 全量 40 条）
| 模型/基线 | clean ↑ | noisy ↑ | accessibility_gap ↓ | overall ↑ |
|---|---:|---:|---:|---:|
| keyword_match (崩塌线) | 1.0 | 0.867 | 0.133 | 0.900 |
| qwen2.5:0.5b (本地) | 0.600 | 0.533 | 0.067 | 0.550 |
| glm-5.2 | 1.0 | 1.0 | **0.0** | **1.0** |
| deepseek-v4-flash | 1.0 | 1.0 | **0.0** | **1.0** |

**v0 诚实结论**：两个强推理模型在粗粒度（3 选 1）意图识别上**完全无障碍**——错别字、方言、语音转写噪声一个没挡住，gap 0.0。**无障碍缺口只在表面匹配基线（keyword 错别字 4/8）和弱小模型（qwen0.5b 0.55）上出现**。这说明：在"听懂老人想干嘛"这个粗层面，当前强模型没问题；真正的无障碍缺口要用更难的任务才能暴露——细粒度槽位（挂哪个科/查哪月养老金）、多意图混杂、答非所问。这是 v0 的边界，也是 v1 的方向（见 PLAN）。qwen0.5b 能被区分（0.55 vs 1.0）证明基准本身有区分力。

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
