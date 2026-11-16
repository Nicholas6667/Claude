import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
BG = (24, 38, 44)
WHITE = (240, 240, 235)
GREY = (150, 165, 170)
EFF = (255, 150, 60)    # fuerza de entrada
OUT = (80, 200, 230)    # fuerza de salida
UNK = (255, 220, 70)    # incógnita
OK = (110, 220, 120)
FD = "/usr/share/fonts/truetype/dejavu/"
def F(sz, b=False): return ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if b else "DejaVuSans.ttf"), sz)
f_title, f_big, f_mid, f_txt, f_small = F(54, True), F(34, True), F(28, True), F(26), F(21)

def mix(c, a): return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))
def ramp(t, s, d=0.5): return max(0.0, min(1.0, (t - s) / d))
def text(d, xy, s, font, col, a=1.0, anchor="la"):
    if a > 0: d.text(xy, s, font=font, fill=mix(col, a), anchor=anchor)

def arrow(d, x1, y1, x2, y2, col, w=5):
    d.line([(x1, y1), (x2, y2)], fill=col, width=w)
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (2.6, -2.6):
        d.line([(x2, y2), (x2 + 18 * math.cos(ang + s), y2 + 18 * math.sin(ang + s))], fill=col, width=w)

def lever(d, cx, cy, se, Le, Lo, ang, lab, a=1.0):
    """se: lado de la fuerza de entrada (-1 izq, +1 der). lab: dict de etiquetas."""
    fx = cx - (se * Le - se * Lo) / 2
    fy = cy
    d.polygon([(fx, fy), (fx - 30, fy + 55), (fx + 30, fy + 55)], fill=mix(GREY, a))
    d.line([(fx - 70, fy + 56), (fx + 70, fy + 56)], fill=mix(GREY, a * .6), width=3)
    c, s = math.cos(ang), math.sin(ang)
    P = lambda u, v=0: (fx + u * c - v * s, fy + u * s + v * c)
    d.line([P(-se * Lo), P(se * Le)], fill=mix(WHITE, a), width=9)
    # entrada
    ex, ey = P(se * Le, -5)
    arrow(d, ex, ey - 95, ex, ey - 8, mix(EFF, a))
    text(d, (ex, ey - 105), lab["Fe"], f_mid, lab.get("Fe_c", EFF), a, "ms")
    # salida: caja + flecha hacia arriba
    ox, oy = P(-se * Lo, -5)
    d.rectangle([ox - 28, oy - 50, ox + 28, oy - 2], outline=mix(OUT, a), width=4)
    arrow(d, ox, oy - 58, ox, oy - 135, mix(OUT, a))
    text(d, (ox, oy - 145), lab["Fs"], f_mid, lab.get("Fs_c", OUT), a, "ms")
    # distancias
    for u, key in ((se * Le / 2, "d1"), (-se * Lo / 2, "d2")):
        x, _ = P(u)
        x = min(max(x, fx - 1e9 if u < 0 else fx + 75), fx - 75) if u < 0 else max(x, fx + 75)
        text(d, (x, fy + 72), lab[key], f_txt, lab.get(key + "_c", WHITE), a, "mt")

def caption(d, s, a):
    if a <= 0: return
    d.rectangle([0, H - 80, W, H], fill=mix((12, 20, 24), a))
    text(d, (W / 2, H - 40), s, f_small, WHITE, a, "mm")

