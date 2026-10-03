import numpy as np, string, sys
from PIL import Image, ImageFont, ImageDraw
F = ImageFont.truetype(sys.argv[1] if len(sys.argv) > 1 else 'lucon.ttf', 20, layout_engine=ImageFont.Layout.BASIC)
T = np.array(Image.open('files/chall.png').convert('L'), dtype=float)
H, W = T.shape; B = 5
TB = T.reshape(H//B, B, W//B, B).mean(axis=(1, 3))   # target block values
ADV = F.getlength('a')

def blocks(text, x0, y0):
    im = Image.new('L', (W, H), 255)
    ImageDraw.Draw(im).text((x0, y0), text, font=F, fill=0)
    a = np.array(im, dtype=float)
    return a.reshape(H//B, B, W//B, B).mean(axis=(1, 3))

def score(text, x0, y0, final=False):
    pb = blocks(text, x0, y0)
    nb = W//B if final else max(0, int((x0 + ADV*len(text) - 2) // B))
    return np.abs(pb[:, :nb] - TB[:, :nb]).sum(), nb

CS = string.ascii_letters + string.digits + " _{}!?.,'-"
def beam(x0, y0, n, width=30):
    beams = [("", 0.0)]
    for _ in range(n):
        cand = []
        for p, _s in beams:
            for c in CS:
                s, nb = score(p + c, x0, y0)
                cand.append((p + c, s))
        cand.sort(key=lambda t: t[1]); beams = cand[:width]
    return beams

if __name__ == '__main__':
    # offset search over first 3 chars -> (0, 3)
    best = min((beam(x0, y0, 3, 8)[0][1], x0, y0) for x0 in range(13) for y0 in range(-6, 8))
    _, x0, y0 = best
    # decode all 57 cells (685 px / 12 px advance)
    text, err = beam(x0, y0, 57, 20)[0]
    print(text, err)
    print('0x1337{%s}' % text)
