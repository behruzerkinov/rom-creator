#!/usr/bin/env python3
"""
sdat2img.py - Convert Android system.new.dat to ext4 raw image file.
Pure Python implementation compatible with transfer list versions 1, 2, 3, 4.
"""

import sys
import os

BLOCK_SIZE_BYTES = 4096


def parse_block_ranges(range_command_string):
    """
    Parse Android block range string format: 'count,start1,end1,start2,end2,...'
    Where count is the total number of integers following (must be even).
    Returns a list of (start_block, end_block) tuples.
    """
    tokens = [int(token) for token in range_command_string.split(',')]
    range_count = tokens[0]
    
    if range_count % 2 != 0 or len(tokens) != (range_count + 1):
        raise ValueError(f"Malformed block range format: {range_command_string}")

    parsed_ranges = []
    for index in range(1, len(tokens), 2):
        start_block = tokens[index]
        end_block = tokens[index + 1]
        parsed_ranges.append((start_block, end_block))
        
    return parsed_ranges


def convert_sdat_to_img(transfer_list_path, new_dat_path, output_img_path):
    """
    Reconstruct raw image from Android OTA sparse data and transfer list.
    """
    if not os.path.isfile(transfer_list_path):
        raise FileNotFoundError(f"Transfer list file not found: {transfer_list_path}")
    if not os.path.isfile(new_dat_path):
        raise FileNotFoundError(f"New dat file not found: {new_dat_path}")

    with open(transfer_list_path, 'r', encoding='utf-8') as list_file:
        version_line = list_file.readline().strip()
        version = int(version_line)
        
        # Versions 1-4 supported
        if version not in (1, 2, 3, 4):
            raise ValueError(f"Unsupported transfer list version: {version}")

        total_blocks_allocated = int(list_file.readline().strip())
        
        # Skip stash metadata lines present in version >= 2
        if version >= 2:
            list_file.readline()  # max stash blocks
            list_file.readline()  # stash entries count

        transfer_commands = list_file.readlines()

    print(f"[*] Transfer list version: {version}, Total blocks: {total_blocks_allocated} ({total_blocks_allocated * BLOCK_SIZE_BYTES // (1024*1024)} MB)")
    
    with open(new_dat_path, 'rb') as dat_file, open(output_img_path, 'w+b') as img_file:
        # Pre-allocate sparse file to maximum size to prevent disk thrashing
        img_file.truncate(total_blocks_allocated * BLOCK_SIZE_BYTES)
        
        for command_line in transfer_commands:
            command_line = command_line.strip()
            if not command_line:
                continue

            parts = command_line.split()
            action = parts[0]

            if action == 'new':
                # Format: new <range_set>
                block_ranges = parse_block_ranges(parts[1])
                for start_block, end_block in block_ranges:
                    block_count = end_block - start_block
                    bytes_to_read = block_count * BLOCK_SIZE_BYTES
                    
                    data_buffer = dat_file.read(bytes_to_read)
                    if len(data_buffer) != bytes_to_read:
                        raise IOError(f"Unexpected EOF reading dat: requested {bytes_to_read}, read {len(data_buffer)}")
                    
                    img_file.seek(start_block * BLOCK_SIZE_BYTES)
                    img_file.write(data_buffer)

            elif action == 'erase':
                # Range is cleared; truncated zero-fill already covers this on creation
                continue
                
            elif action == 'zero':
                block_ranges = parse_block_ranges(parts[1])
                zero_buffer = b'\x00' * BLOCK_SIZE_BYTES
                for start_block, end_block in block_ranges:
                    img_file.seek(start_block * BLOCK_SIZE_BYTES)
                    for _ in range(end_block - start_block):
                        img_file.write(zero_buffer)

        # Inspect ext4 superblock to match true partition geometry if larger than transferred blocks
        img_file.seek(1024)
        superblock_magic_bytes = img_file.read(2)
        if len(superblock_magic_bytes) == 2:
            import struct
            # ext4 magic is 0xef53 at offset 1024 + 0x38 (offset 1080)
            img_file.seek(1080)
            ext4_magic = struct.unpack('<H', img_file.read(2))[0]
            if ext4_magic == 0xEF53:
                img_file.seek(1024 + 4)  # s_blocks_count_lo
                superblock_total_blocks = struct.unpack('<I', img_file.read(4))[0]
                if superblock_total_blocks > total_blocks_allocated:
                    print(f"[*] Adjusting ext4 image bounds to superblock size: {superblock_total_blocks} blocks ({superblock_total_blocks * BLOCK_SIZE_BYTES // (1024*1024)} MB)")
                    img_file.truncate(superblock_total_blocks * BLOCK_SIZE_BYTES)

    print(f"[+] Reconstructed image successfully saved: {output_img_path}")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <transfer_list> <system.new.dat> <output.img>")
        sys.exit(1)
    convert_sdat_to_img(sys.argv[1], sys.argv[2], sys.argv[3])

