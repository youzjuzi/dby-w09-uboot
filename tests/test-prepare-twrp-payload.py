#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
import gzip
import hashlib
import importlib.util
import lzma
from pathlib import Path
import struct
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('payload', Path(__file__).resolve().parents[1]/'tools/prepare-twrp-payload.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)

def images():
    raw = bytearray(4096); raw[56:60] = b'ARM\x64'
    struct.pack_into('<QQQ', raw, 8, 0x80000, 8192, 10)
    k = gzip.compress(raw, mtime=0); rd = gzip.compress(b'synthetic ramdisk'*200, mtime=0)
    b = bytearray(4096); b[:8] = b'ANDROID!'
    struct.pack_into('<I', b, 8, len(k)); struct.pack_into('<II', b, 36, 4096, 2)
    t = bytearray(4096); t[:8] = b'ANDROID!'
    struct.pack_into('<I', t, 16, len(rd)); struct.pack_into('<II', t, 36, 4096, 0)
    return b+k, t+rd, raw

class Payload(unittest.TestCase):
    def run_case(self, mutate=None, badsha=False, existing=False):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp); b,t,raw=images()
            if mutate: b,t=mutate(b,t)
            (d/'b').write_bytes(b); (d/'t').write_bytes(t)
            if existing: (d/'out').mkdir()
            args=(d/'b',d/'t',d/'out','0'*64 if badsha else p.digest(b),p.digest(t))
            if mutate or badsha or existing:
                with self.assertRaises(ValueError): p.prepare(*args)
            else:
                p.prepare(*args)
                p.prepare(d/'b',d/'t',d/'again',p.digest(b),p.digest(t))
                for f in (d/'out').iterdir(): self.assertEqual(f.read_bytes(),(d/'again'/f.name).read_bytes())
                z=(d/'out/stock-kernel.lzma').read_bytes()
                self.assertEqual(struct.unpack_from('<Q',z,5)[0],len(raw))
                self.assertEqual(lzma.decompress(z),raw)
    def test_roundtrip_determinism_and_nondefault_page(self): self.run_case()
    def test_wrong_sha(self): self.run_case(badsha=True)
    def test_existing_output(self): self.run_case(existing=True)
    def test_twrp_kernel(self):
        def mutate(b,t): struct.pack_into('<I',t,8,1); return b,t
        self.run_case(mutate)
    def test_non_arm64(self):
        def mutate(b,t):
            k=gzip.compress(b'invalid'*100,mtime=0);struct.pack_into('<I',b,8,len(k));return b[:4096]+k,t
        self.run_case(mutate)
    def test_bad_placement(self):
        def mutate(b,t):
            raw=bytearray(gzip.decompress(b[4096:]));struct.pack_into('<Q',raw,24,0)
            k=gzip.compress(raw,mtime=0);struct.pack_into('<I',b,8,len(k));return b[:4096]+k,t
        self.run_case(mutate)
    def test_truncated_ramdisk(self): self.run_case(lambda b,t:(b,t[:-2]))
if __name__=='__main__': unittest.main()
