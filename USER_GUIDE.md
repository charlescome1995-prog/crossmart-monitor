# CrossMart Monitor — 小白使用说明

## 这是什么

一个在你电脑上运行的跨境电商监控系统，通过**你自己的 Edge 浏览器**自动访问亚马逊和卖家精灵，抓取 ASIN 排名/评价/价格和关键词市场数据，在前端页面展示。

---

## 准备工作（只需做一次）

### 1. 启动 Edge 监控浏览器
按 `Win+R`，输入：
```
msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
```
回车，Edge 会打开空白窗口。

> **注意**：抓取期间**不要关这个窗口，也不要动鼠标键盘**，让监控系统自己操作。

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

**① ASIN 列表** — 编辑 `backend/data/monitor_list.json`：
```json
[
  {
    "asin": "B09V7Z4TJG",
    "keywords": "batana oil",
    "nickname": ""
  }
]
```
> ASIN 就是亚马逊商品链接里 `dp/` 后面的那段，例如 `https://www.amazon.com/dp/B09V7Z4TJG` → ASIN = `B09V7Z4TJG`  
> `keywords` 是辅助搜索用的关键词，填商品主词就行

**② 关键词列表** — 编辑 `backend/data/keyword_list.json`：
```json
[
  {
    "keyword": "batana oil",
    "note": "",
    "group": "main"
  }
]
```
> 关键词是用来监控市场趋势的，比如你在亚马逊上搜这个词能看到哪些商品排前面

---

### 第二步：运行调度器（一键跑完 ASIN + 关键词）

```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
python scheduler.py
```

**调度器会依次执行：**
1. **Phase A — ASIN 监控**：逐个跑 `monitor_list.json` 里的 ASIN
   - 打开亚马逊搜索关键词 → 点进商品页 → 假装浏览 → 提取数据
   - 打开卖家精灵 → 查竞品 + 广告洞察
   - 对比上次快照，检测价格/评分/评论是否变化
   - 保存快照到 `backend/data/processed/asin_<ASIN>/`

2. **Phase B — 关键词监控**：逐个跑 `keyword_list.json` 里的关键词
   - 在亚马逊上搜索这个词 → 提取搜索结果数量
   - 在卖家精灵上查这个词的搜索量、相关词、竞品
   - 保存快照到 `backend/data/processed/kw_<关键词>/`

> 每个 ASIN 大约 2~3 分钟，每个关键词大约 1~2 分钟，中途会随机等待一段时间模拟真人操作，不要中断

---

### 第三步：生成本地数据文件

```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python sync_monitor_data.py
python sync_to_frontend.py
```

- `sync_monitor_data.py` → 生成 `frontend/data/rawData.json`（前端主数据）
- `sync_to_frontend.py` → 生成 `frontend/data/monitor-data.json`（含历史趋势）

---

### 第四步：打开前端页面查看

**方式一：本地直接打开**
```
C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\monitor.html
```
双击 `monitor.html` 在浏览器里打开。

**方式二：GitHub Pages（你在别的设备上也能看）**
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
│   │       ├── asin_B09V7Z4TJG/   ← ASIN 快照
│   │       └── kw_batana_oil/     ← 关键词快照
│   ├── browser/
│   │   ├── asin_monitor.py        ← ASIN 抓取逻辑
│   │   ├── keyword_monitor.py     ← 关键词抓取逻辑
│   │   └── cdp_bridge.py         ← Edge 浏览器连接
│   ├── run_monitor.py            ← 单独跑 ASIN 监控
│   ├── scheduler.py              ← 调度器（ASIN + 关键词依次跑）
│   ├── sync_monitor_data.py      ← 快照 → rawData.json
│   └── sync_to_frontend.py      ← 快照 → monitor-data.json
├── frontend/
│   ├── monitor.html              ← 前端页面
│   └── data/
│       └── rawData.json          ← 前端读取的数据
└── logs/                         ← 日志（自动生成）
```

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

**查看某个 ASIN 的状态：**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python browser/asin_monitor.py B09V7Z4TJG --status
```

**重新抓取单个 ASIN：**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python run_monitor.py B09V7Z4TJG
```

---

## 常见问题

**Q：抓取中途失败了怎么办？**
A：看 PowerShell 里的错误信息，常见原因：
- Edge 窗口被关了 → 重新启动 Edge（第一步）
- 网络断了 → 检查网络或代理
- 卖家精灵登录态失效 → 在 Edge 里重新登录卖家精灵

**Q：可以同时操作电脑吗？**
A：抓取期间**不要操作 Edge 窗口**，其他浏览器/软件正常使用不受影响。

**Q：数据存在哪里？怎么清理？**
A：本地 `backend/data/processed/` 目录下，每个 ASIN/关键词一个文件夹。要清理，重新跑 `scheduler.py` 之前删掉对应文件夹即可。

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

> 注意：`backend/data/processed/` 和 `backend/data/monitor_list.json` 等配置文件已被 `.gitignore` 排除，不会推送。如果需要同步配置，通过飞书告诉我，或者用 GitHub Actions 的 `repository_dispatch` 触发。

---

有问题就发截图给我，我来排查。