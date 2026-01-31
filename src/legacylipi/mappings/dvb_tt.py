"""DVB-TT (DVBWTT Surekh) font encoding mappings.

This module provides character mappings for DVB-TT/DVBWTT Surekh fonts,
which are legacy fonts used for Marathi/Hindi text in Maharashtra government documents.

The fonts include:
- DVBWTTSurekhNormal
- DVBWTTSurekhBold
- DVBTTSurekhNormal
"""

# DVB-TT Consonants (व्यंजन) - base form without matra
# Format: legacy character code -> Unicode Devanagari character
DVB_TT_CONSONANTS = {
    # Vowels (स्वर)
    "\u2020": "अ",  # † -> अ (a)
    "\u2021": "इ",  # ‡ -> इ (i) - used in इंग्रजी etc.
    "ˆ": "उ",  # ˆ -> उ (u)
    "\u2030": "ऊ",  # ‰ -> ऊ (uu)
    # Consonants (व्यंजन)
    "Û": "क",  # 0xDB -> क (ka)
    "Ü": "ख",  # 0xDC -> ख (kha)
    "\u2039": "ख",  # ‹ -> ख (kha) - alternate
    "Ý": "ग",  # 0xDD -> ग (ga)
    "à": "घ",  # 0xE0 -> घ (gha)
    "ã": "ङ",  # 0xE3 -> ङ (nga)
    "¾": "च",  # 0xBE -> च (cha) - also used for व
    "á": "छ",  # 0xE1 -> छ (chha)
    "\u2022": "ज",  # • -> ज (ja)
    "—": "झ",  # — -> झ (jha)
    "¥": "ञ",  # 0xA5 -> ञ (nya)
    "™": "ट",  # ™ -> ट (ta retroflex)
    "š": "ठ",  # š -> ठ (tha retroflex)
    "›": "ड",  # › -> ड (da retroflex)
    "œ": "ढ",  # œ -> ढ (dha retroflex)
    "Þ": "ण",  # 0xDE -> ण (na retroflex)
    "ŸÖ": "त",  # Ÿ + Ö -> त (ta)
    "Ÿ": "त",  # Ÿ -> त (ta)
    "ÉÖ": "थ",  # É + Ö -> थ (tha)
    "É": "थ",  # É -> थ (tha)
    "¤": "द",  # 0xA4 -> द (da)
    "¬": "ध",  # 0xAC -> ध (dha)
    "®": "न",  # 0xAE -> न (na)
    "¯": "प",  # 0xAF -> प (pa)
    "±": "फ",  # 0xB1 -> फ (pha)
    "²": "ब",  # 0xB2 -> ब (ba)
    "³": "भ",  # 0xB3 -> भ (bha)
    "´": "म",  # 0xB4 -> म (ma)
    "μ": "य",  # μ -> य (ya)
    "¸": "र",  # 0xB8 -> र (ra)
    "»": "ल",  # 0xBB -> ल (la)
    "¹": "ळ",  # 0xB9 -> ळ (La - Marathi specific)
    "¾": "व",  # 0xBE -> व (va)
    "¿": "श",  # 0xBF -> श (sha)
    "Â": "ष",  # 0xC2 -> ष (Sha)
    "Ã": "स",  # 0xC3 -> स (sa)
    "Æ": "ह",  # 0xC6 -> ह (ha)
    "Ê": "क्ष",  # 0xCA -> क्ष (ksha)
}

