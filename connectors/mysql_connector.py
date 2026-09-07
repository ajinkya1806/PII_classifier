"""
MySQL Connector — implements TableConnector for MySQL databases.

Credentials come from the request body or local config — never hardcoded.
Sampling masks/truncates values before anything reaches downstream engines.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import Error as MySQLError

from connectors.base import DataAsset, FieldMeta, TableConnector, mask_value

logger = logging.getLogger(__name__)


class MySQLConnector(TableConnector):
    """MySQL implementation of the TableConnector interface."""

    def __init__(self):
        self._connection = None
        self._config: Dict[str, Any] = {}

    def connect(self, **kwargs) -> None:
        """
        Establish a MySQL connection.

        Expected kwargs: host, port, user, password, database
        """
        self._config = {
            "host": kwargs.get("host", "localhost"),
            "port": int(kwargs.get("port", 3306)),
            "user": kwargs.get("user", "root"),
            "password": kwargs.get("password", ""),
            "database": kwargs.get("database", ""),
            "connect_timeout": int(kwargs.get("connect_timeout", 10)),
            "use_pure": True,
        }
        try:
            self._connection = mysql.connector.connect(**self._config)
            logger.info(
                f"Connected to MySQL: {self._config['host']}:{self._config['port']}"
                f"/{self._config['database']}"
            )
        except MySQLError as e:
            logger.error(f"MySQL connection failed: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """Test MySQL connectivity. Returns success status and message."""
        try:
            if self._connection is None:
                self.connect(**self._config)

            if self._connection and self._connection.is_connected():
                info = self._connection.get_server_info()
                return {
                    "success": True,
                    "message": f"Connected to MySQL server {info}",
                }
            return {"success": False, "message": "Connection not established"}
        except MySQLError as e:
            return {"success": False, "message": str(e)}

    def list_tables(self) -> List[str]:
        """Return list of table names in the connected database."""
        if not self._connection or not self._connection.is_connected():
            raise RuntimeError("Not connected to MySQL. Call connect() first.")

        cursor = self._connection.cursor()
        try:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables")
            return tables
        finally:
            cursor.close()

    def fetch_schema(self, table: str) -> DataAsset:
        """Fetch column metadata for a table → DataAsset."""
        if not self._connection or not self._connection.is_connected():
            raise RuntimeError("Not connected to MySQL. Call connect() first.")

        cursor = self._connection.cursor(dictionary=True)
        try:
            cursor.execute(f"DESCRIBE `{table}`")
            rows = cursor.fetchall()

            fields = []
            for row in rows:
                fields.append(
                    FieldMeta(
                        name=row["Field"],
                        data_type=row["Type"],
                        nullable=(row["Null"] == "YES"),
                    )
                )

            return DataAsset(
                asset_name=table,
                fields=fields,
                source_type="table",
                metadata={
                    "database": self._config.get("database", ""),
                    "host": self._config.get("host", ""),
                },
            )
        finally:
            cursor.close()

    def sample_data(
        self, table: str, column: str, n: int = 100, mask: bool = True
    ) -> List[str]:
        """
        Sample up to n non-null values from a column.
        Values are masked by default to prevent raw sensitive data exposure.
        """
        if not self._connection or not self._connection.is_connected():
            raise RuntimeError("Not connected to MySQL. Call connect() first.")

        cursor = self._connection.cursor()
        try:
            query = (
                f"SELECT `{column}` FROM `{table}` "
                f"WHERE `{column}` IS NOT NULL "
                f"LIMIT {int(n)}"
            )
            cursor.execute(query)
            rows = cursor.fetchall()

            values = []
            for row in rows:
                val = str(row[0]) if row[0] is not None else ""
                if mask:
                    values.append(mask_value(val))
                else:
                    values.append(val)

            logger.info(
                f"Sampled {len(values)} values from {table}.{column}"
                f" (masked={mask})"
            )
            return values
        finally:
            cursor.close()

    def sample_data_raw(self, table: str, column: str, n: int = 100) -> List[str]:
        """
        Sample raw (unmasked) values — used only by the pattern engine
        for regex validation. These values never leave the local pipeline.
        """
        return self.sample_data(table, column, n, mask=False)

    def close(self) -> None:
        """Close the MySQL connection."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            logger.info("MySQL connection closed")
        self._connection = None
