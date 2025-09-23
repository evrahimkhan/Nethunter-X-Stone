#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import datetime
import argparse
import platform

# Global configuration
DEVICE_CODENAME = "stone"
DEVICE_NAME = "Redmi Note 12 5G/POCO X5 5G"
KERNEL_NAME = "Nethunter-X"
KERNEL_DEFCONFIG = "nethunter_defconfig"
ANYKERNEL_DIR = os.path.join(os.getcwd(), "anykernel")
BUILD_TYPE = "RELEASE"
LOG_DIR = "log"

# Required packages for different distributions
REQUIRED_PACKAGES = {
    'debian': [
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
        "gcc-arm-linux-gnueabi"
    ],
    'ubuntu': [
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
        "gcc-arm-linux-gnueabi"
    ],
    'kali': [
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
        "gcc-arm-linux-gnueabi"
    ],
    'linuxmint': [
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
        "gcc-arm-linux-gnueabi"
    ],
    'arch': [
        "base-devel",
        "ncurses",
        "flex",
        "bison",
        "openssl",
        "bc",
        "curl",
        "wget",
        "unzip",
        "zip",
        "git",
        "llvm",
        "clang",
        "lld",
        "aarch64-linux-gnu-gcc",
        "arm-linux-gnueabi-gcc"
    ]
}

REQUIRED_TOOLS = [
    "make",
    "gcc",
    "clang",
    "ld.lld",
    "llvm-ar",
    "llvm-nm",
    "llvm-objcopy",
    "llvm-strip",
    "aarch64-linux-gnu-gcc",
    "arm-linux-gnueabi-gcc"
]

def setup_logging():
    """Setup logging directory and return log file path"""
    # Create log directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, "build_{}.log".format(timestamp))
    
    return log_file

def log_message(message, log_file):
    """Log a message to both console and log file"""
    # Print to console with header
    print(f"\033[1;36m{message}\033[0m")  # Cyan bold header
    
    # Append to log file
    try:
        with open(log_file, 'a') as f:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"\033[1;31m[!] Failed to write to log file: {e}\033[0m")

def detect_os():
    """Detect the operating system"""
    os_name = platform.system().lower()
    if os_name == "linux":
        # Try to detect specific Linux distribution
        try:
            # Check for /etc/os-release
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    content = f.read()
                    if "kali" in content.lower():
                        return "kali"
                    elif "ubuntu" in content.lower():
                        return "ubuntu"
                    elif "debian" in content.lower():
                        return "debian"
                    elif "linuxmint" in content.lower():
                        return "linuxmint"
                    elif "arch" in content.lower() or "manjaro" in content.lower():
                        return "arch"
            # Check for specific files
            if os.path.exists("/etc/kali-version"):
                return "kali"
            elif os.path.exists("/etc/debian_version"):
                return "debian"
            elif os.path.exists("/etc/arch-release"):
                return "arch"
        except:
            pass
        return "linux"
    elif os_name == "windows":
        return "windows"
    else:
        return os_name

def detect_architecture():
    """Detect system architecture"""
    arch = platform.machine().lower()
    if arch in ['x86_64', 'amd64']:
        return 'amd64'
    elif arch in ['i386', 'i686']:
        return 'i386'
    elif arch.startswith('arm') or arch.startswith('aarch'):
        if '64' in arch:
            return 'arm64'
        else:
            return 'arm'
    else:
        return arch

def is_xterm_available():
    """Check if xterm is available"""
    return shutil.which("xterm") is not None

def run_in_xterm(command, title="Kernel Build Process"):
    """Run a command in a separate xterm window"""
    if is_xterm_available():
        xterm_cmd = f"xterm -title '{title}' -e 'bash -c \"{command}; echo; echo Press ENTER to close...; read\"' &"
        subprocess.Popen(xterm_cmd, shell=True)
        return True
    return False

