# Redmi Note 10 Pro (sweet / sweetin) Custom ROM Kitchen Pipeline

Automated, end-to-end custom ROM porting, hybridization, RW filesystem conversion, and packaging pipeline for **Xiaomi Redmi Note 10 Pro / Pro Max** (Codename: `sweet` / `sweetin`, Platform: Qualcomm Snapdragon 732G / SM7150).

---

## Architecture & Features

- **Base Hardware Abstraction:** Preserves Qualcomm SM7150 vendor stack, camera sensor tuning (`s5khm2` 108MP / `s5kgw3` 64MP), audio ACDB calibrations, and AnyKernel3 **SuperRyzeNS** kernel.
- **Port Target (System Donor):** High-end flagship donor integration (Xiaomi Mi 11 Ultra `star` / POCO F5 `marble`) with Android 14 HyperOS framework.
- **Full Read-Write (RW) System Conversion:** 
  - Dynamic partition images mounted and repacked as clean EXT4 with spare block margins.
  - `fstab.qcom` patched from `ro` to `rw,noatime` with dm-verity and AVB enforcement disabled.
- **Kakashi Mods Center Integration:**
  - Automated release fetcher for `HyperOS-Launcher`, `HyperOS-Security-Center`, `HyperOS-App-Vault`, `ColorOS_Control_Center`, `HyperOS-Theme-Manager`, and native `HyperOS-Dialer`.
- **SweetTweaks ("Sweet Lab"):** Custom Settings preference provider embedded natively inside HyperOS Settings under *Special Features* for 120Hz refresh rate forcing, CPU governor management, and ZRAM tuning.
- **Dynamic Partition Builder:** Unified `super.img` generated via `lpmake` configured with sweet's dynamic partition group geometry (9,122,611,200 bytes).

---

## Directory Structure

```text
rom-creator/
├── tools/
│   ├── bin/                 # Native AOSP 15 lpmake, lpunpack, mke2fs, e2fsdroid, erofs tools
│   ├── brotli_extract.py    # Memory-safe chunked Brotli decompressor
│   ├── sdat2img.py          # Android sparse transfer list to raw ext4 image converter
│   ├── simg2img.py          # Android sparse image merger & converter
│   ├── patch_system.py      # Surgical de-flagshiping, build.prop & mod injector
│   ├── repack_super.py      # Dynamic super.img generator using lpmake
│   ├── fetch_kakashi_mods.py# Automated Mods-Center downloader
│   └── downloader.py        # Resumable multi-threaded chunk downloader
├── workspace/
│   ├── base/                # Extracted vendor, odm, firmware & SuperRyzeNS kernel
│   ├── donor/               # Downloaded donor ROM images
│   ├── target/              # Staged merged root filesystem
│   ├── mods/                # Downloaded Kakashi modules
│   ├── sweet_tweaks_app/    # Source tree for SweetTweaks Settings extension
│   └── output/              # Final super.img, boot.img & fastboot flashing scripts
├── unpack_and_prep.ps1      # Pipeline initializer
└── README.md
```

---

## Quick Start

### 1. Initialize Base & Toolchain
Run the master PowerShell preparation script:
```powershell
powershell -ExecutionPolicy Bypass -File .\unpack_and_prep.ps1
```

### 2. Fetch Latest Kakashi Mods
```powershell
python .\tools\fetch_kakashi_mods.py
```

### 3. Patch & Hybridize System Tree
```powershell
python .\tools\patch_system.py .\workspace\target
```

### 4. Build Dynamic Super Partition (RW)
```powershell
python .\tools\repack_super.py .\workspace\target\images .\workspace\output\super.img --rw
```

### 5. Flash via Fastboot
Put device into Fastboot mode and run:
```cmd
.\workspace\output\flash_fastboot.bat
```
