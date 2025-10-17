# COT Studio MVP - Fix Local Development Configuration
# Fixes backend configuration for local development (outside Docker)

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

function Fix-BackendConfig {
    Write-ColorOutput "[INFO] Fixing backend configuration for local development..." $InfoColor
    
    $configFile = "backend/app/core/config.py"
    
    if (-not (Test-Path $configFile)) {
        Write-ColorOutput "[ERROR] Backend config file not found: $configFile" $ErrorColor
        return $false
    }
    
    try {
        $content = Get-Content $configFile -Raw
        $originalContent = $content
        
        # Fix Neo4j URI (Docker internal -> localhost)
        $content = $content -replace 'NEO4J_URI:\s*str\s*=\s*"bolt://neo4j:7687"', 'NEO4J_URI: str = "bolt://localhost:7687"'
        
        # Fix MinIO endpoint
        $content = $content -replace 'MINIO_ENDPOINT:\s*str\s*=\s*"[^"]*"', 'MINIO_ENDPOINT: str = "localhost:9000"'
        
        # Fix MinIO credentials
        $content = $content -replace 'MINIO_ACCESS_KEY:\s*str\s*=\s*"[^"]*"', 'MINIO_ACCESS_KEY: str = "minioadmin"'
        $content = $content -replace 'MINIO_SECRET_KEY:\s*str\s*=\s*"[^"]*"', 'MINIO_SECRET_KEY: str = "minioadmin123"'
        
        # Fix RabbitMQ URL
        $content = $content -replace 'RABBITMQ_URL:\s*str\s*=\s*"[^"]*"', 'RABBITMQ_URL: str = "amqp://cotuser:cotpass@localhost:5672/"'
        
        # Fix Redis URL (should already be correct)
        $content = $content -replace 'REDIS_URL:\s*str\s*=\s*"redis://redis:6379"', 'REDIS_URL: str = "redis://localhost:6379"'
        
        if ($content -ne $originalContent) {
            Set-Content -Path $configFile -Value $content -Encoding UTF8
            Write-ColorOutput "[SUCCESS] Backend configuration updated for local development" $SuccessColor
            return $true
        } else {
            Write-ColorOutput "[INFO] Backend configuration already correct for local development" $InfoColor
            return $true
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to update backend config: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Verify-DockerServices {
    Write-ColorOutput "[INFO] Verifying Docker services are running..." $InfoColor
    
    $services = @("postgres", "redis", "neo4j", "minio", "rabbitmq")
    $runningServices = 0
    
    foreach ($service in $services) {
        $status = docker-compose ps $service
        if ($status -match "Up.*healthy|Up \d+") {
            Write-ColorOutput "[SUCCESS] $service is running" $SuccessColor
            $runningServices++
        } else {
            Write-ColorOutput "[ERROR] $service is not running" $ErrorColor
        }
    }
    
    if ($runningServices -eq $services.Count) {
        Write-ColorOutput "[SUCCESS] All Docker services are running" $SuccessColor
        return $true
    } else {
        Write-ColorOutput "[WARNING] $runningServices/$($services.Count) services are running" $WarningColor
        return $false
    }
}

function Test-ServiceConnections {
    Write-ColorOutput "[INFO] Testing service connections from localhost..." $InfoColor
    
    $tests = @{
        "PostgreSQL" = { 
            try {
                $result = Invoke-WebRequest -Uri "http://localhost:5432" -TimeoutSec 2 2>&1
                return $false  # Should not get HTTP response from PostgreSQL
            } catch {
                if ($_.Exception.Message -match "connection.*refused|timeout") {
                    return $false  # Port not accessible
                } else {
                    return $true   # Port is open (PostgreSQL responds with non-HTTP)
                }
            }
        }
        "Redis" = {
            try {
                $result = Invoke-WebRequest -Uri "http://localhost:6379" -TimeoutSec 2 2>&1
                return $false
            } catch {
                if ($_.Exception.Message -match "connection.*refused|timeout") {
                    return $false
                } else {
                    return $true
                }
            }
        }
        "Neo4j" = {
            try {
                $result = Invoke-WebRequest -Uri "http://localhost:7474" -TimeoutSec 3
                return $result.StatusCode -eq 200
            } catch {
                return $false
            }
        }
        "MinIO" = {
            try {
                $result = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 3
                return $result.StatusCode -eq 200
            } catch {
                return $false
            }
        }
        "RabbitMQ" = {
            try {
                $result = Invoke-WebRequest -Uri "http://localhost:15672" -TimeoutSec 3
                return $result.StatusCode -eq 200
            } catch {
                return $false
            }
        }
    }
    
    $passedTests = 0
    foreach ($testName in $tests.Keys) {
        $testResult = & $tests[$testName]
        if ($testResult) {
            Write-ColorOutput "[SUCCESS] $testName connection test passed" $SuccessColor
            $passedTests++
        } else {
            Write-ColorOutput "[ERROR] $testName connection test failed" $ErrorColor
        }
    }
    
    return $passedTests -eq $tests.Count
}

function Show-LocalDevInstructions {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    LOCAL DEVELOPMENT SETUP COMPLETE" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    Write-ColorOutput "Service Endpoints (from localhost):" $InfoColor
    Write-Host "  PostgreSQL:  localhost:5432"
    Write-Host "  Redis:       localhost:6379"
    Write-Host "  Neo4j:       bolt://localhost:7687 (Browser: http://localhost:7474)"
    Write-Host "  MinIO:       localhost:9000 (Console: http://localhost:9001)"
    Write-Host "  RabbitMQ:    localhost:5672 (Management: http://localhost:15672)"
    Write-Host ""
    
    Write-ColorOutput "Credentials:" $InfoColor
    Write-Host "  Neo4j:    neo4j / neo4jpass"
    Write-Host "  MinIO:    minioadmin / minioadmin123"
    Write-Host "  RabbitMQ: cotuser / cotpass"
    Write-Host ""
    
    Write-ColorOutput "To start backend:" $InfoColor
    Write-Host "  cd backend"
    Write-Host "  .\venv\Scripts\activate"
    Write-Host "  uvicorn app.main:app --reload"
    Write-Host ""
    
    Write-ColorOutput "Backend should now connect to all services without errors!" $SuccessColor
}

function Main {
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    Local Development Configuration Fix" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    $configFixed = Fix-BackendConfig
    $servicesRunning = Verify-DockerServices
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "           RESULTS" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    
    if ($configFixed) {
        Write-ColorOutput "[PASS] Backend Configuration" $SuccessColor
    } else {
        Write-ColorOutput "[FAIL] Backend Configuration" $ErrorColor
    }
    
    if ($servicesRunning) {
        Write-ColorOutput "[PASS] Docker Services" $SuccessColor
        
        $connectionTests = Test-ServiceConnections
        if ($connectionTests) {
            Write-ColorOutput "[PASS] Service Connections" $SuccessColor
        } else {
            Write-ColorOutput "[FAIL] Service Connections" $WarningColor
        }
    } else {
        Write-ColorOutput "[FAIL] Docker Services" $ErrorColor
    }
    
    if ($configFixed -and $servicesRunning) {
        Write-ColorOutput "`n🎉 Local development environment is ready!" $SuccessColor
        Show-LocalDevInstructions
    } else {
        Write-ColorOutput "`n❌ Issues detected in local development setup" $ErrorColor
        Write-Host ""
        Write-Host "Troubleshooting:"
        if (-not $servicesRunning) {
            Write-Host "1. Start Docker services: docker-compose up -d"
        }
        if (-not $configFixed) {
            Write-Host "2. Check backend configuration file permissions"
        }
        Write-Host "3. Run this script again after fixing issues"
    }
}

Main