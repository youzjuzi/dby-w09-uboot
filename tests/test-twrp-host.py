#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual TWRP C + upstream decoder/booti with host RAM and hardware stubs.
Usage: test-twrp-host.py PREPARED_SOURCE OUTPUT_DIR RAMDISK_GZIP
The ramdisk must match the supplied private payload header; no device access.
"""
from pathlib import Path
import subprocess
import sys
src=Path(sys.argv[1]).resolve();work=Path(sys.argv[2]).resolve();ramdisk=Path(sys.argv[3]).resolve()
work.mkdir(parents=True,exist_ok=True)
stub=work/'stub';stub.mkdir(exist_ok=True)
for n,t in {'config.h':'#define CONFIG_LZMA 1\n#define min(a,b) ((a)<(b)?(a):(b))\n','log.h':'#define debug(...) ((void)0)\n','watchdog.h':'#define schedule() ((void)0)\n'}.items():(stub/n).write_text(t)
head=r'''
#define DBY_TWRP_HOST
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <zlib.h>
#include <openssl/sha.h>
#include <libfdt.h>
#include "LzmaTools.h"
#include "dby-twrp-data.h"
typedef unsigned long ulong;
typedef uint64_t phys_addr_t;
typedef uint64_t phys_size_t;
typedef uint8_t u8;
typedef uint32_t u32;
typedef uint64_t u64;
static unsigned int crc_calls;
static uLong counted_crc32(uLong crc, const Bytef *p, uInt n)
{
    crc_calls++;
    return crc32(crc, p, n);
}
#define crc32 counted_crc32
static u64 fake_ticks;
static u64 twrp_counter(void){fake_ticks+=10;return fake_ticks;}
static u64 twrp_frequency(void){return 1000;}

#define __section(x) __attribute__((section(x)))
#define SZ_4K (4096UL)
#define SZ_2M (2UL<<20)
#define SZ_64M (64UL<<20)
#define SZ_128M (128UL<<20)
#define SZ_512M (512UL<<20)
#define CONFIG_SYS_MEM_TOP_HIDE (1024UL<<20)
#define CONFIG_STACK_SIZE (16UL<<20)
#define CONFIG_NR_DRAM_BANKS 2
#define SHA256_SUM_LEN 32
#define CHUNKSZ_SHA256 (64*1024)
#define ALIGN_DOWN(x,a) ((x)&~((a)-1))
#define ALIGN(x,a) (((x)+(a)-1)&~((a)-1))
#define BIT(x) (1UL<<(x))
#define le32_to_cpu(x) (x)
#define le64_to_cpu(x) (x)
struct fake_gd { struct {ulong start,size;} dram[2]; ulong ram_top,start_addr_sp; } global, *gd=&global;
phys_addr_t dby_kernel_buffer,dby_initrd_buffer,dby_fdt_buffer;
static ulong prior_fdt; static int handoffs;
static char saved_args[16384];
static ulong get_prev_bl_fdt_addr(void){return prior_fdt;}
static void sha256_csum_wd(const unsigned char *p,unsigned int n,unsigned char *h,unsigned int chunk){SHA256(p,n,h);}
static void exp_diag_flush(void){}
static int env_set(const char *k,const char *v){if(!strcmp(k,"bootargs"))snprintf(saved_args,sizeof(saved_args),"%s",v);return 0;}
static int run_command(const char *cmd,int flag);
static void *map_sysmem(ulong p,int unused){return (void *)p;}
static void unmap_sysmem(void *p){}
'''
image=(src/'arch/arm/lib/image.c').read_text();image=image[image.index('#define LINUX_ARM64_IMAGE_MAGIC'):]
post=r'''
static int run_command(const char *cmd,int flag){
 ulong kernel,rd,size,fdt;assert(!flag);assert(sscanf(cmd,"booti %lx %lx:%lx %lx",&kernel,&rd,&size,&fdt)==4);
 assert(kernel==dby_kernel_buffer+DBY_KERNEL_OFFSET);assert(size==DBY_TWRP_SIZE+32);
 assert(rd==dby_initrd_buffer&&fdt==dby_fdt_buffer);
 assert(matches_sha((void *)rd,DBY_TWRP_SIZE,dby_twrp_sha));
 for(int i=0;i<32;i++)assert(((u8 *)rd)[DBY_TWRP_SIZE+i]==0xa5);
 assert(!strcmp(saved_args,"androidboot.mode=recovery test=preserve"));
 int node=fdt_path_offset((void *)fdt,"/chosen");ulong v;
 assert(!get_address((void *)fdt,node,"linux,initrd-start",&v)&&v==rd);
 assert(!get_address((void *)fdt,node,"linux,initrd-end",&v)&&v==rd+size);
 assert(!strcmp(fdt_getprop((void *)fdt,node,"test-vendor-prop",NULL),"preserved"));
 handoffs++;return 0;
}
int main(int argc,char **argv){
 assert(argc==2);void *memory;assert(!posix_memalign(&memory,SZ_2M,2048UL<<20));ulong base=(ulong)memory;
 gd->dram[0].start=base;gd->dram[0].size=2048UL<<20;gd->ram_top=base+(2048UL<<20);
 gd->start_addr_sp=gd->ram_top-CONFIG_SYS_MEM_TOP_HIDE-(300UL<<20);
 prior_fdt=base+(2UL<<20);void *fdt=(void *)prior_fdt;
 assert(!fdt_create_empty_tree(fdt,SZ_2M));int node=fdt_add_subnode(fdt,0,"chosen");assert(node>=0);
 ulong original_rd=base+(32UL<<20);FILE *f=fopen(argv[1],"rb");assert(f);
 assert(fread((void *)original_rd,1,DBY_TWRP_SIZE,f)==DBY_TWRP_SIZE);fclose(f);
 memset((void *)(original_rd+DBY_TWRP_SIZE),0xa5,32);
 assert(!fdt_setprop_u64(fdt,node,"linux,initrd-start",original_rd));
 assert(!fdt_setprop_u64(fdt,node,"linux,initrd-end",original_rd+DBY_TWRP_SIZE+32));
 assert(!fdt_setprop_string(fdt,node,"bootargs","androidboot.mode=recovery test=preserve"));
 assert(!fdt_setprop_string(fdt,node,"test-vendor-prop","preserved"));
 dby_kernel_buffer=base+(128UL<<20);dby_initrd_buffer=base+(256UL<<20);dby_fdt_buffer=base+(390UL<<20);
 assert(board_get_usable_ram_top(0)==gd->ram_top&&snap.state==1);
 gd->ram_top-=CONFIG_SYS_MEM_TOP_HIDE;
 /* Negative control: old hook used pre-TOP_HIDE top, rejecting this stack. */
 ulong correct_top=snap.top;
 snap.top+=CONFIG_SYS_MEM_TOP_HIDE;
 assert(!reserve_arch()&&snap.state==-ERANGE);
 snap.top=correct_top;snap.state=1;
 assert(!reserve_arch()&&snap.state==2&&gd->start_addr_sp==snap.fdt);
 assert(crc_calls==0); /* Both early hooks, including rejected reservation. */
 assert(snap.hook_ticks==10&&snap.copy_ticks==10);
 assert(dby_twrp_boot()<0&&handoffs==0&&crc_calls==0); /* No baseline yet. */
 dby_twrp_prepare_menu();
 assert(snap.crc_ready&&crc_calls==2&&snap.menu_ticks==70);
 assert(ticks_to_ms(123456789,19200000)==6430);
 /* Simulate subsequent users overwriting the original ABL source buffers. */
 memset((void *)original_rd,0,DBY_TWRP_SIZE+32);memset(fdt,0,SZ_2M);
 assert(!dby_twrp_boot()&&handoffs==1);
 /* Identity failure with valid CRC must independently reject. */
 ((u8 *)snap.rd)[0]^=1;snap.rd_crc=crc32(0,(void *)snap.rd,snap.rd_size);
 assert(dby_twrp_boot()<0&&handoffs==1);
 ((u8 *)snap.rd)[0]^=1;snap.rd_crc=crc32(0,(void *)snap.rd,snap.rd_size);
 ((u8 *)snap.rd)[snap.rd_size-1]^=1;
 assert(dby_twrp_boot()<0&&handoffs==1);
 ((u8 *)snap.rd)[snap.rd_size-1]^=1;
 ((u8 *)snap.fdt)[snap.fdt_size-1]^=1;
 assert(dby_twrp_boot()<0&&handoffs==1); /* FDT changed after first sight. */
 puts("PASS 8 actual C groups: early CRC zero / post-first-sight FDT corruption / timer conversion and line / TOP_HIDE regression / identity rejection / snapshot / U-Boot LZMA decoder / kernel SHA / booti placement / full initrd and ABL DT / corrupted snapshot refused");
 free(memory);return 0;
}
'''
(work/'test.c').write_text(head+image+'\n'+(src/'cmd/dby-twrp.c').read_text()+post)
dtc=src/'scripts/dtc/libfdt'
args=['cc','-O2','-std=gnu11','-Wall','-Wextra','-Wno-unused-parameter','-I'+str(stub),'-I'+str(dtc),'-I'+str(src/'lib/lzma'),'-I'+str(src/'cmd'),'-idirafter',str(src/'include'),str(work/'test.c'),'-DDBY_STOCK_PAYLOAD="'+str((src/'cmd/stock-kernel.lzma').resolve())+'"',str(src/'cmd/dby-stock.S'),str(src/'lib/lzma/LzmaTools.c'),str(src/'lib/lzma/LzmaDec.c')]
args += [str(dtc/(name+'.c')) for name in ['fdt','fdt_ro','fdt_rw','fdt_sw','fdt_wip','fdt_empty_tree','fdt_check','fdt_strerror']]
args+=['-lz','-lcrypto','-o',str(work/'test')]
subprocess.run(args, check=True)
result = subprocess.run([str(work/'test'), str(ramdisk)], check=True, capture_output=True, text=True)
print(result.stdout, end='')
assert result.stdout.splitlines().count('TWRP prep: hook 10 ms, copy 10 ms, menu at 70 ms') == 1

