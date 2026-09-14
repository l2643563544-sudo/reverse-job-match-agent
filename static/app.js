const form = document.querySelector("#run-form");
const runButton = document.querySelector("#run-button");
const directionInput = document.querySelector("#direction");
const resumeInput = document.querySelector("#resume");
const jdInput = document.querySelector("#jd");
const modeButtons = document.querySelectorAll(".segment");
const message = document.querySelector("#message");
const jobList = document.querySelector("#job-list");
const summarySource = document.querySelector("#summary-source");
const summaryRole = document.querySelector("#summary-role");
const summaryCount = document.querySelector("#summary-count");
const summaryTime = document.querySelector("#summary-time");
const healthDot = document.querySelector("#health-dot");
const healthText = document.querySelector("#health-text");
const progressPanel = document.querySelector("#progress-panel");
const stageText = document.querySelector("#stage-text");

let activeMode = "demo";

const defaults = {
  direction:
    "产品运营实习生，方向偏向用户运营、内容运营和活动运营，意向城市为上海或深圳。",
  resume:
    "求职意向：产品运营实习\n\n个人概述：对互联网产品和用户增长感兴趣，具备内容策划、社群维护和基础数据分析经验。\n\n相关经历：\n- 在校运营学生社群，负责活动策划、通知发布和成员维护。\n- 协助整理课程问卷和报名数据，使用 Excel 制作汇总表和复盘报告。\n- 参与新媒体内容选题和排版。\n\n技能：\n- Excel、Word、PPT\n- 用户运营、内容运营、活动运营",
  jd: "岗位名称：产品运营实习生\n\n职责：\n- 协助产品运营活动策划与执行。\n- 整理用户反馈和运营数据，输出复盘报告。\n- 维护内容与社群，提升用户活跃和留存。\n\n要求：\n- 在校或应届，本科及以上。\n- 熟悉常用办公软件。\n- 有内容运营、社群运营或数据分析经验者优先。",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setMode(mode) {
  activeMode = mode;
  modeButtons.forEach((button) => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

directionInput.value = defaults.direction;
resumeInput.value = defaults.resume;
jdInput.value = defaults.jd;

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    if (data.ok) {
      healthDot.classList.add("is-online");
      healthText.textContent = "服务正常";
    }
  } catch (error) {
    healthDot.classList.remove("is-online");
    healthText.textContent = "连接失败";
  }
}

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("is-error", isError);
  message.style.display = text ? "block" : "none";
}

function renderJobs(jobs) {
  jobList.replaceChildren();
  if (!jobs.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "没有生成推荐结果";
    jobList.append(empty);
    return;
  }

  jobs.forEach((job) => {
    const card = document.createElement("article");
    card.className = "job-card";

    const primary = document.createElement("div");
    const head = document.createElement("div");
    head.className = "job-head";

    const title = document.createElement("h3");
    title.className = "job-title";
    title.textContent = job.title;

    const score = document.createElement("div");
    score.className = "score";
    score.style.setProperty("--score", String(Number(job.match_score).toFixed(0)));
    const scoreText = document.createElement("span");
    scoreText.textContent = Number(job.match_score).toFixed(0);
    score.append(scoreText);

    head.append(title, score);

    const meta = document.createElement("div");
    meta.className = "job-meta";
    [job.company, job.city, job.salary].forEach((value) => {
      const item = document.createElement("span");
      item.className = "meta";
      item.textContent = value;
      meta.append(item);
    });

    const reason = document.createElement("p");
    reason.className = "reason";
    reason.textContent = job.reason || "暂无推荐理由";

    const skills = document.createElement("div");
    skills.className = "skills";
    const skillNames = (job.matched_skills || [])
      .map((item) => item.skill)
      .filter(Boolean);
    const gapNames = (job.gaps || []).filter(Boolean);
    const gapText = gapNames.length ? ` | 缺口：${gapNames.join("、")}` : "";
    skills.textContent = skillNames.length
      ? `匹配技能：${skillNames.join("、")}${gapText}`
      : gapNames.length
        ? `缺口：${gapNames.join("、")}`
        : "";

    const sourceLine = document.createElement("div");
    sourceLine.className = "source-line";

    const sourceBadge = document.createElement("span");
    sourceBadge.className = "source-badge";
    sourceBadge.textContent =
      job.source_label === "live" ? "实时来源" : "固定样例";

    const sourceLink = document.createElement("a");
    sourceLink.className = "source-link";
    sourceLink.textContent = "查看原岗位";
    if (typeof job.url === "string" && /^https?:\/\//.test(job.url)) {
      sourceLink.href = job.url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noreferrer";
    }

    sourceLine.append(sourceBadge, sourceLink);
    primary.append(head, meta, reason, skills, sourceLine);
    card.append(primary);
    jobList.append(card);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  runButton.disabled = true;
  runButton.textContent = "运行中";
  showMessage("");
  jobList.replaceChildren();
  summaryTime.textContent = "-";
  progressPanel.hidden = false;
  stageText.textContent =
    activeMode === "live" ? "正在实时采集岗位" : "正在生成推荐";

  const payload = {
    mode: activeMode,
    direction: directionInput.value.trim(),
    resume: resumeInput.value.trim(),
    jd: jdInput.value.trim(),
  };

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      showMessage(data.error || "运行失败", true);
      summarySource.textContent = "运行失败";
      summaryRole.textContent = "-";
      summaryCount.textContent = "0";
      progressPanel.hidden = true;
      return;
    }

    summarySource.textContent =
      data.source_label === "live" ? "实时采集" : "固定样例";
    summaryRole.textContent = data.target_role || "-";
    summaryCount.textContent = String(data.count);
    summaryTime.textContent =
      (data.jobs && data.jobs[0] && data.jobs[0].collected_at) || "-";
    renderJobs(data.jobs || []);
  } catch (error) {
    showMessage("无法连接本地服务", true);
  } finally {
    runButton.disabled = false;
    runButton.textContent = "运行推荐";
    progressPanel.hidden = true;
  }
});

checkHealth();
