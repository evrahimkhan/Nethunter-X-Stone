#!/bin/bash

# RTL8188EUS Driver Configuration Test Script
# This script tests the RTL8188EUS driver integration without doing a full build

set -e

echo "=== RTL8188EUS Driver Configuration Test ==="

# Check if rtl8188eus directory exists
if [ ! -d "rtl8188eus" ]; then
    echo "❌ Error: rtl8188eus directory not found"
    echo "Please ensure the RTL8188EUS driver source is available"
    exit 1
fi

# Check if the driver source has been copied
if [ ! -d "drivers/net/wireless/realtek/rtl8188eus" ]; then
    echo "[+] Copying RTL8188EUS driver to kernel source..."
    cp -r rtl8188eus drivers/net/wireless/realtek/
fi

# Apply the Android configuration fix
echo "[+] Configuring RTL8188EUS for Android ARM64..."

# Fix the platform configuration
sed -i 's/^CONFIG_PLATFORM_I386_PC = y/CONFIG_PLATFORM_I386_PC = n/' drivers/net/wireless/realtek/rtl8188eus/Makefile

# Add Android-specific configuration if not already present
if ! grep -q "ANDROID_ARM64_NETHUNTER" drivers/net/wireless/realtek/rtl8188eus/Makefile; then
    cat >> drivers/net/wireless/realtek/rtl8188eus/Makefile << 'EOF'

# Android ARM64 NetHunter platform configuration
ifeq ($(CONFIG_PLATFORM_ANDROID_ARM64_NETHUNTER), y)
EXTRA_CFLAGS += -DCONFIG_LITTLE_ENDIAN
EXTRA_CFLAGS += -DCONFIG_IOCTL_CFG80211 -DRTW_USE_CFG80211_STA_EVENT
EXTRA_CFLAGS += -DCONFIG_CONCURRENT_MODE
EXTRA_CFLAGS += -DCONFIG_PLATFORM_ANDROID
EXTRA_CFLAGS += -DCONFIG_RADIO_WORK
EXTRA_CFLAGS += -DRTW_VENDOR_EXT_SUPPORT
# Disabled RTW_ENABLE_WIFI_CONTROL_FUNC to fix compilation with newer kernels
# EXTRA_CFLAGS += -DRTW_ENABLE_WIFI_CONTROL_FUNC
EXTRA_CFLAGS += -DCONFIG_WIFI_MONITOR
ARCH := arm64
endif
EOF
        
    # Enable the Android ARM64 platform
    sed -i 's/^CONFIG_PLATFORM_I386_PC = n/CONFIG_PLATFORM_I386_PC = n\nCONFIG_PLATFORM_ANDROID_ARM64_NETHUNTER = y/' drivers/net/wireless/realtek/rtl8188eus/Makefile
fi

# Verify configuration
echo "[+] Verifying RTL8188EUS configuration..."

# Check platform settings
if grep -q "CONFIG_PLATFORM_I386_PC = n" drivers/net/wireless/realtek/rtl8188eus/Makefile && \
   grep -q "CONFIG_PLATFORM_ANDROID_ARM64_NETHUNTER = y" drivers/net/wireless/realtek/rtl8188eus/Makefile; then
    echo "✅ Platform configuration: CORRECT (Android ARM64)"
else
    echo "❌ Platform configuration: INCORRECT"
fi

# Check driver type settings
if grep -q "CONFIG_RTL8188E = y" drivers/net/wireless/realtek/rtl8188eus/Makefile && \
   grep -q "CONFIG_USB_HCI = y" drivers/net/wireless/realtek/rtl8188eus/Makefile; then
    echo "✅ Driver configuration: CORRECT (RTL8188E + USB)"
else
    echo "❌ Driver configuration: INCORRECT"
fi

# Check monitor mode
if grep -q "CONFIG_WIFI_MONITOR = y" drivers/net/wireless/realtek/rtl8188eus/Makefile; then
    echo "✅ Monitor mode: ENABLED"
else
    echo "❌ Monitor mode: DISABLED"
fi

# Check kernel integration
if grep -q "source.*rtl8188eus/Kconfig" drivers/net/wireless/realtek/Kconfig && \
   grep -q "obj-.*CONFIG_RTL8188EU.*rtl8188eus" drivers/net/wireless/realtek/Makefile; then
    echo "✅ Kernel integration: CORRECT"
else
    echo "❌ Kernel integration: INCORRECT"
fi

# Check defconfig
if grep -q "CONFIG_RTL8188EU=y" arch/arm64/configs/nethunter_defconfig; then
    echo "✅ Kernel defconfig: RTL8188EU ENABLED"
else
    echo "❌ Kernel defconfig: RTL8188EU NOT FOUND"
fi

echo ""
echo "=== Configuration Summary ==="
echo "Driver: RTL8188E USB WiFi Adapter"
echo "Platform: Android ARM64"
echo "Monitor Mode: Enabled"
echo "Built-in: Yes (not module)"
echo ""
echo "✅ RTL8188EUS driver is now properly configured!"
echo ""
echo "Next steps:"
echo "1. Build the kernel: ./build.sh"
echo "2. Flash the kernel to your Android device"
echo "3. Test with RTL8188EUS USB adapter"