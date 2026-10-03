#!/usr/bin/env python3
"""Shiny Hunter solver: recover a Gen 3 Method 1 PID from IVs, derive the SID, decrypt."""
from pathlib import Path

M = 0xFFFFFFFF
nx = lambda s: (s * 0x41C64E6D + 0x6073) & M      # forward LCG
pv = lambda s: (s * 0xEEB9EB65 + 0x0A3561A1) & M  # reverse LCG

TID = 50032
HP, ATK, DEF, SPA, SPD, SPE = 6, 9, 14, 8, 3, 18
HASTY = 11

iv1 = HP | ATK << 5 | DEF << 10
iv2 = SPE | SPA << 5 | SPD << 10
ct = bytes.fromhex((Path(__file__).parent / "files/message.txt").read_text().strip())

for top in (iv1, iv1 | 0x8000):  # bit 15 of the IV word is unused
    for low in range(1 << 16):
        s = top << 16 | low  # state that produced IV word 1
        if (nx(s) >> 16) & 0x7FFF != iv2:
            continue
        hi_state = pv(s)
        hi, lo = hi_state >> 16, pv(hi_state) >> 16
        pid = hi << 16 | lo
        if pid % 25 != HASTY:
            continue
        sid = (TID ^ hi ^ lo) & 0xFFF8  # shiny: TID^SID^hi^lo < 8, pick SID divisible by 8
        key = (pid * sid).to_bytes(6, "big")
        pt = bytes(c ^ key[i % len(key)] for i, c in enumerate(ct))
        print(f"PID={pid:#010x} SID={sid} key={pid * sid} ({key.hex()})")
        print(pt.decode())
