#!/usr/bin/env python3
"""Simulate the Yosys gate-level netlist in Python and DFS the 15-byte key.

Usage: python3 solve.py [path/to/netlist.v]
"""
import re
import sys

src = open(sys.argv[1] if len(sys.argv) > 1 else "netlist.v").read()


def expand(x):
    m = re.match(r"(\w+)\[(\d+):(\d+)\]", x)
    if m:
        return [f"{m[1]}[{i}]" for i in range(int(m[2]), int(m[3]) - 1, -1)]
    return [x]


# Continuous assignments, including the one concatenation at the end.
assigns = []
for m in re.finditer(r"assign (.+?) = (.+?);", src):
    lhs, rhs = m[1].strip(), m[2].strip()
    if lhs.startswith("{"):
        L = sum((expand(x.strip()) for x in lhs.strip("{} ").split(",")), [])
        R = sum((expand(x.strip()) for x in rhs.strip("{} ").split(",")), [])
        assigns += zip(L, R)
    else:
        assigns.append((lhs, rhs))


def to_py(e):
    e = re.sub(r"1'h([01])", r"\1", e)
    e = re.sub(r"(\w+)\[(\d+)\]", r"V['\1[\2]']", e)
    e = re.sub(r"(?<!['\w\[])(_\d+_|rst|valid)(?![\w\[])", r"V['\1']", e)
    return e.replace("~", "1^")


code = [(lhs, compile(to_py(rhs), lhs, "eval")) for lhs, rhs in assigns]

# Flops: (q, reset value or None, enable or None, d)
flops = []
for m in re.finditer(r"always @\(posedge clk\)\s*(if \(rst\).*?;\s*else.*?;|[^i].*?;)", src, re.S):
    b = m[1]
    mm = re.match(r"if \(rst\) (\S+) <= 1'h([01]);\s*else if \((\w+)\) \S+ <= (\S+);", b)
    if mm:
        flops.append((mm[1], int(mm[2]), mm[3], mm[4]))
    else:
        q, d = [x.strip().rstrip(";") for x in b.split("<=")]
        flops.append((q, None, None, d))


def comb(state, inputs):
    V = dict(state)
    V.update(inputs)
    changed = True
    while changed:
        changed = False
        for lhs, c in code:
            try:
                v = eval(c, {"V": V}) & 1
            except KeyError:  # operand not computed yet
                continue
            if V.get(lhs) != v:
                V[lhs] = v
                changed = True
    return V


def step(state, rst, valid, byte):
    inputs = {"rst": rst, "valid": valid}
    inputs.update({f"data_in[{i}]": (byte >> i) & 1 for i in range(8)})
    V = comb(state, inputs)
    nxt = dict(state)
    for q, rv, en, d in flops:
        if rv is None:
            nxt[q] = V[d]
        elif rst:
            nxt[q] = rv
        elif V[en]:
            nxt[q] = V[d]
    return nxt


state = step({q: 0 for q, *_ in flops}, 1, 0, 0)  # reset
state = step(state, 0, 0, 0)                       # idle cycle

FAIL = "_332_[1]"  # FSM sink state on a wrong byte


def dfs(state, prefix):
    if len(prefix) == 15:
        if step(state, 0, 0, 0)["unlocked"]:
            yield bytes(prefix)
        return
    for b in range(256):
        nxt = step(state, 0, 1, b)
        if not nxt[FAIL]:
            yield from dfs(nxt, prefix + [b])


for key in dfs(state, []):
    print(key.decode())
