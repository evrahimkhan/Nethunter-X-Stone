# Nethunter Kmod Tool - Magisk Module Installation Guide

## Quick Installation

1. **Download** the `Nethunter-Kmod-Tool-v1.0.0-Magisk.zip` file to your device
2. **Open Magisk Manager** on your device
3. **Tap the "Modules" tab** at the bottom
4. **Tap "Install from Storage"** (+ button)
5. **Select** the downloaded zip file
6. **Wait** for installation to complete
7. **Reboot** your device

## Alternative Installation Methods

### Method 1: Magisk Manager (Recommended)
- Easiest and safest method
- Automatic verification and installation
- Easy to manage and uninstall

### Method 2: Custom Recovery (TWRP/CWM)
1. Boot into recovery mode
2. Select "Install" or "Install ZIP"
3. Navigate to the zip file
4. Swipe to confirm flash
5. Reboot system

### Method 3: ADB Sideload
```bash
adb reboot recovery
# In recovery, select "Apply update from ADB"
adb sideload Nethunter-Kmod-Tool-v1.0.0-Magisk.zip
# Reboot system
```

## Verification

After installation and reboot, test the module:

```bash
# Check if Kmod is available
adb shell su -c "which Kmod"

# Test basic functionality
adb shell su -c "Kmod help"

# Check current status
adb shell su -c "Kmod status"
```

## Troubleshooting

### Module won't install
- Ensure Magisk is properly installed and working
- Check if you have enough storage space
- Try installing via different method

### Kmod command not found after installation
- Verify the module is enabled in Magisk Manager
- Reboot the device
- Check module logs in Magisk Manager

### Permission denied errors
- Ensure you're running commands as root (`su -c`)
- Check if SELinux is blocking execution
- Verify file permissions in module directory

## Uninstallation

### Via Magisk Manager
1. Open Magisk Manager
2. Go to "Modules" tab  
3. Find "Nethunter Kmod Tool"
4. Tap the trash/remove button
5. Reboot device

### Manual Removal
If Magisk Manager method fails:
```bash
adb shell su -c "rm -rf /data/adb/modules/kmod_tool"
# Reboot device
```

## Support

If you encounter issues:
1. Check the module logs in Magisk Manager
2. Verify Nethunter kernel is properly installed
3. Test with different performance modes
4. Check system logs with `dmesg` or `logcat`

## Compatibility

- **Android**: 7.0+ (API level 24+)
- **Magisk**: 20.0+ recommended
- **Architecture**: ARM/ARM64 (typical Android devices)
- **Kernel**: Nethunter kernel with mode management support required