#!/usr/bin/env python3
"""Image Forensics (SpongeBob) solver: read the per-channel LSB plane of reality.png and pull the flag."""
import re
import sys

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "files/reality.png"
im = Image.open(src).convert("RGB")
px = list(im.getdata())

# The R, G and B LSB planes carry the same payload; the red channel is enough.
bits = [p[0] & 1 for p in px]
stream = bytes(
    int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) // 8 * 8, 8)
)

# 4-byte big-endian length header, then the flag text.
length = int.from_bytes(stream[:4], "big")
flag = stream[4:4 + length].decode()
assert length == 23 and flag == "0x1337{pr0cr4stin4t1on}"
print(flag)
