#!/usr/bin/env bash

DEVICE_CODENAME="stone"
DEVICE_NAME="Redmi Note 12 5G/POCO X5 5G"
KERNEL_NAME="Nethunter-X"
KERNEL_DEFCONFIG="nethunter_defconfig"
ANYKERNEL_DIR="$PWD/anykernel"
BUILD_TYPE="RELEASE"

function check_dependencies() {
    echo "[+] Checking dependencies..."
    
    # List of required packages
    local required_packages=(
        "build-essential"
        "libncurses-dev"
        "flex"
        "bison"
        "libssl-dev"
        "bc"
        "curl"
        "wget"
        "unzip"
        "zip"
        "git"
        "llvm"
        "clang"
        "lld"
        "gcc-aarch64-linux-gnu"
        "gcc-arm-linux-gnueabi"
    )
    
    # Check if we're on a Debian/Ubuntu-based system
    if command -v apt-get &> /dev/null; then
        echo "[+] Detected Debian/Ubuntu-based system"
        
        # Update package list
        echo "[+] Updating package list..."
        sudo apt-get update
        
        # Check and install missing packages
        local missing_packages=()
        for package in "${required_packages[@]}"; do
            if ! dpkg -l | grep -q "^ii  $package "; then
                missing_packages+=("$package")
            fi
        done
        
        if [ ${#missing_packages[@]} -gt 0 ]; then
            echo "[+] Installing missing packages: ${missing_packages[*]}"
            sudo apt-get install -y "${missing_packages[@]}"
        else
            echo "[+] All required packages are already installed"
        fi
    # Check if we're on an Arch-based system
    elif command -v pacman &> /dev/null; then
        echo "[+] Detected Arch-based system"
        
        # Check and install missing packages
        local missing_packages=()
        for package in "${required_packages[@]}"; do
            # Map Debian package names to Arch package names
            case "$package" in
                "build-essential") arch_package="base-devel" ;;
                "libncurses-dev") arch_package="ncurses" ;;
                "flex") arch_package="flex" ;;
                "bison") arch_package="bison" ;;
                "libssl-dev") arch_package="openssl" ;;
                "bc") arch_package="bc" ;;
                "curl") arch_package="curl" ;;
                "wget") arch_package="wget" ;;
                "unzip") arch_package="unzip" ;;
                "zip") arch_package="zip" ;;
                "git") arch_package="git" ;;
                "llvm") arch_package="llvm" ;;
                "clang") arch_package="clang" ;;
                "lld") arch_package="lld" ;;
                "gcc-aarch64-linux-gnu") arch_package="aarch64-linux-gnu-gcc" ;;
                "gcc-arm-linux-gnueabi") arch_package="arm-linux-gnueabi-gcc" ;;
                *) arch_package="$package" ;;
            esac
            
            if ! pacman -Q "$arch_package" &> /dev/null; then
                missing_packages+=("$arch_package")
            fi
        done
        
        if [ ${#missing_packages[@]} -gt 0 ]; then
            echo "[+] Installing missing packages: ${missing_packages[*]}"
            sudo pacman -S --noconfirm "${missing_packages[@]}"
        else
            echo "[+] All required packages are already installed"
        fi
    else
        echo "[!] Unsupported package manager. Please install dependencies manually:"
        echo "    Required packages: ${required_packages[*]}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check for required tools
    local required_tools=("make" "gcc" "clang" "ld.lld" "llvm-ar" "llvm-nm" "llvm-objcopy" "llvm-strip" "aarch64-linux-gnu-gcc" "arm-linux-gnueabi-gcc")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo "[!] Missing required tools: ${missing_tools[*]}"
        echo "[!] Please install them and try again"
        exit 1
    else
        echo "[+] All required tools are available"
    fi
    
    # Check if rtl8188eus directory exists
    if [ ! -d "rtl8188eus" ]; then
        echo "[!] rtl8188eus directory not found"
        echo "[+] Please ensure the rtl8188eus driver source is available"
        exit 1
    fi
    
    echo "[+] Dependency check completed successfully!"
}

function setup_clang() {
    # Use system clang
    export PATH="/usr/lib/llvm-19/bin:$PATH"
    COMPILER_STRING="$(clang --version | head -n 1)"
    echo "[+] Compiler: $COMPILER_STRING"
}

# KernelSU support has been removed from this kernel
# Uncomment the following lines if you want to re-enable KernelSU support
# echo -n "Include KernelSU? (y/n): "
# read -r KERNELSU
# [ "$KERNELSU" = "y" ] && {
#     KERNEL_VARIANT="-KSU"
#     [ ! -d "KernelSU" ] && {
#         echo "[+] Downloading KernelSU..."
#         curl -LSs "https://raw.githubusercontent.com/SingkoLab/Kernel-Builder/batu/ksu_setup.sh" | bash -
#         sed -i "s/CONFIG_KSU=n/CONFIG_KSU=y/g" "arch/arm64/configs/$KERNEL_DEFCONFIG"
#     }
# }

export ARCH=arm64
export LLVM=1
export LLVM_IAS=1
export KBUILD_BUILD_USER="Nethunter"
export KBUILD_BUILD_HOST="Brick"
# KernelSU variant is disabled
KERNEL_VARIANT=""

function integrate_rtl8188eus() {
    echo "[+] Integrating rtl8188eus driver..."
    
    # Copy the rtl8188eus driver to the kernel source tree
    if [ ! -d "drivers/net/wireless/realtek/rtl8188eus" ]; then
        echo "[+] Copying rtl8188eus driver to kernel source..."
        cp -r rtl8188eus drivers/net/wireless/realtek/
    fi
    
    # Configure RTL8188EUS driver for Android ARM64 platform
    echo "[+] Configuring RTL8188EUS for Android ARM64..."
    sed -i 's/^CONFIG_PLATFORM_I386_PC = y/CONFIG_PLATFORM_I386_PC = n/' drivers/net/wireless/realtek/rtl8188eus/Makefile
    
    # Add Android-specific configuration to the end of the Makefile
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
    
    # Update the Kconfig file to include the rtl8188eus driver
    if ! grep -q "source.*rtl8188eus/Kconfig" drivers/net/wireless/realtek/Kconfig; then
        echo "[+] Adding rtl8188eus to Kconfig..."
        sed -i '/endif # WLAN_VENDOR_REALTEK/i source "drivers/net/wireless/realtek/rtl8188eus/Kconfig"' drivers/net/wireless/realtek/Kconfig
    fi
    
    # Update the Makefile to include the rtl8188eus driver
    if ! grep -q "obj-\$(CONFIG_RTL8188EU)" drivers/net/wireless/realtek/Makefile; then
        echo "[+] Adding rtl8188eus to Makefile..."
        echo 'obj-$(CONFIG_RTL8188EU) += rtl8188eus/' >> drivers/net/wireless/realtek/Makefile
    fi
    
    # Enable the driver in the kernel configuration as built-in
    echo "[+] Enabling rtl8188eus driver as built-in..."
    # Check if the line exists and replace it, otherwise append it
    if grep -q "^CONFIG_RTL8188EU=" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
        sed -i 's/^CONFIG_RTL8188EU=.*/CONFIG_RTL8188EU=y/' "arch/arm64/configs/$KERNEL_DEFCONFIG"
    elif grep -q "# CONFIG_RTL8188EU is not set" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
        sed -i 's/# CONFIG_RTL8188EU is not set/CONFIG_RTL8188EU=y/' "arch/arm64/configs/$KERNEL_DEFCONFIG"
    else
        echo "CONFIG_RTL8188EU=y" >> "arch/arm64/configs/$KERNEL_DEFCONFIG"
    fi
    
    # Also ensure it's set in the current .config if it exists
    if [ -f "out/.config" ]; then
        # Remove any existing CONFIG_RTL8188EU lines
        sed -i '/^CONFIG_RTL8188EU/d' "out/.config"
        sed -i '/^# CONFIG_RTL8188EU is not set/d' "out/.config"
        # Add the enabled configuration
        echo "CONFIG_RTL8188EU=y" >> "out/.config"
    fi
    
    # Ensure additional required wireless configurations are enabled
    echo "[+] Adding additional wireless configuration options..."
    configs_to_add=(
        "CONFIG_WIRELESS_EXT=y"
        "CONFIG_WEXT_CORE=y"
        "CONFIG_WEXT_PROC=y"
        "CONFIG_WEXT_PRIV=y"
        "CONFIG_CFG80211_WEXT=y"
        "CONFIG_MAC80211_LEDS=y"
        "CONFIG_NETDEVICES=y"
        "CONFIG_WLAN=y"
    )
    
    for config in "${configs_to_add[@]}"; do
        config_name=$(echo "$config" | cut -d'=' -f1)
        if ! grep -q "^$config_name=" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
            if ! grep -q "^# $config_name is not set" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
                echo "$config" >> "arch/arm64/configs/$KERNEL_DEFCONFIG"
            fi
        fi
        
        # Also add to current .config if it exists
        if [ -f "out/.config" ]; then
            if ! grep -q "^$config_name=" "out/.config"; then
                if ! grep -q "^# $config_name is not set" "out/.config"; then
                    echo "$config" >> "out/.config"
                fi
            fi
        fi
    done
}

function integrate_ft3519t() {
    echo "[+] Integrating FT3519T touchscreen driver..."

    # Ensure the FT3519T driver is enabled in defconfig
    if grep -q "^CONFIG_TOUCHSCREEN_FT3519T=" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
        sed -i 's/^CONFIG_TOUCHSCREEN_FT3519T=.*/CONFIG_TOUCHSCREEN_FT3519T=y/' "arch/arm64/configs/$KERNEL_DEFCONFIG"
    elif grep -q "^# CONFIG_TOUCHSCREEN_FT3519T is not set" "arch/arm64/configs/$KERNEL_DEFCONFIG"; then
        sed -i 's/^# CONFIG_TOUCHSCREEN_FT3519T is not set/CONFIG_TOUCHSCREEN_FT3519T=y/' "arch/arm64/configs/$KERNEL_DEFCONFIG"
    else
        echo "CONFIG_TOUCHSCREEN_FT3519T=y" >> "arch/arm64/configs/$KERNEL_DEFCONFIG"
    fi

    # Also ensure it's set in current .config if present
    if [ -f "out/.config" ]; then
        sed -i '/^CONFIG_TOUCHSCREEN_FT3519T/d' "out/.config"
        sed -i '/^# CONFIG_TOUCHSCREEN_FT3519T is not set/d' "out/.config"
        echo "CONFIG_TOUCHSCREEN_FT3519T=y" >> "out/.config"
    fi
}

function compile() {
    echo "[+] Building kernel..."
    make O=out "$KERNEL_DEFCONFIG"
    
    # Integrate the rtl8188eus driver before compilation
    integrate_rtl8188eus
    
    # Ensure FT3519T touchscreen is enabled
    integrate_ft3519t
    
    # Run non-interactive configuration to handle any new options
    echo "[+] Running non-interactive configuration..."
    make O=out olddefconfig
    
    # Verify RTL8188EU is actually enabled
    echo "[+] Verifying RTL8188EU configuration..."
    if grep -q "^CONFIG_RTL8188EU=y" "out/.config"; then
        echo "✅ RTL8188EU driver is enabled in kernel config"
    else
        echo "❌ RTL8188EU driver is NOT enabled - forcing enable..."
        # Remove any conflicting lines and force enable
        sed -i '/^CONFIG_RTL8188EU/d' "out/.config"
        sed -i '/^# CONFIG_RTL8188EU is not set/d' "out/.config"
        echo "CONFIG_RTL8188EU=y" >> "out/.config"
        # Run olddefconfig again to apply the change
        make O=out olddefconfig
        # Final verification
        if grep -q "^CONFIG_RTL8188EU=y" "out/.config"; then
            echo "✅ RTL8188EU driver is now enabled"
        else
            echo "❌ ERROR: Failed to enable RTL8188EU driver"
            echo "Checking dependencies..."
            grep -E "CONFIG_USB=|CONFIG_WLAN_VENDOR_REALTEK=|CONFIG_WLAN=" "out/.config"
            exit 1
        fi
    fi

    # Verify FT3519T touchscreen is enabled
    echo "[+] Verifying FT3519T touchscreen configuration..."
    if grep -q '^CONFIG_TOUCHSCREEN_FT3519T=y' "out/.config"; then
        echo "✅ FT3519T touchscreen driver is enabled in kernel config"
    else
        echo "❌ FT3519T driver is NOT enabled - forcing enable..."
        sed -i '/^CONFIG_TOUCHSCREEN_FT3519T/d' "out/.config"
        sed -i '/^# CONFIG_TOUCHSCREEN_FT3519T is not set/d' "out/.config"
        echo 'CONFIG_TOUCHSCREEN_FT3519T=y' >> "out/.config"
        make O=out olddefconfig
        if grep -q '^CONFIG_TOUCHSCREEN_FT3519T=y' "out/.config"; then
            echo "✅ FT3519T touchscreen driver is now enabled"
        else
            echo "❌ ERROR: Failed to enable FT3519T touchscreen driver"
            exit 1
        fi
    fi
    
    make -j"$(nproc)" O=out \
        CC=clang \
        LD=ld.lld \
        AR=llvm-ar \
        NM=llvm-nm \
        OBJCOPY=llvm-objcopy \
        STRIP=llvm-strip \
        CLANG_TRIPLE=aarch64-linux-gnu- \
        CROSS_COMPILE=aarch64-linux-gnu- \
        CROSS_COMPILE_ARM32=arm-linux-gnueabi-
}

function package() {
    [ ! -f "out/arch/arm64/boot/Image" ] && {
        echo "❌ Kernel Image missing!"
        exit 1
    }
    echo "[+] Packaging kernel..."
    rm -rf "$ANYKERNEL_DIR/Image" "$ANYKERNEL_DIR/dtbo.img"
    cp "out/arch/arm64/boot/Image" "$ANYKERNEL_DIR/"
    cp "out/arch/arm64/boot/dtbo.img" "$ANYKERNEL_DIR/"
    cd "$ANYKERNEL_DIR" || exit 1
    zip -r9 "../${KERNEL_NAME}-${DEVICE_CODENAME}-$(date '+%Y%m%d')${KERNEL_VARIANT}.zip" * -x .git README.md
}

### --- Main --- ###
check_dependencies
setup_clang
compile
package
echo "[+] Build completed!"
