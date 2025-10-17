# COT Studio MVP 网络配置脚本
# 解决 Docker 镜像下载问题

param(
    [string]$ProxyPort = "10808",
    [switch]$SkipProxy,
    [switch]$PullImages
)

Write-Host "🌐 COT Studio MVP 网络配置脚本" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# 检查 Docker 是否运行
try {
    docker --version | Out-Null
    Write-Host "✅ Docker 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装或未运行，请先安装 Docker Desktop" -ForegroundColor Red
    exit 1
}

if (-not $SkipProxy) {
    Write-Host ""
    Write-Host "🔧 配置代理设置..." -ForegroundColor Yellow
    
    # 设置环境变量
    $env:HTTP_PROXY = "http://127.0.0.1:$ProxyPort"
    $env:HTTPS_PROXY = "http://127.0.0.1:$ProxyPort"
    
    Write-Host "✅ 已设置代理: http://127.0.0.1:$ProxyPort" -ForegroundColor Green
    Write-Host "💡 请确保你的代理软件正在运行在端口 $ProxyPort" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "📋 Docker Desktop 代理配置提示:" -ForegroundColor Yellow
    Write-Host "1. 打开 Docker Desktop" -ForegroundColor White
    Write-Host "2. 进入 Settings → Resources → Proxies" -ForegroundColor White
    Write-Host "3. 设置 HTTP Proxy: http://127.0.0.1:$ProxyPort" -ForegroundColor White
    Write-Host "4. 设置 HTTPS Proxy: http://127.0.0.1:$ProxyPort" -ForegroundColor White
    Write-Host "5. 点击 Apply & Restart" -ForegroundColor White
    
    $continue = Read-Host "`n是否已完成 Docker Desktop 代理配置? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "⏸️  请完成 Docker Desktop 代理配置后重新运行此脚本" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "📦 预拉取 Docker 镜像..." -ForegroundColor Yellow

# 定义需要的镜像
$images = @(
    "python:3.11-slim",
    "node:18-alpine", 
    "postgres:15",
    "neo4j:latest",
    "redis:7-alpine",
    "minio/minio:latest",
    "rabbitmq:3-management"
)

$success = 0
$total = $images.Count

foreach ($image in $images) {
    Write-Host "正在拉取 $image..." -ForegroundColor Cyan
    try {
        docker pull $image
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $image 拉取成功" -ForegroundColor Green
            $success++
        } else {
            Write-Host "❌ $image 拉取失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $image 拉取失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📊 镜像拉取结果: $success/$total 成功" -ForegroundColor $(if ($success -eq $total) { "Green" } else { "Yellow" })

if ($success -eq $total) {
    Write-Host ""
    Write-Host "🎉 所有镜像拉取成功！现在可以启动服务了:" -ForegroundColor Green
    Write-Host "docker-compose up -d" -ForegroundColor Cyan
} elseif ($success -gt 0) {
    Write-Host ""
    Write-Host "⚠️  部分镜像拉取失败，但可以尝试启动服务:" -ForegroundColor Yellow
    Write-Host "docker-compose up -d" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 如果启动失败，请检查:" -ForegroundColor Cyan
    Write-Host "1. 代理设置是否正确" -ForegroundColor White
    Write-Host "2. 网络连接是否稳定" -ForegroundColor White
    Write-Host "3. 尝试使用国内镜像源" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ 所有镜像拉取失败，请检查网络配置" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 建议解决方案:" -ForegroundColor Yellow
    Write-Host "1. 检查代理软件是否运行在端口 $ProxyPort" -ForegroundColor White
    Write-Host "2. 确认 Docker Desktop 代理配置正确" -ForegroundColor White
    Write-Host "3. 尝试使用不同的代理端口" -ForegroundColor White
    Write-Host "4. 配置 Docker 镜像源 (阿里云、腾讯云等)" -ForegroundColor White
}

Write-Host ""
Write-Host "📚 更多帮助信息请查看:" -ForegroundColor Cyan
Write-Host "- PROJECT_GUIDE.md (完整网络配置指南)" -ForegroundColor White
Write-Host "- docs/TROUBLESHOOTING.md (故障排除)" -ForegroundColor White

Write-Host ""
Write-Host "✨ 网络配置脚本执行完成" -ForegroundColor Green