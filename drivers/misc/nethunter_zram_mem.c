/*
 * Nethunter ZRAM and Memory Management Extensions
 * 
 * ANDROID: Enhanced ZRAM configuration and memory management for Nethunter modes
 * 
 * This module provides advanced ZRAM configuration and memory management
 * optimizations for the Nethunter mode management system.
 * 
 * Copyright (C) 2025 Nethunter-X-Stone Project
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/mm.h>
#include <linux/swap.h>
#include <linux/sysctl.h>
#include <linux/vmstat.h>
#include <linux/compaction.h>
#include <linux/oom.h>
#include <linux/memcontrol.h>
#include <linux/writeback.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/mmzone.h>
#include <linux/gfp.h>

/* ZRAM device paths */
#define ZRAM0_DEVICE_PATH "/dev/block/zram0"
#define ZRAM_COMP_ALGORITHM_PATH "/sys/block/zram0/comp_algorithm"
#define ZRAM_DISKSIZE_PATH "/sys/block/zram0/disksize"
#define ZRAM_MAX_COMP_STREAMS_PATH "/sys/block/zram0/max_comp_streams"
#define ZRAM_STATS_PATH "/sys/block/zram0/stat"
#define ZRAM_RESET_PATH "/sys/block/zram0/reset"

/* Memory tunables paths */
#define VM_SWAPPINESS_PATH "/proc/sys/vm/swappiness"
#define VM_VFS_CACHE_PRESSURE_PATH "/proc/sys/vm/vfs_cache_pressure"
#define VM_DIRTY_RATIO_PATH "/proc/sys/vm/dirty_ratio"
#define VM_DIRTY_BG_RATIO_PATH "/proc/sys/vm/dirty_background_ratio"
#define VM_OVERCOMMIT_RATIO_PATH "/proc/sys/vm/overcommit_ratio"
#define VM_MIN_FREE_KBYTES_PATH "/proc/sys/vm/min_free_kbytes"
#define VM_EXTRA_FREE_KBYTES_PATH "/proc/sys/vm/extra_free_kbytes"

struct memory_profile {
	unsigned int swappiness;
	unsigned int vfs_cache_pressure;
	unsigned int dirty_ratio;
	unsigned int dirty_background_ratio;
	unsigned int overcommit_ratio;
	unsigned int min_free_kbytes;
	unsigned int extra_free_kbytes;
	unsigned int zram_comp_ratio;
	const char *zram_algorithm;
	unsigned int max_comp_streams;
};

/* Memory profiles for different modes */
static struct memory_profile memory_profiles[] = {
	/* Standard mode */
	{
		.swappiness = 60,
		.vfs_cache_pressure = 100,
		.dirty_ratio = 20,
		.dirty_background_ratio = 10,
		.overcommit_ratio = 50,
		.min_free_kbytes = 0,        /* Will be calculated */
		.extra_free_kbytes = 0,      /* Will be calculated */
		.zram_comp_ratio = 50,
		.zram_algorithm = "lz4",
		.max_comp_streams = 2,
	},
	/* Gaming mode */
	{
		.swappiness = 10,
		.vfs_cache_pressure = 50,
		.dirty_ratio = 30,
		.dirty_background_ratio = 5,
		.overcommit_ratio = 80,
		.min_free_kbytes = 0,        /* Will be calculated */
		.extra_free_kbytes = 0,      /* Will be calculated */
		.zram_comp_ratio = 75,
		.zram_algorithm = "lzo-rle", /* Better compression for gaming */
		.max_comp_streams = 4,
	},
	/* Dynamic mode */
	{
		.swappiness = 30,
		.vfs_cache_pressure = 75,
		.dirty_ratio = 25,
		.dirty_background_ratio = 8,
		.overcommit_ratio = 65,
		.min_free_kbytes = 0,        /* Will be calculated */
		.extra_free_kbytes = 0,      /* Will be calculated */
		.zram_comp_ratio = 60,
		.zram_algorithm = "lz4",
		.max_comp_streams = 3,
	}
};

static struct memory_profile original_profile;
static bool profile_applied = false;
static unsigned long total_memory_kb = 0;

/*
 * Helper function to write to sysfs/procfs
 */
