# update.md

## 2026-09-13 初始版本

### 背景

项目从零建立，目标是把“求职逆向匹配”做成可展示 Demo。

### 目标

先完成数据模型、固定样例、画像提取、评分和 CLI 输出。

### 改动文件

- 建立 `src/reverse_job_match/`
- 建立 `data/jobs_fixture.json`
- 建立 `tests/`
- 增加画像、评分、数据加载、Mock LLM、CLI 和报告模块

### 验证结果

- 固定样例可生成推荐清单。
- 初始 4 项测试通过。

### 下一步

- 增加本地网站，提升展示观感。
- 接入真实岗位采集。

## 2026-09-13 至 2026-09-14 网站与实时采集

### 背景

原 CLI 和 Markdown 展示不足以满足产品 Demo 观感，同时用户要求实时获取真实岗位。

### 目标

增加本地网站、实时只读采集、来源标识和进度反馈。

### 改动文件

- 新增 `server.py`
- 新增 `static/index.html`
- 新增 `static/styles.css`
- 新增 `static/app.js`
- 新增 `collector_adapter.py`
- 新增 `setup_browser.bat`
- 新增 `run_web.bat`

### 验证结果

- 本地网站可运行。
- 实时采集可生成真实岗位。
- 实时采集单独运行约 4.75 秒。

### 下一步

- 接入真实 LLM。
- 优化推荐理由长度和响应速度。

## 2026-09-14 DeepSeek 接入与性能优化

### 背景

Mock 评分虽然能跑通，但分数区分度不足。用户提供 DeepSeek API，并要求压缩响应时间。

### 目标

接入真实 LLM，保持理由简洁，实时模式响应控制在 30 秒内。

### 改动文件

- 修改 `llm_client.py`
- 修改 `json_utils.py`
- 修改 `prompts.py`
- 修改 `score.py`
- 修改 `pipeline.py`
- 修改 `cli.py`
- 修改 `server.py`
- 更新 `.env`

### 验证结果

- DeepSeek 固定样例接口实测约 18.11 秒。
- 推荐榜默认输出 5 条，理由简洁。
- 4 项自动测试通过。

### 下一步

- 根据用户实际使用反馈继续优化。
- 如需提升分数稳定性，可增加轻量离线评估样例。
- 若需要更多推荐数量，再考虑批量评分接口。

## 2026-09-14 GitHub 仓库发布

### 背景

用户希望把项目作为 GitHub 作品集公开保存，并支持后续同步更新。

### 目标

清理敏感内容，创建公开仓库，提供 README、License 和 CI 测试入口。

### 改动文件

- 更新 `README.md`
- 新增 `LICENSE`
- 新增 `.github/workflows/tests.yml`
- 更新 `.gitignore`
- 新增 `setup_vendor.bat`
- 新增 `assets/.gitkeep`

### 验证结果

- 创建公开仓库 `l2643563544-sudo/reverse-job-match-agent`
- 本地分支推送到 `main`
- 敏感文件未进入版本控制
- 创建个人主页仓库 `l2643563544-sudo/l2643563544-sudo` 及 README

### 下一步

- 补充截图、GIF 或演示视频。
- 个人主页 README 已完成。
- 后续每次修改后继续提交和推送。
