# CrossMart Monitor — 亚马逊运营全链路工具箱

> 覆盖选品、关键词调研、竞品分析、Listing 生成、运营模拟、卖家精灵自动化全链路。

**GitHub 仓库**: https://github.com/charlescome1995-prog/crossmart-monitor
**GitHub Pages**: https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html

---

## 与 GitHub / GitHub Pages 的对应关系

| 层次 | 说明 |
|------|------|
| **main 分支** | 仓库主分支，所有代码的最终来源 |
| **GitHub Pages** | 自动从 `main` 分支部署，访问地址即上方 GitHub Pages URL |
| **前端 monitor.html** | 位于 `frontend/monitor.html`，构建后由 Pages 托管 |
| **backend** | 位于 `backend/`，包含 API Server（本地端口 8765）和爬虫脚本，**不参与 Pages 部署**，仅供本地运行 |
| **.github/workflows/** | GitHub Actions 工作流，如 `save-config.yml`（repository_dispatch 触发） |
| **GitHub Actions Secret** | `GH_TOKEN` — 用于 workflow 写入 `backend/data/user_config.json` |

> ⚠️ **前端代码禁止携带 Token**。GitHub 会检测前端 JS 中的 Token（GH013 push protection）并拒绝 push。所有涉及写操作的逻辑均通过 GitHub Actions workflow 完成。

---

## 目录结构

```
crossmart-monitor/
├── config.py                  # 全局配置（16个选品指标、4种策略、FBA利润模型、AI API）
├── ai_client.py               # 统一AI调用客户端（DeepSeek/Kimi/Gemini）
├── requirements.txt           # Python依赖
├── .gitignore                 # Git忽略规则
│
├── data/                      # 数据目录
│   ├── monitor_list.json      # 监控的ASIN列表（最多5个）
│   ├── keyword_list.json      # 监控的关键词列表
│   ├── keyword_results.json   # 关键词查询结果缓存
│   ├── bos_config.json         # 百度BOS配置
│   └── monitor_report.xlsx    # Excel监控报告输出
│
├── browser/                   # 浏览器自动化（Edge + 卖家精灵CDP操作）
│   ├── cdp_bridge.py          # CDP协议底层桥接
│   ├── amazon_browser.py      # 亚马逊前台操作（逛首页/类目/搜ASIN/看评价）
│   ├── sprite_bridge.py        # 卖家精灵SPA导航操作
│   ├── asin_monitor.py        # ⭐ ASIN监控主脚本（Phase A亚马逊 → Phase B卖家精灵 → Phase C对比保存）
│   ├── keyword_monitor.py     # 关键词排名监控
│   ├── frontend_link.py       # 卖家精灵前台链接导航
│   ├── human_timer.py        # 人类行为模拟（随机等待/滚动等反爬设计）
│   ├── snapshot_storage.py   # ASIN快照存取（data/processed/asin_{ASIN}/snapshot_*.json）
│   └── init_browsers.py      # 浏览器初始化启动
│
├── selectors/
│   └── product_selector.py   # 核心选品筛选引擎（16指标 + 4策略 + 5W1H场景还原 + AI分析）
│
├── pipelines/                # 四阶段自动化选品流水线
│   ├── s1_keyword_layer.py    # S1: 关键词竞争力评分 → S/A/B/C分级
│   ├── s2_asin_layer.py       # S2: ASIN交叉选品
│   ├── s3_operation_plan.py   # S3: 蒙特卡洛运营模拟
│   ├── s4_final_recommendation.py  # S4: 最终推荐方案
│   ├── beauty_pipeline.py     # 美妆个护专项选品
│   └── final_output.py        # 最终输出整合
│
├── research/                  # 数据采集/调研模块
│   ├── sellersprite_crawler.py      # 卖家精灵Selenium采集
│   ├── amazon_crawler_v4.py         # 亚马逊直接爬虫
│   ├── keyword_asin_selector.py     # 关键词×ASIN筛选器
│   └── supply_chain.py              # 1688供应链调研
│
├── listing/                   # Listing详情数据（JSON格式，含Keepa历史）
│
├── simulation/               # 蒙特卡洛运营模拟引擎
│
├── templates/               # Listing模板文件
│
├── tests/                   # 单元测试
│
├── deploy/                  # 服务器部署脚本（VNC防火墙检查、安全组规则等）
│
├── frontend/                 # 前端页面（GitHub Pages 托管）
│   └── monitor.html         # 监控展示页面
│
├── backend/                  # 后端（不参与GitHub Pages部署，仅本地运行）
│   ├── api_server.py        # API Server（端口8765，供本地配置页面测试）
│   ├── run_monitor.py       # 监控抓取入口
│   ├── data/
│   │   └── user_config.json # 用户配置（由GitHub Actions workflow写入）
│   └── sync_groups.py       # 生成monitor-data.json
│
├── server.py                # Flask监控服务器（本地端口5005）
├── scheduler.py             # ⏰ 调度器：每天早/中/晚三窗口自动运行，含随机间隔反爬
├── notifier.py              # 通知模块（钉钉/邮件等）
├── data_reporter.py         # Excel监控报告生成
├── bos_sync.py              # 百度BOS对象存储同步
├── data_sync.py             # 数据同步
└── SKILL.md                 # AgentSkill说明文档
```

---

## 核心入口速查

| 任务 | 命令/文件 |
|------|-----------|
| ASIN监控（手动） | `python browser/asin_monitor.py B0XXXXXXX` |
| 定时调度 | `python scheduler.py` |
| 选品筛选 | `python selectors/product_selector.py` |
| 本地监控面板 | `python server.py` → 访问 http://localhost:5005/monitor |
| 本地API Server | `python backend/api_server.py`（端口8765） |
| 保存配置到GitHub | 点击前端「保存」→ repository_dispatch → GitHub Actions写入 |

---

## 核心概念

### 调度器（scheduler.py）
每天三个随机时间窗口（早/中/晚）自动运行：
- 读取 `monitor_list.json` → 逐个ASIN查亚马逊详情页
- 读取 `keyword_list.json` → 逐个查卖家精灵关键词排名
- ASIN之间随机间隔15-50秒（模拟人工切换浏览注意力）
- 时间窗口每天基于日期hash随机化，避免固定规律被检测

### 选品引擎（selectors/product_selector.py）
基于 **16个核心选品指标** + **4种策略**：
- 🟢 **蓝海策略**：小众低竞争高利润
- 🔴 **红海策略**：成熟大市场高销量
- 🟡 **差异化策略**：有改进空间的细分市场
- ⚪ **跟随策略**：已验证市场稳定收益

### 浏览器自动化（browser/）
使用 **闫旭默认Edge**（`--remote-debugging-port=9225`，不指定 `--user-data-dir`），复用系统profile（收藏夹/登录态/卖家精灵缓存）。

---

## 配置

所有全局配置集中在 `config.py`：
- 16个选品指标阈值
- 4种选品策略参数
- FBA利润计算模型（基于亚马逊官方2025-2026费用表）
- AI API配置（DeepSeek/Kimi/Gemini）

---

*由 yJ 管理，OpenClaw 驱动*