def run_command(command, cwd=None, capture_output=False, log_file=None, use_xterm=False, title="Process"):
    """Run a shell command and return the result with live output"""
    # If xterm is requested and available, run in separate terminal
    if use_xterm and is_xterm_available():
        if run_in_xterm(command, title):
            return True, "Running in separate terminal"
    
    # Log the command being executed
    if log_file:
        log_message(f"[EXECUTING] {command}", log_file)
        print(f"\033[1;33m$ {command}\033[0m")  # Yellow command
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
            # Log output if we have a log file
            if log_file and result.stdout:
                with open(log_file, 'a') as f:
                    f.write(result.stdout)
            return result.returncode == 0, result.stdout
        else:
            # If xterm is requested and available, run in separate terminal
            if use_xterm and is_xterm_available():
                if run_in_xterm(command, title):
                    return True, "Running in separate terminal"
            # Run with live output to terminal
            result = subprocess.run(command, shell=True, cwd=cwd)
            return result.returncode == 0, None
    except Exception as e:
        error_msg = f"[!] Error running command '{command}': {e}"
        if log_file:
            log_message(error_msg, log_file)
        print(f"\033[1;31m{error_msg}\033[0m")  # Red error
        return False, None

def install_packages_debian(packages, log_file):
    """Install packages on Debian-based systems"""
    log_message("=== Installing Dependencies (Debian/Ubuntu/Kali/Linux Mint) ===", log_file)
    
    log_message("[+] Updating package list...", log_file)
    if not run_command("sudo apt-get update", log_file=log_file)[0]:
        log_message("[!] Failed to update package list", log_file)
        return False
    
    # Check and install missing packages
    missing_packages = []
    for package in packages:
        success, output = run_command(f"dpkg -l | grep -q '^ii  {package} '", capture_output=True)
        if not success:
            missing_packages.append(package)
    
    if missing_packages:
        log_message(f"[+] Installing missing packages: {' '.join(missing_packages)}", log_file)
        install_cmd = f"sudo apt-get install -y {' '.join(missing_packages)}"
        if not run_command(install_cmd, log_file=log_file)[0]:
            log_message("[!] Failed to install packages", log_file)
            return False
        return True
    else:
        log_message("[+] All required packages are already installed", log_file)
        return True

def install_packages_arch(packages, log_file):
    """Install packages on Arch-based systems"""
    log_message("=== Installing Dependencies (Arch Linux/Manjaro) ===", log_file)
    
    # Check and install missing packages
    missing_packages = []
    for package in packages:
        success, output = run_command(f"pacman -Q '{package}'", capture_output=True)
        if not success:
            missing_packages.append(package)
    
    if missing_packages:
        log_message(f"[+] Installing missing packages: {' '.join(missing_packages)}", log_file)
        install_cmd = f"sudo pacman -S --noconfirm {' '.join(missing_packages)}"
        if not run_command(install_cmd, log_file=log_file)[0]:
            log_message("[!] Failed to install packages", log_file)
            return False
        return True
    else:
        log_message("[+] All required packages are already installed", log_file)
        return True

def check_dependencies(log_file):
    """Check and install required dependencies"""
    log_message("=== Checking Dependencies ===", log_file)
    
    # Set architecture environment variables
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    os.environ["CROSS_COMPILE"] = "aarch64-linux-gnu-"
    os.environ["CROSS_COMPILE_ARM32"] = "arm-linux-gnueabi-"
    
    # Detect OS and architecture
    detected_os = detect_os()
    detected_arch = detect_architecture()
    
    log_message(f"[+] Detected OS: {detected_os}", log_file)
    log_message(f"[+] Detected Architecture: {detected_arch}", log_file)
    
    # Handle Windows (not supported for kernel building)
    if detected_os == "windows":
        log_message("[!] Windows is not supported for kernel building", log_file)
        log_message("[!] Please use WSL or a Linux distribution", log_file)
        response = input("Continue anyway? (y/N): ")
        if not response.lower().startswith('y'):
            sys.exit(1)
        return True
    
    # Install packages based on detected OS
    if detected_os in ['debian', 'ubuntu', 'kali', 'linuxmint']:
        if shutil.which("apt-get"):
            return install_packages_debian(REQUIRED_PACKAGES.get(detected_os, REQUIRED_PACKAGES['debian']), log_file)
        else:
            log_message(f"[!] apt-get not found on {detected_os}", log_file)
            return False
    elif detected_os == "arch":
        if shutil.which("pacman"):
            return install_packages_arch(REQUIRED_PACKAGES.get(detected_os, REQUIRED_PACKAGES['arch']), log_file)
        else:
            log_message("[!] pacman not found on Arch-based system", log_file)
            return False
    else:
        log_message(f"[!] Unsupported OS: {detected_os}", log_file)
        log_message("[!] Please install dependencies manually:", log_file)
        packages = REQUIRED_PACKAGES.get(detected_os, REQUIRED_PACKAGES.get('debian', []))
        log_message(f"    Required packages: {' '.join(packages)}", log_file)
        response = input("Continue anyway? (y/N): ")
        return response.lower().startswith('y')
    
    # Check for required tools
    missing_tools = []
    for tool in REQUIRED_TOOLS:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        log_message(f"[!] Missing required tools: {' '.join(missing_tools)}", log_file)
        log_message("[!] Please install them and try again", log_file)
        return False
    else:
        log_message("[+] All required tools are available", log_file)
        return True
    
    # Check if rtl8188eus directory exists
    if not os.path.isdir("rtl8188eus"):
        log_message("[!] rtl8188eus directory not found", log_file)
        log_message("[+] Please ensure the rtl8188eus driver source is available", log_file)
        return False
    
    return True

