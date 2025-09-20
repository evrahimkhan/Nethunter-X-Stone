#!/bin/bash
#
# Kmod Installation Helper for Android Devices
# Run this from your Kali Linux system with device connected
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KMOD_SCRIPT="$SCRIPT_DIR/scripts/Kmod"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        Nethunter Kmod Installation Tool      ║${NC}"
    echo -e "${CYAN}║             For Android Devices              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check if adb exists
    if ! command -v adb &> /dev/null; then
        echo -e "${RED}Error: ADB is not installed or not in PATH${NC}"
        exit 1
    fi
    
    # Check if Kmod script exists
    if [ ! -f "$KMOD_SCRIPT" ]; then
        echo -e "${RED}Error: Kmod script not found at $KMOD_SCRIPT${NC}"
        echo "Please ensure you've built the kernel first."
        exit 1
    fi
    
    echo -e "${GREEN}✓ ADB found${NC}"
    echo -e "${GREEN}✓ Kmod script found${NC}"
    echo ""
}

check_device_connection() {
    echo -e "${BLUE}Checking device connection...${NC}"
    
    # Check if device is connected
    local devices=$(adb devices | grep -v "List of devices" | grep "device$" | wc -l)
    
    if [ "$devices" -eq 0 ]; then
        echo -e "${RED}Error: No Android device detected${NC}"
        echo ""
        echo -e "${YELLOW}Please ensure:${NC}"
        echo "1. Device is connected via USB"
        echo "2. USB debugging is enabled in Developer Options"
        echo "3. Device is authorized (check device screen for popup)"
        echo ""
        echo "Run 'adb devices' to verify connection."
        exit 1
    elif [ "$devices" -gt 1 ]; then
        echo -e "${YELLOW}Warning: Multiple devices detected. Using first available device.${NC}"
    fi
    
    local device_info=$(adb devices | grep "device$" | head -1 | awk '{print $1}')
    echo -e "${GREEN}✓ Device connected: $device_info${NC}"
    echo ""
}

check_root_access() {
    echo -e "${BLUE}Checking root access...${NC}"
    
    local root_check=$(adb shell su -c "id" 2>/dev/null | grep "uid=0(root)" || echo "")
    
    if [ -z "$root_check" ]; then
        echo -e "${RED}Error: Root access not available${NC}"
        echo ""
        echo -e "${YELLOW}Please ensure:${NC}"
        echo "1. Device is rooted"
        echo "2. Root access is granted to ADB shell"
        echo "3. Superuser app (like Magisk) is properly configured"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Root access confirmed${NC}"
    echo ""
}

