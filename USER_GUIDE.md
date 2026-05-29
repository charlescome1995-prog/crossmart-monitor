# CrossMart Monitor — 小白使用说明

## 这是什么

一个运行在你电脑上的亚马逊 ASIN 监控系统。每次抓取会在**你自己的 Edge 浏览器**里真实访问亚马逊和卖家精灵，把数据存到本地，前端页面展示结果。

---

## 准备工作（只需做一次）

### 1. 确认 Edge 在跑
按 `Win+R`，输入：
```
msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
```
回车，Edge 会打开一个空白窗口。

> **注意**：不要关这个 Edge 窗口，监控系统会在这上面操作。

### 2. 确认 Python 环境
打开 PowerShell，运行：
```
python --version
```
如果没有，安装 Python 3（[官网](https://www.python.org/downloads/)，记得勾选 "Add Python to PATH"）。

### 3. 安装依赖
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
pip install websocket-client requests
```

---

## 完整跑一遍（手动）

### 第一步：配置要监控的 ASIN

编辑 `backend/data/monitor_list.json`，例如：
```json
[
  {
    "asin": "B09V7Z4TJG",
    "keywords": "batana oil",
    "nickname": ""
  }
]
```

编辑 `backend/data/keyword_list.json`，例如：
```json
[
  {
    "keyword": "batana oil",
    "note": "",
    "group": "main"
  }
]
```

### 第二步：运行监控抓取

在 PowerShell 里运行：
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python run_monitor.py
```
或直接运行调度器：
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
python scheduler.py
```

> 过程中 Edge 会自动跳转到亚马逊搜索页面，请**不要操作键盘鼠标**，让它自己跑。抓一个 ASIN 大约 2~3 分钟。

### 第三步：生成本地数据文件

```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python sync_monitor_data.py
```
这会把快照整理成 `frontend/data/rawData.json`，前端页面直接读这个文件。

### 第四步：打开前端页面查看

直接在浏览器打开：
```
C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\monitor.html
```

或者如果你已经用 GitHub Pages 部署了，访问：
```
https://charlescome1995-prog.github.io/crossmart-monitor/frontend/monitor.html
```

---

## 文件结构

```
crossmart-monitor/
├── backend/
│   ├── data/
│   │   ├── monitor_list.json      ← 你在这里填 ASIN
│   │   ├── keyword_list.json     ← 在这里填关键词
│   │   └── processed/            ← 抓取结果（自动生成）
│   │       └── asin_B09V7Z4TJG/
│   ├── browser/                  ← 浏览器自动化脚本
│   │   ├── asin_monitor.py       ← ASIN 抓取逻辑
│   │   ├── keyword_monitor.py     ← 关键词抓取逻辑
│   │   └── cdp_bridge.py         ← 浏览器连接
│   ├── run_monitor.py            ← 独立入口
│   ├── scheduler.py              ← 调度器（ASIN + 关键词依次跑）
│   ├── sync_monitor_data.py      ← 快照 → rawData.json
│   └── sync_to_frontend.py      ← 快照 → monitor-data.json（含历史）
├── frontend/
│   ├── monitor.html              ← 前端页面
│   └── data/
│       └── rawData.json          ← 前端读取的数据
└── logs/                         ← 日志（自动生成）
```

---

## 常见问题

**Q：Edge 窗口会自动操作，我能用电脑吗？**
A：建议在抓取期间不要操作那个 Edge 窗口，其他浏览器正常使用不受影响。

**Q：抓取失败了怎么办？**
A：检查 Edge 是否还在运行（9225 端口），检查网络是否有代理。错误信息会直接打印在 PowerShell 里。

**Q：如何只抓某个 ASIN，不跑关键词？**
```
python scheduler.py --asin-only
```

**Q：如何查看状态？**
```
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend
python browser/asin_monitor.py B09V7Z4TJG --status
```

**Q：数据存在哪里？**
A：本地 `backend/data/processed/asin_<ASIN>/`，每个 ASIN 一个文件夹，里面有快照文件。

---

## 推送更新到 GitHub

如果你修改了代码，需要推送到 GitHub：

```bash
cd C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
git add .
git commit -m "更新说明"
git push
```

> 快照数据（`backend/data/processed/`）不会推送，因为 `.gitignore` 已经排除了。

---

有问题就发截图给我，我来帮你排查。