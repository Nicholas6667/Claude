import math, subprocess, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw
from helpers import *

DIR = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(DIR, "voices/es-carlfm-x-low.onnx")
SR = 16000
GAP = 0.6

def tts(txt, idx):
    p = os.path.join(DIR, f"seg_{idx}.wav")
    subprocess.run(["piper", "-m", VOICE, "-f", p, "--length_scale", "1.1"], input=txt.encode(),
                   check=True, capture_output=True)
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# ---------- escenas: cada una tiene segmentos (narración, subtítulo) ----------
INTRO = [
  ("Hola. Hoy vamos a resolver cuatro ejercicios de palancas. Una palanca está en equilibrio cuando los dos lados pesan lo mismo.",
   "Una palanca está en equilibrio cuando los dos lados \"pesan\" lo mismo."),
  ("Efe e es la fuerza de entrada, la que tú aplicas. Efe ese es la fuerza de salida, la carga que se mueve.",
   "Fe = fuerza de entrada · Fs = fuerza de salida"),
  ("De uno es la distancia del fulcro a la fuerza de entrada, y de dos es la distancia del fulcro a la fuerza de salida.",
   "d₁ y d₂ se miden desde el fulcro (el triángulo)."),
  ("La regla de oro es: fuerza de entrada por de uno, es igual a fuerza de salida por de dos.",
   "Regla de oro: fuerza × distancia de un lado = fuerza × distancia del otro."),
  ("Muy importante: las distancias deben estar en las mismas unidades. Para pasar de centímetros a metros, dividimos entre cien.",
   "Antes de sustituir, convierte los centímetros a metros."),
]

def intro_scene(T):
    def sc(d, t):
        text(d, (W / 2, 70), "Ley de la Palanca", f_title, WHITE, ramp(t, 0), "mm")
        ang = 0.15 * math.sin(2 * t) * math.exp(-0.15 * t)
        lever(d, 360, 380, +1, 260, 150, ang, {"Fe": "Fe", "Fs": "Fs", "d1": "d₁", "d2": "d₂"}, ramp(t, 0.8))
        x = 700
        rows = [(T[1], "Fe = fuerza de entrada (la que tú aplicas)", EFF),
                (T[1] + 3.5, "Fs = fuerza de salida (la carga que se mueve)", OUT),
                (T[2], "d₁ = distancia del fulcro (Δ) a Fe", WHITE),
                (T[2] + 3.5, "d₂ = distancia del fulcro (Δ) a Fs", WHITE)]
        for i, (s, r, col) in enumerate(rows):
            text(d, (x - 40, 170 + i * 48), r, f_small, col, ramp(t, s))
        a = ramp(t, T[3])
        if a > 0:
            d.rounded_rectangle([x - 20, 390, x + 520, 480], 14, outline=mix(UNK, a), width=4)
            text(d, (x + 250, 435), "Fe · d₁ = Fs · d₂", f_big, UNK, a, "mm")
        text(d, (x + 250, 520), "¡Las distancias deben estar en las MISMAS unidades!", f_small, WHITE, ramp(t, T[4]), "mm")
        text(d, (x + 250, 555), "1 m = 100 cm   →   cm ÷ 100 = m", f_small, GREY, ramp(t, T[4] + 3), "mm")
    return sc

def problem_scene(n, se, Le, Lo, lab0, lab_res, steps):
    def make(T):
        rt = T[4]
        def sc(d, t):
            text(d, (40, 30), f"Ejercicio {n}", f_big, WHITE, ramp(t, 0))
            if t < rt: ang, lab = 0.13 * math.sin(1.6 * t), lab0
            else: ang, lab = 0.13 * math.sin(1.6 * t) * math.exp(-2.5 * (t - rt)), lab_res
            lever(d, 320, 400, se, Le, Lo, ang, lab, ramp(t, 0.3))
            if t > rt + 1.2:
                text(d, (320, 560), "¡Equilibrio! ✓", f_mid, OK, ramp(t, rt + 1.2), "mm")
            x, y = 660, 95
            for i, (title, lines, col) in enumerate(steps):
                a = ramp(t, T[i])
                if a <= 0: continue
                text(d, (x, y), title, f_small, GREY, a); y += 30
                for j, ln in enumerate(lines):
                    c = col if j == len(lines) - 1 else WHITE
                    text(d, (x + 20, y), ln, f_mid if col == OK else f_txt, c, a); y += 36
                y += 10
        return sc
    return make

