"""Shusha font encoding mappings.

This module provides character mappings for Shusha legacy Devanagari fonts,
used for Marathi and Hindi text.

Shusha encoding uses Unicode-range characters mapped to Devanagari glyphs.
Common text signatures include "ÉÉ®úiÉ" and "½þè".

The conversion process involves:
1. Replace multi-character sequences first (ligatures, conjuncts)
2. Replace single character mappings
3. Apply post-processing for matra reordering
"""

# Shusha to Unicode mapping
# Shusha uses extended Latin characters mapped to Devanagari
SHUSHA_MAPPINGS: dict[str, str] = {
    # Vowels (स्वर) - Independent forms
    "A": "अ",  # A
    "AA": "आ",  # Aa
    "B": "इ",  # I
    "C": "उ",  # U
    "D": "ऊ",  # Uu
    "F": "ए",  # E
    "G": "ऋ",  # Ri
    # Consonants (व्यंजन)
    "\xc9": "क",  # É -> क (Ka)
    "\xca": "ख",  # Ê -> ख (Kha)
    "\xc8": "ग",  # È -> ग (Ga)
    "\xcb": "घ",  # Ë -> घ (Gha)
    "\xcc": "ङ",  # Ì -> ङ (Nga)
    "\xcd": "च",  # Í -> च (Cha)
    "\xce": "छ",  # Î -> छ (Chha)
    "\xcf": "ज",  # Ï -> ज (Ja)
    "\xd0": "झ",  # Ð -> झ (Jha)
    "\xd1": "ञ",  # Ñ -> ञ (Nya)
    "\xd2": "ट",  # Ò -> ट (Ta retroflex)
    "\xd3": "ठ",  # Ó -> ठ (Tha retroflex)
    "\xd4": "ड",  # Ô -> ड (Da retroflex)
    "\xd5": "ढ",  # Õ -> ढ (Dha retroflex)
    "\xd6": "ण",  # Ö -> ण (Na retroflex)
    "i": "त",  # i -> त (Ta)
    "\xd8": "थ",  # Ø -> थ (Tha)
    "\xd9": "द",  # Ù -> द (Da)
    "\xda": "ध",  # Ú -> ध (Dha)
    "\xdb": "न",  # Û -> न (Na)
    "\xdc": "प",  # Ü -> प (Pa)
    "\xdd": "फ",  # Ý -> फ (Pha)
    "\xde": "ब",  # Þ -> ब (Ba)
    "\xdf": "भ",  # ß -> भ (Bha)
    "\xe0": "म",  # à -> म (Ma)
    "\xe1": "य",  # á -> य (Ya)
    "\xae": "र",  # ® -> र (Ra)
    "\xe3": "ल",  # ã -> ल (La)
    "\xe4": "व",  # ä -> व (Va)
    "\xe5": "श",  # å -> श (Sha)
    "\xe6": "ष",  # æ -> ष (Sha retroflex)
    "\xe7": "स",  # ç -> स (Sa)
    "\xe8": "ह",  # è -> ह (Ha)
    "\xe9": "ळ",  # é -> ळ (La - Marathi)
    # Matras (vowel signs)
    "\xea": "ा",  # ê -> ा (Aa matra)
    "\xeb": "ि",  # ë -> ि (I matra)
    "\xec": "ी",  # ì -> ी (Ii matra)
    "\xfa": "ु",  # ú -> ु (U matra)
    "\xfb": "ू",  # û -> ू (Uu matra)
    "\xee": "ृ",  # î -> ृ (Ri matra)
    "\xef": "े",  # ï -> े (E matra)
    "\xf0": "ै",  # ð -> ै (Ai matra)
    "\xf1": "ो",  # ñ -> ो (O matra)
    "\xf2": "ौ",  # ò -> ौ (Au matra)
    # Special characters
    "\xbd": "्",  # ½ -> ् (Halant/Virama)
    "\xfe": "ं",  # þ -> ं (Anusvara)
    "\xf5": "ँ",  # õ -> ँ (Chandrabindu)
    "\xf6": "ः",  # ö -> ः (Visarga)
    "\xf7": "़",  # ÷ -> ़ (Nukta)
    "\xa4": "।",  # ¤ -> । (Danda)
    "\xa5": "॥",  # ¥ -> ॥ (Double danda)
    # Numbers
    "0": "०",
    "1": "१",
    "2": "२",
    "3": "३",
    "4": "४",
    "5": "५",
    "6": "६",
    "7": "७",
    "8": "८",
    "9": "९",
    # Punctuation (keep as-is)
    ".": ".",
    ",": ",",
    "!": "!",
    "?": "?",
    ":": ":",
    ";": ";",
    "-": "-",
    "(": "(",
    ")": ")",
    "/": "/",
    "+": "+",
    "=": "=",
}

