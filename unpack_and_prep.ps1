<#
.SYNOPSIS
    Automated Custom ROM Kitchen: Base Unpacking & Toolchain Setup for Redmi Note 10 Pro (sweet)
.DESCRIPTION
    Extracts base vendor/odm stack, prepares RW filesystem staging, integrates SuperRyzeNS kernel,
    and stages donor partition extraction pipeline.
#>

[CmdletBinding()]
param(
    [string]$BaseZipPath = "C:\Users\Retention Manager\Downloads\AyuGram Desktop\HyperOS2-Global-Sweet.zip",
    [string]$KernelZipPath = "C:\Users\Retention Manager\Downloads\AyuGram Desktop\SUperRyzeNS-MIUI-22102026-1926.zip",
    [string]$WorkspaceRoot = "C:\Users\Retention Manager\Documents\rom-creator\workspace"
)

$ErrorActionPreference = "Stop"

$ToolsDir = "C:\Users\Retention Manager\Documents\rom-creator\tools"
$BinDir = "$ToolsDir\bin"
$SevenZip = "C:\Program Files\7-Zip\7z.exe"
$PythonExe = "python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  REDMI NOTE 10 PRO (sweet) KITCHEN: PIPELINE INITIALIZER " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify required tools
Write-Host "`n[*] Verifying local toolchain..." -ForegroundColor Yellow
$RequiredBinaries = @(
    "$BinDir\lpmake.exe",
    "$BinDir\lpunpack.exe",
    "$BinDir\mke2fs.exe",
    "$BinDir\e2fsdroid.exe",
    "$BinDir\extract.erofs.exe",
    "$ToolsDir\brotli_extract.py",
    "$ToolsDir\sdat2img.py"
)

foreach ($Tool in $RequiredBinaries) {
    if (-not (Test-Path $Tool)) {
        throw "Missing required toolchain component: $Tool"
    }
}
Write-Host "[+] All toolchain binaries and Python scripts verified." -ForegroundColor Green

# 2. Stage Base Firmware
Write-Host "`n[*] Staging Base Firmware from: $BaseZipPath" -ForegroundColor Yellow
if (-not (Test-Path $BaseZipPath)) {
    throw "Base firmware ZIP not found at: $BaseZipPath"
}

$BaseExtractDir = "$WorkspaceRoot\base\extracted"
$BaseImagesDir = "$WorkspaceRoot\base\images"
New-Item -ItemType Directory -Path $BaseExtractDir, $BaseImagesDir -Force | Out-Null

Write-Host "[*] Extracting base vendor, odm, boot, and firmware..." -ForegroundColor Gray
& $SevenZip x "$BaseZipPath" -o"$BaseExtractDir" vendor.new.dat.br vendor.transfer.list odm.new.dat.br odm.transfer.list boot.img firmware-update\* -aoa | Out-Null

# 3. Decompress Brotli .new.dat.br for vendor and odm
foreach ($Partition in @("vendor", "odm")) {
    $BrFile = "$BaseExtractDir\$Partition.new.dat.br"
    $DatFile = "$BaseExtractDir\$Partition.new.dat"
    $ListFile = "$BaseExtractDir\$Partition.transfer.list"
    $ImgFile = "$BaseImagesDir\$Partition.img"

    if (Test-Path $BrFile) {
        Write-Host "[*] Decompressing Brotli payload for $Partition..." -ForegroundColor Gray
        & $PythonExe "$ToolsDir\brotli_extract.py" "$BrFile" "$DatFile"
    }

    if ((Test-Path $DatFile) -and (Test-Path $ListFile)) {
        Write-Host "[*] Converting sparse transfer list to raw ext4/erofs image: $Partition.img..." -ForegroundColor Gray
        & $PythonExe "$ToolsDir\sdat2img.py" "$ListFile" "$DatFile" "$ImgFile"
    }
}

# 4. Integrate SuperRyzeNS Kernel
Write-Host "`n[*] Staging SuperRyzeNS Kernel from: $KernelZipPath" -ForegroundColor Yellow
if (Test-Path $KernelZipPath) {
    $KernelExtractDir = "$WorkspaceRoot\base\kernel_superryzens"
    New-Item -ItemType Directory -Path $KernelExtractDir -Force | Out-Null
    & $SevenZip x "$KernelZipPath" -o"$KernelExtractDir" -aoa | Out-Null
    Write-Host "[+] SuperRyzeNS kernel extracted (Image.gz, dtb.img, dtbo.img ready)." -ForegroundColor Green
} else {
    Write-Host "[!] Warning: Kernel zip not found at path, skipping kernel staging." -ForegroundColor Yellow
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  BASE EXTRACTION COMPLETE. READY FOR DONOR INTEGRATION!  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

