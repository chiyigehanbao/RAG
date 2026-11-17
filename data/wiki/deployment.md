# NovaCloud 部署指南

## Docker 部署

推荐使用 Docker Compose。克隆部署仓库后执行：

```bash
docker compose up -d
```

默认监听 `8080` 端口，首次启动需完成初始化向导。

## 环境变量

关键变量：

- `NOVACLOUD_DB_URL`：PostgreSQL 连接串
- `NOVACLOUD_SECRET_KEY`：会话签名密钥（至少 32 字符）
- `NOVACLOUD_REDIS_URL`：Redis 缓存（可选，建议生产环境配置）

## 健康检查

访问 `GET /health` 应返回 `{"status":"ok"}`。
