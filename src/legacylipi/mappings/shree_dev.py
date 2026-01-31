"""SHREE-DEV font encoding mappings.

This module provides character mappings for SHREE-DEV legacy Devanagari fonts
(SHREE-DEV-0708, SHREE-DEV-0714, SHREE-DEV-0715, SHREE-DEV-0721, etc.)

These fonts map ASCII characters to Devanagari glyphs visually, but the
underlying text data contains ASCII codes that need conversion to Unicode.

IMPORTANT: This mapping is based on the verified converter from:
https://hindifontconverter.com/shreedev0714-to-unicode-converter.html

The conversion process involves:
1. Replace multi-character sequences first (conjuncts, ligatures)
2. Replace single character mappings
3. Apply regex post-processing for matra reordering (p/q -> ि)
4. Apply regex post-processing for र् (eyelash ra) reordering
"""

import re


# SHREE-DEV to Unicode mapping
# Maps ASCII/extended-ASCII characters to Devanagari Unicode
# Based on the verified JavaScript converter from hindifontconverter.com
SHREE_DEV_MAPPINGS = {
    # Special/punctuation
    ">": "",      # Empty
    "$": "",      # Empty (double space marker)
    "›": "ॐ",    # Om
    "@": "ऽ",    # Avagraha
    "&": "।",    # Danda

    # Consonants (व्यंजन) - Capital letters
    "H": "क",    # Ka
    "I": "ख",    # Kha
    "J": "ग",    # Ga
    "K": "घ",    # Gha
    "L": "ङ",    # Nga
    "M": "च",    # Cha
    "N": "छ",    # Chha
    "O": "ज",    # Ja
    "P": "झ",    # Jha
    "Q": "ट",    # Ta (retroflex)
    "R": "ठ",    # Tha (retroflex)
    "S": "ड",    # Da (retroflex)
    "T": "ढ",    # Dha (retroflex)
    "U": "ण",    # Na (retroflex)
    "V": "त",    # Ta
    "W": "थ",    # Tha
    "X": "द",    # Da
    "Y": "ध",    # Dha
    "Z": "न",    # Na

    # Consonants - lowercase/special
    "n": "प",    # Pa
    "\\": "फ",   # Pha
    "~": "ब",    # Ba
    "^": "भ",    # Bha
    "_": "म",    # Ma
    "`": "य",    # Ya
    "a": "र",    # Ra
    "b": "ल",    # La
    "c": "ल",    # La (alternate)
    "d": "व",    # Va
    "e": "श",    # Sha
    "f": "ष",    # Sha (retroflex)
    "g": "स",    # Sa
    "h": "ह",    # Ha
    "i": "ळ",    # La (Marathi)

    # Vowels (स्वर) - Independent forms
    "A": "अ",    # A
    "B": "इ",    # I
    "C": "उ",    # U
    "D": "ऊ",    # Uu
    "E": "ए",    # E
    "F": "ऋ",    # Ri
    "G": "ॠ",    # Rri (long Ri)

    # Vowel signs (मात्रा)
    "m": "ा",    # Aa matra
    "r": "ी",    # Ii matra
    "s": "ी",    # Ii matra (alternate)
    "t": "ीं",   # Ii + anusvara
    "w": "ु",    # U matra
    "x": "ु",    # U matra (alternate)
    "y": "ू",    # Uu matra
    "z": "ू",    # Uu matra (alternate)
    "o": "े",    # E matra
    "|": "ें",   # E matra + anusvara
    "¡": "ै",    # Ai matra
    "¢": "ैं",   # Ai + anusvara
    "¥": "ृ",    # Ri matra
    "¦": "ॄ",    # Rri matra (long)
    "°": "ॅ",    # Candra E matra
    "þ": "ु",    # U matra (alternate)
    "ÿ": "ू",    # Uu matra (alternate)

    # Special characters
    "§": "ं",    # Anusvara
    "¨": "ं",    # Anusvara (alternate)
    "±": "ँ",    # Chandrabindu
    "²": "्",    # Halant/Virama
    "…": "ः",    # Visarga
    "µ": "़",    # Nukta (for borrowed sounds)

    # Half consonants (हलंत forms)
    "Š": "क्",   # Ka half
    "»": "ख्",   # Kha half
    "½": "ग्",   # Ga half
    "¿": "घ्",   # Gha half
    "À": "च्",   # Cha half
    "Á": "ज्",   # Ja half
    "Â": "झ्",   # Jha half
    "Ä": "ञ्",   # Nya half
    "Ê": "ण्",   # Na (retroflex) half
    "Ë": "त्",   # Ta half
    "Ï": "थ्",   # Tha half
    "Ü": "ध्",   # Dha half
    "Ý": "न्",   # Na half
    "ß": "प्",   # Pa half
    "â": "फ्",   # Pha half
    "ã": "ब्",   # Ba half
    "ä": "भ्",   # Bha half
    "å": "म्",   # Ma half
    "æ": "य्",   # Ya half
    "ë": "ल्",   # La half
    "ì": "व्",   # Va half
    "í": "श्",   # Sha half
    "î": "ष्",   # Sha (retroflex) half
    "ñ": "स्",   # Sa half
    "ô": "ह्",   # Ha half
    "ù": "ळ्",   # La (Marathi) half
    "û": "श्",   # Sha half (alternate)

    # Conjuncts (संयुक्त अक्षर)
    "ú": "क्ष्",  # Ksha half
    "j": "क्ष",   # Ksha
    "k": "ज्ञ",   # Gya/Dnya
    "l": "श्र",   # Shra
    "Ì": "त्र",   # Tra
    "Í": "त्र्",  # Tra half
    "Î": "त्त्",  # Tta half
    "®": "्रु",   # Ru (with ra)
    "¯": "्रू",   # Ruu (with ra)
    "é": "रु",    # Ru
    "ê": "रू",    # Ruu
    "#": "ञ्च्",  # Ncha half
    "‚": "ज्ज्",  # Jja half
    "ƒ": "च्च",   # Chcha
    "„": "ल्ल",   # Lla
    "†": "ह्ण",   # Hna
    "‡": "ह्ल",   # Hla
    "ˆ": "ह्व",   # Hva
    "‰": "्व",    # Va (conjunct form)
    "'": "ङ्क",   # Ngka
    "'": "ङ्ख",   # Ngkha
    """: "ङ्ग",   # Ngga
    """: "ङ्घ",   # Nggha
    "¬": "ङ्क्ष", # Ngksha
    "•": "ह्न",   # Hna
    "–": "ड्ढ",   # Ddha
    "œ": "श्व",   # Shva
    "³": "्न",    # Na conjunct
    "¶": "ङ्म",   # Ngma
    "¸": "क्क",   # Kka
    "¹": "क्व",   # Kva
    "º": "क्त",   # Kta
    "¼": "ख्र",   # Khra
    "Ã": "झ्र",   # Jhra
    "¾": "ग्न",   # Gna
    "Å": "ट्ट",   # TaTa
    "Æ": "ट्ठ",   # TaTha
    "Ç": "ठ्ठ",   # ThaTha
    "È": "ड्ड",   # DaDa
    "É": "ड्ढ",   # DaDha
    "Ð": "द्र",   # Dra
    "Ñ": "दृ",    # Dri
    "Ò": "द्ग",   # Dga
    "Ó": "द्घ",   # Dgha
    "Ô": "द्द",   # Dda
    "Õ": "द्ध",   # Ddha
    "Ö": "द्न",   # Dna
    "×": "द्ब",   # Dba
    "Ø": "द्भ",   # Dbha
    "Ù": "द्म",   # Dma
    "Ú": "द्य",   # Dya
    "Û": "द्व",   # Dva
    "Þ": "न्न",   # Nna
    "à": "प्र",   # Pra
    "á": "प्त",   # Pta
    "ï": "ष्ट",   # ShTa
    "ð": "ष्ठ",   # ShTha
    "ò": "स्र",   # Sra
    "ó": "स्त्र", # Stra
    "õ": "ह्र",   # Hra
    "ö": "हृ",    # Hri
    "÷": "ह्म",   # Hma
    "ø": "ह्य",   # Hya
    "ü": "श्च",   # Shcha
    "ý": "श्न",   # Shna
    "ç": "्य",    # Ya conjunct
    "Œ": "्र",    # Ra conjunct (eyelash ra)
    "´": "्र",    # Ra conjunct (alternate)
    "«": "्र",    # Ra conjunct (alternate 2)

    # Nukta combinations (borrowed sounds)
    "µH": "क़",   # Qa
    "™": "ख़्",   # Kha with nukta half
    "˜": "ख़",    # Kha with nukta
    "µJ": "ग़",   # Gha with nukta
    "µO": "ज़",   # Za
    "µÁ": "ज़्",  # Za half
    "µS": "ड़",   # Da with nukta
    "µT": "ढ़",   # Dha with nukta
    "µ\\": "फ़",  # Fa

    # Numbers (keep as ASCII - Devanagari numerals optional)
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
    "%": "%",
    "+": "+",
    "=": "=",
    "<": "<",

    # Quote marks
    '"': "'",
    "'": "'",

    # Placeholders for matra reordering (handled in post-processing)
    # "[" and "{" map to "p" which becomes ि after reordering
    # "p" and "q" are placeholders for ि matra
    "[": "p",  # Placeholder for इ matra - reordered in post-processing
    "{": "p",  # Placeholder for इ matra - reordered in post-processing
}

