# COT Studio MVP - Dependency Fix Script
# Fixes local development environment dependency issues

param(
    [switch]$Backend = $false,
    [switch]$Frontend = $false,
    [switch]$All = $false
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
    Write-Host "COT Studio MVP - Dependency Fix Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\fix-dependencies.ps1 -Backend   # Fix backend dependencies"
    Write-Host "  .\scripts\fix-dependencies.ps1 -Frontend  # Fix frontend dependencies"
    Write-Host "  .\scripts\fix-dependencies.ps1 -All       # Fix all dependencies"
    Write-Host ""
}

function Fix-Backend {
    Write-ColorOutput "[INFO] Fixing backend dependencies..." $InfoColor
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "[ERROR] backend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location backend
    
    try {
        # Check Python version
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "[INFO] Current Python version: $pythonVersion" $InfoColor
        
        if ($pythonVersion -match "3\.13") {
            Write-ColorOutput "[WARNING] Python 3.13 may have compatibility issues, recommend Python 3.11" $WarningColor
        }
        
        # Create virtual environment if not exists
        if (-not (Test-Path "venv")) {
            Write-ColorOutput "[INFO] Creating virtual environment..." $InfoColor
            python -m venv venv
        }
        
        # Activate virtual environment
        Write-ColorOutput "[INFO] Activating virtual environment..." $InfoColor
        & ".\venv\Scripts\activate.ps1"
        
        # Upgrade pip
        Write-ColorOutput "[INFO] Upgrading pip..." $InfoColor
        python -m pip install --upgrade pip
        
        # Use layered installation strategy
        Write-ColorOutput "[INFO] Using layered installation strategy..." $InfoColor
        
        # Step 1: Install core dependencies
        if (Test-Path "requirements-core.txt") {
            Write-ColorOutput "[INFO] Installing core dependencies..." $InfoColor
            pip install -r requirements-core.txt
        } else {
            Write-ColorOutput "[INFO] Installing from main requirements.txt..." $InfoColor
            pip install -r requirements.txt
        }
        
        # Step 2: Install problematic packages individually
        if (Test-Path "requirements-problematic.txt") {
            Write-ColorOutput "[INFO] Installing problematic packages individually..." $InfoColor
            $problematicPackages = Get-Content "requirements-problematic.txt" | Where-Object { $_ -notmatch "^#" -and $_.Trim() -ne "" }
            
            foreach ($package in $problematicPackages) {
                $packageName = $package.Split("==")[0].Trim()
                try {
                    Write-ColorOutput "[INFO] Installing $packageName..." $InfoColor
                    pip install $package --no-build-isolation
                    Write-ColorOutput "[SUCCESS] $packageName installed successfully" $SuccessColor
                }
                catch {
                    Write-ColorOutput "[WARNING] Failed to install $packageName, trying alternative method..." $WarningColor
                    try {
                        # Try without version constraint
                        pip install $packageName --no-build-isolation
                        Write-ColorOutput "[SUCCESS] $packageName installed (latest version)" $SuccessColor
                    }
                    catch {
                        Write-ColorOutput "[WARNING] $packageName installation failed, skipping..." $WarningColor
                    }
                }
            }
        }
        
        Write-ColorOutput "[SUCCESS] Backend dependencies fixed" $SuccessColor
        Write-ColorOutput "[INFO] Start backend: uvicorn app.main:app --reload" $InfoColor
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Backend dependency fix failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Fix-Frontend {
    Write-ColorOutput "[INFO] Fixing frontend dependencies..." $InfoColor
    
    if (-not (Test-Path "frontend")) {
        Write-ColorOutput "[ERROR] frontend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location frontend
    
    try {
        # Check Node.js version
        $nodeVersion = node --version 2>&1
        Write-ColorOutput "[INFO] Current Node.js version: $nodeVersion" $InfoColor
        
        # Clean cache and old dependencies
        Write-ColorOutput "[INFO] Cleaning npm cache..." $InfoColor
        npm cache clean --force
        
        if (Test-Path "node_modules") {
            Write-ColorOutput "[INFO] Removing old node_modules..." $InfoColor
            Remove-Item -Recurse -Force node_modules
        }
        
        if (Test-Path "package-lock.json") {
            Write-ColorOutput "[INFO] Removing package-lock.json..." $InfoColor
            Remove-Item package-lock.json
        }
        
        # Install dependencies
        Write-ColorOutput "[INFO] Installing frontend dependencies..." $InfoColor
        npm install
        
        # Check and install missing dependencies
        $packageJson = Get-Content "package.json" | ConvertFrom-Json
        $missingDeps = @()
        
        # Check for required dependencies
        $requiredDeps = @{
            "recharts" = "^2.8.0"
            "cytoscape-cola" = "^2.5.1"
            "cytoscape-cose-bilkent" = "^4.1.0"
            "cytoscape-dagre" = "^2.5.0"
        }
        
        foreach ($dep in $requiredDeps.Keys) {
            if (-not $packageJson.dependencies.$dep) {
                $missingDeps += "$dep@$($requiredDeps[$dep])"
            }
        }
        
        if ($missingDeps.Count -gt 0) {
            Write-ColorOutput "[INFO] Installing missing dependencies: $($missingDeps -join ', ')" $InfoColor
            npm install $missingDeps
        }
        
        Write-ColorOutput "[SUCCESS] Frontend dependencies fixed" $SuccessColor
        Write-ColorOutput "[INFO] Start frontend: npm run dev" $InfoColor
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Frontend dependency fix failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Main {
    if (-not ($Backend -or $Frontend -or $All)) {
        Show-Help
        return
    }
    
    Write-Host "========================================"
    Write-Host "    COT Studio MVP - Dependency Fix"
    Write-Host "========================================"
    Write-Host ""
    
    $success = $true
    
    if ($All -or $Backend) {
        $success = Fix-Backend -and $success
    }
    
    if ($All -or $Frontend) {
        $success = Fix-Frontend -and $success
    }
    
    if ($success) {
        Write-ColorOutput "`n[SUCCESS] Dependencies fixed!" $SuccessColor
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "1. Start infrastructure: docker-compose up -d postgres redis neo4j minio rabbitmq"
        Write-Host "2. Start backend: cd backend; .\venv\Scripts\activate; uvicorn app.main:app --reload"
        Write-Host "3. Start frontend: cd frontend; npm run dev"
        Write-Host ""
        Write-Host "For details see: docs/LOCAL_DEVELOPMENT.md"
    } else {
        Write-ColorOutput "`n[ERROR] Errors occurred during dependency fix" $ErrorColor
        Write-Host "Please check the error messages above and resolve manually"
    }
}

Main