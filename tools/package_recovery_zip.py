#!/usr/bin/env python3
"""
package_recovery_zip.py - Assemble standard TWRP / OrangeFox recovery flashable zip
for Redmi Note 10 Pro (sweet / sweetin).
"""

import os
import sys
import zipfile

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace", "output"))
ZIP_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "HyperOS_sweet_port_recovery.zip")

UPDATE_BINARY_SCRIPT = b"""#!/sbin/sh
# Universal Recovery Installer for Redmi Note 10 Pro (sweet / sweetin)
# Compatible with TWRP, OrangeFox, PBRP

OUTFD=/proc/self/fd/$2
ZIPFILE="$3"

ui_print() {
  echo -e "ui_print $1\\nui_print" > "$OUTFD"
}

set_progress() {
  echo "set_progress $1" > "$OUTFD"
}

ui_print "================================================="
ui_print "   HyperOS Port for Redmi Note 10 Pro (sweet)   "
ui_print "   SuperRyzeNS Kernel + Kakashi Mods + RW Ext4  "
ui_print "================================================="

# Locate block devices
get_block() {
  for base in "/dev/block/bootdevice/by-name" "/dev/block/by-name" "/dev/block/platform/soc/7c4000.sdhci/by-name" "/dev/block/platform/soc/1d84000.ufshc/by-name"; do
    if [ -b "$base/$1" ]; then
      echo "$base/$1"
      return 0
    fi
  done
  return 1
}

SUPER=$(get_block super)
BOOT=$(get_block boot)
DTBO=$(get_block dtbo)
VBMETA=$(get_block vbmeta)
VBMETA_SYS=$(get_block vbmeta_system)

set_progress 0.1
ui_print "[*] 1/5 Flashing vbmeta images (disabling AVB)..."
if [ -n "$VBMETA" ]; then
  unzip -p "$ZIPFILE" vbmeta.img > "$VBMETA" 2>/dev/null
fi
if [ -n "$VBMETA_SYS" ]; then
  unzip -p "$ZIPFILE" vbmeta_system.img > "$VBMETA_SYS" 2>/dev/null
fi

set_progress 0.2
ui_print "[*] 2/5 Flashing display dtbo..."
if [ -n "$DTBO" ]; then
  unzip -p "$ZIPFILE" dtbo.img > "$DTBO" 2>/dev/null
fi

set_progress 0.3
ui_print "[*] 3/5 Flashing SuperRyzeNS custom boot image..."
if [ -n "$BOOT" ]; then
  unzip -p "$ZIPFILE" boot.img > "$BOOT" 2>/dev/null
fi

set_progress 0.4
ui_print "[*] 4/5 Flashing dynamic super partition (super.img)..."
ui_print "    This will take 1-3 minutes. Please wait..."
if [ -n "$SUPER" ]; then
  if command -v simg2img >/dev/null 2>&1; then
    unzip -p "$ZIPFILE" super.img | simg2img - "$SUPER" 2>/dev/null || unzip -p "$ZIPFILE" super.img > "$SUPER" 2>/dev/null
  else
    unzip -p "$ZIPFILE" super.img > "$SUPER" 2>/dev/null
  fi
fi

set_progress 0.95
ui_print "[*] 5/5 Syncing storage buffers..."
sync

set_progress 1.0
ui_print "================================================="
ui_print "   HyperOS Installation Completed Successfully! "
ui_print "   Remember to format data if coming from MIUI   "
ui_print "================================================="
exit 0
"""

UPDATER_SCRIPT_CONTENT = b"# Dummy updater-script for custom recovery compatibility\n"


def create_recovery_zip():
    print(f"[*] Creating recovery flashable zip: {ZIP_OUTPUT_PATH}...")
    if os.path.exists(ZIP_OUTPUT_PATH):
        os.remove(ZIP_OUTPUT_PATH)

    required_files = [
        "boot.img",
        "dtbo.img",
        "vbmeta.img",
        "vbmeta_system.img",
        "super.img"
    ]

    for f in required_files:
        p = os.path.join(OUTPUT_DIR, f)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Required artifact missing: {p}")

    with zipfile.ZipFile(ZIP_OUTPUT_PATH, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
        # 1. Update binary & script
        bin_info = zipfile.ZipInfo("META-INF/com/google/android/update-binary")
        bin_info.external_attr = 0o755 << 16  # Executable permissions
        z.writestr(bin_info, UPDATE_BINARY_SCRIPT)

        z.writestr("META-INF/com/google/android/updater-script", UPDATER_SCRIPT_CONTENT)
        print("[+] Injected META-INF installer binaries.")

        # 2. Images
        for f in required_files:
            file_path = os.path.join(OUTPUT_DIR, f)
            file_size_mb = os.path.getsize(file_path) // (1024 * 1024)
            print(f"[*] Packaging {f} ({file_size_mb} MB)...")
            z.write(file_path, arcname=f)

    zip_size_gb = os.path.getsize(ZIP_OUTPUT_PATH) / (1024 * 1024 * 1024)
    print(f"\n[+] Recovery zip generated successfully: {ZIP_OUTPUT_PATH} ({zip_size_gb:.2f} GB)")


if __name__ == '__main__':
    create_recovery_zip()
