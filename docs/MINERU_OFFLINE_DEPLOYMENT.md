# MinerU 离线部署方案 - 完整指南

本方案分为两个阶段:
1. **准备阶段**: 在网络正常的环境准备镜像
2. **部署阶段**: 在目标服务器加载和运行镜像

---

## 第一阶段: 准备镜像 (需要良好网络)

### 方案 A: 在其他网络正常的机器上准备

如果您有另一台网络良好的电脑:

```powershell
# 1. 克隆或复制项目到网络正常的机器
cd E:\Chris\Document\OneDrive\Project\cotstudio

# 2. 构建所有镜像
docker-compose build

# 3. 导出镜像
docker save -o mineru-image.tar cotstudio-mineru:latest
docker save -o backend-image.tar cotstudio-backend:latest
docker save -o frontend-image.tar cotstudio-frontend:latest

# 4. 导出基础镜像(可选,如果目标机器没有)
docker save -o postgres.tar postgres:15-alpine
docker save -o redis.tar redis:7-alpine
docker save -o neo4j.tar neo4j:5.25-community
docker save -o minio.tar minio/minio:latest
docker save -o rabbitmq.tar rabbitmq:3.12-management-alpine

# 5. 传输所有.tar文件到目标服务器
# 使用U盘、网络共享、或其他传输方式
```

### 方案 B: 使用云服务器临时构建

```bash
# 1. 在云服务器(如阿里云、腾讯云)上
git clone <your-repo>
cd cotstudio

# 2. 构建镜像
docker-compose build

# 3. 导出镜像
docker save -o mineru-image.tar cotstudio-mineru:latest

# 4. 下载到本地
scp user@cloud-server:/path/to/mineru-image.tar ./

# 5. 传输到目标服务器
```

---

## 第二阶段: 目标服务器部署

### 步骤 1: 加载镜像

```powershell
# 进入包含.tar文件的目录
cd E:\path\to\docker\images

# 加载应用镜像
docker load -i mineru-image.tar
docker load -i backend-image.tar
docker load -i frontend-image.tar

# 加载基础镜像(如果需要)
docker load -i postgres.tar
docker load -i redis.tar
docker load -i neo4j.tar
docker load -i minio.tar
docker load -i rabbitmq.tar
```

### 步骤 2: 验证镜像

```powershell
# 查看已加载的镜像
docker images

# 应该看到类似输出:
# REPOSITORY              TAG       IMAGE ID       CREATED        SIZE
# cotstudio-mineru        latest    xxx            2 hours ago    2.5GB
# cotstudio-backend       latest    xxx            2 hours ago    800MB
# cotstudio-frontend      latest    xxx            2 hours ago    200MB
# postgres                15-alpine xxx            1 week ago     230MB
# ...
```

### 步骤 3: 启动服务

```powershell
# 进入项目目录
cd E:\Chris\Document\OneDrive\Project\cotstudio

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看MinerU日志
docker-compose logs -f mineru
```

---

## 当前推荐方案: 使用预构建镜像

由于您的网络环境问题,我建议:

### 选项 1: 使用Python官方镜像 + 手动安装MinerU

不构建自定义镜像,直接运行容器并在容器内安装:

```powershell
# 1. 启动临时Python容器
docker run -it --name mineru-temp python:3.10-slim bash

# 在容器内执行:
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install mineru>=2.5.0 fastapi uvicorn python-multipart opencv-python-headless requests torch

# 2. 在另一个终端,将容器保存为镜像
docker commit mineru-temp cotstudio-mineru:latest

# 3. 清理临时容器
docker rm mineru-temp

# 4. 现在可以启动服务了
docker-compose up -d mineru
```

### 选项 2: 简化构建(最推荐)

修改Dockerfile为最简化版本,只依赖pip安装,不需要apt:

**创建 `docker/mineru/Dockerfile.minimal`:**

```dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 只通过pip安装,不使用apt
RUN pip install --no-cache-dir \
    mineru \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    opencv-python-headless \
    requests \
    torch

COPY mineru_service.py /app/

RUN mkdir -p /app/models /app/temp /app/output && \
    useradd -m mineru && \
    chown -R mineru:mineru /app

USER mineru

EXPOSE 8001

CMD ["python", "mineru_service.py"]
```

**修改 `docker-compose.yml`:**

```yaml
services:
  mineru:
    build:
      context: ./docker/mineru
      dockerfile: Dockerfile.minimal
    # ... 其他配置
```