static int write_sys_file(const char *path, const char *value)
{
	struct file *f;
	loff_t pos = 0;
	int ret;
	mm_segment_t old_fs;

	f = filp_open(path, O_WRONLY, 0);
	if (IS_ERR(f)) {
		pr_debug("nethunter_zram_mem: Failed to open %s: %ld\n", 
		         path, PTR_ERR(f));
		return PTR_ERR(f);
	}

	old_fs = get_fs();
	set_fs(KERNEL_DS);
	ret = kernel_write(f, value, strlen(value), &pos);
	set_fs(old_fs);

	filp_close(f, NULL);

	if (ret < 0) {
		pr_err("nethunter_zram_mem: Failed to write to %s: %d\n", 
		       path, ret);
		return ret;
	}

	return 0;
}

/*
 * Helper function to read from sysfs/procfs
 */
static int read_sys_file(const char *path, char *buffer, size_t size)
{
	struct file *f;
	loff_t pos = 0;
	int ret;
	mm_segment_t old_fs;

	f = filp_open(path, O_RDONLY, 0);
	if (IS_ERR(f)) {
		pr_debug("nethunter_zram_mem: Failed to open %s: %ld\n", 
		         path, PTR_ERR(f));
		return PTR_ERR(f);
	}

	old_fs = get_fs();
	set_fs(KERNEL_DS);
	ret = kernel_read(f, buffer, size - 1, &pos);
	set_fs(old_fs);

	filp_close(f, NULL);

	if (ret > 0) {
		buffer[ret] = '\0';
		/* Remove trailing newline */
		if (ret > 0 && buffer[ret - 1] == '\n')
			buffer[ret - 1] = '\0';
	}

	return ret;
}

/*
 * Calculate optimal memory settings based on total RAM
 */
static void calculate_memory_settings(struct memory_profile *profile)
{
	unsigned long total_pages = totalram_pages();
	unsigned long total_kb = total_pages << (PAGE_SHIFT - 10);
	
	total_memory_kb = total_kb;

	/* Calculate min_free_kbytes as percentage of total memory */
	if (profile == &memory_profiles[0]) {
		/* Standard: 1% of RAM */
		profile->min_free_kbytes = total_kb / 100;
		profile->extra_free_kbytes = total_kb / 200;
	} else if (profile == &memory_profiles[1]) {
		/* Gaming: 2% of RAM for better performance */
		profile->min_free_kbytes = total_kb / 50;
		profile->extra_free_kbytes = total_kb / 100;
	} else {
		/* Dynamic: 1.5% of RAM */
		profile->min_free_kbytes = (total_kb * 15) / 1000;
		profile->extra_free_kbytes = (total_kb * 75) / 10000;
	}

	/* Ensure reasonable bounds */
	if (profile->min_free_kbytes < 16384)
		profile->min_free_kbytes = 16384;  /* At least 16MB */
	if (profile->min_free_kbytes > 524288)
		profile->min_free_kbytes = 524288; /* At most 512MB */

	if (profile->extra_free_kbytes < 8192)
		profile->extra_free_kbytes = 8192;  /* At least 8MB */
	if (profile->extra_free_kbytes > 262144)
		profile->extra_free_kbytes = 262144; /* At most 256MB */

	pr_info("nethunter_zram_mem: Total RAM: %lu KB, calculated min_free: %u KB, extra_free: %u KB\n",
		total_kb, profile->min_free_kbytes, profile->extra_free_kbytes);
}

/*
 * Save current memory settings
 */
static int save_original_profile(void)
{
	char buffer[64];
	int ret;

	/* Save VM settings */
	original_profile.swappiness = vm_swappiness;
	original_profile.vfs_cache_pressure = sysctl_vfs_cache_pressure;
	original_profile.dirty_ratio = vm_dirty_ratio;
	original_profile.dirty_background_ratio = dirty_background_ratio;
	original_profile.overcommit_ratio = sysctl_overcommit_ratio;

	/* Read min_free_kbytes */
	ret = read_sys_file(VM_MIN_FREE_KBYTES_PATH, buffer, sizeof(buffer));
	if (ret > 0) {
		ret = kstrtouint(buffer, 10, &original_profile.min_free_kbytes);
		if (ret)
			original_profile.min_free_kbytes = 16384;
	} else {
		original_profile.min_free_kbytes = 16384;
	}

	/* Read extra_free_kbytes */
	ret = read_sys_file(VM_EXTRA_FREE_KBYTES_PATH, buffer, sizeof(buffer));
	if (ret > 0) {
		ret = kstrtouint(buffer, 10, &original_profile.extra_free_kbytes);
		if (ret)
			original_profile.extra_free_kbytes = 8192;
	} else {
		original_profile.extra_free_kbytes = 8192;
	}

	pr_info("nethunter_zram_mem: Saved original memory profile\n");
	return 0;
}

