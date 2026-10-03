#!/usr/bin/env python3
"""Build the fixed boot program for Processor of Errors and run it on the gate-level sim.

Usage: python3 solve.py <dir containing cpu and data.hex>
Needs iverilog/vvp. On macOS with Homebrew icarus-verilog 13, the vvp header and
VPI paths in `cpu` are patched into `cpu2` automatically.
"""
import os, re, shutil, subprocess, sys

def LI(rd, imm): return 0x1000 | rd << 9 | imm
def R(op, rd, a, b=0): return op << 12 | rd << 9 | a << 6 | b << 3
def OUT(r): return 0xA000 | r << 6
def BNE(a, b, off): return 0x8000 | a << 9 | b << 6 | (off & 63)
SUB, XOR, LD = 3, 4, 6

prog = [
    LI(0, 0xF0), R(LD, 3, 0),         # r3 = key seed (0x3c)
    LI(0, 0xF1), R(LD, 2, 0),         # r2 = length (0x30)
    LI(1, 0),                         # r1 = index
    LI(4, 0xFF),                      # -1 (ADD is broken, use SUB)
    LI(5, 0xF9),                      # -7
    R(LD, 6, 1),                      # loop: r6 = dmem[r1]
    R(SUB, 1, 1, 4),                  # r1 += 1, also fills the load-delay gap
    R(XOR, 7, 6, 3),                  # r7 = r6 ^ key
    OUT(7),
    BNE(1, 2, -4),                    # back to loop
    R(SUB, 3, 3, 5),                  # delay slot: key += 7
    0,                                # HALT
]
prog += [0] * (32 - len(prog))

d = sys.argv[1] if len(sys.argv) > 1 else '.'
open(os.path.join(d, 'prog.hex'), 'w').write('\n'.join('%04x' % w for w in prog) + '\n')

cpu = os.path.join(d, 'cpu2')
if not os.path.exists(cpu):
    src = open(os.path.join(d, 'cpu')).read()
    v = subprocess.run(['vvp', '-V'], capture_output=True, text=True)
    ver = re.search(r'runtime version (\d+\.\d+)', v.stdout + v.stderr)
    if ver:
        src = re.sub(r':ivl_version "[^"]*"', ':ivl_version "%s (stable)"' % ver.group(1), src, count=1)
    libdir = os.path.join(os.path.dirname(os.path.dirname(shutil.which('vvp'))), 'lib', 'ivl') + '/'
    src = src.replace('/usr/lib/x86_64-linux-gnu/ivl/', libdir)
    open(cpu, 'w').write(src)

print(subprocess.run(['vvp', '-n', 'cpu2'], cwd=d, capture_output=True, text=True).stdout)
