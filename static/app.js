const form = document.querySelector("#run-form");
const runButton = document.querySelector("#run-button");
const runButtonText = document.querySelector("#run-button-text");
const directionInput = document.querySelector("#direction");
const resumeInput = document.querySelector("#resume");
const jdInput = document.querySelector("#jd");
const modeButtons = document.querySelectorAll(".segment");
const themeButtons = document.querySelectorAll(".theme-option");
const healthDot = document.querySelector("#health-dot");
const healthText = document.querySelector("#health-text");

const emptyState = document.querySelector("#empty-state");
const resultsContent = document.querySelector("#results-content");
const loadingState = document.querySelector("#loading-state");
const loadingSubtitle = document.querySelector("#loading-subtitle");
const errorState = document.querySelector("#error-state");
const errorMessage = document.querySelector("#error-message");
const overviewSection = document.querySelector("#overview-section");
const recommendationSection = document.querySelector(".recommendation-section");

const summarySource = document.querySelector("#summary-source");
const summaryRole = document.querySelector("#summary-role");
const summaryCount = document.querySelector("#summary-count");
const summaryTime = document.querySelector("#summary-time");
const jobList = document.querySelector("#job-list");
const overviewScoreRing = document.querySelector("#overview-score-ring");
const overviewScoreValue = document.querySelector("#overview-score-value");
const matchBuckets = document.querySelector("#match-buckets");
const overviewSkills = document.querySelector("#overview-skills");
const directionCount = document.querySelector("#direction-count");
const resumeCount = document.querySelector("#resume-count");
const jdCount = document.querySelector("#jd-count");

let activeMode = "demo";

const defaults = {
  direction:
    "产品运营实习生，方向偏向用户运营、内容运营和活动运营，意向城市为上海或深圳。",
  resume:
    "求职意向：产品运营实习\n\n个人概述：对互联网产品和用户增长感兴趣，具备内容策划、社群维护和基础数据分析经验。\n\n相关经历：\n- 在校运营学生社群，负责活动策划、通知发布和成员维护。\n- 协助整理课程问卷和报名数据，使用 Excel 制作汇总表和复盘报告。\n- 参与新媒体内容选题和排版。\n\n技能：\n- Excel、Word、PPT\n- 用户运营、内容运营、活动运营",
  jd: "岗位名称：产品运营实习生\n\n职责：\n- 协助产品运营活动策划与执行。\n- 整理用户反馈和运营数据，输出复盘报告。\n- 维护内容与社群，提升用户活跃和留存。\n\n要求：\n- 在校或应届，本科及以上。\n- 熟悉常用办公软件。\n- 有内容运营、社群运营或数据分析经验者优先。",
};

