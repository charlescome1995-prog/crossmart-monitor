# CrossMart Monitor 服务器管理手册

## 一、环境要求

- Windows 系统（已验证）
- Python 3.10+
- Edge 浏览器（系统默认安装即可）
- 卖家精灵插件（Edge 浏览器已登录卖家精灵账户）
- 亚马逊账户（Edge 默认 profile 已登录）

---

## 二、本地目录结构

```
crossmart-monitor/
├── backend/
│   ├── data/
│   │   ├── processed/      # 抓取数据（asin_* 和 kw_* 子目录）
│   │   ├── user_config.json   # 用户配置（asins + keywords）
│   │   ├── trigger.json       # 触发器（action: run）
│   │   └── keyword_list.json  # 关键词列表
│   ├── browser/
│   │   ├── asin_monitor.py       # ASIN 详情抓取
│   │   ├── keyword_monitor.py    # 关键词搜索结果抓取
│   │   ├── cdp_bridge.py         # 浏览器控制桥接
│   │   ├── init_browsers.py      # 双浏览器初始化
│   │   └── sprite_bridge.py      # 卖家精灵通信（暂不使用）
│   ├── run_monitor.py          # 主入口：定时调度
│   └── sync_monitor_data.py    # 数据合并脚本
├── frontend/
│   ├── monitor.html           # 前端页面（GitHub Pages 托管）
│   └── data/rawData.json      # 合并数据（GitHub Pages 读取）
```

---

## 三、启动服务器

### 方式 A：手动触发一次抓取

1. 关闭所有 Edge 窗口
2. 启动 Edge（默认 profile，端口 9225）：
   ```
   msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
   ```
3. 运行调度器：
   ```
   cd crossmart-monitor/backend
   python run_monitor.py
   ```

### 方式 B：通过 GitHub Actions（推荐）

1. 编辑 `backend/data/trigger.json`，推送：
   ```json
   {"action": "run", "status": "pending"}
   ```
2. GitHub Actions 自动执行 `run_monitor.py`

---

## 四、卖家精灵说明

- **位置**：卖家精灵插件安装在 Edge 浏览器，登录 sellersprite.com
- **作用**：关键词抓取时，插件标记 Amazon 搜索结果页上的 ASIN 位置和排名
- **如果插件未登录**：关键词抓取仍可进行，但无法获取自然排名数据（rank 字段为空）
- **Edge B**：独立的 Edge profile，专用于打开 sellersprite.com 网站

---

## 五、常见问题处理

### 1. git push 失败（TLS 错误）
**原因**：RabbitPro 等代理软件干扰了 443 端口 SSL 连接。
**解决**：暂时关闭代理软件，推完后再打开。

### 2. 页面显示"没有匹配数据"
**原因**：`rawData.json` 为空或不存在。
**解决**：运行 `python sync_monitor_data.py` 本地生成数据，或确认 `run_monitor.py` 已成功执行并推送。

### 3. 关键词 rank 数据为空
**原因**：抓取时卖家精灵插件未加载或未登录，导致 rank 字段为空。
**解决**：确保 Edge A 打开 Amazon 时卖家精灵插件已激活且登录。

### 4. 推送数据到 GitHub 失败
**原因**：网络问题或 RabbitPro 干扰。
**解决**：关闭 RabbitPro 后重试。

---

## 六、关键文件说明

| 文件 | 作用 |
|------|------|
| `user_config.json` | 配置要监控的 ASIN 和关键词 |
| `trigger.json` | 触发 GitHub Actions 执行的开关 |
| `asin_monitor.py` | 抓取单个 ASIN 的详情（价格/BSR/评分等） |
| `keyword_monitor.py` | 抓取关键词搜索结果页的 ASIN 列表 |
| `sync_monitor_data.py` | 合并本地数据到 `rawData.json` |
| `run_monitor.py` | 定时调度主脚本 |

---

## 七、数据维护

### 删除旧数据（重新开始）
1. 删除 `backend/data/processed/` 下的所有子目录
2. 删除 `frontend/data/rawData.json`
3. `git rm frontend/data/rawData.json && git commit -m "clean" && git push`

### 查看抓取日志
`crossmart-monitor/logs/` 目录下有每次运行的日志文件。