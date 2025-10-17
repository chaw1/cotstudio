# COT Studio MVP Windows Setup Script
# Version: 1.0.0
# Updated: 2025-09-15

param(
    [switch]$SkipChecks = $false,
    [switch]$NoProxy = $false,
    [switch]$Help = $false,
    [switch]$DevMode = $false
)

# Color definitions
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-Host "COT Studio MVP Windows Setup Script v1.0.0" -ForegroundColor Green
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  -SkipChecks    Skip system requirements and port checks"
    Write-Host "  -NoProxy       Skip proxy configuration prompt"
    Write-Host "  -DevMode       Setup for local development (infrastructure only)"
    Write-Host "  -Help          Show this help message"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup.ps1                    # Standard installation"
    Write-Host "  .\scripts\setup.ps1 -NoProxy           # Skip proxy setup"
    Write-Host "  .\scripts\setup.ps1 -DevMode           # Development mode (infrastructure only)"
    Write-Host "  .\scripts\setup.ps1 -SkipChecks        # Skip system checks"
    Write-Host ""
    Write-Host "FEATURES:" -ForegroundColor Yellow
    Write-Host "  • Automatic Docker Compose configuration fixes"
    Write-Host "  • Neo4j version and configuration updates"
    Write-Host "  • Proxy configuration for corporate networks"
    Write-Host "  • Infrastructure-first startup strategy"
    Write-Host "  • Comprehensive health checks"
    Write-Host "  • Graceful degradation on network issues"
    Write-Host ""
    Write-Host "DOCUMENTATION:" -ForegroundColor Yellow
    Write-Host "  Installation Guide: docs/INSTALLATION.md"
    Write-Host "  Troubleshooting:    docs/TROUBLESHOOTING.md"
    Write-Host "  Project README:     README.md"
    Write-Host ""
}

function Setup-Proxy {
    if ($NoProxy) {
        Write-ColorOutput "[INFO] Proxy setup skipped by parameter" $InfoColor
        return
    }
    
    Write-ColorOutput "[INFO] Network proxy configuration" $InfoColor
    Write-ColorOutput "[INFO] If you are behind a corporate firewall or need proxy for Docker Hub access," $InfoColor
    Write-ColorOutput "[INFO] you may need to configure HTTP proxy settings." $InfoColor
    Write-Host ""
    
    $useProxy = Read-Host "Do you want to configure HTTP proxy? (y/N)"
    
    if ($useProxy -eq "y" -or $useProxy -eq "Y") {
        $proxyUrl = Read-Host "Enter proxy URL (default: http://127.0.0.1:10808)"
        if ([string]::IsNullOrWhiteSpace($proxyUrl)) {
            $proxyUrl = "http://127.0.0.1:10808"
        }
        
        Write-ColorOutput "[INFO] Setting up proxy: $proxyUrl" $InfoColor
        
        # Set environment variables for current session
        $env:HTTP_PROXY = $proxyUrl
        $env:HTTPS_PROXY = $proxyUrl
        
        # Configure Docker Desktop proxy (if possible)
        Write-ColorOutput "[INFO] Proxy configured for current session" $SuccessColor
        Write-ColorOutput "[WARNING] Please also configure Docker Desktop proxy settings manually:" $WarningColor
        Write-ColorOutput "[INFO] Docker Desktop -> Settings -> Resources -> Proxies" $InfoColor
        Write-ColorOutput "[INFO] Set HTTP/HTTPS proxy to: $proxyUrl" $InfoColor
        Write-Host ""
        
        $continue = Read-Host "Press Enter to continue after configuring Docker Desktop proxy..."
    } else {
        Write-ColorOutput "[INFO] Proxy configuration skipped" $InfoColor
    }
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-Requirements {
    Write-ColorOutput "[INFO] Checking system requirements..." $InfoColor
    
    # Check Docker
    if (-not (Test-Command "docker")) {
        Write-ColorOutput "[ERROR] Docker is not installed. Please install Docker Desktop first" $ErrorColor
        Write-ColorOutput "[INFO] Download from: https://www.docker.com/products/docker-desktop" $InfoColor
        exit 1
    }
    
    # Check Docker version
    $dockerVersion = docker --version
    Write-ColorOutput "[SUCCESS] $dockerVersion" $SuccessColor
    
    # Check Docker Compose
    if (-not (Test-Command "docker-compose")) {
        Write-ColorOutput "[ERROR] Docker Compose is not installed" $ErrorColor
        exit 1
    }
    
    $composeVersion = docker-compose --version
    Write-ColorOutput "[SUCCESS] $composeVersion" $SuccessColor
    
    # Check Git
    if (-not (Test-Command "git")) {
        Write-ColorOutput "[ERROR] Git is not installed. Please install Git first" $ErrorColor
        exit 1
    }
    
    # Test Docker connectivity
    Write-ColorOutput "[INFO] Testing Docker Hub connectivity..." $InfoColor
    try {
        $testResult = docker pull hello-world 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[SUCCESS] Docker Hub connectivity test passed" $SuccessColor
            docker rmi hello-world -f | Out-Null
        } else {
            Write-ColorOutput "[WARNING] Docker Hub connectivity test failed" $WarningColor
            Write-ColorOutput "[INFO] This may indicate network issues or proxy requirements" $InfoColor
        }
    }
    catch {
        Write-ColorOutput "[WARNING] Docker connectivity test failed: $($_.Exception.Message)" $WarningColor
    }
    
    Write-ColorOutput "[SUCCESS] System requirements check completed" $SuccessColor
}

