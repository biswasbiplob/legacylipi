"""Walkman-Chanakya font encoding mappings.

This module provides character mappings for Walkman-Chanakya legacy Devanagari
fonts, a variant of the Chanakya encoding system.

Walkman-Chanakya is based on the Chanakya encoding but with modifications
specific to the Walkman font series. It is commonly used in Hindi publishing
and typesetting, particularly in government and academic documents.

The conversion process involves:
1. Replace multi-character sequences first (ligatures, conjuncts)
2. Replace single character mappings
3. Apply post-processing for matra reordering
"""

# Walkman-Chanakya to Unicode mapping
# Based on Chanakya encoding with Walkman-specific modifications
WALKMAN_CHANAKYA_MAPPINGS: dict[str, str] = {
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
    # Matras (vowel signs) - Walkman variant assignments
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
    # Walkman-specific half consonants
    "\xc0": "क्",  # Ka half (À)
    "\xc1": "ख्",  # Kha half (Á)
    "\xc2": "ग्",  # Ga half (Â)
    "\xc3": "घ्",  # Gha half (Ã)
    "\xc4": "च्",  # Cha half (Ä)
    "\xc5": "ज्",  # Ja half (Å)
    "\xc6": "झ्",  # Jha half (Æ)
    "\xc7": "ट्",  # Ta (retroflex) half (Ç)
    "\xc8": "ठ्",  # Tha (retroflex) half (È)
    "\xc9": "ण्",  # Na (retroflex) half (É)
    "\xca": "त्",  # Ta half (Ê)
    "\xcb": "थ्",  # Tha half (Ë)
    "\xcc": "द्",  # Da half (Ì)
    "\xcd": "ध्",  # Dha half (Í)
    "\xce": "न्",  # Na half (Î)
    "\xcf": "प्",  # Pa half (Ï)
    "\xd0": "फ्",  # Pha half (Ð)
    "\xd1": "ब्",  # Ba half (Ñ)
    "\xd2": "भ्",  # Bha half (Ò)
    "\xd3": "म्",  # Ma half (Ó)
    "\xd4": "य्",  # Ya half (Ô)
    "\xd5": "ल्",  # La half (Õ)
    "\xd6": "व्",  # Va half (Ö)
    "\xd7": "श्",  # Sha half (×)
    "\xd8": "ष्",  # Sha (retroflex) half (Ø)
    "\xd9": "स्",  # Sa half (Ù)
    "\xda": "ह्",  # Ha half (Ú)
    "\xdb": "ळ्",  # La (Marathi) half (Û)
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

# Ligatures - multi-character sequences
WALKMAN_CHANAKYA_LIGATURES: dict[str, str] = {
    # Extended vowels
    "vk": "आ",  # Aa
    "bZ": "ई",  # Ii
    "\xdc": "ऊ",  # Uu (Ü) - Walkman variant
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
    # Walkman-specific conjuncts
    "\xdd": "क्ष",  # Ksha (Ý)
    "\xdf": "ज्ञ",  # Gya/Dnya (ß)
    "\xe0": "श्र",  # Shra (à)
    "\xe1": "त्र",  # Tra (á)
    "\xe2": "द्र",  # Dra (â)
    "\xe3": "प्र",  # Pra (ã)
    "\xe4": "्र",  # Ra conjunct (ä)
    # Common word patterns
    "\xd6kfr": "वाति",
    "\xe7ns'k": "प्रदेश",
}

# Half forms - consonants with halant
WALKMAN_CHANAKYA_HALF_FORMS: dict[str, str] = {
    "\xc0": "क्",
    "\xc1": "ख्",
    "\xc2": "ग्",
    "\xc3": "घ्",
    "\xc4": "च्",
    "\xc5": "ज्",
    "\xc6": "झ्",
    "\xc7": "ट्",
    "\xc8": "ठ्",
    "\xc9": "ण्",
    "\xca": "त्",
    "\xcb": "थ्",
    "\xcc": "द्",
    "\xcd": "ध्",
    "\xce": "न्",
    "\xcf": "प्",
    "\xd0": "फ्",
    "\xd1": "ब्",
    "\xd2": "भ्",
    "\xd3": "म्",
    "\xd4": "य्",
    "\xd5": "ल्",
    "\xd6": "व्",
    "\xd7": "श्",
    "\xd8": "ष्",
    "\xd9": "स्",
    "\xda": "ह्",
    "\xdb": "ळ्",
}
