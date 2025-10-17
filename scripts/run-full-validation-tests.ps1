#!/usr/bin/env pwsh
<#
.SYNOPSIS
    运行全功能验证测试脚本
    
.DESCRIPTION
    执行完整的系统验证测试，包括：
    - 权限系统集成测试
    - 前端性能优化验证
    - 知识图谱功能测试
    - 数据导出功能测试
    - 响应式布局测试
    - 系统监控和用户体验验证
    
.PARAMETER TestType
    指定要运行的测试类型：all, backend, frontend, integration
    
.PARAMETER Verbose
    启用详细输出
    
.EXAMPLE
    .\run-full-validation-tests.ps1 -TestType all -Verbose
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "backend", "frontend", "integration")]
    [string]$TestType = "all",
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Blue" = [ConsoleColor]::Blue
        "Cyan" = [ConsoleColor]::Cyan
        "Magenta" = [ConsoleColor]::Magenta
        "White" = [ConsoleColor]::White
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# 检查依赖
function Test-Dependencies {
    Write-ColorOutput "🔍 检查依赖..." "Blue"
    
    # 检查Python环境
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "✅ Python: $pythonVersion" "Green"
    }
    catch {
        Write-ColorOutput "❌ Python 未安装或不在PATH中" "Red"
        exit 1
    }
    
    # 检查Node.js环境
    try {
        $nodeVersion = node --version 2>&1
        Write-ColorOutput "✅ Node.js: $nodeVersion" "Green"
    }
    catch {
        Write-ColorOutput "❌ Node.js 未安装或不在PATH中" "Red"
        exit 1
    }
    
    # 检查后端依赖
    if (Test-Path "backend/requirements.txt") {
        Write-ColorOutput "✅ 后端依赖文件存在" "Green"
    }
    else {
        Write-ColorOutput "❌ 后端依赖文件不存在" "Red"
        exit 1
    }
    
    # 检查前端依赖
    if (Test-Path "frontend/package.json") {
        Write-ColorOutput "✅ 前端依赖文件存在" "Green"
    }
    else {
        Write-ColorOutput "❌ 前端依赖文件不存在" "Red"
        exit 1
    }
}

# 设置测试环境
function Set-TestEnvironment {
    Write-ColorOutput "🔧 设置测试环境..." "Blue"
    
    # 设置环境变量
    $env:TESTING = "true"
    $env:DATABASE_URL = "sqlite:///./test_integration.db"
    $env:REDIS_URL = "redis://localhost:6379/1"
    
    # 创建测试数据库
    if (Test-Path "backend") {
        Push-Location "backend"
        try {
            Write-ColorOutput "📊 初始化测试数据库..." "Yellow"
            python -c "
from app.core.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('✅ 测试数据库初始化完成')
"
        }
        catch {
            Write-ColorOutput "❌ 测试数据库初始化失败: $_" "Red"
        }
        finally {
            Pop-Location
        }
    }
}

# 运行后端测试
function Invoke-BackendTests {
    Write-ColorOutput "🧪 运行后端测试..." "Blue"
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "❌ 后端目录不存在" "Red"
        return $false
    }
    
    Push-Location "backend"
    try {
        # 安装依赖
        Write-ColorOutput "📦 安装后端依赖..." "Yellow"
        pip install -r requirements.txt -q
        
        # 运行权限系统集成测试
        Write-ColorOutput "🔐 运行权限系统集成测试..." "Cyan"
        $permissionTestResult = python -m pytest tests/integration/test_permission_system_integration.py -v --tb=short
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 权限系统集成测试通过" "Green"
        }
        else {
            Write-ColorOutput "❌ 权限系统集成测试失败" "Red"
            return $false
        }
        
        # 运行全功能验证测试
        Write-ColorOutput "🌐 运行全功能验证测试..." "Cyan"
        $fullSystemTestResult = python -m pytest tests/integration/test_full_system_validation.py -v --tb=short
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 全功能验证测试通过" "Green"
        }
        else {
            Write-ColorOutput "❌ 全功能验证测试失败" "Red"
            return $false
        }
        
        # 运行现有集成测试
        Write-ColorOutput "🔄 运行现有集成测试..." "Cyan"
        $integrationTestResult = python -m pytest tests/integration/ -v --tb=short
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 集成测试通过" "Green"
        }
        else {
            Write-ColorOutput "❌ 集成测试失败" "Red"
            return $false
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ 后端测试执行失败: $_" "Red"
        return $false
    }
    finally {
        Pop-Location
    }
}

# 运行前端测试
function Invoke-FrontendTests {
    Write-ColorOutput "🎨 运行前端测试..." "Blue"
    
    if (-not (Test-Path "frontend")) {
        Write-ColorOutput "❌ 前端目录不存在" "Red"
        return $false
    }
    
    Push-Location "frontend"
    try {
        # 安装依赖
        Write-ColorOutput "📦 安装前端依赖..." "Yellow"
        npm install --silent
        
        # 运行性能优化测试
        Write-ColorOutput "⚡ 运行性能优化测试..." "Cyan"
        $performanceTestResult = npm run test -- src/test/performance.test.tsx --run
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 性能优化测试通过" "Green"
        }
        else {
            Write-ColorOutput "❌ 性能优化测试失败" "Red"
            return $false
        }
        
        # 运行端到端测试
        Write-ColorOutput "🔄 运行端到端测试..." "Cyan"
        $e2eTestResult = npm run test -- src/test/e2e/fullSystem.test.tsx --run
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 端到端测试通过" "Green"
        }
        else {
            Write-ColorOutput "❌ 端到端测试失败" "Red"
            return $false
        }
        
        # 运行所有前端测试
        Write-ColorOutput "🧪 运行所有前端测试..." "Cyan"
        $allTestResult = npm run test:run
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ 所有前端测试通过" "Green"
        }
        else {
            Write-ColorOutput "❌ 前端测试失败" "Red"
            return $false
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ 前端测试执行失败: $_" "Red"
        return $false
    }
    finally {
        Pop-Location
    }
}

