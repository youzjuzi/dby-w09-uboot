# dby-w09-uboot

R4（2026-11-15）：维护者从空白 **16 GB 新卡**照公开文档全新安装通过，包 **`20261115-1`**（**H + R**：用户提供的 Claude SSH 核对与用户交互观察）。见[新卡结果与操作清单](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/fresh-install.md)。第三方独立复现仍为 **U**；已有私有输入复用，提取未重做、保持原证据级别。现有 Recovery/U-Boot 未重编、未重刷；原工作卡保留作回退。

仅有一台平板证据的开发引导器，不提供厂商镜像。需要已解锁 Bootloader 并替换 Recovery，错误镜像可能导致无法启动；可选 TWRP 环境能访问内部存储，须由所有者判断信任。**安装流程未经第三方从空白卡独立验证，欢迎反馈。**

将 U-Boot 放进所有者原厂 Recovery 镜像的内核段，在华为 MatePad 11（DBY-W09）上从 microSD 卡启动 Ubuntu。正常开机仍进鸿蒙，准备完成后的卡启动无需电脑。

[English](README.md) · [项目中心](https://github.com/youzjuzi/dby-w09-linux) · [Linux 内核](https://github.com/youzjuzi/dby-w09-kernel) · [构建安装指南](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md)

## 范围与证据

**H 实机记录**：2026-11-02，一台已解锁、HarmonyOS 4.2.0.213 的 DBY-W09 经 Recovery → U-Boot 启动测试／完整 Ubuntu。上述 **H** 属于旧十补丁基线；离线重建与十二补丁版的 **R 用户观察**范围分别见下。其他个体、固件和原厂镜像组合为 **U 未验证**。这是开发源码，不是通用安装器，也不代表通用绕过验证启动；[状态页](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/status.md)区分当前与历史证据。

本仓库提供 U-Boot v2026.10 的十三个补丁、配置、板级数据、`build.sh` 和 `tools/pack-recovery.py`，不含原厂 Recovery、厂商固件、Linux 或 Ubuntu。[中心仓库](https://github.com/youzjuzi/dby-w09-linux)负责驱动／bundle／rootfs／SD 安装；[内核仓库](https://github.com/youzjuzi/dby-w09-kernel)负责 Linux 补丁、配置与板级 DTS。

## 复现锁定构建

从本仓库执行，自行准备上游 v2026.10 归档和 Git 外的新工作目录。需要 aarch64-linux-gnu GCC/binutils（记录 GCC 15.2.0）、U-Boot 原生构建依赖、make、patch、tar/gzip、coreutils；打包另需 Python 3。[上游压缩包](https://github.com/u-boot/u-boot/archive/refs/tags/v2026.10.tar.gz)单独取得。

```sh
JOBS=8 sh build.sh /path/to/u-boot-2026.10.tar.gz \
  /path/to/new-build/source /path/to/new-build/out
sha256sum /path/to/new-build/out/u-boot.bin
```

源码／输出目录必须尚不存在。`build.sh` 校验上游 SHA-256 `f943a88389c8fd70a6b0d061a88267465e143c7ca6ea2b75837ab20f5b60c739`，fuzz=0 应用十三个补丁、复制板级输入、运行 olddefconfig 并比较最终配置。脚本固定 `SOURCE_DATE_EPOCH=1791417600`、构建用户 `builder` 与主机 `offline`；`CROSS_COMPILE` 默认 `aarch64-linux-gnu-`，`JOBS` 默认 8。摘要、补丁或配置不符时停止，不能忽略错误继续。

旧十补丁基线产物（O，早期注释整理后重建一致；不代表当前构建）：

```text
12213ff67f89ca67e528509cb0466006cfae55cae0af11009036f3c1c8516474  u-boot.bin
```

## 已记录的十二补丁产物（O，2026-11-03）

中性版本后缀为 `-dby-w09`。2026-11-03 所有者在一台已解锁平板上依次刷入了这两个候选（用户观察 R）：默认版三项菜单，进入 Ubuntu、重启回鸿蒙、关机均正常；TWRP 版另可进入 TWRP，其余动作也正常。仅为一台设备、同一原厂输入的短时检查，不代表更广泛验证，重新构建后不能继承该观察。Recovery 哈希使用记录中的同一原厂输入，仅适用于该组合。TWRP 产物含厂商内容，不得作为本项目二进制发布。

| Build | u-boot.bin SHA-256 | Recovery SHA-256 |
|---|---|---|
| plain | `64e66740a03f89b29814899571347b339a99f4b4ab0ac431a94cb25284a1346e` | `862cb1d2bce0e16fec67c63c359e278891b0ffeb0e4e6e57b6df037ec73b6a00` |
| twrp | `65b1853eccff6e6414c7fcc928a527dcd7dab12aa42428c2c73b8e8df4a4fc42` | `8db139807d1255c4744caa3968d0382b6bcb23d35a7d356bdb94ca15c31b9677` |

## 用自己的原厂 Recovery 重打包

使用适配本机／固件、已校验的原厂镜像，并保留校验副本回退。摘要占位符替换为独立核实的 64 位十六进制值。打包仅操作主机文件，不访问设备：

```sh
python3 -I -B tools/pack-recovery.py \
  --base /path/to/own-stock-recovery.img \
  --kernel /path/to/new-build/out/u-boot.bin \
  --out /path/to/new-build/recovery.img \
  --expect-base-sha256 YOUR_VERIFIED_STOCK_SHA256
```

工具先用原内核重打包，要求与原镜像逐字节一致，再将 `gzip -n` 的 U-Boot 放入内核段；ramdisk、recovery_dtbo、DTB、总长度和 AVB 尾部保持原字节，只改 kernel_size、recovery_dtbo_offset 与 header id。保留 AVB 不代表新内核被认证。旧十补丁基线与记录中的自有输入产生 Recovery SHA-256 `43618116c35fa4e01101241499bd1e42bc360602805c5d7b2ffd2652c354fa11`（O；该组合启动 H）；其他原厂输入不在此摘要或实机结论范围。

打包合成测试（O）：

```sh
python3 -I -B tests/test-pack-recovery.py
```

刷写、回退、写卡、首次启动和检查由所有者按中心仓库[安装指南](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/install.zh-CN.md)操作。刷后使用普通 reboot；之后日常启动只需手动进 Recovery，不依赖主机。

## SD 契约

p1 为 FAT32、卷标 `UBOOT`。U-Boot 只读 `UBOOT/Image`（原始／gzip）、`UBOOT/dby-w09.dtb`、`UBOOT/initrd.img`、`UBOOT/MANIFEST`。MANIFEST 恰好三行小写 SHA-256，文件名前两个空格，顺序为 Image、dby-w09.dtb、initrd.img；不符即中止。它只检查一致性，不认证发布者，不能抵御同时替换载荷和清单。

Linux 另读取 `UBOOT/dby-device.img`，由中心仓库 bundle 清单／安装器校验。p2 为 ext4、卷标 `ubuntu-root`，见[完整布局](https://github.com/youzjuzi/dby-w09-linux/blob/main/docs/architecture.md)。无载荷菜单为 Ubuntu／Reboot to HarmonyOS／Power off；带载荷时在关机前加入 TWRP。音量键移动、电源键确认，默认 5 秒后进入 Ubuntu。固定菜单不含 Quit，ESC 与无效快捷键不选择动作。十二补丁 TWRP 版于 2026-11-03 在一台平板上观察到四项菜单、Ubuntu、回鸿蒙、TWRP 与触摸、关机可用（**R 用户观察**）；中性版本后缀的默认无载荷版亦有同一平板 2026-11-03 的短时观察（**R**），范围见上方当前产物节。

## 存储边界与限制

源码写门禁（O）保持 SD 只读；内部存储例外仅在核对 `boot-recovery` 及 NUL 终止字节后清 `misc` 前 32 字节，再读回验证。Linux `reboot recovery` 通过 PON 重启原因进入、misc 命令区 32 字节全零时，U-Boot 不写入也不同步 misc，直接继续；其它命令仍拒绝。MISC 结果在菜单／失败画面重显，拒绝未知命令时仅显示这 32 字节的十六进制。实机(R,一台平板,2026-11-17,TWRP 版):PON 进入显示 `MISC NO COMMAND` 并出菜单;按键进入仍为 `MISC CLEARED OK`;回鸿蒙不回环。适配其他设备前须核对板级分区／帧缓冲数据；字符串碰巧匹配不证明任意分区布局安全。详见[技术说明](docs/how-it-works.md)（英语）。

U-Boot 占用 Recovery 时无法恢复出厂设置，操作前先还原已校验的原厂 Recovery；不刷其他内部存储分区。修改镜像的硬件接受结果限于记录中的已解锁设备，不提供原厂镜像或其他固件兼容承诺。

本项目是独立、非官方的设备移植工作，与 Huawei／HarmonyOS／MatePad、Canonical/Ubuntu、Qualcomm 或 TeamWin 无关联，未获其认可或赞助；相关名称和商标属于各自权利人。不提供厂商固件，不保证其他设备或固件兼容。

需要已经解锁的 Bootloader。刷写会替换 Recovery，修改镜像不匹配原 AVB 摘要；错误镜像或操作可能导致无法启动或无法进入 Recovery。刷前先保留并核对自己的原厂回退镜像，恢复出厂前先刷回原厂 Recovery。写卡会清除所选 SD 卡数据。软件按现状提供，无担保。详见上方中心仓库安装指南。

补丁按各目标文件适用许可处理，见[逐补丁清单与例外](THIRD_PARTY.md)，见 [LICENSE](LICENSE)、[致谢](ACKNOWLEDGEMENTS.md)、[贡献](CONTRIBUTING.md)、[安全政策](SECURITY.md)。工具不授予原厂镜像数据的再分发权。

## 可选内置 TWRP 载荷

本次使用的 TWRP 输入由设备所有者从社区个人提供的下载取得，是面向本机型的第三方镜像，并非 TeamWin 官方发布。其构建者、源码对应关系及构建方式未经独立核实，本项目不对该镜像的许可证、完整来源或安全性作断言。SHA-256 仅确认使用的是同一份文件，不证明它安全或可信。选择 TWRP 会在早期启动阶段运行第三方恢复环境，该环境能够访问内部存储，需由所有者自行判断信任。TWRP 镜像与原厂 Recovery 均不在仓库中分发，仅供所有者自行使用。启用 TWRP 的构建会将压缩后的原厂 Recovery 内核内嵌到 u-boot.bin；该 u-boot.bin 及由其生成的 Recovery 镜像含厂商内容，不得作为本项目二进制发布。工具和引导代码的开源许可证不授予这些载荷的再分发权。本仓库不是通用 TWRP 安装教程。

自行提供原厂 Android v2 recovery 与仅含 ramdisk 的 Android v0 TWRP 镜像。本库不分发厂商二进制或身份头文件。先独立核实输入哈希，再在仓库外生成私有载荷：

```sh
python3 tools/prepare-twrp-payload.py \
  --stock-recovery /path/to/stock-recovery.img --twrp /path/to/twrp.img \
  --expect-stock-sha256 "$STOCK_SHA256" --expect-twrp-sha256 "$TWRP_SHA256" \
  --out-dir /path/to/new-payload
JOBS=8 sh build.sh /path/to/u-boot-2026.10.tar.gz \
  /path/to/new-source /path/to/new-output /path/to/new-payload
```

可选第四参数启用 `CONFIG_DBY_TWRP`；省略时保留三项菜单。两种模式均严格比较基础配置，并单独检查新增选项。生成文件在不同输出目录下逐字节一致；汇编里的 `DBY_STOCK_PAYLOAD` 宏在构建时展开为绝对路径。生成输入与最终固件须留在私有目录。

TWRP 动作在重定位前保留上一级引导器的 FDT 与完整 initrd，校验内置内核和预期 ramdisk 身份后调用标准 `booti`，不进行存储 I/O。校验失败或启动返回时显示阶段与原因，等待 15 秒后沿鸿蒙菜单项的 PSCI 路径复位。设备原有 recovery ramdisk 必须已含匹配的 TWRP；本构建不安装它。TWRP 内核接管后能够访问内部存储。2026-11-03 的 TWRP 版与新版本串候选各有上述限定范围的 R 用户观察；主机测试本身不代表 TWRP 可用。
