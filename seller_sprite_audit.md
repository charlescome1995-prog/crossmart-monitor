# 卖家精灵插件数据审计报告

**审计日期**: 2026-06-16
**测试 ASIN**: B017PCGABI (Garnier Micellar Water)
**测试关键词**: "makeup remover"
**插件状态**: 活跃, 自动注入, 无需点击展开

---

## 1. 数据注入位置（产品页 vs 搜索页完全不同）

### 1.1 产品页（`/dp/<ASIN>`）自动注入的元素

| 元素 ID | 用途 | 数据长度 |
| --- | --- | --- |
| `seller-sprite-extension-quick-view-listing-page` | 核心指标面板 | ~209 chars |
| `seller-sprite-extension-quick-view-listing` | ASIN 基本信息面板 | ~611 chars |
| `seller-sprite-extension-main-relation` | 主要流量词（Vue HTML 结构） | ~366 chars HTML |
| `sellersprite-extension-inventory` | 库存信息 | ~287 chars |
| `seller-sprite-extension-app` | 插件根容器 |  |

**`quick-view-listing-page` 内容**（B017PCGABI 真实数据）：
```
v5.0.3（数据来源：卖家精灵）
质量得分: 10.0
近30天销量(父体): 122,070
(子体销量: 1,114,865)
Listing销售额: $1,076,657
均价: $9.48
BSR: 54
FBA费用: $3.91
变体数: 4
上架时间: 2015-11-12(3,868天)
```

### 1.2 搜索页（`/s?k=<keyword>`）注入的侧边栏

- 根元素：`#seller-sprite-extension-app`（虚拟滚动 3220 chars 可见区）
- 包含 8 个 tab：**产品查询**（默认）、关键词反查、关键词挖掘、关键词收录、筛查相关性、产品库、API接口、MCP服务
- "产品查询" tab 加载 `vxe-table`，**64 个 ASIN**（虚拟滚动，DOM 中始终只 8-10 行）

**`vxe-table` 25 列结构**：

| 列索引 | 列字段 | 例子 |
| --- | --- | --- |
| col_2 | (控件) |  |
| col_3 | 复选框 |  |
| **col_4** | **rank（搜索位置）** | **57, 58, 59 ... 或 Garnier 在 #3** |
| col_5 | 树节点 |  |
| col_6 | 产品标题 | "Farmacy Makeup Remover Cleansing Balm..." |
| col_7 | 品牌 | "Farmacy" |
| col_8 | 品类 | "美妆/个护健康" |
| col_9 | BSR | 2,240 |
| col_10 | 销量 | 10,567 |
| col_11 | 销售额 | $253,608 |
| col_12 | 子体销量/销售额 | 1K+ / $24K+ |
| col_13 | 变体数 | 11 |
| col_14 | 价格 | $24.00 |
| col_15 | Q&A数 | 39 |
| col_16 | 评分人数 | 8,528 |
| col_17 | 月评新增 | 11 |
| col_18 | 评分 | 4.6 |
| col_19 | 留评率 | 0.10% |
| col_20 | FBA 费用 | $3.86 |
| col_21 | 毛利率 | 69% |
| **col_22** | **上架时间** | **2019/02/07** |
| col_23 | 卖家数 | 1 |
| col_24 | 配送方式 | FBA / AMZ |
| col_25 | 配送时间 | 5天 |

---

## 2. 我们目前用到的数据

| 字段 | 来源 | 是否使用 | 备注 |
| --- | --- | --- | --- |
| LQS 质量得分 | quick-view-listing-page | ✅ | `lqs` 字段 |
| 父体/子体销量 | quick-view-listing-page | ✅ | `sales_30d_parent`, `sales_30d_child` |
| Listing 销售额 | quick-view-listing-page | ✅ | `revenue_30d` |
| 均价 | quick-view-listing-page | ✅ | `avg_price` |
| BSR | quick-view-listing-page | ✅ | `bsr` |
| FBA 费用 | quick-view-listing-page | ✅ | `fba_fee` |
| 变体数 | quick-view-listing-page | ✅ | `variant_count` |
| 上架时间 | quick-view-listing-page | ✅ | `launch_date`, `days_online` |
| 毛利率 | quick-view-listing-page | ✅ | `gross_margin` |
| 品牌 | quick-view-listing | ✅ | `brand` |
| 卖家 | quick-view-listing | ✅ | `seller` |
| 评分 | quick-view-listing | ✅ | `rating` |
| 评论数 | quick-view-listing | ✅ | `review_count` |
| BSR 排名（大类） | quick-view-listing | ✅ | `bsr_rank`, `bsr_category` |
| **rank 字段** | **vxe-table col_4** | ❌ **从未提取** | 这是闫旭指出的核心 bug |

---

## 3. 加载行为

### 3.1 产品页（自动注入）
- 进入 `/dp/<ASIN>` 页面后 1-3 秒内卖家精灵自动注入 `quick-view-listing-page`
- **无需点击任何按钮**
- 数据从无 → 完整 是渐进式的：
  - 第 1 秒：可能只有空壳 `<div>`
  - 第 2-3 秒：销量、评分等基础数据出现
  - 第 3-5 秒：上架时间、FBA 费用等完整数据出现
