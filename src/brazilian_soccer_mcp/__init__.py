"""
=============================================================================
File: src/brazilian_soccer_mcp/__init__.py
Project: Brazilian Soccer MCP Server
Purpose: Package initialization and public API exports
Author: Gas Town Agent
Created: 2026-01-13

Description:
    This package provides an MCP (Model Context Protocol) server for querying
    Brazilian soccer data stored in a Neo4j graph database. The server enables
    natural language queries about players, teams, matches, and competitions.

Architecture:
    - db.py: Neo4j database connection management
    - models.py: Data models for teams, players, matches
    - data_loader.py: CSV data loading and graph population
    - queries.py: Query functions for match/team/player data
    - server.py: MCP server implementation with tool definitions

Data Sources:
    - Brasileirao_Matches.csv: Serie A matches (4,180 records)
    - Brazilian_Cup_Matches.csv: Copa do Brasil matches (1,337 records)
    - Libertadores_Matches.csv: Copa Libertadores matches (1,255 records)
    - BR-Football-Dataset.csv: Extended match statistics (10,296 records)
    - novo_campeonato_brasileiro.csv: Historical data 2003-2019 (6,886 records)
    - fifa_data.csv: FIFA player database (18,207 players)

Graph Schema:
    Nodes: Team, Player, Match, Competition, Season
    Relationships: PLAYED_IN, PARTICIPATED, HOME_TEAM, AWAY_TEAM, MEMBER_OF
=============================================================================
"""

from .db import Neo4jConnection, get_connection
from .data_loader import DataLoader
from .queries import MatchQueries, TeamQueries, PlayerQueries, CompetitionQueries
from .server import create_server

__version__ = "1.0.0"
__all__ = [
    "Neo4jConnection",
    "get_connection",
    "DataLoader",
    "MatchQueries",
    "TeamQueries",
    "PlayerQueries",
    "CompetitionQueries",
    "create_server",
]
