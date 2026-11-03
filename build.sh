#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Project host recipe for the pinned upstream archive and project patch series.
# Offline build: pinned upstream U-Boot tarball + patches/ + board/ + config/.
set -eu
if [ "$#" -ne 3 ] && [ "$#" -ne 4 ]; then
    echo "Usage: $0 UPSTREAM_TARBALL SOURCE_DIR BUILD_DIR [PAYLOAD_DIR]" >&2
    echo "  UPSTREAM_TARBALL: u-boot-v2026.10.tar.gz (SHA-256 is checked)" >&2
    echo "  SOURCE_DIR, BUILD_DIR: must not exist yet" >&2
    exit 2
fi
recipe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
archive=$(realpath -- "$1")
source_dir=$(realpath -m -- "$2")
build_dir=$(realpath -m -- "$3")
[ ! -e "$source_dir" ] && [ ! -e "$build_dir" ] || { echo 'Output paths must not exist' >&2; exit 1; }
printf '%s  %s\n' f943a88389c8fd70a6b0d061a88267465e143c7ca6ea2b75837ab20f5b60c739 "$archive" | sha256sum -c -
mkdir -p -- "$source_dir" "$build_dir"
tar -xzf "$archive" --strip-components=1 -C "$source_dir"
for patch_file in "$recipe"/patches/*.patch; do
    patch --batch --fuzz=0 -d "$source_dir" -p1 < "$patch_file"
done
for name in framebuffer-private.dtsi sd-private.dtsi ufs-private.dtsi; do
    cp -- "$recipe/board/$name" "$source_dir/arch/arm/dts/$name"
done
cp -- "$recipe/board/partition-private.h" "$source_dir/include/misc-partition-private.h"
cp -- "$recipe/config/dby-w09.config" "$build_dir/.config"
# Check the new option separately; retain exact comparison of the base.
if [ "$#" -eq 4 ]; then
    payload=$(realpath -- "$4")
    for name in stock-kernel.lzma dby-twrp-data.h dby-stock.S; do
        cp -- "$payload/$name" "$source_dir/cmd/$name"
    done
    printf '\nCONFIG_DBY_TWRP=y\n' >> "$build_dir/.config"
    expected_twrp=CONFIG_DBY_TWRP=y
else
    expected_twrp='# CONFIG_DBY_TWRP is not set'
fi
export SOURCE_DATE_EPOCH=1791417600 KBUILD_BUILD_USER=builder KBUILD_BUILD_HOST=offline
make -C "$source_dir" O="$build_dir" CROSS_COMPILE="${CROSS_COMPILE:-aarch64-linux-gnu-}" olddefconfig
[ "$(grep -E '^(CONFIG_DBY_TWRP=|# CONFIG_DBY_TWRP is not set$)' "$build_dir/.config")" = "$expected_twrp" ]
sed '/^CONFIG_DBY_TWRP=/d; /^# CONFIG_DBY_TWRP is not set$/d' "$build_dir/.config" > "$build_dir/base.config"
cmp -- "$recipe/config/dby-w09.config" "$build_dir/base.config"
make -C "$source_dir" O="$build_dir" CROSS_COMPILE="${CROSS_COMPILE:-aarch64-linux-gnu-}" KAFLAGS="-DDBY_STOCK_PAYLOAD=\\\"$source_dir/cmd/stock-kernel.lzma\\\"" -j"${JOBS:-8}"
echo "Built: $build_dir/u-boot.bin"
