#!/usr/bin/env python3
"""
package_recovery_zip.py - Assemble standard TWRP / OrangeFox recovery flashable zip
for Redmi Note 10 Pro (sweet / sweetin).
Features:
- Robust multi-path block device detection (resolves symlinks in toybox/busybox)
- Chunked 512MB raw dynamic partition streaming (prevents Scudo allocator OOM/SIGABRT in toybox unzip)
- Precise block-aligned dd seeking (bs=4M, seek=128 per chunk) directly to UFS storage
- Device mapper unmount and unmapping (prevents EBUSY partition locking)
- Permissive AVB and SuperRyzeNS kernel injection
"""

import os
import sys
import subprocess
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "workspace", "output")
ZIP_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "HyperOS_sweet_port_recovery.zip")
SIMG2IMG_BIN = os.path.join(PROJECT_ROOT, "tools", "bin", "simg2img.exe")

UPDATE_BINARY_SCRIPT = b"""#!/bin/sh
# Universal Recovery Installer for Redmi Note 10 Pro (sweet / sweetin)
# Compatible with TWRP, OrangeFox, PBRP

set -o pipefail 2>/dev/null || true

OUTFD=/proc/self/fd/$2
ZIPFILE="$3"

ui_print() {
  echo -e "ui_print $1\\nui_print" > "$OUTFD" 2>/dev/null || echo "$1"
}

set_progress() {
  echo "set_progress $1" > "$OUTFD" 2>/dev/null || true
}

ui_print "================================================="
ui_print "   HyperOS Port for Redmi Note 10 Pro (sweet)   "
ui_print "   SuperRyzeNS Kernel + Kakashi Mods + RW Ext4  "
ui_print "================================================="

# Locate block devices reliably across TWRP and OrangeFox
find_block() {
  part="$1"
  for dir in \
    "/dev/block/bootdevice/by-name" \
    "/dev/block/by-name" \
    "/dev/block/platform/soc/1d84000.ufshc/by-name" \
    "/dev/block/platform/soc/*/by-name"; do
    if [ -e "$dir/$part" ]; then
      real_target=$(readlink -f "$dir/$part" 2>/dev/null || echo "$dir/$part")
      echo "$real_target"
      return 0
    fi
  done
  for cand in $(find /dev/block -name "$part" 2>/dev/null); do
    if [ -e "$cand" ]; then
      real_target=$(readlink -f "$cand" 2>/dev/null || echo "$cand")
      echo "$real_target"
      return 0
    fi
  done
  return 1
}

ui_print "[*] Detecting partition block devices..."
BOOT=$(find_block boot)
DTBO=$(find_block dtbo)
VBMETA=$(find_block vbmeta)
VBMETA_SYS=$(find_block vbmeta_system)
SUPER=$(find_block super)

ui_print "    boot   : $BOOT"
ui_print "    dtbo   : $DTBO"
ui_print "    vbmeta : $VBMETA"
ui_print "    super  : $SUPER"

if [ -z "$BOOT" ] || [ -z "$SUPER" ]; then
  ui_print "[-] ERROR: Required block devices (boot/super) could not be located!"
  exit 1
fi

# Unmount dynamic and logical partitions to release super block locks (EBUSY)
ui_print "[*] Preparing dynamic partition map..."
for m in /system /system_root /vendor /product /system_ext /odm /mi_ext /metadata /cache; do
  umount -l "$m" 2>/dev/null || true
done
if [ -d /dev/block/mapper ]; then
  for dm in system vendor product system_ext odm mi_ext; do
    dmctl delete "$dm" 2>/dev/null || true
  done
fi

set_progress 0.1
ui_print "[*] 1/5 Flashing vbmeta images (disabling AVB)..."
if [ -n "$VBMETA" ]; then
  unzip -p "$ZIPFILE" vbmeta.img > "$VBMETA" || { ui_print "[-] Failed flashing vbmeta"; exit 1; }
fi
if [ -n "$VBMETA_SYS" ]; then
  unzip -p "$ZIPFILE" vbmeta_system.img > "$VBMETA_SYS" || { ui_print "[-] Failed flashing vbmeta_system"; exit 1; }
fi

set_progress 0.2
ui_print "[*] 2/5 Flashing display dtbo..."
if [ -n "$DTBO" ]; then
  unzip -p "$ZIPFILE" dtbo.img > "$DTBO" || { ui_print "[-] Failed flashing dtbo"; exit 1; }
fi

set_progress 0.3
ui_print "[*] 3/5 Flashing SuperRyzeNS custom boot image..."
if [ -n "$BOOT" ]; then
  unzip -p "$ZIPFILE" boot.img > "$BOOT" || { ui_print "[-] Failed flashing boot"; exit 1; }
fi

set_progress 0.4
ui_print "[*] 4/5 Flashing dynamic super partition (chunked sectors)..."
ui_print "    Writing 17 chunks of 512 MB. Please wait..."
blockdev --setrw "$SUPER" 2>/dev/null || true

CHUNK_IDX=0
BLOCKS_PER_CHUNK=128

for chunk in $(unzip -l "$ZIPFILE" | awk '{print $4}' | grep '^super\\.raw\\.' | sort); do
  CHUNK_NUM=$((CHUNK_IDX + 1))
  SEEK_OFFSET=$((CHUNK_IDX * BLOCKS_PER_CHUNK))
  ui_print "    [$CHUNK_NUM/17] Writing $chunk..."
  
  unzip -p "$ZIPFILE" "$chunk" | dd of="$SUPER" bs=4M seek=$SEEK_OFFSET conv=notrunc 2>/dev/null
  if [ $? -ne 0 ]; then
    ui_print "[-] ERROR: Failed writing $chunk!"
    exit 1
  fi
  
  # Increment progress indicator
  PROGRESS=$(awk "BEGIN {printf \"%.2f\", 0.4 + ($CHUNK_NUM / 17.0) * 0.55}" 2>/dev/null || echo "0.7")
  set_progress "$PROGRESS"
  
  CHUNK_IDX=$((CHUNK_IDX + 1))
done

if [ $CHUNK_IDX -eq 0 ]; then
  # Fallback for monolithic super image if chunks are not present
  ui_print "    Writing monolithic super.img..."
  unzip -p "$ZIPFILE" super.img | dd of="$SUPER" bs=4M conv=notrunc || { ui_print "[-] Failed writing super.img"; exit 1; }
fi

set_progress 0.95
ui_print "[*] 5/5 Syncing filesystem storage buffers..."
sync

set_progress 1.0
ui_print "================================================="
ui_print "   HyperOS Installation Completed Successfully! "
ui_print "   Remember to format data if coming from MIUI   "
ui_print "================================================="
exit 0
"""

