#!/usr/bin/env python3
"""Nested Matryoshka solver: IEND tail -> repaired JPEG -> EXIF hex -> repeating-XOR (key 'cixin')."""
import re
import struct
import sys

src = sys.argv[1] if len(sys.argv) > 1 else "files/challenge.png"
data = open(src, "rb").read()

# Layer 1: everything after the PNG IEND chunk.
pos, tail = 8, b""
while pos + 8 <= len(data):
    length = struct.unpack(">I", data[pos:pos + 4])[0]
    ctype = data[pos + 4:pos + 8]
    if ctype == b"IEND":
        tail = data[pos + 12:]
        break
    pos += 12 + length
print(f"after IEND: {len(tail)} bytes")

# Layer 2: a JPEG whose SOI/APP0 markers were zeroed out — restore them.
assert tail[:8] == b"\x00\x00\x00\x00\x00\x10\x4a\x46\x49\x46"[:8], "unexpected tail header"
jpeg = b"\xff\xd8\xff\xe0" + tail[4:]
print(f"repaired JPEG: {len(jpeg)} bytes")

# Layer 3: a long hex string in the EXIF ImageDescription.
hexs = max(re.findall(rb"[0-9a-fA-F]{200,}", jpeg), key=len)
blob = bytes.fromhex(hexs.decode())
print(f"decoded payload: {len(blob)} bytes")

# Layer 4: repeating-key XOR — key 'cixin', recovered via coincidence + column frequency.
key = b"cixin"
plain = bytes(c ^ key[i % len(key)] for i, c in enumerate(blob))
print(plain.decode())

flag = re.search(r"0x1337\{[^}]*\}", plain.decode()).group()
assert flag == "0x1337{0nly_4dv4nc3}"
print("FLAG:", flag)
