#!/usr/bin/env python3
"""Semaphore solver: decode arm angles (degrees) into flag-semaphore letters."""

# Positions numbered 0-7 around the circle in 45-degree steps, 0 = arm straight down.
TABLE = {
    (0, 1): "A", (0, 2): "B", (0, 3): "C", (0, 4): "D", (0, 5): "E", (0, 6): "F", (0, 7): "G",
    (1, 2): "H", (1, 3): "I", (1, 4): "K", (1, 5): "L", (1, 6): "M", (1, 7): "N",
    (2, 3): "O", (2, 4): "P", (2, 5): "Q", (2, 6): "R", (2, 7): "S",
    (3, 4): "T", (3, 5): "U", (3, 6): "Y", (3, 7): "Z",
    (4, 6): "J", (4, 7): "V", (5, 6): "W", (5, 7): "X",
}

ANGLES = [135, 270, 45, 180, 90, 225, 180, 225, 0, 270, 225, 270, 270, 315, 90, 270, 45, 180]
pairs = [(ANGLES[i] // 45, ANGLES[i + 1] // 45) for i in range(0, len(ANGLES), 2)]

# The challenge's zero direction and rotation are unknown, so try all 8 offsets both ways.
for direction in (1, -1):
    for offset in range(8):
        word = "".join(
            TABLE.get(tuple(sorted(((direction * a + offset) % 8, (direction * b + offset) % 8))), "?")
            for a, b in pairs
        )
        print(f"dir={direction:+d} offset={offset} {word}")