def setup_clang(log_file):
    """Setup clang compiler"""
    log_message("=== Setting up Clang Compiler ===", log_file)
    
    # Set architecture environment variables
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    os.environ["CROSS_COMPILE"] = "aarch64-linux-gnu-"
    os.environ["CROSS_COMPILE_ARM32"] = "arm-linux-gnueabi-"
    
    # Use system clang
    os.environ["PATH"] = "/usr/lib/llvm-19/bin:" + os.environ.get("PATH", "")
    success, output = run_command("clang --version", capture_output=True)
    if success and output:
        compiler_string = output.split('\n')[0]
        log_message(f"[+] Compiler: {compiler_string}", log_file)
        return True
    return False

def integrate_rtl8188eus(log_file):
    """Integrate RTL8188EUS driver into kernel source"""
    log_message("=== Integrating RTL8188EUS WiFi Driver ===", log_file)
    
    # Set architecture environment
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    
    # Copy the rtl8188eus driver to the kernel source tree
    driver_dest = "drivers/net/wireless/realtek/rtl8188eus"
    if not os.path.isdir(driver_dest):
        log_message("[+] Copying rtl8188eus driver to kernel source...", log_file)
        try:
            shutil.copytree("rtl8188eus", driver_dest)
            log_message("[+] Successfully copied rtl8188eus driver", log_file)
        except Exception as e:
            log_message(f"[!] Failed to copy rtl8188eus driver: {e}", log_file)
            return False
    
    # Configure RTL8188EUS driver for Android ARM64 platform
    log_message("[+] Configuring RTL8188EUS for Android ARM64...", log_file)
    makefile_path = os.path.join(driver_dest, "Makefile")
    
    # Set architecture environment
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    
    # Replace CONFIG_PLATFORM_I386_PC = y with CONFIG_PLATFORM_I386_PC = n
    try:
        with open(makefile_path, 'r') as f:
            content = f.read()
        content = content.replace("CONFIG_PLATFORM_I386_PC = y", "CONFIG_PLATFORM_I386_PC = n")
        with open(makefile_path, 'w') as f:
            f.write(content)
        
        # Add Android-specific configuration if not already present
        if "ANDROID_ARM64_NETHUNTER" not in content:
            android_config = '''

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
'''
            
            # Enable the Android ARM64 platform
            content += android_config
            content = content.replace("CONFIG_PLATFORM_I386_PC = n", 
                                    "CONFIG_PLATFORM_I386_PC = n\nCONFIG_PLATFORM_ANDROID_ARM64_NETHUNTER = y")
            with open(makefile_path, 'w') as f:
                f.write(content)
        
        log_message("[+] Successfully configured RTL8188EUS driver", log_file)
    except Exception as e:
        log_message("[!] Failed to configure RTL8188EUS driver: {}".format(e), log_file)
        return False
    
    # Update the Kconfig file to include the rtl8188eus driver
    kconfig_path = "drivers/net/wireless/realtek/Kconfig"
    try:
        with open(kconfig_path, 'r') as f:
            kconfig_content = f.read()
        
        if 'source "drivers/net/wireless/realtek/rtl8188eus/Kconfig"' not in kconfig_content:
            log_message("[+] Adding rtl8188eus to Kconfig...", log_file)
            kconfig_content = kconfig_content.replace(
                "endif # WLAN_VENDOR_REALTEK",
                'source "drivers/net/wireless/realtek/rtl8188eus/Kconfig"\nendif # WLAN_VENDOR_REALTEK'
            )
            with open(kconfig_path, 'w') as f:
                f.write(kconfig_content)
        
        # Update the Makefile to include the rtl8188eus driver
        makefile_path = "drivers/net/wireless/realtek/Makefile"
        with open(makefile_path, 'r') as f:
            makefile_content = f.read()
        
        if 'obj-$(CONFIG_RTL8188EU)' not in makefile_content:
            log_message("[+] Adding rtl8188eus to Makefile...", log_file)
            makefile_content += 'obj-$(CONFIG_RTL8188EU) += rtl8188eus/\n'
            with open(makefile_path, 'w') as f:
                f.write(makefile_content)
        
        # Enable the driver in the kernel configuration as built-in
        log_message("[+] Enabling rtl8188eus driver as built-in...", log_file)
        defconfig_path = f"arch/arm64/configs/{KERNEL_DEFCONFIG}"
        
        # Read current defconfig
        with open(defconfig_path, 'r') as f:
            defconfig_lines = f.readlines()
        
        # Process defconfig to enable RTL8188EU
        new_lines = []
        found_rtl = False
        for line in defconfig_lines:
            if line.startswith("CONFIG_RTL8188EU="):
                new_lines.append("CONFIG_RTL8188EU=y\n")
                found_rtl = True
            elif line.startswith("# CONFIG_RTL8188EU is not set"):
                new_lines.append("CONFIG_RTL8188EU=y\n")
                found_rtl = True
            else:
                new_lines.append(line)
        
        if not found_rtl:
            new_lines.append("CONFIG_RTL8188EU=y\n")
        
        with open(defconfig_path, 'w') as f:
            f.writelines(new_lines)
        
        # Also ensure it's set in the current .config if it exists
        config_path = "out/.config"
        if os.path.isfile(config_path):
            # Remove any existing CONFIG_RTL8188EU lines
            with open(config_path, 'r') as f:
                config_lines = [line for line in f if not line.startswith(("CONFIG_RTL8188EU", "# CONFIG_RTL8188EU is not set"))]
            
            # Add the enabled configuration
            config_lines.append("CONFIG_RTL8188EU=y\n")
            
            with open(config_path, 'w') as f:
                f.writelines(config_lines)
        
        # Ensure additional required wireless configurations are enabled
        log_message("[+] Adding additional wireless configuration options...", log_file)
        configs_to_add = [
            "CONFIG_WIRELESS_EXT=y",
            "CONFIG_WEXT_CORE=y",
            "CONFIG_WEXT_PROC=y",
            "CONFIG_WEXT_PRIV=y",
            "CONFIG_CFG80211_WEXT=y",
            "CONFIG_MAC80211_LEDS=y",
            "CONFIG_NETDEVICES=y",
            "CONFIG_WLAN=y"
        ]
        
        # Process defconfig for additional configs
        with open(defconfig_path, 'r') as f:
            defconfig_lines = f.readlines()
        
        existing_configs = {}
        for line in defconfig_lines:
            if '=' in line:
                key = line.split('=')[0]
                existing_configs[key] = line.strip()
        
        for config in configs_to_add:
            config_name = config.split('=')[0]
            if config_name not in existing_configs:
                defconfig_lines.append(config + '\n')
        
        with open(defconfig_path, 'w') as f:
            f.writelines(defconfig_lines)
        
        # Also add to current .config if it exists
        if os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                config_lines = f.readlines()
            
            existing_configs = {}
            for line in config_lines:
                if '=' in line:
                    key = line.split('=')[0]
                    existing_configs[key] = line.strip()
            
            for config in configs_to_add:
                config_name = config.split('=')[0]
                if config_name not in existing_configs:
                    config_lines.append(config + '\n')
            
            with open(config_path, 'w') as f:
                f.writelines(config_lines)
                
        log_message("[+] Successfully integrated RTL8188EUS driver", log_file)
        return True
    except Exception as e:
        log_message(f"[!] Failed to integrate RTL8188EUS driver: {e}", log_file)
        return False

