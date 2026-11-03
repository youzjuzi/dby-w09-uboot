#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic tests for tools/pack-recovery.py. No vendor data is used."""
import gzip
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'pack_recovery', Path(__file__).resolve().parents[1] / 'tools' / 'pack-recovery.py')
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
PAGE = pr.PAGE


def make_base(kernel=b'K' * 5000, ramdisk=b'R' * 7000, dtbo=b'O' * 3000, dtb=b'D' * 2000,
              coverage=64 * PAGE, total=80 * PAGE):
    h = bytearray(PAGE)
    h[:8] = b'ANDROID!'
    struct.pack_into('<I', h, 8, len(kernel))
    struct.pack_into('<I', h, 16, len(ramdisk))
    struct.pack_into('<I', h, 36, PAGE)
    struct.pack_into('<I', h, 40, 2)
    dtbo_off = PAGE + pr.align(len(kernel)) + pr.align(len(ramdisk))
    struct.pack_into('<IQ', h, 1632, len(dtbo), dtbo_off)
    struct.pack_into('<I', h, 1644, pr.HEADER_SIZE)
    struct.pack_into('<I', h, 1648, len(dtb))
    h[576:596] = pr.image_id([kernel, ramdisk, b'', dtbo, dtb])
    body = b''.join(p + bytes(pr.align(len(p)) - len(p)) for p in (kernel, ramdisk, dtbo, dtb))
    img = bytearray(bytes(h) + body)
    img += bytes(total - len(img))
    img[-64:-60] = b'AVBf'
    struct.pack_into('>Q', img, total - 52, coverage)
    return bytes(img), coverage


class PackRecovery(unittest.TestCase):
    def test_original_kernel_roundtrip_is_identical(self):
        base, _ = make_base()
        self.assertEqual(pr.assemble(base, pr.parse(base)[0])[0], base)

    def test_replacement_keeps_other_segments_and_tail(self):
        base, coverage = make_base()
        new = gzip.compress(b'x' * 9000, mtime=0)
        out, end, cov = pr.assemble(base, new)
        self.assertEqual(len(out), len(base))
        self.assertEqual(out[coverage:], base[coverage:])
        kernel, ramdisk, dtbo, dtb, _ = pr.parse(out)
        old = pr.parse(base)
        self.assertEqual((kernel, ramdisk, dtbo, dtb), (new, old[1], old[2], old[3]))

    def test_rejects_oversized_kernel(self):
        base, coverage = make_base(coverage=16 * PAGE)
        with self.assertRaises(ValueError):
            pr.assemble(base, bytes(coverage))

    def test_rejects_corrupt_header_id(self):
        base, _ = make_base()
        bad = bytearray(base)
        bad[580] ^= 1
        with self.assertRaises(ValueError):
            pr.parse(bytes(bad))

    def test_rejects_other_versions(self):
        base, _ = make_base()
        bad = bytearray(base)
        struct.pack_into('<I', bad, 40, 1)
        with self.assertRaises(ValueError):
            pr.parse(bytes(bad))


if __name__ == '__main__':
    unittest.main()
