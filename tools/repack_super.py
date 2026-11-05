#!/usr/bin/env python3
"""
repack_super.py - Build unified dynamic partition super.img for sweet using lpmake.
Calculates block-aligned boundaries and configures read-write (RW) partition flags.
"""

import os
import sys
import subprocess

SUPER_CAPACITY_BYTES = 9126805504       # Standard sweet super partition device size
GROUP_MAX_SIZE_BYTES = 9122611200       # qti_dynamic_partitions group capacity
BLOCK_SIZE = 4096
METADATA_SIZE = 65536
METADATA_SLOTS = 2


def align_to_block_size(size_bytes, alignment=BLOCK_SIZE):
    remainder = size_bytes % alignment
    if remainder == 0:
        return size_bytes
    return size_bytes + (alignment - remainder)


def generate_super_image(images_dir, output_super_path, is_rw=True, lpmake_binary=None):
    if lpmake_binary is None:
        lpmake_binary = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin", "lpmake.exe"))

    if not os.path.isfile(lpmake_binary):
        raise FileNotFoundError(f"lpmake executable not found: {lpmake_binary}")

    partition_names = ["system", "system_ext", "product", "vendor", "odm"]
    partition_specs = []
    total_image_size = 0

    attr_flag = "none" if is_rw else "readonly"

    for name in partition_names:
        img_path = os.path.join(images_dir, f"{name}.img")
        if not os.path.isfile(img_path):
            raise FileNotFoundError(f"Partition image missing: {img_path}")

        raw_size = os.path.getsize(img_path)
        aligned_size = align_to_block_size(raw_size)
        total_image_size += aligned_size

        print(f"[*] {name}: {raw_size // (1024*1024)} MB (Aligned: {aligned_size} bytes, Attr: {attr_flag})")
        partition_specs.append({
            "name": name,
            "path": img_path,
            "size": aligned_size,
            "attr": attr_flag
        })

    if total_image_size > GROUP_MAX_SIZE_BYTES:
        raise ValueError(f"Total partitions size ({total_image_size} bytes) exceeds group capacity ({GROUP_MAX_SIZE_BYTES} bytes)")

    print(f"[*] Total dynamic partition payload: {total_image_size // (1024*1024)} MB / {GROUP_MAX_SIZE_BYTES // (1024*1024)} MB")

    cmd = [
        lpmake_binary,
        "--metadata-size", str(METADATA_SIZE),
        "--super-name", "super",
        "--metadata-slots", str(METADATA_SLOTS),
        "--device", f"super:{SUPER_CAPACITY_BYTES}",
        "--group", f"qti_dynamic_partitions:{GROUP_MAX_SIZE_BYTES}",
        "--sparse",
        "--output", output_super_path
    ]

    for part in partition_specs:
        cmd.extend([
            "--partition", f"{part['name']}:{part['attr']}:{part['size']}:qti_dynamic_partitions",
            "--image", f"{part['name']}={part['path']}"
        ])

    print(f"[*] Running lpmake to build: {output_super_path}...")
    subprocess.run(cmd, check=True)
    print(f"[+] super.img successfully generated: {output_super_path} ({os.path.getsize(output_super_path) // (1024*1024)} MB)")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <images_dir> <output_super.img> [--ro|--rw]")
        sys.exit(1)
    img_directory = sys.argv[1]
    out_super = sys.argv[2]
    enable_rw = not ("--ro" in sys.argv)
    generate_super_image(img_directory, out_super, is_rw=enable_rw)

