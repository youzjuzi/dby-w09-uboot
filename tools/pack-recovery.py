#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replace the kernel segment of an owner-supplied Android boot image (v2).

Offline host tool: reads two files, writes one new file. It never touches a device.

The kernel segment of the output is `gzip -n` of the supplied u-boot.bin. The ramdisk,
recovery_dtbo and dtb segments, the total length and the AVB footer region are kept
byte for byte. Only kernel_size, recovery_dtbo_offset and the header id (SHA-1) change.
The retained AVB descriptors do not authenticate the new kernel; acceptance depends on
the bootloader being unlocked.

Before writing, the tool repacks the base image's own kernel and requires the result
to be byte-identical to the base. A base that fails this self-check is rejected.
"""
import argparse
import hashlib
import struct
import subprocess
import sys
import zlib
from pathlib import Path

PAGE = 4096
HEADER_SIZE = 1660


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def align(n):
    return (n + PAGE - 1) // PAGE * PAGE


def u32(data, off):
    return struct.unpack_from('<I', data, off)[0]


def image_id(parts):
    h = hashlib.sha1()
    for part in parts:
        h.update(part)
        h.update(struct.pack('<I', len(part)))
    return h.digest()


def parse(base):
    """Return (kernel, ramdisk, recovery_dtbo, dtb, avb_coverage) of a v2 boot image."""
    if base[:8] != b'ANDROID!' or u32(base, 40) != 2:
        raise ValueError('not an Android boot image v2')
    if u32(base, 36) != PAGE or u32(base, 1644) != HEADER_SIZE:
        raise ValueError('unexpected page size or header size')
    kernel_size, ramdisk_size, second_size = u32(base, 8), u32(base, 16), u32(base, 24)
    if second_size:
        raise ValueError('second-stage segment is not supported')
    dtbo_size, dtbo_offset = struct.unpack_from('<IQ', base, 1632)
    dtb_size = u32(base, 1648)
    ramdisk_offset = PAGE + align(kernel_size)
    if dtbo_offset != ramdisk_offset + align(ramdisk_size):
        raise ValueError('recovery_dtbo offset does not follow the ramdisk')
    dtb_offset = dtbo_offset + align(dtbo_size)
    if base[-64:-60] != b'AVBf':
        raise ValueError('AVB footer not found')
    coverage = struct.unpack_from('>Q', base, len(base) - 52)[0]
    if dtb_offset + align(dtb_size) > coverage:
        raise ValueError('segments exceed the AVB-covered area')
    kernel = base[PAGE:PAGE + kernel_size]
    ramdisk = base[ramdisk_offset:ramdisk_offset + ramdisk_size]
    dtbo = base[dtbo_offset:dtbo_offset + dtbo_size]
    dtb = base[dtb_offset:dtb_offset + dtb_size]
    if image_id([kernel, ramdisk, b'', dtbo, dtb]) != base[576:596]:
        raise ValueError('header id does not match the segments')
    return kernel, ramdisk, dtbo, dtb, coverage


def assemble(base, kernel):
    old_kernel, ramdisk, dtbo, dtb, coverage = parse(base)
    header = bytearray(base[:PAGE])
    struct.pack_into('<I', header, 8, len(kernel))
    struct.pack_into('<Q', header, 1636, PAGE + align(len(kernel)) + align(len(ramdisk)))
    header[576:596] = image_id([kernel, ramdisk, b'', dtbo, dtb])
    body = b''.join(p + bytes(align(len(p)) - len(p)) for p in (kernel, ramdisk, dtbo, dtb))
    end = PAGE + len(body)
    if end > coverage:
        raise ValueError('new kernel does not fit before the AVB footer region')
    return bytes(header) + body + bytes(coverage - end) + base[coverage:], end, coverage


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', type=Path, required=True, help='stock recovery.img (owner-supplied)')
    ap.add_argument('--kernel', type=Path, required=True, help='u-boot.bin')
    ap.add_argument('--out', type=Path, required=True, help='new file; must not exist')
    ap.add_argument('--expect-base-sha256', help='abort unless the base matches this digest')
    args = ap.parse_args()

    base = args.base.read_bytes()
    if args.expect_base_sha256 and sha256(base) != args.expect_base_sha256:
        sys.exit('base image digest mismatch')
    old_kernel = parse(base)[0]
    repacked, _, _ = assemble(base, old_kernel)
    if repacked != base:
        sys.exit('self-check failed: repacking the original kernel is not byte-identical')

    raw = args.kernel.read_bytes()
    if raw[56:60] != b'ARM\x64':
        sys.exit('kernel input is not an arm64 Image-format binary')
    kernel = subprocess.run(['gzip', '-n', '-c', str(args.kernel)],
                            check=True, capture_output=True).stdout
    if zlib.decompress(kernel, 31) != raw:
        sys.exit('gzip round-trip failed')
    packed, end, coverage = assemble(base, kernel)
    assert len(packed) == len(base) and packed[coverage:] == base[coverage:]

    with args.out.open('xb') as f:
        f.write(packed)
    print('output        ', args.out)
    print('bytes         ', len(packed))
    print('sha256        ', sha256(packed))
    print('base sha256   ', sha256(base))
    print('kernel gzip   ', len(kernel), 'bytes, raw sha256', sha256(raw))
    print('free before AVB region', coverage - end, 'bytes')
    print('note: original AVB descriptors retained; the new kernel is not authenticated')


if __name__ == '__main__':
    main()