**执行构建:**

```powershell
# 确保代理环境变量仍然设置
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0

# 构建
docker-compose build mineru
```

---

## 完整自动化脚本

我为您创建一个自动化脚本:

```powershell
# deploy-mineru-offline.ps1

Write-Host "MinerU 离线部署助手" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

$currentDir = Get-Location

# 检查是否有预构建镜像
if (Test-Path ".\mineru-image.tar") {
    Write-Host "[选项 1] 发现预构建镜像文件" -ForegroundColor Green
    $useExisting = Read-Host "是否加载 mineru-image.tar? (Y/N)"
    
    if ($useExisting -eq "Y" -or $useExisting -eq "y") {
        Write-Host "正在加载镜像..." -ForegroundColor Yellow
        docker load -i mineru-image.tar
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 镜像加载成功!" -ForegroundColor Green
            Write-Host "`n启动服务..." -ForegroundColor Cyan
            docker-compose up -d mineru
            
            Write-Host "`n查看日志:" -ForegroundColor Cyan
            Write-Host "  docker-compose logs -f mineru" -ForegroundColor White
            exit 0
        }
    }
}

# 检查Python基础镜像
Write-Host "`n[选项 2] 使用Python基础镜像构建" -ForegroundColor Green
docker images python:3.10-slim --format "{{.Repository}}" | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Python镜像不存在,尝试拉取..." -ForegroundColor Yellow
    docker pull python:3.10-slim
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 无法拉取Python镜像" -ForegroundColor Red
        Write-Host "请在网络正常的机器上执行: docker save -o python-3.10-slim.tar python:3.10-slim" -ForegroundColor Yellow
        exit 1
    }
}

# 设置构建环境
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0

Write-Host "使用 Dockerfile.minimal 构建..." -ForegroundColor Yellow

# 构建
docker-compose build mineru

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 构建成功!" -ForegroundColor Green
    
    # 询问是否导出镜像
    $export = Read-Host "`n是否导出镜像以备后用? (Y/N)"
    if ($export -eq "Y" -or $export -eq "y") {
        docker save -o mineru-image.tar cotstudio-mineru:latest
        Write-Host "✅ 镜像已导出为 mineru-image.tar" -ForegroundColor Green
    }
    
    # 启动服务
    Write-Host "`n启动服务..." -ForegroundColor Cyan
    docker-compose up -d mineru
    
    Write-Host "`n查看日志:" -ForegroundColor Cyan
    Write-Host "  docker-compose logs -f mineru" -ForegroundColor White
} else {
    Write-Host "`n❌ 构建失败" -ForegroundColor Red
    Write-Host "请检查网络连接或使用离线镜像文件" -ForegroundColor Yellow
}
```

---

## 立即可执行的步骤

### 最简单的方案:

```powershell
# 1. 确保已有Python镜像
docker images python:3.10-slim

# 2. 创建最简化Dockerfile (见上方)
# 文件保存为: docker/mineru/Dockerfile.minimal

# 3. 修改docker-compose.yml使用Dockerfile.minimal

# 4. 禁用BuildKit
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0

# 5. 构建
docker-compose build mineru

# 6. 启动
docker-compose up -d mineru
```

---

## 故障排除

### 问题: pip install 仍然超时

**解决**: 在容器内手动安装

```powershell
# 1. 启动交互式容器
docker run -it --name mineru-build python:3.10-slim bash

# 2. 在容器内:
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.timeout 300
pip install mineru fastapi uvicorn python-multipart opencv-python-headless requests torch --no-cache-dir

# 3. 退出容器 (Ctrl+D)

# 4. 保存为镜像
docker commit mineru-build cotstudio-mineru:latest

# 5. 清理
docker rm mineru-build
```

### 问题: 镜像文件太大

**解决**: 分别传输

- mineru-image.tar: ~2-3GB
- backend-image.tar: ~800MB  
- frontend-image.tar: ~200MB

可以分批传输或压缩:
```powershell
# 压缩镜像
tar -czf mineru-image.tar.gz mineru-image.tar

# 解压
tar -xzf mineru-image.tar.gz
```

---

## 下一步

执行我为您创建的自动化脚本:

```powershell
# 保存上面的脚本为:
# scripts/deploy-mineru-offline.ps1

# 然后执行:
.\scripts\deploy-mineru-offline.ps1
```

或者按照"最简单的方案"手动执行步骤。

需要我现在为您创建这些文件吗? 🚀
