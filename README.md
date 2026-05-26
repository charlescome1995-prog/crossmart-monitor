# CrossMart Monitor — 亚马逊运营全链路工具箱

> 让选品、监控、模拟、运营分析全流程自动化，专注决策本身。

**🌐 在线预览**: https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html
**📦 GitHub 仓库**: https://github.com/charlescome1995-prog/crossmart-monitor

---

## 🎯 这个项目做什么？

简单说：**帮你监控亚马逊 ASIN 和关键词数据，筛选潜力产品，模拟运营收益。**

具体来说，它能帮你：

- 📦 **ASIN 监控** — 自动抓取 ASIN 的价格、评分、评论数、BSR 排名变化
- 🔑 **关键词排名** — 通过卖家精灵追踪关键词搜索结果排名
- 🎯 **智能选品** — 基于 16 个核心指标 + 4 种策略（蓝海/红海/差异化/跟随）筛选潜力产品
- 📊 **运营模拟** — 蒙特卡洛模拟不同推广策略下的收益区间
- 📈 **定时调度** — 每天早/中/晚自动跑，无需人工干预
- 📋 **Excel 报告** — 自动生成监控报告

---

## 🗂️ 云端与本地文件对应关系

> 新手必读！理解这个关系很重要。

| GitHub 云端（main 分支） | 本地开发目录 | 说明 |
|------|------|------|
| `frontend/monitor.html` | `frontend/monitor.html` | 监控展示页面，GitHub Pages 直接托管 |
| `backend/` | `backend/` | API Server + 爬虫脚本，**不参与 Pages 部署**，本地运行 |
| `.github/workflows/save-config.yml` | `.github/workflows/save-config.yml` | GitHub Actions workflow，前端保存配置时触发 |
| — | `browser/` | **不在 GitHub 仓库里**，仅本地，用于 CDP 浏览器自动化 |
| — | `data/processed/` | 快照数据，`.gitignore` 忽略，不上传 |
| — | `data/browser_profiles/` | Edge 用户数据，`.gitignore` 忽略，不上传 |

**一句话概括**：`main` 分支里的代码部署到 GitHub Pages（前端），本地目录里的代码跑在你自己的电脑上（爬虫/调度）。

---

## 🚀 新手快速上手

### 前置要求

- Windows 10+
- Python 3.10+
- Edge 浏览器（闫旭默认安装的那个）
- 卖家精灵插件（已登录）

### 第一步：安装依赖

```powershell
cd crossmart-monitor
pip install -r requirements.txt
```

### 第二步：启动 Edge 调试模式

> ⚠️ **必须用闫旭的默认 Edge 账户**，不能指定 `--user-data-dir`。

```powershell
# 1. 先关掉所有 Edge 窗口
# 2. 在命令行执行：
msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
```

### 第三步：配置要监控的 ASIN

编辑 `data/monitor_list.json`：

```json
[
  {"asin": "B0DFLTJQ3N", "nickname": "须后膏"},
  {"asin": "B0DFL5BK8H", "nickname": "折叠足浴盆"}
]
```

最多 5 个。

### 第四步：手动跑一次监控

```powershell
python browser/asin_monitor.py B0DFLTJQ3N
```

成功的话你应该能在终端看到商品数据卡片（价格/评分/BSR/评论数）。

### 第五步：启动本地面板（可选）

```powershell
python server.py
# 然后浏览器打开 http://localhost:5005/monitor
```

### 第六步：设置定时调度（可选）

Windows 任务计划程序，添加任务每天定时运行：

```powershell
python scheduler.py --force
```

---

## 📁 目录结构详解

```
crossmart-monitor/
│
├── 📂 browser/          # 浏览器自动化（Edge CDP 控制）
│   ├── asin_monitor.py       # ⭐ ASIN 监控主脚本
│   ├── keyword_monitor.py    # 关键词排名监控
│   ├── amazon_browser.py    # 亚马逊前台操作
│   ├── sprite_bridge.py     # 卖家精灵 SPA 操作
│   ├── cdp_bridge.py       # CDP 协议底层桥接
│   ├── human_timer.py      # 人类行为模拟（反爬）
│   └── snapshot_storage.py  # 快照存取
│
├── 📂 data/             # 数据目录
│   ├── monitor_list.json   # 监控的 ASIN 列表
│   ├── keyword_list.json   # 监控的关键词列表
│   └── monitor_report.xlsx # Excel 报告
│
├── 📂 backend/          # 后端（本地运行，不上 GitHub Pages）
│   ├── api_server.py       # API Server（端口 8765）
│   ├── run_monitor.py      # 监控抓取入口
│   └── data/user_config.json  # 用户配置（GitHub Actions 写入）
│
├── 📂 frontend/         # 前端（部署到 GitHub Pages）
│   └── monitor.html      # 监控展示页面
│
├── 📂 selectors/         # 选品引擎
│   └── product_selector.py  # 16指标选品 + 4种策略
│
├── 📂 pipelines/        # 四阶段选品流水线
│   ├── s1_keyword_layer.py   # S1: 关键词评分
│   ├── s2_asin_layer.py      # S2: ASIN 选品
│   ├── s3_operation_plan.py  # S3: 运营模拟
│   └── s4_final_recommendation.py  # S4: 最终推荐
│
├── 📂 research/         # 数据采集
│   ├── sellersprite_crawler.py  # 卖家精灵爬虫
│   └── supply_chain.py        # 1688 供应链调研
│
├── 📂 listing/           # ASIN 详情 JSON
│
├── 📂 simulation/       # 蒙特卡洛模拟引擎
│
├── config.py             # 全局配置（选品指标/策略/FBA利润模型/AI API）
├── ai_client.py          # 统一 AI 客户端（DeepSeek/Kimi/Gemini）
├── scheduler.py          # ⏰ 调度器（每天三窗口定时运行）
├── server.py             # Flask 本地面板（端口 5005）
├── data_reporter.py      # Excel 报告生成
└── requirements.txt     # Python 依赖
```

