# Frontier-Stories Local Development Startup Script
# Windows 11 / PowerShell
# Automatically starts all services for local development

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Frontier-Stories Local Development   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow

# Check Node.js
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Node.js is not installed" -ForegroundColor Red
    Write-Host "  Install from: https://nodejs.org/" -ForegroundColor Gray
    exit 1
}
Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green

# Check Docker
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Docker is not installed or not running" -ForegroundColor Red
    Write-Host "  Install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Gray
    exit 1
}
Write-Host "  Docker: $dockerVersion" -ForegroundColor Green

# Check if Docker daemon is running
docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  WARNING: Docker daemon is not running. Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
    Write-Host "  Waiting for Docker to start (30 seconds)..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
}

# Check LM Studio
Write-Host ""
Write-Host "[2/6] Checking LM Studio..." -ForegroundColor Yellow
$lmStudioRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:1234/v1/models" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $lmStudioRunning = $true
        Write-Host "  LM Studio: Running on port 1234" -ForegroundColor Green
    }
} catch {
    Write-Host "  WARNING: LM Studio not detected on port 1234" -ForegroundColor Yellow
    Write-Host "  Please start LM Studio and load a model" -ForegroundColor Gray
    Write-Host "  The app will still start, but AI features won't work" -ForegroundColor Gray
}

# Install dependencies
Write-Host ""
Write-Host "[3/6] Installing dependencies..." -ForegroundColor Yellow
Set-Location $ProjectRoot
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: npm install failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Dependencies already installed" -ForegroundColor Green
}

# Start Docker containers
Write-Host ""
Write-Host "[4/6] Starting Docker containers..." -ForegroundColor Yellow

# Check if containers are already running
$containersRunning = docker ps --filter "name=frontier-stories" --format "{{.Names}}" 2>$null
if ($containersRunning) {
    Write-Host "  Containers already running: $containersRunning" -ForegroundColor Green
} else {
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Failed to start Docker containers" -ForegroundColor Red
        Write-Host "  Try: docker-compose down -v && docker-compose up -d" -ForegroundColor Gray
        exit 1
    }
    Write-Host "  Waiting for containers to be healthy (15 seconds)..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
}

# Check container status
Write-Host ""
Write-Host "[5/6] Verifying services..." -ForegroundColor Yellow

# Check PostgreSQL
try {
    docker exec frontier-stories-postgres pg_isready -U postgres 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  PostgreSQL: Running" -ForegroundColor Green
    } else {
        Write-Host "  PostgreSQL: Starting..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  PostgreSQL: Container not found" -ForegroundColor Red
}

# Check Functions server
try {
    $functionsResponse = Invoke-WebRequest -Uri "http://localhost:3001/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($functionsResponse.StatusCode -eq 200) {
        Write-Host "  Functions API: Running" -ForegroundColor Green
    }
} catch {
    Write-Host "  Functions API: Starting..." -ForegroundColor Yellow
}

# Start development server
Write-Host ""
Write-Host "[6/6] Starting development server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Services Ready!                      " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
$services = @{
    "PostgreSQL" = "http://localhost:5433"
    "Functions" = "http://localhost:3001/health"
    "Frontend" = "http://localhost:5173"
}
Write-Host "  Frontend:      $($services["Frontend"]) " -ForegroundColor White
Write-Host "  Settings:      $($services["Frontend"])/settings" -ForegroundColor White
Write-Host "  pgAdmin:       http://localhost:5050" -ForegroundColor White
Write-Host "  Functions API: $($services["Functions"]) " -ForegroundColor White
Write-Host "  LM Studio:     http://localhost:1234" -ForegroundColor White
Write-Host ""
Write-Host "  pgAdmin Login: admin@frontier.dev / admin" -ForegroundColor Gray
Write-Host ""
Write-Host "  Press Ctrl+C to stop the dev server" -ForegroundColor Gray
Write-Host ""

# Start Vite dev server (this will run in foreground)
npm run dev
