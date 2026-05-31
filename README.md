# CrossMart Monitor — 亚马逊 ASIN 智能监控系统

**在线预览**: https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html

---

## 这个项目做什么？

**核心功能**：监控亚马逊 ASIN 的价格、评分、评论数、BSR 排名、变体状态、Deal 活动、优惠券、Prime 折扣、徽章变化等全维度指标，支持 ASIN 监控 + 关键词搜索结果监控，定时抓取 + 实时展示。

---

## 系统架构

```
用户浏览器（GitHub Pages）
        ↓ 刷新
┌─────────────────────────────────────────────┐
│  GitHub Pages (charlescome1995-prog.github.io) │
│  frontend/monitor.html ← 展示层，读取 rawData.json │
└─────────────────────────────────────────────┘

操作者电脑（本地）
┌─────────────────────────────────────────────┐
│  Edge 浏览器（闫旭默认 profile，CDP 端口 9225）   │
│  ├─ 亚马逊前台（已登录）                         │
│  └─ 卖家精灵 sellersprite.com（已登录）           │
│                                             │
│  backend/run_monitor.py ← 入口脚本            │
│  ├─ keyword_monitor.py  ← 关键词搜索结果抓取    │
│  ├─ asin_monitor.py     ← ASIN详情页抓取        │
│  └─ sync_monitor_data.py ← 同步数据到 rawData.json │
└─────────────────────────────────────────────┘
        ↓ 推送
┌─────────────────────────────────────────────┐
│  GitHub 仓库（main 分支）                       │
│  frontend/data/rawData.json                  │
│  backend/data/user_config.json               │
│  backend/data/trigger.json                   │
└─────────────────────────────────────────────┘
```

---

## 目录结构

```
crossmart-monitor/
│
├── backend/                    # 后端（本地运行，不上 GitHub Pages）
│   ├── run_monitor.py          # 监控入口脚本（本地触发抓取）
│   ├── sync_monitor_data.py    # 同步快照数据 → frontend/data/rawData.json
│   ├── api_server.py           # 本地 API Server（端口 8765）
│   ├── data/
│   │   ├── user_config.json    # 用户配置的 ASINs + 关键词（GitHub Actions 写入）
│   │   ├── trigger.json        # 触发器状态（pending/done）
│   │   ├── keyword_related_asins.json  # 关键词关联的 ASIN 列表
│   │   ├── monitor_list.json   # 历史监控列表（备用）
│   │   ├── keyword_list.json   # 历史关键词列表（备用）
│   │   └── processed/          # 抓取快照数据（每个 ASIN/关键词一个目录）
│   │       ├── asin_B09V7Z4TJG/
│   │       │   ├── _meta.json           # ASIN 基本信息 + 关联竞品列表
│   │       │   ├── latest.json          # 最新快照
│   │       │   └── snapshot_YYYYMMDD_HHMMSS.json  # 历史快照
│   │       └── kw_batana_oil/
│   │           ├── latest.json           # 关键词最新快照
│   │           └── snapshot_YYYYMMDD_HHMMSS.json  # 历史快照
│   └── browser/
│       ├── asin_monitor.py      # ASIN 详情页抓取（价格/BSR/评分/评论/变体/Deal/徽章等）
│       ├── keyword_monitor.py   # 关键词搜索结果抓取（top 5 ASINs + 图片）
│       ├── amazon_browser.py    # 亚马逊前台操作底层
│       ├── sprite_bridge.py     # 卖家精灵 SPA 操作桥接
│       ├── cdp_bridge.py         # Chrome DevTools Protocol 底层桥接
│       ├── human_timer.py       # 人类行为模拟（反爬）
│       ├── snapshot_storage.py  # 快照读写
│       └── init_browsers.py     # Edge 浏览器启动
│
├── frontend/                   # 前端（部署到 GitHub Pages）
│   ├── monitor.html            # ⭐ 监控展示页面
│   ├── selection.html          # 选品页面（未启用）
│   └── data/
│       ├── rawData.json        # 实时监控数据（run_monitor.py 推送）
│       ├── monitor-data.json   # 历史监控报告（备用）
│       ├── notify_config.json  # 通知配置
│       └── selection-data.json # 选品数据（备用）
│
├── .github/workflows/
│   ├── save-config.yml         # 前端保存配置时写入 user_config.json
│   └── sync_data.yml           # 手动人触发（无实际功能）
│
├── logs/                       # 日志目录
├── output/screenshots/         # 爬虫截图（广告追踪/竞品快照）
├── selectors/                  # 选品引擎（16 指标 + 4 种策略）
├── pipelines/                  # 四阶段选品流水线（S1-S4）
├── research/                   # 数据采集（卖家精灵/1688）
├── listing/                    # ASIN 详情 JSON
└── simulation/                 # 蒙特卡洛运营模拟
```

---

## 快速开始

### 前置要求

- Windows 10+，Python 3.10+
- Edge 浏览器（闫旭默认安装，已登录卖家精灵）
- 卖家精灵插件（已安装且已登录 sellersprite.com）

### 第一步：启动 Edge 调试模式

