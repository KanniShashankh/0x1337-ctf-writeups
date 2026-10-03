# Arthur's Redstone Contraption

- **Category:** Reverse / Hardware (Minecraft redstone)
- **Points:** Level 2 special
- **Author:** sans (map by ArthurX256)
- **Flag:** `0x1337{a91f}`
- **Files:** [`files/arthurs_redstone_contraption.zip`](files/arthurs_redstone_contraption.zip), [`files/output.txt`](files/output.txt), [`solve.py`](solve.py)

## Challenge

> ArthurX256 built a redstone contraption. sans, for reasons known only to sans, decided to put something important into it. He turned the machine on, waited for a while, and then recorded what it was doing. Figure out how Arthur's machine works and recover what sans put into it.
>
> Submit the recovered value as lowercase hex: `0x1337{<hex_value>}`.

Free hint (0 points): *sans remembers pressing the note block 2^6 times.*

The zip contains `map.zip`, a Minecraft Java 1.21.11 world named "Linear-feedback shift register", and `output.txt` with 32 bits:

```
00110101100000001010000110100111
```

## Solution

### 1. Dump the world

No NBT tools were installed, so I parsed the Anvil region files directly: sector table, then zlib, then `nbtlib`. I decoded each section's paletted block states. Apart from the sandstone terrain, the build is about 800 blocks inside x 8..17, y 66..98, z 22..29. It uses redstone dust, repeaters, subtract-mode comparators, wall torches, target blocks, 16 redstone lamps, two observers, two note blocks and two signs: "shift" at (17,69,22) and "reset (need to input seed manually)" at (17,69,29). The saved world is in the reset state, with every lamp off.

### 2. Reverse the machine

- **16 identical cells** stacked at odd y = 67, 69, ..., 97, with a lamp at (12, y, 29) for each. Call the bottom cell (y=67) c0 and the top cell (y=97) c15.
- **Cell = torch latch.** Dust at (14,y,24) feeds target (15,y,24), torch (15,y,25), dust (15,y,26) and target (14,y,26). The torches (14,y,25) and (13,y,26) hold the bit. Clock line B, a glass staircase at z=28 that feeds the repeaters at (14,y,27), clears the latch. While B is high the latch is transparent to its input.
- **Shift direction is down.** On each even layer, a subtract comparator at (14,y,23) reads the wool under the latch dust of the cell above. Its output is routed into the repeater (13,y-1,23) of the cell below. The comparator's side input is clock line A: a torch inverter at (16,68,25) feeds a staircase at x=16, z=22/23. So data only passes while A is low, during a press.
- **Clock.** Right-clicking the shift note block changes its pitch, which fires observer (17,68,23). The pulse drops line A, opening the data path, and raises line B, which reloads the latches. The reset note block fires observer (17,68,28), which raises B only, clearing every cell. That is why the sign says to input the seed manually.
- **Feedback.** Taps leave the cell column at y=67 (dust (11,67,26)), y=73 (repeater (11,73,28)), y=75 (repeater (11,75,25)) and y=79 (repeater (11,79,28)). They feed three comparator-pair XOR gates at y=73, 79 and 81. The result climbs a glass staircase at x=9/10, z=27 up to y=96. There it is gated by line A at (12,97,24) and enters the top cell's latch through repeater (13,97,24).

So one shift press does:

```
c[i]  <- c[i+1]                (i = 0..14)
c[15] <- c0 ^ c3 ^ c4 ^ c6
```

This is a 16-bit Fibonacci LFSR with feedback polynomial x^16 + x^13 + x^12 + x^10 + 1. The polynomial is not primitive; the cycle through the recorded state has length 21483.

### 3. Check against `output.txt`

Berlekamp-Massey on the 32 recorded bits gives linear complexity 16 and the recurrence o[i] = o[i-10] ^ o[i-12] ^ o[i-13] ^ o[i-16]. In state terms that is exactly c0 ^ c3 ^ c4 ^ c6. Any 32 bits fit some 16-bit LFSR, so BM alone proves nothing. What counts is that it matches the taps traced in the map, so `output.txt` is the bottom lamp stream of this machine.

### 4. Recover the seed

The first 16 recorded bits are the state at the moment recording started (c0..c15 = o[0..15]). The step is invertible:

```
prev c0 = c15 ^ c2 ^ c3 ^ c5,  prev c1..c15 = c0..c14
```

Without the hint, the wait is undetermined. Every state has exactly one predecessor, so each guess of "a while" gives a different seed. The hint fixes it at 2^6 = 64 presses. Stepping back 64 times and reading c0 as bit 0 gives `1111100010010101` (c0..c15), which is 0xa91f. Replaying forward checks it: 64 presses, then 32 more, reproduces `output.txt` exactly.

```
$ python3 solve.py
BM linear complexity 16 connection poly [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1]
0x1337{a91f}
```

Rejected before the hint: `ace0` (8 steps back, a coincidental "ACE" look-alike) and `01ac` (no wait).

## Lessons

- For redstone, parse the world into a block dump and trace signal flow by block state. Know the `facing` convention: a repeater or comparator's `facing` is its input side, and it outputs the opposite way. Glass staircases only carry signal upward. Dust powers the block it sits on.
- Berlekamp-Massey always fits 2L bits, so check its taps against the hardware before trusting it.
- An invertible LFSR loses no information, but "waited for a while" is still an unknown number of steps. When the data can't decide the step count, look for a hint before spending limited guesses.
- The bit order (bottom cell = LSB) follows the usual `lfsr >> 1` convention: the output bit is bit 0, and the feedback enters bit 15.
