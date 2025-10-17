# COT Studio MVP - Python 3.13 Compatibility Fix
# Fixes compatibility issues with Python 3.13

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

function Fix-Python313Issues {
    Write-ColorOutput "[INFO] Fixing Python 3.13 compatibility issues..." $InfoColor
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "[ERROR] Backend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location backend
    
    try {
        # Check if virtual environment exists
        if (-not (Test-Path "venv")) {
            Write-ColorOutput "[ERROR] Virtual environment not found. Run .\scripts\install-backend.ps1 first" $ErrorColor
            return $false
        }
        
        # Activate virtual environment
        & ".\venv\Scripts\activate.ps1"
        
        # Check Python version
        $pythonVersion = python --version
        Write-ColorOutput "[INFO] Python version: $pythonVersion" $InfoColor
        
        if ($pythonVersion -match "3\.13") {
            Write-ColorOutput "[INFO] Python 3.13 detected, applying compatibility fixes..." $InfoColor
            
            # Fix 1: Replace python-jose with PyJWT
            Write-ColorOutput "[INFO] Replacing python-jose with PyJWT..." $InfoColor
            
            # Uninstall problematic package
            try {
                pip uninstall python-jose -y
                Write-ColorOutput "[SUCCESS] Removed python-jose" $SuccessColor
            }
            catch {
                Write-ColorOutput "[INFO] python-jose not installed or already removed" $InfoColor
            }
            
            # Install PyJWT
            try {
                pip install "PyJWT[cryptography]==2.8.0"
                Write-ColorOutput "[SUCCESS] Installed PyJWT" $SuccessColor
            }
            catch {
                Write-ColorOutput "[ERROR] Failed to install PyJWT" $ErrorColor
                return $false
            }
            
            # Fix 2: Check for other problematic packages
            Write-ColorOutput "[INFO] Checking for other Python 3.13 compatibility issues..." $InfoColor
            
            $problematicPackages = @(
                "python-jose",
                "jose"
            )
            
            $installedPackages = pip list
            foreach ($pkg in $problematicPackages) {
                if ($installedPackages -match $pkg) {
                    Write-ColorOutput "[WARNING] Found potentially problematic package: $pkg" $WarningColor
                    try {
                        pip uninstall $pkg -y
                        Write-ColorOutput "[SUCCESS] Removed $pkg" $SuccessColor
                    }
                    catch {
                        Write-ColorOutput "[WARNING] Could not remove $pkg" $WarningColor
                    }
                }
            }
            
            Write-ColorOutput "[SUCCESS] Python 3.13 compatibility fixes applied" $SuccessColor
        } else {
            Write-ColorOutput "[INFO] Python 3.13 not detected, no fixes needed" $InfoColor
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Fix failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Test-BackendStart {
    Write-ColorOutput "[INFO] Testing backend startup..." $InfoColor
    
    Set-Location backend
    
    try {
        & ".\venv\Scripts\activate.ps1"
        
        # Try to import the main module
        $testResult = python -c "
try:
    from app.main import app
    print('SUCCESS: Backend imports work correctly')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
"
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[SUCCESS] Backend startup test passed" $SuccessColor
            return $true
        } else {
            Write-ColorOutput "[ERROR] Backend startup test failed" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Test failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Main {
    Write-Host "========================================"
    Write-Host "    Python 3.13 Compatibility Fix"
    Write-Host "========================================"
    Write-Host ""
    
    $fixSuccess = Fix-Python313Issues
    
    if ($fixSuccess) {
        Write-ColorOutput "[INFO] Testing backend after fixes..." $InfoColor
        $testSuccess = Test-BackendStart
        
        if ($testSuccess) {
            Write-ColorOutput "`n[SUCCESS] Python 3.13 compatibility fixes completed!" $SuccessColor
            Write-Host ""
            Write-Host "Backend is now ready to start:"
            Write-Host "  cd backend"
            Write-Host "  .\venv\Scripts\activate"
            Write-Host "  uvicorn app.main:app --reload"
        } else {
            Write-ColorOutput "`n[WARNING] Fixes applied but backend test failed" $WarningColor
            Write-Host "Check the error messages and run manual tests"
        }
    } else {
        Write-ColorOutput "`n[ERROR] Failed to apply Python 3.13 fixes" $ErrorColor
        Write-Host ""
        Write-Host "Manual steps:"
        Write-Host "1. cd backend && .\venv\Scripts\activate"
        Write-Host "2. pip uninstall python-jose -y"
        Write-Host "3. pip install 'PyJWT[cryptography]==2.8.0'"
        Write-Host "4. Check app/core/security.py for correct imports"
    }
}

Main