function Test-Ports {
    Write-ColorOutput "[INFO] Checking port usage..." $InfoColor
    
    $ports = @(3000, 8000, 5432, 7474, 6379, 9000, 5672, 15672, 9001, 5555)
    $occupiedPorts = @()
    
    foreach ($port in $ports) {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connection) {
            $occupiedPorts += $port
        }
    }
    
    if ($occupiedPorts.Count -gt 0) {
        Write-ColorOutput "[WARNING] The following ports are occupied: $($occupiedPorts -join ', ')" $WarningColor
        $continue = Read-Host "Continue with installation? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-ColorOutput "[INFO] Installation cancelled" $InfoColor
            exit 1
        }
    } else {
        Write-ColorOutput "[SUCCESS] Port check passed" $SuccessColor
    }
}

function Fix-DockerComposeConfig {
    Write-ColorOutput "[INFO] Checking and fixing Docker Compose configuration..." $InfoColor
    
    # Fix docker-compose.yml
    if (Test-Path "docker-compose.yml") {
        $composeContent = Get-Content "docker-compose.yml" -Raw
        
        # Remove obsolete version attribute
        if ($composeContent -match "version:\s*['\`"]?3\.\d+['\`"]?") {
            Write-ColorOutput "[INFO] Removing obsolete version attribute from docker-compose.yml" $InfoColor
            $composeContent = $composeContent -replace "version:\s*['\`"]?3\.\d+['\`"]?\s*\n", "# Removed obsolete version attribute`n"
            $composeContent | Out-File -FilePath "docker-compose.yml" -Encoding UTF8
        }
        
        # Fix Neo4j image version
        if ($composeContent -match "neo4j:5\.0-community") {
            Write-ColorOutput "[INFO] Updating Neo4j image version to latest community edition" $InfoColor
            $composeContent = $composeContent -replace "neo4j:5\.0-community", "neo4j:latest"
            $composeContent | Out-File -FilePath "docker-compose.yml" -Encoding UTF8
        }
        
        # Remove problematic Neo4j memory settings for v5.x
        if ($composeContent -match "NEO4J_dbms_memory_heap") {
            Write-ColorOutput "[INFO] Removing incompatible Neo4j memory settings" $InfoColor
            $composeContent = $composeContent -replace "\s*NEO4J_dbms_memory_heap_initial_size:.*\n", ""
            $composeContent = $composeContent -replace "\s*NEO4J_dbms_memory_heap_max_size:.*\n", ""
            $composeContent = $composeContent -replace "\s*NEO4J_dbms_memory_pagecache_size:.*\n", ""
            $composeContent | Out-File -FilePath "docker-compose.yml" -Encoding UTF8
        }
    }
    
    # Fix docker-compose.override.yml
    if (Test-Path "docker-compose.override.yml") {
        $overrideContent = Get-Content "docker-compose.override.yml" -Raw
        
        if ($overrideContent -match "version:\s*['\`"]?3\.\d+['\`"]?") {
            Write-ColorOutput "[INFO] Removing obsolete version attribute from docker-compose.override.yml" $InfoColor
            $overrideContent = $overrideContent -replace "version:\s*['\`"]?3\.\d+['\`"]?\s*\n", "# Removed obsolete version attribute`n"
            $overrideContent | Out-File -FilePath "docker-compose.override.yml" -Encoding UTF8
        }
    }
    
    Write-ColorOutput "[SUCCESS] Docker Compose configuration updated" $SuccessColor
}

