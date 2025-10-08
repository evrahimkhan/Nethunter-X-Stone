#!/usr/bin/env python3

import os
import shutil
import subprocess
import glob
import fnmatch
from pathlib import Path

def run_command(cmd, shell=True, capture_output=True, check=False):
    """Run a command and return the result."""
    result = subprocess.run(cmd, shell=shell, capture_output=capture_output, text=True, check=check)
    return result

def remove_directory(dir_path):
    """Remove a directory if it exists."""
    if os.path.isdir(dir_path):
        print(f"[+] Removing {dir_path} directory...")
        shutil.rmtree(dir_path)

def remove_files(pattern):
    """Remove files matching the pattern."""
    files = glob.glob(pattern)
    for file in files:
        if os.path.isfile(file):
            os.remove(file)

def main():
    print("[+] Starting cleanup...")

    # Remove build output directory
    remove_directory("out")

    # Remove any generated zip files
    print("[+] Removing generated zip files...")
    remove_files("Nethunter-X-*.zip")

    # Remove logs folder
    remove_directory("logs")

    # Remove .log files in the project root
    print("[+] Removing .log files...")
    remove_files("*.log")

    # Clean any temporary files
    print("[+] Removing temporary files...")
    remove_files("*.tmp")
    if os.path.exists(".config.old"):
        os.remove(".config.old")
    if os.path.exists(".scmversion"):
        os.remove(".scmversion")

    # Clean any build artifacts in the kernel source
    print("[+] Cleaning kernel build artifacts...")
    if os.path.isfile("Makefile"):
        run_command("make mrproper")

    # Remove any leftover files from previous builds
    print("[+] Removing any remaining build artifacts...")

    # Define patterns to search for and delete
    patterns = [
        "*.o",
        "*.cmd", 
        "*.d",
        "*.mod.c",
        "*.mod.o",
        "*.ko",
        "*.a",
        "*.symvers"
    ]

    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

    # Also search recursively in subdirectories for build artifacts
    for root, dirs, files in os.walk("."):
        for file in files:
            for pattern in patterns:
                # Convert glob pattern to check against filename
                if fnmatch.fnmatch(file, pattern):
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

    print("[+] Cleanup completed!")

if __name__ == "__main__":
    main()