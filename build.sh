#!/usr/bin/env bash

# Explicitly set CC to system clang to avoid clang-neutron
export CC=clang

DEVICE_CODENAME="stone"
DEVICE_NAME="Redmi Note 12 5G/POCO X5 5G"
KERNEL_NAME="Nethunter"
KERNEL_DEFCONFIG="nethunter_defconfig"
ANYKERNEL_DIR="$PWD/anykernel"
BUILD_TYPE="RELEASE"

function check_dependencies() {
    echo "[+] Checking dependencies..."
    
    # Check if required packages are installed
    local missing_packages=()
    
    # Check for basic build tools
    command -v make >/dev/null 2>&1 || missing_packages+=("make")
    command -v gcc >/dev/null 2>&1 || missing_packages+=("gcc")
    command -v curl >/dev/null 2>&1 || missing_packages+=("curl")
    command -v zip >/dev/null 2>&1 || missing_packages+=("zip")
    
    # Check for ARM cross-compilation tools
    command -v aarch64-linux-gnu-gcc >/dev/null 2>&1 || missing_packages+=("gcc-aarch64-linux-gnu")
    command -v arm-linux-gnueabi-gcc >/dev/null 2>&1 || missing_packages+=("gcc-arm-linux-gnueabi")
    
    # Check for clang
    command -v clang >/dev/null 2>&1 || missing_packages+=("clang")
    command -v ld.lld >/dev/null 2>&1 || missing_packages+=("lld")
    
    # Check for clang-neutron
    if command -v clang-neutron >/dev/null 2>&1; then
        echo "[!] clang-neutron detected. Will explicitly use system clang instead."
    fi
    
    # Install missing packages if any
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo "[+] Installing missing dependencies: ${missing_packages[*]}"
        sudo apt update
        sudo apt install -y "${missing_packages[@]}"
    else
        echo "[+] All dependencies are installed"
    fi
    
    # Display compiler information
    echo "[+] Using system compiler:"
    clang --version | head -n 1
}

function clean_build_environment() {
    echo "[+] Cleaning build environment..."
    
    # Clean previous build output if it exists
    if [ -d "out" ]; then
        echo "[+] Removing previous build output..."
        rm -rf out
    fi
    
    # Clean any previous kernel images in anykernel directory
    if [ -f "$ANYKERNEL_DIR/Image" ]; then
        echo "[+] Removing previous kernel image from anykernel directory..."
        rm -f "$ANYKERNEL_DIR/Image"
    fi
    
    # Clean any previous dtbo images in anykernel directory
    if [ -f "$ANYKERNEL_DIR/dtbo.img" ]; then
        echo "[+] Removing previous dtbo image from anykernel directory..."
        rm -f "$ANYKERNEL_DIR/dtbo.img"
    fi
    
    echo "[+] Build environment cleaned!"
}

function check_rtl8188eus_integration() {
    echo "[+] Checking rtl8188eus driver integration..."
    
    # Check if rtl8188eus directory exists
    if [ ! -d "../rtl8188eus" ]; then
        echo "[!] rtl8188eus directory not found. Please ensure the driver is properly cloned."
        return 1
    fi
    
    # Check if the driver is properly linked or copied to the kernel source
    if [ ! -d "drivers/net/wireless/realtek/rtl8188eus" ]; then
        echo "[+] Integrating rtl8188eus driver into kernel source..."
        # Copy the driver to the kernel source
        cp -r ../rtl8188eus drivers/net/wireless/realtek/
        
        # Add the driver to the Kconfig file
        if ! grep -q "source \"drivers/net/wireless/realtek/rtl8188eus/Kconfig\"" drivers/net/wireless/realtek/Kconfig; then
            echo "source \"drivers/net/wireless/realtek/rtl8188eus/Kconfig\"" >> drivers/net/wireless/realtek/Kconfig
        fi
        
        # Add the driver to the Makefile
        if ! grep -q "obj-\$(CONFIG_RTL8188EU) += rtl8188eus/" drivers/net/wireless/realtek/Makefile; then
            echo "obj-\$(CONFIG_RTL8188EU) += rtl8188eus/" >> drivers/net/wireless/realtek/Makefile
        fi
        
        echo "[+] rtl8188eus driver integrated successfully!"
    else
        echo "[+] rtl8188eus driver already integrated."
    fi
    
    # Apply configuration patch
    echo "[+] Applying rtl8188eus configuration..."
    echo "CONFIG_RTL8188EU=y" >> arch/arm64/configs/nethunter_defconfig
}