function Setup-Environment {
    Write-ColorOutput "[INFO] Setting up environment variables..." $InfoColor
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-ColorOutput "[SUCCESS] Created .env file" $SuccessColor
        } else {
            Write-ColorOutput "[INFO] Creating default .env file..." $InfoColor
            
            # Generate random password
            function New-RandomPassword {
                param([int]$Length = 25)
                $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                $password = ""
                for ($i = 0; $i -lt $Length; $i++) {
                    $password += $chars[(Get-Random -Maximum $chars.Length)]
                }
                return $password
            }
            
            $envContent = @"
# Database configuration
POSTGRES_DB=cotdb
POSTGRES_USER=cotuser
POSTGRES_PASSWORD=$(New-RandomPassword)

# Neo4j configuration
NEO4J_PASSWORD=$(New-RandomPassword)

# Redis configuration
REDIS_PASSWORD=$(New-RandomPassword)

# MinIO configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=$(New-RandomPassword)

# RabbitMQ configuration
RABBITMQ_USER=cotuser
RABBITMQ_PASSWORD=$(New-RandomPassword)

# JWT configuration
JWT_SECRET_KEY=$(New-RandomPassword -Length 50)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Application configuration
DEBUG=false
LOG_LEVEL=INFO

# LLM API configuration (please fill in your API keys)
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
"@
            
            $envContent | Out-File -FilePath ".env" -Encoding UTF8
            Write-ColorOutput "[SUCCESS] Created default .env file" $SuccessColor
        }
    } else {
        Write-ColorOutput "[INFO] .env file already exists, skipping creation" $InfoColor
    }
    
    Write-ColorOutput "[WARNING] Please edit the .env file to configure your LLM API keys" $WarningColor
}

function Start-InfrastructureServices {
    Write-ColorOutput "[INFO] Starting infrastructure services first..." $InfoColor
    
    # Start infrastructure services that don't require building
    $infraServices = @("postgres", "redis", "neo4j", "minio", "rabbitmq")
    
    Write-ColorOutput "[INFO] Starting: $($infraServices -join ', ')" $InfoColor
    docker-compose up -d $infraServices
    
    Write-ColorOutput "[INFO] Waiting for infrastructure services to start..." $InfoColor
    Start-Sleep -Seconds 45
    
    # Check infrastructure services status
    Write-ColorOutput "[INFO] Checking infrastructure services status..." $InfoColor
    docker-compose ps $infraServices
    
    # Verify critical services are healthy
    $maxAttempts = 12
    $attempt = 0
    $healthyServices = @()
    
    while ($attempt -lt $maxAttempts -and $healthyServices.Count -lt $infraServices.Count) {
        $attempt++
        Write-ColorOutput "[INFO] Health check attempt $attempt/$maxAttempts..." $InfoColor
        
        $healthyServices = @()
        foreach ($service in $infraServices) {
            try {
                # Use simpler approach - check if service is running
                $psOutput = docker-compose ps $service
                if ($psOutput -match "Up.*\(healthy\)|Up \d+") {
                    $healthyServices += $service
                    Write-ColorOutput "[DEBUG] $service is healthy/running" $InfoColor
                }
            }
            catch {
                # Service might not be ready yet
                Write-ColorOutput "[DEBUG] Failed to check $service" $InfoColor
            }
        }
        
        Write-ColorOutput "[INFO] Healthy services: $($healthyServices.Count)/$($infraServices.Count)" $InfoColor
        
        if ($healthyServices.Count -lt $infraServices.Count) {
            Start-Sleep -Seconds 10
        }
    }
    
    if ($healthyServices.Count -eq $infraServices.Count) {
        Write-ColorOutput "[SUCCESS] All infrastructure services are running" $SuccessColor
        return $true
    } else {
        Write-ColorOutput "[WARNING] Some infrastructure services may not be fully ready" $WarningColor
        $failedServices = $infraServices | Where-Object { $_ -notin $healthyServices }
        Write-ColorOutput "[INFO] Failed services: $($failedServices -join ', ')" $InfoColor
        return $false
    }
}

