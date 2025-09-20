# Installing Kmod Script on Android Device - Detailed Guide

## Prerequisites

Before installing Kmod, ensure you have:
1. ✅ **Flashed the Nethunter kernel** successfully 
2. ✅ **Device booted** and running normally
3. ✅ **Root access** available (su command works)
4. ✅ **USB debugging enabled** in Developer Options
5. ✅ **ADB connection** working from your Kali system

## Step-by-Step Installation

### Step 1: Verify Device Connection

First, make sure your Android device is connected and accessible:

```bash
# On your Kali Linux system
cd /home/kali/project/Nethunter-X-Stone

# Check if device is detected
adb devices
```

**Expected output:**
```
List of devices attached
1234567890ABCDEF    device
```

If no devices appear, troubleshoot the connection first.

### Step 2: Verify Root Access

Check if your device has root access:

```bash
# Test root access
adb shell su -c "id"
```

**Expected output:**
```
uid=0(root) gid=0(root) groups=0(root)
```

If this fails, ensure your device is rooted properly.

### Step 3: Transfer Kmod Script to Device

```bash
# Push the script to device storage (accessible location)
adb push scripts/Kmod /sdcard/

# Verify the transfer
adb shell ls -la /sdcard/Kmod
```

**Expected output:**
```
-rw-rw---- 1 u0_a000 everybody 10568 2025-09-16 18:22 /sdcard/Kmod
```

### Step 4: Choose Installation Location

You have several options for where to install Kmod:

#### Option A: System Binary Directory (Recommended)
```bash
# Remount system as writable
adb shell su -c "mount -o remount,rw /system"

# Copy script to system binaries
adb shell su -c "cp /sdcard/Kmod /system/bin/"

# Set proper permissions
adb shell su -c "chmod 755 /system/bin/Kmod"

# Remount system as read-only (security)
adb shell su -c "mount -o remount,ro /system"

# Verify installation
adb shell su -c "which Kmod"
```

#### Option B: Alternative Location (if /system is protected)
```bash
# Install to /data/local/tmp (always writable)
adb shell su -c "cp /sdcard/Kmod /data/local/tmp/"
adb shell su -c "chmod 755 /data/local/tmp/Kmod"

# Create symlink for easy access
adb shell su -c "ln -sf /data/local/tmp/Kmod /system/bin/Kmod"
```

#### Option C: Vendor Binary Directory
```bash
# Some devices prefer vendor binaries
adb shell su -c "mount -o remount,rw /vendor"
adb shell su -c "cp /sdcard/Kmod /vendor/bin/"
adb shell su -c "chmod 755 /vendor/bin/Kmod"
adb shell su -c "mount -o remount,ro /vendor"
```

### Step 5: Verify Installation

Test if Kmod is properly installed and accessible:

```bash
# Check if command is found
adb shell su -c "which Kmod"

# Test script execution
adb shell su -c "Kmod help"

# Check version
adb shell su -c "Kmod --version"
```

**Expected output for help command:**
```
Nethunter Kernel Mode Control Tool v1.0

Usage: Kmod [COMMAND]

COMMANDS:
  gaming      Switch to gaming mode (performance)
  standard    Switch to standard mode (balanced)
  dynamic     Enable dynamic mode (auto-scaling)
  status      Show current mode and system info
  help        Show this help message

Examples:
  Kmod gaming     # Enable gaming mode
  Kmod status     # Check current mode
```

## Troubleshooting Installation Issues

### Issue 1: "Permission denied" when copying to /system

**Problem:** Modern Android has read-only system partition
**Solution:** 
```bash
# Try alternative location
adb shell su -c "cp /sdcard/Kmod /data/local/tmp/"
adb shell su -c "chmod 755 /data/local/tmp/Kmod"

# Add to PATH temporarily
adb shell su -c "export PATH=/data/local/tmp:$PATH && Kmod help"
```

### Issue 2: "Mount operation not permitted"

