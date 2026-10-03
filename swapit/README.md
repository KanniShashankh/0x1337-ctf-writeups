# Swap It

- **Category:** Stego / Misc
- **Author:** Abhiro0p
- **Flag:** the title of the paper behind the hidden DOI, "Memes as the Phenomenon of Modern Digital Culture" (submitted in the CTF's `0x1337{...}` format)
- **Files:** [`files/chall.jpeg`](files/chall.jpeg), [`files/challenge.txt`](files/challenge.txt), [`files/secret_1.csv`](files/secret_1.csv) (extracted)

## Challenge

> Decode the code using the given image.
>
> `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGFnIjoiU1Y5a2IyNG5kRjlzYVd0bFh6TXkifQ.Nfb2RU1yqxF5Q5UdUeXrYabAHYpar2qCDVBDIyGM_nM`
>
> Happy hacking!!!

`chall.jpeg` is a 251×201 Yoda meme: "FIND THE FLAG YOU MUST".

## Solution

1. **The "code" is a JWT.** Decoding it (no secret needed):
   - header `{"alg":"HS256","typ":"JWT"}`
   - payload `{"flag":"SV9kb24ndF9saWtlXzMy"}`
   - inner base64 decodes to `I_don't_like_32`, a decoy/hint, not the flag.
2. **The image hides data with steghide, using an empty passphrase.**
   ```
   docker run --rm -v "$PWD:/steg" rickdejager/stegseek --seed /steg/chall.jpeg
   docker run --rm -v "$PWD:/steg" rickdejager/stegseek /steg/chall.jpeg /steg/words.txt /steg/out.bin
   # [i] Found passphrase: ""
   # [i] Original filename: "secret_1.csv".
   ```
   Equivalent: `steghide extract -sf chall.jpeg -p ""`.
3. **Peel the base64.** `secret_1.csv` is base64 three layers deep:
   ```
   VFVNMGVVNUVTWHBPUXprellWaE9hMkl5TUhWa2FrVXhZVlJKZFUxNldYZz0=
   -> TUM0eU5ESXpOQzkzYVhOa2IyMHVkakUxYVRJdU16WXg=
   -> MC4yNDIzNC93aXNkb20udjE1aTIuMzYx
   -> 0.24234/wisdom.v15i2.361
   ```
4. **It's a DOI with the leading `1` missing:** `10.24234/wisdom.v15i2.361`. Resolving it:
   ```
   curl -sL -H "Accept: application/vnd.citationstyles.csl+json" https://doi.org/10.24234/wisdom.v15i2.361
   ```
   gives the paper **"Memes as the Phenomenon of Modern Digital Culture"** (Vitiuk, Polishchuk, Kovtun, Fed; *WISDOM* 15(2), 2020). A meme paper for a meme image.
5. The paper title is the flag.

## Dead ends

- **JWT secret:** not in full rockyou (14.3M) or in 55k words and phrases from the paper. The HS256 signature is irrelevant.
- **jphide:** stegdetect reports `jphide(***)`, but that's a false positive caused by the steghide embedding. jpseek and stegbreak found nothing.
- **Header tricks:** swapping SOF width/height or the quantization tables only garbles the image.
- **Pixel-level hiding:** bit planes, channel swaps and LSB streams are plain JPEG noise.

## Lessons

- For JPEGs, run `stegseek --seed` first. It detects steghide data and tries the empty passphrase almost instantly.
- A JWT in a stego challenge is often just a container for a hint. Decode the payload before trying to crack the signature.
- Strings like `0.24234/...` or `10.xxxx/...` are DOIs. Resolve them with `doi.org` content negotiation for clean metadata.
- stegdetect's jphide verdicts are unreliable on images already modified by steghide.
