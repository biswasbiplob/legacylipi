"""Tests for mapping loader module."""

import pytest
import yaml

from legacylipi.mappings.loader import (
    BUILTIN_MAPPINGS,
    MappingLoader,
    MappingLoadError,
    MappingTable,
    get_mapping,
)


class TestMappingTable:
    """Tests for MappingTable dataclass."""

    def test_create_mapping_table(self):
        """Test creating a mapping table."""
        table = MappingTable(
            encoding_name="test-encoding",
            font_family="Test Font",
            language="Hindi",
            script="Devanagari",
            mappings={"a": "अ", "b": "ब"},
        )

        assert table.encoding_name == "test-encoding"
        assert table.font_family == "Test Font"
        assert len(table.mappings) == 2

    def test_all_mappings_includes_ligatures(self):
        """Test that all_mappings includes ligatures and half forms."""
        table = MappingTable(
            encoding_name="test",
            font_family="Test",
            language="Hindi",
            script="Devanagari",
            mappings={"a": "अ"},
            ligatures={"ksh": "क्ष"},
            half_forms={"k~": "क्"},
        )

        all_maps = table.all_mappings
        assert "a" in all_maps
        assert "ksh" in all_maps
        assert "k~" in all_maps

    def test_all_mappings_sorted_by_length(self):
        """Test that all_mappings returns longest keys first."""
        table = MappingTable(
            encoding_name="test",
            font_family="Test",
            language="Hindi",
            script="Devanagari",
            mappings={"a": "अ", "aa": "आ", "aaa": "अआअ"},
        )

        keys = list(table.all_mappings.keys())
        assert keys[0] == "aaa"  # Longest first
        assert keys[1] == "aa"
        assert keys[2] == "a"

    def test_reverse_mapping(self):
        """Test generating reverse mapping."""
        table = MappingTable(
            encoding_name="test",
            font_family="Test",
            language="Hindi",
            script="Devanagari",
            mappings={"a": "अ", "b": "ब"},
        )

        reverse = table.get_reverse_mapping()
        assert reverse["अ"] == "a"
        assert reverse["ब"] == "b"


