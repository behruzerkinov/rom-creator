#!/usr/bin/env python3
"""
patch_system.py - Surgical system modification, de-flagshiping, overlay injection,
and Kakashi mods integration for Redmi Note 10 Pro (sweet).
"""

import os
import sys
import shutil
import glob
import re

SWEET_BUILD_PROPERTIES = {
    "ro.product.model": "Redmi Note 10 Pro",
    "ro.product.brand": "Redmi",
    "ro.product.name": "sweet",
    "ro.product.device": "sweet",
    "ro.build.product": "sweet",
    "ro.product.system.model": "Redmi Note 10 Pro",
    "ro.product.system.brand": "Redmi",
    "ro.product.system.name": "sweet",
    "ro.product.system.device": "sweet",
    "ro.product.product.model": "Redmi Note 10 Pro",
    "ro.product.product.brand": "Redmi",
    "ro.product.product.name": "sweet",
    "ro.product.product.device": "sweet",
    "ro.product.system_ext.model": "Redmi Note 10 Pro",
    "ro.product.system_ext.brand": "Redmi",
    "ro.product.system_ext.name": "sweet",
    "ro.product.system_ext.device": "sweet",
    "ro.product.mod_device": "sweet_global",
    # Dalvik Memory Heap tuning optimized for 6GB/8GB RAM
    "dalvik.vm.heapgrowthlimit": "256m",
    "dalvik.vm.heapsize": "512m",
    "dalvik.vm.heaptargetutilization": "0.75",
    "dalvik.vm.heapminfree": "512k",
    "dalvik.vm.heapmaxfree": "8m",
    # Display & Refresh Rate
    "ro.vendor.display.default_fps": "120",
    "ro.surface_flinger.has_wide_color_display": "true",
    "ro.surface_flinger.has_HDR_display": "true",
    "persist.vendor.power.dfps.level": "120",
    # Play Integrity & CTS Spoofing preparation
    "ro.boot.flash.locked": "1",
    "ro.boot.verifiedbootstate": "green",
    "ro.boot.veritymode": "enforcing"
}

# Bloat and flagship-specific packages to remove from donor (star)
PACKAGES_TO_PURGE = [
    # Secondary Rear Sub-Screen (Mi 11 Ultra specific, causes crashloops on sweet)
    "system/priv-app/SubScreen",
    "product/priv-app/SubScreen",
    "system_ext/priv-app/SubScreen",
    "product/app/SubScreen",
    # Analytics, Telemetry and Ad daemons
    "system/app/AnalyticsCore",
    "system/priv-app/AnalyticsCore",
    "product/app/AnalyticsCore",
    "product/priv-app/AnalyticsCore",
    "product/app/MSA",
    "product/app/Mipay",
    "product/app/MiCredit",
    "product/app/BugReport",
    "product/app/Feedback",
    "system/app/BugReport",
    "system/app/YellowPage",
    "product/app/YellowPage"
]


def patch_build_prop(build_prop_path):
    if not os.path.isfile(build_prop_path):
        print(f"[-] build.prop not found: {build_prop_path}")
        return

    print(f"[*] Patching properties in: {build_prop_path}")
    with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as prop_file:
        lines = prop_file.readlines()

    updated_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or '=' not in stripped:
            new_lines.append(line)
            continue

        key, _ = stripped.split('=', 1)
        key = key.strip()

        if key in SWEET_BUILD_PROPERTIES:
            new_lines.append(f"{key}={SWEET_BUILD_PROPERTIES[key]}\n")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # Append any missing properties
    for key, value in SWEET_BUILD_PROPERTIES.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")

    with open(build_prop_path, 'w', encoding='utf-8') as prop_file:
        prop_file.writelines(new_lines)
    print(f"[+] build.prop patched successfully: {len(updated_keys)} keys updated")


def purge_unwanted_packages(target_root_dir):
    print(f"[*] Purging flagship-specific and telemetry bloat from {target_root_dir}...")
    purged_count = 0
    for relative_path in PACKAGES_TO_PURGE:
        full_path = os.path.join(target_root_dir, relative_path)
        if os.path.exists(full_path):
            print(f" -> Removing: {relative_path}")
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
            purged_count += 1
    print(f"[+] Total purged targets: {purged_count}")


