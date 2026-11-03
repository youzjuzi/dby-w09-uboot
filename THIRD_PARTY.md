# Third-party materials and owner payloads

## Pinned upstream and checked scope

U-Boot v2026.10, archive `u-boot-2026.10.tar.gz`, tag commit `5508406582f6f7120dce0c4b3059819a41788db2`, SHA-256 `f943a88389c8fd70a6b0d061a88267465e143c7ca6ea2b75837ab20f5b60c739`. Obtain the [upstream archive](https://github.com/u-boot/u-boot/archive/refs/tags/v2026.10.tar.gz) separately. The archive was hash-checked and all twelve patches applied with fuzz=0 before reading the resulting file headers.

Most U-Boot code is GPL-2.0-or-later (legacy SPDX `GPL-2.0+`), with file-level exceptions. The archive's `Licenses/README` states GPL version 2, with later versions available for most files, not an unconditional later-version grant for every file. Keep upstream notices and licence texts when building or redistributing permitted code. This source inventory is not complete legal clearance of owner inputs.

## Actual optional-handoff dependencies

| File in the locked archive | Original declaration and use |
|---|---|
| `lib/lzma/LzmaDec.c` | `LZMA-SDK-9.22`; header: “2023-04-07 : Igor Pavlov : Public domain”. Decodes the embedded LZMA kernel. |
| `lib/lzma/LzmaTools.c` | `GPL-2.0+`; wrapper based on LZMA SDK 4.65 LzmaTest.c; preserves Industrie Dial Face S.p.A. (2007–2009) and Igor Pavlov (1999–2005) copyright notices. |
| `scripts/dtc/libfdt/libfdt.h` | `(GPL-2.0-or-later OR BSD-2-Clause)`; libfdt interface for FDT inspection and updates. Preserve David Gibson / IBM attribution. |

These components come from the separate upstream archive, not complete source copies in this repository. The archive's LZMA and libfdt declarations are not replaced by a blanket GPL statement.

## Per-patch target licences

All paths refer to the fully patched v2026.10 tree, including files newly introduced by patches. No SPDX lines are inserted into diff fragments. Project modifications follow the target's applicable terms; new integrated files declare GPL-2.0-or-later using the legacy GPL-2.0+ spelling.

| Patch | Target files | Actual target headers |
|---|---|---|
| [0001-sd-controller.patch](patches/0001-sd-controller.patch) | `drivers/mmc/mmc.c`<br>`drivers/mmc/mmc-uclass.c`<br>`common/board_r.c`<br>`arch/arm/dts/sd-read.dts`<br>`arch/arm/dts/Makefile` | `GPL-2.0+`: `drivers/mmc/mmc.c`, `drivers/mmc/mmc-uclass.c`, `common/board_r.c`, `arch/arm/dts/sd-read.dts`, `arch/arm/dts/Makefile` |
| [0002-misc-clear.patch](patches/0002-misc-clear.patch) | `cmd/misc-clear.c`<br>`include/misc-clear.h` | `GPL-2.0+`: `cmd/misc-clear.c`, `include/misc-clear.h` |
| [0003-storage-write-gates.patch](patches/0003-storage-write-gates.patch) | `drivers/block/blk-uclass.c`<br>`drivers/scsi/scsi.c`<br>`drivers/ufs/ufs-uclass.c` | `GPL-2.0+`: `drivers/block/blk-uclass.c`, `drivers/scsi/scsi.c`, `drivers/ufs/ufs-uclass.c` |
| [0004-environment-cli.patch](patches/0004-environment-cli.patch) | `cmd/nvedit.c` | `GPL-2.0+`: `cmd/nvedit.c` |
| [0005-manifest-boot.patch](patches/0005-manifest-boot.patch) | `cmd/sd-read.c`<br>`cmd/Makefile`<br>`arch/arm/mach-snapdragon/board.c` | `GPL-2.0+`: `cmd/sd-read.c`, `cmd/Makefile`, `arch/arm/mach-snapdragon/board.c` |
| [0006-status-flush.patch](patches/0006-status-flush.patch) | `lib/diagnostic.c`<br>`include/diagnostic.h`<br>`lib/Makefile`<br>`lib/hang.c`<br>`lib/panic.c` | `GPL-2.0+`: `lib/diagnostic.c`, `include/diagnostic.h`, `lib/Makefile`, `lib/hang.c`<br>`No SPDX header; see qualification below`: `lib/panic.c` |
| [0007-pon-observer.patch](patches/0007-pon-observer.patch) | `arch/arm/dts/sd-read.dts` | `GPL-2.0+`: `arch/arm/dts/sd-read.dts` |
| [0008-fixed-boot-menu.patch](patches/0008-fixed-boot-menu.patch) | `drivers/button/button-dby-pmic-gpio.c`<br>`drivers/button/Makefile`<br>`drivers/button/Kconfig`<br>`cmd/dby-boot.c`<br>`cmd/Makefile`<br>`cmd/sd-read.c`<br>`boot/Kconfig`<br>`arch/arm/dts/sd-read.dts` | `GPL-2.0+`: `drivers/button/button-dby-pmic-gpio.c`, `drivers/button/Makefile`, `cmd/dby-boot.c`, `cmd/Makefile`, `cmd/sd-read.c`, `arch/arm/dts/sd-read.dts`<br>`No SPDX header; see qualification below`: `drivers/button/Kconfig`, `boot/Kconfig` |
| [0009-sd-dma-timing.patch](patches/0009-sd-dma-timing.patch) | `cmd/sd-read.c` | `GPL-2.0+`: `cmd/sd-read.c` |
| [0010-gzip-kernel.patch](patches/0010-gzip-kernel.patch) | `arch/arm/mach-snapdragon/board.c`<br>`cmd/sd-read.c` | `GPL-2.0+`: `arch/arm/mach-snapdragon/board.c`, `cmd/sd-read.c` |
| [0011-fixed-menu-no-quit.patch](patches/0011-fixed-menu-no-quit.patch) | `cmd/bootmenu.c`<br>`cmd/dby-boot.c` | `GPL-2.0+`: `cmd/bootmenu.c`, `cmd/dby-boot.c` |
| [0012-optional-embedded-twrp.patch](patches/0012-optional-embedded-twrp.patch) | `cmd/dby-boot.c`<br>`cmd/dby-twrp.c`<br>`cmd/Makefile`<br>`cmd/Kconfig`<br>`cmd/bootmenu.c` | `GPL-2.0+`: `cmd/dby-boot.c`, `cmd/dby-twrp.c`, `cmd/Makefile`, `cmd/bootmenu.c`<br>`No SPDX header; see qualification below`: `cmd/Kconfig` |

`lib/panic.c` retains its historical Linux vsprintf attribution to Linus Torvalds and Lars Wirzenius but has no file SPDX. `drivers/button/Kconfig`, `boot/Kconfig` and `cmd/Kconfig` also have no SPDX header. For these files the archive's general GPL version 2 licensing statement supplies the baseline; this table does not invent a file-specific later-version declaration or remove historical attribution. Their precise file-level provenance remains a review qualification.

## Board facts, configuration and build dependencies

`board/framebuffer-private.dtsi` records the stock bootloader framebuffer region from the owner's runtime FDT. `board/sd-private.dtsi` and `board/ufs-private.dtsi` record controller/register regions from that FDT and the hardware address map. `board/partition-private.h` records the stock GPT geometry used by the guarded misc operation. These are transcribed hardware facts and project integration snippets, not copied vendor implementation source. They do not establish compatibility with another unit or firmware. Integration files use GPL-2.0-or-later.

`config/dby-w09.config` is the U-Boot v2026.10 automatically generated configuration baseline with project selections. `build.sh` checks the regenerated base configuration exactly, checking the optional TWRP selection separately. The host recipe and Python host tools use GPL-2.0-only. Python, GCC/binutils, make, patch, tar/gzip, coreutils and other host build/test libraries are external dependencies, not redistributed components of this repository.

## Owner payloads: stock Recovery kernel and TWRP

The TWRP input used for this work was obtained by the device owner from a download provided by an individual in a community. It is a third-party image built for this model, not an official TeamWin release. Its builder, correspondence to source code and build process have not been independently verified. This project makes no assertion about that image's licence, complete provenance or safety. SHA-256 identifies the same file; it does not establish safety or trustworthiness. Selecting TWRP runs a third-party recovery environment during early boot, with access to internal storage, so the owner must assess that trust. Neither the TWRP image nor stock Recovery is distributed in this repository; they are used only by the owner. A TWRP-enabled build embeds the compressed stock Recovery kernel in u-boot.bin. That u-boot.bin and the Recovery image produced from it contain vendor content and must not be published as project binaries. The open-source licences of the tools and boot code do not grant redistribution rights for these payloads. This repository is not a general TWRP installation tutorial.

本次使用的 TWRP 输入由设备所有者从社区个人提供的下载取得，是面向本机型的第三方镜像，并非 TeamWin 官方发布。其构建者、源码对应关系及构建方式未经独立核实，本项目不对该镜像的许可证、完整来源或安全性作断言。SHA-256 仅确认使用的是同一份文件，不证明它安全或可信。选择 TWRP 会在早期启动阶段运行第三方恢复环境，该环境能够访问内部存储，需由所有者自行判断信任。TWRP 镜像与原厂 Recovery 均不在仓库中分发，仅供所有者自行使用。启用 TWRP 的构建会将压缩后的原厂 Recovery 内核内嵌到 u-boot.bin；该 u-boot.bin 及由其生成的 Recovery 镜像含厂商内容，不得作为本项目二进制发布。工具和引导代码的开源许可证不授予这些载荷的再分发权。本仓库不是通用 TWRP 安装教程。
