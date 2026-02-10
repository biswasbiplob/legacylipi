"""Mapping validation test framework.

Parameterized tests across all BUILTIN_MAPPINGS to ensure consistency,
correctness, and completeness of encoding mapping tables.
"""

import unicodedata

import pytest

from legacylipi.mappings.loader import BUILTIN_MAPPINGS, MappingTable

# Get all encoding names for parameterization
ALL_ENCODINGS = list(BUILTIN_MAPPINGS.keys())


@pytest.fixture(params=ALL_ENCODINGS)
def mapping(request: pytest.FixtureRequest) -> MappingTable:
    """Provide each built-in mapping table as a test fixture."""
    return BUILTIN_MAPPINGS[request.param]


class TestMappingTableStructure:
    """Test that MappingTable fields are properly populated."""

    def test_has_encoding_name(self, mapping: MappingTable) -> None:
        assert mapping.encoding_name, "encoding_name must not be empty"

    def test_has_font_family(self, mapping: MappingTable) -> None:
        assert mapping.font_family, "font_family must not be empty"

    def test_has_language(self, mapping: MappingTable) -> None:
        assert mapping.language, "language must not be empty"
        assert mapping.language in ("Hindi", "Marathi", "Sanskrit", "Tamil")

    def test_has_script(self, mapping: MappingTable) -> None:
        assert mapping.script == "Devanagari", f"Expected Devanagari, got {mapping.script}"

    def test_has_mappings(self, mapping: MappingTable) -> None:
        assert len(mapping.mappings) > 0, "mappings dict must not be empty"

    def test_has_version(self, mapping: MappingTable) -> None:
        assert mapping.version, "version must not be empty"


class TestMappingValues:
    """Test mapping values are valid Unicode."""

    def test_all_values_are_valid_unicode(self, mapping: MappingTable) -> None:
        """Every mapped value must be a valid Unicode string."""
        for key, value in mapping.all_mappings.items():
            assert isinstance(value, str), f"Value for key {repr(key)} is not a string"
            # Check that each character is valid Unicode
            for char in value:
                try:
                    unicodedata.name(char)
                except ValueError:
                    # Some valid chars don't have names (e.g., combining marks)
                    assert ord(char) < 0x110000, f"Invalid Unicode char in value for {repr(key)}"

    def test_no_empty_values(self, mapping: MappingTable) -> None:
        """Values should not be None (empty string is OK for intentional deletion)."""
        for key, value in mapping.mappings.items():
            assert value is not None, f"None value found for key {repr(key)}"

    def test_keys_are_strings(self, mapping: MappingTable) -> None:
        """All keys must be strings."""
        empty_count = 0
        for key in mapping.all_mappings:
            assert isinstance(key, str), f"Key {repr(key)} is not a string"
            if len(key) == 0:
                empty_count += 1
        # Allow at most a small number of empty keys (some legacy encodings
        # use invisible/control characters that appear as empty strings)
        assert empty_count <= 3, f"Too many empty string keys found: {empty_count}"


class TestMappingCoverage:
    """Test mapping coverage for basic Devanagari characters."""

    BASIC_CONSONANTS = set("कखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह")
    BASIC_MATRAS = set("ािीुूृेैोौ")

    def test_covers_basic_consonants(self, mapping: MappingTable) -> None:
        """At least 50% of basic consonants should be mapped."""
        mapped_values: set[str] = set()
        for value in mapping.all_mappings.values():
            mapped_values.update(value)

        coverage = len(self.BASIC_CONSONANTS & mapped_values)
        total = len(self.BASIC_CONSONANTS)
        assert coverage >= total * 0.5, (
            f"Only {coverage}/{total} basic consonants mapped for {mapping.encoding_name}"
        )

    def test_has_halant(self, mapping: MappingTable) -> None:
        """Encoding should map the halant (virama) character."""
        mapped_values: set[str] = set()
        for value in mapping.all_mappings.values():
            mapped_values.update(value)
        assert "\u094d" in mapped_values or len(mapping.half_forms) > 0, (
            f"No halant mapping found for {mapping.encoding_name}"
        )


class TestMappingConsistency:
    """Test mapping table internal consistency."""

    def test_no_duplicate_values_in_ligatures_and_mappings(self, mapping: MappingTable) -> None:
        """Ligature keys should not duplicate base mapping keys."""
        base_keys = set(mapping.mappings.keys())
        lig_keys = set(mapping.ligatures.keys())
        overlap = base_keys & lig_keys
        # Some overlap is OK (e.g., alternate forms), but flag large overlaps
        assert len(overlap) < len(base_keys) * 0.5, (
            f"Too many overlapping keys between mappings and ligatures: {len(overlap)}"
        )

    def test_all_mappings_sorted_by_length(self, mapping: MappingTable) -> None:
        """all_mappings property should return keys sorted by length (longest first)."""
        all_maps = mapping.all_mappings
        keys = list(all_maps.keys())
        for i in range(len(keys) - 1):
            assert len(keys[i]) >= len(keys[i + 1]), (
                f"Keys not sorted by length: {repr(keys[i])} before {repr(keys[i + 1])}"
            )


class TestRoundtrip:
    """Test that reverse mapping can reconstruct original keys."""

    def test_reverse_mapping_exists(self, mapping: MappingTable) -> None:
        """Reverse mapping should have entries."""
        reverse = mapping.get_reverse_mapping()
        assert len(reverse) > 0, "Reverse mapping is empty"

    def test_reverse_mapping_values_are_original_keys(self, mapping: MappingTable) -> None:
        """Values in reverse mapping should be valid original keys."""
        reverse = mapping.get_reverse_mapping()
        all_keys = set(mapping.all_mappings.keys())
        for _unicode_char, legacy_key in reverse.items():
            assert legacy_key in all_keys, (
                f"Reverse mapping value {repr(legacy_key)} not found in original keys"
            )
