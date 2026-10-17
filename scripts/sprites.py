"""Sprites del banner en ASCII. '.' es transparente.

Personaje PROVISIONAL dibujado a mano: se sustituirá por el que se genere con
Gemini/ChatGPT. Para cambiarlo basta con reemplazar WALK y HERO_PAL.
"""

HERO_PAL = {
    "o": "#06121B",  # contorno
    "h": "#3A2416",  # pelo
    "s": "#D9A07A",  # piel
    "S": "#B97F5B",  # sombra de piel
    "c": "#22C3D6",  # sudadera
    "C": "#13738A",  # sombra de sudadera
    "p": "#1E3A52",  # pantalón
    "P": "#142A3D",  # sombra de pantalón
    "w": "#E6F3F6",  # zapatillas
}

_HEAD = [
    "....oooooo....",
    "...ohhhhhho...",
    "..ohhhhhhhho..",
    "..ohhhhhhsso..",
    "..ohhhhhsosso.",
    "...ohhhhsssso.",
    "....oosssSSo..",
    "....occcccco..",
    "...occcccccco.",
    "..occcccccccCo",
    "..occcccccccCo",
    "..osccccccccCo",
    "...occcccccCo.",
    "...ocCCCCCCo..",
]

_LEGS = {
    "idle": [
        "...oppppppo...",
        "...oppoopPo...",
        "...oppo.oPo...",
        "...oppo.oPo...",
        "...oppo.oPo...",
        "...owwo.owwo..",
        "..oowwo.owwwo.",
        "..oooo..ooooo.",
    ],
    "a": [
        "...opppppPo...",
        "..opppopPPo...",
        ".oppo..oPPo...",
        ".oppo...oPo...",
        "oppo....oPo...",
        "owwo....owwo..",
        "owwwo...owwwo.",
        "ooooo...ooooo.",
    ],
    "b": [
        "...oppppppo...",
        "...opppoppPo..",
        "...oPPo.oppo..",
        "..oPo....oppo.",
        "..oPo....oppo.",
        "..owwo...owwo.",
        ".owwwo...owwwo",
        ".ooooo...ooooo",
    ],
}

# fotogramas: 0 = pasada A, 1 = juntos, 2 = pasada B
WALK = [_HEAD + _LEGS["a"], _HEAD + _LEGS["idle"], _HEAD + _LEGS["b"]]
assert all(len(r) == 14 for f in WALK for r in f), "todas las filas deben medir 14"

CHURCH_PAL = {"w": "#E6F3F6", "o": "#0A1822", "y": "#F2C14E", "r": "#9FE7F0"}
CHURCH = [
    "...r...",
    "..rrr..",
    "...r...",
    ".wwwww.",
    "wwwywww",
    "wwwywww",
]

FLAG_PAL = {"o": "#E6F3F6", "c": "#22C3D6"}
FLAG = [
    "cc",
    "co",
    "o.",
    "o.",
    "o.",
    "o.",
]

ROCKET_PAL = {"o": "#06121B", "w": "#E6F3F6", "g": "#9FB8C4", "c": "#22C3D6", "r": "#F28C4B"}
ROCKET = [
    "....o....",
    "...owo...",
    "..owwwo..",
    "..owwgo..",
    "..occco..",
    "..occco..",
    "..owwgo..",
    "..owwgo..",
    ".rowwgor.",
    ".rowwgor.",
    "rrowwgorr",
    "r.ooooo.r",
]

FLAME_PAL = {"y": "#F2C14E", "r": "#F28C4B"}
FLAME = [
    "..ryyyr..",
    "...ryr...",
    "....r....",
]
