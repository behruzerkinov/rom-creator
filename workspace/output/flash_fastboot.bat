@echo off
setlocal enabledelayedexpansion
title Redmi Note 10 Pro (sweet) HyperOS Fastboot Flasher
color 0b

echo ================================================================
echo   REDMI NOTE 10 PRO (sweet/sweetin) HYPEROS FASTBOOT INSTALLER
echo   Android 14 Custom Port with SuperRyzeNS Kernel &amp; Kakashi Mods
echo ================================================================
echo.

:: Check fastboot connection
echo [*] Checking fastboot connection...
fastboot devices &gt; nul 2&gt;&amp;1
if %errorlevel% neq 0 (
    echo [!] Fastboot is not in PATH or device is not detected.
    echo [*] Attempting local tools\bin\fastboot if available...
)

echo [*] Device detected. Flashing firmware and dynamic partitions...
echo.

echo [*] 1/6 Flashing dtbo and vbmeta with verity disabled...
fastboot flash dtbo dtbo.img
fastboot flash --disable-verity --disable-verification vbmeta vbmeta.img
fastboot flash --disable-verity --disable-verification vbmeta_system vbmeta_system.img

echo [*] 2/6 Flashing custom SuperRyzeNS boot image...
fastboot flash boot boot.img

echo [*] 3/6 Flashing dynamic super partition (super.img)...
fastboot flash super super.img

echo.
echo ================================================================
echo   INSTALLATION COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
set /p WIPE="Do you want to format userdata (WIPE DATA - clean flash)? (Y/N): "
if /i "%WIPE%"=="Y" (
    echo [*] Formatting userdata...
    fastboot erase userdata
    fastboot erase metadata
)

echo [*] Rebooting system...
fastboot reboot
echo [*] All done! Enjoy HyperOS on sweet.
pause

