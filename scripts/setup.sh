#!/bin/bash

# COT Studio MVP 一键安装脚本
# 支持 Linux, macOS, Windows (WSL)

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        *)          MACHINE="UNKNOWN:${OS}"
    esac
    log_info "检测到操作系统: $MACHINE"
    
    # 检查Docker
    if ! command_exists docker; then
        log_error "Docker 未安装，请先安装 Docker"
        log_info "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Docker版本
    DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "Docker 版本: $DOCKER_VERSION"
    
    # 检查Docker Compose
    if ! command_exists docker-compose; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        log_info "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 检查Docker Compose版本
    COMPOSE_VERSION=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "Docker Compose 版本: $COMPOSE_VERSION"
    
    # 检查Git
    if ! command_exists git; then
        log_error "Git 未安装，请先安装 Git"
        exit 1
    fi
    
    # 检查磁盘空间 (至少需要5GB)
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    REQUIRED_SPACE=5242880  # 5GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "磁盘空间不足，至少需要 5GB 可用空间"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 检查端口占用
check_ports() {
    log_info "检查端口占用..."
    
    PORTS=(3000 8000 5432 7474 6379 9000 5672 15672 9001 5555)
    OCCUPIED_PORTS=()
    
    for port in "${PORTS[@]}"; do
        if command_exists netstat; then
            if netstat -tuln | grep -q ":$port "; then
                OCCUPIED_PORTS+=($port)
            fi
        elif command_exists ss; then
            if ss -tuln | grep -q ":$port "; then
                OCCUPIED_PORTS+=($port)
            fi
        fi
    done
    
    if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
        log_warning "以下端口被占用: ${OCCUPIED_PORTS[*]}"
        log_warning "这可能会导致服务启动失败"
        read -p "是否继续安装? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "安装已取消"
            exit 1
        fi
    else
        log_success "端口检查通过"
    fi
}

# 创建环境配置
setup_environment() {
    log_info "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "已创建 .env 文件"
        else
            log_info "创建默认 .env 文件..."
            cat > .env << EOF
# 数据库配置
POSTGRES_DB=cotdb
POSTGRES_USER=cotuser
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Neo4j配置
NEO4J_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Redis配置
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# MinIO配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# RabbitMQ配置
RABBITMQ_USER=cotuser
RABBITMQ_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# JWT配置
JWT_SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 应用配置
DEBUG=false
LOG_LEVEL=INFO

# LLM API配置 (请填入您的API密钥)
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
EOF
            log_success "已创建默认 .env 文件"
        fi
    else
        log_info ".env 文件已存在，跳过创建"
    fi
    
    # 提示用户配置API密钥
    log_warning "请编辑 .env 文件，配置您的 LLM API 密钥:"
    log_info "  - OPENAI_API_KEY: OpenAI API 密钥"
    log_info "  - DEEPSEEK_API_KEY: DeepSeek API 密钥"
}

# 构建和启动服务
build_and_start() {
    log_info "构建 Docker 镜像..."
    docker-compose build
    
    log_info "启动服务..."
    docker-compose up -d
    
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose ps
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    # 等待服务完全启动
    log_info "等待服务完全启动 (可能需要几分钟)..."
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "后端服务启动成功"
            break
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        log_info "等待后端服务启动... ($ATTEMPT/$MAX_ATTEMPTS)"
        sleep 10
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        log_error "后端服务启动超时"
        log_info "请检查日志: docker-compose logs backend"
        return 1
    fi
    
    # 检查前端服务
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        log_success "前端服务启动成功"
    else
        log_warning "前端服务可能未完全启动，请稍后检查"
    fi
    
    # 执行数据库迁移
    log_info "执行数据库迁移..."
    docker-compose exec -T backend alembic upgrade head
    
    log_success "安装验证完成"
}

# 显示访问信息
show_access_info() {
    log_success "COT Studio MVP 安装完成!"
    echo
    echo "访问地址:"
    echo "  前端应用:        http://localhost:3000"
    echo "  后端API:         http://localhost:8000"
    echo "  API文档:         http://localhost:8000/docs"
    echo "  Neo4j浏览器:     http://localhost:7474"
    echo "  MinIO控制台:     http://localhost:9001"
    echo "  RabbitMQ管理:    http://localhost:15672"
    echo "  Celery监控:      http://localhost:5555"
    echo
    echo "常用命令:"
    echo "  查看服务状态:    make health-check"
    echo "  查看日志:        make logs"
    echo "  停止服务:        make docker-down"
    echo "  重启服务:        make docker-up"
    echo "  创建备份:        make backup"
    echo
    echo "更多信息请查看文档: docs/README.md"
}

# 主函数
main() {
    echo "========================================"
    echo "    COT Studio MVP 一键安装脚本"
    echo "========================================"
    echo
    
    # 检查是否在项目根目录
    if [ ! -f "docker-compose.yml" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    check_requirements
    check_ports
    setup_environment
    build_and_start
    
    if verify_installation; then
        show_access_info
    else
        log_error "安装验证失败，请检查日志并重试"
        log_info "查看日志: make logs"
        log_info "重新安装: make clean && ./scripts/setup.sh"
        exit 1
    fi
}

# 错误处理
trap 'log_error "安装过程中发生错误，请检查上面的错误信息"' ERR

# 运行主函数
main "$@"