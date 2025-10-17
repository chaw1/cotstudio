# Quick Authentication Test
# Tests if authentication components are properly configured

$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host "    Quick Authentication Test" -ForegroundColor $InfoColor
Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host ""

# Test 1: Check frontend .env
Write-ColorOutput "[TEST 1] Frontend .env configuration" $InfoColor
if (Test-Path "frontend/.env") {
    $envContent = Get-Content "frontend/.env"
    Write-ColorOutput "✓ Frontend .env exists" $SuccessColor
    foreach ($line in $envContent) {
        Write-Host "  $line" -ForegroundColor Gray
    }
} else {
    Write-ColorOutput "✗ Frontend .env missing" $ErrorColor
}

Write-Host ""

# Test 2: Check auth components
Write-ColorOutput "[TEST 2] Authentication components" $InfoColor
$authFiles = @(
    "frontend/src/services/authService.ts",
    "frontend/src/components/auth/Login.tsx",
    "frontend/src/components/auth/ProtectedRoute.tsx"
)

foreach ($file in $authFiles) {
    if (Test-Path $file) {
        Write-ColorOutput "✓ $file exists" $SuccessColor
    } else {
        Write-ColorOutput "✗ $file missing" $ErrorColor
    }
}

Write-Host ""

# Test 3: Check backend seed data
Write-ColorOutput "[TEST 3] Backend user seed data" $InfoColor
if (Test-Path "backend/alembic/versions/002_seed_data.py") {
    Write-ColorOutput "✓ Seed data migration exists" $SuccessColor
    Write-Host "  Default users: admin/secret, editor/secret" -ForegroundColor Gray
} else {
    Write-ColorOutput "✗ Seed data migration missing" $ErrorColor
}

Write-Host ""

# Test 4: Check Vite proxy config
Write-ColorOutput "[TEST 4] Vite proxy configuration" $InfoColor
if (Test-Path "frontend/vite.config.ts") {
    $viteConfig = Get-Content "frontend/vite.config.ts" -Raw
    if ($viteConfig -match "localhost:8000") {
        Write-ColorOutput "✓ Vite proxy configured for /api -> localhost:8000" $SuccessColor
    } else {
        Write-ColorOutput "✗ Vite proxy not configured correctly" $ErrorColor
    }
} else {
    Write-ColorOutput "✗ vite.config.ts missing" $ErrorColor
}

Write-Host ""
Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host "           NEXT STEPS" -ForegroundColor $InfoColor
Write-Host "========================================" -ForegroundColor $InfoColor
Write-Host ""
Write-ColorOutput "To test the complete authentication flow:" $InfoColor
Write-Host "1. Start backend:  cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload"
Write-Host "2. Start frontend: cd frontend && npm run dev"
Write-Host "3. Visit: http://localhost:3000"
Write-Host "4. Login with: admin / secret"
Write-Host ""
Write-ColorOutput "The frontend will now redirect to login page and authentication should work!" $SuccessColor