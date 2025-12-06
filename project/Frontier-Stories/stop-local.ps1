# Frontier-Stories Stop Script
# Stops all Docker containers

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "Stopping Frontier-Stories services..." -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

# Stop Docker containers
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All services stopped." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Warning: Some services may not have stopped cleanly." -ForegroundColor Yellow
    Write-Host "Run 'docker-compose down -v' to force cleanup." -ForegroundColor Gray
}
