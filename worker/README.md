# Cloudflare Worker 源码

## 文件结构

```
worker/
├── src/
│   └── index.js      # Worker 主逻辑
└── wrangler.toml     # 部署配置
```

## 部署步骤

### 1. 安装 Wrangler CLI
```bash
npm install -g wrangler
```

### 2. 登录 Cloudflare
```bash
wrangler login
```

### 3. 配置环境变量
在 Cloudflare Dashboard 中添加加密变量：
- `GH_TOKEN` — GitHub Personal Access Token（需 repo 权限）
- `GH_REPO` — 仓库名（默认已填）
- `GH_CONFIG_PATH` — 配置文件路径（默认已填）

**不要把 token 写在代码里或 wrangler.toml 中！**

### 4. 部署
```bash
cd worker
wrangler deploy
```

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/config` | 读取当前用户配置 |
| POST | `/config` | 保存用户配置到 GitHub |

## 与原版区别

- **Token 从环境变量读取**，不写在代码里
- **修复了 SHA 冲突问题**（先 GET 获取 sha，再 PUT）
- **Workflow 保存逻辑**仍然保留作为备选（如果未来需要）