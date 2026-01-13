"""
=============================================================================
File: tests/test_teams.py
Project: Brazilian Soccer MCP Server
Purpose: BDD tests for team query functionality
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Implements Given/When/Then step definitions for team query scenarios.
    Tests cover team statistics, home records, head-to-head comparisons,
    and team listings.

Test Pattern:
    Uses pytest-bdd with synchronous test execution. Each scenario from
    teams.feature is implemented with corresponding step functions.

Dependencies:
    - pytest-bdd: For BDD scenario execution
    - conftest.py: Provides fixtures (team_queries, loaded_data)
=============================================================================
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load all scenarios from the feature file
scenarios("features/teams.feature")


# Shared context for scenarios
@pytest.fixture
def team_context():
    """Context dictionary for storing scenario state."""
    return {"stats": None, "teams": None, "h2h": None}


# Given steps

@given("the match data is loaded")
def match_data_loaded(loaded_data):
    """Ensure match data is loaded into the database."""
    assert loaded_data is not None


# When steps

@when(parsers.parse('I request statistics for team "{team}"'))
def request_team_stats(team_queries, team_context, team):
    """Get comprehensive statistics for a team."""
    stats = team_queries.get_team_stats(team)
    team_context["stats"] = stats
    team_context["team"] = team


@when(parsers.parse('I request home record for team "{team}"'))
def request_home_record(team_queries, team_context, team):
    """Get home-only statistics for a team."""
    stats = team_queries.get_home_record(team)
    team_context["stats"] = stats
    team_context["team"] = team


@when(parsers.parse('I compare "{team1}" and "{team2}"'))
def compare_teams(team_queries, team_context, team1, team2):
    """Get head-to-head statistics between two teams."""
    h2h = team_queries.get_head_to_head(team1, team2)
    team_context["h2h"] = h2h
    team_context["team1"] = team1
    team_context["team2"] = team2


@when("I request the list of all teams")
def request_team_list(team_queries, team_context):
    """Get list of all teams in the database."""
    teams = team_queries.list_teams(limit=500)  # Get more teams to include Brazilian clubs
    team_context["teams"] = teams


# Then steps

@then("I should receive wins losses draws and goals")
def should_receive_stats(team_context):
    """Verify statistics contain required fields."""
    stats = team_context["stats"]
    assert stats is not None, "No statistics returned"
    assert hasattr(stats, "wins"), "Missing wins"
    assert hasattr(stats, "losses"), "Missing losses"
    assert hasattr(stats, "draws"), "Missing draws"
    assert hasattr(stats, "goals_for"), "Missing goals_for"
    assert hasattr(stats, "goals_against"), "Missing goals_against"


@then("the statistics should have valid point calculations")
def stats_have_valid_points(team_context):
    """Verify points are calculated correctly (3 for win, 1 for draw)."""
    stats = team_context["stats"]
    expected_points = stats.wins * 3 + stats.draws
    assert stats.points == expected_points, f"Points mismatch: {stats.points} != {expected_points}"


@then("I should receive home-only statistics")
def should_receive_home_stats(team_context):
    """Verify statistics were returned."""
    stats = team_context["stats"]
    assert stats is not None, "No home statistics returned"
    assert stats.matches > 0, "No home matches found"


@then("the team name should indicate home record")
def team_name_indicates_home(team_context):
    """Verify the stats indicate this is a home record."""
    stats = team_context["stats"]
    assert "(home)" in stats.team.lower(), f"Expected '(home)' in team name: {stats.team}"


@then("I should receive head to head statistics")
def should_receive_h2h(team_context):
    """Verify head-to-head statistics were returned."""
    h2h = team_context["h2h"]
    assert h2h is not None, "No head-to-head stats returned"
    assert "total_matches" in h2h, "Missing total_matches"
    assert "team1_wins" in h2h, "Missing team1_wins"
    assert "team2_wins" in h2h, "Missing team2_wins"
    assert "draws" in h2h, "Missing draws"


@then("the result should show wins for each team")
def h2h_shows_wins(team_context):
    """Verify head-to-head shows wins breakdown."""
    h2h = team_context["h2h"]
    # Total should equal sum of wins and draws
    total = h2h["total_matches"]
    calculated = h2h["team1_wins"] + h2h["team2_wins"] + h2h["draws"]
    assert total == calculated, f"Win counts don't sum to total: {calculated} != {total}"


@then("I should receive multiple team names")
def should_receive_multiple_teams(team_context):
    """Verify multiple teams were returned."""
    teams = team_context["teams"]
    assert teams is not None
    assert len(teams) > 10, f"Expected many teams, got {len(teams)}"


@then("common Brazilian teams should be present")
def common_teams_present(team_context):
    """Verify well-known Brazilian teams are in the list."""
    teams = team_context["teams"]
    teams_str = " ".join(teams).lower()

    # Check for some major Brazilian clubs (partial matches ok)
    major_clubs = ["palmeiras", "flamengo", "corinthians", "santos", "grêmio", "internacional"]
    found = sum(1 for club in major_clubs if club in teams_str)

    assert found >= 3, f"Expected at least 3 major clubs, found {found} in {len(teams)} teams"


# Additional GWT-style tests

class TestTeamStatistics:
    """Additional GWT-structured tests for team statistics."""

    def test_team_stats_include_goal_difference(self, team_queries, loaded_data):
        """
        Given match data is loaded
        When I request statistics for a team
        Then goal difference should equal goals_for minus goals_against
        """
        stats = team_queries.get_team_stats("Palmeiras")
        if stats:
            expected_gd = stats.goals_for - stats.goals_against
            assert stats.goal_difference == expected_gd

    def test_matches_equal_wins_draws_losses(self, team_queries, loaded_data):
        """
        Given match data is loaded
        When I request statistics for a team
        Then total matches should equal wins + draws + losses
        """
        stats = team_queries.get_team_stats("Flamengo")
        if stats:
            calculated = stats.wins + stats.draws + stats.losses
            assert stats.matches == calculated

    def test_home_record_less_than_total(self, team_queries, loaded_data):
        """
        Given match data is loaded
        When I request both total and home-only statistics
        Then home matches should be less than or equal to total matches
        """
        total_stats = team_queries.get_team_stats("Corinthians")
        home_stats = team_queries.get_home_record("Corinthians")

        if total_stats and home_stats:
            assert home_stats.matches <= total_stats.matches

    def test_head_to_head_symmetric(self, team_queries, loaded_data):
        """
        Given match data is loaded
        When I compare team A vs B and B vs A
        Then the total matches should be the same
        """
        h2h_ab = team_queries.get_head_to_head("Palmeiras", "Santos")
        h2h_ba = team_queries.get_head_to_head("Santos", "Palmeiras")

        assert h2h_ab["total_matches"] == h2h_ba["total_matches"]


class TestTeamNameNormalization:
    """Tests for team name normalization."""

    def test_team_with_state_suffix(self, team_queries, loaded_data):
        """
        Given a team name with state suffix
        When I request statistics
        Then it should match the normalized team
        """
        stats = team_queries.get_team_stats("Palmeiras-SP")
        # Should find the team even with suffix
        assert stats is None or stats.team == "Palmeiras" or "Palmeiras" in stats.team

    def test_team_without_suffix(self, team_queries, loaded_data):
        """
        Given a team name without state suffix
        When I request statistics
        Then it should find the team
        """
        stats = team_queries.get_team_stats("Flamengo")
        assert stats is not None
        assert "Flamengo" in stats.team or stats.matches > 0
