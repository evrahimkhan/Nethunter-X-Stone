#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Device and kernel configuration
DEVICE_CODENAME = "stone"
DEVICE_NAME = "Redmi Note 12 5G/POCO X5 5G"
KERNEL_NAME = "Nethunter-X"
KERNEL_DEFCONFIG = "nethunter_defconfig"
ANYKERNEL_DIR = os.path.join(os.getcwd(), "anykernel")
BUILD_TYPE = "RELEASE"



def check_dependencies():
    """Check for required packages and tools."""
    print("[+] Checking dependencies...")
    
    # List of required packages
    required_packages = [
        "build-essential",
        "libncurses-dev",
        "flex",
        "bison",
        "libssl-dev",
        "bc",
        "curl",
        "wget",
        "unzip",
        "zip",
        "git",
        "llvm",
        "clang",
        "lld",
        "gcc-aarch64-linux-gnu",
        "gcc-arm-linux-gnueabi",
    ]
    
    # Detect the operating system and package manager
    os_name = platform.system().lower()
    
    if os_name == "linux":
        # Detect distribution-specific package manager
        if os.path.exists("/etc/debian_version") or subprocess.run("which apt-get", shell=True, capture_output=True, text=True).returncode == 0:
            # Debian/Ubuntu-based system
            print("[+] Detected Debian/Ubuntu-based system")
            
            # Update package list
            print("[+] Updating package list...")
            subprocess.run("sudo apt-get update", shell=True, capture_output=False, text=True)
            
            # Check and install missing packages
            missing_packages = []
            for package in required_packages:
                result = subprocess.run(f"dpkg -l | grep -q '^ii  {package} '", shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"[+] Installing missing packages: {' '.join(missing_packages)}")
                result = subprocess.run(f"sudo apt-get install -y {' '.join(missing_packages)}", shell=True, capture_output=False, text=True)
            else:
                print("[+] All required packages are already installed")
                
        elif subprocess.run("which pacman", shell=True, capture_output=True, text=True).returncode == 0:
            # Arch-based system
            print("[+] Detected Arch-based system")
            
            # Map Debian package names to Arch package names
            arch_package_map = {
                "build-essential": "base-devel",
                "libncurses-dev": "ncurses",
                "libssl-dev": "openssl",
                "gcc-aarch64-linux-gnu": "aarch64-linux-gnu-gcc",
                "gcc-arm-linux-gnueabi": "arm-linux-gnueabi-gcc"
            }
            
            # Check and install missing packages
            missing_packages = []
            for package in required_packages:
                arch_package = arch_package_map.get(package, package)
                result = subprocess.run(f"pacman -Q {arch_package}", shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    missing_packages.append(arch_package)
            
            if missing_packages:
                print(f"[+] Installing missing packages: {' '.join(missing_packages)}")
                result = subprocess.run(f"sudo pacman -S --noconfirm {' '.join(missing_packages)}", shell=True, capture_output=False, text=True)
            else:
                print("[+] All required packages are already installed")
        else:
            print("[!] Unsupported package manager. Please install dependencies manually:")
            print(f"    Required packages: {' '.join(required_packages)}")
            print("Continuing anyway...")
    else:
        print(f"[!] Unsupported OS: {os_name}")
    
    # Check for required tools
    required_tools = [
        "make", "gcc", "clang", "ld.lld", "llvm-ar", "llvm-nm", 
        "llvm-objcopy", "llvm-strip", "aarch64-linux-gnu-gcc", "arm-linux-gnueabi-gcc"
    ]
    
    missing_tools = []
    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"[!] Missing required tools: {' '.join(missing_tools)}")
        print("[!] Please install them and try again")
        sys.exit(1)
    else:
        print("[+] All required tools are available")
    
    # Check if rtl8188eus directory exists
    if not os.path.isdir("rtl8188eus"):
        print("[!] rtl8188eus directory not found")
        print("[+] Please ensure the rtl8188eus driver source is available")
        sys.exit(1)
    
    print("[+] Dependency check completed successfully!")

