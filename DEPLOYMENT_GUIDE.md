# Nethunter Kernel Mode System - Deployment Guide

## Current Status
✅ **Kernel Build**: Complete  
✅ **Modules Compiled**: All 3 modules integrated  
❌ **Device Deployment**: Not yet deployed  
❌ **Runtime Testing**: Pending device installation  

## Why "Kmod command not found"?

The `Kmod` command is not available because:
1. **Built for Android**: The command is designed to run on Android devices, not your Kali Linux host
2. **Requires Deployment**: The script needs to be installed on the target Android device
3. **Kernel Must Be Flashed**: The underlying kernel modules need to be active first

## Prerequisites for Deployment

### 1. Supported Device
- Device with unlocked bootloader
- Compatible with Nethunter-X-Stone kernel
- ADB and Fastboot access enabled

### 2. Required Tools
```bash
# Verify tools are available
which adb
which fastboot
which heimdall  # For Samsung devices (if applicable)
```

## Step-by-Step Deployment

### Phase 1: Flash the Kernel

**IMPORTANT**: ⚠️ Only proceed if you have a compatible device and recovery method ready!

```bash
# 1. Boot device to fastboot/download mode
# For most devices: Power + Volume Down
# For Samsung: Power + Volume Down + Home (or use Odin)

# 2. Flash kernel components
cd /home/kali/project/Nethunter-X-Stone

# Flash kernel image
fastboot flash boot out/arch/arm64/boot/Image

# Flash device tree
fastboot flash dtb out/arch/arm64/boot/dtb.img

# Flash device tree overlay
fastboot flash dtbo out/arch/arm64/boot/dtbo.img

# Reboot device
fastboot reboot
```

### Phase 2: Install Kmod Tool

```bash
# 1. Wait for device to boot completely
# 2. Enable USB debugging in Developer Options
# 3. Connect device and verify ADB

adb devices

# 4. Install Kmod script
adb push scripts/Kmod /sdcard/
adb shell su -c "mount -o remount,rw /system"
adb shell su -c "cp /sdcard/Kmod /system/bin/"
adb shell su -c "chmod 755 /system/bin/Kmod"
adb shell su -c "mount -o remount,ro /system"

# 5. Verify installation
adb shell su -c "which Kmod"
```

### Phase 3: Test the System

```bash
# Test kernel module loading
adb shell su -c "dmesg | grep nethunter"

# Check procfs interface
adb shell su -c "ls -la /proc/nethunter_mode"

# Test Kmod commands
adb shell su -c "Kmod status"
adb shell su -c "Kmod help"

# Test mode switching
adb shell su -c "Kmod gaming"
adb shell su -c "Kmod standard"
```

## Alternative: Local Testing (Development)

Since you don't have a device connected, here's how to verify the build locally:

### 1. Verify Build Artifacts

```bash
cd /home/kali/project/Nethunter-X-Stone

# Check kernel image
ls -la out/arch/arm64/boot/Image
file out/arch/arm64/boot/Image

# Check compiled modules
ls -la out/drivers/misc/nethunter_*
file out/drivers/misc/nethunter_modes.o

# Verify configurations
grep -E "CONFIG_NETHUNTER_(MODES|THERMAL_GPU|ZRAM_MEM)" out/.config
```

### 2. Static Analysis

```bash
# Check for compilation errors in build log
grep -i error out/build.log

# Look for nethunter module compilation
grep -n "nethunter" out/build.log

# Check symbol resolution
nm out/drivers/misc/nethunter_modes.o | head -10
```

### 3. Script Validation

```bash
# Test script syntax
bash -n scripts/Kmod
echo "Script syntax: $?"

# View script help (won't work fully without Android)
head -50 scripts/Kmod
```

## Troubleshooting

### If Device Not Detected
```bash
# Check USB connection
lsusb

# Restart ADB server
adb kill-server
adb start-server
adb devices

# Check device permissions
ls -la /dev/bus/usb/*/*
```

### If Fastboot Fails
```bash
# Check fastboot devices
fastboot devices

# Try different USB port/cable
# Ensure device is in proper fastboot mode
# Check bootloader unlock status
```

### If Kmod Install Fails
```bash
# Check root access
adb shell su -c "id"

# Check system partition mount
adb shell su -c "mount | grep system"

# Alternative installation location
adb shell su -c "cp /sdcard/Kmod /data/local/tmp/"
adb shell su -c "chmod 755 /data/local/tmp/Kmod"
adb shell su -c "PATH=/data/local/tmp:$PATH Kmod status"
```

## Device Compatibility Check

Before flashing, ensure your device is compatible:

```bash
# Check device model
adb shell getprop ro.product.model
adb shell getprop ro.build.product

# Check current kernel
adb shell uname -a

# Check architecture
adb shell getprop ro.product.cpu.abi
```

## Safe Recovery Options

**Before flashing, ensure you have**:
1. Stock firmware for your device
2. Working custom recovery (TWRP/CWM)
3. Backup of current boot partition
4. Knowledge of device-specific recovery methods

## Next Steps

1. **Connect Device**: Connect your Android device with USB debugging
2. **Backup Current Kernel**: Save current boot partition
3. **Flash Kernel**: Deploy the built kernel carefully
4. **Install Kmod**: Deploy the control script
5. **Test Features**: Verify all modes work correctly

## Expected Results After Deployment

Once deployed successfully, you should be able to:

```bash
# On Android device terminal or via ADB:
su -c "Kmod gaming"     # Enable gaming mode
su -c "Kmod standard"   # Standard mode
su -c "Kmod dynamic"    # Dynamic mode
su -c "Kmod status"     # Check current mode

# Direct kernel interface:
echo "gaming" > /proc/nethunter_mode
cat /proc/nethunter_mode
```

---

**The kernel is ready - deployment to Android device required for testing!**