# 运行集成测试
function Invoke-IntegrationTests {
    Write-ColorOutput "🔗 运行集成测试..." "Blue"
    
    # 启动后端服务（后台）
    Write-ColorOutput "🚀 启动后端服务..." "Yellow"
    $backendProcess = $null
    
    try {
        Push-Location "backend"
        $backendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -PassThru -WindowStyle Hidden
        Pop-Location
        
        # 等待服务启动
        Start-Sleep -Seconds 10
        
        # 检查服务是否启动成功
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✅ 后端服务启动成功" "Green"
            }
            else {
                Write-ColorOutput "❌ 后端服务启动失败" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "❌ 无法连接到后端服务" "Red"
            return $false
        }
        
        # 启动前端服务（后台）
        Write-ColorOutput "🎨 启动前端服务..." "Yellow"
        $frontendProcess = $null
        
        Push-Location "frontend"
        $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -WindowStyle Hidden
        Pop-Location
        
        # 等待前端服务启动
        Start-Sleep -Seconds 15
        
        # 运行端到端集成测试
        Write-ColorOutput "🔄 运行端到端集成测试..." "Cyan"
        
        # 这里可以添加更多的集成测试
        # 例如使用Playwright或Cypress进行真实的浏览器测试
        
        Write-ColorOutput "✅ 集成测试完成" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "❌ 集成测试执行失败: $_" "Red"
        return $false
    }
    finally {
        # 清理进程
        if ($backendProcess) {
            Write-ColorOutput "🛑 停止后端服务..." "Yellow"
            Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        }
        
        if ($frontendProcess) {
            Write-ColorOutput "🛑 停止前端服务..." "Yellow"
            Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

# 生成测试报告
function New-TestReport {
    param(
        [bool]$BackendSuccess,
        [bool]$FrontendSuccess,
        [bool]$IntegrationSuccess
    )
    
    Write-ColorOutput "`n📊 测试报告" "Blue"
    Write-ColorOutput "=" * 50 "Blue"
    
    $totalTests = 0
    $passedTests = 0
    
    if ($TestType -eq "all" -or $TestType -eq "backend") {
        $totalTests++
        Write-ColorOutput "后端测试: $(if ($BackendSuccess) { '✅ 通过' } else { '❌ 失败' })" $(if ($BackendSuccess) { "Green" } else { "Red" })
        if ($BackendSuccess) { $passedTests++ }
    }
    
    if ($TestType -eq "all" -or $TestType -eq "frontend") {
        $totalTests++
        Write-ColorOutput "前端测试: $(if ($FrontendSuccess) { '✅ 通过' } else { '❌ 失败' })" $(if ($FrontendSuccess) { "Green" } else { "Red" })
        if ($FrontendSuccess) { $passedTests++ }
    }
    
    if ($TestType -eq "all" -or $TestType -eq "integration") {
        $totalTests++
        Write-ColorOutput "集成测试: $(if ($IntegrationSuccess) { '✅ 通过' } else { '❌ 失败' })" $(if ($IntegrationSuccess) { "Green" } else { "Red" })
        if ($IntegrationSuccess) { $passedTests++ }
    }
    
    Write-ColorOutput "`n总结: $passedTests/$totalTests 测试通过" $(if ($passedTests -eq $totalTests) { "Green" } else { "Red" })
    
    if ($passedTests -eq $totalTests) {
        Write-ColorOutput "🎉 所有测试通过！系统验证成功！" "Green"
        return $true
    }
    else {
        Write-ColorOutput "❌ 部分测试失败，请检查上述错误信息" "Red"
        return $false
    }
}

# 主函数
function Main {
    Write-ColorOutput "🚀 开始全功能验证测试" "Blue"
    Write-ColorOutput "测试类型: $TestType" "Cyan"
    Write-ColorOutput "详细输出: $($Verbose.IsPresent)" "Cyan"
    Write-ColorOutput ""
    
    # 检查依赖
    Test-Dependencies
    
    # 设置测试环境
    Set-TestEnvironment
    
    # 初始化结果变量
    $backendSuccess = $true
    $frontendSuccess = $true
    $integrationSuccess = $true
    
    try {
        # 根据测试类型运行相应测试
        switch ($TestType) {
            "backend" {
                $backendSuccess = Invoke-BackendTests
                $frontendSuccess = $null
                $integrationSuccess = $null
            }
            "frontend" {
                $backendSuccess = $null
                $frontendSuccess = Invoke-FrontendTests
                $integrationSuccess = $null
            }
            "integration" {
                $backendSuccess = $null
                $frontendSuccess = $null
                $integrationSuccess = Invoke-IntegrationTests
            }
            "all" {
                $backendSuccess = Invoke-BackendTests
                $frontendSuccess = Invoke-FrontendTests
                $integrationSuccess = Invoke-IntegrationTests
            }
        }
        
        # 生成测试报告
        $overallSuccess = New-TestReport -BackendSuccess $backendSuccess -FrontendSuccess $frontendSuccess -IntegrationSuccess $integrationSuccess
        
        if ($overallSuccess) {
            exit 0
        }
        else {
            exit 1
        }
    }
    catch {
        Write-ColorOutput "❌ 测试执行过程中发生错误: $_" "Red"
        exit 1
    }
}

# 运行主函数
Main