function initTheme() {
  const saved = localStorage.getItem("theme");
  const theme = saved === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = theme;
  themeButtons.forEach((button) => {
    const active = button.dataset.theme === theme;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("theme", theme);
  themeButtons.forEach((button) => {
    const active = button.dataset.theme === theme;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

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
    const active = button.dataset.mode === mode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
}

function updateCharCount(input, output) {
  const max = Number(input.maxLength) || 6000;
  output.textContent = `${input.value.length}/${max}`;
}

function formatTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(11, 16) || "-";
  return `${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes()
  ).padStart(2, "0")}`;
}

function matchLevel(score) {
  if (score >= 90) return "高度匹配";
  if (score >= 75) return "中度匹配";
  return "一般匹配";
}

function setResultVisible(visible) {
  emptyState.hidden = visible;
  resultsContent.hidden = !visible;
}

function showLoading() {
  setResultVisible(true);
  loadingState.hidden = false;
  errorState.hidden = true;
  overviewSection.hidden = true;
  recommendationSection.hidden = true;
  loadingSubtitle.textContent =
    activeMode === "live" ? "正在读取实时岗位" : "正在分析候选岗位";
}

function showError(message) {
  setResultVisible(true);
  loadingState.hidden = true;
  overviewSection.hidden = true;
  recommendationSection.hidden = true;
  errorState.hidden = false;
  errorMessage.textContent = message;
}

function showResults(data) {
  setResultVisible(true);
  loadingState.hidden = true;
  errorState.hidden = true;
  overviewSection.hidden = false;
  recommendationSection.hidden = false;

  summarySource.textContent =
    data.source_label === "live" ? "实时采集" : "固定样例";
  summaryRole.textContent = data.target_role || "-";
  summaryCount.textContent = String(data.count);
  summaryTime.textContent =
    (data.jobs && data.jobs[0] && data.jobs[0].collected_at) || "-";

  renderOverview(data.jobs || []);
  renderJobs(data.jobs || []);
}

function renderOverview(jobs) {
  const scores = jobs.map((job) => Number(job.match_score) || 0);
  const average = scores.length
    ? Math.round(scores.reduce((sum, value) => sum + value, 0) / scores.length)
    : 0;
  overviewScoreRing.style.setProperty("--score", String(average));
  overviewScoreValue.textContent = `${average}%`;

  const buckets = [
    ["高度匹配", jobs.filter((job) => (Number(job.match_score) || 0) >= 90).length],
    ["中度匹配", jobs.filter((job) => { const score = Number(job.match_score) || 0; return score >= 75 && score < 90; }).length],
    ["一般匹配", jobs.filter((job) => (Number(job.match_score) || 0) < 75).length],
  ];

  matchBuckets.replaceChildren();
  buckets.forEach(([label, count]) => {
    const bucket = document.createElement("span");
    bucket.className = "match-bucket";
    bucket.append(`${label} `);
    const strong = document.createElement("strong");
    strong.textContent = String(count);
    bucket.append(strong);
    matchBuckets.append(bucket);
  });

  const skillCounts = new Map();
  jobs.forEach((job) => {
    (job.matched_skills || []).forEach((item) => {
      const skill = item.skill || item;
      if (!skill) return;
      skillCounts.set(skill, (skillCounts.get(skill) || 0) + 1);
    });
  });
  const topSkills = [...skillCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([skill]) => skill);

  overviewSkills.replaceChildren();
  if (topSkills.length) {
    topSkills.forEach((skill) => {
      const tag = document.createElement("span");
      tag.className = "skill-tag";
      tag.textContent = skill;
      overviewSkills.append(tag);
    });
  } else {
    overviewSkills.textContent = "暂无技能标签";
  }
}

function createMeta(value) {
  const item = document.createElement("span");
  item.className = "meta";
  item.textContent = value;
  return item;
}

function createSection(title, values, isGap = false) {
  const section = document.createElement("div");
  section.className = isGap ? "job-section gap-box" : "job-section strength-box";
  const heading = document.createElement("div");
  heading.className = "job-section-title";
  heading.textContent = title;
  section.append(heading);

  if (values.length) {
    const list = document.createElement("ul");
    list.className = "job-section-list";
    values.forEach((value) => {
      const li = document.createElement("li");
      li.textContent = value;
      list.append(li);
    });
    section.append(list);
  } else {
    const empty = document.createElement("div");
    empty.className = "job-section-list";
    empty.textContent = "暂无相关信息";
    section.append(empty);
  }
  return section;
}

function renderJobs(jobs) {
  jobList.replaceChildren();
  if (!jobs.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "没有生成推荐结果";
    jobList.append(empty);
    return;
  }

  jobs.forEach((job, index) => {
    const card = document.createElement("article");
    card.className = "job-card";

    const head = document.createElement("div");
    head.className = "job-card-head";

    const identity = document.createElement("div");
    identity.className = "job-index";

    const rank = document.createElement("span");
    rank.className = "rank-number";
    rank.textContent = String(index + 1).padStart(2, "0");

    const title = document.createElement("h2");
    title.className = "job-title";
    title.textContent = job.title;
    identity.append(rank, title);

    const score = document.createElement("div");
    score.className = "job-score";
    const scoreValue = document.createElement("div");
    scoreValue.className = "job-score-value";
    scoreValue.textContent = `${Number(job.match_score).toFixed(0)}%`;
    const level = document.createElement("span");
    level.className = "match-level";
    level.textContent = matchLevel(Number(job.match_score));
    score.append(scoreValue, level);

    head.append(identity, score);
    card.append(head);

    const meta = document.createElement("div");
    meta.className = "job-meta";
    [job.company, job.city, job.salary, job.experience, job.education].forEach(
      (value) => {
        if (value) meta.append(createMeta(value));
      }
    );
    card.append(meta);

    const summary = document.createElement("div");
    summary.className = "job-summary";
    summary.textContent = job.reason || "暂无匹配结论";
    card.append(summary);

    const skillNames = (job.matched_skills || [])
      .map((item) => item.skill || item)
      .filter(Boolean);
    const gapNames = (job.gaps || []).filter(Boolean);

    const skillTags = document.createElement("div");
    skillTags.className = "job-skill-tags";
    skillNames.forEach((skill) => {
      const tag = document.createElement("span");
      tag.className = "job-skill-tag";
      tag.textContent = skill;
      skillTags.append(tag);
    });
    if (skillNames.length) {
      const section = document.createElement("div");
      section.className = "job-section";
      const heading = document.createElement("div");
      heading.className = "job-section-title";
      heading.textContent = "技能匹配";
      section.append(heading, skillTags);
      card.append(section);
    }

    const strengthValues = (job.matched_skills || [])
      .map((item) => item.candidate_evidence || item.job_evidence || item.skill)
      .filter(Boolean);
    const detailGrid = document.createElement("div");
    detailGrid.className = "job-details";
    detailGrid.append(
      createSection("匹配优势", strengthValues, false),
      createSection("岗位差距", gapNames, true)
    );
    card.append(detailGrid);

    const details = document.createElement("div");
    details.className = "detail-content";
    details.hidden = true;
    details.textContent =
      job.jd || "该岗位暂未提供完整 JD 文本。";

    const footer = document.createElement("div");
    footer.className = "job-footer";

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

    const expandButton = document.createElement("button");
    expandButton.className = "expand-button";
    expandButton.type = "button";
    expandButton.textContent = "展开详细分析";
    expandButton.addEventListener("click", () => {
      const willShow = details.hidden;
      details.hidden = !willShow;
      expandButton.textContent = willShow ? "收起详细分析" : "展开详细分析";
    });

    footer.append(sourceBadge, sourceLink, expandButton);
    card.append(details, footer);
    jobList.append(card);
  });
}

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

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

themeButtons.forEach((button) => {
  button.addEventListener("click", () => setTheme(button.dataset.theme));
});

directionInput.value = defaults.direction;
resumeInput.value = defaults.resume;
jdInput.value = defaults.jd;
directionInput.maxLength = 500;
resumeInput.maxLength = 6000;
jdInput.maxLength = 6000;

directionInput.addEventListener("input", () =>
  updateCharCount(directionInput, directionCount)
);
resumeInput.addEventListener("input", () =>
  updateCharCount(resumeInput, resumeCount)
);
jdInput.addEventListener("input", () => updateCharCount(jdInput, jdCount));

updateCharCount(directionInput, directionCount);
updateCharCount(resumeInput, resumeCount);
updateCharCount(jdInput, jdCount);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  runButton.disabled = true;
  runButtonText.textContent = "运行中";
  summarySource.textContent = "-";
  summaryRole.textContent = "-";
  summaryCount.textContent = "0";
  summaryTime.textContent = "-";
  showLoading();

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
      showError(data.error || "运行失败");
      return;
    }
    showResults(data);
  } catch (error) {
    showError("无法连接本地服务");
  } finally {
    runButton.disabled = false;
    runButtonText.textContent = "运行推荐";
  }
});

initTheme();
setResultVisible(false);
checkHealth();
