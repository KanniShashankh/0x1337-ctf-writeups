#!/usr/bin/env python3
"""ContextCon Deccan CTF — "based" (Crypto / Misc, author: sans)

The 78-character ciphertext uses only the first 28 symbols of the standard
Base64 alphabet.  Each riddle in clue.txt resolves to a well-known number and
names a candidate base; decoding the ciphertext as one big base-N number (with
Base64-alphabet digit values) in the file's clue order yields printable ASCII
exactly once -- at base 28 (clue 17, "AAAA", the DNS record type).

Usage:  python3 solve.py [folder-containing-ciphertext.txt-and-clue.txt]
"""
import sys

B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

# Riddle -> number (in clue.txt order).  These are the candidate bases.
CLUES = [
    (1,  "The Poolrooms (Backrooms level 37)",        37),
    (2,  "Venomoth (Pokedex #49)",                    49),
    (3,  "King's Indian Defense (ECO code E60)",      60),
    (4,  "Iron (atomic number 26)",                   26),
    (5,  "Gold Block (Minecraft block ID 41)",        41),
    (6,  "SCP-058 'Heart of Darkness' (bovine heart)", 58),
    (7,  "Bangladesh (ISO 3166-1 numeric 050)",       50),
    (8,  "SIGTERM (signal 15)",                       15),
    (9,  "Stop the Presses (Dreamfall Chapters 15G)", 15),
    (10, "Michael Jordan (23)",                       23),
    (11, "Abraham Lincoln (16th president)",          16),
    (12, "SSH (port 22)",                             22),
    (13, "@ (ASCII code 64)",                         64),
    (14, "Middle C (40th key of an 88-key piano)",    40),
    (15, "Women's suffrage (19th Amendment)",         19),
    (16, "Atlantic Avenue (Monopoly space 26)",       26),
    (17, "AAAA (DNS record type 28)",                 28),
]


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "files"
    ct = open(f"{folder}/ciphertext.txt").read().split("\n")[0].strip()
    vals = [B64.index(c) for c in ct]
    max_digit = max(vals)
    print(f"[*] ciphertext: {len(ct)} chars, digit range {min(vals)}-{max_digit}")

    # Follow the order in the text file: try each clue's base in order.
    for num, desc, base in CLUES:
        if base <= max_digit:
            print(f"[-] base {base:3d} ({desc}): impossible, digits exceed base")
            continue
        n = 0
        for v in vals:
            n = n * base + v
        data = n.to_bytes((n.bit_length() + 7) // 8, "big")
        if all(32 <= b < 127 for b in data):
            text = data.decode()
            print(f"[+] base {base:3d} ({desc}): {text}")
            print(f"\nFlag: 0x1337{{{text}}}")
            return
        print(f"[-] base {base:3d} ({desc}): binary noise")

    raise SystemExit("no base produced printable output")


if __name__ == "__main__":
    main()
