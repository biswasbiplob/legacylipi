"""Mapping table loader for legacy font encodings.

This module handles loading and managing character mapping tables
for converting legacy-encoded text to Unicode.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from legacylipi.mappings.dvb_tt import DVB_TT_WORD_PATTERNS, get_dvb_tt_mapping
from legacylipi.mappings.shree_dev import (
    SHREE_DEV_HALF_FORMS,
    SHREE_DEV_LIGATURES,
    SHREE_DEV_MAPPINGS,
)


@dataclass
class MappingTable:
    """Character mapping table for a legacy font encoding."""

    encoding_name: str
    font_family: str
    language: str
    script: str
    mappings: dict[str, str]  # legacy char -> unicode char
    ligatures: dict[str, str] = field(default_factory=dict)  # multi-char sequences
    half_forms: dict[str, str] = field(default_factory=dict)  # half characters
    version: str = "1.0"
    variants: list[str] = field(default_factory=list)

    @property
    def all_mappings(self) -> dict[str, str]:
        """Get all mappings including ligatures and half forms.

        Returns mappings sorted by key length (longest first) for proper replacement.
        """
        all_maps = {}
        all_maps.update(self.mappings)
        all_maps.update(self.ligatures)
        all_maps.update(self.half_forms)

        # Sort by key length descending to handle longer sequences first
        return dict(sorted(all_maps.items(), key=lambda x: len(x[0]), reverse=True))

    def get_reverse_mapping(self) -> dict[str, str]:
        """Get reverse mapping (Unicode -> legacy)."""
        reverse = {}
        for legacy, unicode_char in self.all_mappings.items():
            if unicode_char not in reverse:
                reverse[unicode_char] = legacy
        return reverse


class MappingLoadError(Exception):
    """Exception raised when mapping table loading fails."""

    pass


class MappingLoader:
    """Loader for font encoding mapping tables."""

    def __init__(self, mapping_dirs: list[Path] | None = None):
        """Initialize the mapping loader.

        Args:
            mapping_dirs: Directories to search for mapping files.
                         Defaults to the package's data/mappings directory.
        """
        self._cache: dict[str, MappingTable] = {}
        self._mapping_dirs: list[Path] = []

        if mapping_dirs:
            self._mapping_dirs.extend(mapping_dirs)

        # Add default mapping directory
        package_dir = Path(__file__).parent.parent.parent.parent
        default_dir = package_dir / "data" / "mappings"
        if default_dir.exists():
            self._mapping_dirs.append(default_dir)

        # Also check in the mappings package directory
        mappings_dir = Path(__file__).parent / "tables"
        if mappings_dir.exists():
            self._mapping_dirs.append(mappings_dir)

    def load(self, encoding_name: str) -> MappingTable:
        """Load a mapping table for the specified encoding.

        Args:
            encoding_name: Name of the encoding (e.g., 'shree-lipi', 'kruti-dev').

        Returns:
            MappingTable for the encoding.

        Raises:
            MappingLoadError: If the mapping table cannot be found or loaded.
        """
        # Check cache first
        if encoding_name in self._cache:
            return self._cache[encoding_name]

        # Search for mapping file
        mapping_file = self._find_mapping_file(encoding_name)
        if mapping_file is None:
            raise MappingLoadError(f"No mapping table found for encoding: {encoding_name}")

        # Load the mapping file
        table = self._load_file(mapping_file)
        self._cache[encoding_name] = table
        return table

    def _find_mapping_file(self, encoding_name: str) -> Path | None:
        """Find mapping file for an encoding.

        Args:
            encoding_name: Name of the encoding.

        Returns:
            Path to the mapping file, or None if not found.
        """
        # Normalize encoding name
        normalized = encoding_name.lower().replace(" ", "-").replace("_", "-")

        # Possible file names
        candidates = [
            f"{normalized}.yaml",
            f"{normalized}.yml",
            f"{normalized}.json",
        ]

        for dir_path in self._mapping_dirs:
            for candidate in candidates:
                file_path = dir_path / candidate
                if file_path.exists():
                    return file_path

        return None

    def _load_file(self, filepath: Path) -> MappingTable:
        """Load mapping table from a file.

        Args:
            filepath: Path to the mapping file.

        Returns:
            MappingTable loaded from the file.

        Raises:
            MappingLoadError: If the file cannot be loaded or parsed.
        """
        try:
            content = filepath.read_text(encoding="utf-8")

            if filepath.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(content)
            elif filepath.suffix == ".json":
                data = json.loads(content)
            else:
                raise MappingLoadError(f"Unsupported file format: {filepath.suffix}")

            return self._parse_mapping_data(data, filepath.stem)
        except yaml.YAMLError as e:
            raise MappingLoadError(f"Failed to parse YAML file {filepath}: {e}")
        except json.JSONDecodeError as e:
            raise MappingLoadError(f"Failed to parse JSON file {filepath}: {e}")
        except Exception as e:
            raise MappingLoadError(f"Failed to load mapping file {filepath}: {e}")

    def _parse_mapping_data(self, data: dict, default_name: str) -> MappingTable:
        """Parse mapping data dictionary into a MappingTable.

        Args:
            data: Dictionary containing mapping data.
            default_name: Default name to use if not in data.

        Returns:
            MappingTable object.

        Raises:
            MappingLoadError: If required fields are missing.
        """
        metadata = data.get("metadata", {})

        if "mappings" not in data:
            raise MappingLoadError("Mapping file must contain 'mappings' field")

        return MappingTable(
            encoding_name=metadata.get("encoding_name", default_name),
            font_family=metadata.get("font_family", "Unknown"),
            language=metadata.get("language", "Unknown"),
            script=metadata.get("script", "Devanagari"),
            version=metadata.get("version", "1.0"),
            variants=metadata.get("variants", []),
            mappings=data.get("mappings", {}),
            ligatures=data.get("ligatures", {}),
            half_forms=data.get("half_forms", {}),
        )

    def list_available(self) -> list[str]:
        """List all available encoding mappings.

        Returns:
            List of encoding names that can be loaded.
        """
        encodings = set()

        for dir_path in self._mapping_dirs:
            if not dir_path.exists():
                continue

            for file_path in dir_path.iterdir():
                if file_path.suffix in (".yaml", ".yml", ".json"):
                    encodings.add(file_path.stem)

        # Also include built-in encodings
        encodings.update(BUILTIN_MAPPINGS.keys())

        return sorted(encodings)

    def get_builtin(self, encoding_name: str) -> MappingTable | None:
        """Get a built-in mapping table.

        Args:
            encoding_name: Name of the encoding.

        Returns:
            MappingTable if available as built-in, None otherwise.
        """
        if encoding_name in BUILTIN_MAPPINGS:
            return BUILTIN_MAPPINGS[encoding_name]
        return None


# Built-in mapping tables for common encodings
# These provide basic support without requiring external files

SHREE_LIPI_MAPPINGS = {
    # Vowels
    "†": "अ",
    "‡": "आ",
    "ˆ": "इ",
    "‰": "ई",
    "Š": "उ",
    "‹": "ऊ",
    "Œ": "ऋ",
    "": "ए",
    "Ž": "ऐ",
    "": "ओ",
    "": "औ",
    "'": "अं",
    "'": "अः",
    # Consonants
    "¹": "क",
    "º": "ख",
    "»": "ग",
    "¼": "घ",
    "½": "ङ",
    "¾": "च",
    "¿": "छ",
    "À": "ज",
    "Á": "झ",
    "Â": "ञ",
    "Ã": "ट",
    "Ä": "ठ",
    "Å": "ड",
    "Æ": "ढ",
    "Ç": "ण",
    "È": "त",
    "É": "थ",
    "Ê": "द",
    "Ë": "ध",
    "Ì": "न",
    "Í": "प",
    "Î": "फ",
    "Ï": "ब",
    "Ð": "भ",
    "Ñ": "म",
    "Ò": "य",
    "Ó": "र",
    "Ô": "ल",
    "Õ": "व",
    "Ö": "श",
    "×": "ष",
    "Ø": "स",
    "Ù": "ह",
    "Ú": "ळ",
    "Û": "क्ष",
    "Ü": "ज्ञ",
    # Matras
    "Ö": "ा",
    "×": "ि",
    "Ø": "ी",
    "Ù": "ु",
    "Ú": "ू",
    "Û": "ृ",
    "Ü": "े",
    "Ý": "ै",
    "Þ": "ो",
    "ß": "ौ",
    "Ö¸ü": "ार",
    "Ö®Ö": "ान",
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
    # Special
    "Ñ": "्",
    "ü": "्",
    "Ÿ": "ं",
    " ": "ः",
    "।": "।",
    "॥": "॥",
}

SHREE_LIPI_LIGATURES = {
    "Œ": "क्ष",
    "¡": "त्र",
    "–": "ज्ञ",
    "´Ö": "मा",
    "Æü": "ढ",
    "Ö¸ü": "ार",
    "®Ö": "न",
    "ÖμÖ": "ाय",
    "ÖÂ": "ाष",
    "™Òü": "ट्र",
    "†×": "अ",
    "×®Ö": "नि",
    "´ÖÆüÖ¸üÖÂ™Òü": "महाराष्ट्र",
}

KRUTI_DEV_MAPPINGS = {
    # Vowels
    "v": "अ",
    "vk": "आ",
    "b": "इ",
    "bZ": "ई",
    "m": "उ",
    "Å": "ऊ",
    ",": "ए",
    ",s": "ऐ",
    "vks": "ओ",
    "vkS": "औ",
    # Consonants
    "d": "क",
    "[k": "ख",
    "x": "ग",
    "?k": "घ",
    "³": "ङ",
    "p": "च",
    "N": "छ",
    "t": "ज",
    ">": "झ",
    "¥": "ञ",
    "V": "ट",
    "B": "ठ",
    "M": "ड",
    "<": "ढ",
    ".k": "ण",
    "r": "त",
    "Fk": "थ",
    "n": "द",
    "/k": "ध",
    "u": "न",
    "i": "प",
    "Q": "फ",
    "c": "ब",
    "Hk": "भ",
    "e": "म",
    ";": "य",
    "j": "र",
    "y": "ल",
    "o": "व",
    "'k": "श",
    '"k': "ष",
    "l": "स",
    "g": "ह",
    "G": "ळ",
    # Matras
    "k": "ा",
    "f": "ि",
    "h": "ी",
    "q": "ु",
    "w": "ू",
    "`": "ृ",
    "s": "े",
    "S": "ै",
    "ks": "ो",
    "kS": "ौ",
    # Special
    "~": "्",
    "a": "ं",
    "¡": "ँ",
    "%": "ः",
    "A": "।",
    "Þ": "॥",
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
}

KRUTI_DEV_LIGATURES = {
    "Hkkjr": "भारत",
    "ns'k": "देश",
    "d`fr": "कृति",
    "gS": "है",
    "fd": "कि",
    "dh": "की",
    "esa": "में",
    "ls": "से",
    "dk": "का",
    "ds": "के",
    "dks": "को",
}

# Build mapping tables
BUILTIN_MAPPINGS: dict[str, MappingTable] = {
    "shree-lipi": MappingTable(
        encoding_name="shree-lipi",
        font_family="Shree-Lipi",
        language="Marathi",
        script="Devanagari",
        mappings=SHREE_LIPI_MAPPINGS,
        ligatures=SHREE_LIPI_LIGATURES,
        variants=["Shree-Dev-0714", "Shree-Dev-0702", "Shree-Dev-0705"],
    ),
    "kruti-dev": MappingTable(
        encoding_name="kruti-dev",
        font_family="Kruti Dev",
        language="Hindi",
        script="Devanagari",
        mappings=KRUTI_DEV_MAPPINGS,
        ligatures=KRUTI_DEV_LIGATURES,
        variants=["KrutiDev010", "KrutiDev040"],
    ),
    "dvb-tt": MappingTable(
        encoding_name="dvb-tt",
        font_family="DVB-TT",
        language="Marathi",
        script="Devanagari",
        mappings=get_dvb_tt_mapping(),
        ligatures=DVB_TT_WORD_PATTERNS,
        variants=[
            "DVBWTTSurekhNormal",
            "DVBWTTSurekhBold",
            "DVBTTSurekhNormal",
            "DVBWTT",
            "DVB-TT-Surekh",
        ],
    ),
    "shree-dev": MappingTable(
        encoding_name="shree-dev",
        font_family="SHREE-DEV",
        language="Marathi",
        script="Devanagari",
        mappings=SHREE_DEV_MAPPINGS,
        ligatures=SHREE_DEV_LIGATURES,
        half_forms=SHREE_DEV_HALF_FORMS,
        variants=[
            "SHREE-DEV-0708",
            "SHREE-DEV-0714",
            "SHREE-DEV-0715",
            "SHREE-DEV-0721",
        ],
    ),
}


def get_mapping(encoding_name: str) -> MappingTable:
    """Get a mapping table for the specified encoding.

    This is a convenience function that uses a default MappingLoader.

    Args:
        encoding_name: Name of the encoding.

    Returns:
        MappingTable for the encoding.

    Raises:
        MappingLoadError: If the mapping cannot be found.
    """
    loader = MappingLoader()

    # Try built-in first
    builtin = loader.get_builtin(encoding_name)
    if builtin:
        return builtin

    # Try loading from file
    return loader.load(encoding_name)