UPDATER_SCRIPT_CONTENT = b"# Dummy updater-script for custom recovery compatibility\n"


def unsparse_super_if_needed(sparse_path, raw_path):
    print(f"[*] Unsparsing {sparse_path} -> {raw_path}...")
    if not os.path.isfile(SIMG2IMG_BIN):
        raise FileNotFoundError(f"simg2img binary not found at: {SIMG2IMG_BIN}")

    cmd = [SIMG2IMG_BIN, sparse_path, raw_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"simg2img failed: {res.stderr}")
    print(f"[+] Unsparsed super image: {os.path.getsize(raw_path) // (1024*1024)} MB")


def create_recovery_zip():
    print(f"[*] Creating recovery flashable zip: {ZIP_OUTPUT_PATH}...")
    if os.path.exists(ZIP_OUTPUT_PATH):
        os.remove(ZIP_OUTPUT_PATH)

    required_standard = [
        "boot.img",
        "dtbo.img",
        "vbmeta.img",
        "vbmeta_system.img"
    ]

    for f in required_standard:
        p = os.path.join(OUTPUT_DIR, f)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Required artifact missing: {p}")

    sparse_super = os.path.join(OUTPUT_DIR, "super.img")
    if not os.path.isfile(sparse_super):
        raise FileNotFoundError(f"Required artifact missing: {sparse_super}")

    raw_super_tmp = os.path.join(OUTPUT_DIR, "super_raw_tmp.img")
    unsparse_super_if_needed(sparse_super, raw_super_tmp)

    raw_total_size = os.path.getsize(raw_super_tmp)
    chunk_size = 512 * 1024 * 1024  # 512 MB per chunk
    num_chunks = (raw_total_size + chunk_size - 1) // chunk_size
    buffer_size = 8 * 1024 * 1024  # 8 MB buffer

    try:
        with zipfile.ZipFile(ZIP_OUTPUT_PATH, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
            # 1. Update binary & updater script
            bin_info = zipfile.ZipInfo("META-INF/com/google/android/update-binary")
            bin_info.external_attr = 0o755 << 16
            z.writestr(bin_info, UPDATE_BINARY_SCRIPT)

            z.writestr("META-INF/com/google/android/updater-script", UPDATER_SCRIPT_CONTENT)
            print("[+] Injected updated recovery META-INF updater.")

            # 2. Standard partition images
            for f in required_standard:
                fp = os.path.join(OUTPUT_DIR, f)
                print(f"[*] Packaging {f} ({os.path.getsize(fp) // (1024*1024)} MB)...")
                z.write(fp, arcname=f)

            # 3. Stream raw super chunks into zip (512 MB each, perfectly aligned to 4MB blocks)
            print(f"[*] Packaging raw dynamic super in {num_chunks} chunks ({chunk_size // (1024*1024)} MB each)...")
            with open(raw_super_tmp, 'rb') as src_file:
                for idx in range(num_chunks):
                    chunk_name = f"super.raw.{idx:02d}"
                    bytes_remaining = min(chunk_size, raw_total_size - (idx * chunk_size))
                    if bytes_remaining <= 0:
                        break

                    print(f"    -> Packaging {chunk_name} ({bytes_remaining // (1024*1024)} MB)...")
                    chunk_info = zipfile.ZipInfo(chunk_name)
                    chunk_info.external_attr = 0o644 << 16
                    chunk_info.compress_type = zipfile.ZIP_DEFLATED
                    chunk_info._compresslevel = 1
                    with z.open(chunk_info, 'w') as dest_file:
                        while bytes_remaining > 0:
                            to_read = min(buffer_size, bytes_remaining)
                            chunk_data = src_file.read(to_read)
                            if not chunk_data:
                                break
                            dest_file.write(chunk_data)
                            bytes_remaining -= len(chunk_data)

        zip_size_gb = os.path.getsize(ZIP_OUTPUT_PATH) / (1024 * 1024 * 1024)
        print(f"\n[+] Recovery zip created successfully: {ZIP_OUTPUT_PATH} ({zip_size_gb:.2f} GB)")
    finally:
        if os.path.exists(raw_super_tmp):
            os.remove(raw_super_tmp)
            print("[*] Cleaned up temporary raw super image.")


if __name__ == '__main__':
    create_recovery_zip()
