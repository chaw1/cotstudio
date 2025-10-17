# COT Studio MVP - Backend Installation Script
# Handles problematic packages with layered installation strategy

param(
    [switch]$Force = $false,
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
    Write-Host "COT Studio MVP - Backend Installation Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\install-backend.ps1        # Standard installation"
    Write-Host "  .\scripts\install-backend.ps1 -Force # Force reinstall all packages"
    Write-Host ""
    Write-Host "Features:" -ForegroundColor Yellow
    Write-Host "  • Layered installation strategy"
    Write-Host "  • Handles problematic packages separately"
    Write-Host "  • Uses --no-build-isolation for build issues"
    Write-Host "  • Automatic fallback to latest versions"
    Write-Host ""
}

function Install-Backend {
    Write-ColorOutput "[INFO] Starting backend installation..." $InfoColor
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "[ERROR] Backend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location backend
    
    try {
        # Check Python version
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "[INFO] Python version: $pythonVersion" $InfoColor
        
        # Create virtual environment if not exists
        if (-not (Test-Path "venv") -or $Force) {
            if (Test-Path "venv" -and $Force) {
                Write-ColorOutput "[INFO] Removing existing virtual environment..." $InfoColor
                Remove-Item -Recurse -Force venv
            }
            
            Write-ColorOutput "[INFO] Creating virtual environment..." $InfoColor
            python -m venv venv
        }
        
        # Activate virtual environment
        Write-ColorOutput "[INFO] Activating virtual environment..." $InfoColor
        & ".\venv\Scripts\activate.ps1"
        
        # Upgrade pip and build tools
        Write-ColorOutput "[INFO] Upgrading pip and build tools..." $InfoColor
        python -m pip install --upgrade pip setuptools wheel
        
        # Install core dependencies first
        if (Test-Path "requirements-core.txt") {
            Write-ColorOutput "[INFO] Installing core dependencies..." $InfoColor
            pip install -r requirements-core.txt
        } else {
            Write-ColorOutput "[WARNING] requirements-core.txt not found, using requirements.txt" $WarningColor
            pip install -r requirements.txt
            return $true
        }
        
        # Install problematic packages individually
        if (Test-Path "requirements-problematic.txt") {
            Write-ColorOutput "[INFO] Installing problematic packages..." $InfoColor
            $problematicContent = Get-Content "requirements-problematic.txt"
            $packages = $problematicContent | Where-Object { $_ -notmatch "^#" -and $_.Trim() -ne "" }
            
            foreach ($package in $packages) {
                $packageName = $package.Split("==")[0].Trim()
                Write-ColorOutput "[INFO] Installing $packageName..." $InfoColor
                
                # Try multiple installation strategies
                $installed = $false
                
                # Strategy 1: Normal installation
                try {
                    pip install $package
                    Write-ColorOutput "[SUCCESS] $packageName installed (normal method)" $SuccessColor
                    $installed = $true
                }
                catch {
                    Write-ColorOutput "[WARNING] Normal installation failed for $packageName" $WarningColor
                }
                
                # Strategy 2: No build isolation
                if (-not $installed) {
                    try {
                        pip install $package --no-build-isolation
                        Write-ColorOutput "[SUCCESS] $packageName installed (no build isolation)" $SuccessColor
                        $installed = $true
                    }
                    catch {
                        Write-ColorOutput "[WARNING] No build isolation failed for $packageName" $WarningColor
                    }
                }
                
                # Strategy 3: Use binary wheel only
                if (-not $installed) {
                    try {
                        pip install $package --only-binary=all
                        Write-ColorOutput "[SUCCESS] $packageName installed (binary only)" $SuccessColor
                        $installed = $true
                    }
                    catch {
                        Write-ColorOutput "[WARNING] Binary only installation failed for $packageName" $WarningColor
                    }
                }
                
                # Strategy 4: Latest version without constraints
                if (-not $installed) {
                    try {
                        pip install $packageName
                        Write-ColorOutput "[SUCCESS] $packageName installed (latest version)" $SuccessColor
                        $installed = $true
                    }
                    catch {
                        Write-ColorOutput "[ERROR] All installation strategies failed for $packageName" $ErrorColor
                    }
                }
                
                if (-not $installed) {
                    Write-ColorOutput "[WARNING] $packageName could not be installed, continuing..." $WarningColor
                }
            }
        }
        
        # Apply Python 3.13 compatibility fixes if needed
        $pythonVersion = python --version
        if ($pythonVersion -match "3\.13") {
            Write-ColorOutput "[INFO] Python 3.13 detected, applying compatibility fixes..." $InfoColor
            
            # Remove python-jose if installed
            try {
                pip uninstall python-jose -y 2>$null
            }
            catch {
                # Ignore if not installed
            }
            
            # Ensure PyJWT is installed
            pip install "PyJWT[cryptography]==2.8.0"
        }
        
        # Verify installation
        Write-ColorOutput "[INFO] Verifying installation..." $InfoColor
        $installedPackages = pip list
        
        # Check for key packages
        $keyPackages = @("fastapi", "uvicorn", "sqlalchemy", "psycopg2-binary", "asyncpg")
        $missingPackages = @()
        
        foreach ($pkg in $keyPackages) {
            if ($installedPackages -match $pkg) {
                Write-ColorOutput "[SUCCESS] $pkg is installed" $SuccessColor
            } else {
                $missingPackages += $pkg
                Write-ColorOutput "[WARNING] $pkg is missing" $WarningColor
            }
        }
        
        if ($missingPackages.Count -eq 0) {
            Write-ColorOutput "[SUCCESS] Backend installation completed successfully" $SuccessColor
        } else {
            Write-ColorOutput "[WARNING] Installation completed with some missing packages: $($missingPackages -join ', ')" $WarningColor
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Backend installation failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Host "========================================"
    Write-Host "    COT Studio MVP - Backend Installation"
    Write-Host "========================================"
    Write-Host ""
    
    $success = Install-Backend
    
    if ($success) {
        Write-ColorOutput "`n[SUCCESS] Backend installation completed!" $SuccessColor
        Write-Host ""
        Write-Host "To start backend:"
        Write-Host "  cd backend"
        Write-Host "  .\venv\Scripts\activate"
        Write-Host "  uvicorn app.main:app --reload"
        Write-Host ""
    } else {
        Write-ColorOutput "`n[ERROR] Backend installation failed" $ErrorColor
        Write-Host ""
        Write-Host "Troubleshooting:"
        Write-Host "  1. Check Python version (recommend 3.11)"
        Write-Host "  2. Try: .\scripts\install-backend.ps1 -Force"
        Write-Host "  3. See: docs/TROUBLESHOOTING.md"
    }
}

Main