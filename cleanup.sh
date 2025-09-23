#!/usr/bin/env bash

DEVICE_CODENAME="stone"
KERNEL_NAME="Nethunter-X"
ANYKERNEL_DIR="$PWD/anykernel"
OUT_DIR="$PWD/out"

echo "[+] Starting cleanup process..."

# Clean the kernel build output directory if it exists
echo "[+] Cleaning kernel build directory..."
if [ -d "out" ]; then
    # Try to run make clean and mrproper first
    if [ -f "out/Makefile" ]; then
        make -C out clean 2>/dev/null || echo "[*] Warning: Could not run make clean"
        make -C out mrproper 2>/dev/null || echo "[*] Warning: Could not run make mrproper"
    fi
    
    # Ask user if they want to completely remove the out directory
    echo -n "[?] Do you want to completely remove the out/ directory? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "[+] Removing out/ directory completely..."
        rm -rf out/
        echo "[+] out/ directory removed successfully!"
    else
        echo "[*] out/ directory preserved as requested."
    fi
else
    echo "[*] No out directory found"
fi

# Remove generated files from anykernel directory, but preserve the base structure
echo "[+] Cleaning anykernel directory..."
rm -f "$ANYKERNEL_DIR/Image" "$ANYKERNEL_DIR/dtbo.img"
rm -f "$ANYKERNEL_DIR"/*.zip

# Reset KernelSU configuration if it was enabled
if [ -d "KernelSU" ]; then
    echo "[+] Resetting KernelSU configuration..."
    KERNEL_DEFCONFIG="nethunter_defconfig"
    if grep -q "CONFIG_KSU=y" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
        sed -i "s/CONFIG_KSU=y/CONFIG_KSU=n/g" "arch/arm64/configs/$KERNEL_DEFCONFIG"
        echo "[+] KernelSU disabled in defconfig"
    fi
fi

# Reset rtl8188eus driver integration
echo "[+] Resetting rtl8188eus driver integration..."
KERNEL_DEFCONFIG="nethunter_defconfig"
if grep -q "CONFIG_RTL8188EU=y" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
    sed -i "s/CONFIG_RTL8188EU=y/# CONFIG_RTL8188EU is not set/g" "arch/arm64/configs/$KERNEL_DEFCONFIG"
    echo "[+] rtl8188eus driver disabled in defconfig"
fi

# Remove rtl8188eus entries from Kconfig and Makefile if they exist
if grep -q "source.*rtl8188eus/Kconfig" drivers/net/wireless/realtek/Kconfig; then
    sed -i "/source.*rtl8188eus\/Kconfig/d" drivers/net/wireless/realtek/Kconfig
    echo "[+] rtl8188eus removed from Kconfig"
fi

if grep -q "obj-\$(CONFIG_RTL8188EU).*rtl8188eus/" drivers/net/wireless/realtek/Makefile; then
    sed -i "/obj-\$(CONFIG_RTL8188EU).*rtl8188eus\//d" drivers/net/wireless/realtek/Makefile
    echo "[+] rtl8188eus removed from Makefile"
fi

# Clean up any generated zip files in the root directory
echo "[+] Checking for generated kernel zip files..."
ZIP_FILES=$(ls "$KERNEL_NAME-$DEVICE_CODENAME"-*.zip 2>/dev/null)
if [ -n "$ZIP_FILES" ]; then
    echo "[+] Found generated kernel zip files:"
    ls -la "$KERNEL_NAME-$DEVICE_CODENAME"-*.zip
    echo -n "[?] Do you want to remove these zip files? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "[+] Removing generated kernel zip files..."
        # Remove all zip files matching the pattern Nethunter-X-stone-*.zip (with or without KSU variant)
        rm -f "$KERNEL_NAME-$DEVICE_CODENAME"-*.zip
        echo "[+] Zip files removed successfully!"
    else
        echo "[*] Zip files preserved as requested."
    fi
else
    echo "[*] No generated kernel zip files found."
fi

echo "[+] Cleanup completed successfully!"
echo "[NOTE] The out/ directory cleanup was processed based on user input."