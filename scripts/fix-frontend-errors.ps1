# COT Studio MVP - Fix Frontend Errors
# Fixes common frontend errors and missing components

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

function Check-FrontendDependencies {
    Write-ColorOutput "[INFO] Checking frontend dependencies..." $InfoColor
    
    Set-Location frontend
    
    try {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-ColorOutput "[ERROR] node_modules not found" $ErrorColor
            return $false
        }
        
        # Check critical dependencies
        $criticalDeps = @(
            "@ant-design/icons",
            "react",
            "react-dom",
            "react-router-dom",
            "antd"
        )
        
        $missingDeps = @()
        foreach ($dep in $criticalDeps) {
            if (-not (Test-Path "node_modules/$dep")) {
                $missingDeps += $dep
            }
        }
        
        if ($missingDeps.Count -gt 0) {
            Write-ColorOutput "[ERROR] Missing dependencies: $($missingDeps -join ', ')" $ErrorColor
            return $false
        } else {
            Write-ColorOutput "[SUCCESS] All critical dependencies found" $SuccessColor
            return $true
        }
    }
    finally {
        Set-Location ..
    }
}

function Check-IconImports {
    Write-ColorOutput "[INFO] Checking icon imports..." $InfoColor
    
    $problematicIcons = @(
        "TrendingUpOutlined",
        "TrendingDownOutlined", 
        "LineChartOutlined"
    )
    
    $foundIssues = @()
    
    foreach ($icon in $problematicIcons) {
        $results = Select-String -Path "frontend/src/**/*.tsx" -Pattern $icon -ErrorAction SilentlyContinue
        if ($results) {
            foreach ($result in $results) {
                $foundIssues += "$($result.Filename):$($result.LineNumber) - $icon"
            }
        }
    }
    
    if ($foundIssues.Count -gt 0) {
        Write-ColorOutput "[ERROR] Found problematic icon imports:" $ErrorColor
        foreach ($issue in $foundIssues) {
            Write-Host "  $issue" -ForegroundColor $ErrorColor
        }
        return $false
    } else {
        Write-ColorOutput "[SUCCESS] No problematic icon imports found" $SuccessColor
        return $true
    }
}

function Clear-FrontendCache {
    Write-ColorOutput "[INFO] Clearing frontend cache..." $InfoColor
    
    Set-Location frontend
    
    try {
        # Clear Vite cache
        if (Test-Path "node_modules/.vite") {
            Remove-Item -Recurse -Force "node_modules/.vite"
            Write-ColorOutput "[SUCCESS] Vite cache cleared" $SuccessColor
        }
        
        # Clear dist folder
        if (Test-Path "dist") {
            Remove-Item -Recurse -Force "dist"
            Write-ColorOutput "[SUCCESS] Dist folder cleared" $SuccessColor
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "[ERROR] Failed to clear cache: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Test-FrontendBuild {
    Write-ColorOutput "[INFO] Testing frontend build..." $InfoColor
    
    Set-Location frontend
    
    try {
        $buildResult = npm run build 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[SUCCESS] Frontend build successful" $SuccessColor
            return $true
        } else {
            Write-ColorOutput "[ERROR] Frontend build failed:" $ErrorColor
            Write-Host $buildResult -ForegroundColor $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Build test failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Reinstall-Dependencies {
    Write-ColorOutput "[INFO] Reinstalling frontend dependencies..." $InfoColor
    
    Set-Location frontend
    
    try {
        # Remove node_modules and package-lock.json
        if (Test-Path "node_modules") {
            Remove-Item -Recurse -Force "node_modules"
        }
        if (Test-Path "package-lock.json") {
            Remove-Item -Force "package-lock.json"
        }
        
        # Reinstall
        npm install
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[SUCCESS] Dependencies reinstalled" $SuccessColor
            return $true
        } else {
            Write-ColorOutput "[ERROR] Failed to reinstall dependencies" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "[ERROR] Reinstall failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
    finally {
        Set-Location ..
    }
}

function Main {
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    Frontend Error Fix Script" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    $depsOk = Check-FrontendDependencies
    $iconsOk = Check-IconImports
    
    if (-not $depsOk) {
        Write-ColorOutput "[INFO] Dependencies issue detected, reinstalling..." $WarningColor
        $reinstallOk = Reinstall-Dependencies
        if (-not $reinstallOk) {
            Write-ColorOutput "[ERROR] Failed to fix dependencies" $ErrorColor
            return
        }
    }
    
    if (-not $iconsOk) {
        Write-ColorOutput "[ERROR] Icon import issues detected" $ErrorColor
        Write-ColorOutput "[INFO] Please check the reported files and fix icon imports" $WarningColor
        return
    }
    
    # Clear cache
    $cacheCleared = Clear-FrontendCache
    
    # Test build
    $buildOk = Test-FrontendBuild
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "           RESULTS" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    
    if ($depsOk -and $iconsOk -and $buildOk) {
        Write-ColorOutput "🎉 Frontend is ready!" $SuccessColor
        Write-Host ""
        Write-ColorOutput "To start frontend:" $InfoColor
        Write-Host "  cd frontend"
        Write-Host "  npm run dev"
        Write-Host ""
        Write-ColorOutput "Frontend will be available at: http://localhost:3000" $SuccessColor
    } else {
        Write-ColorOutput "❌ Frontend has issues" $ErrorColor
        Write-Host ""
        Write-Host "Manual troubleshooting:"
        if (-not $depsOk) {
            Write-Host "1. Check dependencies: cd frontend && npm install"
        }
        if (-not $iconsOk) {
            Write-Host "2. Fix icon imports in reported files"
        }
        if (-not $buildOk) {
            Write-Host "3. Check build errors: cd frontend && npm run build"
        }
    }
}

Main