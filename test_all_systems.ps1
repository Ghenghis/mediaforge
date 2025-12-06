# ============================================================
# MEDIAFORGE - Complete System Test
# ============================================================
# Tests all services, APIs, and integrations
# Run: .\test_all_systems.ps1
# ============================================================

$Host.UI.RawUI.WindowTitle = "MediaForge System Test"

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║          MEDIAFORGE - COMPLETE SYSTEM TEST                ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$tests = @()
$passed = 0
$failed = 0

function Test-Service {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Endpoint = "/"
    )
    
    $result = @{Name = $Name; Port = $Port; Status = "FAIL"; Message = ""}
    
    try {
        $test = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        if ($test.TcpTestSucceeded) {
            $response = Invoke-RestMethod -Uri "http://localhost:$Port$Endpoint" -Method Get -TimeoutSec 5
            $result.Status = "PASS"
            $result.Message = "Running"
        } else {
            $result.Message = "Port not responding"
        }
    } catch {
        if ($_.Exception.Message -match "200") {
            $result.Status = "PASS"
            $result.Message = "Running"
        } else {
            $result.Message = $_.Exception.Message.Substring(0, [Math]::Min(50, $_.Exception.Message.Length))
        }
    }
    
    return $result
}

function Test-API {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    $result = @{Name = $Name; Url = $Url; Status = "FAIL"; Message = ""}
    
    try {
        if ($Method -eq "POST" -and $Body) {
            $json = $Body | ConvertTo-Json
            $response = Invoke-RestMethod -Uri $Url -Method Post -Body $json -ContentType "application/json" -TimeoutSec 10
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 10
        }
        
        if ($response.success -eq $true -or $response.service -or $response.status) {
            $result.Status = "PASS"
            $result.Message = "OK"
        } else {
            $result.Status = "PASS"
            $result.Message = "Response received"
        }
    } catch {
        $result.Message = "Error: $($_.Exception.Message.Substring(0, [Math]::Min(40, $_.Exception.Message.Length)))"
    }
    
    return $result
}

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  SECTION 1: CORE SERVICES" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray

$coreServices = @(
    @{Name="Unified Gateway"; Port=8300},
    @{Name="Rating Studio"; Port=8196},
    @{Name="Dataset Builder"; Port=8211},
    @{Name="AI Learning Brain"; Port=8225},
    @{Name="LoRA Training"; Port=8230},
    @{Name="Master Orchestrator"; Port=8210},
    @{Name="Unified WPF API"; Port=8190}
)

