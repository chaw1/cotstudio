# COT Studio MVP Docker 部署修复脚本
# 解决 Docker 构建卡住的问题

param(
    [switch]$ForceKill,
    [switch]$CleanAll,
    [switch]$QuickStart,
    [switch]$InfraOnly
)

Write-Host "🚀 COT Studio MVP Docker 部署修复脚本" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

if ($ForceKill) {
    Write-Host ""
    Write-Host "💀 强制停止所有 Docker 进程..." -ForegroundColor Red
    
    # 停止所有容器
    Write-Host "停止所有容器..." -ForegroundColor Yellow
    docker stop $(docker ps -aq) 2>$null
    
    # 删除所有容器
    Write-Host "删除所有容器..." -ForegroundColor Yellow
    docker rm $(docker ps -aq) 2>$null
    
    # 停止 Docker 构建进程
    Write-Host "停止构建进程..." -ForegroundColor Yellow
    Get-Process | Where-Object {$_.ProcessName -like "*docker*"} | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ 已强制停止所有 Docker 进程" -ForegroundColor Green
}

if ($CleanAll) {
    Write-Host ""
    Write-Host "🧹 清理所有 Docker 资源..." -ForegroundColor Yellow
    
    # 停止所有服务
    docker-compose down -v --remove-orphans 2>$null
    
    # 清理系统
    docker system prune -af --volumes
    
    # 清理构建缓存
    docker builder prune -af
    
    Write-Host "✅ Docker 资源清理完成" -ForegroundColor Green
}

if ($QuickStart) {
    Write-Host ""
    Write-Host "⚡ 快速启动模式..." -ForegroundColor Yellow
    
    # 设置环境变量
    $env:COMPOSE_HTTP_TIMEOUT = "300"
    $env:DOCKER_CLIENT_TIMEOUT = "300"
    
    # 设置 PyPI 镜像源
    $env:PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
    $env:PIP_TRUSTED_HOST = "pypi.tuna.tsinghua.edu.cn"
    
    Write-Host "正在启动服务 (超时时间: 5分钟)..." -ForegroundColor Cyan
    
    # 使用超时启动
    $job = Start-Job -ScriptBlock {
        docker-compose up -d --build
    }
    
    if (Wait-Job $job -Timeout 300) {
        $result = Receive-Job $job
        Write-Host $result
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 服务启动成功" -ForegroundColor Green
        } else {
            Write-Host "❌ 服务启动失败" -ForegroundColor Red
        }
    } else {
        Write-Host "⏰ 启动超时，正在停止..." -ForegroundColor Yellow
        Stop-Job $job
        Remove-Job $job
        
        Write-Host "建议使用基础设施模式: .\scripts\docker-deploy-fix.ps1 -InfraOnly" -ForegroundColor Cyan
    }
}

if ($InfraOnly) {
    Write-Host ""
    Write-Host "🏗️  基础设施模式启动..." -ForegroundColor Yellow
    
    Write-Host "启动基础设施服务..." -ForegroundColor Cyan
    docker-compose up -d postgres redis neo4j minio rabbitmq
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 基础设施服务启动成功" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "📋 接下来的步骤:" -ForegroundColor Cyan
        Write-Host "1. 后端本地运行:" -ForegroundColor White
        Write-Host "   cd backend" -ForegroundColor Gray
        Write-Host "   python -m venv venv" -ForegroundColor Gray
        Write-Host "   .\venv\Scripts\activate" -ForegroundColor Gray
        Write-Host "   pip install -r requirements-latest.txt" -ForegroundColor Gray
        Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "2. 前端本地运行 (新终端):" -ForegroundColor White
        Write-Host "   cd frontend" -ForegroundColor Gray
        Write-Host "   npm install" -ForegroundColor Gray
        Write-Host "   npm run dev" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "🌐 服务地址:" -ForegroundColor Cyan
        Write-Host "- 前端: http://localhost:3000" -ForegroundColor White
        Write-Host "- 后端: http://localhost:8000" -ForegroundColor White
        Write-Host "- Neo4j: http://localhost:7474" -ForegroundColor White
        Write-Host "- MinIO: http://localhost:9001" -ForegroundColor White
        Write-Host "- RabbitMQ: http://localhost:15672" -ForegroundColor White
    } else {
        Write-Host "❌ 基础设施服务启动失败" -ForegroundColor Red
    }
}

# 默认行为：检查状态和提供建议
if (-not ($ForceKill -or $CleanAll -or $QuickStart -or $InfraOnly)) {
    Write-Host ""
    Write-Host "🔍 检查当前状态..." -ForegroundColor Yellow
    
    # 检查运行中的容器
    $runningContainers = docker ps --format "table {{.Names}}\t{{.Status}}"
    if ($runningContainers) {
        Write-Host ""
        Write-Host "📊 运行中的容器:" -ForegroundColor Cyan
        Write-Host $runningContainers
    }
    
    # 检查构建进程
    $dockerProcesses = Get-Process | Where-Object {$_.ProcessName -like "*docker*"}
    if ($dockerProcesses) {
        Write-Host ""
        Write-Host "⚙️  Docker 进程:" -ForegroundColor Cyan
        $dockerProcesses | Format-Table ProcessName, Id, CPU -AutoSize
    }
    
    Write-Host ""
    Write-Host "🔧 可用选项:" -ForegroundColor Cyan
    Write-Host "1. 强制停止所有进程: .\scripts\docker-deploy-fix.ps1 -ForceKill" -ForegroundColor White
    Write-Host "2. 清理所有资源: .\scripts\docker-deploy-fix.ps1 -CleanAll" -ForegroundColor White
    Write-Host "3. 快速启动: .\scripts\docker-deploy-fix.ps1 -QuickStart" -ForegroundColor White
    Write-Host "4. 基础设施模式: .\scripts\docker-deploy-fix.ps1 -InfraOnly" -ForegroundColor White
    
    Write-Host ""
    Write-Host "💡 如果构建卡住，建议顺序:" -ForegroundColor Yellow
    Write-Host "1. 先尝试: .\scripts\docker-deploy-fix.ps1 -ForceKill" -ForegroundColor White
    Write-Host "2. 然后: .\scripts\docker-deploy-fix.ps1 -CleanAll" -ForegroundColor White
    Write-Host "3. 最后: .\scripts\docker-deploy-fix.ps1 -InfraOnly" -ForegroundColor White
}

Write-Host ""
Write-Host "✨ Docker 部署修复脚本执行完成" -ForegroundColor Green