def setup_clang():
    """Set up Clang compiler."""
    # Use system clang
    os.environ["PATH"] = f"/usr/lib/llvm-19/bin:{os.environ.get('PATH', '')}"
    
    try:
        result = subprocess.run("clang --version", shell=True, capture_output=True, text=True)
        compiler_string = result.stdout.splitlines()[0] if result.stdout else "Unknown"
        print(f"[+] Compiler: {compiler_string}")
    except Exception as e:
        print(f"[!] Error getting compiler version: {e}")

# Set up kernel build environment
os.environ["ARCH"] = "arm64"
os.environ["LLVM"] = "1"
os.environ["LLVM_IAS"] = "1"
os.environ["KBUILD_BUILD_USER"] = "Nethunter"
os.environ["KBUILD_BUILD_HOST"] = "Brick"
KERNEL_VARIANT = ""

def integrate_rtl8188eus():
    """Integrate the rtl8188eus driver into the kernel."""
    print("[+] Integrating rtl8188eus driver...")
    
    # Copy the rtl8188eus driver to the kernel source tree
    if not os.path.isdir("drivers/net/wireless/realtek/rtl8188eus"):
        print("[+] Copying rtl8188eus driver to kernel source...")
        import shutil
        shutil.copytree("rtl8188eus", "drivers/net/wireless/realtek/rtl8188eus")
    
    # Configure RTL8188EUS driver for Android ARM64 platform
    print("[+] Configuring RTL8188EUS for Android ARM64...")
    
    makefile_path = "drivers/net/wireless/realtek/rtl8188eus/Makefile"
    
    # Read the current content of the makefile
    with open(makefile_path, 'r') as f:
        makefile_content = f.read()
    
    # Replace platform configuration
    makefile_content = makefile_content.replace(
        "CONFIG_PLATFORM_I386_PC = y", 
        "CONFIG_PLATFORM_I386_PC = n"
    )
    
    # Add Android-specific configuration to the end of the Makefile
    android_config = """
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
"""
    
    if "ANDROID_ARM64_NETHUNTER" not in makefile_content:
        makefile_content += android_config
        # Enable the Android ARM64 platform
        makefile_content = makefile_content.replace(
            "CONFIG_PLATFORM_I386_PC = n",
            "CONFIG_PLATFORM_I386_PC = n\nCONFIG_PLATFORM_ANDROID_ARM64_NETHUNTER = y",
            1
        )
    
    # Write the updated content back to the makefile
    with open(makefile_path, 'w') as f:
        f.write(makefile_content)
    
    # Update the Kconfig file to include the rtl8188eus driver
    kconfig_path = "drivers/net/wireless/realtek/Kconfig"
    with open(kconfig_path, 'r') as f:
        kconfig_content = f.read()
    
    if "source \"drivers/net/wireless/realtek/rtl8188eus/Kconfig\"" not in kconfig_content:
        print("[+] Adding rtl8188eus to Kconfig...")
        kconfig_content = kconfig_content.replace(
            "endif # WLAN_VENDOR_REALTEK",
            'source "drivers/net/wireless/realtek/rtl8188eus/Kconfig"\nendif # WLAN_VENDOR_REALTEK'
        )
        
        with open(kconfig_path, 'w') as f:
            f.write(kconfig_content)
    
    # Update the Makefile to include the rtl8188eus driver
    makefile_realtek_path = "drivers/net/wireless/realtek/Makefile"
    with open(makefile_realtek_path, 'r') as f:
        makefile_realtek_content = f.read()
    
    if "obj-$(CONFIG_RTL8188EU) += rtl8188eus/" not in makefile_realtek_content:
        print("[+] Adding rtl8188eus to Makefile...")
        makefile_realtek_content += "\nobj-$(CONFIG_RTL8188EU) += rtl8188eus/\n"
        
        with open(makefile_realtek_path, 'w') as f:
            f.write(makefile_realtek_content)
    
    # Enable the driver in the kernel configuration as built-in
    print("[+] Enabling rtl8188eus driver as built-in...")
    
    defconfig_path = f"arch/arm64/configs/{KERNEL_DEFCONFIG}"
    with open(defconfig_path, 'r') as f:
        defconfig_content = f.read()
    
    # Check if the line exists and replace it, otherwise append it
    if "CONFIG_RTL8188EU=" in defconfig_content:
        defconfig_content = defconfig_content.replace(
            "CONFIG_RTL8188EU=m", "CONFIG_RTL8188EU=y"
        ).replace(
            "CONFIG_RTL8188EU=n", "CONFIG_RTL8188EU=y"
        )
    elif "# CONFIG_RTL8188EU is not set" in defconfig_content:
        defconfig_content = defconfig_content.replace(
            "# CONFIG_RTL8188EU is not set", "CONFIG_RTL8188EU=y"
        )
    else:
        defconfig_content += "\nCONFIG_RTL8188EU=y\n"
    
    with open(defconfig_path, 'w') as f:
        f.write(defconfig_content)
    
    # Also ensure it's set in the current .config if it exists
    if os.path.isfile("out/.config"):
        with open("out/.config", 'r') as f:
            config_content = f.read()
        
        # Remove any existing CONFIG_RTL8188EU lines
        lines = config_content.splitlines()
        filtered_lines = [line for line in lines if not line.startswith("CONFIG_RTL8188EU=") and not line.startswith("# CONFIG_RTL8188EU is not set")]
        config_content = "\n".join(filtered_lines) + "\n"
        config_content += "CONFIG_RTL8188EU=y\n"
        
        with open("out/.config", 'w') as f:
            f.write(config_content)
    
    # Ensure additional required wireless configurations are enabled
    print("[+] Adding additional wireless configuration options...")
    configs_to_add = [
        "CONFIG_WIRELESS_EXT=y",
        "CONFIG_WEXT_CORE=y",
        "CONFIG_WEXT_PROC=y",
        "CONFIG_WEXT_PRIV=y",
        "CONFIG_CFG80211_WEXT=y",
        "CONFIG_MAC80211_LEDS=y",
        "CONFIG_NETDEVICES=y",
        "CONFIG_WLAN=y",
    ]
    
    # Process defconfig
    with open(defconfig_path, 'r') as f:
        defconfig_content = f.read()
    
    for config in configs_to_add:
        config_name = config.split('=')[0]
        if f"^{config_name}=" not in defconfig_content and f"# {config_name} is not set" not in defconfig_content:
            defconfig_content += f"{config}\n"
    
    with open(defconfig_path, 'w') as f:
        f.write(defconfig_content)
    
    # Process current .config if it exists
    if os.path.isfile("out/.config"):
        with open("out/.config", 'r') as f:
            config_content = f.read()
        
        for config in configs_to_add:
            config_name = config.split('=')[0]
            if f"{config_name}=" not in config_content and f"# {config_name} is not set" not in config_content:
                config_content += f"{config}\n"
        
        with open("out/.config", 'w') as f:
            f.write(config_content)

