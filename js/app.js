const TOPICS = ["AI", "Security", "Trade", "Climate", "Finance", "Human Rights"];
const TOPIC_LABELS = {
  AI: "AI 人工智能",
  Security: "安全",
  Trade: "贸易",
  Climate: "气候",
  Finance: "金融",
  "Human Rights": "人权",
};
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

let allArticles = [];
let activeSource = "All";
let activeTopic = "All";
let searchQuery = "";

// === Init ===
async function init() {
  try {
    const resp = await fetch("data/articles.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    allArticles = data.articles || [];
  } catch (err) {
    console.error("Failed to load articles:", err);
    renderError("无法加载文章数据。请确保 data/articles.json 文件存在。");
    return;
  }

  if (allArticles.length === 0) {
    renderEmpty();
    return;
  }

  // Sort by date descending
  allArticles.sort((a, b) => (b.pubDate || "").localeCompare(a.pubDate || ""));

  renderStats();
  renderAll();
  bindEvents();
}

// === Filtering ===
function getFilteredArticles() {
  return allArticles.filter((a) => {
    if (activeSource !== "All" && a.source !== activeSource) return false;
    if (activeTopic !== "All" && !(a.categories || []).includes(activeTopic)) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const haystack = [
        a.title, a.title_zh, a.description, a.summary_zh,
        ...(a.authors || []), ...(a.subjects || []),
      ].join(" ").toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });
}

function getCountsByTopic(articles) {
  const counts = {};
  TOPICS.forEach((t) => { counts[t] = 0; });
  articles.forEach((a) => {
    (a.categories || []).forEach((c) => {
      if (counts[c] !== undefined) counts[c]++;
    });
  });
  return counts;
}

// === Rendering ===
function renderAll() {
  const filtered = getFilteredArticles();
  renderFilters(filtered);
  renderArticleList(filtered);
  updateSearchCount(filtered.length);
}

function renderStats() {
  const bar = document.getElementById("stats-bar");
  const swpCount = allArticles.filter((a) => a.source === "SWP").length;
  const cigiCount = allArticles.filter((a) => a.source === "CIGI").length;
  const latest = allArticles[0]?.pubDate || "";
  bar.innerHTML = `
    <strong>${allArticles.length}</strong> 篇文章
    <span class="stats-dot"></span>
    <span>SWP: <strong>${swpCount}</strong></span>
    <span>CIGI: <strong>${cigiCount}</strong></span>
    ${latest ? `<span class="stats-dot"></span>最新: ${latest}` : ""}
  `;
}

function renderFilters(filteredArticles) {
  // Source pills
  const sourceGroup = document.getElementById("source-pills");
  const swpCount = allArticles.filter((a) => a.source === "SWP").length;
  const cigiCount = allArticles.filter((a) => a.source === "CIGI").length;

  sourceGroup.innerHTML = "";
  [
    { key: "All", label: "全部", count: allArticles.length },
    { key: "SWP", label: "SWP", count: swpCount },
    { key: "CIGI", label: "CIGI", count: cigiCount },
  ].forEach(({ key, label, count }) => {
    if (count === 0 && key !== "All") return;
    const pill = document.createElement("span");
    pill.className = `pill${activeSource === key ? " active" : ""}`;
    pill.innerHTML = `${label} <span class="count">${count}</span>`;
    pill.addEventListener("click", () => {
      activeSource = key;
      activeTopic = "All";
      renderAll();
    });
    sourceGroup.appendChild(pill);
  });

  // Topic pills
  const topicGroup = document.getElementById("topic-pills");
  const topicCounts = getCountsByTopic(allArticles);
  topicGroup.innerHTML = "";

  const allTopicPill = document.createElement("span");
  allTopicPill.className = `pill${activeTopic === "All" ? " active" : ""}`;
  allTopicPill.innerHTML = `全部 <span class="count">${allArticles.length}</span>`;
  allTopicPill.addEventListener("click", () => {
    activeTopic = "All";
    renderAll();
  });
  topicGroup.appendChild(allTopicPill);

  TOPICS.forEach((topic) => {
    if (topicCounts[topic] === 0) return;
    const pill = document.createElement("span");
    pill.className = `pill${activeTopic === topic ? " active" : ""}`;
    pill.innerHTML = `${TOPIC_LABELS[topic]} <span class="count">${topicCounts[topic]}</span>`;
    pill.addEventListener("click", () => {
      activeTopic = topic;
      renderAll();
    });
    topicGroup.appendChild(pill);
  });
}

function renderArticleList(filteredArticles) {
  const container = document.getElementById("article-list");

  if (filteredArticles.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <span class="icon">🔍</span>
        <h3>没有找到匹配的文章</h3>
        <p>尝试调整筛选条件或搜索关键词</p>
      </div>`;
    return;
  }

  // Group by date
  const groups = new Map();
  filteredArticles.forEach((a) => {
    const date = a.pubDate || "Unknown";
    if (!groups.has(date)) groups.set(date, []);
    groups.get(date).push(a);
  });

  let html = "";
  groups.forEach((articles, date) => {
    const d = new Date(date + "T00:00:00");
    const weekday = isNaN(d.getTime()) ? "" : WEEKDAYS[d.getDay()];
    const formattedDate = isNaN(d.getTime()) ? date : formatDate(date);

    html += `<div class="date-group">`;
    html += `<div class="date-header">
      ${formattedDate}
      <span class="weekday">${weekday}</span>
      <span class="count">${articles.length} 篇</span>
    </div>`;

    articles.forEach((a) => {
      html += renderCard(a);
    });

    html += `</div>`;
  });

  container.innerHTML = html;

  // Bind tag click events
  container.querySelectorAll(".tag").forEach((tag) => {
    tag.addEventListener("click", (e) => {
      e.stopPropagation();
      const topic = tag.dataset.topic;
      activeTopic = topic;
      renderAll();
      document.querySelector(".controls").scrollIntoView({ behavior: "smooth" });
    });
  });
}

function renderCard(article) {
  const categories = article.categories || [];
  const sourceClass = article.source.toLowerCase();
  const dateDisplay = article.pubDate || "";

  const tagsHtml = categories
    .map((c) => `<span class="tag${activeTopic === c ? " active-tag" : ""}" data-topic="${c}">#${TOPIC_LABELS[c] || c}</span>`)
    .join("");

  return `
    <div class="card">
      <div class="card-meta">
        <span class="source-badge ${sourceClass}">${article.source}</span>
        <span class="card-date">${dateDisplay}</span>
        ${article.type ? `<span class="card-type">${article.type}</span>` : ""}
      </div>
      <div class="card-title">${escapeHtml(article.title)}</div>
      ${article.title_zh ? `<div class="card-title-zh">${escapeHtml(article.title_zh)}</div>` : ""}
      <div class="card-summary">${escapeHtml(article.summary_zh || article.description || "")}</div>
      <div class="card-footer">
        <div class="card-tags">${tagsHtml}</div>
        <a href="${escapeHtml(article.link)}" target="_blank" rel="noopener" class="read-link">
          阅读原文 <span class="arrow">↗</span>
        </a>
      </div>
    </div>`;
}

// === Search ===
let searchTimeout;
function handleSearch(e) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    searchQuery = e.target.value.trim();
    renderAll();
  }, 250);
}

