# COT Studio MVP - Start Services and Test Authentication
# Starts backend and frontend, then tests authentication

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

function Start-Backend {
    Write-ColorOutput "[INFO] Starting backend server..." $InfoColor
    
    Set-Location backend
    
    try {
        # Activate virtual environment and start server
        $backendProcess = Start-Process -FilePath "powershell" -ArgumentList "-Command", "& '.\venv\Scripts\activate.ps1'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru
        
        Write-ColorOutput "[INFO] Backend process started (PID: $($backendProcess.Id))" $InfoColor
        
        # Wait for backend to start
        Write-ColorOutput "[INFO] Waiting for backend to start..." $InfoColor
        Start-Sleep -Seconds 5
        
        # Test if backend is responding
        for ($i = 1; $i -le 10; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
                if ($response.StatusCode -eq 200) {
                    Write-ColorOutput "[SUCCESS] Backend is running and responding" $SuccessColor
                    return $backendProcess
                }
            }
            catch {
                Write-ColorOutput "[INFO] Waiting for backend... ($i/10)" $InfoColor
                Start-Sleep -Seconds 2
            }
        }
        
        Write-ColorOutput "[ERROR] Backend failed to start properly" $ErrorColor
        return $null
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to start backend: $($_.Exception.Message)" $ErrorColor
        return $null
    }
    finally {
        Set-Location ..
    }
}

function Test-Authentication {
    Write-ColorOutput "[INFO] Testing authentication..." $InfoColor
    
    try {
        # Test login
        $loginData = @{
            username = "admin"
            password = "secret"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json"
        
        if ($response.access_token) {
            Write-ColorOutput "[SUCCESS] Login successful!" $SuccessColor
            Write-ColorOutput "[INFO] Token received: $($response.access_token.Substring(0, 20))..." $InfoColor
            
            # Test protected endpoint
            $headers = @{
                "Authorization" = "Bearer $($response.access_token)"
            }
            
            $userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" -Method GET -Headers $headers
            Write-ColorOutput "[SUCCESS] User info retrieved: $($userInfo.username) ($($userInfo.email))" $SuccessColor
            
            return $true
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Authentication test failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    
    return $false
}

function Start-Frontend {
    Write-ColorOutput "[INFO] Starting frontend development server..." $InfoColor
    
    Set-Location frontend
    
    try {
        # Start frontend dev server
        $frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-Command", "npm run dev" -PassThru
        
        Write-ColorOutput "[INFO] Frontend process started (PID: $($frontendProcess.Id))" $InfoColor
        Write-ColorOutput "[INFO] Frontend will be available at: http://localhost:3000" $InfoColor
        
        return $frontendProcess
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to start frontend: $($_.Exception.Message)" $ErrorColor
        return $null
    }
    finally {
        Set-Location ..
    }
}

function Main {
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    COT Studio Authentication Test" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    # Start backend
    $backendProcess = Start-Backend
    
    if ($backendProcess) {
        # Test authentication
        $authTest = Test-Authentication
        
        if ($authTest) {
            Write-ColorOutput "`n🎉 Authentication is working!" $SuccessColor
            
            # Start frontend
            $frontendProcess = Start-Frontend
            
            Write-Host ""
            Write-Host "========================================" -ForegroundColor $InfoColor
            Write-Host "           SERVICES RUNNING" -ForegroundColor $InfoColor
            Write-Host "========================================" -ForegroundColor $InfoColor
            Write-Host ""
            Write-ColorOutput "Backend API:  http://localhost:8000" $SuccessColor
            Write-ColorOutput "Frontend App: http://localhost:3000" $SuccessColor
            Write-Host ""
            Write-ColorOutput "Login Credentials:" $InfoColor
            Write-Host "  Username: admin"
            Write-Host "  Password: secret"
            Write-Host ""
            Write-ColorOutput "Press Ctrl+C to stop all services" $WarningColor
            
            # Keep script running
            try {
                while ($true) {
                    Start-Sleep -Seconds 1
                }
            }
            catch {
                Write-ColorOutput "`nStopping services..." $InfoColor
                if ($backendProcess -and !$backendProcess.HasExited) {
                    Stop-Process -Id $backendProcess.Id -Force
                }
                if ($frontendProcess -and !$frontendProcess.HasExited) {
                    Stop-Process -Id $frontendProcess.Id -Force
                }
            }
        } else {
            Write-ColorOutput "`n❌ Authentication test failed" $ErrorColor
            if ($backendProcess -and !$backendProcess.HasExited) {
                Stop-Process -Id $backendProcess.Id -Force
            }
        }
    } else {
        Write-ColorOutput "`n❌ Failed to start backend" $ErrorColor
    }
}

Main