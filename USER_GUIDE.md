# CrossMart Monitor — 用户手册

一个在你电脑上运行的跨境电商监控系统，通过**你自己的 Edge 浏览器**自动访问亚马逊和卖家精灵，抓取 ASIN 监控数据和关键词市场数据。

---

## 第一章：系统架构与数据存储

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      你自己的电脑                           │
│                                                             │
│  ┌─────────────┐    ┌──────────────────────────────────┐    │
│  │ Edge 浏览器 │◄───│  CDP WebSocket (端口 9225)       │    │
│  │ 闫旭的默认   │    │  cdp_bridge.py 控制浏览器        │    │
│  │ 登录态      │    └──────────────────────────────────┘    │
│  └─────────────┘                    ▲                      │
│                                     │                       │
│  ┌─────────────────────────────────▼──────────────────┐   │
│  │              asin_monitor.py / keyword_monitor.py   │   │
│  │  导航搜索 → 等待插件加载 → 提取 DOM → 保存快照       │   │
│  └─────────────────────────────────▲──────────────────┘   │
│                                    │                       │
│  ┌─────────────────────────────────▼──────────────────┐   │
│  │              sprite_bridge.py                       │   │
│  │  卖家精灵插件交互（竞品/关键词/广告）              │   │
│  └─────────────────────────────────▲──────────────────┘   │
│                                    │                       │
│  ┌─────────────────────────────────▼──────────────────┐   │
│  │           snapshot_storage.py                      │   │
│  │  保存到 backend/data/processed/asin_XXX/           │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
           │
           ▼ push
    ┌──────────────┐
    │  GitHub      │
    │  main 分支   │
    └──────────────┘
           │
           ▼ GitHub Pages
    ┌──────────────┐
    │ monitor.html │  ← 公开访问
    │ (前端页面)    │
    └──────────────┘
```

### 1.2 数据存储结构

**前端数据（展示用）：**
```
frontend/
└── data/
    └── rawData.json        ← 前端唯一读取的数据文件
        items[]             — ASIN 监控数据（含价格/评分/BSR/变体/历史）
        keywords[]          — 关键词搜索结果（Top5 ASIN）
```

**后端数据（原始）：**
```
backend/
├── data/
│   ├── user_config.json        ← 【你改这个】ASIN 列表和关键词列表（前端页面直接编辑保存）
│   ├── trigger.json             ← 触发状态（pending=done）
│   └── processed/
│       └── asin_B09V7Z4TJG/
│           ├── latest.json           ← 最新快照
│           ├── snapshot_*.json        ← 历史快照
│           └── _meta.json            ← 首次固定写入的关联ASIN
```

**数据流向：**
```
user_config.json（ASIN + 关键词配置）
        │
        ▼ Phase A / Phase B 抓取
snapshot_storage.py → processed/asin_XXX/snapshot_*.json
        │
        ▼ sync_monitor_data.py
frontend/data/rawData.json
        │
        ▼ git push → GitHub main
GitHub Pages → monitor.html 读取
```

---

## 第二章：用户操作入口与前端页面

### 2.1 配置监控对象

在 GitHub Pages 前端页面上直接配置：
https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html

输入 ASIN 和关键词后点「保存配置」，数据自动写入 `backend/data/user_config.json`（通过 GitHub Actions 安全上传，无需手动编辑）。

### 2.2 运行监控

**一键运行（ASIN + 关键词）：**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
python reset_and_run.py
```