def integrate_ft3519t():
    """Integrate the FT3519T touchscreen driver."""
    print("[+] Integrating FT3519T touchscreen driver...")

    defconfig_path = f"arch/arm64/configs/{KERNEL_DEFCONFIG}"
    with open(defconfig_path, 'r') as f:
        defconfig_content = f.read()

    # Update defconfig to enable FT3519T driver
    if "CONFIG_TOUCHSCREEN_FT3519T=" in defconfig_content:
        defconfig_content = defconfig_content.replace(
            "CONFIG_TOUCHSCREEN_FT3519T=n", "CONFIG_TOUCHSCREEN_FT3519T=y"
        )
    elif "# CONFIG_TOUCHSCREEN_FT3519T is not set" in defconfig_content:
        defconfig_content = defconfig_content.replace(
            "# CONFIG_TOUCHSCREEN_FT3519T is not set", "CONFIG_TOUCHSCREEN_FT3519T=y"
        )
    else:
        defconfig_content += "\nCONFIG_TOUCHSCREEN_FT3519T=y\n"

    with open(defconfig_path, 'w') as f:
        f.write(defconfig_content)

    # Also update current .config if it exists
    if os.path.isfile("out/.config"):
        with open("out/.config", 'r') as f:
            config_content = f.read()

        # Remove any existing CONFIG_TOUCHSCREEN_FT3519T lines
        lines = config_content.splitlines()
        filtered_lines = [line for line in lines if not line.startswith("CONFIG_TOUCHSCREEN_FT3519T=") and not line.startswith("# CONFIG_TOUCHSCREEN_FT3519T is not set")]
        config_content = "\n".join(filtered_lines) + "\n"
        config_content += "CONFIG_TOUCHSCREEN_FT3519T=y\n"

        with open("out/.config", 'w') as f:
            f.write(config_content)

