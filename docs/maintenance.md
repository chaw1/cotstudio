# COT Studio MVP 维护指南

## 概述

本文档提供了 COT Studio MVP 系统的日常维护、监控、备份和更新指南，确保系统稳定运行和数据安全。

## 日常维护任务

### 系统健康检查

#### 每日检查清单

```bash
#!/bin/bash
# daily_check.sh - 每日健康检查脚本

echo "=== COT Studio 每日健康检查 $(date) ==="

# 1. 检查服务状态
echo "1. 检查服务状态..."
docker-compose ps

# 2. 检查磁盘空间
echo "2. 检查磁盘空间..."
df -h

# 3. 检查内存使用
echo "3. 检查内存使用..."
free -h

# 4. 检查Docker资源使用
echo "4. 检查容器资源使用..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# 5. 检查服务健康状态
echo "5. 检查服务健康状态..."
curl -f http://localhost:8000/health || echo "后端服务异常"
curl -f http://localhost:3000 || echo "前端服务异常"

# 6. 检查数据库连接
echo "6. 检查数据库连接..."
docker-compose exec -T postgres pg_isready -U cotuser -d cotdb || echo "PostgreSQL连接异常"
docker-compose exec -T neo4j cypher-shell -u neo4j -p neo4jpass "RETURN 1" || echo "Neo4j连接异常"

# 7. 检查任务队列状态
echo "7. 检查Celery任务队列..."
docker-compose exec celery celery -A app.worker inspect active || echo "Celery异常"

echo "=== 健康检查完成 ==="
```

#### 自动化健康检查

```bash
# 添加到crontab中，每天上午9点执行
0 9 * * * /path/to/daily_check.sh >> /var/log/cot-studio-health.log 2>&1
```

### 日志管理

#### 日志轮转配置

```bash
# /etc/logrotate.d/cot-studio
/var/log/cot-studio/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker-compose restart rsyslog
    endscript
}
```

#### 日志收集脚本

```bash
#!/bin/bash
# collect_logs.sh - 收集系统日志

LOG_DIR="/var/log/cot-studio/$(date +%Y%m%d)"
mkdir -p $LOG_DIR

# 收集Docker容器日志
docker-compose logs --no-color frontend > $LOG_DIR/frontend.log
docker-compose logs --no-color backend > $LOG_DIR/backend.log
docker-compose logs --no-color celery > $LOG_DIR/celery.log
docker-compose logs --no-color postgres > $LOG_DIR/postgres.log
docker-compose logs --no-color neo4j > $LOG_DIR/neo4j.log
docker-compose logs --no-color redis > $LOG_DIR/redis.log
docker-compose logs --no-color minio > $LOG_DIR/minio.log
docker-compose logs --no-color rabbitmq > $LOG_DIR/rabbitmq.log

# 压缩日志文件
tar czf $LOG_DIR.tar.gz $LOG_DIR
rm -rf $LOG_DIR

echo "日志已收集到: $LOG_DIR.tar.gz"
```

### 数据库维护

#### PostgreSQL 维护

```bash
#!/bin/bash
# postgres_maintenance.sh

echo "开始PostgreSQL维护..."

# 1. 更新统计信息
docker-compose exec postgres psql -U cotuser -d cotdb -c "ANALYZE;"

# 2. 清理死元组
docker-compose exec postgres psql -U cotuser -d cotdb -c "VACUUM;"

# 3. 重建索引
docker-compose exec postgres psql -U cotuser -d cotdb -c "REINDEX DATABASE cotdb;"

# 4. 检查数据库大小
docker-compose exec postgres psql -U cotuser -d cotdb -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# 5. 检查慢查询
docker-compose exec postgres psql -U cotuser -d cotdb -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

echo "PostgreSQL维护完成"
```

#### Neo4j 维护

```bash
#!/bin/bash
# neo4j_maintenance.sh

echo "开始Neo4j维护..."

# 1. 检查数据库状态
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "SHOW DATABASES;"

# 2. 统计节点和关系数量
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "
MATCH (n) RETURN labels(n) as label, count(n) as count ORDER BY count DESC;
"

docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "
MATCH ()-[r]->() RETURN type(r) as relationship, count(r) as count ORDER BY count DESC;
"

# 3. 检查索引状态
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "SHOW INDEXES;"

# 4. 清理孤立节点
docker-compose exec neo4j cypher-shell -u neo4j -p neo4jpass "
MATCH (n) WHERE NOT (n)--() DELETE n;
"

echo "Neo4j维护完成"
```

## 监控和告警

### 系统监控

#### Prometheus 配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cot-studio-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

#### Grafana 仪表板