install_kmod() {
    echo -e "${BLUE}Installing Kmod script...${NC}"
    
    # Transfer script to device
    echo -e "${YELLOW}Transferring script to device...${NC}"
    adb push "$KMOD_SCRIPT" /sdcard/ || {
        echo -e "${RED}Error: Failed to transfer script to device${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Script transferred to /sdcard/Kmod${NC}"
    
    # Try different installation methods
    local installation_success=false
    local install_location=""
    
    # Method 1: Check for Magisk modules directory (most reliable for rooted devices)
    echo -e "${YELLOW}Checking for Magisk modules directory...${NC}"
    if adb shell su -c "test -d /data/adb/modules" 2>/dev/null; then
        echo -e "${YELLOW}Attempting Magisk module installation...${NC}"
        if adb shell su -c "mkdir -p /data/adb/modules/kmod_tool/system/bin && cp /sdcard/Kmod /data/adb/modules/kmod_tool/system/bin/ && chmod 755 /data/adb/modules/kmod_tool/system/bin/Kmod" 2>/dev/null; then
            # Create module.prop for Magisk
            adb shell su -c "cat > /data/adb/modules/kmod_tool/module.prop << 'EOF'
id=kmod_tool
name=Nethunter Kmod Tool
version=v1.0
versionCode=1
author=Nethunter-X-Stone
description=Nethunter kernel mode control tool
EOF" 2>/dev/null
            if adb shell su -c "test -f /data/adb/modules/kmod_tool/system/bin/Kmod && test -x /data/adb/modules/kmod_tool/system/bin/Kmod" 2>/dev/null; then
                echo -e "${GREEN}✓ Successfully installed as Magisk module to /system/bin/Kmod${NC}"
                echo -e "${YELLOW}Note: Reboot required for Magisk module to take effect${NC}"
                installation_success=true
                install_location="/system/bin/Kmod (via Magisk module)"
            fi
        fi
    fi
    
    # Method 2: Direct /system/bin installation (try multiple approaches)
    if [ "$installation_success" = false ]; then
        echo -e "${YELLOW}Attempting direct /system/bin installation...${NC}"
        
        # Try approach 1: Standard remount
        if adb shell su -c "mount -o remount,rw /system 2>/dev/null && cp /sdcard/Kmod /system/bin/ && chmod 755 /system/bin/Kmod && mount -o remount,ro /system" 2>/dev/null; then
            if adb shell su -c "test -f /system/bin/Kmod && test -x /system/bin/Kmod" 2>/dev/null; then
                echo -e "${GREEN}✓ Successfully installed to /system/bin/Kmod${NC}"
                installation_success=true
                install_location="/system/bin/Kmod"
            fi
        fi
        
        # Try approach 2: Mount by block device (for newer Android versions)
        if [ "$installation_success" = false ]; then
            local system_block=$(adb shell su -c "mount | grep ' /system ' | cut -d' ' -f1" 2>/dev/null | head -1)
            if [ -n "$system_block" ]; then
                if adb shell su -c "mount -o remount,rw $system_block /system 2>/dev/null && cp /sdcard/Kmod /system/bin/ && chmod 755 /system/bin/Kmod && mount -o remount,ro $system_block /system" 2>/dev/null; then
                    if adb shell su -c "test -f /system/bin/Kmod && test -x /system/bin/Kmod" 2>/dev/null; then
                        echo -e "${GREEN}✓ Successfully installed to /system/bin/Kmod${NC}"
                        installation_success=true
                        install_location="/system/bin/Kmod"
                    fi
                fi
            fi
        fi
    fi
    
    # Method 3: Install to /system/xbin (alternative system path)
    if [ "$installation_success" = false ]; then
        echo -e "${YELLOW}Attempting installation to /system/xbin...${NC}"
        if adb shell su -c "test -d /system/xbin" 2>/dev/null; then
            if adb shell su -c "mount -o remount,rw /system 2>/dev/null && cp /sdcard/Kmod /system/xbin/ && chmod 755 /system/xbin/Kmod && mount -o remount,ro /system" 2>/dev/null; then
                if adb shell su -c "test -f /system/xbin/Kmod && test -x /system/xbin/Kmod" 2>/dev/null; then
                    echo -e "${GREEN}✓ Successfully installed to /system/xbin/Kmod${NC}"
                    installation_success=true
                    install_location="/system/xbin/Kmod"
                fi
            fi
        fi
    fi
    
    # Method 4: Install to /vendor/bin (alternative)
    if [ "$installation_success" = false ]; then
        echo -e "${YELLOW}Attempting installation to /vendor/bin...${NC}"
        if adb shell su -c "mount -o remount,rw /vendor 2>/dev/null && cp /sdcard/Kmod /vendor/bin/ && chmod 755 /vendor/bin/Kmod && mount -o remount,ro /vendor" 2>/dev/null; then
            if adb shell su -c "test -f /vendor/bin/Kmod && test -x /vendor/bin/Kmod" 2>/dev/null; then
                echo -e "${GREEN}✓ Successfully installed to /vendor/bin/Kmod${NC}"
                installation_success=true
                install_location="/vendor/bin/Kmod"
            fi
        fi
    fi
    
    # Method 5: Install to /data/local/tmp with PATH symlink attempt
    if [ "$installation_success" = false ]; then
        echo -e "${YELLOW}Attempting installation to /data/local/tmp with PATH setup...${NC}"
        if adb shell su -c "cp /sdcard/Kmod /data/local/tmp/ && chmod 755 /data/local/tmp/Kmod" 2>/dev/null; then
            if adb shell su -c "test -f /data/local/tmp/Kmod && test -x /data/local/tmp/Kmod" 2>/dev/null; then
                # Try to create a symbolic link in /system/bin pointing to /data/local/tmp/Kmod
                if adb shell su -c "mount -o remount,rw /system 2>/dev/null && ln -sf /data/local/tmp/Kmod /system/bin/Kmod && mount -o remount,ro /system" 2>/dev/null; then
                    if adb shell su -c "test -L /system/bin/Kmod" 2>/dev/null; then
                        echo -e "${GREEN}✓ Successfully installed to /data/local/tmp/Kmod with /system/bin/Kmod symlink${NC}"
                        installation_success=true
                        install_location="/system/bin/Kmod -> /data/local/tmp/Kmod"
                    fi
                else
                    echo -e "${GREEN}✓ Successfully installed to /data/local/tmp/Kmod${NC}"
                    echo -e "${YELLOW}Note: Not in PATH - use full path: /data/local/tmp/Kmod${NC}"
                    installation_success=true
                    install_location="/data/local/tmp/Kmod"
                fi
            fi
        fi
    fi
    
    if [ "$installation_success" = false ]; then
        echo -e "${RED}Error: Failed to install Kmod script${NC}"
        echo ""
        echo -e "${YELLOW}Manual installation options:${NC}"
        echo "1. The script is available at /sdcard/Kmod on your device"
        echo "2. Copy it to /system/bin/ using a root file manager"
        echo "3. Set permissions to 755 (rwxr-xr-x)"
        echo "4. Alternatively, use: cp /sdcard/Kmod /data/local/tmp/ && chmod 755 /data/local/tmp/Kmod"
        exit 1
    fi
    
    # Store installation location for verification
    echo "$install_location" > /tmp/kmod_install_location
    
    # Clean up
    adb shell rm /sdcard/Kmod 2>/dev/null || true
    echo ""
}

verify_installation() {
    echo -e "${BLUE}Verifying installation...${NC}"
    
    # Read the installation location from temp file
    local install_location=""
    if [ -f "/tmp/kmod_install_location" ]; then
        install_location=$(cat /tmp/kmod_install_location)
        rm -f /tmp/kmod_install_location
    fi
    
    # Check if command is accessible from PATH (priority locations)
    local kmod_location=""
    local kmod_accessible_as_command=false
    
    # First, check if it's accessible directly as 'Kmod' command (in PATH)
    if adb shell su -c "which Kmod" 2>/dev/null | grep -q "/"; then
        kmod_location=$(adb shell su -c "which Kmod" 2>/dev/null | tr -d '\r')
        kmod_accessible_as_command=true
        echo -e "${GREEN}✓ Kmod accessible as command: $kmod_location${NC}"
    else
        # Check specific locations
        for location in "/system/bin/Kmod" "/system/xbin/Kmod" "/vendor/bin/Kmod" "/data/local/tmp/Kmod"; do
            if adb shell su -c "test -x $location" 2>/dev/null; then
                kmod_location="$location"
                break
            fi
        done
        
        if [ -z "$kmod_location" ]; then
            echo -e "${RED}Error: Kmod command not accessible${NC}"
            exit 1
        fi
        
        # Check if it's in a PATH location
        case "$kmod_location" in
            "/system/bin/Kmod"|"/system/xbin/Kmod"|"/vendor/bin/Kmod")
                kmod_accessible_as_command=true
                echo -e "${GREEN}✓ Kmod installed in PATH at: $kmod_location${NC}"
                ;;
            *)
                echo -e "${GREEN}✓ Kmod accessible at: $kmod_location${NC}"
                echo -e "${YELLOW}Note: Not in PATH - use full path to execute${NC}"
                ;;
        esac
    fi
    
    # Test command execution
    echo -e "${YELLOW}Testing command execution...${NC}"
    if adb shell su -c "$kmod_location help" | grep -q "Nethunter Kernel Mode Tool" 2>/dev/null; then
        echo -e "${GREEN}✓ Kmod command working properly${NC}"
    else
        echo -e "${YELLOW}Warning: Kmod help command may not work until kernel is flashed${NC}"
    fi
    
    # Store info for usage instructions
    if [ "$kmod_accessible_as_command" = true ]; then
        echo "command" > /tmp/kmod_usage_type
    else
        echo "$kmod_location" > /tmp/kmod_usage_type
    fi
    
    echo ""
}