P = []
P.append((problem_scene(1, +1, 300, 75,
    {"Fe": "Fe = ?", "Fe_c": UNK, "Fs": "Fs = 70 kg", "d1": "d₁ = 3 m", "d2": "d₂ = 10 cm"},
    {"Fe": "Fe ≈ 2.33 kg", "Fe_c": OK, "Fs": "Fs = 70 kg", "d1": "d₁ = 3 m", "d2": "d₂ = 0.1 m"},
    [("1) Datos", ["Fs = 70 kg   d₁ = 3 m", "d₂ = 10 cm   Fe = ?"], UNK),
     ("2) Convertir unidades", ["d₂ = 10 cm ÷ 100 = 0.1 m"], WHITE),
     ("3) Fórmula y despeje", ["Fe · d₁ = Fs · d₂", "Fe = (Fs · d₂) ÷ d₁"], WHITE),
     ("4) Sustituir", ["Fe = (70 · 0.1) ÷ 3 = 7 ÷ 3"], WHITE),
     ("5) Resultado", ["Fe ≈ 2.33 kg"], OK)]),
  [("Ejercicio uno. Buscamos la fuerza de entrada. Los datos son: fuerza de salida, setenta kilos. De uno, tres metros. Y de dos, diez centímetros.",
    "Buscamos la fuerza de entrada Fe. Anotamos los datos del dibujo."),
   ("De dos está en centímetros. Diez entre cien nos da cero punto uno metros.",
    "d₂ está en centímetros: la pasamos a metros dividiendo entre 100."),
   ("Escribimos la fórmula. Como de uno está multiplicando a la fuerza de entrada, pasa al otro lado dividiendo.",
    "d₁ está multiplicando a Fe, así que pasa al otro lado dividiendo."),
   ("Sustituimos. Setenta por cero punto uno es siete. Y siete entre tres es dos punto treinta y tres.",
    "70 × 0.1 = 7, y 7 ÷ 3 ≈ 2.33"),
   ("Resultado: la fuerza de entrada es de dos punto treinta y tres kilos. Con muy poca fuerza levantamos setenta kilos, porque el brazo es mucho más largo.",
    "Con solo 2.33 kg levantamos 70 kg, porque el brazo de Fe es mucho más largo.")]))
P.append((problem_scene(2, +1, 200, 120,
    {"Fe": "Fc = 120 kg", "Fs": "Fs = 400 kg", "d1": "d₁ = ?", "d1_c": UNK, "d2": "d₂ = 50 cm"},
    {"Fe": "Fc = 120 kg", "Fs": "Fs = 400 kg", "d1": "d₁ ≈ 1.67 m", "d1_c": OK, "d2": "d₂ = 0.5 m"},
    [("1) Datos", ["Fs = 400 kg   Fc(Fe) = 120 kg", "d₂ = 50 cm   d₁ = ?"], UNK),
     ("2) Convertir unidades", ["d₂ = 50 cm ÷ 100 = 0.5 m"], WHITE),
     ("3) Fórmula y despeje", ["Fe · d₁ = Fs · d₂", "d₁ = (Fs · d₂) ÷ Fe"], WHITE),
     ("4) Sustituir", ["d₁ = (400 · 0.5) ÷ 120 = 200 ÷ 120"], WHITE),
     ("5) Resultado", ["d₁ ≈ 1.67 m  (166.7 cm)"], OK)]),
  [("Ejercicio dos. Ahora la incógnita es la distancia de uno. La fuerza de entrada es de ciento veinte kilos, la de salida de cuatrocientos kilos, y de dos mide cincuenta centímetros.",
    "La incógnita es d₁. Fc = 120 kg es la fuerza de entrada."),
   ("Convertimos: cincuenta centímetros son cero punto cinco metros.",
    "50 cm ÷ 100 = 0.5 m"),
   ("De uno está multiplicando a la fuerza de entrada, así que la fuerza de entrada pasa al otro lado dividiendo.",
    "Fe pasa al otro lado dividiendo."),
   ("Cuatrocientos por cero punto cinco es doscientos. Doscientos entre ciento veinte es uno punto sesenta y siete.",
    "400 × 0.5 = 200, y 200 ÷ 120 ≈ 1.67"),
   ("Resultado: de uno mide uno punto sesenta y siete metros, es decir, unos ciento sesenta y siete centímetros.",
    "Hay que empujar a 1.67 m del fulcro para equilibrar los 400 kg.")]))
