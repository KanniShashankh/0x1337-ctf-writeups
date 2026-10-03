# GridMax Logistics — Ordering Desk

- **Category:** Web (+ real-world / OSINT capture)
- **Flag:** `0x1337{f0ur_fr4m3s_x0r3d_1nt0_a_s1gn1ng_k3y}`
- **Service:** `http://40.81.242.56:30117`
- **Files:** [`files/exploit.py`](files/exploit.py) (one-shot capture→decode→forge), [`files/decode_calibrate.py`](files/decode_calibrate.py) (geometry calibration against an oracle), [`files/wall_grid.jpg`](files/wall_grid.jpg) (a captured dashboard frame)

## Challenge

> GridMax Logistics runs a tiny ordering desk. Log in, place an order, and the desk signs your receipt. Orders above your budget are refused. The operations dashboard is up on the big screen for everyone to see.

Extra hint on the prompt: *"offline moving grid irl"*.

The site is an Express app that aggressively tries to scare off automated clients
(`X-AI-Agent-Notice`, a fake `/legal`, a `robots.txt` telling bots to stop). All of
that is decoration — this is an authorized CTF target.

## Recon

The app has a handful of endpoints:

- `POST /login` — no password; sets a **plaintext** `session` cookie equal to the
  username. Every account starts with budget 100.
- `POST /order` (`value=<n>`) — refuses `value > budget`, otherwise returns a signed
  receipt and stores it in an **editable** `order` cookie:
  `order = j:{"user","value","nonce","sig"}`.
- `POST /checkout` — reads the `order` cookie, re-verifies `sig`, and completes the
  order. **The budget is only checked at order time**, so a valid high-value receipt
  passes checkout.
- `GET /changelog` — the useful part:

```
v0.9  switched receipts to rotating per-window signatures.
v0.8  ops dashboard moved to the lobby screen; token auth on /admin.
v0.7  deprecated the old quad-frame parity check (xor of the four calibration
      frames) that the legacy display calibrator used for tamper detection.
```

So: forge a receipt with `value` above budget. The only thing stopping us is the
signature.

## The signature scheme

`sig` is 64 hex chars (SHA-256 sized) and depends on a server-side **key that rotates
per time window** (TTL measured empirically at under ~100 s). Tampering with `value`
in the cookie yields `order signature invalid or expired`, so `value` is covered by
the signature — we need the actual key.

The key is published, in plain sight, on the "operations dashboard … on the big
screen for everyone to see." That screen is a **real projector in the venue lobby**
showing `GRIDMAX · OPS DASHBOARD`: a 10×10 grid of white/dark cells that **animates**
("offline **moving grid** **irl**"). Per the changelog, the display cycles **four
calibration frames**, and their **XOR** is the payload. That payload is the current
window's signing key.

With one captured window where we also have a same-window receipt as an oracle, a
short brute-force pins the exact construction:

```
key = XOR(frame0, frame1, frame2, frame3)          # per-cell, 10x10 -> 13 bytes
      read after one 90° rotation, row-major, MSB-first
sig = HMAC_SHA256(key, f"{user}|{value}|{nonce}").hexdigest()
```

(The `rot90` is just because the phone capture was rotated; the underlying order is
row-major MSB.)

## Capturing the wall

The dashboard is physical, so we photographed it with a phone over `adb`
(`adb shell input keyevent 25` to trigger the shutter, then pull the JPEGs). The
hard part was turning shaky, angled, rotated phone captures into a bit-perfect 10×10:

1. **Burst** ~12 full-res photos (~0.4 s apart) to catch all four animation frames.
2. **Locate** the grid as the largest bright blob (downscaled, thin-structure
   erosion to drop the vertical title text), take its four corners.
3. **Homography-warp** the grid quad to a square and sample each cell centre — this
   absorbs perspective and tilt from shooting the wall at an angle from a desk.
4. **Cluster** the frames into the four distinct states; **XOR** them.
5. **Resolve orientation/encoding** (rotation × mirror × row/col × bit order × invert)
   by checking against an oracle.

The oracle is the key trick for correctness and timing: immediately after capturing,
fetch a normal `POST /order` from the **same window**. Its `sig` lets us verify a
candidate key offline with HMAC — no guessing whether a decode is right, and it lets
us self-correct the orientation automatically.

## Forging

Because `/checkout` recomputes `HMAC(current_key, "user|value|nonce")` from the cookie,
we never even need `/order`: craft our own `nonce`, compute the signature with the
decoded key, drop it in the `order` cookie, and check out.

Everything — capture, decode, verify, forge — has to finish inside one signing window
(<~100 s). The final [`exploit.py`](files/exploit.py) does burst → decode → oracle-verify
→ forge in about **2.4 s**:

```
VERIFY True KEY 3d2756aab943b07423c221b610
CHECKOUT {"ok":true,"message":"order success for 9999 units",
          "flag":"0x1337{f0ur_fr4m3s_x0r3d_1nt0_a_s1gn1ng_k3y}"}
```

## Flag

```
0x1337{f0ur_fr4m3s_x0r3d_1nt0_a_s1gn1ng_k3y}
```

## Lessons

- Server-trusted state in a client-editable cookie + a budget check only at creation
  time = forge-after-the-fact, if you can sign.
- "Rotating per-window signature" and "XOR of four calibration frames" in the
  changelog spelled out the key construction; the scary anti-bot headers were noise.
- A same-window request makes a perfect offline oracle: it removes all ambiguity from
  a noisy real-world capture (orientation, geometry, thresholds) and keeps you honest
  about whether the decode is actually correct before you spend the window on a forge.