function Build-AndStart {
    # First start infrastructure services
    $infraReady = Start-InfrastructureServices
    
    if (-not $infraReady) {
        Write-ColorOutput "[WARNING] Infrastructure services are not fully ready, but continuing..." $WarningColor
    }
    
    # If DevMode, only start infrastructure services
    if ($DevMode) {
        Write-ColorOutput "[INFO] Development mode: Infrastructure services only" $InfoColor
        Write-ColorOutput "[INFO] Use 'docker-compose ps' to check service status" $InfoColor
        return $true
    }
    
    Write-ColorOutput "[INFO] Building and starting application services..." $InfoColor
    
    try {
        # Try to build and start all services
        docker-compose build
        docker-compose up -d
        
        Write-ColorOutput "[INFO] Waiting for all services to start..." $InfoColor
        Start-Sleep -Seconds 30
        
        Write-ColorOutput "[INFO] Checking service status..." $InfoColor
        docker-compose ps
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to build application services: $($_.Exception.Message)" $ErrorColor
        Write-ColorOutput "[INFO] Infrastructure services are still available for development" $InfoColor
        return $false
    }
}

function Test-Installation {
    Write-ColorOutput "[INFO] Verifying installation..." $InfoColor
    
    # First check infrastructure services
    Write-ColorOutput "[INFO] Checking infrastructure services..." $InfoColor
    $infraServices = @("postgres", "redis", "neo4j", "minio", "rabbitmq")
    $workingServices = @()
    
    foreach ($service in $infraServices) {
        try {
            $psOutput = docker-compose ps $service
            if ($psOutput -match "Up.*\(healthy\)|Up \d+") {
                $workingServices += $service
                Write-ColorOutput "[SUCCESS] $service is running" $SuccessColor
            } else {
                Write-ColorOutput "[WARNING] $service is not running properly" $WarningColor
            }
        }
        catch {
            Write-ColorOutput "[ERROR] Failed to check $service status" $ErrorColor
        }
    }
    
    Write-ColorOutput "[INFO] Infrastructure services status: $($workingServices.Count)/$($infraServices.Count) running" $InfoColor
    
    # Check application services if they exist
    $appServices = @("backend", "frontend")
    $runningAppServices = @()
    
    foreach ($service in $appServices) {
        try {
            $psOutput = docker-compose ps $service 2>$null
            if ($psOutput -match "Up.*\(healthy\)|Up \d+") {
                $runningAppServices += $service
            }
        }
        catch {
            # Service might not be built/started
        }
    }
    
    if ($runningAppServices.Count -gt 0) {
        Write-ColorOutput "[INFO] Application services running: $($runningAppServices -join ', ')" $InfoColor
        
        # Test backend if running
        if ("backend" -in $runningAppServices) {
            $maxAttempts = 15
            $attempt = 0
            
            Write-ColorOutput "[INFO] Testing backend service..." $InfoColor
            
            while ($attempt -lt $maxAttempts) {
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
                    if ($response.StatusCode -eq 200) {
                        Write-ColorOutput "[SUCCESS] Backend service is responding" $SuccessColor
                        break
                    }
                }
                catch {
                    # Continue waiting
                }
                
                $attempt++
                Write-ColorOutput "[INFO] Waiting for backend service... ($attempt/$maxAttempts)" $InfoColor
                Start-Sleep -Seconds 5
            }
            
            if ($attempt -eq $maxAttempts) {
                Write-ColorOutput "[WARNING] Backend service health check timeout" $WarningColor
            }
        }
        
        # Test frontend if running
        if ("frontend" -in $runningAppServices) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
                Write-ColorOutput "[SUCCESS] Frontend service is responding" $SuccessColor
            }
            catch {
                Write-ColorOutput "[WARNING] Frontend service may not be fully ready" $WarningColor
            }
        }
    } else {
        Write-ColorOutput "[INFO] No application services running - infrastructure-only setup" $InfoColor
    }
    
    Write-ColorOutput "[SUCCESS] Installation verification completed" $SuccessColor
    return $true
}

