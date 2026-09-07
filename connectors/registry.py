"""
Connector Registry — a simple name→class registry so new connectors
can register themselves without touching engines/classifier/API code.
"""

from __future__ import annotations

import logging
from typing import Dict, Type, Union

from connectors.base import FileConnector, TableConnector

logger = logging.getLogger(__name__)

ConnectorType = Union[Type[TableConnector], Type[FileConnector]]


class ConnectorRegistry:
    """
    Central registry for all data connectors.
    Connectors self-register by calling registry.register(name, cls).
    """

    def __init__(self):
        self._connectors: Dict[str, ConnectorType] = {}

    def register(self, name: str, cls: ConnectorType) -> None:
        """Register a connector class under the given name."""
        if name in self._connectors:
            logger.warning(f"Connector '{name}' is being re-registered. Overwriting.")
        self._connectors[name] = cls
        logger.info(f"Registered connector: {name} -> {cls.__name__}")

    def get(self, name: str) -> ConnectorType:
        """Retrieve a connector class by name. Raises KeyError if not found."""
        if name not in self._connectors:
            available = ", ".join(self._connectors.keys()) or "(none)"
            raise KeyError(
                f"Connector '{name}' not found. Available: {available}"
            )
        return self._connectors[name]

    def list_connectors(self) -> Dict[str, str]:
        """Return a dict of {name: class_name} for all registered connectors."""
        return {name: cls.__name__ for name, cls in self._connectors.items()}

    def has(self, name: str) -> bool:
        """Check if a connector is registered."""
        return name in self._connectors


# Global singleton registry
registry = ConnectorRegistry()


def _auto_register():
    """Auto-register built-in connectors on import."""
    try:
        from connectors.mysql_connector import MySQLConnector
        registry.register("mysql", MySQLConnector)
    except ImportError as e:
        logger.warning(f"Could not auto-register MySQL connector: {e}")


_auto_register()