```json
{
  "dashboard": {
    "title": "COT Studio 监控",
    "panels": [
      {
        "title": "系统负载",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cpu_usage_total[5m])",
            "legendFormat": "CPU使用率"
          }
        ]
      },
      {
        "title": "内存使用",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_bytes / memory_total_bytes * 100",
            "legendFormat": "内存使用率"
          }
        ]
      },
      {
        "title": "API响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th百分位响应时间"
          }
        ]
      }
    ]
  }
}
```

### 告警规则

#### Prometheus 告警规则

```yaml
# alert_rules.yml
groups:
  - name: cot-studio-alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率超过80%持续5分钟"
          
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过85%持续5分钟"
          
      - alert: DatabaseConnectionFailed
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
          description: "PostgreSQL数据库无法连接"
          
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过长"
          description: "95%的API请求响应时间超过2秒"
```

#### 告警通知配置

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourcompany.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    email_configs:
      - to: 'admin@yourcompany.com'
        subject: 'COT Studio 告警: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          告警: {{ .Annotations.summary }}
          描述: {{ .Annotations.description }}
          时间: {{ .StartsAt }}
          {{ end }}
```

## 备份策略

### 自动备份系统

#### 备份脚本

```bash
#!/bin/bash
# backup_system.sh - 系统备份脚本

BACKUP_ROOT="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

mkdir -p $BACKUP_DIR

echo "开始系统备份: $DATE"

# 1. 备份PostgreSQL数据库
echo "备份PostgreSQL数据库..."
docker-compose exec -T postgres pg_dump -U cotuser -Fc cotdb > $BACKUP_DIR/postgres.dump
if [ $? -eq 0 ]; then
    echo "PostgreSQL备份成功"
else
    echo "PostgreSQL备份失败"
    exit 1
fi

# 2. 备份Neo4j数据库
echo "备份Neo4j数据库..."
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j_$DATE.dump
docker cp $(docker-compose ps -q neo4j):/tmp/neo4j_$DATE.dump $BACKUP_DIR/
if [ $? -eq 0 ]; then
    echo "Neo4j备份成功"
else
    echo "Neo4j备份失败"
fi

# 3. 备份MinIO对象存储
echo "备份MinIO数据..."
docker-compose exec minio tar czf /tmp/minio_$DATE.tar.gz /data
docker cp $(docker-compose ps -q minio):/tmp/minio_$DATE.tar.gz $BACKUP_DIR/
if [ $? -eq 0 ]; then
    echo "MinIO备份成功"
else
    echo "MinIO备份失败"
fi

# 4. 备份Redis数据
echo "备份Redis数据..."
docker-compose exec redis redis-cli BGSAVE
sleep 5
docker cp $(docker-compose ps -q redis):/data/dump.rdb $BACKUP_DIR/redis.rdb
if [ $? -eq 0 ]; then
    echo "Redis备份成功"
else
    echo "Redis备份失败"
fi

# 5. 备份配置文件
echo "备份配置文件..."
tar czf $BACKUP_DIR/config.tar.gz docker-compose.yml docker-compose.prod.yml .env docker/
if [ $? -eq 0 ]; then
    echo "配置文件备份成功"
else
    echo "配置文件备份失败"
fi

# 6. 生成备份清单
echo "生成备份清单..."
cat > $BACKUP_DIR/backup_manifest.txt << EOF
备份时间: $DATE
备份内容:
- PostgreSQL数据库: postgres.dump
- Neo4j数据库: neo4j_$DATE.dump
- MinIO对象存储: minio_$DATE.tar.gz
- Redis数据: redis.rdb
- 配置文件: config.tar.gz

