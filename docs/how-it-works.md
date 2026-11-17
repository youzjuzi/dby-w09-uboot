# Technical description

Language: English. 中文入口：[README.zh-CN.md](../README.zh-CN.md)。Mechanisms below are O source descriptions; device behavior is H only for the recorded single-device baseline. See the hub [status](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md).

## 1. Problem statement

The device ships with a vendor system and a bootloader that accepts only vendor-signed images in its normal boot path. The objective is to run a general-purpose Linux distribution from removable storage, subject to three constraints:

- **C1.** The stock system remains the default and is not modified.
- **C2.** Changing the operating system must not require rewriting internal storage.
- **C3.** Booting must not require a host computer.

## 2. Approach

A `recovery` image is an Android-format boot image whose kernel segment the vendor bootloader (ABL) loads and enters. On the tested device, an image whose kernel segment was replaced by an AArch64 executable was loaded and entered when Recovery was selected, although the image's AVB payload digest no longer matches. This work places a U-Boot image in that segment. No bootloader exploit was developed or used. Acceptance of the modified image is an empirical result for one device and firmware version, not a documented vendor behaviour, and may differ elsewhere.

Consequences:

- A normal boot loads the `boot` partition and is unaffected (C1).
- The payload runs only on an explicit entry into Recovery, which is a manual action.
- The operating system is read from the card, so replacing it leaves internal storage untouched (C2) and needs no computer (C3).

## 3. Boot sequence

```
manual Recovery entry
  -> vendor bootloader loads recovery image
     -> kernel segment = this U-Boot
        -> read "misc"; if it holds "boot-recovery", clear the command field
        -> fixed menu (Ubuntu / HarmonyOS / [optional TWRP] / power off)
        -> read the first FAT partition of the card, read-only
        -> verify UBOOT/MANIFEST (SHA-256 of Image, dtb, initrd)
        -> boot Linux with a fixed command line
```

The `misc` partition is cleared because the stock Recovery flow leaves the command `boot-recovery` in it. Without clearing, the following reboot would re-enter Recovery.

Linux `reboot recovery` can request Recovery through the PON restart reason without a misc command. After the same device/partition geometry checks and first-block read, an entirely zero 32-byte command field returns `NO COMMAND` and continues without arming, writing or synchronizing storage. A `boot-recovery` C string retains the existing clear/sync/full-block-readback flow; every other command is rejected. Device result (R, one tablet, 2026-11-17, TWRP build): PON entry shows `MISC NO COMMAND` and reaches the menu; key entry still shows `MISC CLEARED OK`; returning to HarmonyOS does not loop. The saved MISC result/reason is redrawn after menu/SD screen clearing. A rejected command additionally shows only command bytes 0–31 in hex; no other block contents are printed.

## 4. Security design

### 4.1 Assets and assumptions

The assets to protect are the integrity of internal storage and the integrity of what is executed after U-Boot. The design assumes that the person holding the device controls which card is inserted; it does not defend against an adversary who can replace the manifest together with the files it lists, since the manifest resides on the card itself. Its purpose is to detect corruption and accidental mismatch, not to authenticate the card's provider.

### 4.2 Measures

| Measure | Effect |
|---|---|
| Read-only access to the card | The card cannot be altered by this software |
| Write gates in the block layer | Writes to internal storage are rejected except the permitted `misc` range |
| Verify-before-write on `misc` | The first 32 bytes must read as the C string `boot-recovery` (13 characters followed by a zero byte) before they are cleared; bytes after the terminator are not examined; the write is verified by reading back |
| Fixed command line | No bootargs are taken from the card |
| No script or environment loading from the card; environment-editing commands removed | Removes a class of injection through card content |
| Manifest with a fixed order of three digests | Detects corrupt or mismatched files |

### 4.3 Residual risks

- The location of `misc` is device specific. Using the data in `board/` on another unit or firmware version without verification may target a different region; the verify-before-write check makes an unintended write unlikely but does not exclude it.
- A defective U-Boot image written to `recovery` may prevent Recovery from starting. The recovery path is to restore the stock image through the bootloader's flashing mode, which is outside this software.

## 5. Implementation overview