**单独运行 ASIN：**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python run_monitor.py B09V7Z4TJG
```

**查看运行状态：**
```
python browser/asin_monitor.py B09V7Z4TJG --status
```

### 2.3 查看数据

**方式一：GitHub Pages（推荐）**
```
https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html
```

**方式二：本地直接打开**
```
C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\monitor.html
```

### 2.4 定时自动运行（可选）

运行一次即可创建 Windows 定时任务（每天 08:00 和 17:30 自动运行）：
```
python setup_scheduled_tasks.py
```

### 2.5 前端 monitor.html 主要函数

| 函数 | 作用 |
|------|------|
| `loadAllData()` | 启动时加载 rawData.json + user_config.json + trigger.json |
| `renderAsinCard(item)` | 渲染单个 ASIN 卡片（价格↑↓/评分/BSR/变体状态） |
| `renderKeywordSection(kw)` | 渲染关键词 Top5 ASIN 列表 |
| `checkChanges()` | 每次加载后对比历史，标记变化（颜色提示） |
| `pollTrigger()` | 每 30s 轮询 trigger.json，检测是否需要刷新 |

---

## 第三章：自动化抓取与浏览器控制

### 3.1 准备工作

**启动 Edge 监控浏览器：**
```
msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
```

> **注意**：抓取期间**不要关这个窗口，也不要操作鼠标键盘**。

### 3.2 Phase A — ASIN 监控流程

```
① 逛亚马逊首页（随机等待，模拟人类行为）
② 搜索关键词，找到目标 ASIN，点进商品页
③ 等待插件 DOM 加载（最长30秒轮询 #productTitle / #dpContainer）
④ 再等 1-3 秒渲染缓冲
⑤ 提取：标题 / 价格 / 评分 / 评论 / BSR / 品牌
⑥ 卖家精灵竞品分析（首次固定写入 _meta.json，之后不再更新）
⑦ 抓取关联 ASIN 的实时数据
⑧ 保存快照 → backend/data/processed/asin_XXX/
```

**每个 ASIN 约 2~3 分钟。**

### 3.3 Phase B — 关键词监控流程

```
① 亚马逊搜索关键词（人类行为模拟）
② 等待卖家精灵插件 DOM 标记出现（最长15秒轮询）
③ 提取：自然位Top1 + 广告位Top1 + 新品自然Top1 + 新品广告Top1 + 自然顺位补充
④ 取满5个不同 ASIN 固定记录
⑤ 保存快照
```

**每个关键词约 1~2 分钟。**

### 3.4 关键设计：关联ASIN机制

- 首次跑某个 ASIN 监控时，从卖家精灵解析 5 个关联竞品 ASIN，写入 `_meta.json`
- **之后每次跑不再更新**，保持固定
- 每次运行时重新抓取这 5 个 ASIN 的实时数据

### 3.5 卖家精灵插件交互（sprite_bridge.py）

| 方法 | 作用 |
|------|------|
| `lookup_competitor(asin)` | 竞品反查 → 关联 ASIN 列表 |
| `lookup_keywords(asin)` | 关键词反查 → 流量词 |
| `lookup_ads(asin)` | 广告洞察 → 广告投放数据 |
| `full_asin_check(asin)` | 综合查询（竞品+关键词+广告） |

> 注意：以上 3 个字段数据已抓取但**前端暂未展示**，可在 rawData.json 中看到。

### 3.6 常见问题

**Q：Edge 窗口会自动操作，我能用电脑吗？**
A：建议抓取期间不要操作那个 Edge 窗口，其他软件正常用。

**Q：抓取失败了怎么办？**
A：检查 Edge 是否在 9225 端口运行，网络/代理是否正常。错误信息直接打印在 PowerShell 里。

**Q：怎么清理旧数据？**
A：删掉 `backend/data/processed/asin_<ASIN>/` 下的快照文件即可。要完全重新开始就删整个 `processed/` 目录后重新跑。

**Q：GitHub Pages 上的数据和本地不一样？**
A：运行 `reset_and_run.py` 后，数据会自动推送到 GitHub。或者本地手动：
```bash
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
git add .
git commit -m "更新数据"
git push
```
注意：`backend/data/processed/`、`backend/data/monitor_list.json`、`backend/data/keyword_list.json` 已被 `.gitignore` 排除，不会推送。

---

有问题发截图给我，我来排查。