备份大小:
$(du -sh $BACKUP_DIR/*)
EOF

# 7. 压缩备份目录
echo "压缩备份文件..."
cd $BACKUP_ROOT
tar czf "cot-studio-backup-$DATE.tar.gz" $DATE/
rm -rf $DATE/

echo "备份完成: cot-studio-backup-$DATE.tar.gz"

# 8. 清理旧备份 (保留最近30天)
find $BACKUP_ROOT -name "cot-studio-backup-*.tar.gz" -mtime +30 -delete

echo "系统备份完成"
```

#### 定时备份配置

```bash
# 添加到crontab
# 每天凌晨2点执行完整备份
0 2 * * * /path/to/backup_system.sh >> /var/log/cot-studio-backup.log 2>&1

# 每6小时执行增量备份
0 */6 * * * /path/to/incremental_backup.sh >> /var/log/cot-studio-backup.log 2>&1
```

### 备份验证

#### 备份完整性检查

```bash
#!/bin/bash
# verify_backup.sh - 验证备份完整性

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件>"
    exit 1
fi

echo "验证备份文件: $BACKUP_FILE"

# 1. 检查文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在"
    exit 1
fi

# 2. 检查文件完整性
echo "检查文件完整性..."
tar tzf $BACKUP_FILE > /dev/null
if [ $? -eq 0 ]; then
    echo "文件完整性检查通过"
else
    echo "错误: 文件损坏"
    exit 1
fi

# 3. 提取并验证内容
TEMP_DIR="/tmp/backup_verify_$$"
mkdir -p $TEMP_DIR
tar xzf $BACKUP_FILE -C $TEMP_DIR

# 4. 验证PostgreSQL备份
if [ -f "$TEMP_DIR/*/postgres.dump" ]; then
    echo "验证PostgreSQL备份..."
    pg_restore --list $TEMP_DIR/*/postgres.dump > /dev/null
    if [ $? -eq 0 ]; then
        echo "PostgreSQL备份验证通过"
    else
        echo "警告: PostgreSQL备份可能有问题"
    fi
fi

# 5. 验证Neo4j备份
if [ -f "$TEMP_DIR/*/neo4j_*.dump" ]; then
    echo "Neo4j备份文件存在"
fi

# 6. 验证配置文件
if [ -f "$TEMP_DIR/*/config.tar.gz" ]; then
    echo "配置文件备份存在"
fi

# 清理临时文件
rm -rf $TEMP_DIR

echo "备份验证完成"
```

## 系统更新

### 应用更新流程

#### 更新脚本

```bash
#!/bin/bash
# update_system.sh - 系统更新脚本

echo "开始系统更新..."

# 1. 备份当前系统
echo "1. 创建更新前备份..."
./backup_system.sh

# 2. 拉取最新代码
echo "2. 拉取最新代码..."
git fetch origin
git checkout main
git pull origin main

# 3. 检查配置文件变更
echo "3. 检查配置文件..."
if [ -f ".env.example" ]; then
    echo "请检查.env.example中的新配置项"
    diff .env .env.example || true
fi

# 4. 更新依赖
echo "4. 更新依赖..."
cd frontend && npm install && cd ..
cd backend && pip install -r requirements.txt && cd ..

# 5. 构建新镜像
echo "5. 构建Docker镜像..."
docker-compose build

# 6. 执行数据库迁移
echo "6. 执行数据库迁移..."
docker-compose run --rm backend alembic upgrade head

# 7. 滚动更新服务
echo "7. 更新服务..."
docker-compose up -d --no-deps backend
sleep 30
docker-compose up -d --no-deps frontend
docker-compose up -d --no-deps celery

# 8. 验证更新
echo "8. 验证更新..."
sleep 60
curl -f http://localhost:8000/health || echo "后端服务异常"
curl -f http://localhost:3000 || echo "前端服务异常"

echo "系统更新完成"
```

### 回滚流程

#### 回滚脚本

```bash
#!/bin/bash
# rollback_system.sh - 系统回滚脚本

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <备份文件>"
    exit 1
fi

echo "开始系统回滚..."

# 1. 停止当前服务
echo "1. 停止服务..."
docker-compose down

# 2. 恢复备份
echo "2. 恢复备份..."
./restore_backup.sh $BACKUP_FILE

# 3. 重启服务
echo "3. 重启服务..."
docker-compose up -d

# 4. 验证回滚
echo "4. 验证回滚..."
sleep 60
curl -f http://localhost:8000/health || echo "后端服务异常"
curl -f http://localhost:3000 || echo "前端服务异常"

echo "系统回滚完成"
```

## 性能优化

### 数据库性能优化

#### PostgreSQL 优化

```sql
-- 性能优化配置
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- 重新加载配置
SELECT pg_reload_conf();

-- 创建性能监控视图
CREATE OR REPLACE VIEW performance_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;
```

#### Neo4j 优化

```cypher
// 创建索引优化查询性能
CREATE INDEX entity_name_index FOR (e:Entity) ON (e.name);
CREATE INDEX document_id_index FOR (d:Document) ON (d.id);
CREATE INDEX cot_item_id_index FOR (c:COTItem) ON (c.id);

// 创建约束确保数据一致性
CREATE CONSTRAINT entity_id_unique FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT document_id_unique FOR (d:Document) REQUIRE d.id IS UNIQUE;
```

### 应用性能优化

#### 缓存策略

```python
# backend/app/core/cache.py
import redis
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(ttl=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 异步任务优化

```python
# backend/app/worker.py
from celery import Celery

# 优化Celery配置
celery_app = Celery(
    "cot_studio",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.tasks"]
)

# 配置任务路由
celery_app.conf.task_routes = {
    'app.tasks.ocr_task': {'queue': 'ocr'},
    'app.tasks.llm_task': {'queue': 'llm'},
    'app.tasks.kg_task': {'queue': 'kg'},
}

# 配置任务优先级
celery_app.conf.task_default_priority = 5
celery_app.conf.worker_prefetch_multiplier = 1
```

## 安全维护

### 安全更新

#### 定期安全检查

```bash
#!/bin/bash
# security_check.sh - 安全检查脚本

echo "开始安全检查..."

# 1. 检查Docker镜像漏洞
echo "1. 检查Docker镜像安全..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image cot-studio-mvp_backend:latest

# 2. 检查依赖漏洞
echo "2. 检查Python依赖安全..."
docker-compose exec backend pip-audit

echo "3. 检查Node.js依赖安全..."
cd frontend && npm audit && cd ..

# 4. 检查配置安全
echo "4. 检查配置安全..."
if grep -q "password.*123" .env; then
    echo "警告: 发现弱密码"
fi

if grep -q "secret.*test" .env; then
    echo "警告: 发现测试密钥"
fi

echo "安全检查完成"
```

### 访问控制维护

#### 用户权限审计

```bash
#!/bin/bash
# audit_permissions.sh - 权限审计脚本

echo "开始权限审计..."

# 1. 检查数据库用户权限
docker-compose exec postgres psql -U cotuser -d cotdb -c "
SELECT 
    r.rolname,
    r.rolsuper,
    r.rolinherit,
    r.rolcreaterole,
    r.rolcreatedb,
    r.rolcanlogin,
    r.rolconnlimit,
    r.rolvaliduntil
FROM pg_roles r
ORDER BY r.rolname;
"

# 2. 检查文件权限
echo "检查关键文件权限..."
ls -la .env docker-compose.yml

# 3. 检查网络访问
echo "检查网络端口..."
netstat -tulpn | grep -E ':(3000|8000|5432|7474|6379|9000|5672)'

echo "权限审计完成"
```

## 容量规划

### 存储容量监控

```bash
#!/bin/bash
# storage_monitoring.sh - 存储监控脚本

echo "存储使用情况监控..."

# 1. 检查主机存储
echo "1. 主机存储使用情况:"
df -h

# 2. 检查Docker卷使用情况
echo "2. Docker卷使用情况:"
docker system df

# 3. 检查数据库大小
echo "3. 数据库大小:"
docker-compose exec postgres psql -U cotuser -d cotdb -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database;
"

# 4. 检查MinIO存储使用
echo "4. MinIO存储使用:"
docker-compose exec minio du -sh /data/*

# 5. 预测存储增长
echo "5. 存储增长预测:"
# 基于历史数据预测未来30天的存储需求
# 这里可以集成更复杂的预测算法

echo "存储监控完成"
```

### 性能容量规划

```bash
#!/bin/bash
# capacity_planning.sh - 容量规划脚本

echo "性能容量分析..."

# 1. CPU使用趋势
echo "1. CPU使用趋势:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}"

# 2. 内存使用趋势
echo "2. 内存使用趋势:"
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# 3. 网络I/O趋势
echo "3. 网络I/O趋势:"
docker stats --no-stream --format "table {{.Container}}\t{{.NetIO}}"

# 4. 磁盘I/O趋势
echo "4. 磁盘I/O趋势:"
docker stats --no-stream --format "table {{.Container}}\t{{.BlockIO}}"

echo "容量分析完成"
```

## 维护计划

### 维护时间表

| 频率 | 任务 | 脚本 | 时间 |
|------|------|------|------|
| 每日 | 健康检查 | daily_check.sh | 09:00 |
| 每日 | 日志收集 | collect_logs.sh | 23:00 |
| 每日 | 完整备份 | backup_system.sh | 02:00 |
| 每周 | 数据库维护 | postgres_maintenance.sh | 周日 03:00 |
| 每周 | 安全检查 | security_check.sh | 周日 04:00 |
| 每月 | 性能优化 | performance_tuning.sh | 第一个周日 |
| 每月 | 容量规划 | capacity_planning.sh | 最后一个周日 |
| 每季度 | 系统更新 | update_system.sh | 按需 |

### 维护检查清单

#### 每日维护清单

- [ ] 检查所有服务状态
- [ ] 检查系统资源使用
- [ ] 检查错误日志
- [ ] 验证备份完成
- [ ] 检查监控告警

#### 每周维护清单

- [ ] 数据库性能优化
- [ ] 清理临时文件
- [ ] 更新安全补丁
- [ ] 检查用户权限
- [ ] 分析性能趋势

#### 每月维护清单

- [ ] 容量规划评估
- [ ] 备份策略审查
- [ ] 安全审计
- [ ] 性能基准测试
- [ ] 文档更新

---

本维护指南提供了系统运维的完整框架。请根据实际环境和需求调整维护策略和时间表。