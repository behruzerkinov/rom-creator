#!/usr/bin/env python3
"""
patch_system.py - Surgical system modification, de-flagshiping, overlay injection,
fs_config synchronization, and Kakashi mods integration for Redmi Note 10 Pro (sweet).
"""

import os
import sys
import shutil
import glob
import re
import zipfile

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
    # Display & Refresh Rate (120Hz)
    "ro.vendor.display.default_fps": "120",
    "ro.surface_flinger.has_wide_color_display": "true",
    "ro.surface_flinger.has_HDR_display": "true",
    "persist.vendor.power.dfps.level": "120",
    # Play Integrity & CTS Spoofing preparation
    "ro.boot.flash.locked": "1",
    "ro.boot.verifiedbootstate": "green",
    "ro.boot.veritymode": "enforcing"
}

BLOAT_DIR_NAMES = [
    "MiuiSubScreenUi",
    "SubScreen",
    "AnalyticsCore",
    "MSA-Global",
    "MSA",
    "MiBugReportOS2Global",
    "BugReport",
    "GoogleFeedback",
    "Feedback",
    "YellowPage"
]


def patch_build_prop(build_prop_path):
    if not os.path.isfile(build_prop_path):
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

    for key, value in SWEET_BUILD_PROPERTIES.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")

    with open(build_prop_path, 'w', encoding='utf-8') as prop_file:
        prop_file.writelines(new_lines)
    print(f"[+] build.prop patched successfully: {len(updated_keys)} keys updated")


def purge_unwanted_packages(target_root_dir):
    print(f"[*] Purging flagship-specific SubScreen and telemetry bloat from {target_root_dir}...")
    purged_count = 0
    for root, dirs, files in os.walk(target_root_dir, topdown=False):
        for d in dirs:
            if d in BLOAT_DIR_NAMES:
                full_path = os.path.join(root, d)
                print(f" -> Removing bloat directory: {full_path}")
                try:
                    shutil.rmtree(full_path)
                    purged_count += 1
                except Exception as e:
                    print(f" [-] Error removing {full_path}: {e}")
    print(f"[+] Total purged targets: {purged_count}")


def clean_oat_directory(app_dir):
    """Remove stale oat/dexopt caches after replacing an APK."""
    oat_path = os.path.join(app_dir, "oat")
    if os.path.isdir(oat_path):
        print(f" -> Cleaning stale oat cache in: {oat_path}")
        shutil.rmtree(oat_path, ignore_errors=True)


