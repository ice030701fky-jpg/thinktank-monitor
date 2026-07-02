# ThinkTank Monitor · 智库文章监测

每日自动监测 **SWP Berlin** 和 **CIGI** 国际顶尖智库的最新英文文章，通过 DeepSeek AI 生成中文摘要并进行主题分类。

## 功能

- 每日自动抓取 SWP、CIGI 最新发表文章
- AI 生成中文摘要（DeepSeek API）
- 按来源（SWP / CIGI）和主题（AI、安全、贸易、气候、金融、人权）分类
- 支持关键词搜索
- 浅色主题，响应式设计
- GitHub Pages 一键部署

## 快速开始

### 1. Fork 或克隆本仓库

```bash
git clone <your-repo-url>
cd thinktank
```

### 2. 配置 DeepSeek API Key

在 GitHub 仓库页面：
- **Settings → Secrets and variables → Actions → New repository secret**
- 名称: `DEEPSEEK_API_KEY`
- 值: 你的 DeepSeek API Key

### 3. 首次手动运行抓取

- 前往 **Actions** 标签页
- 选择 **Daily Article Scraper** workflow
- 点击 **Run workflow** 手动触发

### 4. 启用 GitHub Pages

- **Settings → Pages**
- Source: `Deploy from a branch`
- Branch: `main` (或 `gh-pages`)，目录 `/ (root)`
- 保存，等待部署完成

### 5. 本地开发

```bash
# 安装依赖
pip install -r scraper/requirements.txt

# 本地运行抓取（需要设置环境变量）
export DEEPSEEK_API_KEY="your-api-key"
python scraper/main.py

# 本地预览前端
python3 -m http.server 8080
# 打开 http://localhost:8080
```

## 工作原理

```
GitHub Actions (每日定时 8:37 UTC)
    │
    ├─ 1. 抓取 SWP RSS feed
    │     └─ https://www.swp-berlin.org/en/SWPPublications.xml
    │
    ├─ 2. 抓取 CIGI publications (即将支持)
    │     └─ https://www.cigionline.org/publications/
    │
    ├─ 3. 对比已有文章，识别新文章
    │
    ├─ 4. 调用 DeepSeek API
    │     ├─ 主题分类 (AI/Security/Trade/Climate/Finance/Human Rights)
    │     ├─ 标题翻译为中文
    │     └─ 生成中文摘要 (150-300字)
    │
    ├─ 5. 保存到 data/articles.json
    │
    └─ 6. 自动 commit & push → GitHub Pages 更新
```

## 项目结构

```
thinktank/
├── index.html              # 前端页面
├── css/
│   └── style.css           # 样式 (浅色主题)
├── js/
│   └── app.js              # 前端逻辑 (筛选、搜索、渲染)
├── data/
│   └── articles.json       # 文章数据 (自动更新)
├── scraper/
│   ├── requirements.txt    # Python 依赖
│   ├── main.py             # 主程序
│   ├── config.py           # 配置
│   ├── swp_scraper.py      # SWP RSS 解析
│   ├── ai_processor.py     # DeepSeek API 集成
│   └── storage.py          # JSON 读写
├── .github/
│   └── workflows/
│       └── daily_scrape.yml # GitHub Actions 定时任务
└── README.md
```

## 主题分类

| 主题 | 涵盖范围 |
|------|---------|
| **AI** | 人工智能、数字政策、网络安全、技术治理 |
| **Security** | 国防安全、军事冲突、地区争端、反恐 |
| **Trade** | 国际贸易、经济制裁、供应链、贸易协定 |
| **Climate** | 气候政策、环境治理、能源转型、可持续发展 |
| **Finance** | 全球经济、货币政策、金融监管、发展融资 |
| **Human Rights** | 人权、民主治理、国际法、人道主义 |

## 数据源

- [SWP Berlin](https://www.swp-berlin.org/en/) — 德国国际与安全事务研究所
- [CIGI](https://www.cigionline.org/) — 加拿大国际治理创新中心（即将支持）
