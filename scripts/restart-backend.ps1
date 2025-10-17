# COT Studio MVP - Restart Backend Service
# Restarts backend to apply configuration changes

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

function Stop-BackendProcess {
    Write-ColorOutput "[INFO] Stopping any running backend processes..." $InfoColor
    
    try {
        # Find and stop uvicorn processes
        $uvicornProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*app.main:app*"
        }
        
        if ($uvicornProcesses) {
            foreach ($process in $uvicornProcesses) {
                Write-ColorOutput "[INFO] Stopping process $($process.Id)..." $InfoColor
                Stop-Process -Id $process.Id -Force
            }
            Write-ColorOutput "[SUCCESS] Backend processes stopped" $SuccessColor
        } else {
            Write-ColorOutput "[INFO] No running backend processes found" $InfoColor
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "[WARNING] Error stopping processes: $($_.Exception.Message)" $WarningColor
        return $false
    }
}

function Test-BackendHealth {
    Write-ColorOutput "[INFO] Testing backend health..." $InfoColor
    
    for ($i = 1; $i -le 10; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "[SUCCESS] Backend is healthy and responding" $SuccessColor
                return $true
            }
        }
        catch {
            Write-ColorOutput "[INFO] Waiting for backend... ($i/10)" $InfoColor
            Start-Sleep -Seconds 2
        }
    }
    
    Write-ColorOutput "[ERROR] Backend health check failed" $ErrorColor
    return $false
}

function Start-Backend {
    Write-ColorOutput "[INFO] Starting backend server..." $InfoColor
    
    if (-not (Test-Path "backend")) {
        Write-ColorOutput "[ERROR] Backend directory not found" $ErrorColor
        return $false
    }
    
    Set-Location backend
    
    try {
        # Check if virtual environment exists
        if (-not (Test-Path "venv\Scripts\activate.ps1")) {
            Write-ColorOutput "[ERROR] Virtual environment not found" $ErrorColor
            return $false
        }
        
        # Start backend in new window
        $backendProcess = Start-Process -FilePath "powershell" -ArgumentList "-Command", "& '.\venv\Scripts\activate.ps1'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru
        
        Write-ColorOutput "[INFO] Backend process started (PID: $($backendProcess.Id))" $InfoColor
        Write-ColorOutput "[INFO] Waiting for backend to start..." $InfoColor
        
        return $backendProcess
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to start backend: $($_.Exception.Message)" $ErrorColor
        return $null
    }
    finally {
        Set-Location ..
    }
}

function Test-Neo4jConnection {
    Write-ColorOutput "[INFO] Testing Neo4j connection from backend..." $InfoColor
    
    try {
        # Test a simple endpoint that might use Neo4j
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "[SUCCESS] Backend started successfully" $SuccessColor
            Write-ColorOutput "[INFO] Check backend logs for Neo4j connection status" $InfoColor
            return $true
        }
    }
    catch {
        Write-ColorOutput "[WARNING] Could not test Neo4j connection: $($_.Exception.Message)" $WarningColor
        return $false
    }
    
    return $false
}

function Main {
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    Backend Restart Script" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    # Stop existing backend
    Stop-BackendProcess
    
    # Wait a moment
    Start-Sleep -Seconds 2
    
    # Start backend
    $backendProcess = Start-Backend
    
    if ($backendProcess) {
        # Test health
        $healthTest = Test-BackendHealth
        
        if ($healthTest) {
            Write-ColorOutput "`n🎉 Backend restarted successfully!" $SuccessColor
            Write-Host ""
            Write-ColorOutput "Backend API: http://localhost:8000" $SuccessColor
            Write-ColorOutput "API Docs: http://localhost:8000/docs" $InfoColor
            Write-Host ""
            Write-ColorOutput "Check the backend console for Neo4j connection status." $InfoColor
            Write-ColorOutput "If Neo4j connection is successful, you should see:" $InfoColor
            Write-Host "  ✓ No more 'Neo4j connection failed' errors" -ForegroundColor $SuccessColor
            Write-Host ""
            Write-ColorOutput "Backend process ID: $($backendProcess.Id)" $InfoColor
            Write-ColorOutput "To stop: Stop-Process -Id $($backendProcess.Id)" $InfoColor
        } else {
            Write-ColorOutput "`n❌ Backend failed to start properly" $ErrorColor
            Write-Host ""
            Write-Host "Troubleshooting:"
            Write-Host "1. Check if port 8000 is available"
            Write-Host "2. Verify virtual environment is set up"
            Write-Host "3. Check backend logs for errors"
            Write-Host "4. Ensure all dependencies are installed"
        }
    } else {
        Write-ColorOutput "`n❌ Failed to start backend" $ErrorColor
    }
}

Main