> ⚠️ **必须使用闫旭的默认 Edge 账户**（不指定 `--user-data-dir`）

```powershell
# 1. 先关掉所有 Edge 窗口
# 2. 执行：
msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
```

### 第二步：重置触发器并运行监控

```powershell
cd crossmart-monitor

# 重置 trigger 为 pending（每次抓取前必须）
python reset_and_run.py

# 或手动分步：
# 1. 重置触发器
python reset_trigger.py

# 2. 运行监控抓取
python backend/run_monitor.py
```

运行流程：
1. 检测 `trigger.json` 为 `pending` → 继续抓取
2. 依次执行关键词监控（keyword_monitor.py）→ ASIN 监控（asin_monitor.py）
3. 同步数据到 `frontend/data/rawData.json` 并推送到 GitHub
4. 将 `trigger.json` 状态置为 `done`

### 第三步：查看结果

刷新页面：https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html

---

## 监控数据内容（全维度指标）

每个 ASIN 行展示以下指标：

| 指标分类 | 具体内容 |
|---------|---------|
| **基础信息** | ASIN / 产品标题 / 品牌 / 图片 / 价格 / 评分 / 评论数 |
| **排名** | 大类 BSR / 子类 BSR |
| **变体状态** | 父子关系 / 变体异常检测 |
| **Deal 活动** | Lightning Deal / 秒杀 / Coupon |
| **优惠券** | 🎟️ 是否有 Coupon |
| **Prime 折扣** | 📦 Prime 专享折扣 |
| **徽章状态** | A+ / Best Seller / AC / New Release |
| **信息变更** | 标题变化 / 图片变化 / 五点描述变化 / 详情页变化 |
| **历史趋势** | 价格/BSR 涨跌记录 |

---

## 配置管理

### 用户配置（前端保存）

访问 monitor.html → 输入 ASIN 和关键词 → 点保存

前端通过 GitHub Actions（repository_dispatch）写入 `backend/data/user_config.json`，无需携带 Token 安全上传。

### 手动编辑配置

直接编辑 `backend/data/user_config.json`：

```json
{
  "asins": [
    { "main": "B09V7Z4TJG", "nickname": "medicube Toner Pads", "related": ["B0GCMKDSJB", "B0BPLYHDPG", "B0FJ21Z6BW"] }
  ],
  "keywords": [
    { "main": "batana oil" }
  ]
}
```

---

## 工作流程详解

### 抓取流程（本地）

```
reset_trigger.py → 写入 trigger.json {status: "pending"}
    ↓
run_monitor.py → load_trigger() 读取 GitHub trigger.json
    ↓ 检测 pending
    ├─ keyword_monitor.py batana oil → backend/data/processed/kw_batana_oil/
    ├─ asin_monitor.py B09V7Z4TJG → backend/data/processed/asin_B09V7Z4TJG/
    │   └─ _fetch_related_asin_data() → 抓取关联竞品 B0GCMKDSJB/B0BPLYHDPG/B0FJ21Z6BW
    ├─ sync_monitor_data.py → 生成 frontend/data/rawData.json
    └─ push_trigger_done() → 写入 trigger.json {status: "done"}
```

### 同步流程

`sync_monitor_data.py` 从本地快照读取数据，构建 `rawData.json`：

- 主 ASIN：`processed/asin_{ASIN}/latest.json`
- 关联竞品：每个竞品自己的 `latest.json`（`is_related_item: true`）
- 关键词 ASINs：`processed/kw_{keyword}/latest.json` 的 `top_asins`

最终 `rawData.items` 包含：主 ASIN + 关联竞品 + 关键词 ASINs，统一展示。

---

## GitHub Actions 说明

| Workflow | 触发方式 | 功能 |
|---------|---------|------|
| `save-config.yml` | `repository_dispatch`（前端保存配置） | 写入 `backend/data/user_config.json` |
| `sync_data.yml` | workflow_dispatch手动 | 空生手动（无实际功能） |

---

## 常见问题

**Q: run_monitor.py 提示"触发器状态: done，无需执行"**
→ 每次抓取前需要先重置：`python reset_trigger.py`

**Q: 为什么需要 Edge 默认 profile？**
→ 复用闫旭已登录的亚马逊和卖家精灵 Cookie，headless 模式无法加载已保存的登录态

**Q: 前端页面数据不更新**
→ 确认 `trigger.json` 状态为 `pending`，然后运行 `python backend/run_monitor.py`

**Q: 卖家精灵登录失效**
→ 在 Edge 默认 profile 中重新登录 sellersprite.com

---

## 相关文件说明

| 文件 | 说明 |
|------|------|
| `reset_trigger.py` | 重置 trigger.json 为 pending |
| `reset_and_run.py` | 重置 + 运行监控（一步到位） |
| `backend/data/user_config.json` | 用户配置的 ASINs + 关键词 |
| `backend/data/trigger.json` | 触发器状态（pending=done）|
| `frontend/data/rawData.json` | 前端展示用的实时数据 |

---

*由 yJ 管理，OpenClaw 驱动*