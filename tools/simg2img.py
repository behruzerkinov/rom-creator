#!/usr/bin/env python3
"""
simg2img.py - Convert single or split Android sparse images into raw ext4 / super images.
Pure Python implementation supporting split chunk files (e.g. super.img.0, super.img.1, ...).
"""

import sys
import os
import struct

SPARSE_HEADER_MAGIC = 0xED26FF3A
CHUNK_TYPE_RAW = 0xCAC1
CHUNK_TYPE_FILL = 0xCAC2
CHUNK_TYPE_DONT_CARE = 0xCAC3
CHUNK_TYPE_CRC32 = 0xCAC4


def process_sparse_file(source_sparse_handle, destination_raw_handle, expected_block_size=4096):
    header_bytes = source_sparse_handle.read(28)
    if len(header_bytes) < 28:
        raise ValueError("File too short for sparse image header")

    magic, major, minor, file_hdr_sz, chunk_hdr_sz, block_size, total_blocks, total_chunks, checksum = struct.unpack(
        '<IHHHHIIII', header_bytes
    )

    if magic != SPARSE_HEADER_MAGIC:
        raise ValueError(f"Invalid magic: {hex(magic)} (expected {hex(SPARSE_HEADER_MAGIC)})")
    if file_hdr_sz > 28:
        # Seek past any extended header padding
        source_sparse_handle.seek(file_hdr_sz - 28, os.SEEK_CUR)

    for chunk_index in range(total_chunks):
        chunk_header = source_sparse_handle.read(chunk_hdr_sz)
        if len(chunk_header) < 12:
            break
        chunk_type, reserved, chunk_blocks, total_sz = struct.unpack('<HHII', chunk_header[:12])
        data_bytes_expected = chunk_blocks * block_size

        if chunk_type == CHUNK_TYPE_RAW:
            bytes_to_read = total_sz - chunk_hdr_sz
            raw_data = source_sparse_handle.read(bytes_to_read)
            destination_raw_handle.write(raw_data)
        elif chunk_type == CHUNK_TYPE_FILL:
            fill_val = source_sparse_handle.read(4)
            fill_block = fill_val * (block_size // 4)
            for _ in range(chunk_blocks):
                destination_raw_handle.write(fill_block)
        elif chunk_type == CHUNK_TYPE_DONT_CARE:
            # Advance write pointer without writing actual physical bytes (sparse hole)
            destination_raw_handle.seek(data_bytes_expected, os.SEEK_CUR)
        elif chunk_type == CHUNK_TYPE_CRC32:
            source_sparse_handle.seek(4, os.SEEK_CUR)
        else:
            raise ValueError(f"Unknown chunk type: {hex(chunk_type)} at chunk {chunk_index}")


def convert_sparse_to_raw(sparse_paths, output_raw_path):
    print(f"[*] Merging/Unsparsing {len(sparse_paths)} files into {output_raw_path}...")
    with open(output_raw_path, 'wb') as raw_file:
        for file_path in sparse_paths:
            print(f" -> Processing {file_path}...")
            with open(file_path, 'rb') as sparse_file:
                process_sparse_file(sparse_file, raw_file)
    print(f"[+] Output raw image created: {output_raw_path} ({os.path.getsize(output_raw_path) // (1024*1024)} MB)")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <sparse_in1> [sparse_in2 ...] <raw_out.img>")
        sys.exit(1)
    sparse_inputs = sys.argv[1:-1]
    raw_output = sys.argv[-1]
    convert_sparse_to_raw(sparse_inputs, raw_output)

