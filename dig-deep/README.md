# Dig Deep

- **Category:** Forensics / Stego (audio)
- **Flag:** `0x1337{sp3ctrograph-1s-coo1}`
- **Files:** [`files/dig-deep.zip`](files/dig-deep.zip), [`files/outer-spectrogram.png`](files/outer-spectrogram.png), [`files/hidden-spectrogram.png`](files/hidden-spectrogram.png)

## Challenge

> Layers upon layers, decompression is only the surface. When the static clears and the signal emerges, look beyond what meets the ear—and dig a little deeper.

## Solution

1. **Unwrap the zips.** `dig-deep.zip` holds `file.zip`, which holds another zip, and so on: 51 single-entry zips in total. A loop that keeps opening the only entry ends at a 122-second WAV (16-bit stereo, 44.1 kHz, about 21.6 MB).
2. **The outer WAV is a decoy.** Its spectrogram only says "Dig Deep" over and over ([`outer-spectrogram.png`](files/outer-spectrogram.png)). The sample values are a giveaway, though: the first frames are all 0, 1, 256 and 257, meaning only the lowest bit of each byte is set.
3. **Extract the LSBs.** Take the lowest bit of every byte in the `data` chunk (both bytes of every sample, both channels) and pack the bits MSB-first:
   ```
   00 27 91 64 52 49 46 46 ...   ->   length 0x00279164 = 2593124, then "RIFF"
   ```
   The first 4 bytes are a big-endian length, followed by a complete second WAV (14.7 s, identical left and right channels).
4. **View the spectrogram of the hidden WAV.**
   ```
   sox hidden.wav -n spectrogram -x 3000 -y 1025 -o hidden.png
   ```
   The flag is drawn between about 3 and 15 kHz ([`hidden-spectrogram.png`](files/hidden-spectrogram.png)):
   **`0x1337{sp3ctrograph-1s-coo1}`**

[`solve.py`](solve.py) does all three steps in about 3 seconds (only the standard library is needed; `sox` is optional, for the image).

## Lessons

- For deeply nested archives, script the unwrapping and check the file type at each step instead of doing it by hand.
- Before reaching for stego tools, look at raw sample values. Values that only ever use bit 0 of each byte (0, 1, 256, 257) mean LSB embedding in every byte, not every sample.
- LSB payloads often start with a length prefix. Check whether the first 4 bytes decode to a sensible size, then look for a magic number (`RIFF`, `PK`, `\x89PNG`) right after.
- In audio challenges, check the spectrogram of every layer. The outer one here was a hint that something more was hidden.