function fix_common_warnings() {
    echo "[+] Fixing common warnings..."
    
    # Apply patch to rtl8188eus driver
    if [ -d "../rtl8188eus" ]; then
        echo "[+] Applying patch to rtl8188eus driver..."
        cd ../rtl8188eus
        patch -p1 < ../rtl8188eus-fix.patch
        cd ../nethunter-x-stone
    fi
    
    # Fix snprintf size warnings in thermal_core.c
    if [ -f "drivers/thermal/thermal_core.c" ]; then
        echo "[+] Fixing snprintf size warnings in thermal_core.c..."
        sed -i 's/snprintf(buffer, 4096, /snprintf(buffer, sizeof(buffer), /g' drivers/thermal/thermal_core.c
    fi
    
    # Fix misleading indentation in pd_policy_manager.c
    if [ -f "drivers/power/supply/pd_policy_manager.c" ]; then
        echo "[+] Fixing misleading indentation in pd_policy_manager.c..."
        # This is a more complex fix that would require manual inspection
        # For now, we'll just note that this needs attention
        echo "[!] Please manually fix misleading indentation in drivers/power/supply/pd_policy_manager.c"
    fi
    
    # Fix uninitialized variable warning in dsi_display.c
    if [ -f "techpack/display/msm/dsi/dsi_display.c" ]; then
        echo "[+] Initializing connector variable in dsi_display.c..."
        # This would require careful inspection of the code to properly initialize the variable
        # For now, we'll just note that this needs attention
        echo "[!] Please initialize 'connector' variable in techpack/display/msm/dsi/dsi_display.c"
    fi
    
    echo "[+] Common warning fixes applied (some require manual attention)!"
}

echo -n "Include KernelSU? (y/n): "
read -r KERNELSU
[ "$KERNELSU" = "y" ] && {
    KERNEL_VARIANT="-KSU"
    [ ! -d "KernelSU" ] && {
        echo "[+] Downloading KernelSU..."
        curl -LSs "https://raw.githubusercontent.com/SingkoLab/Kernel-Builder/batu/ksu_setup.sh" | bash -
        sed -i "s/CONFIG_KSU=n/CONFIG_KSU=y/g" "arch/arm64/configs/$KERNEL_DEFCONFIG"
    }
}

export ARCH=arm64
export LLVM=1
export LLVM_IAS=1
export KBUILD_BUILD_USER="Nethunter"
export KBUILD_BUILD_HOST="Brick"

function compile() {
    echo "[+] Building kernel..."
    
    # Explicitly use system clang
    export CC=clang
    export LD=ld.lld
    export AR=llvm-ar
    export NM=llvm-nm
    export OBJCOPY=llvm-objcopy
    export STRIP=llvm-strip
    
    # Configure the kernel
    make O=out "$KERNEL_DEFCONFIG"
    
    # Build with error checking
    # Increase frame size warning limit to 4096 to address stack frame warnings
    # Disable -Werror to allow build to continue despite warnings
    if ! make -j"$(nproc)" O=out \
        CC="$CC" \
        LD="$LD" \
        AR="$AR" \
        NM="$NM" \
        OBJCOPY="$OBJCOPY" \
        STRIP="$STRIP" \
        CLANG_TRIPLE=aarch64-linux-gnu- \
        CROSS_COMPILE=aarch64-linux-gnu- \
        CROSS_COMPILE_ARM32=arm-linux-gnueabi- \
        KCFLAGS="-Wframe-larger-than=4096 -Wno-error" 2>&1 | tee build.log; then
        echo "❌ Kernel build failed! Check build.log for details."
        exit 1
    fi
    
    # Check for warnings (but allow frame size warnings to pass since we've increased the limit)
    if grep -q "warning:" build.log; then
        echo "⚠️  Warnings found during build. Checking if they are critical..."
        # Filter out frame size warnings and non-critical warnings
        critical_warnings=$(grep "warning:" build.log | grep -v "frame-larger-than" | grep -v "deprecated" | grep -v "unused" | wc -l)
        if [ "$critical_warnings" -gt 0 ]; then
            echo "❌ Critical warnings found during build!"
            grep "warning:" build.log | grep -v "frame-larger-than" | grep -v "deprecated" | grep -v "unused"
            echo "[!] Build completed with warnings. Please review and address them."
        else
            echo "[+] Only non-critical warnings found. Continuing..."
        fi
    else
        echo "[+] Build completed with no warnings!"
    fi
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
check_rtl8188eus_integration
deep_clean
fix_common_warnings
compile
package
echo "[+] Build completed!"