---

## ⚙️ 核心模块说明

### 🕐 调度器 — scheduler.py

为什么要用调度器？因为亚马逊和卖家精灵都有反爬限制。

**解决方案：模拟人类行为**

- 每天三个随机时间窗口（早 8-10 点、中 13-15 点、晚 17:30-19:30）
- 时间窗口每天基于日期 hash 变化，避免固定规律
- ASIN 之间随机间隔 15-50 秒，模拟人工浏览
- 每次启动先逛首页/类目/搜索页再正经干活

```
启动 → 判断当前时间是否在窗口内
  ├── 否 → 等待到下一个窗口
  └── 是 → Phase A（ASIN监控）→ Phase B（关键词监控）→ Phase C（生成报告）
```

### 🎯 选品引擎 — product_selector.py

**16 个核心指标**（来自亚马逊爆款选品思维）：

1. 价格 $10-50（冲动购买甜蜜点）
2. 重量 < 2-3 磅（利润空间）
3. 大分类排名 < 5000
4. 无大品牌垄断
5. 坚固耐用
6. 首页 2-3 个竞品 Review < 50
7. 毛利率 > 30%
8. Listing 有优化空间
9. 前三关键字月搜 > 10 万
10. 中国可找到供货商
11. 非季节性尤佳
12. eBay 也有售
13. 可拓展品牌
14. 可升级改良
15. 需定期购买
16. 多样化关键词

**4 种策略**：

| 策略 | 特点 | 适合场景 |
|------|------|---------|
| 🟢 蓝海策略 | 小众低竞争高利润 | 新手切入，低竞争赛道 |
| 🔴 红海策略 | 成熟大市场高销量 | 有资源，搏大体量 |
| 🟡 差异化策略 | 有改进空间的细分市场 | 排名上升中，产品有痛点可优化 |
| ⚪ 跟随策略 | 已验证市场稳定收益 | 保守打法，跟成熟爆款 |

### 🌐 浏览器自动化 — browser/

使用闫旭的 **Edge 默认 profile**（`--remote-debugging-port=9225`，不指定 `--user-data-dir`），复用：
- 收藏夹
- 亚马逊登录态
- 卖家精灵登录态

**为什么不用 Selenium 的 headless 模式？**
因为需要用到闫旭已登录的卖家精灵会话，headless 无法加载已保存的登录 Cookie。

---

## 🔧 配置说明

### 全局配置 — config.py

```python
# 选品规则示例
SELECTION_RULES = {
    "min_price": 10,           # 价格下限 $10
    "max_price": 50,           # 价格上限 $50
    "min_review_count": 0,     # 最低评分数
    "min_rating": 4.0,         # 最低评分
    "max_review_count": 10000, # 避免饱和市场
}

# 4种策略配置
STRATEGY_CONFIG = {
    "strategy1_blue_ocean": { "quota": 30, ... },
    "strategy2_red_ocean": { "quota": 30, ... },
    ...
}
```

### AI API 配置

支持 DeepSeek / Kimi / Gemini，可在 `config.py` 中切换默认提供商：

```python
AI_CONFIG = {
    "default_provider": "deepseek",  # 切换这里
    "deepseek": { "api_key": "...", "enabled": True },
    "kimi": { "api_key": "...", "enabled": False },
}
```

---

## ❓ 常见问题

**Q: 为什么 monitor.html 打开是空白的？**
→ 确保 Edge 已登录卖家精灵，且 sellersprite.com 可以正常访问。

**Q: 监控数据保存在哪里？**
→ `data/processed/asin_{ASIN}/snapshot_{日期}.json`，每个 ASIN 一个文件夹。

**Q: GitHub Actions Secret 是什么？**
→ `GH_TOKEN`，用于 workflow 写入 `backend/data/user_config.json`。前端不携带 token，防止 GitHub GH013 检测拒绝 push。

**Q: 想新增一个 ASIN 怎么操作？**
→ 编辑 `data/monitor_list.json`，或者访问本地面板 http://localhost:5005/monitor 添加。

**Q: 调度器不跑怎么办？**
→ 检查是否在时间窗口内：`python scheduler.py --show-plan`
→ 强制运行一次：`python scheduler.py --force`

---

## 📊 工作流图

```
[本地]                     [GitHub]              [浏览器]
 ┌──────────────────┐      ┌──────────────┐      ┌──────────────┐
 │  monitor_list.json│      │              │      │              │
 │  keyword_list.json│──push──▶│ GitHub Pages │      │              │
 └──────────┬─────────┘      └──────────────┘      └──────┬───────┘
            │                        ▲                     │
            │schedule               │deploy               │
            ▼                        │                     ▼
 ┌──────────────────┐      ┌──────────────┐      ┌──────────────┐
 │   scheduler.py   │      │  main 分支   │      │  Edge CDP    │
 │  (定时三窗口运行) │      └──────────────┘      │ (闫旭默认配置)│
 └──────────┬─────────┘                             └──────┬───────┘
            │                                             │
            │ ASIN监控            读取                    ▼
            ▼                                    ┌──────────────────┐
 ┌──────────────────┐                          │ 亚马逊前台      │
 │ asin_monitor.py  │───────────────────────────│ sellersprite.com │
 └──────────┬─────────┘                          └──────────────────┘
            │
            │快照保存
            ▼
 ┌──────────────────┐
 │ data/processed/   │
 │ asin_XXXXX/      │
 │ snapshot_*.json   │
 └──────────────────┘
```

---

*由 yJ 管理，OpenClaw 驱动*