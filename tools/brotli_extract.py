#!/usr/bin/env python3
"""
brotli_extract.py - Stream decompress .new.dat.br files to .new.dat using Brotli.
Memory-safe streaming chunk decompressor to avoid loading multi-gigabyte partitions into RAM.
"""

import sys
import os
import brotli

CHUNK_SIZE = 1024 * 1024 * 4  # 4 MB read/write buffer


def decompress_brotli_file(input_brotli_path, output_decompressed_path):
    if not os.path.isfile(input_brotli_path):
        raise FileNotFoundError(f"Input file not found: {input_brotli_path}")

    input_size = os.path.getsize(input_brotli_path)
    print(f"[*] Decompressing {input_brotli_path} ({input_size // (1024*1024)} MB)...")

    decompressor = brotli.Decompressor()
    bytes_read = 0

    with open(input_brotli_path, 'rb') as source_stream, open(output_decompressed_path, 'wb') as destination_stream:
        while True:
            chunk = source_stream.read(CHUNK_SIZE)
            if not chunk:
                break
            bytes_read += len(chunk)
            decompressed_chunk = decompressor.process(chunk)
            if decompressed_chunk:
                destination_stream.write(decompressed_chunk)
            
            percent = (bytes_read / input_size) * 100
            print(f"\rProgress: {percent:.1f}% ({bytes_read // (1024*1024)} MB / {input_size // (1024*1024)} MB)", end='', flush=True)

    print(f"\n[+] Finished: {output_decompressed_path} ({os.path.getsize(output_decompressed_path) // (1024*1024)} MB)")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.br> <output.dat>")
        sys.exit(1)
    decompress_brotli_file(sys.argv[1], sys.argv[2])