# Ligatures - multi-character sequences that map to single Unicode sequences
# These MUST be processed before single-character mappings
SHREE_DEV_LIGATURES = {
    # Extended vowels (process first - longest matches)
    "Am¡": "औ",   # Au
    "Amo": "ओ",   # O
    "Am°": "ऑ",   # Candra O (English O sound)
    "Am": "आ",    # Aa
    "B©": "ई",    # Ii
    "Eo": "ऐ",    # Ai

    # Matra combinations
    "m¡": "ौ",    # Au matra
    "mo": "ो",    # O matra
    "m°": "ॉ",    # Candra O matra
    "m|": "ों",   # O + anusvara
    "m¢": "ौं",   # Au + anusvara

    # Pre-positioned matras with © placeholder for र्
    "ª": "र्",    # Eyelash Ra (repha)
    "©": "र्",    # Eyelash Ra placeholder

    # Complex conjuncts
    "Q´": "ट्र",   # Tra (retroflex)
    "Q­": "ट्र",   # Tra (retroflex alternate)
    "º$": "क्त",   # Kta
    "Îm": "त्ता",  # Tta + aa matra

    # Nukta combinations
    "µO": "ज़",
    "µÁ": "ज़्",
    "¶S": "ड़",
    "¶T": "ढ़",
    "µH": "क़",
    "µJ": "ग़",
    "µ\\": "फ़",

    # Halant combinations that create specific conjuncts
    "²m": "",     # Halant + aa = remove halant
    "²o": "े",    # Halant + e matra
    "²¡": "ै",    # Halant + ai matra
}

