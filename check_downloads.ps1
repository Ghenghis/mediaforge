# Quick script to check model download progress
Write-Host "=== Model Download Status ===" -ForegroundColor Cyan
Write-Host ""

$models = @{
    "checkpoints" = @(
        @{name="sd_xl_base_1.0.safetensors"; target=6.94},
        @{name="sd_xl_refiner_1.0.safetensors"; target=6.08},
        @{name="ponyDiffusionV6XL.safetensors"; target=6.46},
        @{name="juggernautXL_v9.safetensors"; target=6.46}
    )
    "controlnet" = @(
        @{name="diffusers_xl_canny_full.safetensors"; target=2.5},
        @{name="diffusers_xl_depth_full.safetensors"; target=2.5}
    )
    "vae" = @(
        @{name="sdxl_vae.safetensors"; target=0.31},
        @{name="vae-ft-mse-840000-ema-pruned.safetensors"; target=0.31}
    )
    "upscale_models" = @(
        @{name="4x-UltraSharp.pth"; target=0.06},
        @{name="RealESRGAN_x4plus.pth"; target=0.06}
    )
}

$base = "G:/Github/ComfyUI/models"
$totalDone = 0
$totalNeeded = 0

foreach ($cat in $models.Keys) {
    Write-Host "$($cat.ToUpper()):" -ForegroundColor Yellow
    foreach ($m in $models[$cat]) {
        $path = Join-Path $base $cat $m.name
        $current = if (Test-Path $path) { [math]::Round((Get-Item $path).Length / 1GB, 2) } else { 0 }
        $pct = if ($m.target -gt 0) { [math]::Round(($current / $m.target) * 100) } else { 0 }
        
        $status = if ($pct -ge 99) { "[DONE]" } elseif ($pct -gt 0) { "[{0,3}%]" -f $pct } else { "[----]" }
        $color = if ($pct -ge 99) { "Green" } elseif ($pct -gt 0) { "Yellow" } else { "Gray" }
        
        Write-Host "  $status $($m.name) ($current/$($m.target)GB)" -ForegroundColor $color
        
        if ($pct -ge 99) { $totalDone++ }
        $totalNeeded++
    }
    Write-Host ""
}

Write-Host "Summary: $totalDone/$totalNeeded models complete" -ForegroundColor Cyan
