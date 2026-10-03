# Processor of Errors

- **Category:** Reverse / Hardware
- **Author:** afoolishman
- **Flag:** `0x1337{my_c0mpute_not_c0mputing}`
- **Files:** [`files/processor_of_errors.zip`](files/processor_of_errors.zip), [`solve.py`](solve.py), [`fixed.hex`](fixed.hex)

## Challenge

> Our secure-boot chip runs chall.hex: it decrypts a boot phrase from data memory, and when the boot phrase comes out correctly the chip rewards you.
>
> chall.hex worked perfectly in our instruction-set emulator. On the real silicon it prints garbage and refuses to boot. Make it boot on the real chip.

The zip contains `ISA.md` (the datasheet for TinyCPU-2), `chall.hex` (the boot program), `data.hex` (256 bytes of data memory) and `cpu`, a compiled Icarus Verilog (`vvp`) gate-level simulation of the chip. The datasheet says it documents the *intended* ISA, "but the hardware is what actually runs". The CPU has eight 8-bit registers, a 5-bit PC and 32 words of instruction memory. A boot checker watches every write to `r7`.

## Solution

### 1. Decode the original program

| PC | Word | Instruction |
|----|------|-------------|
| 0 | `10f0` | `LI r0, 0xf0` |
| 1 | `6600` | `LD r3, [r0]` (key = `dmem[0xf0]` = `0x3c`) |
| 2 | `10f1` | `LI r0, 0xf1` |
| 3 | `6400` | `LD r2, [r0]` (length = `dmem[0xf1]` = `0x30`) |
| 4 | `1200` | `LI r1, 0` |
| 5 | `1801` | `LI r4, 1` |
| 6 | `1a07` | `LI r5, 7` |
| 7 | `6c40` | `LD r6, [r1]` |
| 8 | `4f98` | `XOR r7, r6, r3` |
| 9 | `a1c0` | `OUT r7` |
| a | `26e8` | `ADD r3, r3, r5` (key += 7) |
| b | `2260` | `ADD r1, r1, r4` |
| c | `82bb` | `BNE r1, r2, -5` (to PC 7) |
| d | `0000` | `HALT` |

Following the datasheet, the program XORs each of the 48 data bytes with a key that starts at `0x3c` and increases by 7 each byte. Doing that in Python prints `TinyCPU secure boot :: integrity check passed OK`, which is the phrase the checker expects.

### 2. Run the chip

The `cpu` file was built by Icarus 12.0 on Linux, but Homebrew installs 13.0. Two edits to a copy (`cpu2`) make it run on macOS:

- change the header `:ivl_version "12.0 (stable)"` to `13.0`
- change the VPI module paths from `/usr/lib/x86_64-linux-gnu/ivl/` to `/opt/homebrew/lib/ivl/`

With the original program, the chip prints only `<` and then `[ACCESS DENIED]`. `0x3c` is the key itself, which means `r6` was still `0` when the XOR ran.

### 3. Test each instruction on the hardware

I wrote short test programs that print their results with `OUT` and ran them in parallel against the sim:

- **LI, SUB, XOR, AND, ST, JMP, NOP**: match the datasheet.
- **ADD**: wrong whenever bits 0 to 3 produce a carry. `0x0f+0x01 = 0x00`, `0x08+0x08 = 0x00`, `0x3c+0x07 = 0x33`, `0xff+0x01 = 0xf0`. Sums without that carry, such as `0x44+0x20` and `0x10+0x10`, come out right. The carry from bit 3 into bit 4 is never connected, so the chip behaves like two separate 4-bit adders.
- **LD**: the loaded value lands one instruction late. `LD r3,[r1]` followed directly by `OUT r3` prints the old `r3`. With one `NOP` in between, it prints the right value.
- **BNE**: the comparison and the target (`pc + off6`) are correct, but the instruction after the `BNE` always runs, whether or not the branch is taken (a delay slot). `JMP` does not have one.

These three bugs explain the output. The `XOR` reads `r6` before the load has landed. `ADD` breaks the key and the index. The `HALT` after the `BNE` sits in the delay slot, so it runs on the first pass and the chip stops after one character.

### 4. Rewrite the program for the real chip

- Add with `SUB`, which works: `+1` becomes `SUB` of `0xff`, `+7` becomes `SUB` of `0xf9`.
- Put a useful instruction (the index increment) between the `LD` and the `XOR` that reads the loaded value.
- Use the `BNE` delay slot for the key update, which also keeps `HALT` out of it.
- Write to `r7` only the bytes of the phrase, because the checker sees every write.

```
10f0  LI  r0, 0xf0
6600  LD  r3, [r0]      ; key
10f1  LI  r0, 0xf1
6400  LD  r2, [r0]      ; length
1200  LI  r1, 0
18ff  LI  r4, 0xff      ; -1
1af9  LI  r5, 0xf9      ; -7
6c40  LD  r6, [r1]      ; loop:
3320  SUB r1, r1, r4    ; r1 += 1 (fills the load gap)
4f98  XOR r7, r6, r3
a1c0  OUT r7
8287  BNE r1, r2, -4    ; to loop
36e8  SUB r3, r3, r5    ; delay slot: key += 7
0000  HALT
```

```
$ python3 solve.py <unzipped dir>
TinyCPU secure boot :: integrity check passed OK
[UNLOCKED]
0x1337{my_c0mpute_not_c0mputing}
```

`solve.py` writes `prog.hex`, patches `cpu` into `cpu2` for the installed `vvp`, and runs the sim.

## Lessons

- When the netlist is large and you are told "the hardware is truth", test it as a black box. Small tests of each instruction found all three bugs without reading the 50k-line `vvp` file.
- Choose test values that exercise carries across the nibble boundary. A simple test like `1+1` passes even on a broken adder.
- Load delays and branch delay slots are classic hardware behaviours that an ISA emulator leaves out. Test for them first whenever a program works in the emulator but fails on the hardware.
- An old `.vvp` file can still run on a newer Icarus runtime after you edit the version header and the VPI paths.
