##########################################################################################
#
# Magisk Module Installer Script
#
##########################################################################################
##########################################################################################
#
# Instructions:
#
# 1. Place your files into system folder (delete the placeholder file)
# 2. Fill in your module's info into module.prop
# 3. Configure and implement callbacks in this file
# 4. If you need boot scripts, add them into common/post-fs-data.sh or common/service.sh
# 5. Add other or modify other necessary files in this module
#
##########################################################################################

##########################################################################################
# Config Flags
##########################################################################################

# Set to true if you do *NOT* want Magisk to mount
# any files for you. Most modules would want to leave this as false
SKIPMOUNT=false

# Set to true if you need to load system.prop
PROPFILE=false

# Set to true if you need post-fs-data script
POSTFSDATA=false

# Set to true if you need late_start service script
LATESTARTSERVICE=false

##########################################################################################
# Replace list
##########################################################################################

# List all directories you want to directly replace in the system
# Check the documentations for more info why you would need this

# Construct your list in the following format
# This is an example
REPLACE_EXAMPLE="
/system/app/Youtube
/system/priv-app/SystemUI
/system/priv-app/Settings
/system/framework
"

# Construct your own list here
REPLACE="
"

##########################################################################################
# Function Callbacks
##########################################################################################

# The following functions will be called by the Magisk module installer framework.
# You do not have the ability to modify update-binary, the only way you can customize
# installation is through implementing these functions.
#
# When running your callbacks, the installation framework will make sure the following
# variables are properly defined:
#
# $MAGISK_VER (string): the version string of current installed Magisk
# $MAGISK_VER_CODE (int): the version code of current installed Magisk
# $BOOTMODE (bool): true if the module is currently being installed in Magisk Manager
# $MODPATH (path): the path where your module files should be installed
# $TMPDIR (path): a place where you can temporarily store files
# $ZIPFILE (path): your module's installation zip
# $ARCH (string): the architecture of the device. Value is either arm, arm64, x86, or x64
# $IS64BIT (bool): true if $ARCH is either arm64 or x64
#
##########################################################################################

print_modname() {
  ui_print "*******************************"
  ui_print "     Nethunter Kmod Tool      "
  ui_print "*******************************"
  ui_print " "
  ui_print "  Performance Mode Control Tool"
  ui_print "  for Nethunter Kernel         "
  ui_print " "
  ui_print "  Features:"
  ui_print "  • Gaming Mode (Overclocked)"
  ui_print "  • Standard Mode (Balanced)"
  ui_print "  • Dynamic Mode (Auto-switch)"
  ui_print " "
  ui_print "*******************************"
}

on_install() {
  ui_print "- Extracting module files"
  unzip -o "$ZIPFILE" 'system/*' -d $MODPATH >&2
  
  ui_print "- Setting permissions"
  set_perm_recursive $MODPATH/system/bin 0 0 0755 0755
  
  ui_print "- Checking for Nethunter kernel"
  if [ -f "/proc/nethunter_mode" ]; then
    ui_print "✓ Nethunter kernel detected"
    ui_print "✓ Mode management available"
  else
    ui_print "⚠ Nethunter kernel not detected"
    ui_print "⚠ Please flash Nethunter kernel first"
    ui_print "⚠ Module will still install but may not function"
  fi
  
  ui_print " "
  ui_print "Installation complete!"
  ui_print " "
  ui_print "Usage after reboot:"
  ui_print "  su -c 'Kmod status'    # Check current mode"
  ui_print "  su -c 'Kmod gaming'    # Enable gaming mode"
  ui_print "  su -c 'Kmod standard'  # Enable standard mode"
  ui_print "  su -c 'Kmod dynamic'   # Enable dynamic mode"
  ui_print " "
}

set_permissions() {
  # The following is the default rule, DO NOT remove
  set_perm_recursive $MODPATH 0 0 0755 0644
  
  # Set execute permissions for Kmod
  set_perm $MODPATH/system/bin/Kmod 0 0 0755
}