def integrate_ft3519t(log_file):
    """Integrate FT3519T touchscreen driver"""
    log_message("=== Integrating FT3519T Touchscreen Driver ===", log_file)
    
    # Set architecture environment
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    
    defconfig_path = f"arch/arm64/configs/{KERNEL_DEFCONFIG}"
    
    try:
        # Read current defconfig
        with open(defconfig_path, 'r') as f:
            defconfig_lines = f.readlines()
        
        # Process defconfig to enable FT3519T
        new_lines = []
        found_ft = False
        for line in defconfig_lines:
            if line.startswith("CONFIG_TOUCHSCREEN_FT3519T="):
                new_lines.append("CONFIG_TOUCHSCREEN_FT3519T=y\n")
                found_ft = True
            elif line.startswith("# CONFIG_TOUCHSCREEN_FT3519T is not set"):
                new_lines.append("CONFIG_TOUCHSCREEN_FT3519T=y\n")
                found_ft = True
            else:
                new_lines.append(line)
        
        if not found_ft:
            new_lines.append("CONFIG_TOUCHSCREEN_FT3519T=y\n")
        
        with open(defconfig_path, 'w') as f:
            f.writelines(new_lines)
        
        # Also ensure it's set in current .config if present
        config_path = "out/.config"
        if os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                config_lines = [line for line in f if not line.startswith(("CONFIG_TOUCHSCREEN_FT3519T", "# CONFIG_TOUCHSCREEN_FT3519T is not set"))]
            config_lines.append("CONFIG_TOUCHSCREEN_FT3519T=y\n")
            with open(config_path, 'w') as f:
                f.writelines(config_lines)
                
        log_message("[+] Successfully integrated FT3519T touchscreen driver", log_file)
        return True
    except Exception as e:
        log_message(f"[!] Failed to integrate FT3519T touchscreen driver: {e}", log_file)
        return False

