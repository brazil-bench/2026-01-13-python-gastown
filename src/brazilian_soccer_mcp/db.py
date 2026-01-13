"""
=============================================================================
File: src/brazilian_soccer_mcp/db.py
Project: Brazilian Soccer MCP Server
Purpose: Neo4j database connection management and session handling
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Provides a connection manager for Neo4j database operations. Implements
    the context manager protocol for safe resource handling and supports
    both single queries and transaction batches.

Configuration:
    Environment variables (with defaults):
    - NEO4J_URI: bolt://localhost:7687
    - NEO4J_USER: neo4j
    - NEO4J_PASSWORD: password123
    - NEO4J_DATABASE: neo4j

Usage:
    # Single query
    with get_connection() as conn:
        result = conn.execute_query("MATCH (t:Team) RETURN t.name")

    # Using the class directly
    conn = Neo4jConnection()
    conn.connect()
    try:
        result = conn.execute_query("MATCH (n) RETURN count(n)")
    finally:
        conn.close()

Thread Safety:
    The Neo4j driver is thread-safe. Each Neo4jConnection instance manages
    its own driver instance. For concurrent access, create separate
    connection instances or use the driver's session pooling.
=============================================================================
"""

import os
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver, Session, Result


class Neo4jConnection:
    """
    Manages Neo4j database connections with automatic resource cleanup.

    Attributes:
        uri: Neo4j bolt URI
        user: Database username
        password: Database password
        database: Target database name
        driver: Neo4j driver instance (None until connected)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        Initialize connection parameters from arguments or environment.

        Args:
            uri: Neo4j bolt URI, defaults to NEO4J_URI env or localhost
            user: Username, defaults to NEO4J_USER env or 'neo4j'
            password: Password, defaults to NEO4J_PASSWORD env or 'password123'
            database: Database name, defaults to NEO4J_DATABASE env or 'neo4j'
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password123")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        """Get the driver, connecting if necessary."""
        if self._driver is None:
            self.connect()
        return self._driver

    def connect(self) -> None:
        """
        Establish connection to Neo4j database.

        Raises:
            ServiceUnavailable: If Neo4j server is not reachable
            AuthError: If credentials are invalid
        """
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            self._driver.verify_connectivity()

    def close(self) -> None:
        """Close the driver connection and release resources."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as a list of dicts.

        Args:
            query: Cypher query string
            parameters: Query parameters (optional)
            database: Override database name (optional)

        Returns:
            List of records as dictionaries
        """
        db = database or self.database
        with self.driver.session(database=db) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> None:
        """
        Execute a write query within a transaction.

        Args:
            query: Cypher query string for write operation
            parameters: Query parameters (optional)
            database: Override database name (optional)
        """
        db = database or self.database
        with self.driver.session(database=db) as session:
            session.execute_write(
                lambda tx: tx.run(query, parameters or {})
            )

    def execute_batch(
        self,
        queries: List[tuple[str, Optional[Dict[str, Any]]]]
    ) -> None:
        """
        Execute multiple write queries in a single transaction.

        Args:
            queries: List of (query, parameters) tuples
        """
        def batch_write(tx):
            for query, params in queries:
                tx.run(query, params or {})

        with self.driver.session(database=self.database) as session:
            session.execute_write(batch_write)

    def __enter__(self) -> "Neo4jConnection":
        """Context manager entry - connect and return self."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connection."""
        self.close()


# Module-level connection instance for convenience
_connection: Optional[Neo4jConnection] = None


def get_connection() -> Neo4jConnection:
    """
    Get or create the module-level Neo4j connection.

    Returns:
        Neo4jConnection instance (connected)

    Note:
        This returns a shared connection. For isolated connections,
        create a new Neo4jConnection instance directly.
    """
    global _connection
    if _connection is None:
        _connection = Neo4jConnection()
        _connection.connect()
    return _connection


def close_connection() -> None:
    """Close the module-level connection if open."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