def inject_kakashi_mods(mods_dir, target_root_dir):
    print(f"[*] Injecting Kakashi Mods into target tree...")

    # Determine partition root paths
    sys_root = os.path.join(target_root_dir, "system", "system", "system")
    if not os.path.exists(sys_root):
        sys_root = os.path.join(target_root_dir, "system", "system")

    prod_root = os.path.join(target_root_dir, "product", "product")
    if not os.path.exists(prod_root):
        prod_root = os.path.join(target_root_dir, "product")

    # 1. HyperOS Launcher (MiuiHome + XiaomiEuExt)
    launcher_zip = os.path.join(mods_dir, "HyperOS-Launcher", "HyperOS_LauncherV7.5F@kashis_cringey_stuffs.zip")
    if os.path.exists(launcher_zip):
        with zipfile.ZipFile(launcher_zip) as z:
            dest_home = os.path.join(prod_root, "priv-app", "MiuiHome")
            os.makedirs(dest_home, exist_ok=True)
            clean_oat_directory(dest_home)
            with open(os.path.join(dest_home, "MiuiHome.apk"), 'wb') as out_f:
                out_f.write(z.read("files/MiuiHome.apk"))

            dest_ext = os.path.join(prod_root, "priv-app", "XiaomiEuExt")
            os.makedirs(dest_ext, exist_ok=True)
            with open(os.path.join(dest_ext, "XiaomiEuExt.apk"), 'wb') as out_f:
                out_f.write(z.read("files/ext/XiaomiEUExt.apk"))

            perm_dir = os.path.join(sys_root, "etc", "permissions")
            os.makedirs(perm_dir, exist_ok=True)
            for perm_file in ["privapp_whitelist_com.miui.home.xml", "privapp_whitelist_eu.xiaomi.ext.xml"]:
                src_path = f"system/etc/permissions/{perm_file}"
                if src_path in z.namelist():
                    with open(os.path.join(perm_dir, perm_file), 'wb') as out_f:
                        out_f.write(z.read(src_path))
        print("[+] HyperOS Launcher & XiaomiEuExt injected.")

    # 2. HyperOS Security Center (v7)
    sec_zip = os.path.join(mods_dir, "HyperOS-Security-Center", "HyperOS_SecurityV7@kashis_cringey_stuffs.zip")
    if os.path.exists(sec_zip):
        with zipfile.ZipFile(sec_zip) as z:
            dest_sec = os.path.join(prod_root, "priv-app", "MIUISecurityCenterGlobal")
            os.makedirs(dest_sec, exist_ok=True)
            clean_oat_directory(dest_sec)
            with open(os.path.join(dest_sec, "MIUISecurityCenterGlobal.apk"), 'wb') as out_f:
                out_f.write(z.read("files/MIUISecurityCenter.apk"))
        print("[+] HyperOS Security Center mod injected.")

    # 3. HyperOS App Vault (v5)
    vault_zip = os.path.join(mods_dir, "HyperOS-App-Vault", "HyperOS_AppVaultV5@kashis_cringey_stuffs.zip")
    if os.path.exists(vault_zip):
        with zipfile.ZipFile(vault_zip) as z:
            dest_vault = os.path.join(prod_root, "priv-app", "AppVault")
            os.makedirs(dest_vault, exist_ok=True)
            clean_oat_directory(dest_vault)
            with open(os.path.join(dest_vault, "AppVault.apk"), 'wb') as out_f:
                out_f.write(z.read("files/AppVault.apk"))
        print("[+] HyperOS App Vault mod injected.")

    # 4. ColorOS Control Center Plugin (v4)
    cc_zip = os.path.join(mods_dir, "ColorOS_Control_Center", "ColorOS_plugin_mod_V4@kashis_cringey_stuffs.zip")
    if os.path.exists(cc_zip):
        with zipfile.ZipFile(cc_zip) as z:
            dest_cc = os.path.join(prod_root, "app", "MIUISystemUIPlugin")
            os.makedirs(dest_cc, exist_ok=True)
            clean_oat_directory(dest_cc)
            with open(os.path.join(dest_cc, "MIUISystemUIPlugin.apk"), 'wb') as out_f:
                out_f.write(z.read("files/OS4/MIUISystemUIPlugin.apk"))
        print("[+] ColorOS Control Center plugin injected.")

    # 5. HyperOS Native Dialer, Contacts & MMS
    dialer_zip = os.path.join(mods_dir, "HyperOS-Dialer", "HyperOS_Dialer_V3@kashis_cringey_stuffs.zip")
    if os.path.exists(dialer_zip):
        with zipfile.ZipFile(dialer_zip) as z:
            for apk_name, rel_path in [
                ("InCallUI.apk", "files/InCallUI/InCallUI.apk"),
                ("MIUIContacts.apk", "files/MIUIContacts/MIUIContacts.apk"),
                ("MiuiMms.apk", "files/MiuiMms/MiuiMms.apk")
            ]:
                folder_name = apk_name.replace(".apk", "")
                dest_dir = os.path.join(sys_root, "priv-app", folder_name)
                os.makedirs(dest_dir, exist_ok=True)
                clean_oat_directory(dest_dir)
                with open(os.path.join(dest_dir, apk_name), 'wb') as out_f:
                    out_f.write(z.read(rel_path))

            # Whitelist permission
            perm_dir = os.path.join(sys_root, "etc", "permissions")
            os.makedirs(perm_dir, exist_ok=True)
            perm_entry = "system/etc/permissions/privapp_whitelist_kashi.dialer.ext.xml"
            if perm_entry in z.namelist():
                with open(os.path.join(perm_dir, "privapp_whitelist_kashi.dialer.ext.xml"), 'wb') as out_f:
                    out_f.write(z.read(perm_entry))

            # Product Overlays
            overlay_dir = os.path.join(prod_root, "overlay")
            os.makedirs(overlay_dir, exist_ok=True)
            for ol in ["Dialer_overlay1_mods_center.apk", "Dialer_overlay2_mods_center.apk", "GmsConfigOverlayComms.apk"]:
                src_path = f"system/product/overlay/{ol}"
                if src_path in z.namelist():
                    with open(os.path.join(overlay_dir, ol), 'wb') as out_f:
                        out_f.write(z.read(src_path))
        print("[+] Native HyperOS Dialer, Contacts, MMS and Overlays injected.")

    # 6. HyperOS Theme Manager (v7)
    theme_zip = os.path.join(mods_dir, "HyperOS-Theme-Manager", "HyperOS_ThemeManagerV7@kashis_cringey_stuffs.zip")
    if os.path.exists(theme_zip):
        with zipfile.ZipFile(theme_zip) as z:
            dest_theme = os.path.join(prod_root, "app", "MIUIThemeManagerGlobal")
            os.makedirs(dest_theme, exist_ok=True)
            clean_oat_directory(dest_theme)
            with open(os.path.join(dest_theme, "MIUIThemeManagerGlobal.apk"), 'wb') as out_f:
                out_f.write(z.read("files/MIUIThemeManager.apk"))
        print("[+] HyperOS Theme Manager mod injected.")

    # 7. SweetTweaks Settings Integration App
    tweaks_apk = os.path.abspath(os.path.join(target_root_dir, "..", "sweet_tweaks_app", "dist", "SweetTweaks.apk"))
    if os.path.isfile(tweaks_apk):
        dest_tweaks = os.path.join(sys_root, "priv-app", "SweetTweaks")
        os.makedirs(dest_tweaks, exist_ok=True)
        shutil.copy2(tweaks_apk, os.path.join(dest_tweaks, "SweetTweaks.apk"))
        print("[+] SweetTweaks App injected into system/priv-app/SweetTweaks.")


