import os
import shutil
import sys
import threading
import time
import tkinter as tk
import winreg as reg
from tkinter import filedialog

import win32api
import win32file
from PIL import Image
from pystray import Icon, Menu, MenuItem

from helpers.config import (
    create_config,
    read_config,
    save_config,
)
from helpers.github import auto_update

REPO = "SavageCore/OnionSavesBackup"
CURRENT_VERSION = "0.0.0"
APP_PATH = os.path.dirname(os.path.abspath(sys.executable))

if not read_config():
    create_config()

config = read_config()

auto_update(REPO, CURRENT_VERSION, APP_PATH, config)

source_path = "Saves/CurrentProfile"
destination_path = os.path.expanduser("~/Desktop/OnionSavesBackup")
source_drive = None
running = True

if "destination_path" in config:
    destination_path = config["destination_path"]


def copy_files():
    """Copy files from SD card to destination."""
    global source_drive
    global destination_path
    try:
        path = os.path.join(source_drive, source_path)
        shutil.copytree(path, destination_path, dirs_exist_ok=True)
        print("Files copied successfully.")
    except Exception as e:
        print(f"Error copying files: {e}")


def is_sd_card_mounted():
    """Check if SD card is mounted and has 'Onion' as volume label."""
    global source_drive
    drives = win32api.GetLogicalDrives()
    for i in range(26):
        mask = 1 << i
        if drives & mask:
            drive = f"{chr(65 + i)}:\\"
            drive_type = win32file.GetDriveType(drive)
            if drive_type != win32file.DRIVE_REMOVABLE:
                continue
            try:
                volume_info = win32api.GetVolumeInformation(drive)
                if volume_info[0] == "Onion":
                    source_drive = drive
                    return True
            except Exception as e:
                print(f"Error getting volume information: {e}")
                continue
    return False


def monitor_sd_card(icon):
    """Monitor SD card for changes and copy files when detected."""
    while running:
        if is_sd_card_mounted():
            print("SD card detected. Copying files...")
            copy_files()
            while is_sd_card_mounted():
                time.sleep(5)
        else:
            time.sleep(5)


def exit_action(icon, item):
    """Exit the tray application."""
    global running
    running = False
    icon.stop()


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


def set_destination_path(icon, item):
    """Set the destination path for copied files."""
    global destination_path
    global config

    # Initialize a hidden Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Prompt user to choose a directory
    selected_path = filedialog.askdirectory(title="Select Destination Folder")

    # Update the global destination path if the user selected a folder
    if selected_path:
        destination_path = selected_path
        config["destination_path"] = destination_path
        save_config(config)
        print(f"Destination path updated to: {destination_path}")
    else:
        print("No folder selected. Destination path remains unchanged.")


def setup_tray_icon():
    """Set up system tray icon."""
    # Get path to bundled icon.png
    image_path = resource_path("icon.png")

    # Use a placeholder image if icon.png does not exist
    if not os.path.exists(image_path):
        img = Image.new("RGB", (64, 64), color=(255, 0, 0))  # Red square
    else:
        img = Image.open(image_path)

    # Create the tray icon menu
    menu = Menu(
        MenuItem("Choose Backup Folder", set_destination_path),
        # Checkable menu item, start with windows
        MenuItem("Start with Windows", toggle_startup, checked=is_startup_enabled),
        # Divider
        MenuItem(Menu.SEPARATOR, None),
        MenuItem("Exit", exit_action),
    )
    icon = Icon("OnionSavesBackup", img, "Onion Saves Backup", menu)
    threading.Thread(target=monitor_sd_card, args=(icon,), daemon=True).start()
    icon.run()


def add_to_startup():
    # Get the correct path to the running executable
    if getattr(sys, "frozen", False):  # Check if running as a PyInstaller executable
        address = sys.executable  # Path to the .exe file
    else:
        address = os.path.abspath(
            __file__
        )  # Path to the script (if running as a script)

    # Add to startup registry
    s_name = "OnionSavesBackup"
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        open_key = reg.OpenKey(key, key_value, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(open_key, s_name, 0, reg.REG_SZ, address)
        reg.CloseKey(open_key)

        config["start_with_windows"] = True
        save_config(config)
    except Exception as e:
        print(f"Failed to add to startup: {e}")


def remove_from_startup():
    global config
    # Remove from startup registry
    s_name = "OnionSavesBackup"
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        open_key = reg.OpenKey(key, key_value, 0, reg.KEY_SET_VALUE)
        reg.DeleteValue(open_key, s_name)
        reg.CloseKey(open_key)

        config["start_with_windows"] = False
        save_config(config)
    except Exception as e:
        print(f"Failed to remove from startup: {e}")


def toggle_startup(icon, item):
    """Toggle whether the application starts with Windows."""
    global config

    # Check if the application is set to start with Windows
    if item.checked:
        remove_from_startup()
        item.checked = False
    else:
        add_to_startup()
        item.checked = True

    # Save the updated configuration
    save_config(config)


def is_startup_enabled(item=None):
    """Check if the application is set to start with Windows."""
    s_name = "OnionSavesBackup"
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        open_key = reg.OpenKey(key, key_value, 0, reg.KEY_READ)
        value, _ = reg.QueryValueEx(open_key, s_name)
        reg.CloseKey(open_key)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Failed to check startup: {e}")
        return False


if __name__ == "__main__":
    if config.get("start_with_windows", True):
        add_to_startup()
    setup_tray_icon()