**Problem:** SELinux or system protection
**Solution:**
```bash
# Check SELinux status
adb shell getenforce

# If Enforcing, try:
adb shell su -c "setenforce 0"  # Temporarily disable
# Install script, then re-enable:
adb shell su -c "setenforce 1"
```

### Issue 3: "No such file or directory" when running Kmod

**Problem:** Missing dependencies or wrong interpreter
**Solution:**
```bash
# Check script header
adb shell head -1 /system/bin/Kmod

# Should show: #!/system/bin/sh
# If wrong, fix the shebang:
adb shell su -c "sed -i '1s|.*|#!/system/bin/sh|' /system/bin/Kmod"
```

### Issue 4: Script runs but kernel interface not found

**Problem:** Kernel modules not loaded or procfs not available
**Solution:**
```bash
# Check if kernel modules are loaded
adb shell su -c "dmesg | grep nethunter"

# Check procfs interface
adb shell su -c "ls -la /proc/nethunter_mode"

# If missing, verify kernel was flashed correctly
```

## Advanced Installation Options

### Option 1: Magisk Module Installation

If you have Magisk installed:

```bash
# Create Magisk module structure
mkdir -p magisk_kmod/system/bin/

# Copy script
cp scripts/Kmod magisk_kmod/system/bin/

# Create module files
cat > magisk_kmod/module.prop << EOF
id=nethunter_kmod
name=Nethunter Kmod
version=v1.0
versionCode=1
author=Nethunter-X-Stone
description=Kernel mode control for Nethunter performance management
EOF

# Package and install via Magisk Manager
```

### Option 2: Custom Recovery Installation

Using TWRP or similar:

```bash
# Create flashable zip structure
mkdir -p kmod_flashable/META-INF/com/google/android/
mkdir -p kmod_flashable/system/bin/

# Copy script
cp scripts/Kmod kmod_flashable/system/bin/

# Create update script for recovery flashing
# (updater-script content would go here)
```

## Verification After Installation

### Basic Functionality Test

```bash
# Test all main functions
adb shell su -c "Kmod status"      # Should show current mode
adb shell su -c "Kmod gaming"      # Switch to gaming mode  
adb shell su -c "Kmod standard"    # Switch to standard mode
adb shell su -c "Kmod dynamic"     # Switch to dynamic mode
```

### Kernel Interface Test

```bash
# Test direct kernel interface
adb shell su -c "cat /proc/nethunter_mode"          # Read current mode
adb shell su -c "echo 'gaming' > /proc/nethunter_mode"  # Write new mode
adb shell su -c "cat /proc/nethunter_mode"          # Verify change
```

### Performance Monitoring

```bash
# Monitor CPU frequencies while switching modes
adb shell su -c "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"

# Check ZRAM status
adb shell su -c "cat /proc/swaps"

# Monitor thermal status
adb shell su -c "cat /sys/class/thermal/thermal_zone*/temp"
```

## Security Considerations

1. **File Permissions**: Always set 755 (executable by owner, readable by others)
2. **System Protection**: Remount system read-only after installation
3. **SELinux**: Be aware of security policy enforcement
4. **Root Access**: Only grant root to trusted scripts

## Cleanup (if needed)

To remove Kmod script:

```bash
# Remove from system
adb shell su -c "mount -o remount,rw /system"
adb shell su -c "rm /system/bin/Kmod"
adb shell su -c "mount -o remount,ro /system"

# Remove from alternative locations
adb shell su -c "rm /data/local/tmp/Kmod"

# Remove from sdcard
adb shell rm /sdcard/Kmod
```

## Summary

After successful installation, you'll be able to use:

```bash
# From Android terminal or via ADB:
su -c "Kmod gaming"     # 🎮 Gaming mode with overclocking
su -c "Kmod standard"   # ⚖️ Balanced performance
su -c "Kmod dynamic"    # 🧠 Intelligent scaling  
su -c "Kmod status"     # 📊 Current system status
```

The script will now be permanently available on your device and can control the kernel mode management system you built!