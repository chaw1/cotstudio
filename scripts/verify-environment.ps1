# COT Studio MVP - Environment Verification Script
# Comprehensive test of the entire development environment

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

function Test-Infrastructure {
    Write-ColorOutput "[INFO] Testing infrastructure services..." $InfoColor
    
    $services = @("postgres", "redis", "neo4j", "minio", "rabbitmq")
    $runningCount = 0
    
    $psOutput = docker-compose ps $services
    
    foreach ($service in $services) {
        if ($psOutput -match "$service.*Up.*\(healthy\)|$service.*Up \d+") {
            Write-ColorOutput "[SUCCESS] $service is running" $SuccessColor
            $runningCount++
        } else {
            Write-ColorOutput "[ERROR] $service is not running" $ErrorColor
        }
    }
    
    return $runningCount -eq $services.Count
}

function Test-BackendDependencies {
    Write-ColorOutput "[INFO] Testing backend dependencies..." $InfoColor
    
    if (-not (Test-Path "backend/requirements.txt")) {
        Write-ColorOutput "[ERROR] Backend requirements.txt not found" $ErrorColor
        return $false
    }
    
    if (Test-Path "backend/venv") {
        Write-ColorOutput "[SUCCESS] Backend virtual environment exists" $SuccessColor
        
        # Check for Python 3.13 compatibility issues
        Set-Location backend
        try {
            & ".\venv\Scripts\activate.ps1"
            $pythonVersion = python --version
            
            if ($pythonVersion -match "3\.13") {
                # Check if python-jose is installed (problematic)
                $installedPackages = pip list
                if ($installedPackages -match "python-jose") {
                    Write-ColorOutput "[WARNING] python-jose detected with Python 3.13 (compatibility issue)" $WarningColor
                    Write-ColorOutput "[INFO] Run: .\scripts\fix-python313.ps1" $InfoColor
                } else {
                    Write-ColorOutput "[SUCCESS] Python 3.13 compatibility looks good" $SuccessColor
                }
            }
        }
        finally {
            Set-Location ..
        }
    } else {
        Write-ColorOutput "[WARNING] Backend virtual environment not found" $WarningColor
    }
    
    return $true
}

function Test-FrontendDependencies {
    Write-ColorOutput "[INFO] Testing frontend dependencies..." $InfoColor
    
    if (-not (Test-Path "frontend/package.json")) {
        Write-ColorOutput "[ERROR] Frontend package.json not found" $ErrorColor
        return $false
    }
    
    Set-Location frontend
    
    try {
        $packageJson = Get-Content "package.json" | ConvertFrom-Json
        $requiredDeps = @(
            "cytoscape",
            "cytoscape-cola", 
            "cytoscape-cose-bilkent",
            "cytoscape-dagre",
            "recharts"
        )
        
        $allPresent = $true
        foreach ($dep in $requiredDeps) {
            if ($packageJson.dependencies.$dep) {
                Write-ColorOutput "[SUCCESS] $dep is present" $SuccessColor
            } else {
                Write-ColorOutput "[ERROR] $dep is missing" $ErrorColor
                $allPresent = $false
            }
        }
        
        return $allPresent
    }
    finally {
        Set-Location ..
    }
}

function Test-Configuration {
    Write-ColorOutput "[INFO] Testing configuration files..." $InfoColor
    
    $configFiles = @(
        "docker-compose.yml",
        ".env"
    )
    
    $allPresent = $true
    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Write-ColorOutput "[SUCCESS] $file exists" $SuccessColor
        } else {
            Write-ColorOutput "[ERROR] $file is missing" $ErrorColor
            $allPresent = $false
        }
    }
    
    return $allPresent
}

function Test-NetworkConnectivity {
    Write-ColorOutput "[INFO] Testing network connectivity..." $InfoColor
    
    $urls = @{
        "Neo4j Browser" = "http://localhost:7474"
        "MinIO Console" = "http://localhost:9001"
        "RabbitMQ Management" = "http://localhost:15672"
    }
    
    $successCount = 0
    foreach ($service in $urls.Keys) {
        try {
            $response = Invoke-WebRequest -Uri $urls[$service] -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "[SUCCESS] $service is accessible" $SuccessColor
                $successCount++
            }
        }
        catch {
            Write-ColorOutput "[WARNING] $service is not accessible" $WarningColor
        }
    }
    
    return $successCount -gt 0
}

function Main {
    Write-Host "========================================"
    Write-Host "    COT Studio MVP - Environment Verification"
    Write-Host "========================================"
    Write-Host ""
    
    $results = @{
        "Infrastructure" = Test-Infrastructure
        "Backend Dependencies" = Test-BackendDependencies
        "Frontend Dependencies" = Test-FrontendDependencies
        "Configuration" = Test-Configuration
        "Network Connectivity" = Test-NetworkConnectivity
    }
    
    Write-Host ""
    Write-Host "========================================"
    Write-Host "           VERIFICATION RESULTS"
    Write-Host "========================================"
    
    $passedTests = 0
    $totalTests = $results.Count
    
    foreach ($test in $results.Keys) {
        if ($results[$test]) {
            Write-ColorOutput "[PASS] $test" $SuccessColor
            $passedTests++
        } else {
            Write-ColorOutput "[FAIL] $test" $ErrorColor
        }
    }
    
    Write-Host ""
    Write-ColorOutput "Tests Passed: $passedTests/$totalTests" $InfoColor
    
    if ($passedTests -eq $totalTests) {
        Write-ColorOutput "`n[SUCCESS] Environment is fully ready for development!" $SuccessColor
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "1. Start backend: cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload"
        Write-Host "2. Start frontend: cd frontend && npm run dev"
        Write-Host "3. Access frontend: http://localhost:3000"
    } elseif ($passedTests -ge 3) {
        Write-ColorOutput "`n[WARNING] Environment is partially ready" $WarningColor
        Write-Host ""
        Write-Host "Fix remaining issues:"
        Write-Host "- Infrastructure: .\scripts\dev-start.ps1 -Infrastructure"
        Write-Host "- Dependencies: .\scripts\fix-dependencies.ps1 -All"
        Write-Host "- Configuration: .\scripts\setup.ps1 -DevMode"
    } else {
        Write-ColorOutput "`n[ERROR] Environment needs significant fixes" $ErrorColor
        Write-Host ""
        Write-Host "Recommended actions:"
        Write-Host "1. Run full setup: .\scripts\setup.ps1"
        Write-Host "2. Fix dependencies: .\scripts\fix-dependencies.ps1 -All"
        Write-Host "3. Check troubleshooting guide: docs/TROUBLESHOOTING.md"
    }
}

Main