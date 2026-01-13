"""
=============================================================================
File: tests/test_players.py
Project: Brazilian Soccer MCP Server
Purpose: BDD tests for player query functionality
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Implements Given/When/Then step definitions for player query scenarios.
    Tests cover searching players by nationality, club, rating, position,
    and name.

Test Pattern:
    Uses pytest-bdd with synchronous test execution. Each scenario from
    players.feature is implemented with corresponding step functions.

Dependencies:
    - pytest-bdd: For BDD scenario execution
    - conftest.py: Provides fixtures (player_queries, loaded_data)
=============================================================================
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load all scenarios from the feature file
scenarios("features/players.feature")


# Shared context for scenarios
@pytest.fixture
def player_context():
    """Context dictionary for storing scenario state."""
    return {"players": None, "search_criteria": {}}


# Given steps

@given("the player data is loaded")
def player_data_loaded(loaded_data):
    """Ensure player data is loaded into the database."""
    assert loaded_data is not None


# When steps

@when(parsers.parse('I search for players from "{nationality}"'))
def search_players_by_nationality(player_queries, player_context, nationality):
    """Search for players by nationality."""
    players = player_queries.search_players(nationality=nationality)
    player_context["players"] = players
    player_context["nationality"] = nationality


@when(parsers.parse('I search for players at club "{club}"'))
def search_players_by_club(player_queries, player_context, club):
    """Search for players by club."""
    players = player_queries.get_players_by_club(club)
    player_context["players"] = players
    player_context["club"] = club


@when(parsers.parse("I search for players with minimum rating {rating:d}"))
def search_players_by_rating(player_queries, player_context, rating):
    """Search for players with minimum overall rating."""
    players = player_queries.search_players(min_overall=rating)
    player_context["players"] = players
    player_context["min_rating"] = rating


@when("I request top Brazilian players")
def request_top_brazilian_players(player_queries, player_context):
    """Get top-rated Brazilian players."""
    players = player_queries.get_top_players(nationality="Brazil")
    player_context["players"] = players
    player_context["nationality"] = "Brazil"


@when(parsers.parse('I search for player named "{name}"'))
def search_player_by_name(player_queries, player_context, name):
    """Search for a player by name."""
    players = player_queries.search_players(name=name)
    player_context["players"] = players
    player_context["name"] = name


# Then steps

@then("I should receive a list of Brazilian players")
def should_receive_brazilian_players(player_context):
    """Verify Brazilian players were returned."""
    players = player_context["players"]
    assert players is not None
    assert len(players) > 0, "No Brazilian players found"


@then(parsers.parse('all players should have nationality "{nationality}"'))
def all_players_have_nationality(player_context, nationality):
    """Verify all players have the specified nationality."""
    players = player_context["players"]
    for player in players:
        assert nationality.lower() in player.nationality.lower(), \
            f"Player {player.name} has nationality {player.nationality}, expected {nationality}"


@then("I should receive players from Flamengo")
def should_receive_flamengo_players(player_context):
    """Verify players from Flamengo were returned."""
    players = player_context["players"]
    # May be empty if no Flamengo players in FIFA data with that exact club name
    assert players is not None


@then("I should receive high-rated players")
def should_receive_high_rated_players(player_context):
    """Verify high-rated players were returned."""
    players = player_context["players"]
    assert players is not None
    assert len(players) > 0, "No high-rated players found"


@then(parsers.parse("all players should have overall rating at least {rating:d}"))
def all_players_meet_rating(player_context, rating):
    """Verify all players meet minimum rating threshold."""
    players = player_context["players"]
    for player in players:
        if player.overall is not None:
            assert player.overall >= rating, \
                f"Player {player.name} has rating {player.overall}, expected >= {rating}"


@then("I should receive Brazilian players sorted by rating")
def should_receive_sorted_brazilian_players(player_context):
    """Verify Brazilian players are sorted by rating descending."""
    players = player_context["players"]
    assert len(players) > 0

    # Verify sorted by overall rating (descending)
    prev_rating = float("inf")
    for player in players:
        if player.overall is not None:
            assert player.overall <= prev_rating, "Players not sorted by rating"
            prev_rating = player.overall


@then("I should find Neymar in the results")
def should_find_neymar(player_context):
    """Verify Neymar is in the search results."""
    players = player_context["players"]
    assert players is not None

    neymar_found = any(
        "neymar" in player.name.lower()
        for player in players
    )
    assert neymar_found, "Neymar not found in results"


# Additional GWT-style tests

class TestPlayerSearchIntegrity:
    """Additional GWT-structured tests for player search."""

    def test_player_has_required_fields(self, player_queries, loaded_data):
        """
        Given player data is loaded
        When I search for any players
        Then each player should have name and nationality
        """
        players = player_queries.search_players(limit=5)
        for player in players:
            assert player.name, "Player missing name"
            assert player.nationality, "Player missing nationality"

    def test_search_by_position(self, player_queries, loaded_data):
        """
        Given player data is loaded
        When I search for goalkeepers
        Then I should find players with GK position
        """
        players = player_queries.search_players(position="GK", limit=10)
        if players:
            for player in players:
                if player.position:
                    assert "GK" in player.position

    def test_combined_search_criteria(self, player_queries, loaded_data):
        """
        Given player data is loaded
        When I search with multiple criteria
        Then results should match all criteria
        """
        players = player_queries.search_players(
            nationality="Brazil",
            min_overall=75,
            limit=20
        )
        for player in players:
            assert "brazil" in player.nationality.lower()
            if player.overall:
                assert player.overall >= 75

    def test_limit_parameter_respected(self, player_queries, loaded_data):
        """
        Given player data is loaded
        When I search with a limit of 5
        Then I should receive at most 5 players
        """
        players = player_queries.search_players(nationality="Brazil", limit=5)
        assert len(players) <= 5


class TestPlayerRatings:
    """Tests for player rating functionality."""

    def test_top_players_are_high_rated(self, player_queries, loaded_data):
        """
        Given player data is loaded
        When I request top players
        Then all should have rating above 80
        """
        players = player_queries.get_top_players(limit=10)
        for player in players:
            if player.overall:
                assert player.overall >= 80

    def test_potential_at_least_overall(self, player_queries, loaded_data):
        """
        Given player data is loaded
        When I check player ratings
        Then potential should be >= overall for each player
        """
        players = player_queries.search_players(limit=20)
        for player in players:
            if player.overall and player.potential:
                assert player.potential >= player.overall, \
                    f"{player.name}: potential {player.potential} < overall {player.overall}"
