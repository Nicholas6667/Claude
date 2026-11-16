"""Video: Ley de la palanca. Ejemplo resuelto + "Tu turno" para cada problema.
Uso: python3 video_v2.py salida.mp4   (requiere piper con voz es-carlfm-x-low, ffmpeg, numpy, Pillow)
"""
import math, os, re, sys, wave, subprocess
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SS = 1920, 1080, 30, 2
WORK = os.environ.get("WORK", os.path.dirname(os.path.abspath(__file__)))
VOICE = os.environ.get("VOICE", os.path.join(WORK, "voices/es-carlfm-x-low.onnx"))
SR = 16000
FD = "/usr/share/fonts/truetype/dejavu/"

# ---------------------------------------------------------------- colores
BG = (19, 32, 40)
CARD = (29, 48, 58)
EDGE = (62, 92, 104)
WHITE = (242, 242, 236)
GREY = (140, 158, 165)
DIM = (80, 100, 108)
EFF = (255, 150, 60)
EFF2 = (255, 196, 140)
OUT = (80, 200, 235)
OUT2 = (160, 225, 245)
UNK = (255, 218, 60)
OK = (110, 222, 125)
RED = (255, 105, 105)
WOOD = (184, 128, 74)
WOOD_D = (120, 80, 44)

_fc = {}
def font(sz, b=False):
    k = (sz, b)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if b else "DejaVuSans.ttf"), int(sz * SS))
    return _fc[k]

def mix(c, a, bg=BG):
    a = max(0.0, min(1.0, a))
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))

def ramp(t, s, d=0.45):
    return max(0.0, min(1.0, (t - s) / d))

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

class Dr:
    def __init__(s, im): s.d = ImageDraw.Draw(im)
    def P(s, pts): return [(x * SS, y * SS) for x, y in pts]
    def line(s, pts, fill, width=2): s.d.line(s.P(pts), fill=fill, width=max(1, int(width * SS)), joint="curve")
    def poly(s, pts, fill=None, outline=None, width=1):
        s.d.polygon(s.P(pts), fill=fill, outline=outline, width=max(1, int(width * SS)) if outline else 0)
    def rect(s, b, fill=None, outline=None, width=2, r=0):
        b = [v * SS for v in b]
        if r: s.d.rounded_rectangle(b, int(r * SS), fill=fill, outline=outline, width=int(width * SS))
        else: s.d.rectangle(b, fill=fill, outline=outline, width=int(width * SS))
    def ell(s, b, fill=None, outline=None, width=2):
        s.d.ellipse([v * SS for v in b], fill=fill, outline=outline, width=int(width * SS))
    def pie(s, b, a0, a1, fill): s.d.pieslice([v * SS for v in b], a0, a1, fill=fill)
    def text(s, xy, txt, sz, col, bold=False, anchor="la"):
        s.d.text((xy[0] * SS, xy[1] * SS), txt, font=font(sz, bold), fill=col, anchor=anchor)
    def tw(s, txt, sz, bold=False): return s.d.textlength(txt, font=font(sz, bold)) / SS

_meas = Dr(Image.new("RGB", (10, 10)))
def tw(txt, sz, bold=False): return _meas.tw(txt, sz, bold)

def T(d, xy, txt, sz, col, a=1.0, bold=False, anchor="la", bg=BG):
    if a > 0.01: d.text(xy, txt, sz, mix(col, a, bg), bold, anchor)

def arrow(d, x1, y1, x2, y2, col, w=7, head=22):
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    d.line([(x1, y1), (bx, by)], col, w)
    px, py = -math.sin(ang), math.cos(ang)
    d.poly([(x2, y2), (bx + px * head * .6, by + py * head * .6), (bx - px * head * .6, by - py * head * .6)], fill=col)

def wrap(txt, sz, maxw, bold=False):
    out, cur = [], ""
    for w_ in txt.split():
        t2 = (cur + " " + w_).strip()
        if tw(t2, sz, bold) > maxw and cur: out.append(cur); cur = w_
        else: cur = t2
    if cur: out.append(cur)
    return out

# ---------------------------------------------------------------- fondo
def make_base():
    im = Image.new("RGB", (W * SS, H * SS), BG)
    px = np.zeros((H * SS, W * SS, 3), np.uint8)
    yy = np.linspace(0, 1, H * SS)[:, None]
    for i, (a, b) in enumerate(zip((16, 28, 36), (24, 40, 50))):
        px[:, :, i] = (a + (b - a) * yy).astype(np.uint8)
    im = Image.fromarray(px)
    d = ImageDraw.Draw(im)
    for x in range(0, W * SS, 60 * SS):
        d.line([(x, 0), (x, H * SS)], fill=(26, 41, 50), width=SS)
    for y in range(0, H * SS, 60 * SS):
        d.line([(0, y), (W * SS, y)], fill=(26, 41, 50), width=SS)
    return im
BASE = None

CHIPS = ["Intro", "Ej 1", "Tú 1", "Ej 2", "Tú 2", "Ej 3", "Tú 3", "Ej 4", "Tú 4", "Repaso"]
def header(d, title, chip, a=1.0):
    d.rect([0, 0, W, 96], fill=(12, 21, 27))
    T(d, (40, 48), title, 40, WHITE, a, True, "lm", (12, 21, 27))
    x = W - 30
    for i in range(len(CHIPS) - 1, -1, -1):
        lab = CHIPS[i]; w = tw(lab, 20, True) + 26; x -= w
        on = i == chip; done = i < chip
        fill = UNK if on else ((40, 70, 60) if done else (30, 46, 55))
        d.rect([x, 32, x + w, 66], fill=fill, r=17)
        d.text((x + w / 2, 49), lab, 20, (20, 20, 20) if on else (OK if done else GREY), True, "mm")
        x -= 8

def caption(d, s, a=1.0):
    if not s or a <= 0: return
    bg = (10, 17, 22)
    d.rect([0, 990, W, H], fill=bg)
    s = re.sub(r" {2,}", "  •  ", s)
    lines = wrap(s, 32, W - 160)
    y0 = 1035 - (len(lines) - 1) * 21
    for i, ln in enumerate(lines):
        T(d, (W / 2, y0 + i * 42), ln, 32, WHITE, a, False, "mm", bg)

def card(d, b, a=1.0, title=None, edge=EDGE):
    if a <= 0: return
    d.rect(b, fill=mix(CARD, a), outline=mix(edge, a), width=3, r=22)
    if title: T(d, (b[0] + 28, b[1] + 22), title, 28, GREY, a, True, "la", CARD)

