#!/usr/bin/env python3
"""
build_all_images.py - Reconstruct ext4 partition images for system, product, and vendor/odm
with block-accurate geometry satisfying sweet's dynamic partition group capacity.
"""

import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_DIR = os.path.join(PROJECT_ROOT, "tools", "bin")
TARGET_DIR = os.path.join(PROJECT_ROOT, "workspace", "target")
IMAGES_DIR = os.path.join(TARGET_DIR, "images")
BASE_IMAGES_DIR = os.path.join(PROJECT_ROOT, "workspace", "base", "images")

MKE2FS = os.path.join(BIN_DIR, "mke2fs.exe")
E2FSDROID = os.path.join(BIN_DIR, "e2fsdroid.exe")

# Block allocations (4096 bytes / block)
# Total: 346,112 (system) + 268,800 (system_ext) + 1,171,273 (product)
# + 440,503 (vendor: 1,804,300,288 bytes) + 512 (odm: 2,097,152 bytes)
# = 2,227,200 blocks * 4096 = 9,122,611,200 bytes (EXACT GROUP_MAX)
PARTITION_CONFIGS = [
    {
        "name": "system",
        "mountpoint": "/system",
        "blocks": 346112,
        "src_dir": os.path.join(TARGET_DIR, "system", "system"),
        "fs_config": os.path.join(TARGET_DIR, "system", "config", "system_fs_config"),
        "file_contexts": os.path.join(TARGET_DIR, "system", "config", "system_file_contexts")
    },
    {
        "name": "system_ext",
        "mountpoint": "/system_ext",
        "blocks": 268800,
        "src_dir": os.path.join(TARGET_DIR, "system_ext", "system_ext"),
        "fs_config": os.path.join(TARGET_DIR, "system_ext", "config", "system_ext_fs_config"),
        "file_contexts": os.path.join(TARGET_DIR, "system_ext", "config", "system_ext_file_contexts")
    },
    {
        "name": "product",
        "mountpoint": "/product",
        "blocks": 1171273,
        "src_dir": os.path.join(TARGET_DIR, "product", "product"),
        "fs_config": os.path.join(TARGET_DIR, "product", "config", "product_fs_config"),
        "file_contexts": os.path.join(TARGET_DIR, "product", "config", "product_file_contexts")
    }
]


def build_partition_image(cfg):
    out_img = os.path.join(IMAGES_DIR, f"{cfg['name']}.img")
    print(f"\n========================================================")
    print(f"[*] Building {cfg['name']}.img ({cfg['blocks']} blocks, ~{cfg['blocks']*4096 // (1024*1024)} MB)...")
    print(f"========================================================")

    if os.path.exists(out_img):
        os.remove(out_img)

    # 1. Format raw ext4 with mke2fs
    cmd_mke2fs = [
        MKE2FS,
        "-O", "^has_journal",
        "-b", "4096",
        "-L", cfg["name"],
        "-M", cfg["mountpoint"],
        "-m", "0",
        os.path.relpath(out_img, PROJECT_ROOT),
        str(cfg["blocks"])
    ]
    print(f"[*] Running: {' '.join(cmd_mke2fs)}")
    subprocess.run(cmd_mke2fs, cwd=PROJECT_ROOT, check=True)

    # 2. Populate files, permissions, and SELinux contexts with e2fsdroid
    # Note: e2fsdroid requires -f to be relative to cwd
    cmd_e2fsdroid = [
        E2FSDROID,
        "-e",
        "-S", os.path.relpath(cfg["file_contexts"], PROJECT_ROOT),
        "-C", os.path.relpath(cfg["fs_config"], PROJECT_ROOT),
        "-a", cfg["mountpoint"],
        "-f", os.path.relpath(cfg["src_dir"], PROJECT_ROOT),
        os.path.relpath(out_img, PROJECT_ROOT)
    ]
    print(f"[*] Running: {' '.join(cmd_e2fsdroid)}")
    subprocess.run(cmd_e2fsdroid, cwd=PROJECT_ROOT, check=True)
    print(f"[+] Successfully generated: {out_img} ({os.path.getsize(out_img)} bytes)")


def stage_base_vendor_and_odm():
    print(f"\n[*] Staging base vendor.img and odm.img into {IMAGES_DIR}...")
    for part in ["vendor.img", "odm.img"]:
        src = os.path.join(BASE_IMAGES_DIR, part)
        dst = os.path.join(IMAGES_DIR, part)
        if not os.path.isfile(src):
            raise FileNotFoundError(f"Missing base partition image: {src}")
        if not os.path.isfile(dst) or os.path.getsize(dst) != os.path.getsize(src):
            print(f" -> Copying {part} ({os.path.getsize(src) // (1024*1024)} MB)...")
            shutil.copy2(src, dst)
        else:
            print(f" -> {part} already staged in images directory.")
    print("[+] Base vendor and ODM staged successfully.")


if __name__ == '__main__':
    os.makedirs(IMAGES_DIR, exist_ok=True)
    # Stage vendor and odm
    stage_base_vendor_and_odm()

    # Build system, system_ext, product
    for cfg in PARTITION_CONFIGS:
        build_partition_image(cfg)

    print("\n[+] All ext4 partition images have been successfully built and staged!")
