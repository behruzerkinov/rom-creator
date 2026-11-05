#!/usr/bin/env python3
"""
debloat_rom.py - Deep, safe debloating for Redmi Note 10 Pro (sweet) HyperOS port.
Removes ~2GB of heavy user-apps, offline AI models, and ad daemons,
bringing the ROM down to a lean ~4.6 GB - 4.8 GB target.
"""

import os
import shutil

TARGET_DIR = os.path.abspath("workspace/target")

PACKAGES_TO_REMOVE = [
    # 1. product/data-app (Pre-installed heavy Google & ad apps)
    "product/product/data-app/MIMediaEditorGlobal",
    "product/product/data-app/Photos",
    "product/product/data-app/Meet",
    "product/product/data-app/Drive",
    "product/product/data-app/YTMusic",
    "product/product/data-app/Videos",
    "product/product/data-app/MiGalleryLockScreenGlobalOs020",
    
    # 2. product/app (Downloadable Google apps, tracking stubs & unused bloat)
    "product/product/app/Gmail2",
    "product/product/app/YouTube",
    "product/product/app/Maps",
    "product/product/app/SpeechServicesByGoogle",
    "product/product/app/talkback",
    "product/product/app/MiLinkOS2Global",
    "product/product/app/MIUIHealthGlobal",
    "product/product/app/MIUIGuardProviderGlobal",
    "product/product/app/CatchLog",
    "product/product/app/PlayAutoInstallStubApp",
    "product/product/app/com.google.mainline.telemetry",
    "product/product/app/com.google.mainline.adservices",
    "product/product/app/com.xiaomi.ugd",
    
    # 3. product/priv-app (Heavy offline AI models, ad cleaner, car mirror)
    "product/product/priv-app/Velvet",
    "product/product/priv-app/MIUIAICR",
    "product/product/priv-app/ExtraPhotoGlobal",
    "product/product/priv-app/MIUIMusicGlobal",
    "product/product/priv-app/MIUICleanMasterGlobal-cleaner",
    "product/product/priv-app/MirrorOS2Global",
    "product/product/priv-app/Wellbeing",
    "product/product/priv-app/PersonalSafety",
    "product/product/priv-app/MIServiceGlobal",
    "product/product/priv-app/MIUIBarrage",
    "product/product/priv-app/AndroidAutoStub",
    
    # 4. system_ext/app (Telemetry & diagnostics)
    "system_ext/system_ext/app/MiuiDaemon",
    "system_ext/system_ext/app/ModemTestBox"
]


def debloat():
    print(f"[*] Starting surgical debloat on {TARGET_DIR}...")
    total_freed_bytes = 0
    removed_count = 0

    for rel_path in PACKAGES_TO_REMOVE:
        full_path = os.path.join(TARGET_DIR, rel_path)
        if os.path.exists(full_path):
            # Calculate directory size
            dir_size = 0
            if os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if not os.path.islink(fp):
                            dir_size += os.path.getsize(fp)
                shutil.rmtree(full_path)
            else:
                dir_size = os.path.getsize(full_path)
                os.remove(full_path)

            total_freed_bytes += dir_size
            removed_count += 1
            print(f" -> Removed: {rel_path} ({dir_size // (1024*1024)} MB)")

    print(f"\n[+] Debloat completed!")
    print(f"[+] Total removed targets: {removed_count}")
    print(f"[+] Total space freed: {total_freed_bytes // (1024*1024)} MB ({total_freed_bytes / (1024*1024*1024):.2f} GB)")


if __name__ == '__main__':
    debloat()

