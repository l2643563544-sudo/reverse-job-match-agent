# 求职逆向匹配 Agent「Vibe Coding 速通流程」

> **目标**：用最短时间做出一个能完整跑通、能写进简历、能讲清原理的求职岗位匹配 Agent。
> **边界**：只跑通一次、仅用于展示、不上线、不应对真实业务。
> **版本**：v1.0 ｜ 创建：2026-09-13

---

## 一、项目定位（先立框架，面试开场就讲这个）

**一句话**：输入「我的简历 + 心仪岗位方向 + 目标 JD」，输出一份来自招聘平台的、按匹配度排序的岗位推荐清单。

**差异化**：市面上的求职工具都是「正向」——先抓一堆岗位，再拿简历去匹配投递。我这个是「**逆向**」——先有明确的岗位画像（从目标 JD 反推），再反向去招聘平台搜符合画像的岗位。

**三层架构**（面试时画这个图）：

```
输入层   简历(md) + 岗位方向 + 目标JD
   ↓
画像层   LLM Prompt① → 抽取结构化求职画像（技能/赛道/薪资/城市）
   ↓
采集层   复用 boss-zhipin-scraper → 按关键词抓 Boss直聘岗位JD
   ↓
匹配层   LLM Prompt② → 画像 vs 每条JD → 匹配度(0-100) + 理由
   ↓
输出层   排序过滤 → Markdown 推荐清单
```

---

## 二、技术选型（每个选择都要能说出"为什么"）

| 层 | 选型 | 为什么（面试考点） |
|----|------|------------------|
| 采集 | `eatmoreduck/boss-zhipin-scraper`（Chrome CDP） | Boss直聘**无公开 API** 且带**字体反爬**；CDP 复用真实登录态是最稳、最省事的方案 |
| 匹配 | LLM（DeepSeek / GPT / Claude 任一） | 语义理解 > 关键词硬匹配；且能输出「匹配理由」——**可解释性**是核心卖点 |
| 语言 | Python | 爬虫 + LLM 调用生态成熟，脚本串联快 |
| 输出 | Markdown | 直接可读，无需写前端，速通友好 |

> 关键判断：**采集层不要自己写**（反爬是深坑，会拖死你），**匹配层自己写**（这是你的差异化，也是面试能展开讲的部分）。

---

## 三、分步流程（5 个 Phase，总约 3-4 天）

### Phase 0：环境准备 + 跑通采集（0.5 天）

**目标**：能用现成工具抓到 Boss直聘真实岗位 JD。

**实现要点**：
1. `git clone https://github.com/eatmoreduck/boss-zhipin-scraper`
2. 按 README 装依赖，本地 Chrome 登录 Boss直聘（复用真实登录态）
3. 跑通一次抓取，确认输出 JSON/CSV 含「岗位名 + JD全文 + 薪资 + 城市 + 公司规模」

**产出物**：`data/jobs_raw.json`（10-30 条岗位）

**面试追问点**：数据从哪来？→ Boss直聘没有公开 API，我用 Chrome DevTools Protocol 连接本地已登录的 Chrome，复用真实登录态调用它的搜索接口，同时绕过前端字体反爬。

---

### Phase 1：画像提取 Prompt①（0.5 天）

**目标**：把「简历 + 岗位方向 + 目标 JD」变成结构化画像 JSON。

**实现要点**：
1. 简历先转成纯文本（md/txt）
2. 设计 Prompt①（完整模板见附录 A），要求 LLM 输出**严格 JSON**
3. 解析 JSON，校验字段完整性，失败则重试

**产出物**：`data/profile.json`

**面试追问点**：为什么用 LLM 提取画像？→ 简历是非结构化文本，规则/正则抽不干净；LLM 能做语义抽取，输出结构化画像，既方便后续匹配，也让「为什么推荐这个岗」可解释。

---

### Phase 2：岗位采集（0.5 天）

**目标**：用画像里的关键词，批量抓目标赛道的岗位。

**实现要点**：
1. 从 `profile.json` 的 `track_keywords` 提取 3-5 个搜索词
2. 逐个关键词调采集工具抓取，**去重**（按岗位 ID/链接）
3. 存 `data/jobs.json`（30-100 条）

**产出物**：`data/jobs.json`

**面试追问点**：怎么控制抓取量、不触发风控？→ 复用工具的限速/随机延迟机制；抓取量控制在百条内（展示够用）；只抓不投递，风险低。

---

### Phase 3：匹配打分 Prompt②（1 天，核心）

**目标**：对每条 JD 打 0-100 匹配分 + 匹配理由。

**实现要点**：
1. 设计打分 rubric（技能重合 40% / 赛道契合 30% / 经验 20% / 薪资城市 10%）
2. 逐条调用 LLM（画像 + 单条 JD → JSON），输出 `match_score` + `matched_skills` + `gap` + `reason`
3. **处理 LLM 输出不稳定**：JSON 解析失败重试 1-2 次；温度调低（0.2-0.3）；用 `json.loads` 校验

**产出物**：`data/scored_jobs.json`

