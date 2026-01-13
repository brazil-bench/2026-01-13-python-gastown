"""
=============================================================================
File: tests/conftest.py
Project: Brazilian Soccer MCP Server
Purpose: PyTest fixtures and configuration for BDD tests
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Provides shared fixtures for all tests including Neo4j database
    connection, data loading, and query interface instances. Uses
    pytest-bdd for BDD/Gherkin-style testing.

Fixtures:
    - neo4j_connection: Database connection (session-scoped)
    - loaded_data: Ensures data is loaded into Neo4j
    - match_queries: MatchQueries instance
    - team_queries: TeamQueries instance
    - player_queries: PlayerQueries instance
    - competition_queries: CompetitionQueries instance

Configuration:
    Uses environment variables or defaults:
    - NEO4J_URI: bolt://localhost:7687
    - NEO4J_USER: neo4j
    - NEO4J_PASSWORD: password123
=============================================================================
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from brazilian_soccer_mcp.db import Neo4jConnection
from brazilian_soccer_mcp.data_loader import DataLoader
from brazilian_soccer_mcp.queries import (
    MatchQueries,
    TeamQueries,
    PlayerQueries,
    CompetitionQueries
)


@pytest.fixture(scope="session")
def neo4j_connection():
    """
    Create a Neo4j connection for the test session.

    Yields:
        Neo4jConnection: Connected database instance

    Note:
        Connection is shared across all tests for efficiency.
        Data is loaded once at session start.
    """
    conn = Neo4jConnection(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password123"),
        database=os.getenv("NEO4J_DATABASE", "neo4j")
    )
    conn.connect()
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def data_dir():
    """
    Get the path to the data directory.

    Returns:
        Path: Path to data/kaggle directory
    """
    return Path(__file__).parent.parent / "data" / "kaggle"


@pytest.fixture(scope="session")
def loaded_data(neo4j_connection, data_dir):
    """
    Load test data into Neo4j database.

    This fixture ensures data is loaded before any tests run.
    Only loads data once per test session.

    Args:
        neo4j_connection: Database connection
        data_dir: Path to CSV files

    Returns:
        dict: Load statistics
    """
    loader = DataLoader(neo4j_connection, str(data_dir))

    # Check if data already loaded (both matches and players)
    match_count = neo4j_connection.execute_query("MATCH (m:Match) RETURN count(m) as count")
    player_count = neo4j_connection.execute_query("MATCH (p:Player) RETURN count(p) as count")

    matches_loaded = match_count and match_count[0].get("count", 0) > 100
    players_loaded = player_count and player_count[0].get("count", 0) > 100

    if matches_loaded and players_loaded:
        # All data already loaded, return cached stats
        return {"cached": True}

    # Load fresh data
    stats = loader.load_all(clear=True)
    return stats


@pytest.fixture
def match_queries(neo4j_connection, loaded_data):
    """
    Create MatchQueries instance with loaded data.

    Args:
        neo4j_connection: Database connection
        loaded_data: Ensures data is loaded

    Returns:
        MatchQueries: Query interface for matches
    """
    return MatchQueries(neo4j_connection)


@pytest.fixture
def team_queries(neo4j_connection, loaded_data):
    """
    Create TeamQueries instance with loaded data.

    Args:
        neo4j_connection: Database connection
        loaded_data: Ensures data is loaded

    Returns:
        TeamQueries: Query interface for teams
    """
    return TeamQueries(neo4j_connection)


@pytest.fixture
def player_queries(neo4j_connection, loaded_data):
    """
    Create PlayerQueries instance with loaded data.

    Args:
        neo4j_connection: Database connection
        loaded_data: Ensures data is loaded

    Returns:
        PlayerQueries: Query interface for players
    """
    return PlayerQueries(neo4j_connection)


@pytest.fixture
def competition_queries(neo4j_connection, loaded_data):
    """
    Create CompetitionQueries instance with loaded data.

    Args:
        neo4j_connection: Database connection
        loaded_data: Ensures data is loaded

    Returns:
        CompetitionQueries: Query interface for competitions
    """
    return CompetitionQueries(neo4j_connection)


# BDD step definition helpers

@pytest.fixture
def context():
    """
    Shared context dictionary for BDD scenarios.

    Returns:
        dict: Empty context for storing scenario state
    """
    return {}
