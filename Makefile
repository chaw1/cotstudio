# COT Studio MVP Makefile

.PHONY: help install dev build test clean docker-build docker-up docker-down

# 默认目标
help:
	@echo "COT Studio MVP - 可用命令:"
	@echo ""
	@echo "开发命令:"
	@echo "  install      - 安装所有依赖"
	@echo "  dev          - 启动开发环境"
	@echo "  build        - 构建应用"
	@echo "  test         - 运行所有测试"
	@echo "  lint         - 运行代码检查"
	@echo "  format       - 格式化代码"
	@echo "  clean        - 清理构建文件"
	@echo ""
	@echo "Docker命令:"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-up    - 启动Docker服务"
	@echo "  docker-down  - 停止Docker服务"
	@echo "  docker-logs  - 查看Docker日志"
	@echo ""
	@echo "部署命令:"
	@echo "  deploy-dev   - 部署开发环境"
	@echo "  deploy-prod  - 部署生产环境"
	@echo "  update       - 更新系统"
	@echo ""
	@echo "维护命令:"
	@echo "  health-check - 执行健康检查"
	@echo "  backup       - 创建系统备份"
	@echo "  monitor      - 查看系统监控信息"
	@echo "  logs         - 实时查看日志"
	@echo "  logs-save    - 保存日志到文件"
	@echo ""
	@echo "数据库命令:"
	@echo "  db-migrate   - 执行数据库迁移"
	@echo "  db-reset     - 重置数据库"

# 安装依赖
install:
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt

# 启动开发环境
dev:
	docker-compose up -d postgres redis neo4j minio rabbitmq
	@echo "等待服务启动..."
	sleep 10
	@echo "启动后端开发服务器..."
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "启动前端开发服务器..."
	cd frontend && npm run dev

# 构建应用
build:
	@echo "构建前端..."
	cd frontend && npm run build
	@echo "构建完成"

# 运行测试
test:
	@echo "运行前端测试..."
	cd frontend && npm run test -- --run
	@echo "运行后端测试..."
	cd backend && pytest

# 代码检查
lint:
	@echo "检查前端代码..."
	cd frontend && npm run lint
	@echo "检查后端代码..."
	cd backend && flake8 .

# 格式化代码
format:
	@echo "格式化后端代码..."
	cd backend && black . && isort .
	@echo "代码格式化完成"

# 清理构建文件
clean:
	@echo "清理构建文件..."
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	rm -rf backend/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	@echo "清理完成"

# Docker操作
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# 数据库操作
db-migrate:
	cd backend && alembic upgrade head

db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	cd backend && alembic upgrade head

# 部署操作
deploy-dev:
	@echo "部署开发环境..."
	docker-compose up -d
	@echo "等待服务启动..."
	sleep 30
	@echo "验证部署..."
	curl -f http://localhost:8000/health || echo "后端服务检查失败"
	curl -f http://localhost:3000 || echo "前端服务检查失败"
	@echo "开发环境部署完成"

deploy-prod:
	@echo "部署生产环境..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "等待服务启动..."
	sleep 60
	@echo "验证部署..."
	curl -f http://localhost:8000/health || echo "后端服务检查失败"
	curl -f http://localhost:3000 || echo "前端服务检查失败"
	@echo "生产环境部署完成"

# 维护操作
health-check:
	@echo "执行健康检查..."
	docker-compose ps
	@echo "检查服务健康状态..."
	curl -f http://localhost:8000/health && echo "后端服务正常" || echo "后端服务异常"
	curl -f http://localhost:3000 && echo "前端服务正常" || echo "前端服务异常"

backup:
	@echo "创建系统备份..."
	@if [ ! -d "backup" ]; then mkdir backup; fi
	@DATE=$$(date +%Y%m%d_%H%M%S) && \
	echo "备份时间: $$DATE" && \
	docker-compose exec -T postgres pg_dump -U cotuser -Fc cotdb > backup/postgres_$$DATE.dump && \
	echo "PostgreSQL备份完成" && \
	docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j_$$DATE.dump && \
	docker cp $$(docker-compose ps -q neo4j):/tmp/neo4j_$$DATE.dump backup/ && \
	echo "Neo4j备份完成" && \
	tar czf backup/config_$$DATE.tar.gz docker-compose.yml docker-compose.prod.yml .env docker/ && \
	echo "配置文件备份完成" && \
	echo "备份完成，文件保存在 backup/ 目录"

logs:
	docker-compose logs -f

logs-save:
	@DATE=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p logs/$$DATE && \
	docker-compose logs --no-color frontend > logs/$$DATE/frontend.log && \
	docker-compose logs --no-color backend > logs/$$DATE/backend.log && \
	docker-compose logs --no-color celery > logs/$$DATE/celery.log && \
	docker-compose logs --no-color postgres > logs/$$DATE/postgres.log && \
	docker-compose logs --no-color neo4j > logs/$$DATE/neo4j.log && \
	tar czf logs/cot-studio-logs-$$DATE.tar.gz logs/$$DATE && \
	rm -rf logs/$$DATE && \
	echo "日志已保存到 logs/cot-studio-logs-$$DATE.tar.gz"

# 更新操作
update:
	@echo "更新系统..."
	git pull origin main
	docker-compose build
	docker-compose up -d
	@echo "系统更新完成"

# 监控操作
monitor:
	@echo "系统监控信息:"
	@echo "=== 容器状态 ==="
	docker-compose ps
	@echo "=== 资源使用 ==="
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
	@echo "=== 磁盘使用 ==="
	df -h
	@echo "=== 内存使用 ==="
	free -h