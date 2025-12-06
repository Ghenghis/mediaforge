# ImDisk Installation Script for RAMDrive Support
# ================================================
# Run this as Administrator to enable RAMDrives

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ImDisk Toolkit Installation" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n[ERROR] Please run this script as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Download location
$downloadUrl = "https://sourceforge.net/projects/imdisk-toolkit/files/latest/download"
$tempDir = "$env:TEMP\imdisk_install"
$installerPath = "$tempDir\imdisk_setup.exe"

# Create temp directory
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

Write-Host "`n[1/3] Downloading ImDisk Toolkit..." -ForegroundColor Yellow

try {
    # Download installer
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $installerPath)
    Write-Host "[OK] Download complete" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Download failed: $_" -ForegroundColor Red
    Write-Host "`nPlease download manually from:" -ForegroundColor Yellow
    Write-Host "https://sourceforge.net/projects/imdisk-toolkit/" -ForegroundColor Cyan
    exit 1
}

Write-Host "`n[2/3] Installing ImDisk..." -ForegroundColor Yellow

try {
    # Run installer silently
    Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait -NoNewWindow
    Write-Host "[OK] Installation complete" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Installation failed: $_" -ForegroundColor Red
    Write-Host "`nPlease install manually by running: $installerPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[3/3] Verifying installation..." -ForegroundColor Yellow

# Check if imdisk is available
$imdiskPath = "C:\Windows\System32\imdisk.exe"
if (Test-Path $imdiskPath) {
    Write-Host "[OK] ImDisk installed successfully!" -ForegroundColor Green
    
    # Test creating a small RAMDisk
    Write-Host "`nTesting RAMDisk creation..." -ForegroundColor Yellow
    try {
        & imdisk -a -s 100M -m X: -p "/fs:ntfs /q /y" 2>$null
        Start-Sleep -Seconds 2
        
        if (Test-Path "X:\") {
            Write-Host "[OK] RAMDisk test successful!" -ForegroundColor Green
            # Remove test disk
            & imdisk -D -m X: 2>$null
        }
    } catch {
        Write-Host "[WARN] Test failed, but ImDisk is installed" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] ImDisk not found at expected location" -ForegroundColor Yellow
    Write-Host "You may need to reboot" -ForegroundColor Yellow
}

# Cleanup
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Reboot your computer (recommended)" -ForegroundColor White
Write-Host "2. Run: python -m performance.ramdrive_manager --init" -ForegroundColor White
Write-Host "`nThis will create:" -ForegroundColor Yellow
Write-Host "  R: - 16GB Training Data" -ForegroundColor White
Write-Host "  M: - 24GB Model Cache" -ForegroundColor White
Write-Host "  T: - 8GB Temp Workspace" -ForegroundColor White
Write-Host "  O: - 8GB Output Cache" -ForegroundColor White
Write-Host "  Total: 56GB RAMDrives" -ForegroundColor Cyan
