"""
=============================================================================
File: tests/__init__.py
Project: Brazilian Soccer MCP Server
Purpose: Test package initialization
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Test suite for the Brazilian Soccer MCP Server. Tests are structured
    using BDD (Behavior-Driven Development) with Given/When/Then scenarios
    implemented via pytest-bdd.

Test Structure:
    - conftest.py: Shared fixtures (Neo4j connection, data loading)
    - features/: Gherkin feature files
    - test_matches.py: Match query tests
    - test_teams.py: Team statistics tests
    - test_players.py: Player search tests
    - test_competitions.py: Competition/season tests

Running Tests:
    pytest tests/                    # Run all tests
    pytest tests/ -v                 # Verbose output
    pytest tests/ -k "match"         # Run match tests only
    pytest tests/ --tb=short         # Shorter traceback

Note:
    Tests use synchronous execution (no async). A fresh Neo4j database
    is used for testing with sample data loaded via fixtures.
=============================================================================
"""
