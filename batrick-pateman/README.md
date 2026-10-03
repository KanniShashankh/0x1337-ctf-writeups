# Batrick Pateman

- **Category:** Misc / Forensics (Level 1 special)
- **Flag:** `0x1337{ThisisobfuscationsobadtheJapanesewouldbedisappointedinyou}`
- **Files:** [`files/chall.png`](files/chall.png), [`solve.py`](solve.py) (run `python3 solve.py /path/to/lucon.ttf`; the font is not redistributed here)

## Challenge

> Look at that subtle full black on white coloring; the tasteful PIL rendering... Oh my God, it even has size 20 lucon font. Remember to submit your flag in the format 0x1337{<your_flag_here>}

The title and description riff on the American Psycho business-card scene. `chall.png` is a 685x25 image of pixelated text.

## Solution

1. **The image is a 5x5 mosaic.** Every 5x5 tile holds one gray value, so the grid is 137x5 blocks. Each value is the mean of the original pixels in that tile.
2. **The description gives the renderer exactly:** PIL, black on white, `lucon.ttf` (Lucida Console) at size 20. Lucida Console is monospaced, so the text can be recovered by brute force one character at a time.
3. **Get the layout right.** By default PIL uses the raqm layout engine, which gives a fractional advance (12.047 px). With that, the match drifts after about 11 characters. With `ImageFont.Layout.BASIC` the advance is an integer 12 px, and the reconstruction stays exact. An offset search puts the text origin at `(0, 3)`.
4. **Beam search.** Extend each candidate prefix by one character, render it, pixelate it, and score only the blocks that the prefix fully covers. Keep the 20 best candidates. 685 / 12 gives 57 characters.
5. The top candidate matches every block of the image to within 1 gray level (that difference is rounding):
   ```
   ThisisobfuscationsobadtheJapanesewouldbedisappointedinyou
   ```

## Lessons

- Pixelating or mosaicking text isn't redaction. If the font, size and renderer are known, the text can be recovered by brute force (see Depix and the "Unredacter" research).
- Match the exact rasteriser. Here, using PIL's BASIC layout instead of raqm made the difference between drift and a perfect fit.
