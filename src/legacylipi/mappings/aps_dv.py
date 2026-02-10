"""APS-DV (Akhand Pratap Singh Devanagari) font encoding mappings.

This module provides character mappings for APS-DV legacy Devanagari fonts,
commonly used in newspaper typesetting and desktop publishing.

APS-DV encoding uses extended ASCII range (128-255) extensively to map
characters to Devanagari glyphs. It is one of the older encoding systems
used primarily in Hindi newspaper composition.

The conversion process involves:
1. Replace multi-character sequences first (ligatures, conjuncts)
2. Replace single character mappings
3. Apply post-processing for matra reordering
"""

# APS-DV to Unicode mapping
# Maps extended-ASCII characters to Devanagari Unicode
APS_DV_MAPPINGS: dict[str, str] = {
    # Vowels (स्वर) - Independent forms
    "\xbc": "अ",  # ¼ -> अ (A)
    "\xbd": "आ",  # ½ -> आ (Aa)
    "\xbe": "इ",  # ¾ -> इ (I)
    "\xbf": "ई",  # ¿ -> ई (Ii)
    "\xc0": "उ",  # À -> उ (U)
    "\xc1": "ऊ",  # Á -> ऊ (Uu)
    "\xc2": "ऋ",  # Â -> ऋ (Ri)
    "\xc3": "ए",  # Ã -> ए (E)
    "\xc4": "ऐ",  # Ä -> ऐ (Ai)
    "\xc5": "ओ",  # Å -> ओ (O)
    "\xc6": "औ",  # Æ -> औ (Au)
    # Consonants (व्यंजन)
    "\xc7": "क",  # Ç -> क (Ka)
    "\xc8": "ख",  # È -> ख (Kha)
    "\xc9": "ग",  # É -> ग (Ga)
    "\xca": "घ",  # Ê -> घ (Gha)
    "\xcb": "ङ",  # Ë -> ङ (Nga)
    "\xcc": "च",  # Ì -> च (Cha)
    "\xcd": "छ",  # Í -> छ (Chha)
    "\xce": "ज",  # Î -> ज (Ja)
    "\xcf": "झ",  # Ï -> झ (Jha)
    "\xd0": "ञ",  # Ð -> ञ (Nya)
    "\xd1": "ट",  # Ñ -> ट (Ta retroflex)
    "\xd2": "ठ",  # Ò -> ठ (Tha retroflex)
    "\xd3": "ड",  # Ó -> ड (Da retroflex)
    "\xd4": "ढ",  # Ô -> ढ (Dha retroflex)
    "\xd5": "ण",  # Õ -> ण (Na retroflex)
    "\xd6": "त",  # Ö -> त (Ta)
    "\xd7": "थ",  # × -> थ (Tha)
    "\xd8": "द",  # Ø -> द (Da)
    "\xd9": "ध",  # Ù -> ध (Dha)
    "\xda": "न",  # Ú -> न (Na)
    "\xdb": "प",  # Û -> प (Pa)
    "\xdc": "फ",  # Ü -> फ (Pha)
    "\xdd": "ब",  # Ý -> ब (Ba)
    "\xde": "भ",  # Þ -> भ (Bha)
    "\xdf": "म",  # ß -> म (Ma)
    "\xe0": "य",  # à -> य (Ya)
    "\xe1": "र",  # á -> र (Ra)
    "\xe2": "ल",  # â -> ल (La)
    "\xe3": "व",  # ã -> व (Va)
    "\xe4": "श",  # ä -> श (Sha)
    "\xe5": "ष",  # å -> ष (Sha retroflex)
    "\xe6": "स",  # æ -> स (Sa)
    "\xe7": "ह",  # ç -> ह (Ha)
    "\xe8": "ळ",  # è -> ळ (La - Marathi)
    # Matras (vowel signs)
    "\xe9": "ा",  # é -> ा (Aa matra)
    "\xea": "ि",  # ê -> ि (I matra)
    "\xeb": "ी",  # ë -> ी (Ii matra)
    "\xec": "ु",  # ì -> ु (U matra)
    "\xed": "ू",  # í -> ू (Uu matra)
    "\xee": "ृ",  # î -> ृ (Ri matra)
    "\xef": "े",  # ï -> े (E matra)
    "\xf0": "ै",  # ð -> ै (Ai matra)
    "\xf1": "ो",  # ñ -> ो (O matra)
    "\xf2": "ौ",  # ò -> ौ (Au matra)
    # Special characters
    "\xf3": "्",  # ó -> ् (Halant/Virama)
    "\xf4": "ं",  # ô -> ं (Anusvara)
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
APS_DV_LIGATURES: dict[str, str] = {
    # Conjuncts
    "\xf8": "क्ष",  # ø -> क्ष (Ksha)
    "\xf9": "ज्ञ",  # ù -> ज्ञ (Gya/Dnya)
    "\xfa": "त्र",  # ú -> त्र (Tra)
    "\xfb": "श्र",  # û -> श्र (Shra)
    # Half form + consonant patterns
    "\xc7\xf3": "क्",  # क + halant -> क् (Ka half)
    "\xc8\xf3": "ख्",  # ख + halant -> ख् (Kha half)
    "\xc9\xf3": "ग्",  # ग + halant -> ग् (Ga half)
    "\xca\xf3": "घ्",  # घ + halant -> घ् (Gha half)
    "\xcc\xf3": "च्",  # च + halant -> च् (Cha half)
    "\xce\xf3": "ज्",  # ज + halant -> ज् (Ja half)
    "\xd6\xf3": "त्",  # त + halant -> त् (Ta half)
    "\xd8\xf3": "द्",  # द + halant -> द् (Da half)
    "\xda\xf3": "न्",  # न + halant -> न् (Na half)
    "\xdb\xf3": "प्",  # प + halant -> प् (Pa half)
    "\xdd\xf3": "ब्",  # ब + halant -> ब् (Ba half)
    "\xdf\xf3": "म्",  # म + halant -> म् (Ma half)
    "\xe2\xf3": "ल्",  # ल + halant -> ल् (La half)
    "\xe4\xf3": "श्",  # श + halant -> श् (Sha half)
    "\xe6\xf3": "स्",  # स + halant -> स् (Sa half)
    "\xe7\xf3": "ह्",  # ह + halant -> ह् (Ha half)
    # Matra combinations
    "\xe9\xef": "ो",  # aa + e matra -> o matra
    "\xe9\xf0": "ौ",  # aa + ai matra -> au matra
}

# Half forms - consonants with halant
APS_DV_HALF_FORMS: dict[str, str] = {
    "\x80": "क्",  # Ka half
    "\x81": "ख्",  # Kha half
    "\x82": "ग्",  # Ga half
    "\x83": "घ्",  # Gha half
    "\x84": "च्",  # Cha half
    "\x85": "ज्",  # Ja half
    "\x86": "झ्",  # Jha half
    "\x87": "ञ्",  # Nya half
    "\x88": "ण्",  # Na (retroflex) half
    "\x89": "त्",  # Ta half
    "\x8a": "थ्",  # Tha half
    "\x8b": "द्",  # Da half
    "\x8c": "ध्",  # Dha half
    "\x8d": "न्",  # Na half
    "\x8e": "प्",  # Pa half
    "\x8f": "फ्",  # Pha half
    "\x90": "ब्",  # Ba half
    "\x91": "भ्",  # Bha half
    "\x92": "म्",  # Ma half
    "\x93": "य्",  # Ya half
    "\x94": "ल्",  # La half
    "\x95": "व्",  # Va half
    "\x96": "श्",  # Sha half
    "\x97": "ष्",  # Sha (retroflex) half
    "\x98": "स्",  # Sa half
    "\x99": "ह्",  # Ha half
    "\x9a": "ळ्",  # La (Marathi) half
}
