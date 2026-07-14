# PLAN · elderly-accessibility-bench-zh

## 目标
中文老年人数字无障碍评测：AI 助手能否听懂老年人（错别字/同音/方言/口语
啰嗦/语音转写噪声）。头条指标 accessibility_gap = clean − noisy 意图准确率。
与 fraud-detect-bench-zh 联动（老人是诈骗主受害者，含防诈咨询意图）。

## v0（已达成 ✅）
- [x] 种子化生成器：10 意图 × (1 clean + 3 noisy) = 40 条，5 类噪声
- [x] gold 重算校验器（gold 字母须指向本行意图）+ 确定性锁入 CI
- [x] score.py：clean/noisy 准确率、accessibility_gap、按噪声类型细分
- [x] keyword_match 崩塌线基线（错别字击穿）

## v1（已达成 ✅ 2026-07-12）
- [x] 新增 misleading 误导埋点题（表面词指向 trap 意图、真实需求埋在啰嗦里）12 条 → 52 条
- [x] keyword 基线在误导型掉到 9/12(0.75)，证明该类有区分力
- [ ] 双模型重跑填 v1 榜（进行中）
- [x] run_model.py 默认本地 Ollama；零依赖 / CC BY 4.0

## 路线图
- v1：扩到 20 意图 × 更多 noisy，加入"多意图混杂""答非所问"更难项
- v1：多模型排行榜；防诈咨询意图与 fraud-detect-bench-zh 交叉分析
- v2：真实老年人语音转写语料（需伦理与版权处理）
