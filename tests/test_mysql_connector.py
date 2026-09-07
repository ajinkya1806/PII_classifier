"""Tests for MySQL Connector — mocked MySQL connection."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.base import mask_value
from connectors.mysql_connector import MySQLConnector


class TestMySQLConnector:
    """Test MySQL connector with mocked database."""

    @patch("connectors.mysql_connector.mysql.connector.connect")
    def test_connect_success(self, mock_connect):
        """Successful connection should not raise."""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.get_server_info.return_value = "8.0.32"
        mock_connect.return_value = mock_conn

        connector = MySQLConnector()
        connector.connect(
            host="localhost", port=3306,
            user="test", password="test", database="testdb"
        )
        result = connector.test_connection()
        assert result["success"] is True
        assert "8.0.32" in result["message"]

    @patch("connectors.mysql_connector.mysql.connector.connect")
    def test_list_tables(self, mock_connect):
        """list_tables should return table names from SHOW TABLES."""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("users",), ("payments",), ("logs",)]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = MySQLConnector()
        connector.connect(host="localhost", user="test", password="test", database="testdb")
        tables = connector.list_tables()
        assert tables == ["users", "payments", "logs"]

    @patch("connectors.mysql_connector.mysql.connector.connect")
    def test_fetch_schema(self, mock_connect):
        """fetch_schema should return DataAsset with fields."""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"Field": "id", "Type": "int(11)", "Null": "NO", "Key": "PRI", "Default": None, "Extra": "auto_increment"},
            {"Field": "email", "Type": "varchar(255)", "Null": "YES", "Key": "", "Default": None, "Extra": ""},
            {"Field": "pan_no", "Type": "char(10)", "Null": "YES", "Key": "", "Default": None, "Extra": ""},
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        connector = MySQLConnector()
        connector.connect(host="localhost", user="test", password="test", database="testdb")
        schema = connector.fetch_schema("users")
        assert schema.asset_name == "users"
        assert len(schema.fields) == 3
        assert schema.fields[1].name == "email"
        assert schema.fields[2].name == "pan_no"

    def test_mask_value_digits(self):
        """Digits should be masked with #."""
        assert mask_value("411001") == "######"

    def test_mask_value_email(self):
        """Email should preserve @ and . but mask chars."""
        masked = mask_value("john@ex.com")
        assert "@" in masked
        assert "." in masked
        assert "j" not in masked

    def test_mask_value_mixed(self):
        """Mixed alphanumeric with delimiters."""
        masked = mask_value("4111-1111-1111")
        assert masked == "####-####-####"
