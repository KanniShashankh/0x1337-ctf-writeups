#!/usr/bin/env python3
"""Rebuild the orc flag from the PyInstaller-extracted doom.pyc and DOOM.wad.

Prereqs:
  tail -c +1324033 o.scr > a.rar && bsdtar -xf a.rar          # RAR5 SFX overlay
  python3 pyinstxtractor.py doom.exe                          # -> doom.exe_extracted/
Run with python3.13, since doom.pyc is 3.13 bytecode.
"""
import marshal
import re
import struct
import sys

base = sys.argv[1] if len(sys.argv) > 1 else "doom.exe_extracted"

# Part 2: zero-width binary (U+200B=0, U+200C=1) hidden in a string constant in doom.pyc
code = marshal.loads(open(f"{base}/doom.pyc", "rb").read()[16:])
blob = b""
def walk(c):
    global blob
    for k in c.co_consts:
        if hasattr(k, "co_code"):
            walk(k)
        elif isinstance(k, str) and "​" in k:
            bits = "".join("0" if ch == "​" else "1" for ch in k if ch in "​‌")
            blob += bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) - 7, 8))
walk(code)
tail_part = re.search(rb"0x1337\{(_4bs0[^}]*\})_27\}", blob).group(1)

# Part 1: text appended after the WAD directory, padded with random [a-z0-9]
wad = open(f"{base}/DOOM.wad", "rb").read()
_, n, off = struct.unpack("<4sii", wad[:12])
head_part = re.search(rb"0x1337\{[0-9a-z_]*_in", wad[off + 16 * n:]).group(0)

print((head_part + tail_part).decode())
