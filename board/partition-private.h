/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Board geometry transcribed from owner-inspected stock GPT; hardware facts, not copied vendor implementation. */
/*
 * Geometry of the "misc" partition on DBY-W09, read from the stock GPT
 * (HarmonyOS 4.2.0.213). Verify against your own device before use.
 * U-Boot only clears the command field after reading it back and checking
 * that it is "boot-recovery"; a wrong location fails the check and writes nothing.
 */
#define MISC_LUN 0ULL
#define MISC_START 9480ULL
#define MISC_BLOCKS 512ULL
#define MISC_BLKSZ 4096ULL