def compile():
    """Compile the kernel."""
    print("[+] Building kernel...")
    
    # Create out directory if it doesn't exist
    os.makedirs("out", exist_ok=True)
    
    # Run defconfig
    result = subprocess.run(f"make O=out {KERNEL_DEFCONFIG}", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Defconfig failed!")
        print("=== STDERR ===")
        print(result.stderr)
        print("=== STDOUT ===")
        print(result.stdout)
        print(f"Exit code: {result.returncode}")
        sys.exit(1)
    
    # Integrate the rtl8188eus driver before compilation
    integrate_rtl8188eus()
    
    # Ensure FT3519T touchscreen is enabled
    integrate_ft3519t()
    
    # Run non-interactive configuration to handle any new options
    print("[+] Running non-interactive configuration...")
    result = subprocess.run("make O=out olddefconfig", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Olddefconfig failed!")
        print("=== STDERR ===")
        print(result.stderr)
        print("=== STDOUT ===")
        print(result.stdout)
        print(f"Exit code: {result.returncode}")
        sys.exit(1)
    
    # Verify RTL8188EU is actually enabled
    print("[+] Verifying RTL8188EU configuration...")
    if os.path.isfile("out/.config"):
        with open("out/.config", 'r') as f:
            config_content = f.read()
        
        if "CONFIG_RTL8188EU=y" in config_content:
            print("✅ RTL8188EU driver is enabled in kernel config")
        else:
            print("❌ RTL8188EU driver is NOT enabled - forcing enable...")
            # Remove any conflicting lines and force enable
            lines = config_content.splitlines()
            filtered_lines = [line for line in lines if not line.startswith("CONFIG_RTL8188EU=") and not line.startswith("# CONFIG_RTL8188EU is not set")]
            config_content = "\n".join(filtered_lines) + "\n"
            config_content += "CONFIG_RTL8188EU=y\n"
            
            with open("out/.config", 'w') as f:
                f.write(config_content)
            
            # Run olddefconfig again to apply the change
            result = subprocess.run("make O=out olddefconfig", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Olddefconfig failed!")
                print("=== STDERR ===")
                print(result.stderr)
                print("=== STDOUT ===")
                print(result.stdout)
                print(f"Exit code: {result.returncode}")
                sys.exit(1)
            
            # Final verification
            with open("out/.config", 'r') as f:
                config_content = f.read()
            
            if "CONFIG_RTL8188EU=y" in config_content:
                print("✅ RTL8188EU driver is now enabled")
            else:
                print("❌ ERROR: Failed to enable RTL8188EU driver")
                print("Checking dependencies...")
                # Look for relevant configuration lines
                relevant_lines = [line for line in config_content.splitlines() if "CONFIG_USB=" in line or "CONFIG_WLAN_VENDOR_REALTEK=" in line or "CONFIG_WLAN=" in line]
                for line in relevant_lines:
                    print(line)
                sys.exit(1)
    
    # Verify FT3519T touchscreen is enabled
    print("[+] Verifying FT3519T touchscreen configuration...")
    if os.path.isfile("out/.config"):
        with open("out/.config", 'r') as f:
            config_content = f.read()
        
        if 'CONFIG_TOUCHSCREEN_FT3519T=y' in config_content:
            print("✅ FT3519T touchscreen driver is enabled in kernel config")
        else:
            print("❌ FT3519T driver is NOT enabled - forcing enable...")
            # Remove any conflicting lines
            lines = config_content.splitlines()
            filtered_lines = [line for line in lines if not line.startswith("CONFIG_TOUCHSCREEN_FT3519T=") and not line.startswith("# CONFIG_TOUCHSCREEN_FT3519T is not set")]
            config_content = "\n".join(filtered_lines) + "\n"
            config_content += "CONFIG_TOUCHSCREEN_FT3519T=y\n"
            
            with open("out/.config", 'w') as f:
                f.write(config_content)
            
            result = subprocess.run("make O=out olddefconfig", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Olddefconfig failed!")
                print("=== STDERR ===")
                print(result.stderr)
                print("=== STDOUT ===")
                print(result.stdout)
                print(f"Exit code: {result.returncode}")
                sys.exit(1)
            
            with open("out/.config", 'r') as f:
                config_content = f.read()
            
            if 'CONFIG_TOUCHSCREEN_FT3519T=y' in config_content:
                print("✅ FT3519T touchscreen driver is now enabled")
            else:
                print("❌ ERROR: Failed to enable FT3519T touchscreen driver")
                sys.exit(1)
    
    # Run the actual compilation
    cmd = f"make -j{os.cpu_count()} O=out " \
          f"CC=clang " \
          f"LD=ld.lld " \
          f"AR=llvm-ar " \
          f"NM=llvm-nm " \
          f"OBJCOPY=llvm-objcopy " \
          f"STRIP=llvm-strip " \
          f"CLANG_TRIPLE=aarch64-linux-gnu- " \
          f"CROSS_COMPILE=aarch64-linux-gnu- " \
          f"CROSS_COMPILE_ARM32=arm-linux-gnueabi-"
    
    print(f"[+] Running compilation command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Kernel compilation failed!")
        print("=== STDERR ===")
        print(result.stderr)
        print("=== STDOUT ===")
        print(result.stdout)
        print(f"Exit code: {result.returncode}")
        sys.exit(1)
    else:
        print("✅ Kernel compilation completed successfully!")

def package():
    """Package the kernel into a flashable zip."""
    if not os.path.isfile("out/arch/arm64/boot/Image"):
        print("❌ Kernel Image missing!")
        sys.exit(1)
    
    print("[+] Packaging kernel...")
    
    # Remove old files in AnyKernel directory
    image_path = os.path.join(ANYKERNEL_DIR, "Image")
    dtbo_path = os.path.join(ANYKERNEL_DIR, "dtbo.img")
    
    if os.path.exists(image_path):
        os.remove(image_path)
    if os.path.exists(dtbo_path):
        os.remove(dtbo_path)
    
    # Copy the built kernel image and dtbo to AnyKernel directory
    shutil.copy("out/arch/arm64/boot/Image", os.path.join(ANYKERNEL_DIR, "Image"))
    shutil.copy("out/arch/arm64/boot/dtbo.img", os.path.join(ANYKERNEL_DIR, "dtbo.img"))
    
    # Create the zip file
    import zipfile
    from datetime import datetime
    
    date_str = datetime.now().strftime('%Y%m%d')
    zip_filename = f"{KERNEL_NAME}-{DEVICE_CODENAME}-{date_str}{KERNEL_VARIANT}.zip"
    zip_path = os.path.join(os.getcwd(), zip_filename)
    
    print(f"[+] Creating flashable zip: {zip_filename}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ANYKERNEL_DIR):
            for file in files:
                if file not in ['.git', 'README.md']:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, ANYKERNEL_DIR)
                    zipf.write(file_path, arcname)

    print(f"[+] Flashable zip created: {zip_path}")

def main():
    """Main function to run the full build process."""
    check_dependencies()
    setup_clang()
    compile()
    package()
    print("[+] Build completed!")

if __name__ == "__main__":
    main()