# CrossMart Monitor 用户手册

## 一、系统功能

通过**自己的 Edge 浏览器**自动访问亚马逊和卖家精灵，抓取 ASIN 详情数据和关键词市场数据。

---

## 二、前端页面

**地址**：https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html

**功能**：
- 查看所有监控 ASIN 的价格、BSR、评分、评论数变化曲线
- 查看 ASIN 来源（直接监控 / 关键词发现）
- 筛选：全部 / ASIN监控 / 关键词监控
- 搜索：按 ASIN 或标题搜索
- 数据下载（Excel 导出）

---

## 三、如何添加新的监控目标

### 1. 添加 ASIN 监控

编辑 GitHub 上的配置文件：
`backend/data/user_config.json`

```json
{
  "asins": [
    { "main": "B0XXXXXXX", "related": ["B0YYYYYYY"] }
  ],
  "keywords": [
    { "main": "dark spot" }
  ]
}
```

- `main`：必填，要监控的 ASIN
- `related`：可选，该 ASIN 的关联竞品 ASIN

### 2. 添加关键词监控

同上，在 `keywords` 数组里添加：

```json
{ "main": "skin care serum" }
```

---

## 四、Badge 说明

| Badge 样式 | 含义 |
|-----------|------|
| `ASIN`（蓝底） | 直接监控的 ASIN |
| `KW-dark spot`（粉底） | 通过关键词 "dark spot" 发现的 ASIN |
| `主监控` | 直接监控的 ASIN（第二 badge） |
| `自然位：第x页第x位` | 关键词搜索结果中的排名位置 |

---

## 五、如何触发一次抓取

通过 GitHub 触发器触发，编辑：
`backend/data/trigger.json`

```json
{
  "action": "run",
  "status": "pending"
}
```

推送后云端会自动执行 `run_monitor.py`。

---

## 六、数据说明

- **前端页面**读取的是 `frontend/data/rawData.json`（由 `sync_monitor_data.py` 合并生成）
- **本地抓取数据**保存在 `backend/data/processed/asin_*` 和 `backend/data/processed/kw_*`
- 每次抓取完成后，数据会自动同步到 GitHub Pages 前端

---

## 七、常见问题

**Q: 页面显示"没有匹配数据"**
A: 检查 GitHub 上 `frontend/data/rawData.json` 是否存在且有数据。可能是还没有执行过抓取。

**Q: 筛选功能不正常**
A: 按 Ctrl + Shift + R 强制刷新页面，清除浏览器缓存。

**Q: 想看关键词带来的 ASIN 排名变化**
A: 选"关键词监控"筛选，可以看到每个 ASIN 在关键词搜索结果中的位置变化。