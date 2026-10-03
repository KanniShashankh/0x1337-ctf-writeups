# Shiny Hunter

- **Category:** Crypto / Misc (Pokémon Gen 3 RNG reversing)
- **Flag:** `0x1337{s34l3d_w17h1n_m4r1n3_c4v3}`
- **Files:** [`files/trainer_info.txt`](files/trainer_info.txt), [`files/message.txt`](files/message.txt)
- **Solver:** [`solve.py`](solve.py)

## Challenge

> You're the best shiny hunter in the Hoenn region [...] the message can only be decoded using the product of your Secret ID (whatever that is), and the Pokemon ID of your shiny Rayquaza [...]
>
> Note- As Secret IDs that have the same quotient when divided by 8 are functionally the same, use the Secret ID that is divisible by 8.

`trainer_info.txt` gives Trainer ID `50032` and a shiny Rayquaza: Hasty nature, IVs `6/9/14/8/3/18` (HP/Atk/Def/SpA/SpD/Spe), stationary legendary in a single encounter slot. `message.txt` is 33 bytes of hex ciphertext.

## Background

- Gen 3 (Ruby/Sapphire/Emerald) uses a 32-bit LCG: `s = s * 0x41C64E6D + 0x6073 mod 2^32`. Each call returns `s >> 16`.
- Stationary encounters use **Method 1**, four consecutive calls:
  1. PID low 16 bits
  2. PID high 16 bits
  3. IV word 1: HP, Atk, Def (5 bits each, bit 15 unused)
  4. IV word 2: Spe, SpA, SpD
- Nature is `PID % 25`. Hasty is index 11.
- Shiny check: `TID ^ SID ^ PID_high ^ PID_low < 8`.

## Solution

1. Pack the IVs into the two IV words: `iv1 = HP | Atk<<5 | Def<<10`, `iv2 = Spe | SpA<<5 | SpD<<10`.
2. The LCG state at the IV1 call has its top 16 bits known (except unused bit 15), so brute-force the low 16 bits: 2^17 candidates. Keep states whose next output, masked to 15 bits, equals `iv2`.
3. Step the LCG backwards twice (inverse: `s = s * 0xEEB9EB65 + 0x0A3561A1`) to get PID high, then PID low.
4. Filter on `PID % 25 == 11` (Hasty). Exactly one candidate survives: **PID = `0xFD1ACDC5`**. Methods 2 and 4 give no match, which confirms Method 1.
5. Shiny condition gives the SID up to its low 3 bits: `50032 ^ 0xFD1A ^ 0xCDC5 = 0xF3AF` (62383). Any SID sharing the upper 13 bits is shiny, which is the challenge's "same quotient when divided by 8". Clearing the low 3 bits gives **SID = 62376** (`0xF3A8`).
6. Key = `62376 * 0xFD1ACDC5 = 264872963672136` = `0xF0E68AE90848` (6 bytes).
7. XOR the ciphertext with the 6 key bytes, big-endian, repeating:

```
$ python3 solve.py
PID=0xfd1acdc5 SID=62376 key=264872963672136 (f0e68ae90848)
0x1337{s34l3d_w17h1n_m4r1n3_c4v3}
```

## Lessons

- Gen 3 IVs leak 30 of the 32 LCG state bits, so recovering the PID from a known spread is instant.
- The Secret ID is the hidden half of the trainer ID. The shiny check only pins its upper 13 bits, hence the "divisible by 8" note.
- Encounter type picks the RNG method. "Stationary, single slot" means Method 1 with no encounter-slot or level calls in between.
- The key is a raw big-endian integer, not its decimal string. Try both encodings when a challenge says "use the number".
- The flag refers to Marine Cave, where Kyogre sleeps in Emerald.
