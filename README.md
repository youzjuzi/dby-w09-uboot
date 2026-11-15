# dby-w09-uboot

R4 (2026-11-15): see the [fresh rebuild and separate 16 GB card checklist](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/fresh-install.md). Existing private inputs are reused; extraction is not repeated. New-card installation/first boot are Pending; third-party reproduction remains unverified. Preserve the working card for rollback and retain the existing Recovery/U-Boot without rebuilding or reflashing.

One-tablet development bootloader; no vendor images are supplied. Requires an unlocked bootloader and replacement Recovery: a wrong image can leave the tablet unbootable. The optional TWRP environment can access internal storage and needs an owner trust assessment. **The installation workflow has not been independently validated by a third party starting from a blank card; feedback is welcome.**

Boot Ubuntu from a microSD card on the Huawei MatePad 11 (DBY-W09) by placing U-Boot in the kernel segment of the owner's stock Recovery image. Normal power-on remains HarmonyOS; prepared card boot needs no computer.

[简体中文](README.zh-CN.md) · [Project hub](https://github.com/youzjuzi/dby-w09-linux) · [Linux kernel](https://github.com/youzjuzi/dby-w09-kernel) · [Build-to-install guide](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md)

## Scope and evidence

**H** recorded checks on one unlocked DBY-W09/HarmonyOS 4.2.0.213 cover Recovery → U-Boot → test/full Ubuntu boot (2026-11-02). Those **H** checks concern the historical ten-patch baseline. **O** rebuild evidence and the separate twelve-patch **R** observation are scoped below. Other units, firmware and stock-image combinations are **U**. These are development sources, not a universal installer or a verified-boot bypass. [Status and limits](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md) separate current and historical evidence.

This repository provides twelve patches against U-Boot v2026.10, configuration, board data, `build.sh` and `tools/pack-recovery.py`. It excludes stock Recovery, vendor firmware, Linux and Ubuntu. The [hub](https://github.com/youzjuzi/dby-w09-linux) owns drivers/bundles/rootfs/SD installation; the [kernel repository](https://github.com/youzjuzi/dby-w09-kernel) owns Linux patches, configuration and board DTS.

## Reproduce the pinned build

From this repository, supply the upstream v2026.10 archive and a fresh work location outside Git. Needed tools include aarch64-linux-gnu GCC/binutils (recorded GCC 15.2.0), native U-Boot build dependencies, make, patch, tar/gzip, coreutils and Python 3 for packing. Obtain the [upstream archive](https://github.com/u-boot/u-boot/archive/refs/tags/v2026.10.tar.gz) separately.

```sh
JOBS=8 sh build.sh /path/to/u-boot-2026.10.tar.gz \
  /path/to/new-build/source /path/to/new-build/out
sha256sum /path/to/new-build/out/u-boot.bin
```

Both source/output paths must be new. `build.sh` checks archive SHA-256 `f943a88389c8fd70a6b0d061a88267465e143c7ca6ea2b75837ab20f5b60c739`, applies twelve patches with fuzz=0, copies the board inputs, runs olddefconfig and compares the final configuration. It sets `SOURCE_DATE_EPOCH=1791417600`, build user `builder` and host `offline`. `CROSS_COMPILE` defaults to `aarch64-linux-gnu-`, `JOBS` to 8. Do not ignore failed hashes, patch errors or configuration differences.

Historical ten-patch output (O, reproduced after the earlier comment cleanup; not the current twelve-patch build):

```text
12213ff67f89ca67e528509cb0466006cfae55cae0af11009036f3c1c8516474  u-boot.bin
```

## Current twelve-patch outputs (O, 2026-11-03)

The neutral version suffix is `-dby-w09`. On 2026-11-03 the owner flashed both candidates on one unlocked tablet (user observation, R): the default build showed the three-item menu and Ubuntu, HarmonyOS reboot and power off worked; the TWRP build additionally entered TWRP, and the other actions also worked. This is one device, one stock input and short checks; it is not a wider validation, and a rebuild does not carry the observation forward. The Recovery hashes use the same recorded stock input and apply only to that combination. The TWRP artifacts contain vendor content and must not be published as project binaries.

| Build | u-boot.bin SHA-256 | Recovery SHA-256 |
|---|---|---|
| plain | `64e66740a03f89b29814899571347b339a99f4b4ab0ac431a94cb25284a1346e` | `862cb1d2bce0e16fec67c63c359e278891b0ffeb0e4e6e57b6df037ec73b6a00` |
| twrp | `65b1853eccff6e6414c7fcc928a527dcd7dab12aa42428c2c73b8e8df4a4fc42` | `8db139807d1255c4744caa3968d0382b6bcb23d35a7d356bdb94ca15c31b9677` |

## Repack your own Recovery

Use a verified original stock image for this device/firmware; preserve a checked copy for rollback. Replace the hash placeholder with its independently verified 64-hex digest. Packing is offline and never accesses a device:

```sh
python3 -I -B tools/pack-recovery.py \
  --base /path/to/own-stock-recovery.img \
  --kernel /path/to/new-build/out/u-boot.bin \
  --out /path/to/new-build/recovery.img \
  --expect-base-sha256 YOUR_VERIFIED_STOCK_SHA256
```

The tool first repacks the stock kernel and requires byte identity to the original. It then places `gzip -n` of U-Boot in the kernel segment, preserving ramdisk, recovery_dtbo, DTB, total length and AVB tail; only kernel_size, recovery_dtbo_offset and header id change. Retaining AVB metadata does not authenticate the new kernel. The historical ten-patch build with its recorded owner input produced Recovery SHA-256 `43618116c35fa4e01101241499bd1e42bc360602805c5d7b2ffd2652c354fa11` (O; H boot for that combination). Different stock inputs are not covered by that hash or device evidence.

Synthetic packing tests (O):

```sh
python3 -I -B tests/test-pack-recovery.py
```

Flashing, rollback, card preparation, first boot and checks are owner operations documented in the hub's [installation guide](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.md). Use plain reboot after flashing; everyday boot thereafter is manual Recovery entry, without a host.

## SD contract

p1 is FAT32 label `UBOOT`. U-Boot reads only `UBOOT/Image` (raw/gzip), `UBOOT/dby-w09.dtb`, `UBOOT/initrd.img` and `UBOOT/MANIFEST`. MANIFEST has exactly three lowercase SHA-256 lines, with two spaces before the basenames, ordered Image, dby-w09.dtb, initrd.img. Mismatch aborts boot. It authenticates no publisher; someone replacing both payloads and manifest can defeat this consistency check.

Linux additionally consumes `UBOOT/dby-device.img`; the hub's bundle manifest/installer checks that file. p2 is ext4 label `ubuntu-root`. See the [full card layout](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/architecture.md). The menu is Ubuntu / Reboot to HarmonyOS / Power off, or Ubuntu / Reboot to HarmonyOS / TWRP / Power off when built with a payload. Volume keys move, power confirms, and the default is Ubuntu after 5 seconds. The fixed menu has no Quit entry; ESC and invalid shortcuts do not select an action. The twelve-patch TWRP build was observed on one tablet on 2026-11-03: four menu actions, Ubuntu, HarmonyOS reboot, TWRP with touch and power off (**R**, user observation). The neutral-version default build was also observed on the same tablet on 2026-11-03 (**R**), within the short scope of the current-artifact section above.

## Storage boundary and limitations

Source-level write gates (O) keep SD read-only. The internal exception clears only `misc`'s first 32 bytes after checking `boot-recovery` with a NUL terminator, then reads back to verify. Board-specific partition/framebuffer data must be checked before adapting to another device; a matching string is not proof that arbitrary geometry is safe. Details: [technical description](docs/how-it-works.md) (English).

While U-Boot occupies Recovery, factory reset is unavailable; restore your verified stock Recovery first. Do not flash other internal partitions. Hardware acceptance of a modified image is limited to the recorded unlocked device. The project does not supply stock images or promise compatibility with other firmware.

This is an independent, unofficial device-porting project, not affiliated with, endorsed by or sponsored by Huawei/HarmonyOS/MatePad, Canonical/Ubuntu, Qualcomm or TeamWin. Names and trademarks belong to their respective owners. Vendor firmware is not provided; other device/firmware compatibility is not guaranteed.

An already unlocked bootloader is required. Flashing replaces Recovery; the modified image does not match the original AVB digest. An incorrect image or operation can make the device unbootable or prevent entry into Recovery. Keep and verify your own stock rollback image before flashing, and restore stock Recovery before a factory reset. SD installation erases the selected card. Software is provided as is, without warranty. See the hub installation guide linked above.

Patch licences follow individual target files; see the [per-patch inventory and exceptions](THIRD_PARTY.md). See [LICENSE](LICENSE), [acknowledgements](ACKNOWLEDGEMENTS.md), [contributing](CONTRIBUTING.md) and [security](SECURITY.md). Tools do not grant redistribution rights to stock-image data.

## Optional embedded TWRP payload

The TWRP input used for this work was obtained by the device owner from a download provided by an individual in a community. It is a third-party image built for this model, not an official TeamWin release. Its builder, correspondence to source code and build process have not been independently verified. This project makes no assertion about that image's licence, complete provenance or safety. SHA-256 identifies the same file; it does not establish safety or trustworthiness. Selecting TWRP runs a third-party recovery environment during early boot, with access to internal storage, so the owner must assess that trust. Neither the TWRP image nor stock Recovery is distributed in this repository; they are used only by the owner. A TWRP-enabled build embeds the compressed stock Recovery kernel in u-boot.bin. That u-boot.bin and the Recovery image produced from it contain vendor content and must not be published as project binaries. The open-source licences of the tools and boot code do not grant redistribution rights for these payloads. This repository is not a general TWRP installation tutorial.

Supply your own stock Android v2 recovery and ramdisk-only Android v0 TWRP image. No vendor binaries or identity headers are distributed here. Generate the private payload outside this repository, using independently verified input hashes:

```sh
python3 tools/prepare-twrp-payload.py \
  --stock-recovery /path/to/stock-recovery.img --twrp /path/to/twrp.img \
  --expect-stock-sha256 "$STOCK_SHA256" --expect-twrp-sha256 "$TWRP_SHA256" \
  --out-dir /path/to/new-payload
JOBS=8 sh build.sh /path/to/u-boot-2026.10.tar.gz \
  /path/to/new-source /path/to/new-output /path/to/new-payload
```

The optional fourth argument enables `CONFIG_DBY_TWRP`; omitting it keeps the three-action menu. Both builds require the base configuration to match exactly, with the new option checked separately. All generated payload files are deterministic across output directories: the assembly's `DBY_STOCK_PAYLOAD` macro expands to an absolute path at build time. Keep generated inputs and resulting firmware private.

The TWRP action preserves the previous bootloader's FDT and full initrd before relocation, verifies the embedded kernel and expected ramdisk identity, and calls standard `booti`. It does no storage I/O. A failed check or returned handoff prints the stage/reason, waits 15 seconds and uses the HarmonyOS PSCI reset path. The original recovery ramdisk must already contain the expected TWRP; this build does not install it. A running TWRP kernel can access internal storage. The 2026-11-03 TWRP build has the scoped user observation (**R**) above; newly built firmware still needs device validation. Host tests alone do not establish TWRP usability.
