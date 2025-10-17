# COT Studio MVP - 开发环境快速启动脚本

param(
    [switch]$Backend = $false,
    [switch]$Frontend = $false,
    [switch]$Infrastructure = $false,
    [switch]$All = $false,
    [switch]$Help = $false
)

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
    Write-Host "COT Studio MVP - Development Start Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev-start.ps1 -Infrastructure  # Start infrastructure services only"
    Write-Host "  .\scripts\dev-start.ps1 -Backend         # Start backend (requires infrastructure)"
    Write-Host "  .\scripts\dev-start.ps1 -Frontend        # Start frontend"
    Write-Host "  .\scripts\dev-start.ps1 -All             # Start everything"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev-start.ps1 -Infrastructure  # For local development"
    Write-Host "  .\scripts\dev-start.ps1 -All             # Full stack development"
    Write-Host ""
}

function Start-Infrastructure {
    Write-ColorOutput "[INFO] Starting infrastructure services..." $InfoColor
    
    try {
        docker-compose up -d postgres redis neo4j minio rabbitmq
        
        Write-ColorOutput "[INFO] Waiting for services to be ready..." $InfoColor
        Start-Sleep -Seconds 15
        
        # Check service status using simple approach
        $psOutput = docker-compose ps postgres redis neo4j minio rabbitmq
        $runningCount = 0
        $services = @("postgres", "redis", "neo4j", "minio", "rabbitmq")
        
        foreach ($service in $services) {
            if ($psOutput -match "$service.*Up.*\(healthy\)|$service.*Up \d+") {
                $runningCount++
                Write-ColorOutput "[SUCCESS] $service is running" $SuccessColor
            } else {
                Write-ColorOutput "[WARNING] $service may not be ready" $WarningColor
            }
        }
        
        Write-ColorOutput "[INFO] Infrastructure services: $runningCount/5 running" $InfoColor
        return $runningCount -ge 4  # Allow 1 service to be not ready
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to start infrastructure: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Start-Backend {
    Write-ColorOutput "[INFO] Starting backend service..." $InfoColor
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "[ERROR] Backend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location backend
    
    try {
        # Check if virtual environment exists
        if (-not (Test-Path "venv")) {
            Write-ColorOutput "[INFO] Backend environment not found, setting up..." $InfoColor
            Write-ColorOutput "[INFO] Run: .\scripts\install-backend.ps1 for full installation" $InfoColor
            
            # Basic setup for development
            python -m venv venv
            & ".\venv\Scripts\activate.ps1"
            pip install --upgrade pip
            
            # Try to install core dependencies only
            if (Test-Path "requirements-core.txt") {
                pip install -r requirements-core.txt
            } else {
                Write-ColorOutput "[WARNING] Use .\scripts\install-backend.ps1 for complete setup" $WarningColor
            }
        }
        
        # Check if .env exists
        if (-not (Test-Path ".env")) {
            Write-ColorOutput "[INFO] Creating backend .env file..." $InfoColor
            $envContent = @"
# Database connections (using Docker services)
DATABASE_URL=postgresql://cotuser:cotpass@localhost:5432/cotdb
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpass

# MinIO configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# RabbitMQ configuration
RABBITMQ_URL=amqp://cotuser:cotpass@localhost:5672/

# JWT configuration
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# LLM API configuration
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Development mode
DEBUG=true
LOG_LEVEL=DEBUG
"@
            $envContent | Out-File -FilePath ".env" -Encoding UTF8
        }
        
        Write-ColorOutput "[SUCCESS] Backend environment ready" $SuccessColor
        Write-ColorOutput "[INFO] To start backend manually:" $InfoColor
        Write-ColorOutput "[INFO]   cd backend" $InfoColor
        Write-ColorOutput "[INFO]   .\venv\Scripts\activate" $InfoColor
        Write-ColorOutput "[INFO]   uvicorn app.main:app --reload" $InfoColor
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Backend setup failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Start-Frontend {
    Write-ColorOutput "[INFO] Starting frontend service..." $InfoColor
    
    if (-not (Test-Path "frontend")) {
        Write-ColorOutput "[ERROR] Frontend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location frontend
    
    try {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-ColorOutput "[INFO] Installing frontend dependencies..." $InfoColor
            npm install
        }
        
        # Check if .env exists
        if (-not (Test-Path ".env")) {
            Write-ColorOutput "[INFO] Creating frontend .env file..." $InfoColor
            $envContent = @"
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
"@
            $envContent | Out-File -FilePath ".env" -Encoding UTF8
        }
        
        Write-ColorOutput "[SUCCESS] Frontend environment ready" $SuccessColor
        Write-ColorOutput "[INFO] To start frontend manually:" $InfoColor
        Write-ColorOutput "[INFO]   cd frontend" $InfoColor
        Write-ColorOutput "[INFO]   npm run dev" $InfoColor
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Frontend setup failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Main {
    if ($Help -or (-not ($Backend -or $Frontend -or $Infrastructure -or $All))) {
        Show-Help
        return
    }
    
    Write-Host "========================================"
    Write-Host "    COT Studio MVP - Development Start"
    Write-Host "========================================"
    Write-Host ""
    
    $success = $true
    
    # Always start infrastructure if any service is requested
    if ($All -or $Backend -or $Infrastructure) {
        $infraSuccess = Start-Infrastructure
        if (-not $infraSuccess) {
            Write-ColorOutput "[WARNING] Infrastructure services may not be fully ready" $WarningColor
        }
        $success = $infraSuccess -and $success
    }
    
    if ($All -or $Backend) {
        $backendSuccess = Start-Backend
        $success = $backendSuccess -and $success
    }
    
    if ($All -or $Frontend) {
        $frontendSuccess = Start-Frontend
        $success = $frontendSuccess -and $success
    }
    
    Write-Host ""
    if ($success) {
        Write-ColorOutput "[SUCCESS] Development environment ready!" $SuccessColor
        Write-Host ""
        Write-Host "Service URLs:"
        Write-Host "  Frontend:        http://localhost:3000"
        Write-Host "  Backend API:     http://localhost:8000"
        Write-Host "  API Docs:        http://localhost:8000/docs"
        Write-Host "  Neo4j Browser:   http://localhost:7474"
        Write-Host "  MinIO Console:   http://localhost:9001"
        Write-Host "  RabbitMQ Mgmt:   http://localhost:15672"
        Write-Host ""
        Write-Host "Next steps:"
        if ($Backend -or $All) {
            Write-Host "  1. Start backend: cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload"
        }
        if ($Frontend -or $All) {
            Write-Host "  2. Start frontend: cd frontend && npm run dev"
        }
        Write-Host ""
    } else {
        Write-ColorOutput "[ERROR] Some services failed to start" $ErrorColor
        Write-Host "Check the error messages above for details"
    }
}

Main