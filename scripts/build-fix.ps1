# COT Studio MVP Docker 构建修复脚本
# 解决 pip install 失败问题

param(
    [switch]$UseMinimal,
    [switch]$UseLatest,
    [switch]$StepByStep,
    [switch]$InfraOnly,
    [switch]$TestPackages
)

Write-Host "🔧 COT Studio MVP 构建修复脚本" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# 检查 Docker 是否运行
try {
    docker --version | Out-Null
    Write-Host "✅ Docker 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装或未运行" -ForegroundColor Red
    exit 1
}

# 设置 PyPI 镜像源
Write-Host ""
Write-Host "🌐 配置 PyPI 镜像源..." -ForegroundColor Yellow
$env:PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
$env:PIP_TRUSTED_HOST = "pypi.tuna.tsinghua.edu.cn"
Write-Host "✅ 已设置清华大学 PyPI 镜像源" -ForegroundColor Green

if ($InfraOnly) {
    Write-Host ""
    Write-Host "🏗️  只启动基础设施服务..." -ForegroundColor Yellow
    docker-compose up -d postgres redis neo4j minio rabbitmq
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 基础设施服务启动成功" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 接下来可以本地运行前后端:" -ForegroundColor Cyan
        Write-Host "1. 后端: cd backend && python -m venv venv && .\venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --reload" -ForegroundColor White
        Write-Host "2. 前端: cd frontend && npm install && npm run dev" -ForegroundColor White
    } else {
        Write-Host "❌ 基础设施服务启动失败" -ForegroundColor Red
    }
    exit 0
}

if ($TestPackages) {
    Write-Host ""
    Write-Host "🧪 测试包安装..." -ForegroundColor Yellow
    .\scripts\test-packages.ps1 -TestAll -GenerateFixed
    
    $useFixed = Read-Host "是否使用生成的修复文件? (y/N)"
    if ($useFixed -eq "y" -or $useFixed -eq "Y") {
        if (Test-Path "backend/requirements-fixed.txt") {
            Copy-Item "backend/requirements.txt" "backend/requirements.txt.backup"
            Copy-Item "backend/requirements-fixed.txt" "backend/requirements.txt"
            Write-Host "✅ 已切换到修复后的依赖" -ForegroundColor Green
        }
    }
}

if ($UseLatest) {
    Write-Host ""
    Write-Host "🚀 使用最新版本依赖构建..." -ForegroundColor Yellow
    
    # 备份原始 requirements.txt
    if (Test-Path "backend/requirements.txt.backup") {
        Write-Host "发现备份文件，跳过备份" -ForegroundColor Cyan
    } else {
        Copy-Item "backend/requirements.txt" "backend/requirements.txt.backup"
        Write-Host "✅ 已备份原始 requirements.txt" -ForegroundColor Green
    }
    
    # 使用最新版本依赖
    Copy-Item "backend/requirements-latest.txt" "backend/requirements.txt"
    Write-Host "✅ 已切换到最新版本依赖 (移除问题包)" -ForegroundColor Green
}

if ($UseMinimal) {
    Write-Host ""
    Write-Host "📦 使用最小化依赖构建..." -ForegroundColor Yellow
    
    # 备份原始 requirements.txt
    if (Test-Path "backend/requirements.txt.backup") {
        Write-Host "发现备份文件，跳过备份" -ForegroundColor Cyan
    } else {
        Copy-Item "backend/requirements.txt" "backend/requirements.txt.backup"
        Write-Host "✅ 已备份原始 requirements.txt" -ForegroundColor Green
    }
    
    # 使用最小化依赖
    Copy-Item "backend/requirements-minimal.txt" "backend/requirements.txt"
    Write-Host "✅ 已切换到最小化依赖" -ForegroundColor Green
}

if ($StepByStep) {
    Write-Host ""
    Write-Host "🔨 分步构建..." -ForegroundColor Yellow
    
    Write-Host "正在构建后端..." -ForegroundColor Cyan
    docker-compose build --no-cache backend
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 后端构建成功" -ForegroundColor Green
        
        Write-Host "正在构建前端..." -ForegroundColor Cyan
        docker-compose build --no-cache frontend
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 前端构建成功" -ForegroundColor Green
        } else {
            Write-Host "❌ 前端构建失败" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ 后端构建失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 建议尝试:" -ForegroundColor Yellow
        Write-Host "1. 使用最新版本依赖: .\scripts\build-fix.ps1 -UseLatest -StepByStep" -ForegroundColor White
        Write-Host "2. 测试并修复包: .\scripts\build-fix.ps1 -TestPackages" -ForegroundColor White
        Write-Host "3. 使用最小化依赖: .\scripts\build-fix.ps1 -UseMinimal -StepByStep" -ForegroundColor White
        Write-Host "4. 只启动基础设施: .\scripts\build-fix.ps1 -InfraOnly" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "🔨 清理并重新构建..." -ForegroundColor Yellow
    
    # 清理 Docker 缓存
    Write-Host "清理 Docker 缓存..." -ForegroundColor Cyan
    docker system prune -f
    
    # 重新构建
    Write-Host "重新构建所有服务..." -ForegroundColor Cyan
    docker-compose build --no-cache
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🚀 启动所有服务..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 构建和启动成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 服务状态:" -ForegroundColor Cyan
        docker-compose ps
        
        Write-Host ""
        Write-Host "🌐 访问地址:" -ForegroundColor Cyan
        Write-Host "- 前端: http://localhost:3000" -ForegroundColor White
        Write-Host "- 后端: http://localhost:8000" -ForegroundColor White
        Write-Host "- API文档: http://localhost:8000/docs" -ForegroundColor White
    } else {
        Write-Host "❌ 服务启动失败" -ForegroundColor Red
        Write-Host "查看日志: docker-compose logs" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "❌ 构建失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 建议尝试:" -ForegroundColor Yellow
    Write-Host "1. 使用最新版本依赖: .\scripts\build-fix.ps1 -UseLatest" -ForegroundColor White
    Write-Host "2. 测试并修复包: .\scripts\build-fix.ps1 -TestPackages" -ForegroundColor White
    Write-Host "3. 使用最小化依赖: .\scripts\build-fix.ps1 -UseMinimal" -ForegroundColor White
    Write-Host "4. 分步构建: .\scripts\build-fix.ps1 -StepByStep" -ForegroundColor White
    Write-Host "5. 只启动基础设施: .\scripts\build-fix.ps1 -InfraOnly" -ForegroundColor White
}

# 恢复原始 requirements.txt (如果修改了依赖文件)
if (($UseMinimal -or $UseLatest -or $TestPackages) -and (Test-Path "backend/requirements.txt.backup")) {
    Write-Host ""
    $restore = Read-Host "是否恢复原始 requirements.txt? (y/N)"
    if ($restore -eq "y" -or $restore -eq "Y") {
        Copy-Item "backend/requirements.txt.backup" "backend/requirements.txt"
        Remove-Item "backend/requirements.txt.backup"
        Write-Host "✅ 已恢复原始 requirements.txt" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✨ 构建修复脚本执行完成" -ForegroundColor Green