show_usage_info() {
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo ""
    
    # Read usage type from temp file
    local usage_info=""
    if [ -f "/tmp/kmod_usage_type" ]; then
        usage_info=$(cat /tmp/kmod_usage_type)
        rm -f /tmp/kmod_usage_type
    fi
    
    if [ "$usage_info" = "command" ]; then
        echo -e "${GREEN}✓ Kmod is installed in PATH and ready to use!${NC}"
        echo ""
        echo -e "${GREEN}Basic Commands (from ADB):${NC}"
        echo "  adb shell su -c \"Kmod status\"      # Check current mode"
        echo "  adb shell su -c \"Kmod help\"        # Show help"
        echo "  adb shell su -c \"Kmod gaming\"      # Enable gaming mode"
        echo "  adb shell su -c \"Kmod standard\"    # Enable standard mode"
        echo "  adb shell su -c \"Kmod dynamic\"     # Enable dynamic mode"
        echo ""
        echo -e "${GREEN}Direct Device Usage (in Android terminal):${NC}"
        echo "  su -c \"Kmod gaming\"     # 🎮 Gaming mode"
        echo "  su -c \"Kmod status\"     # 📊 Check status"
        echo "  su -c \"Kmod help\"       # ℹ️ Show help"
    else
        echo -e "${YELLOW}Kmod is installed but not in PATH${NC}"
        echo -e "${BLUE}Location: $usage_info${NC}"
        echo ""
        echo -e "${GREEN}Basic Commands (from ADB):${NC}"
        echo "  adb shell su -c \"$usage_info status\"      # Check current mode"
        echo "  adb shell su -c \"$usage_info help\"        # Show help"
        echo "  adb shell su -c \"$usage_info gaming\"      # Enable gaming mode"
        echo "  adb shell su -c \"$usage_info standard\"    # Enable standard mode"
        echo "  adb shell su -c \"$usage_info dynamic\"     # Enable dynamic mode"
        echo ""
        echo -e "${GREEN}Direct Device Usage (in Android terminal):${NC}"
        echo "  su -c \"$usage_info gaming\"     # 🎮 Gaming mode"
        echo "  su -c \"$usage_info status\"     # 📊 Check status"
        echo "  su -c \"$usage_info help\"       # ℹ️ Show help"
    fi
    
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    if echo "$usage_info" | grep -q "Magisk"; then
        echo "1. Reboot the device for Magisk module to take effect"
        echo "2. Flash the Nethunter kernel (if not already done)"
        echo "3. Test the Kmod commands"
    else
        echo "1. Flash the Nethunter kernel to your device (if not already done)"
        echo "2. Test the Kmod commands"
    fi
    echo ""
}

main() {
    print_header
    check_prerequisites
    check_device_connection
    check_root_access
    install_kmod
    verify_installation
    show_usage_info
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0"
        echo ""
        echo "This script installs the Kmod control script to your Android device."
        echo "Prerequisites:"
        echo "  - Android device connected via ADB"
        echo "  - USB debugging enabled"
        echo "  - Root access available"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use $0 --help for usage information"
        exit 1
        ;;
esac