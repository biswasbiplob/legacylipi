"""Font mapping tables for legacy encodings."""

from legacylipi.mappings.loader import (
    MappingLoadError,
    MappingLoader,
    MappingTable,
    get_mapping,
)

__all__ = [
    "MappingTable",
    "MappingLoader",
    "MappingLoadError",
    "get_mapping",
]
