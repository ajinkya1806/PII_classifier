"""
Tests for the Connector Registry and stub FileConnector.

Verifies:
  - Registry registration and lookup
  - Duplicate handling
  - The FileConnector interface generalizes to data lake/warehouse/SFTP
"""

import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.base import DataAsset, FieldMeta, FileConnector
from connectors.registry import ConnectorRegistry


class StubFileConnector(FileConnector):
    """
    Stub FileConnector for testing interface generalization.
    Proves the abstract interface works for file-based sources.
    """

    def __init__(self):
        self._files = [
            "data/customers.csv",
            "data/transactions.parquet",
            "data/kyc_docs.json",
        ]

    def list_files(self, path: str = "") -> List[str]:
        if path:
            return [f for f in self._files if f.startswith(path)]
        return self._files

    def infer_schema(self, file_path: str) -> DataAsset:
        # Simulate inferring schema from a CSV file
        if file_path.endswith(".csv"):
            return DataAsset(
                asset_name=file_path,
                fields=[
                    FieldMeta(name="name", data_type="string", nullable=True),
                    FieldMeta(name="email", data_type="string", nullable=True),
                    FieldMeta(name="phone", data_type="string", nullable=True),
                ],
                source_type="file",
            )
        return DataAsset(
            asset_name=file_path,
            fields=[],
            source_type="file",
        )

    def sample_data(self, file_path: str, field_name: str, n: int = 100) -> List[str]:
        # Return mock masked samples
        return ["****@******.***", "****@******.***"] if field_name == "email" else []

    def close(self) -> None:
        pass


class TestConnectorRegistry:
    """Test the connector registry."""

    def test_register_and_get(self):
        """Register a connector and retrieve it."""
        reg = ConnectorRegistry()
        reg.register("stub_file", StubFileConnector)
        cls = reg.get("stub_file")
        assert cls == StubFileConnector

    def test_get_nonexistent_raises(self):
        """Getting a non-existent connector should raise KeyError."""
        reg = ConnectorRegistry()
        try:
            reg.get("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass

    def test_list_connectors(self):
        """list_connectors should return registered connector names."""
        reg = ConnectorRegistry()
        reg.register("test_mysql", type("FakeMySQL", (), {}))
        reg.register("test_file", StubFileConnector)
        listing = reg.list_connectors()
        assert "test_mysql" in listing
        assert "test_file" in listing

    def test_has_connector(self):
        """has() should return True for registered, False otherwise."""
        reg = ConnectorRegistry()
        reg.register("my_conn", StubFileConnector)
        assert reg.has("my_conn")
        assert not reg.has("other_conn")

    def test_duplicate_registration_overwrites(self):
        """Re-registering with same name should overwrite."""
        reg = ConnectorRegistry()
        reg.register("dup", StubFileConnector)
        reg.register("dup", type("NewConnector", (), {}))
        cls = reg.get("dup")
        assert cls.__name__ == "NewConnector"


class TestStubFileConnector:
    """Test the stub FileConnector to prove interface generalization."""

    def setup_method(self):
        self.connector = StubFileConnector()

    def test_list_files(self):
        """Should list available files."""
        files = self.connector.list_files()
        assert len(files) == 3
        assert "data/customers.csv" in files

    def test_list_files_with_path(self):
        """Should filter files by path prefix."""
        files = self.connector.list_files("data/")
        assert len(files) == 3

    def test_infer_schema_csv(self):
        """Should return DataAsset with fields for CSV."""
        schema = self.connector.infer_schema("data/customers.csv")
        assert schema.source_type == "file"
        assert len(schema.fields) == 3
        assert schema.fields[0].name == "name"

    def test_infer_schema_non_csv(self):
        """Non-CSV files should return empty fields (stub behavior)."""
        schema = self.connector.infer_schema("data/kyc_docs.json")
        assert schema.source_type == "file"
        assert len(schema.fields) == 0

    def test_sample_data(self):
        """Should return masked sample values."""
        samples = self.connector.sample_data("data/customers.csv", "email", 10)
        assert len(samples) == 2
        assert "@" in samples[0]

    def test_close(self):
        """Close should not raise."""
        self.connector.close()