def inject_kakashi_mods(mods_dir, target_root_dir):
    print(f"[*] Injecting Kakashi Mods into target tree: {target_root_dir}")
    # 1. HyperOS Launcher (MiuiHome + XiaomiEuExt)
    launcher_zip = os.path.join(mods_dir, "HyperOS-Launcher", "HyperOS_LauncherV7.5F@kashis_cringey_stuffs.zip")
    if os.path.exists(launcher_zip):
        import zipfile
        with zipfile.ZipFile(launcher_zip) as z:
            # Extract MiuiHome.apk
            dest_home = os.path.join(target_root_dir, "product", "priv-app", "MiuiHome")
            os.makedirs(dest_home, exist_ok=True)
            with open(os.path.join(dest_home, "MiuiHome.apk"), 'wb') as out_f:
                out_f.write(z.read("files/MiuiHome.apk"))

            # Extract XiaomiEuExt.apk
            dest_ext = os.path.join(target_root_dir, "product", "priv-app", "XiaomiEuExt")
            os.makedirs(dest_ext, exist_ok=True)
            with open(os.path.join(dest_ext, "XiaomiEuExt.apk"), 'wb') as out_f:
                out_f.write(z.read("files/ext/XiaomiEUExt.apk"))

            # Permissions
            perm_dir = os.path.join(target_root_dir, "system", "etc", "permissions")
            os.makedirs(perm_dir, exist_ok=True)
            for perm_file in ["privapp_whitelist_com.miui.home.xml", "privapp_whitelist_eu.xiaomi.ext.xml"]:
                src_path = f"system/etc/permissions/{perm_file}"
                if src_path in z.namelist():
                    with open(os.path.join(perm_dir, perm_file), 'wb') as out_f:
                        out_f.write(z.read(src_path))
        print("[+] HyperOS Launcher & XiaomiEuExt injected.")

    # 2. HyperOS Security Center
    sec_zip = os.path.join(mods_dir, "HyperOS-Security-Center", "HyperOS_SecurityV7@kashis_cringey_stuffs.zip")
    if os.path.exists(sec_zip):
        import zipfile
        with zipfile.ZipFile(sec_zip) as z:
            dest_sec = os.path.join(target_root_dir, "system", "priv-app", "SecurityCenter")
            os.makedirs(dest_sec, exist_ok=True)
            with open(os.path.join(dest_sec, "SecurityCenter.apk"), 'wb') as out_f:
                out_f.write(z.read("files/MIUISecurityCenter.apk"))
        print("[+] HyperOS Security Center mod injected.")

    # 3. HyperOS App Vault
    vault_zip = os.path.join(mods_dir, "HyperOS-App-Vault", "HyperOS_AppVaultV5@kashis_cringey_stuffs.zip")
    if os.path.exists(vault_zip):
        import zipfile
        with zipfile.ZipFile(vault_zip) as z:
            dest_vault = os.path.join(target_root_dir, "product", "app", "AppVault")
            os.makedirs(dest_vault, exist_ok=True)
            with open(os.path.join(dest_vault, "AppVault.apk"), 'wb') as out_f:
                out_f.write(z.read("files/AppVault.apk"))
        print("[+] HyperOS App Vault mod injected.")

    # 4. ColorOS Control Center Plugin
    cc_zip = os.path.join(mods_dir, "ColorOS_Control_Center", "ColorOS_plugin_mod_V4@kashis_cringey_stuffs.zip")
    if os.path.exists(cc_zip):
        import zipfile
        with zipfile.ZipFile(cc_zip) as z:
            dest_cc = os.path.join(target_root_dir, "system_ext", "priv-app", "MiuiSystemUIPlugin")
            os.makedirs(dest_cc, exist_ok=True)
            with open(os.path.join(dest_cc, "MiuiSystemUIPlugin.apk"), 'wb') as out_f:
                out_f.write(z.read("files/OS4/MIUISystemUIPlugin.apk"))
        print("[+] ColorOS Control Center quick settings plugin injected.")

    # 5. HyperOS Native Dialer & Contacts
    dialer_zip = os.path.join(mods_dir, "HyperOS-Dialer", "HyperOS_Dialer_V3@kashis_cringey_stuffs.zip")
    if os.path.exists(dialer_zip):
        import zipfile
        with zipfile.ZipFile(dialer_zip) as z:
            dest_dialer = os.path.join(target_root_dir, "system", "priv-app", "InCallUI")
            os.makedirs(dest_dialer, exist_ok=True)
            with open(os.path.join(dest_dialer, "InCallUI.apk"), 'wb') as out_f:
                out_f.write(z.read("files/InCallUI/InCallUI.apk"))
        print("[+] Native HyperOS Dialer injected.")


def patch_fstab_for_rw(fstab_input_path, fstab_output_path):
    print(f"[*] Patching fstab for Read-Write (RW) support: {fstab_input_path} -> {fstab_output_path}")
    with open(fstab_input_path, 'r', encoding='utf-8') as in_f, open(fstab_output_path, 'w', encoding='utf-8') as out_f:
        for line in in_f:
            # Change read-only ro to rw for all dynamic mounts (system, system_ext, product, vendor, odm)
            if any(partition in line for partition in ["/system", "/system_ext", "/product", "/vendor", "/odm"]):
                line = re.sub(r'\bro\b', 'rw', line)
                line = re.sub(r'avb=vbmeta_system,?', '', line)
                line = re.sub(r'avb,?', '', line)
                line = re.sub(r',,+', ',', line)
            out_f.write(line)
    print("[+] fstab patched with rw flags and AVB enforcement removed.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <target_extracted_dir> [mods_dir]")
        sys.exit(1)
    target_dir = sys.argv[1]
    mods_directory = sys.argv[2] if len(sys.argv) > 2 else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace", "mods"))
    
    # 1. Purge unwanted flagship packages
    purge_unwanted_packages(target_dir)
    
    # 2. Patch build.props
    for prop in glob.glob(os.path.join(target_dir, "**", "build.prop"), recursive=True):
        patch_build_prop(prop)

    # 3. Inject Kakashi Mods
    inject_kakashi_mods(mods_directory, target_dir)