**面试追问点**：怎么保证打分稳定一致？→ 用 rubric 固定评分维度 + 权重；要求严格 JSON 输出；温度调低降低随机性；解析失败自动重试。同时承认「LLM 打分存在一定波动，但对排序结论影响可控」。

---

### Phase 4：排序过滤 + 串联 CLI（0.5 天）

**目标**：一条命令跑通全流程，输出最终清单。

**实现要点**：
1. 写 `main.py` 串联 Phase 1→4（画像 → 采集 → 打分 → 输出）
2. 排序（按 `match_score` 降序）+ 过滤（分数阈值，如 ≥60）+ 去重
3. 输出 `output/recommendations.md`（表格：岗位名 / 公司 / 薪资 / 城市 / 匹配度 / 匹配理由）

**产出物**：`output/recommendations.md` + 一次完整跑通

**面试追问点**：怎么运行？→ 命令行执行 `python main.py --resume 简历.md --direction 产品运营 --jd 目标JD.md`，自动产出推荐清单。

---

### Phase 5：Demo 录制 + README（0.5 天）

**目标**：面试展示用。

**实现要点**：
1. 录一段 30-60 秒演示（输入 → 跑 → 出清单）
2. 写 README（架构图 + 运行方式 + 示例输出）

**产出物**：demo 视频 + README

---

## 四、关键技术点深挖（面试必问，逐个准备好话术）

### 4.1 数据来源与反爬（必问）

- **Q：Boss直聘有 API 吗？** 没有公开 API。我通过 Chrome DevTools Protocol（CDP）连接本地已登录的 Chrome，复用真实登录态调用其前端搜索接口。
- **Q：反爬怎么破？** 两个难点：① 登录态——复用真实 Chrome Profile；② **字体反爬**（页面文字用自定义字体映射，直接抓是乱码）——工具已做字体映射还原，输出明文薪资。
- **Q：合规吗？** 仅个人学习研究 + 展示，不商业转售、不恶意高频抓取，控制抓取量。

### 4.2 匹配逻辑（必问，最能体现深度）

- **Q：为什么用 LLM，而不是关键词匹配或 embedding？** 三层递进：
  1. 关键词匹配：只能硬碰硬，漏掉语义相近但措辞不同的岗位（如"用户增长" vs "增长运营"）；
  2. Embedding + 余弦相似度：能做语义相似，但**不可解释**（只给一个分数，说不出为什么）；
  3. LLM：既能语义理解，又能输出**匹配理由 + 缺口**，可解释性好，这正是求职场景最需要的。
- **可加分的说法**：如果面试官问"embedding 是不是更快更便宜"，回答——embedding 适合做**粗筛**（快速从 1000 条里筛出 Top 50），LLM 做**精排**（对 Top 50 打分+给理由），这是"召回 + 精排"的两段式，工业界通用做法。这是你的优化方向，体现思考深度。

### 4.3 Prompt 设计（必问，模板见附录）

- **Q：Prompt 怎么设计的？** 两个核心 prompt：
  1. **画像提取**：角色设定（招聘顾问）+ 输入（简历/方向/JD）+ 严格 JSON schema 约束；
  2. **匹配打分**：评分 rubric（四维加权）+ 严格 JSON 输出 + 理由字数限制。
- **设计原则**：结构化输出（JSON schema 约束）、打分维度显式化（rubric）、温度调低保证稳定。

### 4.4 运行方式（必问）

- 纯命令行 CLI，一条命令跑通；输入三个文件（简历/方向/JD），输出一个 Markdown 清单；无前端、无数据库、无部署。

### 4.5 效果评估（体现严谨性）

- **Q：怎么知道匹配准不准？** 目前用**人工抽查**：随机抽 10 条推荐结果，检查匹配理由是否合理、打分是否大致符合直觉；记录 bad case（如"JD 里要求 3 年经验但画像只写了实习"，分数却没降）。诚实说明：这是展示型项目，没做大规模量化评测，但 bad case 分析能体现工程意识。

---

## 五、简历成果描述（可直接抄，三档可选）

### 精简版（一句话，放项目列表）

> **逆投（ReverseJobMatch）— 求职岗位逆向匹配 Agent**：基于 LLM 的岗位逆向检索工具，输入简历与目标 JD 画像，通过 Chrome CDP 采集 Boss直聘真实岗位、LLM 四维加权打分（技能/赛道/经验/薪资），输出按匹配度排序的岗位推荐清单及匹配理由。Python + LLM API + Chrome DevTools Protocol。

### 标准版（STAR，放项目经历）

> **项目背景**：招聘平台推荐不准，想「从目标岗位反推匹配岗位」。
> **我的方案**：设计「画像提取 → 岗位采集 → LLM 匹配打分 → 排序输出」四层流水线。画像层用 LLM 将简历+JD 抽取为结构化求职画像；采集层复用开源 CDP 方案绕过 Boss直聘字体反爬抓取真实岗位；匹配层用 LLM 按四维 rubric 打 0-100 分并输出匹配理由。
> **结果**：单命令跑通全流程，输入简历+方向+JD，约 X 秒产出 N 条高匹配岗位清单（含匹配理由），替代人工逐条翻 JD 的重复劳动。

