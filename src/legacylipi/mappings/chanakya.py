"""Chanakya font encoding mappings.

This module provides character mappings for Chanakya legacy Devanagari fonts,
commonly used in Hindi/Sanskrit academic publishing.

Chanakya encoding maps ASCII characters to Devanagari glyphs visually.
It is similar to KrutiDev but with different character assignments.

The conversion process involves:
1. Replace multi-character sequences first (ligatures, conjuncts)
2. Replace single character mappings
3. Apply post-processing for matra reordering
"""

# Chanakya to Unicode mapping
# Maps ASCII/extended-ASCII characters to Devanagari Unicode
CHANAKYA_MAPPINGS: dict[str, str] = {
    # Vowels (स्वर) - Independent forms
    "v": "अ",  # A
    "b": "इ",  # I
    "m": "उ",  # U
    ",": "ए",  # E
    # Consonants (व्यंजन)
    "d": "क",  # Ka
    "x": "ग",  # Ga
    "p": "च",  # Cha
    "N": "छ",  # Chha
    "t": "ज",  # Ja
    ">": "झ",  # Jha
    "V": "ट",  # Ta (retroflex)
    "B": "ठ",  # Tha (retroflex)
    "M": "ड",  # Da (retroflex)
    "<": "ढ",  # Dha (retroflex)
    "r": "त",  # Ta
    "n": "द",  # Da
    "u": "न",  # Na
    "i": "प",  # Pa
    "Q": "फ",  # Pha
    "c": "ब",  # Ba
    "e": "म",  # Ma
    ";": "य",  # Ya
    "j": "र",  # Ra
    "y": "ल",  # La
    "o": "व",  # Va
    "l": "स",  # Sa
    "g": "ह",  # Ha
    "G": "ळ",  # La (Marathi)
    # Matras (vowel signs)
    "k": "ा",  # Aa matra
    "f": "ि",  # I matra
    "h": "ी",  # Ii matra
    "q": "ु",  # U matra
    "w": "ू",  # Uu matra
    "`": "ृ",  # Ri matra
    "s": "े",  # E matra
    "S": "ै",  # Ai matra
    # Special characters
    "~": "्",  # Halant/Virama
    "a": "ं",  # Anusvara
    "\xa1": "ँ",  # Chandrabindu (¡)
    "%": "ः",  # Visarga
    "A": "।",  # Danda
    "\xde": "॥",  # Double danda (Þ)
    # Half consonants (हलंत forms)
    "D": "क्",  # Ka half
    "R": "ख्",  # Kha half
    "T": "ग्",  # Ga half
    "W": "घ्",  # Gha half
    "P": "च्",  # Cha half
    "X": "ज्",  # Ja half
    "Y": "झ्",  # Jha half
    "K": "ट्",  # Ta (retroflex) half
    "L": "ठ्",  # Tha (retroflex) half
    "J": "ण्",  # Na (retroflex) half
    "E": "त्",  # Ta half
    "F": "थ्",  # Tha half
    "H": "द्",  # Da half
    "I": "ध्",  # Dha half
    "C": "न्",  # Na half
    "O": "प्",  # Pa half
    "U": "फ्",  # Pha half
    "Z": "ब्",  # Ba half
    "\xc2": "भ्",  # Bha half (Â)
    "\xc4": "म्",  # Ma half (Ä)
    "\xc6": "य्",  # Ya half (Æ)
    "\xc8": "ल्",  # La half (È)
    "\xca": "व्",  # Va half (Ê)
    "\xcc": "श्",  # Sha half (Ì)
    "\xce": "ष्",  # Sha (retroflex) half (Î)
    "\xd0": "स्",  # Sa half (Ð)
    "\xd2": "ह्",  # Ha half (Ò)
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
    "!": "!",
    "?": "?",
    ":": ":",
    "-": "-",
    "(": "(",
    ")": ")",
    "/": "/",
    "+": "+",
    "=": "=",
}

# Ligatures - multi-character sequences that map to single Unicode sequences
# These MUST be processed before single-character mappings
CHANAKYA_LIGATURES: dict[str, str] = {
    # Extended vowels
    "vk": "आ",  # Aa
    "bZ": "ई",  # Ii
    "\xc5": "ऊ",  # Uu (Å)
    ",s": "ऐ",  # Ai
    "vks": "ओ",  # O
    "vkS": "औ",  # Au
    # Matra combinations
    "ks": "ो",  # O matra
    "kS": "ौ",  # Au matra
    # Multi-char consonants
    "[k": "ख",  # Kha
    "?k": "घ",  # Gha
    ".k": "ण",  # Na (retroflex)
    "Fk": "थ",  # Tha
    "/k": "ध",  # Dha
    "Hk": "भ",  # Bha
    "'k": "श",  # Sha
    '"k': "ष",  # Sha (retroflex)
    # Common conjuncts
    "\xd4": "क्ष",  # Ksha (Ô)
    "\xd6": "ज्ञ",  # Gya/Dnya (Ö)
    "\xd8": "श्र",  # Shra (Ø)
    "\xda": "त्र",  # Tra (Ú)
    # Common word patterns
    "Hkkjr": "भारत",
    "ns'k": "देश",
    "gS": "है",
    "fd": "कि",
    "dh": "की",
    "esa": "में",
    "ls": "से",
    "dk": "का",
    "ds": "के",
    "dks": "को",
}

# Half forms - consonants with halant
CHANAKYA_HALF_FORMS: dict[str, str] = {
    "D": "क्",
    "R": "ख्",
    "T": "ग्",
    "W": "घ्",
    "P": "च्",
    "X": "ज्",
    "Y": "झ्",
    "K": "ट्",
    "L": "ठ्",
    "J": "ण्",
    "E": "त्",
    "F": "थ्",
    "H": "द्",
    "I": "ध्",
    "C": "न्",
    "O": "प्",
    "U": "फ्",
    "Z": "ब्",
    "\xc2": "भ्",
    "\xc4": "म्",
    "\xc6": "य्",
    "\xc8": "ल्",
    "\xca": "व्",
    "\xcc": "श्",
    "\xce": "ष्",
    "\xd0": "स्",
    "\xd2": "ह्",
}