# Half forms - consonants with halant
SHREE_DEV_HALF_FORMS = {
    "Š": "क्",
    "»": "ख्",
    "½": "ग्",
    "¿": "घ्",
    "À": "च्",
    "Á": "ज्",
    "Â": "झ्",
    "Ä": "ञ्",
    "Ê": "ण्",
    "Ë": "त्",
    "Ï": "थ्",
    "Ü": "ध्",
    "Ý": "न्",
    "ß": "प्",
    "â": "फ्",
    "ã": "ब्",
    "ä": "भ्",
    "å": "म्",
    "æ": "य्",
    "ë": "ल्",
    "ì": "व्",
    "í": "श्",
    "î": "ष्",
    "ñ": "स्",
    "ô": "ह्",
    "ù": "ळ्",
    "û": "श्",
    "ú": "क्ष्",
}


def apply_shree_dev_post_processing(text: str) -> str:
    """Apply post-processing rules for SHREE-DEV conversion.

    This handles special cases like:
    1. Reordering of इ matra (ि) which appears before the consonant in SHREE-DEV
       but should come after in Unicode
    2. Reordering of र् (eyelash ra/repha) which appears before consonant clusters

    Args:
        text: Text after initial character mapping

    Returns:
        Text with proper Unicode ordering
    """
    # Define consonant character class for regex
    consonants = (
        "[\u0915\u0916\u0917\u0918\u0919"  # क-ङ
        "\u091A\u091B\u091C\u091D\u091E"   # च-ञ
        "\u091F\u0920\u0921\u0922\u0923"   # ट-ण
        "\u0924\u0925\u0926\u0927\u0928"   # त-न
        "\u092A\u092B\u092C\u092D\u092E"   # प-म
        "\u092F\u0930\u0932\u0933\u0935"   # य,र,ल,ळ,व
        "\u0936\u0937\u0938\u0939"         # श,ष,स,ह
        "\u0958\u0959\u095A\u095B\u095C\u095D\u095E\u095F"  # Nukta consonants
        "\u0931\u0929]"                    # Additional
    )

    # Step 1: Handle 'p' placeholder for इ matra
    # 'p' before consonant -> consonant + ि
    text = re.sub(
        r'([pq])(' + consonants + ')',
        r'\2\1',
        text
    )

    # Step 2: Handle 'p' before consonant clusters (with halant)
    text = re.sub(
        r'([pq])((\u094D' + consonants + ')+)',
        r'\2\1',
        text
    )

    # Step 3: Convert 'p' to ि and 'q' to िं
    text = text.replace('p', '\u093F')      # इ matra
    text = text.replace('q', '\u093F\u0902')  # इ matra + anusvara

    # Step 4: Handle © placeholder for र्
    # © before consonant -> consonant + र्... (repha moves after)
    # This is complex - र् (repha) should appear after the consonant cluster
    text = re.sub(
        r'(' + consonants + r')([\u093E\u093F\u0940\u0941\u0942\u0943\u0947\u0948\u094B\u094C\u0902\u0901]*)(©)',
        r'©\1\2',
        text
    )

    # Move © before consonant clusters
    text = re.sub(
        r'((' + consonants + r'[\u094D])+)(©)',
        r'©\1',
        text
    )

    # Convert © to र्
    text = text.replace('©', 'र्')

    # Step 5: Clean up any remaining placeholders
    text = text.replace('प्लेसहोल्डर_इ', 'प')

    # Step 6: Fix matra ordering issues
    # ा + े -> ो
    text = text.replace('\u093E\u0947', '\u094B')
    # ा + ै -> ौ
    text = text.replace('\u093E\u0948', '\u094C')
    # ॅ + ं -> ँ
    text = text.replace('\u0945\u0902', '\u0901')
    # ं + ॅ -> ँ
    text = text.replace('\u0902\u0945', '\u0901')
    # ा + ॅ -> ॉ
    text = text.replace('\u093E\u0945', '\u0949')
    # ॅ + ा -> ॉ
    text = text.replace('\u0945\u093E', '\u0949')
    # ा + ो -> ो (duplicate)
    text = text.replace('\u093E\u094B', '\u094B')
    # ै + ा -> ौ
    text = text.replace('\u0948\u093E', '\u094C')
    # े + ा -> ो
    text = text.replace('\u0947\u093E', '\u094B')

    # Step 7: Fix visarga/anusvara ordering with matras
    # Visarga/anusvara should come after matras
    text = re.sub(
        r'([\u0903\u0902\u0901\u0970]+)([\u093E\u093F\u0940\u0941\u0942\u0943\u0947\u0948\u094B\u094C]+)',
        r'\2\1',
        text
    )

    # Step 8: Clean up space + matra (matra should attach to previous char)
    text = re.sub(
        r'([\s]+)([\u093D\u094D\u093E\u0940\u0941\u0942\u0943\u0947\u0948\u094B\u094C\u0902\u0901])',
        r'\2',
        text
    )

    return text


def get_shree_dev_mapping():
    """Get the complete SHREE-DEV mapping table.

    Returns a MappingTable compatible with the LegacyLipi converter.
    """
    from legacylipi.mappings.loader import MappingTable

    return MappingTable(
        encoding_name="shree-dev",
        font_family="SHREE-DEV",
        language="Marathi",
        script="Devanagari",
        version="2.0",
        variants=["SHREE-DEV-0708", "SHREE-DEV-0714", "SHREE-DEV-0715", "SHREE-DEV-0721"],
        mappings=SHREE_DEV_MAPPINGS,
        ligatures=SHREE_DEV_LIGATURES,
        half_forms=SHREE_DEV_HALF_FORMS,
    )