### 技术栈标签（简历技能栏）

`Python` `LLM 应用开发` `Prompt Engineering` `Chrome DevTools Protocol` `数据采集/反爬`

---

## 六、面试追问应对清单（高频 10 问）

| # | 追问 | 应对要点 |
|---|------|---------|
| 1 | 数据从哪来？ | CDP 复用登录态，无公开 API |
| 2 | 反爬怎么处理？ | 字体反爬绕过 + 登录态复用 + 限速 |
| 3 | 为什么用 LLM 不用关键词/embedding？ | 可解释性；embedding 做粗筛、LLM 做精排是进阶 |
| 4 | Prompt 怎么保证输出稳定？ | JSON schema + rubric + 低温 + 重试 |
| 5 | 打分怎么保证准确？ | 固定 rubric 加权 + 人工抽查 + bad case |
| 6 | 怎么运行？ | 单命令 CLI，无前端无部署 |
| 7 | 和现成投递工具（JobClaw 等）区别？ | 他们是「岗位→投递」正向，我是「画像→岗位」逆向 |
| 8 | 数据合规吗？ | 个人学习展示，控量、不转售 |
| 9 | 如果岗位量很大怎么扩展？ | 两段式：embedding 粗筛 + LLM 精排，可并行 |
| 10 | 遇到 LLM 返回乱格式怎么办？ | 解析校验 + 重试 + 降级（失败则标记低置信） |

---

## 附录 A：核心 Prompt 模板（可直接抄）

### Prompt① 画像提取

```text
你是一名资深招聘顾问。请根据以下信息，提取求职者的结构化求职画像。

【简历】
{resume}

【目标岗位方向】
{direction}

【目标JD参考】
{reference_jd}

请严格输出 JSON（不要输出任何其他文字），字段如下：
{
  "target_role": "目标岗位名",
  "skills": ["核心技能1", "核心技能2", "..."],
  "track_keywords": ["赛道/领域关键词，用于岗位搜索", "..."],
  "salary_expectation": "薪资预期或'不限'",
  "cities": ["意向城市1", "..."],
  "experience_level": "实习 / 应届 / 1-3年",
  "profile_summary": "一句话画像描述（50字内）"
}
```

### Prompt② 匹配打分

```text
你是一名招聘匹配评估专家。请评估「求职者画像」与「岗位JD」的匹配程度。

【求职者画像】
{profile_json}

【岗位JD】
{job_jd}

按以下维度打分（加权合成 0-100）：
- 技能重合度（权重40%）
- 岗位方向/赛道契合（权重30%）
- 经验匹配（权重20%）
- 薪资/城市匹配（权重10%）

请严格输出 JSON（不要输出任何其他文字）：
{
  "match_score": 0到100的整数,
  "matched_skills": ["重合的技能"],
  "gap": ["该岗位要求但你缺失的点"],
  "reason": "不超过50字的匹配理由"
}
```

---

## 附录 B：main.py 骨架（精简可跑版）

```python
import json, os
import openai  # 或 requests 直接调 DeepSeek/GPT

# 1. 画像提取
def build_profile(resume, direction, jd):
    prompt = PROMPT1.format(resume=resume, direction=direction, reference_jd=jd)
    raw = llm_call(prompt, temperature=0.2)
    return parse_json(raw)  # 失败重试

# 2. 采集（调用 boss-zhipin-scraper，产出 jobs_raw.json）
def collect_jobs(keywords):
    # 复用工具命令，按关键词抓取，去重
    return load_json("data/jobs.json")

# 3. 匹配打分
def score_jobs(profile, jobs):
    scored = []
    for job in jobs:
        raw = llm_call(PROMPT2.format(profile_json=profile, job_jd=job["jd"]),
                       temperature=0.2)
        r = parse_json(raw)
        scored.append({**job, **r})
    return scored

# 4. 排序输出
def main():
    args = parse_args()  # --resume --direction --jd
    profile = build_profile(...)
    jobs = collect_jobs(profile["track_keywords"])
    scored = [s for s in score_jobs(profile, jobs) if s["match_score"] >= 60]
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    write_markdown(scored, "output/recommendations.md")

if __name__ == "__main__":
    main()
```

> 关键：`llm_call` 和 `parse_json` 是唯二需要认真写的工具函数，其余都是胶水。

---

## 附：本次速通的总投入与验收标准

| 项 | 内容 |
|----|------|
| 总投入 | 3-4 个整天（业余约 1-2 周） |
| 验收标准 | 单命令跑通；输入简历+方向+JD；输出 ≥10 条带匹配理由的岗位清单；demo 可展示 |
| 前置条件 | 能访问 LLM API（DeepSeek 便宜够用）；本地 Chrome；Boss直聘账号 |

**一句话记住这个项目的价值**：它证明你「能独立把一个 LLM 应用从 0 搭到能跑」，并且「讲得清楚每个技术决策背后的取舍」——这比项目本身功能多完整更重要。
