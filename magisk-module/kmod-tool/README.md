# Nethunter Kmod Tool - Magisk Module

A Magisk module for easy installation of the Nethunter Kmod performance control tool.

## Features

- **Gaming Mode**: Overclocked performance (1.17GHz-2.2GHz CPU, 560MHz-1.1GHz GPU, +15°C thermal)
- **Standard Mode**: Balanced performance (300MHz-1.8GHz CPU, 315MHz-840MHz GPU)
- **Dynamic Mode**: Auto-switching based on system load (300MHz-2.0GHz CPU, 315MHz-980MHz GPU)

## Requirements

- Rooted Android device with Magisk installed
- Nethunter kernel with mode management support
- Compatible hardware (typically ARM-based SoCs)

## Installation

1. Flash this module through Magisk Manager or recovery
2. Reboot your device
3. The `Kmod` command will be available system-wide

## Usage

After installation and reboot, you can use these commands:

```bash
# Check current mode and system status
su -c "Kmod status"

# Switch to gaming mode (maximum performance)
su -c "Kmod gaming"

# Switch to standard mode (balanced)
su -c "Kmod standard"

# Switch to dynamic mode (auto-switching)
su -c "Kmod dynamic"

# Show help information
su -c "Kmod help"
```

## Performance Modes Explained

### Gaming Mode
- CPU: 1.17GHz - 2.2GHz (overclocked)
- GPU: 560MHz - 1.1GHz (overclocked)
- Thermal: +15°C headroom
- ZRAM: 75% compression
- VM swappiness: 10 (less swapping)
- Cache pressure: 50 (aggressive caching)

### Standard Mode
- CPU: 300MHz - 1.8GHz
- GPU: 315MHz - 840MHz
- Thermal: Normal limits
- ZRAM: 50% compression
- VM swappiness: 60
- Cache pressure: 100

### Dynamic Mode
- CPU: 300MHz - 2.0GHz
- GPU: 315MHz - 980MHz
- Thermal: +5°C headroom
- ZRAM: 60% compression
- VM swappiness: 30
- Cache pressure: 75
- Auto-switches between standard/gaming based on system load

## Troubleshooting

### Module installs but Kmod doesn't work
- Verify Nethunter kernel is properly installed
- Check if `/proc/nethunter_mode` exists
- Ensure you're running as root when using Kmod commands

### Permission denied errors
- Make sure the module installed correctly
- Reboot after installation
- Verify Magisk is working properly

## Technical Details

- Module ID: `kmod_tool`
- Version: 1.0.0
- Installation location: `/system/bin/Kmod` (via Magisk overlay)
- Compatible with: Android 7.0+ with Magisk 20.0+

## Credits

- Nethunter-X-Stone Project
- Magisk by topjohnwu
- MMT Extended template

## License

This module is part of the Nethunter-X-Stone project.