# DVB-TT Matras (मात्रा) - vowel signs
DVB_TT_MATRAS = {
    # Combined patterns (must be matched first)
    "üÖ": "ा",  # halant + Ö -> ा (aa matra replaces halant)
    "ÖÖ": "ा",  # double Ö -> ा (aa matra)
    "Öã": "ु",  # Ö + ã -> ु (u matra)
    "Ö‡Ô": "ई",  # Ö + ‡ + Ô -> ई (ii vowel, as in मुंबई)
    "Ö‡": "इ",  # Ö + ‡ -> इ (i vowel)
    "Ö": "",  # single Ö -> empty (inherent vowel spacing)
    # Other matras
    "×": "ि",  # 0xD7 -> ि (i matra)
    "Ø": "ी",  # 0xD8 -> ी (ii matra) - alternate
    "ß": "ी",  # 0xDF -> ी (ii matra)
    "Ù": "ु",  # 0xD9 -> ु (u matra)
    "ò": "ू",  # 0xF2 -> ू (uu matra)
    "é": "ृ",  # 0xE9 -> ृ (ri matra)
    "ê": "े",  # 0xEA -> े (e matra)
    "ì": "ै",  # 0xEC -> ै (ai matra)
    "ë": "ॅ",  # 0xEB -> ॅ (candra e)
    "üÖê": "ो",  # halant + Ö + ê -> ो (o matra)
    "üÖì": "ौ",  # halant + Ö + ì -> ौ (au matra)
}

# DVB-TT Special characters
DVB_TT_SPECIAL = {
    "ü": "्",  # 0xFC -> ् (halant/virama)
    "Ó": "ं",  # 0xD3 -> ं (anusvara)
    "Ô": "ः",  # 0xD4 -> ः (visarga)
    "Õ": "ँ",  # 0xD5 -> ँ (chandrabindu)
    "ú": "",  # 0xFA -> modifier (removed, combines with consonant)
    "û": "",  # 0xFB -> modifier (removed)
    "§": "॥",  # 0xA7 -> ॥ (double danda)
    "¦": "।",  # 0xA6 -> । (danda)
    "·": "॰",  # 0xB7 -> ॰ (abbreviation sign)
}

# DVB-TT Conjuncts and ligatures
DVB_TT_CONJUNCTS = {
    # Subscript forms
    "Ò": "्र",  # 0xD2 -> ्र (subscript ra)
    "Î": "्र",  # 0xCE -> ्र (subscript ra alternate)
    "Ï": "्र",  # 0xCF -> ्र (subscript ra - common form)
    "ÛÎ": "क्र",  # ÛÎ -> क्र (kra)
    "ÛÎú": "क्र",  # क्र with modifier
    "¦ü": "द्र",  # ¦ + ü -> द्र (dra, as in मुद्रण)
    "Ã£": "स्थ",  # Ã + £ -> स्थ (stha, as in व्यवस्थापक)
    # Common conjuncts
    "ÐÖ": "द्ध",  # Ð + Ö -> द्ध (ddha)
    "Ð": "द्",  # Ð alone
    "©": "द्व",  # © -> द्व (dva)
    "ª": "द्य",  # 0xAA -> द्य (dya)
    "«": "ट्ट",  # 0xAB -> ट्ट (tta)
    "'": "श्र",  # ' -> श्र (shra)
    "\u201cÖÔ": "र्च",  # " + Ö + Ô -> र्च (rcha, as in मार्च)
    "\u201c": "च",  # " (U+201C left double quote) -> च (cha)
    "–": "ह्य",  # – -> ह्य (hya)
    "æ": "त्त",  # 0xE6 -> त्त (tta)
    "î": "द्द",  # 0xEE -> द्द (dda)
}

# DVB-TT Numbers
DVB_TT_NUMBERS = {
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
}

# Additional character mappings discovered from analysis
DVB_TT_ADDITIONAL = {
    # More consonant variations
    "¡": "ड़",  # 0xA1 -> ड़ (dda with nukta)
    "£": "ण",  # 0xA3 -> ण (alternate)
    "¨": "ऑ",  # 0xA8 -> ऑ (o with candra)
    "º": "ळ",  # 0xBA -> ळ (alternate)
    # Word-specific ligatures
    "ó": "ू",  # 0xF3 -> ू (uu matra alternate)
    "ô": "ृ",  # 0xF4 -> ृ (ri matra alternate)
    "õ": "े",  # 0xF5 -> े (e matra alternate)
    "ý": "य",  # 0xFD -> य (ya alternate)
    "þ": "र",  # 0xFE -> र (ra alternate)
    # Modifiers that should be removed
    "Œ": "",  # OE ligature - remove
    "œ": "",  # oe ligature - remove
}

