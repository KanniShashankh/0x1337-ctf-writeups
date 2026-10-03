# Two Flags (Semaphore)

- **Category:** Forensics / Misc (audio, flag semaphore)
- **Flag:** `0x1337{semaphore}`
- **Files:** [`files/audio.wav`](files/audio.wav), [`files/spectrogram.png`](files/spectrogram.png)
- **Solver:** [`solve.py`](solve.py)

## Challenge

> Two flags speak, but neither says a word.
>
> One flag tells you nothing. Two flags tell you something. Enough of them might just tell you the flag.
>
> All you have to do is listen. Submit the flag in the format 0x1337{word}.

`audio.wav`: 16-bit mono PCM, 22050 Hz, 34 s.

## Solution

1. **Listen / extract the numbers.** The audio carries 18 numbers:
   `135 270 45 180 90 225 180 225 0 270 225 270 270 315 90 270 45 180`.
2. **Spectrogram.** `sox audio.wav -n trim 0 9 spectrogram -x 1800 -Y 800 -z 80 -o spectrogram.png`.
   The first ~8 s contain tones drawn as text spelling **`DEGREES`**. So the numbers are angles. The rest of the file is speech.
3. **"Two flags" = flag semaphore.** Each letter is two arm positions, and each arm points in one of 8 directions 45° apart. All the numbers are multiples of 45, so pair them up: 9 pairs means 9 letters.
4. **Decode.** Map each angle to a position `angle / 45` and look up the unordered pair in the semaphore table. The challenge's zero direction is unknown, so try all 8 rotations in both directions. Only one is readable:

```
$ python3 solve.py | grep -v '?'
...
dir=+1 offset=4 SEMAPHORE
...
```

With offset 4 (0° = arm pointing up, i.e. 180° from the "down" convention) the pairs read `S E M A P H O R E`.

## Lessons

- Run a spectrogram on every audio challenge. Here it only gave a hint (`DEGREES`), but that hint is what turns 18 numbers into angles.
- "Two flags" plus "one tells you nothing" is the classic semaphore clue: one arm alone is not a letter.
- When the angle convention is unknown, brute-force rotation and mirror. There are only 16 combinations.