# Ligatures - multi-character sequences that map to single Unicode sequences
SHUSHA_LIGATURES: dict[str, str] = {
    # Extended vowels
    "AA": "आ",  # Aa
    "BB": "ई",  # Ii
    "CC": "ऊ",  # Uu - alternate
    "FF": "ऐ",  # Ai
    # Conjuncts
    "\xf8": "क्ष",  # ø -> क्ष (Ksha)
    "\xf9": "ज्ञ",  # ù -> ज्ञ (Gya/Dnya)
    "\xf3": "त्र",  # ó -> त्र (Tra)
    "\xf4": "श्र",  # ô -> श्र (Shra)
    # Common Shusha patterns (from signatures)
    "\xc9\xc9\xae\xfa": "कार",  # ÉÉ®ú -> कार
    "\xc9\xc9\xae\xfai\xc9": "कारतक",  # ÉÉ®úiÉ
    "\xbd\xfe\xe8": "्ंह",  # ½þè
    # Matra combinations
    "\xea\xef": "ो",  # aa + e matra -> o matra
    "\xea\xf0": "ौ",  # aa + ai matra -> au matra
    # Half form + consonant patterns
    "\xc9\xbd": "क्",  # Ka + halant -> Ka half
    "\xca\xbd": "ख्",  # Kha + halant -> Kha half
    "\xc8\xbd": "ग्",  # Ga + halant -> Ga half
    "\xcb\xbd": "घ्",  # Gha + halant -> Gha half
    "\xcd\xbd": "च्",  # Cha + halant -> Cha half
    "\xcf\xbd": "ज्",  # Ja + halant -> Ja half
    "i\xbd": "त्",  # Ta + halant -> Ta half
    "\xd9\xbd": "द्",  # Da + halant -> Da half
    "\xdb\xbd": "न्",  # Na + halant -> Na half
    "\xdc\xbd": "प्",  # Pa + halant -> Pa half
    "\xdd\xbd": "फ्",  # Pha + halant -> Pha half
    "\xde\xbd": "ब्",  # Ba + halant -> Ba half
    "\xe0\xbd": "म्",  # Ma + halant -> Ma half
    "\xe3\xbd": "ल्",  # La + halant -> La half
    "\xe5\xbd": "श्",  # Sha + halant -> Sha half
    "\xe7\xbd": "स्",  # Sa + halant -> Sa half
    "\xe8\xbd": "ह्",  # Ha + halant -> Ha half
}

# Half forms - consonants with halant
SHUSHA_HALF_FORMS: dict[str, str] = {
    "\x80": "क्",  # Ka half
    "\x81": "ख्",  # Kha half
    "\x82": "ग्",  # Ga half
    "\x83": "घ्",  # Gha half
    "\x84": "च्",  # Cha half
    "\x85": "ज्",  # Ja half
    "\x86": "झ्",  # Jha half
    "\x87": "ञ्",  # Nya half
    "\x88": "ट्",  # Ta (retroflex) half
    "\x89": "ठ्",  # Tha (retroflex) half
    "\x8a": "ण्",  # Na (retroflex) half
    "\x8b": "त्",  # Ta half
    "\x8c": "थ्",  # Tha half
    "\x8d": "द्",  # Da half
    "\x8e": "ध्",  # Dha half
    "\x8f": "न्",  # Na half
    "\x90": "प्",  # Pa half
    "\x91": "फ्",  # Pha half
    "\x92": "ब्",  # Ba half
    "\x93": "भ्",  # Bha half
    "\x94": "म्",  # Ma half
    "\x95": "य्",  # Ya half
    "\x96": "ल्",  # La half
    "\x97": "व्",  # Va half
    "\x98": "श्",  # Sha half
    "\x99": "ष्",  # Sha (retroflex) half
    "\x9a": "स्",  # Sa half
    "\x9b": "ह्",  # Ha half
    "\x9c": "ळ्",  # La (Marathi) half
}
