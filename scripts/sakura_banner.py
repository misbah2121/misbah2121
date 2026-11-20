"""Generate an animated pixel-art sakura banner for the GitHub profile README.

Usage (from the repo root, needs Pillow: pip install pillow):
    python scripts/sakura_banner.py                 # writes assets/banner-sakura.gif
    python scripts/sakura_banner.py out.gif --preview   # also writes out-preview.png (frame 0)
"""
import math
import random
import sys
from PIL import Image

W, H = 320, 80          # logical pixel canvas
SCALE = 4               # output 1280x320
FRAMES = 48
DURATION = 80           # ms per frame
import os
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = ARGS[0] if ARGS else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "banner-sakura.gif")
PREVIEW = "--preview" in sys.argv

rng = random.Random(7)

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def dither_pick(colors, t, x, y):
    """t in [0,1] -> pick from colors (dark->light) with ordered dithering."""
    t = max(0.0, min(0.9999, t))
    pos = t * (len(colors) - 1)
    i = int(pos)
    frac = pos - i
    if i + 1 < len(colors) and frac > (BAYER[y % 4][x % 4] + 0.5) / 16:
        i += 1
    return colors[i]


img = Image.new("RGB", (W, H))
px = img.load()

# ---------- sky ----------
SKY = [hexc(c) for c in ["#3b2a5c", "#57357a", "#7f4591", "#a85799", "#d1709f", "#ec93ad", "#f7b8c0"]]
for y in range(H):
    for x in range(W):
        px[x, y] = dither_pick(SKY, y / 62, x, y)

# stars
star_pos = []
for _ in range(40):
    x, y = rng.randrange(W), rng.randrange(0, 22)
    star_pos.append((x, y))
    px[x, y] = hexc("#fbe6ff") if rng.random() < 0.5 else hexc("#c9a7e6")

# sun
SUN = [hexc("#f9c9b6"), hexc("#ffe0c4"), hexc("#fff1dc")]
cx, cy, r = 236, 50, 14
for y in range(cy - r, cy + r + 1):
    for x in range(cx - r, cx + r + 1):
        d = math.hypot(x - cx, y - cy)
        if d <= r and 0 <= y < H:
            px[x, y] = dither_pick(SUN, 1 - d / r * 0.9, x, y)


