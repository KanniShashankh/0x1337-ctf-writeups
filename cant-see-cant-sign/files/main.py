import random
import os

FLAG = os.environ["FLAG"]

r = random.getrandbits(512)

try:
    N = int(input("Enter N: "))

    bit_length = N.bit_length()

    if bit_length < 512:
        print("N not big enough :(")
        exit(0)
except:
    print("Bad N!")
    exit(0)


def blind(m, N, e, r):
    b = (m * pow(r, e, N)) % N
    return b

def verify(m, N, sb, e, r):
    s = (sb * pow(r, -1, N)) % N

    if pow(s, e, N) == m:
        return True
    else:
        return False

for i in FLAG:
    mony = ord(i)
    blinded = blind(mony, N, 65537, r)
    print("Please sign this:", blinded)
    sb = int(input("Enter signature: "))
    if not verify(mony, N, sb, 65537, r):
        print("Invalid signature!!\n")
        print("Unauthorized! Shutting down!\n")
        exit(0)
    else:
        print("Signature verified\n")

print("Thanks for the signatures!")
