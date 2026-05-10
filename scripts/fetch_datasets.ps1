<#
.SYNOPSIS
Fetches initial datasets for the IEPA Phase 1: Data Collection pipeline.

.DESCRIPTION
- Clones the DeepFix dataset (C compiler errors).
- Creates placeholder directories for CodeNet (Python/C subset) CSV/JSON files.
- Creates placeholder directories for Synthetic data.
#>

$WorkspaceDir = "c:\Users\Pramukh\Music\final_yr_project"
$DataDir = Join-Path $WorkspaceDir "data"

Write-Host "Initializing Dataset Collection Pipeline..." -ForegroundColor Cyan

# Ensure data directory exists
if (-Not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    Write-Host "[+] Created data directory at $DataDir"
}

# 1. DeepFix
$DeepFixDir = Join-Path $DataDir "DeepFix"
if (-Not (Test-Path $DeepFixDir)) {
    Write-Host "[*] Cloning DeepFix repository..."
    git clone https://github.com/iamgroot42/DeepFix $DeepFixDir
    Write-Host "[+] DeepFix cloned successfully." -ForegroundColor Green
} else {
    Write-Host "[-] DeepFix already exists at $DeepFixDir, skipping clone." -ForegroundColor Yellow
}

# 2. CodeNet Placeholders
$CodeNetDir = Join-Path $DataDir "CodeNet_subset"
if (-Not (Test-Path $CodeNetDir)) {
    New-Item -ItemType Directory -Force -Path $CodeNetDir | Out-Null
    New-Item -ItemType File -Force -Path (Join-Path $CodeNetDir ".gitkeep") | Out-Null
    Write-Host "[+] Created CodeNet subset placeholder folder at $CodeNetDir" -ForegroundColor Green
    Write-Host "    -> NOTE: Drop kaggle CSV/JSON files here later." -ForegroundColor Yellow
}

# 3. Synthetic Programs Placeholders
$SyntheticDir = Join-Path $DataDir "synthetic"
$SyntheticPythonDir = Join-Path $SyntheticDir "python"
$SyntheticCDir = Join-Path $SyntheticDir "c"

if (-Not (Test-Path $SyntheticPythonDir)) {
    New-Item -ItemType Directory -Force -Path $SyntheticPythonDir | Out-Null
    New-Item -ItemType File -Force -Path (Join-Path $SyntheticPythonDir ".gitkeep") | Out-Null
}
if (-Not (Test-Path $SyntheticCDir)) {
    New-Item -ItemType Directory -Force -Path $SyntheticCDir | Out-Null
    New-Item -ItemType File -Force -Path (Join-Path $SyntheticCDir ".gitkeep") | Out-Null
}
Write-Host "[+] Created Synthetic dataset placeholder folders (C / Python)" -ForegroundColor Green

Write-Host "Dataset initialization completed successfully." -ForegroundColor Cyan