def sync_fs_config(fs_config_path, src_dir, partition_name):
    """
    Synchronizes fs_config with the actual disk contents so e2fsdroid has
    entries for all directories and files, avoiding runtime exit errors.
    """
    if not os.path.isfile(fs_config_path):
        print(f"[-] fs_config not found: {fs_config_path}")
        return

    print(f"[*] Synchronizing {partition_name} fs_config: {fs_config_path}")
    existing_entries = {}
    with open(fs_config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split(None, 4)
            path = parts[0]
            existing_entries[path] = line_str

    # Build actual existing paths relative to partition
    disk_entries = {}
    prefix = partition_name

    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir).replace("\\", "/")
        if rel_root == ".":
            current_dir_key = prefix
        else:
            current_dir_key = f"{prefix}/{rel_root}"

        # Register directory
        if current_dir_key not in disk_entries:
            if current_dir_key in existing_entries:
                disk_entries[current_dir_key] = existing_entries[current_dir_key]
            else:
                disk_entries[current_dir_key] = f"{current_dir_key} 0 0 0755"

        for file_name in files:
            if rel_root == ".":
                file_key = f"{prefix}/{file_name}"
            else:
                file_key = f"{prefix}/{rel_root}/{file_name}"

            if file_key in existing_entries:
                disk_entries[file_key] = existing_entries[file_key]
            else:
                mode = "0755" if "/bin" in file_key else "0644"
                disk_entries[file_key] = f"{file_key} 0 0 {mode}"

    # Always ensure root and base entries exist
    root_lines = [
        "/ 0 0 0755",
        f"{prefix}/ 0 0 0755",
        f"{prefix} 0 0 0755",
        f"{prefix}/lost+found 0 0 0755"
    ]

    all_lines = []
    for r in root_lines:
        all_lines.append(existing_entries.get(r.split()[0], r))

    for k in sorted(disk_entries.keys()):
        if k not in ["/", prefix, f"{prefix}/", f"{prefix}/lost+found"]:
            all_lines.append(disk_entries[k])

    with open(fs_config_path, 'w', encoding='utf-8', newline='\n') as f:
        for entry in all_lines:
            f.write(entry + "\n")

    print(f"[+] fs_config synchronized: {len(all_lines)} entries written.")


def patch_fstab_for_rw(fstab_input_path, fstab_output_path):
    print(f"[*] Patching fstab for Read-Write (RW) support: {fstab_input_path} -> {fstab_output_path}")
    with open(fstab_input_path, 'r', encoding='utf-8') as in_f, open(fstab_output_path, 'w', encoding='utf-8') as out_f:
        for line in in_f:
            if any(partition in line for partition in ["/system", "/system_ext", "/product", "/vendor", "/odm"]):
                line = re.sub(r'\bro\b', 'rw', line)
                line = re.sub(r'\bavb(_keys)?(=[^,\s]+)?', '', line)
                line = re.sub(r',,+', ',', line)
                # Clean dangling comma before space
                line = re.sub(r',\s', '  ', line)
            out_f.write(line)
    print("[+] fstab patched with rw flags and AVB enforcement removed.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <target_extracted_dir> [mods_dir]")
        sys.exit(1)
    target_dir = os.path.abspath(sys.argv[1])
    mods_directory = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace", "mods"))

    # 1. Purge unwanted bloat & subscreen
    purge_unwanted_packages(target_dir)

    # 2. Patch build.props
    for prop in glob.glob(os.path.join(target_dir, "**", "build.prop"), recursive=True):
        patch_build_prop(prop)

    # 3. Inject Kakashi Mods
    inject_kakashi_mods(mods_directory, target_dir)

    # 4. Synchronize fs_config for system, system_ext, and product
    sync_fs_config(
        os.path.join(target_dir, "system", "config", "system_fs_config"),
        os.path.join(target_dir, "system", "system"),
        "system"
    )
    sync_fs_config(
        os.path.join(target_dir, "system_ext", "config", "system_ext_fs_config"),
        os.path.join(target_dir, "system_ext", "system_ext"),
        "system_ext"
    )
    sync_fs_config(
        os.path.join(target_dir, "product", "config", "product_fs_config"),
        os.path.join(target_dir, "product", "product"),
        "product"
    )
    print("\n[+] System patching & Kakashi mods injection completed successfully!")
