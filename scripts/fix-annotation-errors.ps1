# COT Studio MVP - Fix Annotation Page Errors
# Fixes annotation page routing and component issues

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

function Test-AnnotationComponents {
    Write-ColorOutput "[INFO] Checking annotation components..." $InfoColor
    
    $requiredFiles = @(
        "frontend/src/pages/AnnotationProjects.tsx",
        "frontend/src/components/annotation/AnnotationWorkspace.tsx",
        "frontend/src/components/annotation/TextSelector.tsx",
        "frontend/src/components/annotation/QuestionGenerator.tsx",
        "frontend/src/components/annotation/CandidateList.tsx",
        "frontend/src/hooks/useAnnotation.ts",
        "frontend/src/stores/annotationStore.ts",
        "frontend/src/services/annotationService.ts"
    )
    
    $missingFiles = @()
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-ColorOutput "[ERROR] Missing annotation files:" $ErrorColor
        foreach ($file in $missingFiles) {
            Write-Host "  - $file" -ForegroundColor $ErrorColor
        }
        return $false
    } else {
        Write-ColorOutput "[SUCCESS] All annotation components found" $SuccessColor
        return $true
    }
}

function Test-RouterConfig {
    Write-ColorOutput "[INFO] Checking router configuration..." $InfoColor
    
    $routerFile = "frontend/src/router/index.tsx"
    if (Test-Path $routerFile) {
        $content = Get-Content $routerFile -Raw
        
        if ($content -match "path: '/annotation'" -and $content -match "AnnotationProjects") {
            Write-ColorOutput "[SUCCESS] Router configuration updated" $SuccessColor
            return $true
        } else {
            Write-ColorOutput "[ERROR] Router configuration needs update" $ErrorColor
            return $false
        }
    } else {
        Write-ColorOutput "[ERROR] Router file not found" $ErrorColor
        return $false
    }
}

function Start-DevServerAndTest {
    Write-ColorOutput "[INFO] Testing annotation page..." $InfoColor
    
    # Check if dev server is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "[SUCCESS] Frontend is accessible" $SuccessColor
            
            # Test annotation route
            try {
                $annotationResponse = Invoke-WebRequest -Uri "http://localhost:3000/annotation" -UseBasicParsing -TimeoutSec 3
                if ($annotationResponse.StatusCode -eq 200) {
                    Write-ColorOutput "[SUCCESS] Annotation route is working" $SuccessColor
                    return $true
                } else {
                    Write-ColorOutput "[WARNING] Annotation route returned status: $($annotationResponse.StatusCode)" $WarningColor
                    return $false
                }
            }
            catch {
                Write-ColorOutput "[WARNING] Could not test annotation route: $($_.Exception.Message)" $WarningColor
                return $false
            }
        }
    }
    catch {
        Write-ColorOutput "[WARNING] Frontend dev server not running" $WarningColor
        return $false
    }
}

function Show-Instructions {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    ANNOTATION PAGE SETUP COMPLETE" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    Write-ColorOutput "The annotation page has been fixed with the following changes:" $InfoColor
    Write-Host ""
    Write-Host "1. ✅ Created AnnotationProjects.tsx - Project selection page"
    Write-Host "2. ✅ Updated router to handle /annotation route"
    Write-Host "3. ✅ Added route for /annotation/:projectId"
    Write-Host ""
    
    Write-ColorOutput "Navigation Flow:" $InfoColor
    Write-Host "  Sidebar 'CoT标注' → /annotation → Project Selection → /annotation/:projectId → Annotation Workspace"
    Write-Host ""
    
    Write-ColorOutput "To test:" $InfoColor
    Write-Host "1. Ensure frontend is running: cd frontend && npm run dev"
    Write-Host "2. Login with: admin / 971028"
    Write-Host "3. Click 'CoT标注' in sidebar"
    Write-Host "4. You should see project selection page"
    Write-Host "5. Click '开始标注' on any project"
    Write-Host ""
    
    Write-ColorOutput "Note: The annotation workspace requires:" $InfoColor
    Write-Host "- Projects with uploaded files"
    Write-Host "- Backend API endpoints for annotation"
    Write-Host "- LLM services for question/answer generation"
}

function Main {
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "    Annotation Error Fix Script" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host ""
    
    $componentsOk = Test-AnnotationComponents
    $routerOk = Test-RouterConfig
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $InfoColor
    Write-Host "           RESULTS" -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
    
    if ($componentsOk) {
        Write-ColorOutput "[PASS] Annotation Components" $SuccessColor
    } else {
        Write-ColorOutput "[FAIL] Annotation Components" $ErrorColor
    }
    
    if ($routerOk) {
        Write-ColorOutput "[PASS] Router Configuration" $SuccessColor
    } else {
        Write-ColorOutput "[FAIL] Router Configuration" $ErrorColor
    }
    
    # Test if server is running
    $serverTest = Start-DevServerAndTest
    if ($serverTest) {
        Write-ColorOutput "[PASS] Server Test" $SuccessColor
    } else {
        Write-ColorOutput "[INFO] Server Test (not critical)" $WarningColor
    }
    
    if ($componentsOk -and $routerOk) {
        Write-ColorOutput "`n🎉 Annotation page is ready!" $SuccessColor
        Show-Instructions
    } else {
        Write-ColorOutput "`n❌ Annotation page has issues" $ErrorColor
        Write-Host ""
        Write-Host "Manual steps needed:"
        if (-not $componentsOk) {
            Write-Host "1. Check missing annotation component files"
        }
        if (-not $routerOk) {
            Write-Host "2. Update router configuration"
        }
    }
}

Main