# ---------------------------------------------------------------- palanca
def lever(d, fx, fy, ang, sides, a=1.0, ground=True):
    """sides: dicts con u (px con signo), kind 'push'|'box', label, lcol, box, bcol, dim, dcol"""
    if a <= 0: return
    c, s = math.cos(ang), math.sin(ang)
    P = lambda u, v=0: (fx + u * c - v * s, fy + u * s + v * c)
    if ground:
        d.line([(fx - 120, fy + 90), (fx + 120, fy + 90)], mix(GREY, a), 4)
        for k in range(-110, 120, 22):
            d.line([(fx + k, fy + 90), (fx + k - 14, fy + 104)], mix(DIM, a), 3)
    d.poly([(fx, fy), (fx - 48, fy + 90), (fx + 48, fy + 90)], fill=mix((120, 135, 140), a), outline=mix((180, 190, 195), a), width=3)
    us = [sd["u"] for sd in sides] + [0]
    u0, u1 = min(us) - 34, max(us) + 34
    d.poly([P(u0, -24), P(u1, -24), P(u1, 0), P(u0, 0)], fill=mix(WOOD, a), outline=mix(WOOD_D, a), width=3)
    for k in range(int(u0) + 40, int(u1) - 20, 70):
        d.line([P(k, -16), P(k + 30, -16)], mix(WOOD_D, a * .5), 2)
    d.ell([fx - 7, fy - 19, fx + 7, fy - 5], fill=mix(WOOD_D, a))
    for sd in sides:
        u = sd["u"]
        if sd.get("dim"):
            dc = sd.get("dcol", WHITE)
            p0, p1 = P(0, 120), P(u, 120)
            d.line([p0, p1], mix(dc, a * .8), 3)
            for p in (p0, p1):
                d.line([(p[0] - 14 * -s, p[1] - 14 * c), (p[0] + 14 * -s, p[1] + 14 * c)], mix(dc, a * .8), 3)
            m = P(u / 2, 120)
            T(d, (m[0], m[1] + 16), sd["dim"], 32, dc, a, True, "mt")
        bx, by = P(u, -24)
        if sd["kind"] == "box":
            bw, bh = sd.get("bw", 96), sd.get("bh", 74)
            if sd.get("box"): bw = max(bw, tw(sd["box"], 26 if len(sd["box"]) > 5 else 30, True) + 26)
            col = sd.get("bcol", OUT)
            d.rect([bx - bw / 2, by - bh, bx + bw / 2, by], fill=mix((40, 66, 80), a), outline=mix(col, a), width=4, r=8)
            if sd.get("box"): T(d, (bx, by - bh / 2), sd["box"], 26 if len(sd["box"]) > 5 else 30, col, a, True, "mm", (40, 66, 80))
            if sd.get("label"): T(d, (bx, by - bh - 14), sd["label"], 36, sd.get("lcol", col), a, True, "ms")
        else:
            col = sd.get("bcol", EFF)
            arrow(d, bx, by - 150, bx, by - 6, mix(col, a), 9, 28)
            if sd.get("label"): T(d, (bx, by - 162), sd["label"], 36, sd.get("lcol", col), a, True, "ms")

# ---------------------------------------------------------------- ecuaciones
def it(txt, col=WHITE, tag=None): return ("t", txt, col, tag)
def fr(num, den): return ("f", num, den)

def eq_w(items, sz):
    g = sz * 0.28; w = 0
    for i, x in enumerate(items):
        w += (tw(x[1], sz) if x[0] == "t" else max(eq_w(x[1], sz * .92), eq_w(x[2], sz * .92)) + sz * .5)
        if i: w += g
    return w

def eq_draw(d, items, x, y, sz, a=1.0, bg=CARD, hide=(), pos=None, over=None):
    if pos is None: pos = {}
    g = sz * 0.28
    for x_ in items:
        if x_[0] == "t":
            w = tw(x_[1], sz)
            tag = x_[3]
            col = (over or {}).get(tag, x_[2])
            if tag not in hide: T(d, (x, y), x_[1], sz, col, a, False, "lm", bg)
            if tag: pos[tag] = (x + w / 2, y)
        else:
            s2 = sz * .92
            wn, wd = eq_w(x_[1], s2), eq_w(x_[2], s2)
            w = max(wn, wd) + sz * .5
            cx = x + w / 2
            eq_draw(d, x_[1], cx - wn / 2, y - sz * .66, s2, a, bg, hide, pos, over)
            d.line([(x + 6, y), (x + w - 6, y)], mix(WHITE, a, bg), 3)
            eq_draw(d, x_[2], cx - wd / 2, y + sz * .70, s2, a, bg, hide, pos, over)
        x += w + g
    return pos

# ---------------------------------------------------------------- números en palabras
U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce",
     "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno",
     "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
TEN = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
HUN = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
       7: "setecientos", 8: "ochocientos", 9: "novecientos"}
def i2es(n):
    if n < 30: return U[n]
    if n < 100:
        t, u = divmod(n, 10); return TEN[t] + ("" if u == 0 else " y " + U[u])
    if n == 100: return "cien"
    if n < 1000:
        h, r = divmod(n, 100); return HUN[h] + ("" if r == 0 else " " + i2es(r))
    m, r = divmod(n, 1000)
    return ("mil" if m == 1 else i2es(m) + " mil") + ("" if r == 0 else " " + i2es(r))
def n2es(s):
    s = str(s)
    if "." in s:
        a, b = s.split(".")
        dec = i2es(int(b)) if (len(b) <= 2 and b[0] != "0") else " ".join(U[int(ch)] for ch in b)
        return i2es(int(a)) + " punto " + dec
    return i2es(int(s))

def fmt(x):
    s = f"{round(x, 4):.4f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"
def rnd(x): return round(x, 2) if x >= 1 else round(x, 3)

# ---------------------------------------------------------------- problemas
SYM = {"Fe": "Fe", "Fs": "Fs", "d1": "d₁", "d2": "d₂"}
SCOL = {"Fe": EFF, "Fs": OUT, "d1": EFF2, "d2": OUT2}
NAME = {"Fe": "la fuerza de entrada", "Fs": "la fuerza de salida", "d1": "de uno", "d2": "de dos"}
SHORT = {"Fe": "fuerza de entrada", "Fs": "fuerza de salida", "d1": "de uno", "d2": "de dos"}
UW = {"kg": "kilos", "m": "metros", "cm": "centímetros"}
PART = {"Fe": "d1", "d1": "Fe", "Fs": "d2", "d2": "Fs"}

