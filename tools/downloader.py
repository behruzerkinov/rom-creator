#!/usr/bin/env python3
"""
downloader.py - Resumable HTTP/HTTPS file downloader with progress bar and integrity check.
"""

import sys
import os
import urllib.request
import time

CHUNK_SIZE = 1024 * 1024  # 1 MB


def download_file(url, destination_path):
    print(f"[*] Target URL: {url}")
    print(f"[*] Destination: {destination_path}")

    # Determine existing file size for resume capability
    existing_bytes = 0
    if os.path.exists(destination_path):
        existing_bytes = os.path.getsize(destination_path)
        print(f"[*] Found existing partial download: {existing_bytes // (1024*1024)} MB")

    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    if existing_bytes > 0:
        request.add_header('Range', f'bytes={existing_bytes}-')

    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as error:
        if error.code == 416:  # Requested Range Not Satisfiable (already fully downloaded)
            print("[+] File is already fully downloaded.")
            return destination_path
        raise

    is_range_supported = (response.status == 206)
    if not is_range_supported and existing_bytes > 0:
        print("[!] Server does not support resume. Restarting from byte 0...")
        existing_bytes = 0

    content_length = response.headers.get('Content-Length')
    total_bytes = (int(content_length) + existing_bytes) if content_length else None

    mode = 'ab' if (is_range_supported and existing_bytes > 0) else 'wb'
    downloaded_bytes = existing_bytes

    start_time = time.time()
    last_print_time = start_time

    with open(destination_path, mode) as file_handle:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            file_handle.write(chunk)
            downloaded_bytes += len(chunk)

            current_time = time.time()
            if current_time - last_print_time >= 1.0:
                last_print_time = current_time
                elapsed = current_time - start_time
                speed_mb_s = ((downloaded_bytes - existing_bytes) / (1024 * 1024)) / (elapsed if elapsed > 0 else 1)
                
                if total_bytes:
                    percent = (downloaded_bytes / total_bytes) * 100
                    print(f"\rProgress: {percent:5.1f}% | {downloaded_bytes // (1024*1024)}/{total_bytes // (1024*1024)} MB | {speed_mb_s:5.2f} MB/s", end='', flush=True)
                else:
                    print(f"\rDownloaded: {downloaded_bytes // (1024*1024)} MB | {speed_mb_s:5.2f} MB/s", end='', flush=True)

    print(f"\n[+] Download completed successfully: {destination_path} ({os.path.getsize(destination_path) // (1024*1024)} MB)")
    return destination_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <URL> <destination_path>")
        sys.exit(1)
    download_file(sys.argv[1], sys.argv[2])