- **稳定判断标志**：`seller-sprite-extension-quick-view-listing-page` 的 `innerText` 包含 "上架时间" 字样

### 3.2 搜索页（自动注入侧边栏 + 需用户激活"产品查询"）
- 进入 `/s?k=<keyword>` 页面后卖家精灵在右侧自动注入侧边栏
- 默认显示 "产品查询" tab 的统计摘要（总销量、平均销量等）
- **vxe-table 不会自动加载**——需要用户点击"产品查询" tab 或插件内某些按钮触发
- 表格加载需要 1-2 分钟（卖家精灵服务端查询）
- **虚拟滚动**：DOM 中始终只有 8-10 行可见，需要 `body.scrollTop` 配合 `dispatchEvent('scroll')` 触发加载新批
- **ASIN 不在表格中**：表格只显示标题、品牌等，**没有 `/dp/<ASIN>` 链接**
- ASIN 关联方式：必须**用表格标题 + 左侧 Amazon 搜索结果中同标题的 ASIN** 进行匹配

---

## 4. rank 字段的修复方案

### 当前问题
- `keyword_monitor.py` 提取的 `top_asins` 数据中**没有 rank 字段**
- 闫旭指出：fix 后应该显示 "第一页自然位第1位" 这种格式

### 真实数据格式
卖家精灵 vxe-table 的 col_4 直接给出**数字 rank**（1-64），不是 "自然位/广告位" 文字。

**Garnier B017PCGABI 在 "makeup remover" 关键词下的 rank = 3**

**判断自然位/广告位**：
- Amazon 搜索结果有 16 个 organic slots + N 个 sponsored slots
- vxe-table 的 1-7 范围通常包含自然位 + 广告位
- 卖家精灵的 vxe-table 中 col_4 是**该 ASIN 在搜索结果中的真实位置编号**（不分自然/广告）
- 区分自然/广告需要**与 Amazon 搜索结果中 `data-component-type="s-search-result"` 的位置比较**：
  - 如果 vxe-table 的 rank 数字 = organic 结果中第 N 个 → 自然位
  - 否则 → 广告位

### 修复实现（需要做 2 件事）
1. **从 vxe-table 提取每行 ASIN 的 rank 数字**（通过 col_4）
2. **关联 ASIN**：标题 + 滚动 vxe-table 提取所有 64 行的 rank
3. **自然/广告位判断**：与 Amazon 搜索结果中 organic 项的位置匹配

### 关键技术点
- vxe-table 虚拟滚动需要用 `body.scrollTop` + `dispatchEvent('scroll')` 触发新批加载
- 表格内 ASIN 不直接显示，需要二次匹配
- 加载耗时 1-2 分钟（卖家精灵服务端查询）— 需要在轮询循环中等待

---

## 5. 修复建议

### 优先级 P0：rank 字段
- 在 `fetch_keyword_asins.py` 中添加 `extract_sprite_table_rank(page)` 函数
- 该函数：滚动 vxe-table 加载所有 64 行 → 提取每行 (rank, title, brand) → 返回
- 在轮询循环中调用，等待 vxe-table 加载完成

### 优先级 P1：自然位/广告位判断
- 抓取 Amazon 搜索结果的 organic 项（`[data-component-type="s-search-result"]`）
- 记录每个 organic 项的 ASIN 和位置（1, 2, 3, ...）
- 与 vxe-table 的 rank 对比：
  - vxe-table rank = organic 位置 → 自然位第 X 位
  - 否则 → 广告位

### 优先级 P2：launch_date 优化
- 之前测试 B017PCGABI 总是空——已确认 Amazon 产品页 DOM 本身就没有 "上架时间" 字段
- 卖家精灵 `quick-view-listing-page` 提供了 `上架时间: 2015-11-12(3,868天)`
- 这个数据**已经在 `extract_sprite_plugin_data` 里被提取**了，但是需要 `plugin_ready=True` 才会被调用
- **关键 bug**：`plugin_ready` 门控逻辑有问题——让我测试一次真实流程

---

## 6. 关键 bug：plugin_ready 门控失败

**症状**：
- 卖家精灵插件明确已加载（vxe-table 都有数据）
- `extract_sprite_plugin_data` 被调用但**返回 0 字段**
- `plugin_ready` 永远为 False
- `plugin_data` 永远是空 `{}`
- 导致 launch_date、lqs、sales_30d_parent 等**所有卖家精灵字段都是空的**

**根因**（待确认）：
1. **`amazon` 模式跳过 `plugin_ready` 检查**（从代码看不是）
2. **`connect_tab("about:blank")` 破坏了已加载的 seller-sprite 状态**（很可能！）
3. **多次 eval 调用导致 seller-sprite 数据丢失**（不太可能）

下一步：直接用我自己的脚本验证 `extract_sprite_plugin_data` 在 `asin_monitor.py` 调用流程下能否拿到数据。
