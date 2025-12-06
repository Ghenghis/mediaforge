# Setup Uncensored Vision Models
# Run this after the base models finish downloading

Write-Host "=== Building Uncensored Vision Models ===" -ForegroundColor Cyan

$modelDir = "C:\Users\Admin\civitai\models"

# Build uncensored variants
Write-Host "`n[1/3] Building llava-uncensored..." -ForegroundColor Yellow
ollama create llava-uncensored -f "$modelDir\Modelfile.llava-uncensored"

Write-Host "`n[2/3] Building minicpm-uncensored..." -ForegroundColor Yellow
ollama create minicpm-uncensored -f "$modelDir\Modelfile.minicpm-uncensored"

Write-Host "`n[3/3] Building llava-llama3-uncensored..." -ForegroundColor Yellow
ollama create llava-llama3-uncensored -f "$modelDir\Modelfile.llava-llama3-uncensored"

Write-Host "`n=== Available Vision Models ===" -ForegroundColor Green
ollama list | Select-String -Pattern "llava|minicpm"

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Cyan
Write-Host "Use these models for video filtering:"
Write-Host "  - llava-uncensored       (High quality, 7.4GB)"
Write-Host "  - minicpm-uncensored     (Fast, 4.4GB)"
Write-Host "  - llava-llama3-uncensored (Modern, 4.9GB)"
