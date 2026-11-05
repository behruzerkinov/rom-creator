# Redmi Note 10 Pro (sweet / sweetin) Custom ROM Kitchen Pipeline

Automated, end-to-end custom ROM porting, hybridization, RW filesystem conversion, and packaging pipeline for **Xiaomi Redmi Note 10 Pro / Pro Max** (Codename: `sweet` / `sweetin`, Platform: Qualcomm Snapdragon 732G / SM7150).

---

## Architecture & Features

- **Base Hardware Abstraction:** Preserves Qualcomm SM7150 stock vendor stack (`V14.0.9.0.TKFEUXM`), audio ACDB calibrations, and AnyKernel3 **SuperRyzeNS** custom kernel.
- **Port Target (System Donor):** Xiaomi Mi 11 Ultra Global (`star` — `OS2.0.7.0.UKAMIXM`, Android 14 HyperOS) hybrid port.
- **Full Read-Write (RW) System Conversion:** 
  - Dynamic partition images mounted and repacked as clean EXT4 with spare block margins using `mke2fs` and `e2fsdroid`.
  - `fstab.default` / `fstab.qcom` patched from `ro` to `rw,barrier=1,discard` with AVB/dm-verity enforcement stripped.
  - Dynamic partition table generated via `lpmake` with attribute `none` (Read-Write) across all dynamic partitions (`system`, `system_ext`, `product`, `vendor`, `odm`).
- **Surgical De-Flagshiping:**
  - Removal of Mi 11 Ultra secondary rear display HAL (`MiuiSubScreenUi`) to prevent SystemUI and SurfaceFlinger crashloops.
  - Clean purge of telemetry daemons, ad modules (`MSA-Global`, `AnalyticsCore`), and Google Feedback.
- **Kakashi Mods Integration:**
  - `HyperOS-Launcher` (v7.5F with MiuiHome & XiaomiEuExt).
  - `HyperOS-Security-Center` (v7 with unlocked Game Turbo & Performance mode).
  - `HyperOS-App-Vault` (v5).
  - `ColorOS_Control_Center` (v4 quick settings plugin).
  - `HyperOS-Theme-Manager` (v7).
  - `HyperOS-Dialer` (Native MIUI Dialer, Contacts, MMS, and call recording).
- **SweetTweaks ("Sweet Lab"):** Custom Settings preference provider embedded natively inside HyperOS Settings under *Special Features* for 120Hz refresh rate forcing, CPU governor management (`reflex`, `moonbeam`, `schedhorizon`), and ZRAM tuning.
- **Dynamic Partition Geometry:** Block-aligned payload exactly matching `sweet` dynamic partition group capacity (`9,122,611,200` bytes) and super device capacity (`9,126,805,504` bytes).
- **Indian Variant (`sweetin`) Support:** Included Samsung GW3 64MP sensor tuning fix (`sweetin_camera_tint_fix.zip`).

---

## Directory Structure

```text
rom-creator/
├── tools/
│   ├── bin/                 # Native AOSP 15 lpmake, lpunpack, mke2fs, e2fsdroid, magiskboot, apktool
│   ├── brotli_extract.py    # Memory-safe chunked Brotli decompressor
│   ├── sdat2img.py          # Android sparse transfer list to raw ext4 image converter
│   ├── patch_system.py      # Surgical de-flagshiping, build.prop, fs_config sync & mod injector
│   ├── build_all_images.py  # EXT4 partition image builder with SELinux contexts
│   ├── repack_super.py      # Dynamic super.img generator using lpmake
│   └── fetch_kakashi_mods.py# Automated Mods-Center downloader
├── workspace/
│   ├── base/                # Extracted vendor, odm, firmware & SuperRyzeNS kernel
│   ├── donor/               # Downloaded donor ROM images (star OS2.0.7.0)
│   ├── target/              # Staged merged root filesystem & repacked ext4 images
│   ├── mods/                # Downloaded Kakashi modules
│   ├── sweet_tweaks_app/    # Source tree for SweetTweaks Settings extension
│   └── output/              # Final super.img, boot.img, dtbo.img, vbmeta.img & flasher
└── README.md
```

---

## Execution Pipeline

### 1. Patch & Hybridize System Tree
De-flagship, update `build.prop` identities to `sweet`, inject Kakashi mods, and sync `fs_config`:
```powershell
python .\tools\patch_system.py .\workspace\target .\workspace\mods
```

### 2. Build Ext4 Partition Images (RW)
Construct `system.img`, `system_ext.img`, and `product.img` with SELinux labeling:
```powershell
python .\tools\build_all_images.py
```

### 3. Build Dynamic Super Partition (RW)
Pack dynamic partitions into unified `super.img`:
```powershell
python .\tools\repack_super.py .\workspace\target\images .\workspace\output\super.img --rw
```

### 4. Flash via Fastboot
Connect device in Fastboot mode and run:
```cmd
.\workspace\output\flash_fastboot.bat
```
