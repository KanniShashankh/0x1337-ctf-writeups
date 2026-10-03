#!/usr/bin/env python3
"""Dig Deep solver: unwrap the nested zips, pull the WAV hidden in the byte LSBs, render its spectrogram."""
import io
import shutil
import subprocess
import sys
import zipfile

src = sys.argv[1] if len(sys.argv) > 1 else "files/dig-deep.zip"
data = open(src, "rb").read()

# Layer 1: 51 single-entry zips nested inside each other.
layers = 0
while data[:4] == b"PK\x03\x04":
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        data = z.read(z.namelist()[0])
    layers += 1
print(f"unzipped {layers} layers -> {data[:4]!r}, {len(data)} bytes")
open("outer.wav", "wb").write(data)

# Layer 2: one bit per byte (LSB of every byte of the data chunk, MSB-first packing).
# The first 32 bits are a big-endian length, followed by a complete WAV file.
i = data.find(b"data")
size = int.from_bytes(data[i + 4:i + 8], "little")
pcm = data[i + 8:i + 8 + size]

bits = bytearray()
acc = 0
for n, b in enumerate(pcm):
    acc = (acc << 1) | (b & 1)
    if n % 8 == 7:
        bits.append(acc)
        acc = 0

length = int.from_bytes(bits[:4], "big")
hidden = bytes(bits[4:4 + length])
print(f"hidden payload: {length} bytes, header {hidden[:4]!r}")
open("hidden.wav", "wb").write(hidden)

# Layer 3: the flag is drawn in the hidden WAV's spectrogram.
if shutil.which("sox"):
    subprocess.run(["sox", "hidden.wav", "-n", "spectrogram", "-x", "3000", "-y", "1025", "-o", "hidden.png"], check=True)
    print("spectrogram written to hidden.png")
else:
    print("install sox (or open hidden.wav in Audacity/Sonic Visualiser) to view the spectrogram")