P.append((problem_scene(3, -1, 300, 70,
    {"Fe": "Fe = 15 kg", "Fs": "95 kg", "d1": "d₁ = 1.7 m", "d2": "d₂ = ?", "d2_c": UNK},
    {"Fe": "Fe = 15 kg", "Fs": "95 kg", "d1": "d₁ = 1.7 m", "d2": "d₂ ≈ 0.27 m", "d2_c": OK},
    [("1) Datos", ["Fe = 15 kg   d₁ = 1.7 m", "Fs = 95 kg   d₂ = ?"], UNK),
     ("2) Convertir unidades", ["Todo ya está en metros ✓"], WHITE),
     ("3) Fórmula y despeje", ["Fe · d₁ = Fs · d₂", "d₂ = (Fe · d₁) ÷ Fs"], WHITE),
     ("4) Sustituir", ["d₂ = (15 · 1.7) ÷ 95 = 25.5 ÷ 95"], WHITE),
     ("5) Resultado", ["d₂ ≈ 0.268 m  (26.8 cm)"], OK)]),
  [("Ejercicio tres. Buscamos de dos, la distancia a la que debe ir la caja de noventa y cinco kilos. La fuerza de entrada es de quince kilos, y de uno mide uno punto siete metros.",
    "Buscamos d₂: a qué distancia del fulcro va la caja de 95 kg."),
   ("Aquí no hay centímetros, así que no hay que convertir nada.",
    "No hay centímetros: no hay que convertir."),
   ("De dos está multiplicando a la fuerza de salida, entonces la fuerza de salida pasa dividiendo.",
    "Fs pasa al otro lado dividiendo."),
   ("Quince por uno punto siete es veinticinco punto cinco. Y veinticinco punto cinco entre noventa y cinco es cero punto dos seis ocho.",
    "15 × 1.7 = 25.5, y 25.5 ÷ 95 ≈ 0.268"),
   ("Resultado: de dos mide cero punto dos seis ocho metros, unos veintiséis punto ocho centímetros. La caja va muy cerca del fulcro.",
    "La caja debe ir a unos 26.8 cm del fulcro.")]))
P.append((problem_scene(4, -1, 300, 60,
    {"Fe": "Fe = 35 kg", "Fs": "Fs = ?", "Fs_c": UNK, "d1": "d₁ = 4.5 m", "d2": "d₂ = 18 cm"},
    {"Fe": "Fe = 35 kg", "Fs": "Fs = 875 kg", "Fs_c": OK, "d1": "d₁ = 4.5 m", "d2": "d₂ = 0.18 m"},
    [("1) Datos", ["Fe = 35 kg   d₁ = 4.5 m", "d₂ = 18 cm   Fs = ?"], UNK),
     ("2) Convertir unidades", ["d₂ = 18 cm ÷ 100 = 0.18 m"], WHITE),
     ("3) Fórmula y despeje", ["Fe · d₁ = Fs · d₂", "Fs = (Fe · d₁) ÷ d₂"], WHITE),
     ("4) Sustituir", ["Fs = (35 · 4.5) ÷ 0.18 = 157.5 ÷ 0.18"], WHITE),
     ("5) Resultado", ["Fs = 875 kg"], OK)]),
  [("Ejercicio cuatro. Ahora buscamos la fuerza de salida. La fuerza de entrada es de treinta y cinco kilos, de uno mide cuatro punto cinco metros, y de dos, dieciocho centímetros.",
    "Buscamos la fuerza de salida Fs."),
   ("Convertimos: dieciocho centímetros son cero punto dieciocho metros.",
    "18 cm ÷ 100 = 0.18 m"),
   ("La fuerza de salida está multiplicando a de dos, así que de dos pasa al otro lado dividiendo.",
    "d₂ pasa al otro lado dividiendo."),
   ("Treinta y cinco por cuatro punto cinco es ciento cincuenta y siete punto cinco. Y eso entre cero punto dieciocho da ochocientos setenta y cinco.",
    "35 × 4.5 = 157.5, y 157.5 ÷ 0.18 = 875"),
   ("Resultado: la fuerza de salida es de ochocientos setenta y cinco kilos. Con solo treinta y cinco kilos y un brazo largo, levantamos muchísimo peso.",
    "¡Con 35 kg y un brazo de 4.5 m levantamos 875 kg!")]))

OUTRO = [("En resumen: anota los datos, convierte los centímetros a metros, escribe la fórmula, despeja la incógnita, sustituye, y obtén el resultado. ¡Muy bien, ahora inténtalo tú!",
          "Datos → convertir a metros → fórmula → despejar → sustituir → resultado")]