| Patch | Function |
|---|---|
| 0001 | SD controller bring-up for this SoC (driver adjustments, device tree, board initialisation) |
| 0002 | Clearing of the `misc` command field |
| 0003 | Storage write gates in the block, SCSI and UFS layers |
| 0004 | Removal of the environment-editing commands |
| 0005 | Manifest-verified boot of Linux |
| 0006 | Flushing of status output at handoff, hang and panic boundaries |
| 0007 | Device tree nodes for the PMIC power and volume-down keys |
| 0008 | Fixed three-item boot menu; volume-up key read from a PMIC GPIO |
| 0009 | ADMA64 transfers and timing for the SD controller |
| 0010 | Acceptance of a gzip-compressed kernel image |
| 0011 | Non-exitable board menu, with generic callers unchanged |
| 0012 | Optional embedded recovery kernel and preserved ABL handoff |
| 0013 | Accept an empty misc command without writes; retain MISC diagnostics after clearing the screen |

## 6. Evidence and limits

The historical ten-patch build with the recorded owner inputs reproduced `u-boot.bin` SHA-256 `12213ff67f89ca67e528509cb0466006cfae55cae0af11009036f3c1c8516474`; its Recovery image was `43618116c35fa4e01101241499bd1e42bc360602805c5d7b2ffd2652c354fa11`. The 2026-11-02 H boot records apply to that combination, not every mechanism or subsequent build.

The neutral-version twelve-patch default build was observed on one tablet on 2026-11-03 (R): three menu actions, Ubuntu, HarmonyOS reboot and power off; see the current-artifact section in README. The TWRP build was observed on one tablet on 2026-11-03 (R): four menu actions, Ubuntu, HarmonyOS reboot, TWRP with touch and power off. Other devices/firmware remain U. New version-string builds require new device validation; historical R is not promoted to H.

### Optional recovery handoff

The TWRP input used for this work was obtained by the device owner from a download provided by an individual in a community. It is a third-party image built for this model, not an official TeamWin release. Its builder, correspondence to source code and build process have not been independently verified. This project makes no assertion about that image's licence, complete provenance or safety. SHA-256 identifies the same file; it does not establish safety or trustworthiness. Selecting TWRP runs a third-party recovery environment during early boot, with access to internal storage, so the owner must assess that trust. Neither the TWRP image nor stock Recovery is distributed in this repository; they are used only by the owner. A TWRP-enabled build embeds the compressed stock Recovery kernel in u-boot.bin. That u-boot.bin and the Recovery image produced from it contain vendor content and must not be published as project binaries. The open-source licences of the tools and boot code do not grant redistribution rights for these payloads. This repository is not a general TWRP installation tutorial.

本次使用的 TWRP 输入由设备所有者从社区个人提供的下载取得，是面向本机型的第三方镜像，并非 TeamWin 官方发布。其构建者、源码对应关系及构建方式未经独立核实，本项目不对该镜像的许可证、完整来源或安全性作断言。SHA-256 仅确认使用的是同一份文件，不证明它安全或可信。选择 TWRP 会在早期启动阶段运行第三方恢复环境，该环境能够访问内部存储，需由所有者自行判断信任。TWRP 镜像与原厂 Recovery 均不在仓库中分发，仅供所有者自行使用。启用 TWRP 的构建会将压缩后的原厂 Recovery 内核内嵌到 u-boot.bin；该 u-boot.bin 及由其生成的 Recovery 镜像含厂商内容，不得作为本项目二进制发布。工具和引导代码的开源许可证不授予这些载荷的再分发权。本仓库不是通用 TWRP 安装教程。

Patch 0011 removes the synthetic exit entry only while the board fixed menu is active. It also changes last-entry dispatch, ESC/shortcut handling and the automatic-menu Quit fallback; generic bootmenu callers retain upstream behavior. Patch 0012 adds the default-off `DBY_TWRP` build option and the optional third action. Ubuntu SD reads and the MANIFEST contract are unchanged.

