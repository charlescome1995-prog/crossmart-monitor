# CrossMart Monitor — 小白使用说明

## 这是什么

一个在你电脑上运行的跨境电商监控系统。通过**你自己的 Edge 浏览器**自动访问亚马逊和卖家精灵，抓取：
- ASIN 监控：价格 / 评分 / 评论 / BSR / 变体 / 历史趋势
- 关键词市场：自然位Top1 + 广告位Top1 + 新品自然Top1 + 新品广告Top1 + 自然顺位补充（共5个ASIN）
- ASIN 关联ASIN：每个监控ASIN下方固定5个关联竞品ASIN

---

## 准备工作（只需做一次）

### 1. 启动 Edge 监控浏览器
按 `Win+R`，输入：
```
msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
```
回车，Edge 会打开空白窗口。

> **注意**：抓取期间**不要关这个窗口，也不要操作鼠标键盘**，让监控系统自己跑。

### 2. 确认 Python 版本
打开 PowerShell，运行：
```
python --version
```
如果没有或版本低于 3.8，去 [python.org](https://www.python.org/downloads/) 安装。

### 3. 安装依赖
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
pip install websocket-client requests
```

---

## 完整跑一遍（手动）

### 第一步：配置要监控的内容

**ASIN 列表** → `backend/data/monitor_list.json`：
```json
[
  {
    "asin": "B09V7Z4TJG",
    "keywords": "batana oil",
    "nickname": ""
  }
]
```

**关键词列表** → `backend/data/keyword_list.json`：
```json
[
  {
    "keyword": "batana oil",
    "note": "",
    "group": "main"
  }
]
```

### 第二步：运行调度器（一键跑完 ASIN + 关键词）

```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
python scheduler.py
```

**调度器流程：**
1. **Phase A — ASIN 监控**：逐个跑 monitor_list.json 里的 ASIN
   - 逛亚马逊首页（随机）
   - 搜索关键词，找目标 ASIN，点进商品页
   - 提取：标题 / 价格 / 评分 / 评论 / BSR / 品牌
   - 卖家精灵竞品分析 → **首次写入 _meta.json（5个关联ASIN固定不更新）**
   - 抓关联 ASIN 实时数据（亚马逊前台）
   - 保存快照

2. **Phase B — 关键词监控**：逐个跑 keyword_list.json 里的关键词
   - 亚马逊搜索关键词（人类行为模拟）
   - 从卖家精灵插件 DOM 提取：自然位Top1 / 广告位Top1 / 新品自然Top1 / 新品广告Top1 / 自然顺位补充
   - 取满5个不同 ASIN 固定记录（不更新）
   - 保存快照

> 每个 ASIN 约 2~3 分钟，每个关键词约 1~2 分钟。中途随机等待，不要中断。

### 第三步：生成本地数据文件

```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python sync_monitor_data.py
python sync_to_frontend.py
```

- `sync_monitor_data.py` → `frontend/data/rawData.json`（前端主数据，含关联ASIN）
- `sync_to_frontend.py` → `frontend/data/monitor-data.json`（含历史趋势）

### 第四步：打开前端页面查看

**方式一：本地直接打开**
```
C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\monitor.html
```
双击在浏览器里打开。

**方式二：GitHub Pages**
```
https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html
```

---

## 文件结构说明

```
crossmart-monitor/
├── backend/
│   ├── data/
│   │   ├── monitor_list.json      ← 【你改这个】ASIN 列表
│   │   ├── keyword_list.json     ← 【你改这个】关键词列表
│   │   └── processed/            ← 抓取结果（自动生成）
│   │       └── asin_B09V7Z4TJG/
│   │           ├── latest.json        ← 最新快照
│   │           ├── snapshot_*.json    ← 历史快照
│   │           └── _meta.json        ← 【首次固定】关联ASIN列表
│   └── browser/
│       ├── asin_monitor.py        ← ASIN 抓取逻辑
│       ├── keyword_monitor.py     ← 关键词抓取逻辑
│       └── cdp_bridge.py         ← Edge 浏览器连接
├── frontend/
│   ├── monitor.html              ← 前端页面
│   └── data/
│       └── rawData.json          ← 前端读取的数据
└── USER_GUIDE.md                 ← 本说明
```

---

## 关键设计说明

### 关联ASIN机制（_meta.json）
- 首次跑某个 ASIN 监控时，从卖家精灵解析5个关联竞品ASIN，写入 `_meta.json`
- **之后每次跑不再更新**，保持固定
- 每次跑时重新抓这5个 ASIN 的亚马逊实时数据，写入快照

### 关键词Top5 ASIN
- 首次从亚马逊搜索结果 + 卖家精灵插件标记提取5个 ASIN，固定写入快照
- **不翻页**，凑不够就空着，不影响主流程

### 数据不更新怎么办？
检查 `backend/data/processed/` 下有没有对应 ASIN 的快照文件。如果没有，说明抓取失败了，看 PowerShell 错误信息。

---

## 常见用法

**只跑 ASIN，不跑关键词：**
```
python scheduler.py --asin-only
```

**只跑关键词，不跑 ASIN：**
```
python scheduler.py --keyword-only
```

**只跑单个 ASIN：**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python run_monitor.py B09V7Z4TJG
```

**查看某个 ASIN 的状态：**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python browser/asin_monitor.py B09V7Z4TJG --status
```

---

## 常见问题

**Q：Edge 窗口会自动操作，我能用电脑吗？**
A：建议抓取期间不要操作那个 Edge 窗口，其他软件正常用。

**Q：抓取失败了怎么办？**
A：检查 Edge 是否在 9225 端口运行，网络/代理是否正常。错误信息直接打印在 PowerShell 里。

**Q：怎么清理旧数据？**
A：删掉 `backend/data/processed/asin_<ASIN>/` 下的快照文件即可。要完全重新开始就删整个 `processed/` 目录后重新跑。

**Q：GitHub Pages 上的数据和本地不一样？**
A：本地 `frontend/data/rawData.json` 需要手动推送到 GitHub，或者等 GitHub Actions 自动部署。

---

## 推送到 GitHub

```bash
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
git add .
git commit -m "更新数据"
git push
```

> 注意：`backend/data/processed/`、`backend/data/monitor_list.json`、`backend/data/keyword_list.json` 已被 `.gitignore` 排除，不会推送。

---

有问题发截图给我，我来排查。