def compile_kernel(log_file):
    """Compile the kernel"""
    log_message("=== Compiling Kernel ===", log_file)
    
    # Create output directory if it doesn't exist
    os.makedirs("out", exist_ok=True)
    
    # Set architecture environment variables
    env_backup = dict(os.environ)
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    os.environ["CROSS_COMPILE"] = "aarch64-linux-gnu-"
    os.environ["CROSS_COMPILE_ARM32"] = "arm-linux-gnueabi-"
    
    # Configure the kernel with proper architecture (non-interactive)
    print("[+] Configuring kernel for ARM64...")
    config_result, _ = run_command(f"make O=out ARCH=arm64 {KERNEL_DEFCONFIG}", use_xterm=True, title="Kernel Configuration")
    if not config_result:
        print("[!] Failed to configure kernel")
        sys.exit(1)
    
    # Run olddefconfig to handle any new options non-interactively
    print("[+] Running non-interactive configuration...")
    olddefconfig_result, _ = run_command("make O=out ARCH=arm64 olddefconfig", use_xterm=True, title="Kernel Olddefconfig")
    if not olddefconfig_result:
        print("[!] Failed to run olddefconfig")
        sys.exit(1)
    
    # Integrate the rtl8188eus driver before compilation
    if not integrate_rtl8188eus(log_file):
        log_message("[!] Failed to integrate RTL8188EUS driver", log_file)
        return False
    
    # Ensure FT3519T touchscreen is enabled
    if not integrate_ft3519t(log_file):
        log_message("[!] Failed to integrate FT3519T touchscreen driver", log_file)
        return False
    
    # Run non-interactive configuration to handle any new options
    print("[+] Running non-interactive configuration...")
    olddefconfig_result, _ = run_command("make O=out olddefconfig", use_xterm=True, title="Kernel Olddefconfig")
    if not olddefconfig_result:
        print("[!] Failed to run olddefconfig")
        sys.exit(1)
    
    # Verify RTL8188EU is actually enabled
    log_message("[+] Verifying RTL8188EU configuration...", log_file)
    config_path = "out/.config"
    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        if "CONFIG_RTL8188EU=y" in config_content:
            log_message("✅ RTL8188EU driver is enabled in kernel config", log_file)
        else:
            log_message("❌ RTL8188EU driver is NOT enabled - forcing enable...", log_file)
            # Remove any conflicting lines and force enable
            with open(config_path, 'r') as f:
                config_lines = [line for line in f if not line.startswith(("CONFIG_RTL8188EU", "# CONFIG_RTL8188EU is not set"))]
            config_lines.append("CONFIG_RTL8188EU=y\n")
            with open(config_path, 'w') as f:
                f.writelines(config_lines)
            
            # Run olddefconfig again to apply the change non-interactively
            run_command("make O=out ARCH=arm64 olddefconfig", use_xterm=True, title="Re-running Olddefconfig")
            
            # Final verification
            with open(config_path, 'r') as f:
                config_content = f.read()
            if "CONFIG_RTL8188EU=y" in config_content:
                log_message("✅ RTL8188EU driver is now enabled", log_file)
            else:
                log_message("❌ ERROR: Failed to enable RTL8188EU driver", log_file)
                # Check dependencies
                deps = []
                for line in config_content.split('\n'):
                    if any(dep in line for dep in ["CONFIG_USB=", "CONFIG_WLAN_VENDOR_REALTEK=", "CONFIG_WLAN="]):
                        deps.append(line)
                for dep in deps:
                    log_message(dep, log_file)
                return False
    
    # Verify FT3519T touchscreen is enabled
    log_message("[+] Verifying FT3519T touchscreen configuration...", log_file)
    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        if "CONFIG_TOUCHSCREEN_FT3519T=y" in config_content:
            log_message("✅ FT3519T touchscreen driver is enabled in kernel config", log_file)
        else:
            log_message("❌ FT3519T driver is NOT enabled - forcing enable...", log_file)
            with open(config_path, 'r') as f:
                config_lines = [line for line in f if not line.startswith(("CONFIG_TOUCHSCREEN_FT3519T", "# CONFIG_TOUCHSCREEN_FT3519T is not set"))]
            config_lines.append("CONFIG_TOUCHSCREEN_FT3519T=y\n")
            with open(config_path, 'w') as f:
                f.writelines(config_lines)
            
            run_command("make O=out ARCH=arm64 olddefconfig", use_xterm=True, title="Re-running Olddefconfig")
            
            with open(config_path, 'r') as f:
                config_content = f.read()
            if "CONFIG_TOUCHSCREEN_FT3519T=y" in config_content:
                log_message("✅ FT3519T touchscreen driver is now enabled", log_file)
            else:
                log_message("❌ ERROR: Failed to enable FT3519T touchscreen driver", log_file)
                return False
    
    # Compile the kernel
    cores = os.cpu_count()
    compile_command = (
        f"make -j{cores} O=out ARCH=arm64 "
        "CC=clang "
        "LD=ld.lld "
        "AR=llvm-ar "
        "NM=llvm-nm "
        "OBJCOPY=llvm-objcopy "
        "STRIP=llvm-strip "
        "CLANG_TRIPLE=aarch64-linux-gnu- "
        "CROSS_COMPILE=aarch64-linux-gnu- "
        "CROSS_COMPILE_ARM32=arm-linux-gnueabi- "
        "KCFLAGS=-Wno-error=date-time"
    )
    
    log_message(f"[+] Compiling kernel with {cores} threads (this may take a while)...", log_file)
    start_time = datetime.datetime.now()
    log_message(f"[+] Started compilation at {start_time.strftime('%Y-%m-%d %H:%M:%S')}", log_file)
    
    # Use xterm for compilation but ensure non-interactive mode
    compile_result, _ = run_command(compile_command, use_xterm=True, title="Kernel Compilation")
    
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    log_message(f"[+] Finished compilation at {end_time.strftime('%Y-%m-%d %H:%M:%S')}", log_file)
    log_message(f"[+] Compilation took {duration}", log_file)
    
    if not compile_result:
        log_message("❌ Kernel compilation failed!", log_file)
        return False
    
    log_message("✅ Kernel compilation completed successfully!", log_file)
    return True

