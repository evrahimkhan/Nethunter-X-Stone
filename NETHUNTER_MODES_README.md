# Nethunter Kernel Mode Management System

## Overview

The Nethunter Mode Management System provides comprehensive performance control for the Nethunter-X-Stone kernel with three distinct operational modes designed for different use cases.

## Features

- **Three Performance Modes**: Standard, Gaming, and Dynamic
- **CPU Frequency Scaling**: 300MHz - 2.2GHz range with mode-specific limits
- **GPU Frequency Control**: 315MHz - 1.1GHz with overclocking support
- **Thermal Management**: Configurable thermal limits with +15°C headroom for gaming
- **Memory Optimization**: Dynamic ZRAM configuration and memory management tuning
- **Auto-Switching**: Dynamic mode with intelligent load-based switching
- **User-Friendly Control**: Command-line tool and /proc interface

## Performance Modes

### 1. Standard Mode (Default)
- **CPU**: 300MHz - 1.8GHz
- **GPU**: 315MHz - 840MHz  
- **Thermal**: Normal limits
- **Memory**: Balanced settings (50% ZRAM compression, 60 swappiness)
- **Use Case**: Daily usage, balanced power consumption

### 2. Gaming Mode
- **CPU**: 1.17GHz - 2.2GHz (overclocked)
- **GPU**: 560MHz - 1.1GHz (overclocked)
- **Thermal**: +15°C headroom for sustained performance
- **Memory**: Optimized for gaming (75% ZRAM compression, 10 swappiness)
- **Use Case**: Gaming, benchmarks, maximum performance

### 3. Dynamic Mode
- **CPU**: 300MHz - 2.0GHz (adaptive)
- **GPU**: 315MHz - 980MHz (adaptive)
- **Thermal**: +5°C moderate headroom
- **Memory**: Balanced adaptive settings (60% ZRAM compression, 30 swappiness)
- **Use Case**: Automatic switching based on system load

## Installation

### 1. Build Configuration
The system is enabled by default in `nethunter_defconfig`. Ensure these options are set:
```
CONFIG_NETHUNTER_MODES=y
CONFIG_NETHUNTER_THERMAL_GPU=y
CONFIG_NETHUNTER_ZRAM_MEM=y
```

### 2. Build the Kernel
```bash
# Use the provided test script
./test_nethunter_modes.sh build

# Or manually:
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-android-
make O=out nethunter_defconfig
make O=out -j$(nproc)
```

### 3. Flash Kernel
Flash the built kernel to your device using your preferred method (fastboot, custom recovery, etc.).

### 4. Install Command Tool
Copy the `Kmod` script to your device:
```bash
adb push scripts/Kmod /system/bin/
adb shell chmod 755 /system/bin/Kmod
```

## Usage

### Command Line Interface
The primary interface is the `Kmod` command-line tool:

```bash
# Switch to gaming mode
su -c "Kmod gaming"

# Switch to standard mode  
su -c "Kmod standard"

# Switch to dynamic mode
su -c "Kmod dynamic"

# Show current status and system info
su -c "Kmod status"

# Show help
su -c "Kmod help"

# Enable/disable the system
su -c "Kmod enable"
su -c "Kmod disable"
```

### Direct /proc Interface
You can also control modes directly via the proc filesystem:
```bash
# Check current mode
cat /proc/nethunter_mode

# Switch modes (as root)
echo "gaming" > /proc/nethunter_mode
echo "standard" > /proc/nethunter_mode
echo "dynamic" > /proc/nethunter_mode
echo "0" > /proc/nethunter_mode  # Standard (numeric)
echo "1" > /proc/nethunter_mode  # Gaming (numeric)
echo "2" > /proc/nethunter_mode  # Dynamic (numeric)
```

## Monitoring

### System Status
```bash
# Show detailed status
su -c "Kmod status"

# Monitor kernel messages
dmesg | grep nethunter

# Check CPU frequency
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq

# Check GPU frequency  
cat /sys/class/devfreq/*/cur_freq

# Check thermal zones
cat /sys/class/thermal/thermal_zone*/temp

# Check memory info
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable)"

# Check ZRAM status
cat /sys/block/zram0/disksize
```

### Performance Monitoring
```bash
# Monitor load average
cat /proc/loadavg

# Monitor CPU usage
top -n 1 | grep "CPU:"

# Check active frequency governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

## Dynamic Mode Behavior

Dynamic mode automatically switches between standard and gaming performance based on system load:

- **High Load (>80% CPU)**: Switches to gaming performance profile
- **Low Load (<20% CPU)**: Switches to standard performance profile
- **Moderate Load (20-80%)**: Maintains current profile
- **Check Interval**: Every 5 seconds
- **Thermal Safety**: Monitors temperatures and adjusts if needed

## Troubleshooting

### Module Not Loading
```bash
# Check if modules are present in kernel
zcat /proc/config.gz | grep NETHUNTER

# Check kernel messages for errors
dmesg | grep -E "(nethunter|error|fail)"

# Verify /proc interface exists
ls -la /proc/nethunter_mode
```

### Mode Switching Issues
```bash
# Check current mode and status
su -c "Kmod status"

# Try manual mode switch with verbose output
echo "gaming" > /proc/nethunter_mode
dmesg | tail -20

# Check if system is disabled
echo "enable" > /proc/nethunter_mode
```

### Performance Issues
```bash
# Verify frequency scaling is working
watch -n 1 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq'

# Check thermal throttling
cat /sys/class/thermal/thermal_zone*/temp
cat /sys/class/thermal/thermal_zone*/trip_point_*_temp

# Monitor memory usage
cat /proc/meminfo | grep -E "(MemTotal|MemFree|Cached|SwapTotal|SwapFree)"
```

## Development and Testing

### Build Testing
```bash
# Run complete test suite
./test_nethunter_modes.sh all

# Test individual components
./test_nethunter_modes.sh check    # Environment check
./test_nethunter_modes.sh test     # Implementation test
./test_nethunter_modes.sh report   # Generate report
```

### Code Structure
- `drivers/misc/nethunter_modes.c` - Core mode management
- `drivers/misc/nethunter_thermal_gpu.c` - Thermal and GPU control
- `drivers/misc/nethunter_zram_mem.c` - Memory and ZRAM management
- `scripts/Kmod` - User command-line interface
- `drivers/misc/Kconfig` - Configuration options
- `arch/arm64/configs/nethunter_defconfig` - Default configuration

## Safety Considerations

- **Thermal Management**: Gaming mode increases thermal limits. Monitor temperatures to prevent overheating
- **Power Consumption**: Gaming mode significantly increases power draw
- **Battery Life**: Extended gaming mode usage will reduce battery life
- **Stability**: Overclocking may cause instability on some devices
- **Default Safety**: System defaults to standard mode on boot

## Compatibility

- **Kernel Version**: Designed for Android kernel trees
- **Architecture**: ARM64 (aarch64)
- **SoC Support**: Primarily Qualcomm Snapdragon with KGSL GPU
- **Android Version**: Compatible with Android kernel requirements
- **Root Required**: Yes, for mode switching

## Contributing

Follow Android kernel patch format with proper tags:
- Use `ANDROID:` prefix for Android-specific features
- Include `Signed-off-by:` tag
- Add `Change-Id:` for Gerrit integration
- Test thoroughly before submission

## License

GPL v2 - Same as Linux kernel

## Support

Check kernel logs with `dmesg | grep nethunter` for debugging information.