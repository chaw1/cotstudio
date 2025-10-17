# COT Studio MVP - Update User Password
# Updates user password in database

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

function Update-DatabasePassword {
    Write-ColorOutput "[INFO] Updating admin user password in database..." $InfoColor
    
    Set-Location backend
    
    try {
        # Activate virtual environment
        & ".\venv\Scripts\activate.ps1"
        
        # Generate new password hash
        Write-ColorOutput "[INFO] Generating password hash for '971028'..." $InfoColor
        $hashResult = python -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
hash_value = pwd_context.hash('971028')
print(hash_value)
"
        
        if ($hashResult) {
            Write-ColorOutput "[SUCCESS] Password hash generated: $hashResult" $SuccessColor
            
            # Update database directly using Python
            Write-ColorOutput "[INFO] Updating database..." $InfoColor
            $updateResult = python -c "
import sqlite3
import os

# Connect to database
db_path = 'cot_studio.db'
if not os.path.exists(db_path):
    print('ERROR: Database file not found')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Update admin user password
new_hash = '$hashResult'
cursor.execute('UPDATE users SET hashed_password = ? WHERE username = ?', (new_hash, 'admin'))

if cursor.rowcount > 0:
    conn.commit()
    print('SUCCESS: Admin password updated')
else:
    print('ERROR: Admin user not found')

conn.close()
" 2>&1
            
            Write-ColorOutput "[INFO] Database update result: $updateResult" $InfoColor
            
            if ($updateResult -match "SUCCESS") {
                Write-ColorOutput "[SUCCESS] Admin password updated successfully" $SuccessColor
                return $true
            } else {
                Write-ColorOutput "[ERROR] Failed to update password in database" $ErrorColor
                return $false
            }
        } else {
            Write-ColorOutput "[ERROR] Failed to generate password hash" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Password update failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Reset-DatabaseFromSeed {
    Write-ColorOutput "[INFO] Resetting database from seed data..." $InfoColor
    
    Set-Location backend
    
    try {
        # Activate virtual environment
        & ".\venv\Scripts\activate.ps1"
        
        # Drop and recreate users table
        Write-ColorOutput "[INFO] Dropping existing users..." $InfoColor
        python -c "
import sqlite3
import os

db_path = 'cot_studio.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username IN (\"admin\", \"editor\")')
    conn.commit()
    conn.close()
    print('Users deleted')
else:
    print('Database not found')
"
        
        # Re-run seed migration
        Write-ColorOutput "[INFO] Re-applying seed data..." $InfoColor
        alembic downgrade 001
        alembic upgrade heads
        
        Write-ColorOutput "[SUCCESS] Database reset with new password" $SuccessColor
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Database reset failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Test-Login {
    Write-ColorOutput "[INFO] Testing login with new password..." $InfoColor
    
    try {
        # Test login API
        $loginData = @{
            username = "admin"
            password = "971028"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $loginData -ContentType "application/json" -ErrorAction Stop
        
        if ($response.access_token) {
            Write-ColorOutput "[SUCCESS] Login test passed with new password!" $SuccessColor
            return $true
        } else {
            Write-ColorOutput "[ERROR] Login test failed - no token received" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Login test failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Main {
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    Update User Password" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    Write-ColorOutput "Updating admin password to: 971028" $InfoColor
    Write-Host ""
    
    # Try direct database update first
    $directUpdate = Update-DatabasePassword
    
    if (-not $directUpdate) {
        Write-ColorOutput "[INFO] Direct update failed, trying database reset..." $WarningColor
        $resetResult = Reset-DatabaseFromSeed
        
        if (-not $resetResult) {
            Write-ColorOutput "[ERROR] Both update methods failed" $ErrorColor
            return
        }
    }
    
    # Test if backend is running
    try {
        $healthCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
        if ($healthCheck.StatusCode -eq 200) {
            $loginTest = Test-Login
            
            if ($loginTest) {
                Write-ColorOutput "`n🎉 Password update successful!" $SuccessColor
                Write-Host ""
                Write-ColorOutput "New login credentials:" $InfoColor
                Write-Host "  Username: admin"
                Write-Host "  Password: 971028"
                Write-Host ""
                Write-ColorOutput "You can now login to the frontend with these credentials." $SuccessColor
            } else {
                Write-ColorOutput "`n❌ Password updated but login test failed" $ErrorColor
                Write-ColorOutput "Please restart the backend and try again." $WarningColor
            }
        } else {
            Write-ColorOutput "`n⚠️  Password updated but backend is not running" $WarningColor
            Write-ColorOutput "Start backend to test login: cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload" $InfoColor
        }
    }
    catch {
        Write-ColorOutput "`n⚠️  Password updated but cannot test (backend not running)" $WarningColor
        Write-ColorOutput "Start backend to test login: cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload" $InfoColor
    }
}

Main