Before relocation, `board_get_usable_ram_top` validates the ABL FDT/initrd and bootargs against the effective top after `SYS_MEM_TOP_HIDE`, while returning the original top. Metadata lives in `.data`; `reserve_arch` reserves copies above the stack without early CRC scans. Once caches are enabled, the board menu records first-sight CRCs of those copies; the TWRP action checks them again before use. The handoff verifies ramdisk identity, embedded LZMA and decoded ARM64 kernel SHA-256, then checks `booti_setup` placement. It copies the preserved FDT/initrd into existing buffers and runs `booti`. Any failure or returned `booti` is reported on screen, followed by a 15-second delay and the existing HarmonyOS reset action. No new storage operations are introduced.

The generated assembly uses an absolute-path macro supplied by the build, keeping generated file contents independent of their directory. Payload bytes reside in normal read-only linked sections, inside the Image size and relocation range. Host tests use the actual new C, U-Boot decoder and ARM64 placement code, but stub hardware, timers and command handoff; they cannot validate display, button timing, cache behavior or a TWRP boot on the device.

中文：0011 仅为板级固定菜单去掉退出项，并同步处理末项、ESC、快捷键与自动菜单回退；通用调用者不变。0012 可选内置载荷，默认关闭。重定位前按扣除 `SYS_MEM_TOP_HIDE` 的有效顶端检查 ABL FDT/initrd，钩子仍返回原顶端；早期不做 CRC 扫描，将副本纳入栈上方保留区；缓存开启后在菜单入口建立副本首次 CRC 基线，选择 TWRP 时再复核。校验 ramdisk 身份、压缩及解压内核 SHA 与 ARM64 放置后走标准 `booti`；任何失败或返回显示原因，15 秒后走鸿蒙 PSCI 复位。Ubuntu/SD/MANIFEST 行为不变，无新增存储操作。主机替身不能证明实机显示、按键时序、缓存或 TWRP 启动成功。

The early copy relies on the existing non-overlap checks: the ABL source buffers lie outside the validated top window used for relocation, stack and malloc, and this boot flow has no second writer to them. First-sight CRC does not verify the early source/copy operation; it detects subsequent changes to either saved FDT or initrd. FDT structural checks, bounds and overlap checks, and the ramdisk/kernel SHA identity checks remain unchanged.

Payload builds show `TWRP prep: hook X ms, copy Y ms, menu at Z ms` after the board title, then redraw the same values in the fixed menu header so the menu clear does not erase the record. Header redraw does not recompute CRCs. Early hooks store raw ARM generic physical-counter ticks only; conversion uses CNTFRQ at menu time. `menu at` is absolute counter time at the title, before first-sight CRC scans, not elapsed time since the power key and not the bootmenu countdown start. The line has no memory addresses; plain builds do not call or display it. The user reported faster menu entry on 2026-11-03 (R), with displayed hook/copy/menu-at values 596/1222/6539 ms. This is one observation, not a general performance guarantee or a measurement for future builds.

中文：早期复制依赖既有不重叠检查：ABL 源缓冲区位于重定位、栈与 malloc 使用的已验证顶部窗口之外，此启动流程没有第二个写入者。首次 CRC 不证明早期源数据或复制过程完整，只检测副本 FDT/initrd 此后的改动；结构、范围、重叠与 SHA 身份检查保持不变。带载荷版在标题之后显示上述计时行，并在固定菜单首行重绘同一组数值，避免清屏后消失；重绘不重新计算 CRC。无载荷版不显示。早期仅存物理计数器原始值，显示时按 CNTFRQ 换算；menu at 是标题处、首次 CRC 之前的绝对计数器时间，不是按电源后的耗时，也不是倒计时开始时刻。2026-11-03 用户观察进菜单变快（R），显示值为 hook/copy/menu at 596/1222/6539 ms；仅为一次观察，不保证其他构建的性能。

### Neutral version suffix and new candidates (O; R on one tablet)

The configured suffix is now `-dby-w09`. It is the same length as the historical suffix to isolate the change. For both default and TWRP binaries, `cmp -l` found exactly 21 changed bytes across three version strings: the FDT version value, the board menu title and the shared version/banner string used by `version` (abbreviated `ver`). All other bytes and total lengths are identical. New Recovery images have new compressed kernels and header identities; their unchanged stock components/AVB tail do not authenticate them. Both new images were checked on one tablet on 2026-11-03 by the owner (R, short checks; see the README), which does not extend to other units or inputs. Current hashes are in the [README](../README.md#current-twelve-patch-outputs-o-2026-11-03).