function Show-AccessInfo {
    Write-ColorOutput "`nCOT Studio MVP setup completed!" $SuccessColor
    Write-Host ""
    
    # Check which services are actually running
    $runningServices = @()
    $serviceUrls = @{
        "frontend" = "http://localhost:3000"
        "backend" = "http://localhost:8000"
        "neo4j" = "http://localhost:7474"
        "minio" = "http://localhost:9001"
        "rabbitmq" = "http://localhost:15672"
        "flower" = "http://localhost:5555"
    }
    
    foreach ($service in $serviceUrls.Keys) {
        try {
            $psOutput = docker-compose ps $service 2>$null
            if ($psOutput -match "Up.*\(healthy\)|Up \d+") {
                $runningServices += $service
            }
        }
        catch {
            # Service not running
        }
    }
    
    Write-Host "Available Services:"
    foreach ($service in $runningServices) {
        $url = $serviceUrls[$service]
        $serviceName = switch ($service) {
            "frontend" { "Frontend App" }
            "backend" { "Backend API" }
            "neo4j" { "Neo4j Browser" }
            "minio" { "MinIO Console" }
            "rabbitmq" { "RabbitMQ Management" }
            "flower" { "Celery Monitor" }
        }
        Write-Host "  $serviceName`: $url"
    }
    
    if ("backend" -in $runningServices) {
        Write-Host "  API Documentation:   http://localhost:8000/docs"
    }
    
    Write-Host ""
    Write-Host "Infrastructure Services:"
    $infraServices = @("postgres", "redis", "neo4j", "minio", "rabbitmq")
    foreach ($service in $infraServices) {
        try {
            $psOutput = docker-compose ps $service 2>$null
            if ($psOutput -match "Up.*\(healthy\)") {
                Write-Host "  $service`: ✓ Running (healthy)"
            } elseif ($psOutput -match "Up \d+") {
                Write-Host "  $service`: ✓ Running"
            } elseif ($psOutput -match "Exit|Exited") {
                Write-Host "  $service`: ✗ Stopped"
            } else {
                Write-Host "  $service`: ✗ Not found"
            }
        }
        catch {
            Write-Host "  $service`: ✗ Error checking status"
        }
    }
    
    Write-Host ""
    Write-Host "Common Commands:"
    Write-Host "  Check service status: docker-compose ps"
    Write-Host "  View logs:           docker-compose logs [service]"
    Write-Host "  Stop services:       docker-compose down"
    Write-Host "  Restart services:    docker-compose up -d"
    Write-Host "  Start specific:      docker-compose up -d [service]"
    Write-Host ""
    
    if ($runningServices.Count -lt 2) {
        Write-ColorOutput "[INFO] Local Development Setup:" $InfoColor
        Write-Host "  1. Backend: See docs/LOCAL_DEVELOPMENT.md"
        Write-Host "  2. Frontend: cd frontend && npm install && npm run dev"
        Write-Host "  3. Use -DevMode for infrastructure-only setup"
        Write-Host ""
    }
    
    Write-Host "For more information, see documentation: docs/README.md"
}

# Main function
function Main {
    # Show help if requested
    if ($Help) {
        Show-Help
        exit 0
    }
    
    Write-Host "========================================"
    Write-Host "    COT Studio MVP Windows Setup Script"
    Write-Host "    Version 1.0.0 - Updated 2025-09-15"
    Write-Host "========================================"
    Write-Host ""
    
    # Check if running in project root directory
    if (-not (Test-Path "docker-compose.yml")) {
        Write-ColorOutput "[ERROR] Please run this script from the project root directory" $ErrorColor
        Write-ColorOutput "[INFO] Use -Help for usage information" $InfoColor
        exit 1
    }
    
    # Setup proxy configuration first
    Setup-Proxy
    
    if (-not $SkipChecks) {
        Test-Requirements
        Test-Ports
    }
    
    # Fix Docker Compose configuration issues
    Fix-DockerComposeConfig
    
    Setup-Environment
    
    $buildSuccess = Build-AndStart
    
    if (Test-Installation) {
        Show-AccessInfo
        
        if (-not $buildSuccess) {
            Write-Host ""
            Write-ColorOutput "[INFO] Setup completed with infrastructure services only" $InfoColor
            Write-ColorOutput "[INFO] Application services can be built separately when network issues are resolved" $InfoColor
        }
    } else {
        Write-ColorOutput "[ERROR] Installation verification failed, please check logs and retry" $ErrorColor
        Write-ColorOutput "[INFO] View logs: docker-compose logs [service]" $InfoColor
        Write-ColorOutput "[INFO] Retry setup: .\scripts\setup.ps1" $InfoColor
        exit 1
    }
}

# Error handling
$ErrorActionPreference = "Stop"

try {
    Main
}
catch {
    Write-ColorOutput "[ERROR] An error occurred during installation: $($_.Exception.Message)" $ErrorColor
    exit 1
}