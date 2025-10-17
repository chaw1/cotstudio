# COT Studio MVP 故障排除指南

## 常见问题解决方案

### 1. 服务启动问题

#### Docker 服务无法启动
```bash
# 检查 Docker 是否运行
docker --version
docker-compose --version

# 检查端口占用
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432

# 停止占用端口的进程
sudo kill -9 $(lsof -t -i:3000)
```

#### 内存不足
```bash
# 检查系统资源
docker stats
free -h

# 清理 Docker 资源
docker system prune -f
docker volume prune -f
```

### 2. 数据库连接问题

#### PostgreSQL 连接失败
```bash
# 检查 PostgreSQL 容器状态
docker-compose ps postgres
docker-compose logs postgres

# 测试连接
docker-compose exec postgres psql -U cotuser -d cotdb -c "SELECT 1;"

# 重启 PostgreSQL
docker-compose restart postgres
```

#### Neo4j 连接失败
```bash
# 检查 Neo4j 容器状态
docker-compose ps neo4j
docker-compose logs neo4j

# 测试连接
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "RETURN 1;"

# 重启 Neo4j
docker-compose restart neo4j
```

### 3. 认证和登录问题

#### 前端登录失败
1. **检查后端服务状态**
   ```bash
   curl http://localhost:8000/health
   ```

2. **使用正确的凭据**
   - 用户名: `admin`
   - 密码: `971028`

3. **检查浏览器控制台**
   - 打开开发者工具 (F12)
   - 查看 Console 和 Network 标签页
   - 查找 401、404 或其他错误

4. **清除浏览器缓存**
   - 清除 localStorage 和 sessionStorage
   - 刷新页面重新登录

#### JWT Token 问题
```bash
# 检查后端日志
docker-compose logs backend | grep -i "auth\|token\|jwt"

# 重启后端服务
docker-compose restart backend
```

### 4. API 调用问题

#### LLM API 调用失败
1. **检查 API 密钥配置**
   ```bash
   # 查看环境变量
   docker-compose exec backend env | grep -i "api_key"
   ```

2. **验证 API 密钥有效性**
   - 检查 OpenAI/DeepSeek/KIMI 账户余额
   - 确认 API 密钥未过期
   - 测试 API 密钥是否正确

3. **检查网络连接**
   ```bash
   # 测试外部 API 连接
   curl -I https://api.openai.com
   curl -I https://api.deepseek.com
   ```

#### 文件上传失败
```bash
# 检查 MinIO 服务
docker-compose ps minio
docker-compose logs minio

# 检查存储空间
df -h

# 重启 MinIO
docker-compose restart minio
```

### 5. 性能问题

#### 响应速度慢
1. **检查系统资源使用**
   ```bash
   docker stats
   htop  # 或 top
   ```

2. **检查数据库性能**
   ```bash
   # PostgreSQL 性能查询
   docker-compose exec postgres psql -U cotuser -d cotdb -c "
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC LIMIT 10;"
   ```

3. **优化配置**
   ```bash
   # 增加数据库连接池
   # 在 .env 中设置
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=30
   ```

#### 内存使用过高
```bash
# 检查各服务内存使用
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 重启内存使用过高的服务
docker-compose restart [service_name]
```

### 6. 开发环境问题

#### 前端开发服务器问题
```bash
# 清理 node_modules
cd frontend
rm -rf node_modules package-lock.json
npm install

# 检查 Node.js 版本
node --version  # 应该是 18+
npm --version
```

#### 后端开发服务器问题
```bash
# 重新创建虚拟环境
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 检查 Python 版本
python --version  # 应该是 3.11+
```

### 7. 数据问题

#### 数据库迁移失败
```bash
# 检查迁移状态
docker-compose exec backend alembic current
docker-compose exec backend alembic history

# 重新执行迁移
docker-compose exec backend alembic upgrade head

# 如果迁移失败，回滚并重试
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

#### 数据丢失或损坏
```bash
# 检查数据卷
docker volume ls
docker volume inspect cotstudio_postgres_data

# 从备份恢复 (如果有备份)
docker-compose exec postgres pg_restore -U cotuser -d cotdb /backup/backup.sql
```

### 8. 网络问题

#### 服务间通信失败
```bash
# 检查 Docker 网络
docker network ls
docker network inspect cotstudio_cot-network

# 测试服务间连接
docker-compose exec backend ping postgres
docker-compose exec backend ping neo4j
```

#### 外部网络访问问题
```bash
# 检查防火墙设置
sudo ufw status

# 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 测试外部连接
curl -I https://www.google.com
```

## 日志分析

### 查看服务日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# 实时查看日志
docker-compose logs -f backend

# 查看最近的日志
docker-compose logs --tail=100 backend
```

### 日志级别设置
在 `.env` 文件中设置日志级别：
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 性能监控

### 系统监控
- **系统资源**: http://localhost:3000/dashboard
- **Celery 任务**: http://localhost:5555
- **Neo4j 监控**: http://localhost:7474
- **MinIO 监控**: http://localhost:9001
- **RabbitMQ 监控**: http://localhost:15672

### 健康检查
```bash
# 检查所有服务健康状态
curl http://localhost:8000/health
curl http://localhost:3000/health.html

# 检查数据库连接
docker-compose exec backend python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK:', result.fetchone())
"
```

## 重置和清理

### 完全重置环境
```bash
# 停止所有服务
docker-compose down

# 删除所有数据卷 (注意：会丢失所有数据)
docker-compose down -v

# 清理 Docker 资源
docker system prune -a

# 重新启动
docker-compose up -d
```

### 部分重置
```bash
# 只重置数据库
docker-compose stop postgres
docker volume rm cotstudio_postgres_data
docker-compose up -d postgres

# 只重置 Neo4j
docker-compose stop neo4j
docker volume rm cotstudio_neo4j_data
docker-compose up -d neo4j
```

## 获取帮助

如果以上解决方案都无法解决问题，请：

1. **收集信息**
   ```bash
   # 系统信息
   docker --version
   docker-compose --version
   uname -a
   
   # 服务状态
   docker-compose ps
   
   # 错误日志
   docker-compose logs > debug.log
   ```

2. **查看文档**
   - [项目指南](../PROJECT_GUIDE.md)
   - [安装指南](INSTALLATION.md)
   - [开发指南](DEVELOPMENT.md)

3. **提交 Issue**
   - 在 GitHub 上创建 Issue
   - 提供详细的错误信息和系统环境
   - 包含相关的日志文件

---

**更新日期**: 2025-01-17  
**版本**: 1.0.0