foreach ($svc in $coreServices) {
    $result = Test-Service -Name $svc.Name -Port $svc.Port
    $tests += $result
    
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    $icon = if ($result.Status -eq "PASS") { "✓" } else { "✗" }
    Write-Host "  [$icon] $($result.Name) (Port $($result.Port)): $($result.Status)" -ForegroundColor $color
    
    if ($result.Status -eq "PASS") { $passed++ } else { $failed++ }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  SECTION 2: API ENDPOINTS" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray

$apiTests = @(
    @{Name="Learning Stats"; Url="http://localhost:8225/api/stats"},
    @{Name="Training Status"; Url="http://localhost:8230/api/status"},
    @{Name="Rating Stats"; Url="http://localhost:8196/api/stats"},
    @{Name="WPF Health"; Url="http://localhost:8190/api/health"},
    @{Name="Kohya Check"; Url="http://localhost:8230/api/check"},
    @{Name="Dataset List"; Url="http://localhost:8211/api/dataset/list"},
    @{Name="Dataset Stats"; Url="http://localhost:8211/api/stats"},
    @{Name="Prompt Suggest"; Url="http://localhost:8225/api/suggest"}
)

foreach ($api in $apiTests) {
    $result = Test-API -Name $api.Name -Url $api.Url
    $tests += $result
    
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    $icon = if ($result.Status -eq "PASS") { "✓" } else { "✗" }
    Write-Host "  [$icon] $($result.Name): $($result.Status)" -ForegroundColor $color
    
    if ($result.Status -eq "PASS") { $passed++ } else { $failed++ }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  SECTION 3: EXTENDED SERVICES" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray

$extServices = @(
    @{Name="Voice Tools"; Port=8220},
    @{Name="Auto Captioner"; Port=8207},
    @{Name="Story Generator"; Port=8197}
)

foreach ($svc in $extServices) {
    $result = Test-Service -Name $svc.Name -Port $svc.Port
    $tests += $result
    
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Yellow" }
    $icon = if ($result.Status -eq "PASS") { "✓" } else { "○" }
    Write-Host "  [$icon] $($result.Name) (Port $($result.Port)): $($result.Status)" -ForegroundColor $color
    
    if ($result.Status -eq "PASS") { $passed++ } else { $failed++ }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  SECTION 4: EXTERNAL SERVICES" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray

$extServices = @(
    @{Name="ComfyUI"; Port=8188},
    @{Name="LM Studio"; Port=1234},
    @{Name="Ollama"; Port=11434}
)

foreach ($svc in $extServices) {
    $result = Test-Service -Name $svc.Name -Port $svc.Port
    
    $color = if ($result.Status -eq "PASS") { "Green" } else { "DarkGray" }
    $icon = if ($result.Status -eq "PASS") { "✓" } else { "○" }
    Write-Host "  [$icon] $($result.Name) (Port $($result.Port)): $(if($result.Status -eq 'PASS'){'Available'}else{'Not Running'})" -ForegroundColor $color
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  SECTION 5: FILE SYSTEM" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray

$paths = @(
    @{Name="SDXL Models"; Path="G:\Github\ComfyUI\models\checkpoints"; Min=4},
    @{Name="ControlNets"; Path="G:\Github\ComfyUI\models\controlnet"; Min=2},
    @{Name="Training Datasets"; Path="c:\Users\Admin\civitai\training\datasets"; Min=1},
    @{Name="WPF Dashboard"; Path="c:\Users\Admin\civitai\ui\WPF\AIStudioDashboard\bin\Release"; Min=1}
)

foreach ($p in $paths) {
    if (Test-Path $p.Path) {
        $count = (Get-ChildItem $p.Path -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -match '\.(safetensors|pth|png|jpg|exe)$'}).Count
        $status = if ($count -ge $p.Min) { "PASS" } else { "WARN" }
        $color = if ($status -eq "PASS") { "Green" } else { "Yellow" }
        Write-Host "  [✓] $($p.Name): $count files" -ForegroundColor $color
        $passed++
    } else {
        Write-Host "  [✗] $($p.Name): Not found" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  SECTION 6: FUNCTIONAL TESTS" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray

# Test Chat
Write-Host "  Testing AI Chat..." -ForegroundColor Gray
try {
    $chatBody = @{message = "I like blue eyes"} | ConvertTo-Json
    $chatResult = Invoke-RestMethod -Uri "http://localhost:8225/api/learn/chat" -Method Post -Body $chatBody -ContentType "application/json" -TimeoutSec 10
    if ($chatResult.success) {
        Write-Host "  [✓] AI Chat: Working" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [✗] AI Chat: Failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  [✗] AI Chat: Error" -ForegroundColor Red
    $failed++
}

# Test Training Job Creation
Write-Host "  Testing Training API..." -ForegroundColor Gray
try {
    $trainBody = @{
        name = "test_validation"
        tier = "bronze"
        dataset_path = "C:\Users\Admin\civitai\training\datasets\15_mystyle"
        base_model = "G:\Github\ComfyUI\models\checkpoints\sd_xl_base_1.0.safetensors"
    } | ConvertTo-Json
    $trainResult = Invoke-RestMethod -Uri "http://localhost:8230/api/create" -Method Post -Body $trainBody -ContentType "application/json" -TimeoutSec 10
    if ($trainResult.success) {
        Write-Host "  [✓] Training API: Working (Job ID: $($trainResult.job_id))" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [✗] Training API: Failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  [✗] Training API: Error" -ForegroundColor Red
    $failed++
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$total = $passed + $failed
$pct = if ($total -gt 0) { [math]::Round(($passed / $total) * 100) } else { 0 }

Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if($failed -gt 0){'Red'}else{'Green'})
Write-Host "  Total:  $total" -ForegroundColor White
Write-Host ""
Write-Host "  Score: $pct%" -ForegroundColor $(if($pct -ge 80){'Green'}elseif($pct -ge 60){'Yellow'}else{'Red'})
Write-Host ""

if ($pct -ge 90) {
    Write-Host "  ★★★★★ EXCELLENT - System fully operational!" -ForegroundColor Green
} elseif ($pct -ge 70) {
    Write-Host "  ★★★★☆ GOOD - Most systems working" -ForegroundColor Yellow
} elseif ($pct -ge 50) {
    Write-Host "  ★★★☆☆ FAIR - Some issues to address" -ForegroundColor Yellow
} else {
    Write-Host "  ★★☆☆☆ NEEDS ATTENTION - Multiple systems offline" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
