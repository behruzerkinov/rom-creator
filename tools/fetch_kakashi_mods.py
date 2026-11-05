#!/usr/bin/env python3
"""
fetch_kakashi_mods.py - Download latest mod releases from Mods-Center (Kakashi) using curl.
"""

import os
import sys
import json
import urllib.request
import subprocess

MODS_TO_FETCH = [
    "HyperOS-Launcher",
    "HyperOS-Security-Center",
    "HyperOS-App-Vault",
    "HyperOS-PLugin",
    "HyperOS-Theme-Manager",
    "ColorOS_Control_Center",
    "Apk-Protection-Patch",
    "FPS-Limitation-Patcher",
    "HyperOS-Dialer"
]

DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace", "mods"))


def fetch_release_assets_for_repo(repo_name):
    api_url = f"https://api.github.com/repos/Mods-Center/{repo_name}/releases/latest"
    request = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            release_data = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        print(f"[-] No releases found via API for {repo_name} (HTTP {error.code})")
        return []

    assets = release_data.get("assets", [])
    if not assets:
        print(f"[-] No attached assets in latest release for {repo_name}")
        return []

    downloaded = []
    repo_target_dir = os.path.join(DEST_DIR, repo_name)
    os.makedirs(repo_target_dir, exist_ok=True)

    for asset in assets:
        asset_name = asset["name"]
        download_url = asset["browser_download_url"]
        output_file_path = os.path.join(repo_target_dir, asset_name)
        
        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 1024:
            print(f"[=] Asset already present: {output_file_path} ({os.path.getsize(output_file_path) // 1024} KB)")
            downloaded.append(output_file_path)
            continue

        print(f"[*] Downloading {asset_name} via curl...")
        try:
            cmd = ["curl.exe", "-L", "-k", "-f", "-o", output_file_path, download_url]
            subprocess.run(cmd, check=True, timeout=120)
            file_size_kb = os.path.getsize(output_file_path) // 1024
            print(f"[+] Downloaded: {asset_name} ({file_size_kb} KB)")
            downloaded.append(output_file_path)
        except Exception as dl_err:
            print(f"[!] Failed to download {asset_name}: {dl_err}")
            if os.path.exists(output_file_path) and os.path.getsize(output_file_path) == 0:
                os.remove(output_file_path)

    return downloaded


def fetch_all_mods():
    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"[*] Fetching Kakashi Mods into: {DEST_DIR}")
    for mod in MODS_TO_FETCH:
        print(f"\n--- Checking: {mod} ---")
        fetch_release_assets_for_repo(mod)


if __name__ == '__main__':
    fetch_all_mods()
