# Untitled Session 04

- **Category:** Forensics / Audio stego
- **Flag:** `0x1337{4ud10_tr4ck_4ss3mbl3d_fr0m_f0ur}`
- **Files:** [`files/audio_track.zip`](files/audio_track.zip), [`solve.py`](solve.py)

## Challenge

> The studio lost the master of Untitled Session 04. All that survives are four archives the engineer left behind.
>
> - **Soundcheck:** Someone dumped the entire session archive from the studio and the engineer swears the take is in there somewhere. Most of it is dead air.
> - **Contact:** Sixty takes, one contact sheet, one usable session. The rest is the band warming up.
> - **Matryoshka:** The engineer zipped it. Then zipped it again. Then kept going.
> - **Signature:** Sixteen fragments. Half of them are ours. You already know which half.
>
> The flag arrives in four parts, one from each archive. Put them together in the order above and submit the whole thing.
>
> Tools: Audacity, CyberChef.

`audio_track.zip` contains `ch1_soundcheck.zip`, `ch2_contact.zip`, `ch3_matryoshka.zip` and `ch4_signature.zip`.

## Solution

Every real fragment is text drawn in a WAV's **spectrogram**. Each carrier file holds one glyph (or one short string), framed by pilot tones at about 0.9 kHz and 7 kHz plus side bars at about 2.4 kHz and 5.9 kHz. Use `sox file.wav -n rate 16k spectrogram -r -o out.png` or Audacity's spectrogram view.

1. **Soundcheck: `0x1337{4ud10_t`.** There are 240 `take_*.wav` files, and 226 of them are silence (sample std of about 1). Only 14 takes have signal: 070, 089, 113, 121, 134, 137, 165, 172, 178, 196, 200, 221, 222, 230. Read in take-number order, their glyphs are `0 x 1 3 3 7 { 4 u d 1 0 _ t`.
2. **Contact: `r4ck_4ss3m`.** `contact_sheet.png` shows spectrogram thumbnails of all 60 reels. Most reels are broadband noise with horizontal lines. The ten tiles with diagonal sweeps (03, 14, 18, 23, 41, 43, 48, 52, 57, 59) are the carriers. Their spectrograms are clean above 7 kHz and show `r 4 c k _ 4 s s 3 m`.
3. **Matryoshka: `bl3d_fr`.** `matryoshka.zip` is 200 nested layers, each with `master_*.zip` and a `notes_NNN.txt` filler note. The innermost layer holds `final_mix.wav`, whose spectrogram reads `bl3d_fr`.
4. **Signature: `0m_f0ur}`.** The 16 parts spell `q z v 0 w k m _ j x f 0 y u r }`. The decoy half is the eight uncommon letters `q z v w k j x y`. The remaining parts (04, 07, 08, 11, 12, 14, 15, 16) finish the phrase "from four". The two round glyphs are as tall as the digits in the other archives (about 2.4 to 5.1 kHz), while lowercase letters top out near 4.4 kHz. That makes them zeros, so the fragment is `fr0m_f0ur`.
5. **Join the parts:** `0x1337{4ud10_t` + `r4ck_4ss3m` + `bl3d_fr` + `0m_f0ur}` reads as "audio track assembled from four".

```
$ python3 solve.py files/audio_track.zip
[+] ch1: 14 glyphs -> out/ch1.png
[+] ch2: 10 glyphs -> out/ch2.png
[+] ch3: 1 glyphs -> out/ch3.png
[+] ch4: 8 glyphs -> out/ch4.png
[+] read glyphs: 0x1337{4ud10_tr4ck_4ss3mbl3d_fr0m_f0ur}
```

`solve.py` finds the carriers automatically and renders them in flag order. The glyphs themselves are read by eye from the PNGs.

## Decoys

The archives contain several red herrings:

- **Helper scripts that print fake flags.** They hardcode the output instead of computing it: `batch_extract.py` prints `0x1337{n0t_qu1t3_my_t3mp0}`, `sheet_decode.py` prints `0x1337{w4v3_g00dby3_t0_th4t_0n3}`, and `solve.py` in the matryoshka layers prints `0x1337{tr3bl3_4h34d_n0_b4ss_f0r_y0u}`. The SHA1 in `verify.py` (`82ee999d…`) only matches that last fake flag.
- **Fake flags in RIFF `LIST/INFO` metadata.** `take_070.wav` has `ICRD = 0x1337{n0t_qu1t3_my_t3mp0}` and `part_01_of_16.wav` has `0x1337{f4ls3tt0_fl4g_n1c3_p1tch_th0ugh}`.
- **A fake AES route.** An `ICMT` comment says spectrogram inspection "will NOT yield the payload". It says the real data is AES-256-CBC in the RIFF tail with `key = SHA256("naadamcollective")` and a fallback list of rotating keys in `candidates.txt`. The tail bytes are random (entropy about 7.9 to 8.0 bits per byte) in every file, carriers and silent files alike. `candidates.txt` is the same 2.3M-line file in all four archives: 56 unique band-name variants plus fake progress comments like `partial match: 0x1337{ ... recovering remainder`.
- **Filler notes.** The `notes_NNN.txt` files in the matryoshka layers say `packet N of 7 verified, continue` and carry no data.

## Lessons

- In audio stego, check the spectrogram first. "Dead air" means filtering by signal energy is the fastest triage.
- A contact sheet or thumbnail view can be the index that picks out the real files.
- Text embedded in a challenge (comments, metadata, helper scripts) can steer you toward a dead end. Check its claims against the data, such as tail entropy or whether a script computes anything, before spending time on it.
- When the parts must be put back in order and filtered, a readable leetspeak phrase is a strong check. Use glyph height to tell `0` from `o`.
