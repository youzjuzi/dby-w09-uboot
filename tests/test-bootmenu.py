#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compile actual bootmenu C with host UI stubs; not a sandbox/device test.
Usage: test-bootmenu.py PREPARED_SOURCE OUTPUT_DIR
"""
from pathlib import Path
import subprocess
import sys
src=Path(sys.argv[1]);work=Path(sys.argv[2]);work.mkdir(parents=True,exist_ok=True)
s=(src/'cmd/bootmenu.c').read_text()
# Include actual entry creation, shortcut and escape handling. Rendering/EFI
# are stubbed; bootmenu_show is included to exercise last-entry dispatch.
s=s[s.index('/* maximum bootmenu entries */'):s.index('U_BOOT_CMD(')]
head=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <errno.h>
#include <assert.h>
typedef uint16_t u16;typedef unsigned long efi_uintn_t;typedef int efi_status_t;
#define CONFIG_CMD_BOOTEFI_BOOTMGR 0
#define CONFIG_CMD_EFICONFIG 0
#define CONFIG_BOOTMENU_DISABLE_UBOOT_CONSOLE 1
#define CONFIG_AUTOBOOT_MENU_SHOW
#define IS_ENABLED(x) (x)
#define EFI_SUCCESS 0
#define EFI_VARIABLE_BOOTSERVICE_ACCESS 0
#define EFI_VARIABLE_RUNTIME_ACCESS 0
#define CMD_RET_SUCCESS 0
#define debug(...) ((void)0)
#define log_warning(...) ((void)0)
#define fallthrough __attribute__((fallthrough))
#define ANSI_CURSOR_POSITION ""
#define ANSI_COLOR_REVERSE ""
#define ANSI_COLOR_RESET ""
#define ANSI_CLEAR_LINE ""
#define ANSI_CLEAR_LINE_TO_END ""
#define ANSI_CURSOR_HIDE ""
#define ANSI_CLEAR_CONSOLE ""
#define ANSI_CURSOR_SHOW ""
#define simple_strtol strtol
struct cmd_tbl {};
static int fixed=1,selected,ran,timing_lines;
void dby_twrp_print_timing(void){timing_lines++;}
static bool dby_bootmenu_fixed(void){return fixed;}
static char *options[]={"Ubuntu=ubuntu","Harmony=reset","TWRP=twrp","Power off=poweroff",NULL};
static char *env_get(const char *s){if(!strcmp(s,"bootmenu_default"))return "0";if(!strncmp(s,"bootmenu_",9)&&s[9]>='0'&&s[9]<='4')return options[s[9]-'0'];return NULL;}
enum bootmenu_key {BKEY_NONE,BKEY_UP,BKEY_DOWN,BKEY_SHORTCUT,BKEY_SELECT,BKEY_QUIT};
struct cli_ch_state {int shortcut_key;};
struct bootmenu_entry;
struct bootmenu_data {int delay,active,last_active,count;struct bootmenu_entry *first;};
static int key,shortcut;
static void cli_ch_init(struct cli_ch_state *c){c->shortcut_key=shortcut;}
static enum bootmenu_key bootmenu_loop(struct bootmenu_data *m,struct cli_ch_state *c){int k=key; key=BKEY_SELECT; return k;}
static enum bootmenu_key bootmenu_autoboot_loop(struct bootmenu_data *m,struct cli_ch_state *c){return bootmenu_loop(m,c);}
struct menu {void *entries[100];int count;};
static struct menu *menu_create(const char *a,int b,int c,void(*d)(struct menu*),void(*e)(void*),char*(*f)(void*),bool(*g)(void*),void*h){return calloc(1,sizeof(struct menu));}
static int menu_item_add(struct menu*m,const char*k,void*v){m->entries[m->count++]=v;return 1;}
static int menu_default_choice(struct menu*m,void **v){*v=m->entries[0];return 1;}
static void menu_default_set(struct menu*m,const char*k){}
static void menu_display_statusline(struct menu *m);
static int menu_get_choice(struct menu*m,void **v){int before=timing_lines;menu_display_statusline(m);assert(timing_lines==before+fixed*CONFIG_DBY_TWRP);assert(selected<m->count);*v=m->entries[selected];return 1;}
static void menu_destroy(struct menu*m){free(m);}
static int efi_global_variable_guid;
static int efi_init_obj_list(void){return 1;}
static int efi_get_variable_int(const void*a,const void*b,void*c,void*d,void*e,void*f){return 1;}
static int efi_set_variable_int(const void*a,const void*b,int c,int d,void*e,bool f){return 0;}
static int run_command(const char*c,int flag){assert(!strcmp(c,options[selected]+strcspn(options[selected],"=")+1));ran++;return 0;}
'''
post=r'''
int main(void){
 struct bootmenu_data *m=bootmenu_create(0,5);assert(m&&m->count==4&&m->delay==5&&m->active==0);
 shortcut=-1;key=BKEY_SHORTCUT;assert(!bootmenu_choice_entry(m));assert(m->active==0);
 shortcut=4;key=BKEY_SHORTCUT;assert(!bootmenu_choice_entry(m));
 key=BKEY_QUIT;assert(!bootmenu_choice_entry(m));assert(m->active==0);
 key=BKEY_NONE;assert(!strcmp(bootmenu_choice_entry(m),"0"));
 shortcut=3;key=BKEY_SHORTCUT;assert(!strcmp(bootmenu_choice_entry(m),"3"));
 key=BKEY_UP;assert(!bootmenu_choice_entry(m)&&m->active==2);
 key=BKEY_DOWN;assert(!bootmenu_choice_entry(m)&&m->active==3);
 bootmenu_destroy(m);
 for(selected=0;selected<4;selected++){int before=ran;assert(bootmenu_show(0,5)==BOOTMENU_RET_SUCCESS);assert(ran==before+1);}
 options[2]="Power off=poweroff";options[3]=NULL;
 m=bootmenu_create(0,5);assert(m->count==3);bootmenu_destroy(m);selected=2;assert(bootmenu_show(0,5)==BOOTMENU_RET_SUCCESS);
 fixed=0;m=bootmenu_create(0,5);assert(m->count==4);key=BKEY_QUIT;assert(!strcmp(bootmenu_choice_entry(m),"3"));bootmenu_destroy(m);
 selected=3;assert(bootmenu_show(0,5)==BOOTMENU_RET_QUIT);
 puts("PASS 14 bootmenu cases: entries, last dispatch, ESC, shortcuts, navigation, default, legacy policy");
}
'''
(work/'test.c').write_text(head+s+post)
for enabled in (0, 1):
    binary = work / f'test-{enabled}'
    subprocess.run(['cc', '-std=gnu11', '-Wno-format-extra-args', f'-DCONFIG_DBY_TWRP={enabled}', str(work/'test.c'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
