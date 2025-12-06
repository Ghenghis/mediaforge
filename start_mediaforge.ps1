# ============================================================
# MEDIAFORGE - Master Startup Script
# ============================================================
# Starts all services in the correct order with health checks
# Run: .\start_mediaforge.ps1
# ============================================================

param(
    [switch]$Minimal,      # Start only core services
    [switch]$All,          # Start all services
    [switch]$Stop,         # Stop all services
    [switch]$Status        # Check status only
)

$Host.UI.RawUI.WindowTitle = "MediaForge Service Manager"

# Service definitions with dependencies
$Services = @(
    # Core Services (Start First)
    @{Name="Unified Gateway"; Port=8300; Script="scripts/unified_gateway.py"; Core=$true; Priority=1},
    @{Name="Rating Studio"; Port=8196; Script="scripts/rating_studio_pro.py"; Core=$true; Priority=2},
    @{Name="Dataset Builder"; Port=8211; Script="scripts/dataset_builder.py"; Core=$true; Priority=2},
    @{Name="AI Learning Brain"; Port=8225; Script="scripts/ai_learning_brain.py"; Core=$true; Priority=2},
    @{Name="LoRA Training"; Port=8230; Script="scripts/lora_training_integration.py"; Core=$true; Priority=3},
    @{Name="Master Orchestrator"; Port=8210; Script="scripts/master_orchestrator.py"; Core=$true; Priority=3},
    
    # Extended Services
    @{Name="Auto Captioner"; Port=8207; Script="scripts/auto_captioner_api.py"; Core=$false; Priority=4},
    @{Name="ComfyUI Automation"; Port=8213; Script="scripts/comfyui_automation.py"; Core=$false; Priority=4},
    @{Name="Unified WPF API"; Port=8190; Script="scripts/unified_wpf_api.py"; Core=$false; Priority=4},
    @{Name="Story Generator"; Port=8197; Script="scripts/story_generator_api.py"; Core=$false; Priority=5},
    @{Name="Voice Tools"; Port=8220; Script="scripts/voice_tools_unified.py"; Core=$false; Priority=5},
    @{Name="Workflow Manager"; Port=8221; Script="scripts/workflow_manager.py"; Core=$false; Priority=5},
    @{Name="Quality Gate"; Port=8216; Script="scripts/quality_gate.py"; Core=$false; Priority=5}
)

function Write-Banner {
    Write-Host ""
    Write-Host "  ███╗   ███╗███████╗██████╗ ██╗ █████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗" -ForegroundColor Cyan
    Write-Host "  ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝" -ForegroundColor Cyan
    Write-Host "  ██╔████╔██║█████╗  ██║  ██║██║███████║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  " -ForegroundColor Cyan
    Write-Host "  ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  " -ForegroundColor Cyan
    Write-Host "  ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗" -ForegroundColor Cyan
    Write-Host "  ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  AI-Powered Content Creation Platform" -ForegroundColor Gray
    Write-Host ""
}

function Test-ServiceRunning {
    param([int]$Port)
    $result = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    return $result.TcpTestSucceeded
}

function Start-Service {
    param($Service)
    
    $scriptPath = Join-Path "c:\Users\Admin\civitai" $Service.Script
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "  [SKIP] $($Service.Name) - Script not found" -ForegroundColor Yellow
        return $false
    }
    
    if (Test-ServiceRunning -Port $Service.Port) {
        Write-Host "  [RUNNING] $($Service.Name) (Port $($Service.Port))" -ForegroundColor Green
        return $true
    }
    
    Write-Host "  [STARTING] $($Service.Name)..." -ForegroundColor Yellow
    Start-Process python -ArgumentList $Service.Script -WorkingDirectory "c:\Users\Admin\civitai" -WindowStyle Minimized
    
    # Wait for startup
    $attempts = 0
    while ($attempts -lt 10) {
        Start-Sleep -Milliseconds 500
        if (Test-ServiceRunning -Port $Service.Port) {
            Write-Host "  [OK] $($Service.Name) started on port $($Service.Port)" -ForegroundColor Green
            return $true
        }
        $attempts++
    }
    
    Write-Host "  [WARN] $($Service.Name) may not have started properly" -ForegroundColor Yellow
    return $false
}

function Stop-AllServices {
    Write-Host "`nStopping all MediaForge services..." -ForegroundColor Yellow
    
    # Get all python processes
    $pythonProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -eq "" -and $_.Path -match "python"
    }
    
    foreach ($proc in $pythonProcs) {
        try {
            $proc | Stop-Process -Force
            Write-Host "  Stopped process $($proc.Id)" -ForegroundColor Gray
        } catch {}
    }
    
    Write-Host "[OK] Services stopped" -ForegroundColor Green
}

function Show-Status {
    Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
    
    $running = 0
    $total = 0
    
    foreach ($svc in $Services) {
        $total++
        $isRunning = Test-ServiceRunning -Port $svc.Port
        $status = if ($isRunning) { "[RUNNING]" } else { "[STOPPED]" }
        $color = if ($isRunning) { "Green" } else { "Red" }
        
        if ($isRunning) { $running++ }
        
        $core = if ($svc.Core) { "(Core)" } else { "" }
        Write-Host "  $status $($svc.Name) - Port $($svc.Port) $core" -ForegroundColor $color
    }
    
    Write-Host "`n  Total: $running / $total services running" -ForegroundColor $(if($running -eq $total){'Green'}elseif($running -gt 0){'Yellow'}else{'Red'})
    
    return $running
}

# Main execution
Write-Banner

if ($Stop) {
    Stop-AllServices
    exit 0
}

if ($Status) {
    Show-Status
    exit 0
}

# Determine which services to start
$toStart = if ($All) {
    $Services
} elseif ($Minimal) {
    $Services | Where-Object { $_.Core -eq $true }
} else {
    # Default: Core services
    $Services | Where-Object { $_.Core -eq $true }
}

Write-Host "Starting MediaForge services..." -ForegroundColor Cyan
Write-Host ""

# Sort by priority and start
$toStart = $toStart | Sort-Object { $_.Priority }
$started = 0

foreach ($svc in $toStart) {
    if (Start-Service -Service $svc) {
        $started++
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Started $started / $($toStart.Count) services" -ForegroundColor $(if($started -eq $toStart.Count){'Green'}else{'Yellow'})
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Access:" -ForegroundColor Yellow
Write-Host "  Gateway:    http://localhost:8300" -ForegroundColor Gray
Write-Host "  Rating:     http://localhost:8196" -ForegroundColor Gray
Write-Host "  Training:   http://localhost:8230" -ForegroundColor Gray
Write-Host "  AI Brain:   http://localhost:8225" -ForegroundColor Gray
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  .\start_mediaforge.ps1 -Status    # Check status" -ForegroundColor Gray
Write-Host "  .\start_mediaforge.ps1 -Stop      # Stop all" -ForegroundColor Gray
Write-Host "  .\start_mediaforge.ps1 -All       # Start all services" -ForegroundColor Gray
Write-Host ""
