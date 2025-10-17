#!/bin/bash

# COT Studio MVP 一键启动脚本
# 使用方法: ./scripts/start.sh [dev|prod]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统依赖检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p docker/postgres
    mkdir -p docker/nginx
    mkdir -p logs
    mkdir -p data/uploads
    
    log_success "目录创建完成"
}

# 初始化环境变量
init_env() {
    log_info "初始化环境变量..."
    
    if [ ! -f .env ]; then
        log_info "创建 .env 文件..."
        cat > .env << EOF
# COT Studio MVP 环境配置

# 数据库配置
POSTGRES_DB=cotdb
POSTGRES_USER=cotuser
POSTGRES_PASSWORD=cotpass_$(date +%s)

# Neo4j配置
NEO4J_PASSWORD=neo4jpass_$(date +%s)

# Redis配置
REDIS_PASSWORD=redispass_$(date +%s)

# MinIO配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_$(date +%s)

# RabbitMQ配置
RABBITMQ_USER=cotuser
RABBITMQ_PASSWORD=cotpass_$(date +%s)

# JWT配置
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 环境类型
ENVIRONMENT=${1:-dev}
EOF
        log_success ".env 文件创建完成"
    else
        log_info ".env 文件已存在，跳过创建"
    fi
}

# 启动服务
start_services() {
    local env_type=${1:-dev}
    
    log_info "启动 COT Studio MVP ($env_type 环境)..."
    
    if [ "$env_type" = "prod" ]; then
        log_info "使用生产环境配置启动..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        log_info "使用开发环境配置启动..."
        docker-compose up -d
    fi
    
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    check_services_health
}

# 检查服务健康状态
check_services_health() {
    log_info "检查服务健康状态..."
    
    local services=("postgres" "redis" "neo4j" "minio" "rabbitmq" "backend" "frontend")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "${service}.*Up.*healthy\|${service}.*Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务启动失败"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "所有服务启动成功！"
        show_access_info
    else
        log_error "以下服务启动失败: ${failed_services[*]}"
        log_info "查看日志: docker-compose logs <service_name>"
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    log_info "服务访问信息:"
    echo ""
    echo "🌐 前端应用:        http://localhost:3000"
    echo "🔧 后端API:         http://localhost:8000"
    echo "📚 API文档:         http://localhost:8000/docs"
    echo "🗄️  Neo4j浏览器:    http://localhost:7474"
    echo "📦 MinIO控制台:     http://localhost:9001"
    echo "🐰 RabbitMQ管理:    http://localhost:15672"
    echo ""
    echo "默认登录信息请查看 .env 文件"
    echo ""
    log_success "COT Studio MVP 启动完成！"
}

# 主函数
main() {
    local env_type=${1:-dev}
    
    if [ "$env_type" != "dev" ] && [ "$env_type" != "prod" ]; then
        log_error "无效的环境类型: $env_type (支持: dev, prod)"
        exit 1
    fi
    
    log_info "开始启动 COT Studio MVP ($env_type 环境)..."
    
    check_dependencies
    create_directories
    init_env "$env_type"
    start_services "$env_type"
}

# 脚本入口
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi