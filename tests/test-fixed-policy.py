#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run actual fixed board policy C with host command/timer/reset stubs.
Usage: test-fixed-policy.py PREPARED_SOURCE OUTPUT_DIR
"""
from pathlib import Path
import subprocess
import sys
src=Path(sys.argv[1]);work=Path(sys.argv[2]);work.mkdir(parents=True,exist_ok=True)
s=(src/'cmd/dby-boot.c').read_text();s=s[s.index('int dby_clear_misc'):s.index('U_BOOT_CMD(')]
head=r'''
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <assert.h>
#include <errno.h>
#include <setjmp.h>
#include <stdlib.h>
#define IS_ENABLED(x) (x)
#define __noreturn
#define PLAIN_VERSION "host"
#define CMD_RET_USAGE 2
#define CMD_RET_SUCCESS 0
struct cmd_tbl {};
static jmp_buf done;static int scenario,clears,sd,reset,off,menus,delay,twrp;
static int prep;
void dby_twrp_prepare_menu(void){prep++;}
static char values[7][128];static int do_dbyselect(struct cmd_tbl *,int,int,char *const[]);
static void exp_diag_flush(void){}
static void clear_ctrlc(void){}
static void console_clear(void){}
static void hang(void){longjmp(done,1);}
static void mdelay(int n){delay+=n;}
static int console_assign(FILE *stream,const char *name){return 0;}
int dby_clear_misc(void){clears++;return scenario==6?-EINVAL:0;}
int dby_twrp_boot(void){twrp++;if(scenario==2)longjmp(done,1);return scenario==3?-EIO:0;}
static int env_set(const char *key,const char *val){int n=-1;if(!strncmp(key,"bootmenu_",9)&&key[9]>='0'&&key[9]<='4'&&!key[10])n=key[9]-'0';else if(!strcmp(key,"bootmenu_default"))n=5;else if(!strcmp(key,"bootmenu_delay"))n=6;assert(n>=0);snprintf(values[n],128,"%s",val?val:"NULL");return 0;}
static int run_command(const char *c,int flag){assert(!flag);if(!strcmp(c,"bootmenu")){assert(prep==CONFIG_DBY_TWRP);menus++;char *v[]={"dbyselect",scenario==1?"reboot":scenario==4?"off":scenario>=2?"twrp":"ubuntu"};assert(!do_dbyselect(NULL,0,2,v));return 0;}if(!strcmp(c,"sdread")){sd++;longjmp(done,1);}if(!strcmp(c,"reset")){reset++;longjmp(done,1);}if(!strcmp(c,"poweroff")){off++;longjmp(done,1);}assert(0);return -1;}
'''
post=r'''
int main(int argc,char **argv){assert(argc==2);scenario=atoi(argv[1]);char *v[]={"dbyselect","invalid"};assert(do_dbyselect(NULL,0,2,v)==CMD_RET_USAGE);assert(do_dbyselect(NULL,0,1,v)==CMD_RET_USAGE);
 if(!CONFIG_DBY_TWRP){v[1]="twrp";assert(do_dbyselect(NULL,0,2,v)==CMD_RET_USAGE);}
 if(!setjmp(done))do_dbyboot(NULL,0,1,NULL);
 if(scenario==6){assert(clears==1&&sd==1&&!menus&&!twrp&&!reset&&!off);assert(dby_boot_misc_status()==-EINVAL);puts("PASS rejected misc never enters menu/TWRP");return 0;}
 assert(prep==CONFIG_DBY_TWRP);assert(clears==1&&menus==1);assert(sd==(scenario==0));assert(twrp==(scenario==2||scenario==3||scenario==5));assert(reset==(scenario==1||scenario==3||scenario==5));assert(off==(scenario==4));
 assert(!strcmp(values[0],"Ubuntu=dbyselect ubuntu"));assert(!strcmp(values[1],"Reboot to HarmonyOS=dbyselect reboot"));
 assert(!strcmp(values[2],CONFIG_DBY_TWRP?"TWRP=dbyselect twrp":"Power off=dbyselect off"));
 assert(!strcmp(values[3],CONFIG_DBY_TWRP?"Power off=dbyselect off":"NULL"));assert(!strcmp(values[4],"NULL"));assert(!strcmp(values[5],"0"));assert(!strcmp(values[6],"5"));
 assert(delay==((scenario==3||scenario==5)?15000:0));printf("PASS policy enabled=%d scenario=%d\n",CONFIG_DBY_TWRP,scenario);
}
'''
(work/'test.c').write_text(head+s+post)
for enabled,scenarios in [(1,range(7)),(0,[0,1,4,6])]:
    binary=work/f'test-{enabled}'
    subprocess.run(['cc','-std=gnu11',f'-DCONFIG_DBY_TWRP={enabled}',str(work/'test.c'),'-o',str(binary)],check=True)
    for scenario in scenarios: subprocess.run([str(binary),str(scenario)],check=True)