# Complete mapping combining all categories
DVB_TT_COMPLETE_MAPPING = {}
DVB_TT_COMPLETE_MAPPING.update(DVB_TT_CONSONANTS)
DVB_TT_COMPLETE_MAPPING.update(DVB_TT_MATRAS)
DVB_TT_COMPLETE_MAPPING.update(DVB_TT_SPECIAL)
DVB_TT_COMPLETE_MAPPING.update(DVB_TT_CONJUNCTS)
DVB_TT_COMPLETE_MAPPING.update(DVB_TT_ADDITIONAL)

# Word-level mappings for common patterns that don't decompose well
DVB_TT_WORD_PATTERNS = {
    "´ÖÆüÖ¸üÖÂ™Òü": "महाराष्ट्र",
    "¿ÖÖÃÖ®Ö": "शासन",
    "×¾Ö³ÖÖÝÖ": "विभाग",
    "×®ÖμÖ´Ö": "नियम",
    "†×¬Ö×®ÖμÖ´Ö": "अधिनियम",
    "Ûú»Ö´Ö": "कलम",
    "†®Öãêû¤ü": "अनुच्छेद",
    "¯ÖÏ×ŸÖ": "प्रति",
    "¯Öã¹ýÂÖ": "पुरुष",
    "´Ö×Æü»ÖÖ": "महिला",
    "ÃÖ´ÖÖ®Ö": "समान",
    "†×¬ÖÛúÖ¸ü": "अधिकार",
    "ÃÖ¸üÛúÖ¸ü": "सरकार",
    "¸üÖ•μÖ": "राज्य",
    "³ÖÖÂÖÖ": "भाषा",
    "¸üÖ•Ö³ÖÖÂÖÖ": "राजभाषा",
    "´Ö¸üÖšüß": "मराठी",
    "¤êü¾Ö®ÖÖÝÖ¸üß": "देवनागरी",
    "ÃÖÓ×¾Ö¬ÖÖ®Ö": "संविधान",
    "×¾Ö¬ÖÖ®Ö´ÖÓ›üôû": "विधानमंडळ",
    "×¾Ö¬ÖêμÖÛú": "विधेयक",
    "×¾Ö×¬Ö": "विधि",
    "®μÖÖμÖ": "न्याय",
    "¯ÖÏÖ¸Óü³Ö": "प्रारंभ",
    "ˆ¯Ö²ÖÓ¬Ö": "उपबंध",
    "ŸÖ¸üŸÖæ¤ü": "तरतूद",
    "†Ó´Ö»Ö²Ö•ÖÖ¾ÖÞÖß": "अंमलबजावणी",
    "ÃÖ×´ÖŸÖß": "समिती",
    "ÛúÖμÖÖÔ»ÖμÖ": "कार्यालय",
    "×¤ü®ÖÖÓÛú": "दिनांक",
    "ÛÎú´ÖÖÓÛú": "क्रमांक",
    "¯ÖéÂšü": "पृष्ठ",
}


def get_dvb_tt_mapping() -> dict:
    """Get the complete DVB-TT character mapping.

    Returns:
        Dictionary mapping DVB-TT characters to Unicode Devanagari.
    """
    # Combine all mappings, sorted by key length (longest first)
    all_mappings = {}
    all_mappings.update(DVB_TT_WORD_PATTERNS)
    all_mappings.update(DVB_TT_CONJUNCTS)
    all_mappings.update(DVB_TT_COMPLETE_MAPPING)
    all_mappings.update(DVB_TT_NUMBERS)

    # Sort by key length descending for proper replacement
    return dict(sorted(all_mappings.items(), key=lambda x: len(x[0]), reverse=True))