class Prob:
    def __init__(s, n, mode, unk, vals, se, story="", insight="", statement="", statement_say="", title=""):
        s.n, s.mode, s.unk, s.vals, s.se = n, mode, unk, vals, se
        s.story, s.insight, s.statement, s.statement_say, s.title = story, insight, statement, statement_say, title
        m = {k: (v[0] / 100 if v[1] == "cm" else v[0]) for k, v in vals.items() if v[0] is not None}
        if unk == "Fe": ex = m["Fs"] * m["d2"] / m["d1"]
        elif unk == "Fs": ex = m["Fe"] * m["d1"] / m["d2"]
        elif unk == "d1": ex = m["Fs"] * m["d2"] / m["Fe"]
        else: ex = m["Fe"] * m["d1"] / m["Fs"]
        s.exact, s.res = ex, rnd(ex)
        s.rounded = abs(s.res - ex) > 1e-9
        s.unit = "kg" if unk in ("Fe", "Fs") else "m"
        s.m = dict(m); s.m[unk] = s.res
        s.P = PART[unk]
        s.Q, s.R = ("Fs", "d2") if unk in ("Fe", "d1") else ("Fe", "d1")
        s.prod = m[s.Q] * m[s.R]
        lhs, rhs = s.m["Fe"] * s.m["d1"], s.m["Fs"] * s.m["d2"]
        s.lhs, s.rhs = lhs, rhs
        dm = max(s.m["d1"], s.m["d2"]); sc = 400 / dm
        s.Le = max(95, s.m["d1"] * sc); s.Lo = max(95, s.m["d2"] * sc)
        s.cms = [k for k in ("d1", "d2") if k in vals and vals[k][0] is not None and vals[k][1] == "cm"]

    # ---- texto de cada valor
    def raw(s, k):
        v = s.vals[k]; return f"{fmt(v[0])} {v[1]}"
    def say_raw(s, k):
        v = s.vals[k]; return f"{n2es(fmt(v[0]))} {UW[v[1]]}"
    def mstr(s, k): return fmt(s.m[k])
    def res_s(s): return fmt(s.res)

    def segments(s):
        """lista de (etapa, narración, subtítulo, duración_mínima)"""
        u, P, Q, R = s.unk, s.P, s.Q, s.R
        known = [k for k in ("Fe", "Fs", "d1", "d2") if k != u]
        def dato(k):
            return (f"{SHORT[k].capitalize()}: {s.say_raw(k)}." if k in ("Fe", "Fs") else f"{SHORT[k].capitalize()} mide {s.say_raw(k)}.")
        conv_say = " ".join(f"{SHORT[k].capitalize()} está en centímetros. Para pasarlo a metros dividimos entre cien: "
                            f"{n2es(fmt(s.vals[k][0]))} entre cien es {n2es(s.mstr(k))} metros." for k in s.cms)
        conv_cap = "   ".join(f"{SYM[k]} = {s.raw(k)} ÷ 100 = {s.mstr(k)} m" for k in s.cms)
        approx = "aproximadamente " if s.rounded else ""
        ru = UW[s.unit]
        cm_extra = f", es decir, unos {n2es(fmt(round(s.res*100,1)))} centímetros" if s.unit == "m" and s.res < 1 else ""
        same = abs(s.lhs - s.rhs) < 1e-6
        segs = []
        if s.mode == "ej":
            segs += [
                ("intro", f"Ejemplo {s.n}. En este problema buscamos {NAME[u]}. {s.story}",
                 f"Ejemplo {s.n}: buscamos {SYM[u]}", 0),
                ("datos", "Paso uno: anotamos los datos. " + " ".join(dato(k) for k in known) +
                 f" Y lo que no conocemos, la incógnita, es {NAME[u]}. La marcamos con un signo de interrogación.",
                 "Paso 1: anotamos los datos y marcamos la incógnita con ?", 0),
                ("convert", ("Paso dos: revisamos las unidades. " + conv_say + " Es como recorrer el punto decimal dos lugares a la izquierda.")
                 if s.cms else "Paso dos: revisamos las unidades. Todas las distancias ya están en metros, así que no hay que convertir nada.",
                 ("Paso 2: pasamos cm a metros (÷ 100):  " + conv_cap) if s.cms else "Paso 2: todo ya está en metros ✓", 0),
                ("formula", "Paso tres: escribimos la ley de la palanca. Fuerza de entrada por de uno, es igual a fuerza de salida por de dos. "
                 f"Lo que buscamos, {NAME[u]}, está en amarillo.",
                 "Paso 3: escribimos la fórmula  Fe · d₁ = Fs · d₂", 0),
                ("despeje", f"Paso cuatro: despejamos. Queremos dejar sola a {NAME[u]}. Pero {NAME[P]} la está multiplicando. "
                 f"Lo que está multiplicando, pasa al otro lado dividiendo. Entonces nos queda: {SHORT[u]} es igual a "
                 f"{SHORT[Q]} por {SHORT[R]}, entre {SHORT[P]}.",
                 f"Paso 4: {SYM[P]} está multiplicando → pasa al otro lado dividiendo", 4.5),
                ("sust", f"Paso cinco: sustituimos cada letra por su número, ya en metros. Arriba queda {n2es(s.mstr(Q))} por "
                 f"{n2es(s.mstr(R))}, y abajo {n2es(s.mstr(P))}.",
                 "Paso 5: cambiamos cada letra por su número", 0),
                ("mult", f"Paso seis: primero resolvemos la multiplicación de arriba. {n2es(s.mstr(Q))} por {n2es(s.mstr(R))} "
                 f"es {n2es(fmt(s.prod))}.",
                 f"Paso 6: multiplicamos arriba:  {s.mstr(Q)} × {s.mstr(R)} = {fmt(s.prod)}", 0),
                ("div", f"Y luego dividimos: {n2es(fmt(s.prod))} entre {n2es(s.mstr(P))} es {approx}{n2es(s.res_s())}.",
                 f"Paso 7: dividimos:  {fmt(s.prod)} ÷ {s.mstr(P)} {'≈' if s.rounded else '='} {s.res_s()}", 0),
                ("result", f"¡Listo! {NAME[u].capitalize()} es {approx}{n2es(s.res_s())} {ru}{cm_extra}. {s.insight}",
                 f"Resultado: {SYM[u]} {'≈' if s.rounded else '='} {s.res_s()} {s.unit}", 0),
                ("check", f"Siempre podemos comprobar. Fuerza de entrada por de uno da {n2es(fmt(s.lhs))}. "
                 f"Fuerza de salida por de dos da {n2es(fmt(s.rhs))}. " +
                 ("¡Son iguales! La palanca está en equilibrio, así que el resultado es correcto." if same else
                  "¡Son prácticamente iguales! La pequeña diferencia es solo por redondear. El resultado es correcto."),
                 "Comprobación: si los dos lados dan lo mismo, ¡está bien!", 0),
            ]
        else:
            segs += [
                ("statement", f"¡Ahora es tu turno! {s.statement_say} Pausa el video y resuélvelo en tu cuaderno con los mismos pasos. "
                 "Te doy unos segundos.", "¡Tu turno! Pausa el video y resuélvelo en tu cuaderno", 0),
                ("count1", "", "Datos → convertir a metros → fórmula → despejar → sustituir → calcular", 15),
                ("hint", f"¿Necesitas una pista? Buscas {NAME[u]}. " +
                 (f"No olvides pasar los centímetros a metros. " if s.cms else "") +
                 f"Despejando, queda: {SHORT[u]} es igual a {SHORT[Q]} por {SHORT[R]}, entre {SHORT[P]}.",
                 f"Pista: {SYM[u]} = ({SYM[Q]} · {SYM[R]}) ÷ {SYM[P]}", 0),
                ("count2", "", "¿Ya lo tienes? Ahora vemos la solución…", 8),
                ("datos", "¡Veamos la solución! Primero los datos. " + " ".join(dato(k) for k in known),
                 "Paso 1: datos", 0),
                ("convert", ("Pasamos a metros: " + " ".join(f"{n2es(fmt(s.vals[k][0]))} centímetros son {n2es(s.mstr(k))} metros." for k in s.cms))
                 if s.cms else "Las distancias ya están en metros.",
                 ("Paso 2: " + conv_cap) if s.cms else "Paso 2: todo ya está en metros ✓", 0),
                ("formula", "Escribimos la fórmula.", "Paso 3: fórmula", 0),
                ("despeje", f"{NAME[P].capitalize()} está multiplicando, así que pasa dividiendo.",
                 f"Paso 4: {SYM[P]} pasa al otro lado dividiendo", 3.5),
                ("sust", "Sustituimos los números.", "Paso 5: sustituimos", 0),
                ("mult", f"{n2es(s.mstr(Q))} por {n2es(s.mstr(R))} es {n2es(fmt(s.prod))}.",
                 f"Paso 6: {s.mstr(Q)} × {s.mstr(R)} = {fmt(s.prod)}", 0),
                ("div", f"Y {n2es(fmt(s.prod))} entre {n2es(s.mstr(P))} es {approx}{n2es(s.res_s())}.",
                 f"Paso 7: {fmt(s.prod)} ÷ {s.mstr(P)} {'≈' if s.rounded else '='} {s.res_s()}", 0),
                ("result", f"El resultado es {approx}{n2es(s.res_s())} {ru}{cm_extra}. ¿Te salió igual? ¡Excelente! "
                 "Si no, regresa el video y revisa en qué paso te equivocaste.",
                 f"Resultado: {SYM[u]} {'≈' if s.rounded else '='} {s.res_s()} {s.unit}   ¿Te salió igual?", 0),
                ("check", f"Comprobamos: los dos lados dan {n2es(fmt(s.rhs))}. ¡Equilibrio!",
                 "Comprobación ✓", 0),
            ]
        return segs

    # ------------------------------------------------------------ dibujo
    def draw(s, d, t, St, chip):
        g = lambda k: St.get(k, 1e9)
        u, P, Q, R = s.unk, s.P, s.Q, s.R
        header(d, s.title, chip)
        solved = t >= g("result")
        conv = t >= g("convert") + 1.2
        # --- palanca
        if solved: ang = 0.09 * math.sin(1.5 * t) * math.exp(-2.2 * (t - g("result")))
        else: ang = 0.09 * math.sin(1.5 * t)
        def lab(k, with_sym=True):
            if k == u:
                return (f"{SYM[k]} = {s.res_s()} {s.unit}" if solved else f"{SYM[k]} = ?"), (OK if solved else UNK)
            if k in s.cms and conv: return f"{SYM[k]} = {s.mstr(k)} m", SCOL[k]
            return f"{SYM[k]} = {s.raw(k)}", SCOL[k]
        fe_l, fe_c = lab("Fe"); fs_l, fs_c = lab("Fs"); d1_l, d1_c = lab("d1"); d2_l, d2_c = lab("d2")
        uE, uO = s.se * s.Le, -s.se * s.Lo
        fx = 500 - (uE + uO) / 2
        boxtxt = ("?" if (u == "Fs" and not solved) else (f"{s.res_s()} kg" if u == "Fs" else s.raw("Fs")))
        lever(d, fx, 380, ang, [
            dict(u=uE, kind="push", label=fe_l, lcol=fe_c, bcol=EFF, dim=d1_l, dcol=d1_c),
            dict(u=uO, kind="box", label=fs_l, lcol=fs_c, bcol=OUT, box=boxtxt, dim=d2_l, dcol=d2_c),
        ], ramp(t, 0.2))
        if solved:
            a = ramp(t, g("result") + 1.0)
            if a > 0:
                d.rect([360, 112, 640, 160], fill=mix((30, 70, 45), a), r=24)
                T(d, (500, 136), "¡Equilibrio! ✓", 30, OK, a, True, "mm", (30, 70, 45))
        # --- datos
        a = ramp(t, g("datos"))
        card(d, [30, 640, 970, 890], a, "Datos")
        if a > 0:
            for i, k in enumerate(("Fe", "d1", "Fs", "d2")):
                x = 70 + (i // 2) * 460; y = 718 + (i % 2) * 78
                ai = ramp(t, g("datos") + 0.3 + i * 0.5)
                T(d, (x, y), SYM[k] + " =", 40, SCOL[k], ai, True, "lm", CARD)
                xv = x + tw(SYM[k] + " = ", 40, True)
                if k == u:
                    if solved: T(d, (xv, y), f"{s.res_s()} {s.unit}", 40, OK, ai, True, "lm", CARD)
                    else:
                        T(d, (xv, y), "?", 44, UNK, ai, True, "lm", CARD)
                        T(d, (xv + 45, y), "← buscamos", 26, UNK, ai, False, "lm", CARD)
                else:
                    T(d, (xv, y), s.raw(k), 40, WHITE, ai, False, "lm", CARD)
                    if k in s.cms:
                        ac = ramp(t, g("convert") + 0.8)
                        if ac > 0:
                            w0 = tw(s.raw(k), 40)
                            d.line([(xv - 4, y + 2), (xv + w0 + 4, y + 2)], mix(RED, ac, CARD), 4)
                            T(d, (xv + w0 + 14, y), f"→ {s.mstr(k)} m", 40, OK, ac, True, "lm", CARD)
        # --- pizarra o enunciado
        sol0 = g("datos")
        if s.mode == "tu" and t < sol0 + 0.5:
            s.draw_statement(d, t, St, 1 - ramp(t, sol0, 0.5))
        if t >= g("formula") - 0.1:
            s.draw_board(d, t, St)
        # --- comprobación
        a = ramp(t, g("check"))
        if a > 0:
            bg = (24, 58, 40)
            d.rect([30, 908, W - 30, 976], fill=mix(bg, a), outline=mix(OK, a * .7), width=3, r=18)
            same = abs(s.lhs - s.rhs) < 1e-6
            t1 = f"Fe · d₁ = {s.mstr('Fe')} × {s.mstr('d1')} = {fmt(s.lhs)}"
            t2 = f"Fs · d₂ = {s.mstr('Fs')} × {s.mstr('d2')} = {fmt(s.rhs)}"
            T(d, (60, 942), "Comprobación:", 30, OK, a, True, "lm", bg)
            T(d, (330, 942), t1, 30, EFF2, ramp(t, g("check") + 0.5), False, "lm", bg)
            T(d, (960, 942), t2, 30, OUT2, ramp(t, g("check") + 1.5), False, "lm", bg)
            T(d, (W - 60, 942), "✓ iguales" if same else "✓ casi iguales", 30, OK, ramp(t, g("check") + 2.5), True, "rm", bg)

    def draw_statement(s, d, t, St, a):
        g = lambda k: St.get(k, 1e9)
        b = [1000, 120, 1890, 890]
        card(d, b, a, edge=UNK)
        T(d, (1040, 160), f"¡Tu turno! — Problema {s.n}", 40, UNK, a, True, "la", CARD)
        y = 230
        for ln in wrap(s.statement, 33, 800):
            T(d, (1040, y), ln, 33, WHITE, a * ramp(t, 0.6), False, "la", CARD); y += 46
        # pista
        ah = ramp(t, g("hint")) * a
        if ah > 0:
            hb = (52, 52, 30)
            d.rect([1040, 520, 1850, 650], fill=mix(hb, ah, CARD), outline=mix(UNK, ah * .6, CARD), width=2, r=16)
            T(d, (1065, 548), "Pista", 26, UNK, ah, True, "la", hb)
            items = [it(SYM[s.unk], UNK), it("="), fr([it(SYM[s.Q], SCOL[s.Q]), it("·"), it(SYM[s.R], SCOL[s.R])], [it(SYM[s.P], SCOL[s.P])])]
            eq_draw(d, items, 1220, 590, 40, ah, hb)
            if s.cms: T(d, (1560, 590), "¡cm → m!", 30, RED, ah, True, "lm", hb)
        # temporizador
        for key in ("count1", "count2"):
            if key in St:
                st = St[key]; dur = St[key + "_dur"]
                if st - 0.5 <= t < st + dur + 0.3:
                    ac = min(ramp(t, st - 0.5), 1 - ramp(t, st + dur - 0.1, 0.4)) * a
                    left = max(0.0, st + dur - t)
                    cx, cy, r = 1445, 765, 82
                    d.ell([cx - r, cy - r, cx + r, cy + r], fill=mix((40, 60, 70), ac, CARD))
                    frac = left / dur
                    if frac > 0: d.pie([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=mix(UNK, ac * .85, CARD))
                    d.ell([cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16], fill=mix(CARD, 1))
                    T(d, (cx, cy), str(int(math.ceil(left))) if left > 0 else "0", 56, WHITE, ac, True, "mm", CARD)
                    pill = (70, 40, 40)
                    d.rect([1090, 735, 1320, 795], fill=mix(pill, ac, CARD), r=30)
                    T(d, (1205, 765), "PAUSA ‖", 30, RED, ac, True, "mm", pill)
                    T(d, (1690, 765), "cuaderno ✎", 30, GREY, ac, True, "mm", CARD)

    def draw_board(s, d, t, St):
        g = lambda k: St.get(k, 1e9)
        u, P, Q, R = s.unk, s.P, s.Q, s.R
        a0 = ramp(t, g("formula") - 0.1)
        if s.mode == "tu": a0 *= ramp(t, g("formula") - 0.1)
        card(d, [1000, 120, 1890, 890], a0, None)
        cur = None
        for k in ("formula", "despeje", "sust", "mult", "result"):
            if t >= g(k): cur = k
        if t >= g("div") and cur == "mult": cur = "mult"
        rows = [("formula", "1 Fórmula", 210), ("despeje", "2 Despejar", 350), ("sust", "3 Sustituir", 490),
                ("mult", "4 Calcular", 630), ("result", "5 Resultado", 775)]
        for key, lab_, y in rows:
            a = ramp(t, g(key))
            if a <= 0: continue
            on = key == cur
            pf = UNK if on else (44, 66, 76)
            d.rect([1025, y - 24, 1205, y + 24], fill=mix(pf, a, CARD), r=24)
            T(d, (1115, y), lab_, 22, (25, 25, 25) if on else GREY, a, True, "mm", pf)
        X0, SZ = 1240, 48
        sym = lambda k, tag=None, col=None: it(SYM[k], col or (UNK if k == u else SCOL[k]), tag)
        # fila 1
        td = g("despeje")
        fly0, fly1 = td + 1.0, td + 2.6
        line1 = [sym("Fe", "Fe1"), it("·"), sym("d1", "d11"), it("="), sym("Fs", "Fs1"), it("·"), sym("d2", "d21")]
        tagmap = {"Fe": "Fe1", "d1": "d11", "Fs": "Fs1", "d2": "d21"}
        over = {}
        if td <= t:
            pulse = 0.5 + 0.5 * math.sin(10 * (t - td))
            over[tagmap[P]] = RED if t < fly1 else DIM
        pos1 = eq_draw(d, line1, X0, 210, SZ, a0 if t >= g("formula") else 0, CARD, over=over)
        if t >= g("formula") and t < td + 0.2:
            pass
        # fila 2 (despeje)
        if t >= td:
            a = ramp(t, td + 0.3)
            line2 = [sym(u), it("="), fr([sym(Q), it("·"), sym(R)], [sym(P, "P2")])]
            hide = ("P2",) if t < fly1 else ()
            pos2 = eq_draw(d, line2, X0, 350, SZ, a, CARD, hide=hide)
            if fly0 <= t < fly1:
                k = ease((t - fly0) / (fly1 - fly0))
                (x0, y0), (x1, y1) = pos1[tagmap[P]], pos2["P2"]
                x = x0 + (x1 - x0) * k; y = y0 + (y1 - y0) * k - math.sin(math.pi * k) * 70
                T(d, (x, y), SYM[P], int(SZ * (1 - .08 * k)), RED, 1, False, "mm", CARD)
            an = min(ramp(t, td + 0.6), 1 - ramp(t, g("sust") - 0.3))
            if an > 0:
                T(d, (1600, 272), f"{SYM[P]} multiplica → pasa dividiendo", 24, RED, an, True, "mm", CARD)
        # fila 3
        if t >= g("sust"):
            a = ramp(t, g("sust"))
            line3 = [sym(u), it("="), fr([it(s.mstr(Q)), it("·"), it(s.mstr(R))], [it(s.mstr(P))])]
            eq_draw(d, line3, X0, 490, SZ, a, CARD)
        # fila 4
        if t >= g("mult"):
            a = ramp(t, g("mult"))
            line4 = [it("="), fr([it(fmt(s.prod), UNK)], [it(s.mstr(P))])]
            eq_draw(d, line4, X0, 630, SZ, a, CARD)
            if t >= g("div"):
                w4 = eq_w(line4, SZ)
                eq_draw(d, [it("≈" if s.rounded else "="), it(f"{s.res_s()} {s.unit}", OK)], X0 + w4 + 14, 630, SZ, ramp(t, g("div")), CARD)
        # fila 5
        if t >= g("result"):
            a = ramp(t, g("result"))
            pop = 1 + 0.12 * math.exp(-6 * (t - g("result"))) * math.sin(14 * (t - g("result")))
            txt = f"{SYM[u]} {'≈' if s.rounded else '='} {s.res_s()} {s.unit}"
            sz = int(54 * pop)
            w = tw(txt, sz, True) + 70
            bb = (30, 70, 45)
            d.rect([X0, 775 - 44, X0 + w, 775 + 44], fill=mix(bb, a, CARD), outline=mix(OK, a, CARD), width=4, r=20)
            T(d, (X0 + w / 2, 775), txt, sz, OK, a, True, "mm", bb)
            if s.unit == "m" and s.res < 1:
                T(d, (X0 + w + 24, 775), f"= {fmt(round(s.res * 100, 1))} cm", 36, OK, ramp(t, g("result") + 0.8), True, "lm", CARD)

# ---------------------------------------------------------------- escenas de introducción
INTRO1 = [
    ("a0", "¡Hola! En este video vas a aprender a resolver problemas de palancas, paso a paso. Primero te explico la idea. "
           "Después resolvemos un ejemplo juntos, y luego te toca a ti resolver uno parecido. Así con los cuatro problemas del pizarrón.",
     "Primero la idea → luego un ejemplo → luego ¡tu turno!", 0),
    ("a1", "Piensa en un subibaja. De un lado se sienta un adulto de sesenta kilos, y del otro un niño de treinta kilos, "
           "los dos a un metro del centro. ¿Qué pasa? El adulto pesa más, así que su lado baja.",
     "Adulto 60 kg y niño 30 kg, los dos a 1 m: el adulto baja", 0),
    ("a2", "Pero mira qué pasa si el niño se aleja del centro, hasta dos metros. ¡Ahora el subibaja queda en equilibrio! "
           "Esto nos enseña algo muy importante: la distancia al centro importa tanto como el peso.",
     "Si el niño se aleja a 2 m… ¡equilibrio! La distancia importa tanto como el peso", 6),
]
def draw_intro1(d, t, St):
    header(d, "¿Qué es una palanca?", 0)
    t2 = St["a2"]
    dr = 1 + ease((t - t2 - 2.5) / 3.0)
    tau = 30 * dr - 60 * 1.0
    target = max(-0.2, min(0.2, 0.0065 * tau))
    ang = target if t > St["a1"] - 1 else 0.0
    if t < St["a1"]: ang = -0.2 * ease((t - St["a1"] + 1.5) / 1.5)
    sc = 190
    fx = 960
    lever(d, fx, 560, ang, [
        dict(u=-sc * 1.0, kind="box", label="Adulto", lcol=OUT, bcol=OUT, box="60 kg", bw=120, bh=110, dim="1 m", dcol=OUT2),
        dict(u=sc * dr, kind="box", label="Niño", lcol=EFF, bcol=EFF, box="30 kg", bw=86, bh=74,
             dim=f"{fmt(round(dr, 1))} m", dcol=EFF2),
    ], ramp(t, St["a1"] - 1.5))
    a = ramp(t, 0.3) * (1 - ramp(t, St["a1"] - 1.6))
    if a > 0:
        T(d, (W / 2, 300), "Ley de la Palanca", 90, WHITE, a, True, "mm")
        T(d, (W / 2, 420), "Ejemplo resuelto  →  ¡Tu turno!  (×4)", 44, UNK, ramp(t, 3) * a, True, "mm")
        T(d, (W / 2, 520), "Ten listo tu cuaderno y tu calculadora", 36, GREY, ramp(t, 6) * a, False, "mm")
    if t > St["a2"] + 5.5:
        aa = ramp(t, St["a2"] + 5.5)
        d.rect([520, 150, 1400, 230], fill=mix((30, 70, 45), aa), r=30)
        T(d, (960, 190), "La distancia importa tanto como el peso", 32, OK, aa, True, "mm", (30, 70, 45))

INTRO2 = [
    ("b0", "Veamos las partes de una palanca.", "Las partes de una palanca", 0),
    ("b1", "El fulcro es el punto de apoyo: el triangulito sobre el que gira la barra.", "Fulcro (Δ) = punto de apoyo", 0),
    ("b2", "Efe e es la fuerza de entrada: la fuerza que tú aplicas para mover la palanca.", "Fe = fuerza de entrada (la que tú aplicas)", 0),
    ("b3", "Efe ese es la fuerza de salida: la carga, o el peso, que quieres mover o levantar.", "Fs = fuerza de salida (la carga que se mueve)", 0),
    ("b4", "De uno es la distancia desde el fulcro hasta la fuerza de entrada. Y de dos es la distancia desde el fulcro hasta la carga. "
           "Ojo: las distancias siempre se miden desde el fulcro.", "d₁ = fulcro → Fe      d₂ = fulcro → Fs      (siempre desde el fulcro)", 0),
]
def draw_intro2(d, t, St):
    header(d, "Las partes de una palanca", 0)
    ang = 0.05 * math.sin(1.2 * t)
    a1, a2, a3, a4 = (ramp(t, St[k]) for k in ("b1", "b2", "b3", "b4"))
    lever(d, 900, 470, ang, [
        dict(u=330, kind="push", label="Fe" if a2 > 0 else "", bcol=mix(EFF, max(.25, a2)), lcol=EFF,
             dim="d₁" if a4 > 0 else None, dcol=EFF2),
        dict(u=-250, kind="box", label="Fs" if a3 > 0 else "", bcol=OUT, lcol=OUT, box="carga",
             dim="d₂" if a4 > 0 else None, dcol=OUT2),
    ], ramp(t, 0.2))
    def call(x, y, tx, ty, txt, col, a, anchor):
        if a <= 0: return
        d.line([(tx, ty), (x, y)], mix(col, a), 3)
        d.ell([x - 7, y - 7, x + 7, y + 7], fill=mix(col, a))
        T(d, (tx + (12 if anchor == "lm" else -12), ty), txt, 32, col, a, True, anchor)
    call(930, 525, 1080, 525, "Fulcro: punto de apoyo", WHITE, a1, "lm")
    call(1232, 390, 1310, 390, "Fuerza de entrada (tú)", EFF, a2, "lm")
    call(592, 410, 520, 410, "Fuerza de salida: la carga", OUT, a3, "rm")
    if a4 > 0:
        bg = (40, 50, 30)
        d.rect([360, 790, 1560, 870], fill=mix(bg, a4), r=30)
        T(d, (960, 830), "Las distancias se miden SIEMPRE desde el fulcro", 34, UNK, a4, True, "mm", bg)

INTRO3 = [
    ("c0", "Ahora, el secreto de las palancas: el efecto de giro. Se calcula multiplicando la fuerza por la distancia al fulcro.",
     "Efecto de giro = fuerza × distancia", 0),
    ("c1", "Del lado izquierdo, sesenta kilos a un metro: sesenta por uno, da sesenta.", "Izquierda: 60 kg × 1 m = 60", 0),
    ("c2", "Del lado derecho, treinta kilos a dos metros: treinta por dos, también da sesenta.", "Derecha: 30 kg × 2 m = 60", 0),
    ("c3", "Como los dos lados dan lo mismo, la palanca está en equilibrio. Y eso es la ley de la palanca: "
           "fuerza de entrada por de uno, es igual a fuerza de salida por de dos. Esta es la única fórmula que vas a necesitar.",
     "Ley de la palanca:  Fe · d₁ = Fs · d₂", 0),
]
def draw_intro3(d, t, St):
    header(d, "La idea clave: fuerza × distancia", 0)
    lever(d, 520, 420, 0.0, [
        dict(u=-150, kind="box", label="60 kg", lcol=OUT, bcol=OUT, box="", bw=100, bh=90, dim="1 m", dcol=OUT2),
        dict(u=300, kind="box", label="30 kg", lcol=EFF, bcol=EFF, box="", bw=80, bh=64, dim="2 m", dcol=EFF2),
    ], ramp(t, 0.2))
    T(d, (1440, 170), "fuerza × distancia", 46, WHITE, ramp(t, St["c0"] + 1), True, "mm")
    # rectángulos: ancho = distancia, alto = fuerza  (área = efecto de giro)
    for key, F_, D_, col, x0 in (("c1", 60, 1, OUT, 1130), ("c2", 30, 2, EFF, 1430)):
        a = ramp(t, St[key])
        if a <= 0: continue
        k = ease((t - St[key]) / 1.2)
        w_, h_ = D_ * 130, F_ * 4.2 * k
        yb = 640
        d.rect([x0, yb - h_, x0 + w_, yb], fill=mix(tuple(int(c * .45) for c in col), a), outline=mix(col, a), width=3)
        T(d, (x0 + w_ / 2, yb + 30), f"{D_} m", 30, col, a, True, "mm")
        T(d, (x0 - 14, yb - h_ / 2), f"{F_} kg", 30, col, a, True, "rm")
        T(d, (x0 + w_ / 2, yb + 80), f"{F_} × {D_} = 60", 40, WHITE, ramp(t, St[key] + 1.4), True, "mm")
    a = ramp(t, St["c3"])
    if a > 0:
        T(d, (1440, 280), "Mismo tamaño → ¡equilibrio!", 34, OK, a, True, "mm")
        d.rect([560, 790, 1360, 900], fill=mix((60, 56, 20), a), outline=mix(UNK, a), width=4, r=26)
        T(d, (960, 845), "Fe · d₁ = Fs · d₂", 62, UNK, ramp(t, St["c3"] + 3), True, "mm", (60, 56, 20))

INTRO4 = [
    ("u0", "Antes de usar la fórmula, revisa las unidades. Las distancias tienen que estar en metros. "
           "En el pizarrón algunas están en centímetros, así que hay que convertirlas.", "Todas las distancias deben estar en METROS", 0),
    ("u1", "Como un metro tiene cien centímetros, para pasar de centímetros a metros dividimos entre cien. "
           "Es lo mismo que recorrer el punto decimal dos lugares a la izquierda. Mira: diez centímetros son cero punto uno metros.",
     "cm ÷ 100 = m   →   el punto se recorre 2 lugares a la izquierda", 5),
    ("u2", "Otros ejemplos: cincuenta centímetros son cero punto cinco metros. Y dieciocho centímetros son cero punto dieciocho metros.",
     "50 cm = 0.5 m      18 cm = 0.18 m", 0),
]
def draw_intro4(d, t, St):
    header(d, "Primero: las unidades", 0)
    T(d, (W / 2, 190), "1 m = 100 cm", 70, WHITE, ramp(t, 0.3), True, "mm")
    T(d, (W / 2, 280), "cm  ÷ 100  →  m", 46, UNK, ramp(t, St["u1"]), True, "mm")
    a = ramp(t, St["u1"] + 1)
    if a > 0:
        digs = ["0", "1", "0"]; x0, y0, step = 760, 470, 110
        for i, ch in enumerate(digs):
            col = DIM if (i == 0 and t < St["u1"] + 3) else WHITE
            T(d, (x0 + i * step, y0), ch, 110, col, a, True, "mm")
        k = ease((t - St["u1"] - 3) / 2.5)
        p0 = x0 + 2 * step + step / 2; p1 = x0 + step / 2 - 0  # después del 0 inicial
        px = p0 + (p1 - p0) * k
        hop = abs(math.sin(math.pi * k * 2)) * 60
        d.ell([px - 12, y0 + 30 - hop, px + 12, y0 + 54 - hop], fill=mix(RED, a))
        T(d, (x0 - 140, y0), "10 cm", 50, GREY, a, True, "rm")
        T(d, (x0 + 3 * step + 40, y0), "→  0.1 m", 60, OK, ramp(t, St["u1"] + 5.8), True, "lm")
    for i, (cm, m) in enumerate((("50 cm", "0.5 m"), ("18 cm", "0.18 m"))):
        a = ramp(t, St["u2"] + i * 3.5)
        y = 680 + i * 100
        T(d, (900, y), cm, 54, WHITE, a, True, "rm")
        T(d, (960, y), "→", 54, GREY, a, True, "mm")
        T(d, (1020, y), m, 54, OK, a, True, "lm")

INTRO5 = [
    ("e0", "Lo último que necesitas es saber despejar. Despejar es dejar sola a la letra que no conocemos.",
     "Despejar = dejar sola la letra que no conocemos", 0),
    ("e1", "Mira este ejemplo: cuatro por equis es igual a veinte. El cuatro está multiplicando a la equis.",
     "4 · x = 20      el 4 está multiplicando a la x", 0),
    ("e2", "La regla es: lo que está multiplicando, pasa al otro lado dividiendo. Entonces equis es igual a veinte entre cuatro, que da cinco.",
     "Lo que multiplica → pasa al otro lado dividiendo:  x = 20 ÷ 4 = 5", 5),
    ("e3", "¡Con la palanca hacemos exactamente lo mismo! Ahora sí, vamos con el primer ejemplo.",
     "¡Con la palanca es igual! Vamos al ejemplo 1", 0),
]
def draw_intro5(d, t, St):
    header(d, "Cómo despejar", 0)
    a = ramp(t, St["e1"])
    X, SZ = 720, 90
    td = St["e2"]; f0, f1 = td + 1.2, td + 3.0
    over = {"four": RED if t >= St["e1"] + 2 and t < f1 else (DIM if t >= f1 else WHITE)}
    pos1 = eq_draw(d, [it("4", WHITE, "four"), it("·"), it("x", UNK), it("="), it("20")], X, 330, SZ, a, BG, over=over)
    if t >= td:
        a2 = ramp(t, td + 0.4)
        line2 = [it("x", UNK), it("="), fr([it("20")], [it("4", RED, "f2")])]
        pos2 = eq_draw(d, line2, X, 600, SZ, a2, BG, hide=("f2",) if t < f1 else ())
        if f0 <= t < f1:
            k = ease((t - f0) / (f1 - f0))
            (x0, y0), (x1, y1) = pos1["four"], pos2["f2"]
            T(d, (x0 + (x1 - x0) * k, y0 + (y1 - y0) * k - math.sin(math.pi * k) * 90), "4", SZ, RED, 1, False, "mm")
        if t >= f1 + 1.2:
            eq_draw(d, [it("="), it("5", OK)], X + eq_w(line2, SZ) + 20, 600, SZ, ramp(t, f1 + 1.2), BG)
    a = ramp(t, td + 0.5)
    if a > 0:
        bg = (70, 34, 34)
        d.rect([360, 800, 1560, 880], fill=mix(bg, a), r=30)
        T(d, (960, 840), "Lo que está MULTIPLICANDO pasa al otro lado DIVIDIENDO", 34, RED, a, True, "mm", bg)

OUTRO = [
    ("o0", "¡Muy bien! Repasemos los pasos para cualquier problema de palancas.", "Repaso", 0),
    ("o1", "Uno, anota los datos y marca la incógnita. Dos, pasa los centímetros a metros. Tres, escribe la fórmula. "
           "Cuatro, despeja. Cinco, sustituye los números. Seis, calcula. Y siete, comprueba.", "Los 7 pasos", 0),
    ("o2", "Y aquí tienes la fórmula ya despejada para cada caso. Puedes pausar el video y copiarla en tu cuaderno. "
           "¡Ya sabes resolver palancas! Si te equivocaste en alguno de tus turnos, regresa y vuelve a intentarlo.",
     "Copia esta tabla en tu cuaderno", 6),
]
def draw_outro(d, t, St):
    header(d, "Repaso final", 9)
    steps = ["Datos (marca la ?)", "cm → m  (÷ 100)", "Fórmula  Fe·d₁ = Fs·d₂", "Despejar", "Sustituir", "Calcular", "Comprobar"]
    card(d, [40, 130, 900, 960], ramp(t, 0.2), "Los pasos")
    for i, s_ in enumerate(steps):
        a = ramp(t, St["o1"] + i * 1.6)
        y = 230 + i * 100
        d.ell([80, y - 30, 140, y + 30], fill=mix(UNK, a, CARD))
        T(d, (110, y), str(i + 1), 32, (25, 25, 25), a, True, "mm", UNK)
        T(d, (170, y), s_, 38, WHITE, a, False, "lm", CARD)
    card(d, [960, 130, 1880, 960], ramp(t, St["o2"]), "Fórmula despejada")
    rows = [("Fe", "Fs", "d2", "d1"), ("Fs", "Fe", "d1", "d2"), ("d1", "Fs", "d2", "Fe"), ("d2", "Fe", "d1", "Fs")]
    for i, (u, q, r, p) in enumerate(rows):
        a = ramp(t, St["o2"] + 0.5 + i * 0.8)
        y = 260 + i * 175
        T(d, (1000, y), f"Si buscas {SYM[u]}:", 30, GREY, a, True, "lm", CARD)
        eq_draw(d, [it(SYM[u], UNK), it("="), fr([it(SYM[q], SCOL[q]), it("·"), it(SYM[r], SCOL[r])], [it(SYM[p], SCOL[p])])],
                1330, y, 52, a, CARD)

# ---------------------------------------------------------------- guion
def P_(**k): return Prob(**k)
PROBS = [
    P_(n=1, mode="ej", unk="Fe", vals={"Fe": (None, "kg"), "Fs": (70, "kg"), "d1": (3, "m"), "d2": (10, "cm")}, se=+1,
       title="Ejemplo 1 · buscar Fe",
       story="En el dibujo hay una caja de setenta kilos muy cerca del fulcro, y del otro lado, lejos, empujamos hacia abajo. ¿Con cuánta fuerza hay que empujar?",
       insight="Con muy poquita fuerza levantamos setenta kilos, porque nuestro brazo es treinta veces más largo que el de la caja."),
    P_(n=1, mode="tu", unk="Fe", vals={"Fe": (None, "kg"), "Fs": (120, "kg"), "d1": (2, "m"), "d2": (30, "cm")}, se=+1,
       title="¡Tu turno! 1 · buscar Fe",
       statement="Quieres levantar una roca de 120 kg con una barra. La roca está a 30 cm del fulcro y tú empujas a 2 m del fulcro. ¿Qué fuerza Fe necesitas?",
       statement_say="Quieres levantar una roca de ciento veinte kilos con una barra. La roca está a treinta centímetros del fulcro, y tú empujas a dos metros del fulcro. ¿Qué fuerza de entrada necesitas?"),
    P_(n=2, mode="ej", unk="d1", vals={"Fe": (120, "kg"), "Fs": (400, "kg"), "d1": (None, "m"), "d2": (50, "cm")}, se=+1,
       title="Ejemplo 2 · buscar d₁",
       story="Tenemos una carga de cuatrocientos kilos, y empujamos con ciento veinte kilos. En el pizarrón la fuerza de entrada aparece como efe ce, pero es lo mismo. ¿A qué distancia del fulcro hay que empujar?",
       insight="Como empujamos con menos fuerza que la carga, nuestro brazo tiene que ser más largo que el de la carga."),
    P_(n=2, mode="tu", unk="d1", vals={"Fe": (40, "kg"), "Fs": (200, "kg"), "d1": (None, "m"), "d2": (80, "cm")}, se=+1,
       title="¡Tu turno! 2 · buscar d₁",
       statement="Una caja de 200 kg está a 80 cm del fulcro. Tú puedes empujar con 40 kg. ¿A qué distancia d₁ del fulcro debes empujar?",
       statement_say="Una caja de doscientos kilos está a ochenta centímetros del fulcro. Tú puedes empujar con cuarenta kilos. ¿A qué distancia del fulcro debes empujar? Es decir, ¿cuánto vale de uno?"),
    P_(n=3, mode="ej", unk="d2", vals={"Fe": (15, "kg"), "Fs": (95, "kg"), "d1": (1.7, "m"), "d2": (None, "m")}, se=-1,
       title="Ejemplo 3 · buscar d₂",
       story="Empujamos con quince kilos y queremos equilibrar una caja de noventa y cinco kilos. ¿Dónde hay que poner la caja?",
       insight="Como la caja pesa mucho más que nuestra fuerza, tiene que ir muy cerca del fulcro."),
    P_(n=3, mode="tu", unk="d2", vals={"Fe": (18, "kg"), "Fs": (90, "kg"), "d1": (2, "m"), "d2": (None, "m")}, se=-1,
       title="¡Tu turno! 3 · buscar d₂",
       statement="Empujas con 18 kg a 2 m del fulcro. ¿A qué distancia d₂ del fulcro debes poner una carga de 90 kg para que la palanca quede en equilibrio?",
       statement_say="Empujas con dieciocho kilos a dos metros del fulcro. ¿A qué distancia del fulcro debes poner una carga de noventa kilos para que quede en equilibrio? Es decir, ¿cuánto vale de dos?"),
    P_(n=4, mode="ej", unk="Fs", vals={"Fe": (35, "kg"), "Fs": (None, "kg"), "d1": (4.5, "m"), "d2": (18, "cm")}, se=-1,
       title="Ejemplo 4 · buscar Fs",
       story="Empujamos con treinta y cinco kilos, con un brazo muy largo. ¿Cuánto peso podemos levantar?",
       insight="Como nuestro brazo es veinticinco veces más largo, levantamos veinticinco veces más peso."),
    P_(n=4, mode="tu", unk="Fs", vals={"Fe": (28, "kg"), "Fs": (None, "kg"), "d1": (3, "m"), "d2": (35, "cm")}, se=-1,
       title="¡Tu turno! 4 · buscar Fs",
       statement="Empujas con 28 kg a 3 m del fulcro. La carga está a 35 cm del fulcro. ¿Cuánta carga Fs puedes levantar?",
       statement_say="Empujas con veintiocho kilos a tres metros del fulcro. La carga está a treinta y cinco centímetros del fulcro. ¿Cuánta carga puedes levantar? Es decir, ¿cuánto vale la fuerza de salida?"),
]

SCENES = []   # (draw(d,t), segs[(st, cap)], dur)
def build():
    global SCENES
    specs = [(lambda St: (lambda d, t: draw_intro1(d, t, St)), INTRO1),
             (lambda St: (lambda d, t: draw_intro2(d, t, St)), INTRO2),
             (lambda St: (lambda d, t: draw_intro3(d, t, St)), INTRO3),
             (lambda St: (lambda d, t: draw_intro4(d, t, St)), INTRO4),
             (lambda St: (lambda d, t: draw_intro5(d, t, St)), INTRO5)]
    for i, p in enumerate(PROBS):
        chip = 1 + i
        specs.append(((lambda p, chip: (lambda St: (lambda d, t: p.draw(d, t, St, chip))))(p, chip), p.segments()))
    specs.append((lambda St: (lambda d, t: draw_outro(d, t, St)), OUTRO))
    voice, dings, ticks = [], [], []
    g, k = 0.0, 0
    for maker, segs in specs:
        t = 0.8; St = {}; caps = []
        for key, narr, cap, mind in segs:
            St[key] = t; caps.append((t, cap))
            if narr:
                p = os.path.join(WORK, f"v2seg_{k:03d}.wav"); k += 1
                cached = os.path.exists(p) and os.path.exists(p + ".txt") and open(p + ".txt").read() == narr
                if not cached:
                    subprocess.run(["piper", "-m", VOICE, "-f", p, "--length_scale", "1.12", "--sentence_silence", "0.35"],
                                   input=narr.encode(), check=True, capture_output=True)
                    open(p + ".txt", "w").write(narr)
                with wave.open(p) as w:
                    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
                voice.append((g + t, a)); dur = len(a) / SR
            else:
                dur = 0
                St[key + "_dur"] = mind
                for sec in range(int(mind)): ticks.append(g + t + sec)
            if key == "result": dings.append(g + t)
            t += max(dur, mind) + 0.7
        dur = t + 1.0
        SCENES.append((maker(St), caps, dur, g)); g += dur
    return g, voice, dings, ticks

def render_scene(i):
    fn, caps, dur, _ = SCENES[i]
    out = os.path.join(WORK, f"v2part_{i:02d}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                           "-crf", "20", "-threads", "1", out], stdin=subprocess.PIPE)
    blank = Image.new("RGB", (W, H), BG)
    for f in range(int(round(dur * FPS))):
        t = f / FPS
        im = BASE.copy(); d = Dr(im)
        fn(d, t)
        cur = ""
        for s_, c in caps:
            if t >= s_ - 0.1: cur = c
        caption(d, cur, ramp(t, 0.4))
        im = im.reduce(SS)
        fa = min(1, t / 0.35, (dur - t) / 0.35)
        if fa < 1: im = Image.blend(blank, im, max(0, fa))
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()
    return out

def wwav(p, x, sr):
    with wave.open(p, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def make_audio(total, voice, dings, ticks):
    MSR = 44100
    vt = np.zeros(int((total + 1) * SR), np.float32)
    for st, a in voice:
        i = int(st * SR); vt[i:i + len(a)] += a[: len(vt) - i]
    vt = vt / max(1e-6, np.abs(vt).max()) * 0.85
    wwav(os.path.join(WORK, "v2voz.wav"), vt, SR)
    n = int((total + 1) * MSR); tt = np.arange(n) / MSR
    mus = np.zeros(n, np.float32)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    bpm = 88; beat = 60 / bpm; bar = 4 * beat
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for b in range(int(total / bar) + 2):
        ch = chords[b % 4]; s0 = b * bar
        i0, i1 = int(s0 * MSR), min(n, int((s0 + bar) * MSR))
        if i0 >= n: break
        seg = tt[i0:i1] - s0
        env = np.minimum(1, seg / 0.5) * np.minimum(1, (bar - seg) / 0.5)
        for m in ch:
            f = hz(m)
            mus[i0:i1] += 0.045 * env * (np.sin(2 * np.pi * f * seg) + 0.25 * np.sin(2 * np.pi * 2 * f * seg + .3))
        mus[i0:i1] += 0.07 * env * np.sin(2 * np.pi * hz(ch[0] - 12) * seg)
        arp = ch + [ch[0] + 12, ch[2], ch[1], ch[0] + 12, ch[1]]
        for j in range(8):
            s_ = s0 + j * beat / 2; a0 = int(s_ * MSR); a1 = min(n, a0 + int(0.9 * MSR))
            if a0 >= n: break
            x = tt[a0:a1] - s_; f = hz(arp[j] + 12)
            mus[a0:a1] += 0.03 * np.exp(-4 * x) * (np.sin(2 * np.pi * f * x) + 0.2 * np.sin(2 * np.pi * 3 * f * x))
        if b % 2 == 0:  # golpe suave
            a0 = i0; a1 = min(n, a0 + int(0.25 * MSR)); x = tt[a0:a1] - s0
            mus[a0:a1] += 0.08 * np.exp(-18 * x) * np.sin(2 * np.pi * (55 + 60 * np.exp(-30 * x)) * x)
    mus *= np.clip(np.minimum(tt / 2, (total - tt) / 3), 0, 1)
    mus = mus / np.abs(mus).max() * 0.8
    fx = np.zeros(n, np.float32)
    for st in dings:
        a0 = int(st * MSR); a1 = min(n, a0 + int(1.5 * MSR)); x = tt[a0:a1] - st
        for f, g in ((1046.5, 1), (1318.5, .7), (1568, .5)):
            fx[a0:a1] += 0.12 * g * np.exp(-3 * x) * np.sin(2 * np.pi * f * x)
    for st in ticks:
        a0 = int(st * MSR); a1 = min(n, a0 + int(0.05 * MSR)); x = tt[a0:a1] - st
        fx[a0:a1] += 0.15 * np.exp(-80 * x) * np.sin(2 * np.pi * 1800 * x)
    wwav(os.path.join(WORK, "v2musica.wav"), mus, MSR)
    wwav(os.path.join(WORK, "v2fx.wav"), fx, MSR)

if __name__ == "__main__":
    out = sys.argv[1]
    only = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
    total, voice, dings, ticks = build()
    BASE = make_base()
    print("duración", round(total, 1), "s, escenas", len(SCENES), flush=True)
    idx = only or list(range(len(SCENES)))
    with Pool(4) as pool:
        parts = pool.map(render_scene, idx)
    if only: sys.exit(0)
    make_audio(total, voice, dings, ticks)
    lst = os.path.join(WORK, "v2list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(WORK, "v2silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", os.path.join(WORK, "v2voz.wav"),
        "-i", os.path.join(WORK, "v2musica.wav"), "-i", os.path.join(WORK, "v2fx.wav"), "-filter_complex",
        "[1:a]aresample=44100,volume=1.15,asplit=2[v][sc];"
        "[2:a]volume=0.32[m];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[md];"
        "[3:a]volume=0.8[fx];[v][md][fx]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.85[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
        "-movflags", "+faststart", out], check=True)
    print("ok", out)
