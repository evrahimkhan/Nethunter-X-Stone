#!/bin/bash

# Cleanup script for Nethunter-X kernel build

echo "[+] Starting cleanup..."

# Remove build output directory
if [ -d "out" ]; then
    echo "[+] Removing build output directory..."
    rm -rf out
fi

# Remove any generated zip files
echo "[+] Removing generated zip files..."
rm -f Nethunter-X-*.zip

# Remove any log files or log folders
if [ -d "logs" ]; then
    echo "[+] Removing logs folder..."
    rm -rf logs
fi

# Remove .log files in the project root
echo "[+] Removing .log files..."
rm -f *.log

# Clean any temporary files
echo "[+] Removing temporary files..."
rm -f *.tmp
rm -f .config.old
rm -f .scmversion

# Clean any build artifacts in the kernel source
echo "[+] Cleaning kernel build artifacts..."
if [ -f "Makefile" ]; then
    make mrproper
fi

# Remove any leftover files from previous builds
echo "[+] Removing any remaining build artifacts..."
find . -name "*.o" -type f -delete
find . -name "*.cmd" -type f -delete
find . -name "*.d" -type f -delete
find . -name "*.mod.c" -type f -delete
find . -name "*.mod.o" -type f -delete
find . -name "*.ko" -type f -delete
find . -name "*.a" -type f -delete
find . -name "*.symvers" -type f -delete

echo "[+] Cleanup completed!"