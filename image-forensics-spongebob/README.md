# Image Forensics (SpongeBob)

- **Category:** Forensics / Stego
- **Author:** SoggyBiscuit28
- **Flag:** `0x1337{pr0cr4stin4t1on}`
- **Files:** [`files/reality.png`](files/reality.png)

## Challenge

> A cringe-worthy joke hides a secret. Don't let the reality check distract you, dig into your life after this meme.

`reality.png` (500×563) is a SpongeBob "Break time!" meme with the caption "YOU, RIGHT NOW, WATCHING MEMES WHEN YOU SHOULD BE WORKING".

## Solution

1. **Sweep the standard layers first — all clean:**
   - nothing after `IEND` (no appended blob),
   - the only unusual chunk is a plain 456-byte sRGB `iCCP` colour profile,
   - the IDAT stream decompresses to exactly 563 rows (no hidden rows below the image),
   - the zip container has no comments or extra entries.
2. **Read the least significant bits.** Taking bit 0 of each pixel channel produces identical strings in the **R, G and B planes**:
   ```
   0x1337{pr0cr4stin4t1on}
   ```
3. **Locate it:** the payload starts at pixel (32, 0) — inside the flat white banner strip above the meme text — with a 4-byte big-endian length header `00 00 00 17` (23 = the flag's length). The strip looks like plain background, but its LSBs spell the flag.

Flag: `0x1337{pr0cr4stin4t1on}`

## Lessons

- When every container-level check (trailing data, extra chunks, extra rows) is clean, the next step is the pixel bit planes.
- LSB payloads in flat colour regions are invisible to the eye but trivially extractable — check each channel separately and all channels together.
- A length header in front of an LSB payload is a nice sanity check that you decoded the stream in the right order and endianness.

## Files

- `files/reality.png` — the challenge image.
- `solve.py` — extracts the red-channel LSB stream and prints the flag.
