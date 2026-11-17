#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run actual misc-clear C against RAM-backed storage and counted I/O stubs.
Usage: test-misc-clear.py PREPARED_SOURCE OUTPUT_DIR
"""
from pathlib import Path
import subprocess
import sys

src = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
work.mkdir(parents=True, exist_ok=True)
(work / 'misc-partition-private.h').write_bytes((src / 'include/misc-partition-private.h').read_bytes())
source = (src / 'cmd/misc-clear.c').read_text()
source = source[source.index('enum permission'):source.index('static int do_miscclear')]
source = source.replace('#ifndef DBY_MISC_HOST_TEST\n', '')
head = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <misc-partition-private.h>
typedef uint64_t lbaint_t;
typedef uint32_t u32;
#define UCLASS_SCSI 1
#define UCLASS_BLK 2
#define DMA_TO_DEVICE 1
#define DMA_NONE 0
#define ARCH_DMA_MINALIGN 64
struct blk_desc { int uclass_id, target, lun; unsigned int blksz; };
struct udevice { struct udevice *parent; struct blk_desc desc; };
struct disk_partition { lbaint_t start, size; unsigned int blksz; };
struct scsi_cmd { unsigned char cmd[16]; int target, lun, cmdlen;
                 void *pdata; unsigned int datalen; int dma_dir; };
static struct udevice controller, block;
static unsigned char disk[MISC_BLKSZ], original[MISC_BLKSZ];
static int scenario, reads, writes, syncs, scans, probes, diag_calls;
static const char *diag_result, *diag_reason;
static int diag_rc;
static void *dev_get_uclass_plat(struct udevice *d) { return &d->desc; }
static int console_assign(FILE *stream, const char *name) { return 0; }
static int ufs_probe_dev(int n) { assert(n == 0); probes++; return 0; }
static int uclass_find_first_device(int cls, struct udevice **d) {
 *d = cls == UCLASS_SCSI ? &controller : &block; return 0;
}
static int uclass_find_next_device(struct udevice **d) { *d = NULL; return 0; }
static int scsi_scan_dev(struct udevice *d, bool verbose) {
 assert(d == &controller && !verbose); scans++; return 0;
}
static int part_get_info_by_name(struct blk_desc *d, const char *name,
                                 struct disk_partition *p) {
 assert(d == &block.desc && !strcmp(name, "misc"));
 *p = (struct disk_partition){MISC_START, MISC_BLOCKS, MISC_BLKSZ};
 if (scenario == 7) p->start++;
 return 1;
}
static void *memalign(size_t alignment, size_t bytes) { return malloc(bytes); }
static long blk_read(struct udevice *d, lbaint_t start, lbaint_t count, void *buf) {
 assert(d == &block && start == MISC_START && count == 1); reads++;
 if (scenario == 8) return -EIO;
 memcpy(buf, disk, sizeof(disk));
 if (scenario == 11 && reads == 2) ((unsigned char *)buf)[40] ^= 1;
 return 1;
}
static long blk_write(struct udevice *, lbaint_t, lbaint_t, const void *);
int misc_scsi_sync(struct udevice *);
static void exp_diag_misc(const char *result, const char *reason, int rc) {
 diag_result = result; diag_reason = reason; diag_rc = rc; diag_calls++;
 printf("MISC %s (%s; rc=%d)\n", result, reason, rc);
}
'''
post = r'''
static struct scsi_cmd cdb(unsigned char op) {
 struct scsi_cmd c = {.cmdlen=10, .target=0, .lun=MISC_LUN};
 c.cmd[0]=op; c.cmd[2]=(MISC_START>>24)&255; c.cmd[3]=(MISC_START>>16)&255;
 c.cmd[4]=(MISC_START>>8)&255; c.cmd[5]=MISC_START&255; c.cmd[8]=1;
 return c;
}
static long blk_write(struct udevice *d, lbaint_t start, lbaint_t count,
                      const void *buf) {
 struct scsi_cmd c = cdb(0x2a); writes++;
 assert(!misc_block_gate(d,start,count,buf));
 assert(!misc_scsi_gate(d,start,count,buf));
 c.cmd[1]=8; c.pdata=(void *)buf; c.datalen=MISC_BLKSZ; c.dma_dir=DMA_TO_DEVICE;
 assert(!misc_transport_gate(&controller,&c));
 if (scenario == 9) return -EIO;
 memcpy(disk,buf,sizeof(disk)); return 1;
}
int misc_scsi_sync(struct udevice *d) {
 struct scsi_cmd c = cdb(0x35); syncs++; assert(d == &block);
 assert(!misc_transport_gate(&controller,&c));
 return scenario == 10 ? -EIO : 0;
}
int main(int argc, char **argv) {
 assert(argc == 2 || argc == 3); scenario=atoi(argv[1]);
 block.parent=&controller;
 block.desc=(struct blk_desc){UCLASS_SCSI,0,MISC_LUN,MISC_BLKSZ};
 memset(disk,0xa5,sizeof(disk)); memset(disk,0,32);
 if (scenario == 1) { /* all-zero command; nonzero remainder must survive */ }
 else if (scenario == 2) { assert(argc == 3); disk[atoi(argv[2])]=1; }
 else if (scenario == 3) memset(disk,0xff,32);
 else {
  memcpy(disk,"boot-recovery",14);
  if (scenario == 0) memset(disk+14,0xcc,18); /* existing C-string policy */
  if (scenario == 4) disk[13]='x';
  if (scenario == 5) disk[12]=0;
 }
 if (scenario == 6) block.desc.blksz=512;
 memcpy(original,disk,sizeof(disk));
 int rc=dby_clear_misc();
 assert(permission==CLOSED && !bound && !payload);
 assert(probes==1 && scans==1 && diag_calls==1 && diag_rc==rc);
 if (scenario == 0 || scenario == 12) {
  assert(rc==0 && spent && writes==1 && syncs==1 && reads==2);
  assert(!strcmp(diag_result,"CLEARED OK"));
  assert(no_command(disk) && !memcmp(disk+32,original+32,MISC_BLKSZ-32));
 } else if (scenario == 1) {
  assert(rc==0 && !spent && writes==0 && syncs==0 && reads==1);
  assert(!strcmp(diag_result,"NO COMMAND") && !memcmp(disk,original,sizeof(disk)));
 } else if (scenario >= 2 && scenario <= 8) {
  assert(rc==(scenario==8 ? -EIO : -EINVAL) && !spent && !writes && !syncs);
  assert(reads==(scenario==6 || scenario==7 ? 0 : 1));
  assert(!memcmp(disk,original,sizeof(disk)));
 } else {
  assert(rc==-EIO && spent && writes==1);
  assert(syncs==(scenario==9 ? 0 : 1));
  assert(reads==(scenario==11 ? 2 : 1));
 }
 assert(show_command==(scenario>=2 && scenario<=5));
 if (show_command) assert(!memcmp(rejected_command,original,32));
 int old_reads=reads, old_writes=writes, old_syncs=syncs;
 dby_misc_print_status();
 assert(diag_calls==2 && reads==old_reads && writes==old_writes && syncs==old_syncs);
 assert(dby_clear_misc()==-EPERM); /* repeat invocation never retries I/O */
 assert(reads==old_reads && writes==old_writes && syncs==old_syncs);
 assert(misc_block_gate(&block,MISC_START,1,disk)==-EROFS);
 assert(misc_scsi_gate(&block,MISC_START,1,disk)==-EROFS);
 assert(arm_sync()==-EROFS && permission==CLOSED);
 puts("PASS misc flow");
}
'''
(work / 'test.c').write_text(head + source + post)
binary = work / 'test'
subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Wno-unused-parameter',
                '-I' + str(work), str(work / 'test.c'), '-o', str(binary)], check=True)
cases = [(n,) for n in range(13) if n != 2] + [(2, i) for i in range(32)]
for args in cases:
    result = subprocess.run([str(binary), *map(str, args)], capture_output=True, text=True, check=True)
    hex_lines = [line for line in result.stdout.splitlines() if line.startswith('MISC command')]
    if args[0] in (2, 3, 4, 5):
        assert len(hex_lines) == 3
        assert all(len(line.split(':', 2)[-1].split()) == 32 for line in hex_lines)
    else:
        assert not hex_lines
print(f'PASS {len(cases)} misc cases: exact command, zero command, every byte nonzero, '
      'malformed commands, geometry/read/write/sync/readback failures, replay and one-shot gates')