def outro_scene(T):
    def sc(d, t):
        text(d, (W / 2, 90), "Resumen", f_title, WHITE, ramp(t, 0), "mm")
        rows = [("Ejercicio 1", "Fe = (70 · 0.1) ÷ 3", "Fe ≈ 2.33 kg"),
                ("Ejercicio 2", "d₁ = (400 · 0.5) ÷ 120", "d₁ ≈ 1.67 m"),
                ("Ejercicio 3", "d₂ = (15 · 1.7) ÷ 95", "d₂ ≈ 0.268 m"),
                ("Ejercicio 4", "Fs = (35 · 4.5) ÷ 0.18", "Fs = 875 kg")]
        for i, (a, b, c) in enumerate(rows):
            al = ramp(t, 0.8 + i * 0.8); y = 190 + i * 80
            text(d, (170, y), a, f_mid, GREY, al); text(d, (420, y), b, f_txt, WHITE, al); text(d, (900, y), c, f_mid, OK, al)
        text(d, (W / 2, 560), "Fe · d₁ = Fs · d₂", f_big, UNK, ramp(t, 4.5), "mm")
    return sc

specs = [(intro_scene, INTRO)] + P + [(outro_scene, OUTRO)]

# ---------- audio de voz y tiempos ----------
voice = []          # (inicio_global, muestras)
scenes = []
g = 0.0; k = 0
for maker, segs in specs:
    t = 1.0; T = []; caps = []
    for narr, cap in segs:
        a = tts(narr, k); k += 1
        T.append(t); caps.append((t, cap)); voice.append((g + t, a))
        t += len(a) / SR + GAP
    dur = t + 1.5
    scenes.append((maker(T), caps, dur)); g += dur
total = g
vt = np.zeros(int(total * SR) + SR, np.float32)
for st, a in voice:
    i = int(st * SR); vt[i:i + len(a)] += a
vt = vt / max(1e-6, np.abs(vt).max()) * 0.9
def wwav(p, x, sr):
    with wave.open(p, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
wwav(os.path.join(DIR, "voz.wav"), vt, SR)

# ---------- música de fondo (generada) ----------
MSR = 44100
n = int((total + 1) * MSR); tt = np.arange(n) / MSR
mus = np.zeros(n, np.float32)
bpm = 92; beat = 60 / bpm; bar = 4 * beat
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # Am F C G
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
nb = int(total / bar) + 2
for b in range(nb):
    ch = chords[b % 4]; s0 = b * bar
    i0, i1 = int(s0 * MSR), min(n, int((s0 + bar) * MSR))
    if i0 >= n: break
    seg = tt[i0:i1] - s0
    env = np.minimum(1, seg / 0.4) * np.minimum(1, (bar - seg) / 0.4)
    for m in ch:   # pad suave
        f = hz(m)
        mus[i0:i1] += 0.05 * env * (np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(2 * np.pi * 2 * f * seg + .3))
    f = hz(ch[0] - 12)  # bajo
    mus[i0:i1] += 0.07 * env * np.sin(2 * np.pi * f * seg)
    arp = ch + [ch[0] + 12, ch[2], ch[1], ch[0] + 12, ch[1]]
    for j in range(8):   # arpegio tipo campana
        s = s0 + j * beat / 2; a0 = int(s * MSR); a1 = min(n, a0 + int(0.9 * MSR))
        if a0 >= n: break
        x = tt[a0:a1] - s; f = hz(arp[j] + 12)
        mus[a0:a1] += 0.035 * np.exp(-4 * x) * (np.sin(2 * np.pi * f * x) + 0.2 * np.sin(2 * np.pi * 3 * f * x))
fade = np.minimum(1, np.minimum(tt / 2, (total - tt) / 3).clip(0))
mus *= fade
mus = mus / np.abs(mus).max() * 0.9
wwav(os.path.join(DIR, "musica.wav"), mus, MSR)

# ---------- video ----------
silent = os.path.join(DIR, "silent.mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", silent],
    stdin=subprocess.PIPE)
blank = Image.new("RGB", (W, H), BG)
for fn, caps, dur in scenes:
    for i in range(int(dur * FPS)):
        t = i / FPS
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        fn(d, t)
        cur = ""
        for s, c in caps:
            if t >= s: cur = c
        caption(d, cur, ramp(t, 0.5))
        f = min(1, t / 0.4, (dur - t) / 0.4)
        if f < 1: img = Image.blend(blank, img, max(0, f))
        ff.stdin.write(img.tobytes())
ff.stdin.close(); ff.wait()

# ---------- mezcla: música baja y se atenúa cuando habla la voz ----------
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", os.path.join(DIR, "voz.wav"),
    "-i", os.path.join(DIR, "musica.wav"), "-filter_complex",
    "[1:a]aresample=44100,volume=1.2,asplit=2[v][sc];"
    "[2:a]volume=0.35[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
    "[v][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
    "-movflags", "+faststart", sys.argv[1]], check=True)
print("ok", round(total, 1), "s")
