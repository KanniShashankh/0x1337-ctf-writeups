# Nested Matryoshka

- **Category:** Forensics / Stego
- **Author:** raghav aggarwal
- **Flag:** `0x1337{0nly_4dv4nc3}`
- **Files:** [`files/challenge.png`](files/challenge.png)

## Challenge

> An image was recovered from a suspect's system. Can you uncover what's inside?

`challenge.png` (828×1242) is a normal-looking picture with a pile of metadata chunks (iCCP, eXIf, a zTXt, a dozen tEXt) — all decoys.

## Solution

1. **Peel layer 1 — the bytes after `IEND`.** The PNG parses cleanly, but there are **100,158 bytes after the end marker**. They start with `00000000 0010 4a46 4946` — a JPEG whose first four bytes (`FFD8 FFE0`, SOI + APP0) were **zeroed out**.
2. **Peel layer 2 — repair the header.** Writing back `FFD8 FFE0` yields a valid 1892×806 JPEG (a sci-fi scene, nothing readable in it).
3. **Peel layer 3 — the EXIF description.** The JPEG's `ImageDescription` holds a 2,052-character hex string. Decoding it gives 1,026 bytes of ciphertext.
4. **Peel layer 4 — repeating-key XOR.** Coincidence scoring puts the key period at multiples of 5; column-wise English frequency scoring over the whole 1,026-byte payload recovers the key **`cixin`** cleanly. The plaintext opens with:
   ```
   0x1337{0nly_4dv4nc3}
   delete all files related to reverse engineering software and the software itself. ...
   ```
   followed by a "TOP SECRET POTUS bioweapon" troll narrative meant to scare people off from peeling further. Ignore it, take the flag.

Flag: `0x1337{0nly_4dv4nc3}`

## Dead ends

- Single-byte XOR, XOR with dictionary keys, and file-magic interpretations of the decoded blob (it is not a corrupted container, just encrypted text).
- The PNG's own metadata chunks (eXIf/zTXt/tEXt) and the iCCP profile — all genuine ImageMagick output, no payload.

## Lessons

- "Matryoshka" stego chains layers across *formats*: PNG tail → repaired JPEG → EXIF text → classical crypto.
- A JPEG that refuses to open but starts with `00 00 00 00 0010 4a46 4946` is a header-shredded file: the `JFIF\0` signature survives, so just restore `FFD8 FFE0`.
- For repeating-key XOR, coincidence scoring over candidate key lengths plus per-column English-frequency fitting recovers the key without any crib.

## Files

- `files/challenge.png` — the challenge image.
- `solve.py` — runs the whole chain and prints the flag.
