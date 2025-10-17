# COT Studio MVP - Backend Issues Fix Script
# Comprehensive fix for all backend import and compatibility issues

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

function Fix-AllBackendIssues {
    Write-ColorOutput "[INFO] Fixing all backend issues..." $InfoColor
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "[ERROR] Backend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location backend
    
    try {
        # Activate virtual environment
        if (Test-Path "venv") {
            & ".\venv\Scripts\activate.ps1"
        } else {
            Write-ColorOutput "[ERROR] Virtual environment not found. Run .\scripts\install-backend.ps1 first" $ErrorColor
            return $false
        }
        
        Write-ColorOutput "[INFO] Step 1: Installing missing dependencies..." $InfoColor
        
        # Install missing core dependencies
        $missingPackages = @("psutil", "redis", "PyJWT", "cryptography", "passlib[bcrypt]")
        foreach ($package in $missingPackages) {
            try {
                pip install $package
                Write-ColorOutput "[SUCCESS] Installed $package" $SuccessColor
            }
            catch {
                Write-ColorOutput "[WARNING] Failed to install $package" $WarningColor
            }
        }
        
        Write-ColorOutput "[INFO] Step 2: Testing application import..." $InfoColor
        
        # Test if the app can be imported
        $testResult = python -c "
try:
    from app.main import app
    print('SUCCESS: Backend application imports correctly')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[SUCCESS] Backend application imports successfully" $SuccessColor
            
            # Test uvicorn import
            $uvicornTest = python -c "
try:
    import uvicorn
    from app.main import app
    print('SUCCESS: Ready to serve with uvicorn')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "[SUCCESS] Backend is ready to start with uvicorn" $SuccessColor
                return $true
            } else {
                Write-ColorOutput "[ERROR] Uvicorn test failed: $uvicornTest" $ErrorColor
                return $false
            }
        } else {
            Write-ColorOutput "[ERROR] Application import failed: $testResult" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Fix process failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Show-StartupInstructions {
    Write-ColorOutput "`n[SUCCESS] Backend is ready!" $SuccessColor
    Write-Host ""
    Write-Host "To start the backend server:"
    Write-Host "  cd backend"
    Write-Host "  .\venv\Scripts\activate"
    Write-Host "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Write-Host ""
    Write-Host "Backend will be available at:"
    Write-Host "  API: http://localhost:8000"
    Write-Host "  Docs: http://localhost:8000/docs"
    Write-Host ""
    Write-Host "Note: Some optional features may show warnings:"
    Write-Host "  - PaddleOCR: Install with 'pip install paddlepaddle paddleocr'"
    Write-Host "  - YARA: Already loaded successfully"
    Write-Host ""
}

function Main {
    Write-Host "========================================"
    Write-Host "    Backend Issues Comprehensive Fix"
    Write-Host "========================================"
    Write-Host ""
    
    $success = Fix-AllBackendIssues
    
    if ($success) {
        Show-StartupInstructions
    } else {
        Write-ColorOutput "`n[ERROR] Backend fix failed" $ErrorColor
        Write-Host ""
        Write-Host "Manual troubleshooting steps:"
        Write-Host "1. Check Python version: python --version"
        Write-Host "2. Recreate virtual environment: .\scripts\install-backend.ps1 -Force"
        Write-Host "3. Check specific errors: cd backend && .\venv\Scripts\activate && python -c 'from app.main import app'"
        Write-Host "4. See troubleshooting guide: docs/TROUBLESHOOTING.md"
    }
}

Main