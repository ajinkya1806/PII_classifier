"""
Base abstractions for data connectors.

Defines DataAsset, FieldMeta, and abstract connector interfaces (TableConnector, FileConnector)
that generalize across MySQL, PostgreSQL, data lakes, warehouses, and SFTP sources.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FieldMeta:
    """Metadata for a single field/column in a data asset."""
    name: str
    data_type: str
    nullable: bool = True
    sample_values: List[str] = field(default_factory=list)


@dataclass
class DataAsset:
    """
    A data asset represents a table, file, or any structured data source
    with a name and a list of fields.
    """
    asset_name: str
    fields: List[FieldMeta]
    source_type: str = "table"  # "table" | "file"
    metadata: Dict[str, Any] = field(default_factory=dict)


def mask_value(value: str) -> str:
    """
    Mask a raw value to preserve format/structure without exposing sensitive data.
    Digits → '#', letters → '*', preserves delimiters and whitespace.
    Also preserves length information.

    Examples:
        "411001"      → "######"
        "john@ex.com" → "****@**.***"
        "4111-1111"   → "####-####"
    """
    if value is None:
        return ""
    result = []
    for ch in str(value):
        if ch.isdigit():
            result.append("#")
        elif ch.isalpha():
            result.append("*")
        else:
            result.append(ch)
    return "".join(result)


def generalize_value(value: str) -> Dict[str, Any]:
    """
    Produce a generalized summary of a value: length, character-class pattern,
    and format hints — never the raw value itself.
    """
    if value is None:
        return {"length": 0, "pattern": "", "has_digits": False, "has_alpha": False}

    v = str(value)
    pattern_parts = []
    i = 0
    while i < len(v):
        if v[i].isdigit():
            count = 0
            while i < len(v) and v[i].isdigit():
                count += 1
                i += 1
            pattern_parts.append(f"D{{{count}}}")
        elif v[i].isalpha():
            count = 0
            while i < len(v) and v[i].isalpha():
                count += 1
                i += 1
            pattern_parts.append(f"A{{{count}}}")
        else:
            pattern_parts.append(v[i])
            i += 1

    return {
        "length": len(v),
        "pattern": "".join(pattern_parts),
        "has_digits": any(c.isdigit() for c in v),
        "has_alpha": any(c.isalpha() for c in v),
        "has_special": bool(re.search(r'[^a-zA-Z0-9\s]', v)),
    }


class TableConnector(ABC):
    """
    Abstract base for connectors that talk to tabular data sources
    (MySQL, PostgreSQL, data warehouses, etc.).
    """

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """Establish a connection to the data source."""
        ...

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection.
        Returns: {"success": bool, "message": str}
        """
        ...

    @abstractmethod
    def list_tables(self) -> List[str]:
        """Return a list of table names in the connected database."""
        ...

    @abstractmethod
    def fetch_schema(self, table: str) -> DataAsset:
        """
        Fetch column metadata for a given table.
        Returns a DataAsset with field metadata (no sample data yet).
        """
        ...

    @abstractmethod
    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        """
        Sample up to n values from a table column.
        Values should be returned as masked/generalized strings.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the connection."""
        ...


class FileConnector(ABC):
    """
    Abstract base for connectors that handle file-based data sources
    (data lake, SFTP, S3, local filesystem, etc.).

    Not implemented in this iteration — interface exists as a drop-in
    for future connectors.
    """

    @abstractmethod
    def list_files(self, path: str = "") -> List[str]:
        """List available files at the given path."""
        ...

    @abstractmethod
    def infer_schema(self, file_path: str) -> DataAsset:
        """
        Infer the schema (field names, types) from a file.
        Returns a DataAsset with source_type="file".
        """
        ...

    @abstractmethod
    def sample_data(self, file_path: str, field_name: str, n: int = 100) -> List[str]:
        """
        Sample up to n values for a given field from a file.
        Values should be returned as masked/generalized strings.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close any open connections/handles."""
        ...