/*
 * Configure ZRAM device
 */
static int configure_zram_device(struct memory_profile *profile)
{
	char value_str[64];
	unsigned long zram_size;
	int ret;

	/* Calculate ZRAM size based on total memory and compression ratio */
	zram_size = (total_memory_kb * profile->zram_comp_ratio) / 100;
	zram_size *= 1024; /* Convert to bytes */

	pr_info("nethunter_zram_mem: Configuring ZRAM: size=%lu bytes, algorithm=%s, streams=%u\n",
		zram_size, profile->zram_algorithm, profile->max_comp_streams);

	/* Reset ZRAM device first (this may fail if not initialized) */
	write_sys_file(ZRAM_RESET_PATH, "1");

	/* Set compression algorithm */
	ret = write_sys_file(ZRAM_COMP_ALGORITHM_PATH, profile->zram_algorithm);
	if (ret) {
		pr_warn("nethunter_zram_mem: Failed to set ZRAM algorithm, using default\n");
	}

	/* Set max compression streams */
	snprintf(value_str, sizeof(value_str), "%u", profile->max_comp_streams);
	ret = write_sys_file(ZRAM_MAX_COMP_STREAMS_PATH, value_str);
	if (ret) {
		pr_warn("nethunter_zram_mem: Failed to set ZRAM compression streams\n");
	}

	/* Set disk size */
	snprintf(value_str, sizeof(value_str), "%lu", zram_size);
	ret = write_sys_file(ZRAM_DISKSIZE_PATH, value_str);
	if (ret) {
		pr_err("nethunter_zram_mem: Failed to set ZRAM disk size\n");
		return ret;
	}

	pr_info("nethunter_zram_mem: ZRAM configured successfully\n");
	return 0;
}

/*
 * Apply memory profile
 */
int nethunter_apply_memory_profile(int mode)
{
	struct memory_profile *profile;
	char value_str[32];
	int ret = 0;

	if (mode < 0 || mode >= ARRAY_SIZE(memory_profiles)) {
		pr_err("nethunter_zram_mem: Invalid memory profile mode %d\n", mode);
		return -EINVAL;
	}

	profile = &memory_profiles[mode];

	/* Save original profile if not done yet */
	if (!profile_applied) {
		save_original_profile();
		profile_applied = true;
	}

	/* Calculate memory settings based on system RAM */
	calculate_memory_settings(profile);

	pr_info("nethunter_zram_mem: Applying memory profile for mode %d\n", mode);

	/* Apply VM settings */
	vm_swappiness = profile->swappiness;
	sysctl_vfs_cache_pressure = profile->vfs_cache_pressure;
	vm_dirty_ratio = profile->dirty_ratio;
	dirty_background_ratio = profile->dirty_background_ratio;
	sysctl_overcommit_ratio = profile->overcommit_ratio;

	/* Apply min_free_kbytes */
	snprintf(value_str, sizeof(value_str), "%u", profile->min_free_kbytes);
	ret = write_sys_file(VM_MIN_FREE_KBYTES_PATH, value_str);
	if (ret) {
		pr_warn("nethunter_zram_mem: Failed to set min_free_kbytes\n");
	}

	/* Apply extra_free_kbytes */
	snprintf(value_str, sizeof(value_str), "%u", profile->extra_free_kbytes);
	ret = write_sys_file(VM_EXTRA_FREE_KBYTES_PATH, value_str);
	if (ret) {
		pr_warn("nethunter_zram_mem: Failed to set extra_free_kbytes\n");
	}

	/* Configure ZRAM */
	ret = configure_zram_device(profile);
	if (ret) {
		pr_err("nethunter_zram_mem: Failed to configure ZRAM device\n");
		/* Don't fail completely if ZRAM configuration fails */
	}

	/* Trigger memory compaction for better performance */
	if (mode == 1) { /* Gaming mode */
		pr_info("nethunter_zram_mem: Gaming mode - memory compaction requested\n");
		/* Note: Direct memory compaction calls require different API in this kernel */
	}

	pr_info("nethunter_zram_mem: Applied memory profile for mode %d\n", mode);
	pr_info("nethunter_zram_mem: swappiness=%u, cache_pressure=%u, dirty_ratio=%u\n",
		profile->swappiness, profile->vfs_cache_pressure, profile->dirty_ratio);

	return 0;
}
EXPORT_SYMBOL(nethunter_apply_memory_profile);

/*
 * Reset to original memory settings
 */
