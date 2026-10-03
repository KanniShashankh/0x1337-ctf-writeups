# based

- **Category:** Crypto / Misc
- **Author:** sans
- **Flag:** `0x1337{w0w_y0u_c0nn3ct3d_th3_d0ts_pr3tty_w3ll_g00d_j0b}`
- **Files:** [`files/based.zip`](files/based.zip) (contains `ciphertext.txt`, `clue.txt`), [`files/solve.py`](files/solve.py)

## Challenge

> The Base64 alphabet sets the order. How much of it you use is up to the
> number. Follow the order in the text file aswell.
>
> Flag format: `0x1337{flag}`
>
> Author: sans

`clue.txt` holds 17 numbered riddles; `ciphertext.txt` is a 78-character string
drawn from `A–Z` plus lowercase `a` and `b`:

```
aPNHBRQVKLBJPHRHCOZFWOLJABFAZCZIISHXIQYFDOTBXMTFIMOTQbFSBHRCAABMEYPRZWMZTIXaES
```

## Solution

1. **"The Base64 alphabet sets the order"** — a character's numeric value is its
   index in the standard Base64 alphabet (`A=0 … Z=25, a=26, b=27, …`). The
   ciphertext only uses values **0 through 27**, i.e. exactly the first 28
   symbols of the alphabet.
2. **"How much of it you use is up to the number"** — each riddle resolves to a
   well-known number, and that number is a **base** (the challenge is literally
   called *based*). The riddles:

   | # | Clue | Number |
   |---|------|--------|
   | 1 | The Poolrooms (Backrooms level) | 37 |
   | 2 | Venomoth (Pokédex #49) | 49 |
   | 3 | King's Indian Defense (ECO code E60) | 60 |
   | 4 | Iron (atomic number) | 26 |
   | 5 | Gold Block (Minecraft block ID) | 41 |
   | 6 | SCP-058 "Heart of Darkness" (the bovine-heart SCP) | 58 |
   | 7 | Bangladesh (ISO 3166-1 numeric code 050) | 50 |
   | 8 | SIGTERM (signal number) | 15 |
   | 9 | "Stop the Presses" (Dreamfall Chapters achievement, 15G) | 15 |
   | 10 | Michael Jordan | 23 |
   | 11 | Abraham Lincoln (16th president) | 16 |
   | 12 | SSH (port 22) | 22 |
   | 13 | `@` (ASCII code 64) | 64 |
   | 14 | Middle C (40th key of an 88-key piano) | 40 |
   | 15 | The women's-suffrage amendment | 19 |
   | 16 | Atlantic Avenue (Monopoly space 26) | 26 |
   | 17 | AAAA (DNS record type for IPv6) | **28** |

3. **Decode.** Treat the whole ciphertext as one big number whose digits are
   those Base64 values, and convert it in each candidate base (clue numbers
   below the maximum digit 27 can't represent the string at all), keeping the
   one that decodes to printable ASCII:

   ```python
   B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
   vals = [B64.index(c) for c in ciphertext]
   for base in candidate_bases:            # clue numbers, in file order
       n = 0
       for v in vals:
           n = n * base + v
       data = n.to_bytes((n.bit_length() + 7) // 8, "big")
       if all(32 <= b < 127 for b in data):
           print(base, data.decode())      # base 28 hits
   ```

   Every base produces binary noise except **base 28** — clue 17, `AAAA`, the
   DNS record type for IPv6:

   ```
   w0w_y0u_c0nn3ct3d_th3_d0ts_pr3tty_w3ll_g00d_j0b
   ```

4. **Flag:** `0x1337{w0w_y0u_c0nn3ct3d_th3_d0ts_pr3tty_w3ll_g00d_j0b}` —
   "wow, you connected the dots pretty well, good job".

## Dead ends

- **Indexing the alphabet**: spelling the flag directly with `B64[n]` per clue
  yields `kw7Zo5xOOWPV/nSZb`-style noise (including a literal `/` from
  `@` = 64), which is what gave the game away — CTF flags don't look like that.
- **Vigenère over Base64**: shifting the ciphertext characters by the clue
  numbers (cycled in file order) just scrambles them.
- **The lowercase `a`/`b` as segment markers**: they're simply digits 26 and 27
  of the base-28 number.

## Lessons

- *"How much of it you use"* is radix-speak: the number of usable alphabet
  symbols **is the base**.
- The digit range bounds the base from below (max digit 27 ⇒ base ≥ 28), and a
  printable-ASCII filter picks the right base instantly — no need to guess.
- When a challenge is named after a concept ("based"), the concept is usually
  the mechanism, not decoration.