def package_kernel(log_file):
    """Package the compiled kernel"""
    log_message("=== Packaging Kernel ===", log_file)
    
    image_path = "out/arch/arm64/boot/Image"
    if not os.path.isfile(image_path):
        log_message("❌ Kernel Image missing!", log_file)
        return False
    
    # Remove old files
    for file in ["Image", "dtbo.img"]:
        file_path = os.path.join(ANYKERNEL_DIR, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # Copy new files
    shutil.copy(image_path, ANYKERNEL_DIR)
    dtbo_path = "out/arch/arm64/boot/dtbo.img"
    if os.path.isfile(dtbo_path):
        shutil.copy(dtbo_path, ANYKERNEL_DIR)
    
    # Create zip package
    os.chdir(ANYKERNEL_DIR)
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    zip_name = f"../{KERNEL_NAME}-{DEVICE_CODENAME}-{date_str}.zip"
    
    log_message("[+] Creating zip package...", log_file)
    package_result, _ = run_command(f"zip -r9 \"{zip_name}\" * -x .git README.md", log_file=log_file)
    
    if not package_result:
        log_message("❌ Kernel packaging failed!", log_file)
        os.chdir("..")
        return False
    
    log_message(f"[+] Kernel successfully packaged as: {zip_name}", log_file)
    os.chdir("..")
    return True

def clean_build_directory(log_file):
    """Clean the build directory"""
    log_message("=== Cleaning Build Directory ===", log_file)
    
    if os.path.isdir("out"):
        log_message("[+] Removing build directory...", log_file)
        clean_result, _ = run_command("rm -rf out", log_file=log_file)
        if not clean_result:
            log_message("[!] Failed to clean build directory", log_file)
            return False
        log_message("[+] Build directory cleaned successfully!", log_file)
    else:
        log_message("[+] Build directory doesn't exist, nothing to clean", log_file)
    
    return True

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(description="Nethunter-X Kernel Builder")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency checking")
    parser.add_argument("--clean", action="store_true", help="Clean build directory before building")
    parser.add_argument("--no-log", action="store_true", help="Disable logging to log directory")
    parser.add_argument("--os", choices=['auto', 'kali', 'ubuntu', 'debian', 'arch', 'linuxmint', 'windows'], 
                       default='auto', help="Specify OS type (default: auto-detect)")
    parser.add_argument("--arch", choices=['auto', 'amd64', 'i386', 'arm', 'arm64'], 
                       default='auto', help="Specify architecture (default: auto-detect)")
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = None
    if not args.no_log:
        log_file = setup_logging()
        print(f"\033[1;32m=== Logging to: {log_file} ===\033[0m")  # Green header
    
    # Setup environment variables for ARM64
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    os.environ["CROSS_COMPILE"] = "aarch64-linux-gnu-"
    os.environ["CROSS_COMPILE_ARM32"] = "arm-linux-gnueabi-"
    
    # Log start time
    start_time = datetime.datetime.now()
    log_message(f"=== Nethunter-X Kernel Build Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===", log_file)
    
    # Detect OS and architecture if not specified
    detected_os = detect_os() if args.os == 'auto' else args.os
    detected_arch = detect_architecture() if args.arch == 'auto' else args.arch
    
    log_message(f"=== System Information ===", log_file)
    log_message(f"[+] OS: {detected_os}", log_file)
    log_message(f"[+] Architecture: {detected_arch}", log_file)
    
    # Force ARM64 architecture for Android kernel
    log_message(f"[+] Target Architecture: arm64 (forced for Android kernel)", log_file)
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    
    # Clean build directory if requested
    if args.clean:
        if not clean_build_directory(log_file):
            log_message("❌ Failed to clean build directory!", log_file)
            sys.exit(1)
    
    # Check dependencies unless skipped
    if not args.skip_deps:
        if not check_dependencies(log_file):
            log_message("❌ Dependency check failed!", log_file)
            sys.exit(1)
    else:
        log_message("=== Skipping Dependency Check ===", log_file)
    
    # Setup compiler
    if not setup_clang(log_file):
        log_message("❌ Failed to setup clang compiler!", log_file)
        sys.exit(1)
    
    # Compile kernel
    if not compile_kernel(log_file):
        log_message("❌ Kernel compilation failed!", log_file)
        sys.exit(1)
    
    # Package kernel
    if not package_kernel(log_file):
        log_message("❌ Kernel packaging failed!", log_file)
        sys.exit(1)
    
    # Log completion
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    log_message(f"=== Build Completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')} ===", log_file)
    log_message(f"=== Total Build Time: {duration} ===", log_file)
    
    if log_file and not args.no_log:
        print(f"\033[1;32m=== Build completed! Log file: {log_file} ===\033[0m")  # Green completion message

if __name__ == "__main__":
    main()