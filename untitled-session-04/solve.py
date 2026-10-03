#!/usr/bin/env python3
"""Untitled Session 04: find the carrier WAVs in each archive and render their
spectrograms in flag order. The glyphs are read by eye from the PNGs in out/.

Usage: python3 solve.py files/audio_track.zip
Needs numpy and sox.
"""
import io, subprocess, sys, wave, zipfile
from pathlib import Path

import numpy as np

OUT = Path('out')
SIG4 = [4, 7, 8, 11, 12, 14, 15, 16]  # ch4 genuine half (common letters)


def samples(raw):
    w = wave.open(io.BytesIO(raw))
    return np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float)


def hf_ratio(a):
    # glyph carriers are quiet above the 7 kHz pilot; noise reels are not
    S = np.abs(np.fft.rfft(a)); f = np.fft.rfftfreq(len(a), 1 / 44100)
    return S[(f > 7500) & (f < 8000)].mean() / S[(f > 6800) & (f < 7100)].mean()


def render(name, raws):
    paths = []
    for i, raw in enumerate(raws):
        wav = OUT / f'{name}_{i:02d}.wav'; png = wav.with_suffix('.png')
        wav.write_bytes(raw)
        subprocess.run(['sox', wav, '-n', 'rate', '16k', 'spectrogram',
                        '-x', '250', '-y', '250', '-r', '-o', png], check=True)
        paths.append(png)
    args = sum([['-i', str(p)] for p in paths], [])
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *args, '-filter_complex',
                    f'hstack=inputs={len(paths)}' if len(paths) > 1 else 'null',
                    str(OUT / f'{name}.png')], check=True)
    print(f'[+] {name}: {len(raws)} glyphs -> {OUT / name}.png')


def members(z, prefix):
    return {Path(n).name: z.read(n) for n in sorted(z.namelist())
            if Path(n).name.startswith(prefix) and n.endswith('.wav')}


def main(path):
    OUT.mkdir(exist_ok=True)
    outer = zipfile.ZipFile(path)
    inner = {n.split('.')[0]: zipfile.ZipFile(io.BytesIO(outer.read(n)))
             for n in outer.namelist() if n.endswith('.zip')}

    # 1. Soundcheck: only a handful of takes are not silent
    takes = members(inner['ch1_soundcheck'], 'take_')
    render('ch1', [r for r in takes.values() if samples(r).std() > 10])

    # 2. Contact: carriers match the swept tiles on contact_sheet.png
    reels = members(inner['ch2_contact'], 'reel_')
    render('ch2', [r for r in reels.values() if hf_ratio(samples(r)) < 0.1])

    # 3. Matryoshka: peel the nested zips down to final_mix.wav
    z = inner['ch3_matryoshka']
    blob = z.read(next(n for n in z.namelist() if n.endswith('matryoshka.zip')))
    while True:
        z = zipfile.ZipFile(io.BytesIO(blob))
        nxt = [n for n in z.namelist() if n.endswith('.zip')]
        if not nxt:
            break
        blob = z.read(nxt[0])
    render('ch3', [z.read('final_mix.wav')])

    # 4. Signature: keep the half that forms words
    parts = members(inner['ch4_signature'], 'part_')
    render('ch4', [parts[f'part_{i:02d}_of_16.wav'] for i in SIG4])

    print('[+] read glyphs:', '0x1337{4ud10_t' + 'r4ck_4ss3m' + 'bl3d_fr' + '0m_f0ur}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'files/audio_track.zip')
