from secret import diffiehillman
from hashlib import sha256
import secrets

from Crypto.Cipher import AES


p = diffiehillman.p
g = diffiehillman.g

sans = diffiehillman.sans
papyrus = diffiehillman.papyrus
undyne = diffiehillman.undyne

a = sans.a
b = papyrus.b
c = undyne.c

A = pow(g, a, p)
B = pow(g, b, p)
C = pow(g, c, p)

diffiehillman.send(sans, [papyrus, undyne])
diffiehillman.send(papyrus, [sans, undyne])
diffiehillman.send(undyne, [sans, papyrus])

X_A = pow(B * pow(C, -1, p) % p, a, p)
X_B = pow(C * pow(A, -1, p) % p, b, p)
X_C = pow(A * pow(B, -1, p) % p, c, p)

diffiehillman.send(sans, [papyrus, undyne])
diffiehillman.send(papyrus, [sans, undyne])
diffiehillman.send(undyne, [sans, papyrus])

K_AB = pow(B, a, p)
K_AC = pow(C, a, p)

salt_AB = b"AB share"
salt_AC = b"AC share"
salt_flag = b"flag"

key_AB = sha256(
    salt_AB + K_AB.to_bytes((p.bit_length() + 7) // 8, "big")
).digest()[:16]

key_AC = sha256(
    salt_AC + K_AC.to_bytes((p.bit_length() + 7) // 8, "big")
).digest()[:16]

S = diffiehillman.random_secret(p)
r = diffiehillman.random_secret(p)

share_A = (S + r) % p
share_B = (S + 2 * r) % p
share_C = (S + 3 * r) % p

size = (p.bit_length() + 7) // 8
share_B_bytes = share_B.to_bytes(size, "big")
share_C_bytes = share_C.to_bytes(size, "big")

iv_B = secrets.token_bytes(16)
iv_C = secrets.token_bytes(16)
iv_flag = secrets.token_bytes(16)

padding_B = 16 - len(share_B_bytes) % 16
padding_C = 16 - len(share_C_bytes) % 16

encrypted_B = AES.new(key_AB, AES.MODE_CBC, iv_B).encrypt(
    share_B_bytes + bytes([padding_B]) * padding_B
)
encrypted_C = AES.new(key_AC, AES.MODE_CBC, iv_C).encrypt(
    share_C_bytes + bytes([padding_C]) * padding_C
)

sans.message = {"iv": iv_B.hex(), "encrypted": encrypted_B.hex()}
x_bob_share = diffiehillman.send(sans, [papyrus])

sans.message = {"iv": iv_C.hex(), "encrypted": encrypted_C.hex()}
x_carol_share = diffiehillman.send(sans, [undyne])

G = pow(A, 3 * b, p) * pow(X_B, 2, p) * X_C % p

flag_key = sha256(
    salt_flag
    + G.to_bytes(size, "big")
    + S.to_bytes(size, "big")
).digest()[:16]

flag = diffiehillman.flag
padding_flag = 16 - len(flag) % 16
encrypted_flag = AES.new(flag_key, AES.MODE_CBC, iv_flag).encrypt(
    flag + bytes([padding_flag]) * padding_flag
)

sans.message = {"iv": iv_flag.hex(), "encrypted": encrypted_flag.hex()}
x_flag = diffiehillman.send(sans, [papyrus, undyne])