def lerp(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def bayer(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16


SUN_X, SUN_Y = cx, cy
GLOW = hexc("#ffd9c4")
for y in range(H):
    for x in range(W):
        d = math.hypot(x - SUN_X, (y - SUN_Y) * 1.3)
        if 14 < d < 40:                                     # soft halo
            w = (1 - (d - 14) / 26) ** 1.5
            if w > bayer(x, y):
                px[x, y] = lerp(px[x, y], GLOW, 0.28)
        if d >= 16 and y < SUN_Y:                           # light rays fanning upward
            ang = math.atan2(y - SUN_Y, x - SUN_X)
            ray = math.sin(ang * 14 + 0.8) * math.sin(ang * 5.0)
            fade = max(0.0, 1 - d / 150)
            if ray > 0.55 and fade * 0.7 > bayer(x, y):
                px[x, y] = lerp(px[x, y], GLOW, 0.16)

# ---------- mountains ----------
def ridge(seed, base, amp, freq):
    rr = random.Random(seed)
    ph = [rr.random() * 6.28 for _ in range(3)]
    return [base - amp * (0.55 * math.sin(x * freq + ph[0]) + 0.3 * math.sin(x * freq * 2.3 + ph[1])
                          + 0.15 * math.sin(x * freq * 5.1 + ph[2])) for x in range(W)]


far = ridge(3, 52, 9, 0.025)
near = ridge(11, 60, 6, 0.04)
# a tall snow-capped peak
for x in range(W):
    peak = 30 + abs(x - 150) * 0.55
    far[x] = min(far[x], peak)
for x in range(W):
    for y in range(int(far[x]), H):
        snow = y < 37 + 2 * math.sin(x * 0.7) or (y < far[x] + 1 and far[x] < 44)
        px[x, y] = hexc("#f3dcef") if snow else dither_pick([hexc("#8a5a98"), hexc("#a36fa8")], 1 - (y - far[x]) / 25, x, y)
    for y in range(int(near[x]), H):
        px[x, y] = dither_pick([hexc("#5b3c72"), hexc("#714a84")], 1 - (y - near[x]) / 15, x, y)

# ---------- ground ----------
GROUND_Y = 69
GROUND = [hexc("#3a2540"), hexc("#4f3150"), hexc("#6a405f")]
for y in range(GROUND_Y, H):
    for x in range(W):
        px[x, y] = dither_pick(GROUND, 1 - (y - GROUND_Y) / 11, x, y)
for x in range(W):  # grass edge
    px[x, GROUND_Y] = hexc("#7a4f6c")
for _ in range(140):  # fallen petals
    x, y = rng.randrange(W), rng.randrange(GROUND_Y, H)
    px[x, y] = rng.choice([hexc("#f7a1c0"), hexc("#ffd1e0"), hexc("#e077a1")])

# ---------- sakura trees ----------
TRUNK_D, TRUNK_L = hexc("#3b1f2b"), hexc("#64363f")
PINK = [hexc(c) for c in ["#9e4570", "#c95c8a", "#e682a8", "#f7a8c4", "#ffd3e2", "#fff0f5"]]


TRUNK = [hexc("#2e1720"), hexc("#4a2632"), hexc("#6b3a47")]          # dark, mid, light
TRUNK_FAR = [hexc("#3d2440"), hexc("#53324f"), hexc("#6a4462")]
PINK_FAR = [hexc(c) for c in ["#7a4479", "#93558c", "#ad6aa0", "#c584b3", "#d9a2c6"]]


def put(x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        px[x, y] = c


def limb(x0, y0, x1, y1, cx, cy, w0, w1, cols):
    """Curved tapered limb (quadratic bezier) shaded light on the left, dark on the right."""
    steps = int(math.hypot(x1 - x0, y1 - y0) * 2) + 2
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        w = w0 + (w1 - w0) * t
        if w < 0.75:
            put(x, y, cols[0])
            continue
        r = int(math.ceil(w))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= w * w + 0.3:
                    c = cols[2] if dx < -w * 0.35 else cols[0] if dx > w * 0.35 else cols[1]
                    put(x + dx, y + dy, c)


def disc(cx, cy, r, c, keep=None):
    ri = int(math.ceil(r))
    for dy in range(-ri, ri + 1):
        for dx in range(-ri, ri + 1):
            if dx * dx + dy * dy <= r * r + 0.4:
                x, y = int(round(cx + dx)), int(round(cy + dy))
                if 0 <= x < W and 0 <= y < H and (keep is None or (x, y) in keep):
                    px[x, y] = c


def puff_mask(cx, cy, r):
    ri = int(math.ceil(r))
    return {(int(round(cx + dx)), int(round(cy + dy)))
            for dy in range(-ri, ri + 1) for dx in range(-ri, ri + 1) if dx * dx + dy * dy <= r * r + 0.4}


def tree(tx, height, spread, puff, seed, far=False):
    rr = random.Random(seed)
    tcols = TRUNK_FAR if far else TRUNK
    pal = PINK_FAR if far else PINK
    base_w = max(1.0, height / 11)
    tips, twigs = [], []

    def grow(x, y, ang, length, w, depth):
        x1, y1 = x + math.cos(ang) * length, y + math.sin(ang) * length
        bend = rr.uniform(-0.35, 0.35) * length
        cx, cy = (x + x1) / 2 + math.cos(ang + math.pi / 2) * bend, (y + y1) / 2 + math.sin(ang + math.pi / 2) * bend
        limb(x, y, x1, y1, cx, cy, w, w * 0.7, tcols)
        if depth <= 1:
            tips.append(((x + x1) / 2, (y + y1) / 2))
        if depth == 0:
            tips.append((x1, y1))
            twigs.append((x1, y1, ang))
            return
        n = 3 if rr.random() < 0.35 else 2
        for k in range(n):
            da = (k - (n - 1) / 2) * rr.uniform(0.45, 0.75) + rr.uniform(-0.15, 0.15)
            grow(x1, y1, ang + da, length * rr.uniform(0.62, 0.8), w * 0.62, depth - 1)

    trunk_len = height * 0.42
    lean = rr.uniform(-0.18, 0.18)
    grow(tx, GROUND_Y, -math.pi / 2 + lean, trunk_len, base_w, 0 if False else 0)  # trunk drawn alone first
    tips.clear(); twigs.clear()
    top_x, top_y = tx + math.cos(-math.pi / 2 + lean) * trunk_len, GROUND_Y + math.sin(-math.pi / 2 + lean) * trunk_len
    # main scaffold branches spread outward like a sakura crown
    for a in (-0.95, -0.3, 0.3, 0.95)[: 4 if spread > 12 else 3]:
        ang = -math.pi / 2 + a * rr.uniform(0.8, 1.1)
        grow(top_x, top_y, ang, spread * rr.uniform(0.55, 0.7), base_w * 0.5, 2)
    # roots
    if not far and base_w >= 2:
        limb(tx - base_w - 2, GROUND_Y, tx, GROUND_Y - 5, tx - base_w, GROUND_Y - 1, 1, 1, tcols)
        limb(tx + base_w + 2, GROUND_Y, tx, GROUND_Y - 5, tx + base_w, GROUND_Y - 1, 1, 1, tcols)

    # canopy puffs around every tip, drawn bottom-to-top so each puff's dark underside shows
    puffs = []
    for (x, y) in tips:
        for _ in range(rr.randint(3, 4)):
            r = rr.uniform(puff * 0.7, puff * 1.15)
            puffs.append((x + rr.uniform(-puff, puff), y + rr.uniform(-puff * 0.8, puff * 0.4), r))
    puffs.sort(key=lambda p: -p[1])
    for cx, cy, r in puffs:
        m = puff_mask(cx, cy, r)
        disc(cx + 0.5, cy + 1.2, r, pal[0])                     # shadow / outline underside
        disc(cx, cy, r - 0.6, pal[1], m)                         # body
        disc(cx - r * 0.18, cy - r * 0.22, r * 0.72, pal[2], m)  # mid
        disc(cx - r * 0.32, cy - r * 0.42, r * 0.42, pal[3], m)  # light top
        if not far:
            disc(cx - r * 0.4, cy - r * 0.55, r * 0.18, pal[4], m)  # highlight
            # textured edge: little clumps of blossoms sticking out
            for _ in range(int(r)):
                a = rr.uniform(math.pi * 0.9, math.pi * 2.1)
                put(cx + math.cos(a) * (r + 0.6), cy + math.sin(a) * (r + 0.6), pal[rr.choice([1, 2])])
    # a few twig ends poking through the blossoms
    for (x, y, ang) in ([] if far else twigs[:: 9]):
        limb(x - math.cos(ang) * 3, y - math.sin(ang) * 3, x, y, x, y, 0.5, 0.5, tcols)
    # scattered single blossoms
    if not far:
        for _ in range(len(puffs) // 2):
            cx, cy, r = rr.choice(puffs)
            put(cx + rr.uniform(-r, r) * 0.7, cy + rr.uniform(-r, r * 0.3) * 0.7, pal[-1])


# back row: small, hazy, center (kept low so the title stays readable)
for tx, h, s, p, seed in [(96, 22, 9, 3.2, 1), (124, 20, 8, 3.0, 2), (176, 21, 8, 3.0, 3), (206, 23, 9, 3.2, 4)]:
    tree(tx, h, s, p, seed, far=True)
# ---------- torii gate (centre focal point) ----------
RED, RED_D, RED_L, CAP = hexc("#d6374f"), hexc("#8e1f3a"), hexc("#f0637a"), hexc("#2a1636")
TX = 160
for x in (TX - 8, TX + 7):                       # pillars
    for y in range(50, GROUND_Y):
        put(x, y, RED_L if x < TX else RED)
        put(x + 1, y, RED_D)
for x in range(TX - 12, TX + 14):                # kasagi (top beam), ends turned up
    put(x, 47, RED); put(x, 48, RED_D)
    put(x, 46, CAP)
for x in (TX - 13, TX - 12, TX + 13, TX + 14):
    put(x, 45, CAP); put(x, 46, CAP)
for x in range(TX - 10, TX + 12):                # nuki (tie beam)
    put(x, 52, RED); put(x, 53, RED_D)
for y in range(49, 52):                          # centre strut
    put(TX, y, RED); put(TX + 1, y, RED_D)
for y in range(GROUND_Y - 2, GROUND_Y):          # dark pillar feet
    for x in (TX - 8, TX - 7, TX + 7, TX + 8):
        put(x, y, CAP)

# front row: big trees framing the sides
KEY = (255, 0, 255)
TREE_LAYERS = []          # [(phase, amplitude, top_y, [(x, y, colour), ...]), ...]
_base_px = px
for i, (tx, h, s, p, seed) in enumerate([(24, 50, 19, 5.5, 10), (70, 34, 13, 4.5, 11),
                                          (258, 36, 14, 4.5, 12), (300, 52, 19, 5.5, 13)]):
    layer = Image.new("RGB", (W, H), KEY)
    px = layer.load()
    tree(tx, h, s, p, seed)
    pix = [(x, y, px[x, y]) for y in range(H) for x in range(W) if px[x, y] != KEY]
    top = min(y for _, y, _ in pix)
    TREE_LAYERS.append((i * 0.23, 1.0 + h / 40, top, pix))
px = _base_px
TREE_COVER = {(x, y) for *_, pix in TREE_LAYERS for x, y, _ in pix}


def draw_trees(p, t):
    tau = 2 * math.pi
    for ph, amp, top, pix in TREE_LAYERS:
        # gusty wind: main sway plus a faster flutter; both loop with t
        wind = 0.75 * math.sin(tau * (t + ph)) + 0.25 * math.sin(tau * (2 * t + ph * 2))
        span = GROUND_Y - top
        for x, y, c in pix:
            k = max(0.0, (GROUND_Y - 6 - y) / span)          # roots stay planted
            xx = x + int(round(wind * amp * k * k * 1.6))
            if 0 <= xx < W:
                p[xx, y] = c


# ---------- stone lanterns (light flickers per frame) ----------
STONE_D, STONE, STONE_L = hexc("#5e4f66"), hexc("#8d7d8f"), hexc("#b3a5b5")
LANTERNS = [141, 181]
for lx in LANTERNS:
    for x in range(lx - 3, lx + 4):
        put(x, 57, STONE_D); put(x, 58, STONE)
    put(lx, 56, STONE_D)
    for y in range(59, 63):
        for x in range(lx - 2, lx + 3):
            put(x, y, STONE_L if x == lx - 2 else STONE_D if x == lx + 2 else STONE)
    for x in range(lx - 2, lx + 3):
        put(x, 63, STONE_D)
    for y in range(64, GROUND_Y):
        for x in range(lx - 1, lx + 2):
            put(x, y, STONE_L if x == lx - 1 else STONE)
    for x in range(lx - 2, lx + 3):
        put(x, GROUND_Y - 1, STONE_D)

SHADOW = hexc("#2a1636")


def ground_shadow(x0, half, length):
    """Darken an ellipse on the ground, stretched away from the sun."""
    away = -1 if x0 < SUN_X else 1
    cxs = x0 + away * length * 0.45
    rx = half + length * 0.5
    for y in range(GROUND_Y, min(H, GROUND_Y + 4)):
        for x in range(int(cxs - rx) - 1, int(cxs + rx) + 2):
            if 0 <= x < W:
                e = ((x - cxs) / rx) ** 2 + ((y - GROUND_Y - 0.5) / 2.6) ** 2
                if e < 1 and (1 - e) * 1.6 > bayer(x, y) * 0.9:
                    px[x, y] = lerp(px[x, y], SHADOW, 0.45)


for tx, half, ln in [(24, 6, 14), (70, 4, 10), (258, 4, 10), (300, 6, 14),
                     (96, 3, 6), (124, 3, 6), (176, 3, 6), (206, 3, 6)]:
    ground_shadow(tx, half, ln)
ground_shadow(TX - 8, 1, 7); ground_shadow(TX + 8, 1, 7)
for lx in LANTERNS:
    ground_shadow(lx, 2, 5)
ground_shadow(109, 3, 4)  # cat (sprite x=106)

STAR_COLS = {hexc("#fbe6ff"), hexc("#c9a7e6")}
STARS = [(x, y, rng.random()) for x, y in star_pos
         if img.getpixel((x, y)) in STAR_COLS and (x, y) not in TREE_COVER]

CAT = ["k...k...",
       "kk.kk...",
       "kkkkk...",
       "kekek...",
       "kkpkk...",
       "rrrrr...",
       "kkkkkk..",
       "kkkkkkk.",
       "kkkkkkk.",
       "kkkkkkkk"]
CAT_COL = {"k": hexc("#22122a"), "e": hexc("#ffd88a"), "p": hexc("#e682a8"), "r": hexc("#d6374f")}
CAT_X = 106

BIRDS = [(0.00, 40, 0.0), (0.06, 37, 0.3), (0.10, 42, 0.6)]   # (offset, y, phase)
WING_UP = [(-2, -2), (-1, -1), (0, 0), (1, -1), (2, -2)]
WING_DN = [(-2, 1), (-1, 0), (0, 0), (1, 0), (2, 1)]


MIST = hexc("#f0c6da")


def draw_dynamic(p, f, t):
    tau = 2 * math.pi
    for y in range(52, GROUND_Y + 2):
        band = 1 - abs(y - 62) / 10
        for x in range(W):
            dens = band * (0.55 + 0.25 * math.sin(x * 0.045 + tau * t) + 0.2 * math.sin(x * 0.11 - tau * t * 2 + y * 0.3))
            if dens * 0.55 > bayer(x, y):
                p[x, y] = lerp(p[x, y], MIST, 0.22)
    # twinkling stars
    for x, y, ph in STARS:
        v = math.sin(tau * (t * 2 + ph))
        p[x, y] = hexc("#ffffff") if v > 0.55 else hexc("#7c5a9e") if v < -0.55 else hexc("#e8d4f7")
        if v > 0.9:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H and y + dy < 22:
                    p[x + dx, y + dy] = hexc("#c9a7e6")
    # lantern glow
    for i, lx in enumerate(LANTERNS):
        v = 0.5 + 0.5 * math.sin(tau * (t * 3 + i * 0.37)) * math.sin(tau * (t * 5 + i * 0.11))
        core = hexc("#fff3c4") if v > 0.6 else hexc("#ffd88a") if v > 0.3 else hexc("#f5a25a")
        for y in (60, 61):
            for x in (lx - 1, lx, lx + 1):
                p[x, y] = core
        if v > 0.45:
            for x, y in ((lx - 3, 60), (lx + 3, 60), (lx - 3, 61), (lx + 3, 61)):
                if 0 <= x < W:
                    p[x, y] = hexc("#f7b06b")
    # birds crossing the sky
    for off, by, ph in BIRDS:
        bx = int(((off + t) % 1) * (W + 60)) - 30
        yy = by + int(round(math.sin(tau * (t * 2 + ph))))
        shape = WING_UP if (f // 3 + int(ph * 10)) % 2 else WING_DN
        for dx, dy in shape:
            if 0 <= bx + dx < W and 0 <= yy + dy < H:
                p[bx + dx, yy + dy] = hexc("#2a1636")
    # cat sitting under the trees, tail swaying
    top = GROUND_Y - len(CAT)
    for cy, row in enumerate(CAT):
        for cx, ch in enumerate(row):
            if ch != ".":
                p[CAT_X + cx, top + cy] = CAT_COL[ch]
    sway = math.sin(tau * t * 2)
    for i in range(6):
        tx = CAT_X + 7 + i * 0.55 + sway * (i / 5) ** 2 * 2.5
        ty = GROUND_Y - 1 - i * 0.95
        p[int(round(tx)), int(round(ty))] = CAT_COL["k"]


# ---------- pixel font ----------
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "D": "11110 10001 10001 10001 10001 10001 11110", "E": "11111 10000 10000 11110 10000 10000 11111",
    "G": "01111 10000 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111", "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111", "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001", "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100", "W": "10001 10001 10001 10101 10101 10101 01010",
    "·": "00000 00000 00000 00100 00000 00000 00000", " ": "00000 00000 00000 00000 00000 00000 00000",
}


def text_mask(s, scale):
    w = len(s) * 6 * scale - scale
    pts = set()
    for i, ch in enumerate(s):
        rows = FONT[ch].split()
        for gy, row in enumerate(rows):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            pts.add((i * 6 * scale + gx * scale + sx, gy * scale + sy))
    return pts, w


def draw_text(im, s, y0, scale, fill, shade, outline):
    p = im.load()
    pts, w = text_mask(s, scale)
    x0 = (W - w) // 2
    pts = {(x + x0, y + y0) for x, y in pts}
    ring = set()
    for x, y in pts:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1, 2):
                ring.add((x + dx, y + dy))
    for x, y in ring - pts:
        if 0 <= x < W and 0 <= y < H:
            p[x, y] = outline
    bottom = max(y for _, y in pts)
    for x, y in pts:
        p[x, y] = shade if y >= bottom - scale + 1 and scale > 1 else fill


# ---------- falling petals ----------
petals = []
for _ in range(90):
    depth = rng.random()
    layer = "far" if depth < 0.4 else "near" if depth > 0.82 else "mid"
    petals.append({
        "x": rng.uniform(-40, W),
        "y": rng.uniform(0, H + 20),
        "k": 2 if layer == "near" else 1,    # loops per animation cycle (keeps it seamless)
        "amp": {"far": 1.0, "mid": 2.5, "near": 4.5}[layer] * rng.uniform(0.7, 1.3),
        "ph": rng.random(),
        "c": rng.choice(PINK_FAR[3:]) if layer == "far" else rng.choice([PINK[3], PINK[4], PINK[5], PINK[2]]),
        "layer": layer,
    })

# ---------- reflecting pond ----------
POND_CX, POND_CY, POND_RX, POND_RY = 160, 75, 44, 4.6
WATER = hexc("#2f2350")
POND = set()
for y in range(GROUND_Y + 1, H):
    for x in range(W):
        if ((x - POND_CX) / POND_RX) ** 2 + ((y - POND_CY) / POND_RY) ** 2 <= 1:
            POND.add((x, y))
for x, y in POND:                                   # stone rim
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = (x + dx, y + dy)
        if q not in POND and 0 <= q[0] < W and GROUND_Y <= q[1] < H:
            px[q] = hexc("#7d6a86") if dy < 0 else hexc("#4a3a55")
for x, y in POND:
    px[x, y] = WATER
LILY = [(128, 76), (191, 73)]                       # lily pads
for lx, ly in LILY:
    for dx in range(-2, 3):
        px[lx + dx, ly] = hexc("#4f7a5a")
    for dx in range(-1, 2):
        px[lx + dx, ly + 1] = hexc("#3c5f47")
    px[lx, ly - 1] = hexc("#ffd3e2")                 # tiny lotus bud
POND_PETALS = [(rng.uniform(POND_CX - 36, POND_CX + 36), rng.uniform(POND_CY - 2.5, POND_CY + 2.5), rng.random())
               for _ in range(9)]


def draw_pond(p, t):
    tau = 2 * math.pi
    src = {}
    for x, y in POND:
        if (x, y) in {(lx + d, ly) for lx, ly in LILY for d in range(-2, 3)} or            (x, y) in {(lx + d, ly + 1) for lx, ly in LILY for d in range(-1, 2)} or (x, y) in {(lx, ly - 1) for lx, ly in LILY}:
            continue
        depth = y - GROUND_Y
        ripple = int(round(math.sin(y * 1.3 + tau * t * 2) * (0.6 + depth * 0.12)))
        sy = GROUND_Y - depth                       # mirror around the waterline
        sx = min(W - 1, max(0, x + ripple))
        c = p[sx, sy]
        k = 0.28 + depth * 0.04                    # deeper rows fade into the water
        src[(x, y)] = lerp(c, WATER, min(0.8, k))
    for (x, y), c in src.items():
        p[x, y] = c
    # glints sliding across the surface
    for i in range(6):
        gx = int(POND_CX - 34 + ((i * 0.17 + t) % 1) * 68)
        gy = int(POND_CY - 3 + (i * 7) % 6)
        if (gx, gy) in POND and (gx + 1, gy) in POND and math.sin(tau * (t * 2 + i * 0.3)) > -0.2:
            p[gx, gy] = hexc("#f7c8dc"); p[gx + 1, gy] = hexc("#c99ac0")
    # petals floating and bobbing
    for x, y, ph in POND_PETALS:
        xx = int(round(x + math.sin(tau * (t + ph)) * 1.5))
        if (xx, int(y)) in POND:
            p[xx, int(y)] = hexc("#ffd3e2")


frames = []
for f in range(FRAMES):
    fr = img.copy()
    p = fr.load()
    t = f / FRAMES
    draw_trees(p, t)
    draw_dynamic(p, f, t)
    draw_pond(p, t)
    for pt in petals:
        span = H + 20
        yy = (pt["y"] + span * pt["k"] * t) % span - 10
        x = pt["x"] + yy * 0.45 + pt["amp"] * math.sin(2 * math.pi * (t * pt["k"] * 2 + pt["ph"]))
        x, y = int(round(x)) % (W + 40) - 20, int(round(yy))
        flip = math.sin(2 * math.pi * (t * 3 + pt["ph"])) > 0
        if pt["layer"] == "far":
            cells = [(0, 0)]
        elif pt["layer"] == "mid":
            cells = [(0, 0), (1, 0)] if flip else [(0, 0), (0, 1)]
        else:
            cells = [(0, 0), (1, 0), (0, 1), (1, 1)] if flip else [(0, 0), (1, 0), (2, 1)]
        for dx, dy in cells:
            if 0 <= x + dx < W and 0 <= y + dy < H:
                p[x + dx, y + dy] = pt["c"]
    draw_text(fr, "MISBAH HUNNASIK", 8, 2, hexc("#ffffff"), hexc("#ffd3e2"), hexc("#2a1636"))
    draw_text(fr, "MOBILE · WEB · GAME DEVELOPER", 27, 1, hexc("#fff0f5"), hexc("#fff0f5"), hexc("#2a1636"))
    frames.append(fr.resize((W * SCALE, H * SCALE), Image.NEAREST))

pal = frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
q[0].save(OUT, save_all=True, append_images=q[1:], duration=DURATION, loop=0, optimize=False, disposal=1)
if PREVIEW:
    frames[0].save(OUT.replace(".gif", "-preview.png"))
print("saved", OUT)