int nethunter_reset_memory_profile(void)
{
	char value_str[32];
	int ret = 0;

	if (!profile_applied) {
		pr_info("nethunter_zram_mem: No memory profile to reset\n");
		return 0;
	}

	pr_info("nethunter_zram_mem: Resetting to original memory profile\n");

	/* Restore VM settings */
	vm_swappiness = original_profile.swappiness;
	sysctl_vfs_cache_pressure = original_profile.vfs_cache_pressure;
	vm_dirty_ratio = original_profile.dirty_ratio;
	dirty_background_ratio = original_profile.dirty_background_ratio;
	sysctl_overcommit_ratio = original_profile.overcommit_ratio;

	/* Restore min_free_kbytes */
	snprintf(value_str, sizeof(value_str), "%u", original_profile.min_free_kbytes);
	ret = write_sys_file(VM_MIN_FREE_KBYTES_PATH, value_str);
	if (ret) {
		pr_warn("nethunter_zram_mem: Failed to restore min_free_kbytes\n");
	}

	/* Restore extra_free_kbytes */
	snprintf(value_str, sizeof(value_str), "%u", original_profile.extra_free_kbytes);
	ret = write_sys_file(VM_EXTRA_FREE_KBYTES_PATH, value_str);
	if (ret) {
		pr_warn("nethunter_zram_mem: Failed to restore extra_free_kbytes\n");
	}

	/* Reset ZRAM device */
	write_sys_file(ZRAM_RESET_PATH, "1");

	pr_info("nethunter_zram_mem: Reset to original memory profile\n");
	return 0;
}
EXPORT_SYMBOL(nethunter_reset_memory_profile);

/*
 * Get current memory statistics
 */
int nethunter_get_memory_stats(unsigned long *free_kb, unsigned long *available_kb,
			       unsigned long *zram_used_kb, unsigned long *zram_total_kb)
{
	struct sysinfo si;
	char buffer[256];
	int ret;

	si_meminfo(&si);

	if (free_kb)
		*free_kb = si.freeram << (PAGE_SHIFT - 10);
	
	if (available_kb) {
		/* This is an approximation */
		*available_kb = si_mem_available() << (PAGE_SHIFT - 10);
	}

	/* Read ZRAM stats if requested */
	if (zram_used_kb || zram_total_kb) {
		ret = read_sys_file(ZRAM_STATS_PATH, buffer, sizeof(buffer));
		if (ret > 0) {
			/* Parse ZRAM stats - this is a simplified version */
			if (zram_used_kb)
				*zram_used_kb = 0; /* Would need proper parsing */
			if (zram_total_kb)
				*zram_total_kb = 0; /* Would need proper parsing */
		} else {
			if (zram_used_kb)
				*zram_used_kb = 0;
			if (zram_total_kb)
				*zram_total_kb = 0;
		}
	}

	return 0;
}
EXPORT_SYMBOL(nethunter_get_memory_stats);

/*
 * Force memory cleanup for gaming mode
 */
int nethunter_force_memory_cleanup(void)
{
	pr_info("nethunter_zram_mem: Memory cleanup requested\n");

	/* Note: Direct memory management calls require different API in this kernel */
	/* For now, just log the operation */
	pr_info("nethunter_zram_mem: Memory cleanup would be performed here\n");
	return 0;
}
EXPORT_SYMBOL(nethunter_force_memory_cleanup);

/*
 * Module initialization
 */
static int __init nethunter_zram_mem_init(void)
{
	pr_info("nethunter_zram_mem: Initializing ZRAM and memory management\n");

	/* Get total system memory */
	total_memory_kb = totalram_pages() << (PAGE_SHIFT - 10);
	
	pr_info("nethunter_zram_mem: System memory: %lu KB\n", total_memory_kb);
	pr_info("nethunter_zram_mem: Module loaded successfully\n");

	return 0;
}

/*
 * Module cleanup
 */
static void __exit nethunter_zram_mem_exit(void)
{
	pr_info("nethunter_zram_mem: Cleaning up ZRAM and memory management\n");

	/* Reset to original memory profile */
	nethunter_reset_memory_profile();

	pr_info("nethunter_zram_mem: Module unloaded\n");
}

module_init(nethunter_zram_mem_init);
module_exit(nethunter_zram_mem_exit);

MODULE_AUTHOR("Nethunter-X-Stone Project");
MODULE_DESCRIPTION("Nethunter ZRAM and Memory Management Extensions");
MODULE_LICENSE("GPL v2");
MODULE_VERSION("1.0");