function updateSearchCount(count) {
  const el = document.getElementById("search-count");
  if (el) el.textContent = `找到 ${count} 篇文章`;
}

// === Utilities ===
function formatDate(dateStr) {
  const parts = dateStr.split("-");
  if (parts.length !== 3) return dateStr;
  const months = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  const month = months[parseInt(parts[1]) - 1] || parts[1];
  return `${month} ${parseInt(parts[2])}, ${parts[0]}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderEmpty() {
  document.getElementById("article-list").innerHTML = `
    <div class="empty-state">
      <span class="icon">📭</span>
      <h3>暂无文章</h3>
      <p>文章数据正在收集中，请稍后再来查看。</p>
    </div>`;
}

function renderError(msg) {
  document.getElementById("article-list").innerHTML = `
    <div class="error-state">
      <span class="icon">⚠️</span>
      <h3>数据加载失败</h3>
      <p>${escapeHtml(msg)}</p>
    </div>`;
}

// === Scroll Effects ===
function handleScroll() {
  const controls = document.querySelector(".controls");
  const backToTop = document.getElementById("back-to-top");

  if (window.scrollY > 80) {
    controls?.classList.add("scrolled");
  } else {
    controls?.classList.remove("scrolled");
  }

  if (window.scrollY > 400) {
    backToTop?.classList.add("visible");
  } else {
    backToTop?.classList.remove("visible");
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// === Events ===
function bindEvents() {
  document.getElementById("search-input")?.addEventListener("input", handleSearch);
  window.addEventListener("scroll", handleScroll, { passive: true });
  document.getElementById("back-to-top")?.addEventListener("click", scrollToTop);
}

// === Boot ===
document.addEventListener("DOMContentLoaded", init);