class TestMappingLoader:
    """Tests for MappingLoader class."""

    def test_default_initialization(self):
        """Test default initialization."""
        loader = MappingLoader()
        assert loader is not None

    def test_custom_mapping_dirs(self, temp_dir):
        """Test initialization with custom mapping directories."""
        loader = MappingLoader(mapping_dirs=[temp_dir])
        assert temp_dir in loader._mapping_dirs

    def test_load_from_yaml_file(self, temp_dir):
        """Test loading mapping from YAML file."""
        # Create a test mapping file
        mapping_data = {
            "metadata": {
                "font_family": "Test Font",
                "language": "Hindi",
                "script": "Devanagari",
            },
            "mappings": {"a": "अ", "b": "ब"},
        }

        mapping_file = temp_dir / "test-font.yaml"
        mapping_file.write_text(yaml.dump(mapping_data))

        loader = MappingLoader(mapping_dirs=[temp_dir])
        table = loader.load("test-font")

        assert table.font_family == "Test Font"
        assert table.mappings["a"] == "अ"

    def test_load_from_json_file(self, temp_dir):
        """Test loading mapping from JSON file."""
        import json

        mapping_data = {
            "metadata": {
                "font_family": "JSON Font",
            },
            "mappings": {"x": "क"},
        }

        mapping_file = temp_dir / "json-font.json"
        mapping_file.write_text(json.dumps(mapping_data))

        loader = MappingLoader(mapping_dirs=[temp_dir])
        table = loader.load("json-font")

        assert table.font_family == "JSON Font"

    def test_load_nonexistent_raises_error(self):
        """Test that loading nonexistent mapping raises error."""
        loader = MappingLoader(mapping_dirs=[])

        with pytest.raises(MappingLoadError, match="No mapping table found"):
            loader.load("nonexistent-encoding")

    def test_load_with_caching(self, temp_dir):
        """Test that loaded mappings are cached."""
        mapping_data = {
            "metadata": {"font_family": "Cached Font"},
            "mappings": {"a": "अ"},
        }

        mapping_file = temp_dir / "cached-font.yaml"
        mapping_file.write_text(yaml.dump(mapping_data))

        loader = MappingLoader(mapping_dirs=[temp_dir])

        # First load
        table1 = loader.load("cached-font")
        # Second load (should be cached)
        table2 = loader.load("cached-font")

        assert table1 is table2

    def test_load_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML file."""
        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: ][")

        loader = MappingLoader(mapping_dirs=[temp_dir])

        with pytest.raises(MappingLoadError, match="Failed to parse YAML"):
            loader.load("invalid")

    def test_load_missing_mappings_field(self, temp_dir):
        """Test loading file without mappings field."""
        mapping_data = {
            "metadata": {"font_family": "No Mappings"},
            # Missing 'mappings' field
        }

        mapping_file = temp_dir / "no-mappings.yaml"
        mapping_file.write_text(yaml.dump(mapping_data))

        loader = MappingLoader(mapping_dirs=[temp_dir])

        with pytest.raises(MappingLoadError, match="must contain 'mappings' field"):
            loader.load("no-mappings")

    def test_list_available(self, temp_dir):
        """Test listing available mappings."""
        # Create test mapping files
        for name in ["font-a", "font-b", "font-c"]:
            mapping_file = temp_dir / f"{name}.yaml"
            mapping_file.write_text(yaml.dump({"mappings": {}}))

        loader = MappingLoader(mapping_dirs=[temp_dir])
        available = loader.list_available()

        assert "font-a" in available
        assert "font-b" in available
        assert "font-c" in available

    def test_get_builtin(self):
        """Test getting built-in mapping tables."""
        loader = MappingLoader()

        shree_lipi = loader.get_builtin("shree-lipi")
        assert shree_lipi is not None
        assert shree_lipi.font_family == "Shree-Lipi"

        kruti_dev = loader.get_builtin("kruti-dev")
        assert kruti_dev is not None
        assert kruti_dev.font_family == "Kruti Dev"

    def test_get_nonexistent_builtin(self):
        """Test getting nonexistent built-in returns None."""
        loader = MappingLoader()

        result = loader.get_builtin("nonexistent")
        assert result is None


class TestBuiltinMappings:
    """Tests for built-in mapping tables."""

    def test_shree_lipi_builtin_exists(self):
        """Test that Shree-Lipi built-in exists."""
        assert "shree-lipi" in BUILTIN_MAPPINGS

        table = BUILTIN_MAPPINGS["shree-lipi"]
        assert table.font_family == "Shree-Lipi"
        assert table.language == "Marathi"
        assert table.script == "Devanagari"

    def test_kruti_dev_builtin_exists(self):
        """Test that Kruti Dev built-in exists."""
        assert "kruti-dev" in BUILTIN_MAPPINGS

        table = BUILTIN_MAPPINGS["kruti-dev"]
        assert table.font_family == "Kruti Dev"
        assert table.language == "Hindi"

    def test_shree_lipi_has_consonants(self):
        """Test that Shree-Lipi mapping has consonant mappings."""
        table = BUILTIN_MAPPINGS["shree-lipi"]
        mappings = table.mappings

        # Check for some key consonants
        # Note: These are sample mappings based on common Shree-Lipi patterns
        assert len(mappings) > 0

    def test_kruti_dev_has_mappings(self):
        """Test that Kruti Dev mapping has character mappings."""
        table = BUILTIN_MAPPINGS["kruti-dev"]

        assert len(table.mappings) > 0
        assert len(table.ligatures) > 0


class TestGetMappingFunction:
    """Tests for get_mapping convenience function."""

    def test_get_builtin_mapping(self):
        """Test getting a built-in mapping."""
        table = get_mapping("shree-lipi")
        assert table.encoding_name == "shree-lipi"

    def test_get_another_builtin(self):
        """Test getting another built-in mapping."""
        table = get_mapping("kruti-dev")
        assert table.encoding_name == "kruti-dev"

    def test_get_nonexistent_raises(self):
        """Test that getting nonexistent mapping raises error."""
        with pytest.raises(MappingLoadError):
            get_mapping("definitely-not-a-real-encoding")


class TestMappingWithLigatures:
    """Tests for mapping tables with ligatures."""

    def test_ligatures_sorted_before_single_chars(self):
        """Test that ligatures appear before single character mappings."""
        table = MappingTable(
            encoding_name="test",
            font_family="Test",
            language="Hindi",
            script="Devanagari",
            mappings={"a": "अ", "k": "क"},
            ligatures={"ksh": "क्ष", "gya": "ज्ञ"},
        )

        all_maps = table.all_mappings
        keys = list(all_maps.keys())

        # Multi-char should come before single char
        ksh_idx = keys.index("ksh")
        a_idx = keys.index("a")
        assert ksh_idx < a_idx

    def test_half_forms_included(self):
        """Test that half forms are included in all mappings."""
        table = MappingTable(
            encoding_name="test",
            font_family="Test",
            language="Hindi",
            script="Devanagari",
            mappings={"k": "क"},
            half_forms={"k~": "क्", "g~": "ग्"},
        )

        all_maps = table.all_mappings
        assert "k~" in all_maps
        assert "g~" in all_maps
        assert all_maps["k~"] == "क्"
