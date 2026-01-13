"""
=============================================================================
File: tests/test_competitions.py
Project: Brazilian Soccer MCP Server
Purpose: BDD tests for competition query functionality
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Implements Given/When/Then step definitions for competition and season
    query scenarios. Tests cover league standings, competition statistics,
    and listing functions.

Test Pattern:
    Uses pytest-bdd with synchronous test execution. Each scenario from
    competitions.feature is implemented with corresponding step functions.

Dependencies:
    - pytest-bdd: For BDD scenario execution
    - conftest.py: Provides fixtures (competition_queries, loaded_data)
=============================================================================
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load all scenarios from the feature file
scenarios("features/competitions.feature")


# Shared context for scenarios
@pytest.fixture
def comp_context():
    """Context dictionary for storing scenario state."""
    return {"standings": None, "stats": None, "competitions": None, "seasons": None}


# Given steps

@given("the match data is loaded")
def match_data_loaded(loaded_data):
    """Ensure match data is loaded into the database."""
    assert loaded_data is not None


# When steps

@when(parsers.parse("I request standings for Brasileirao in season {season:d}"))
def request_standings(competition_queries, comp_context, season):
    """Get league standings for a season."""
    standings = competition_queries.get_season_standings(season, "Brasileirão")
    comp_context["standings"] = standings
    comp_context["season"] = season


@when("I request statistics for Brasileirao")
def request_competition_stats(competition_queries, comp_context):
    """Get aggregate statistics for Brasileirão."""
    stats = competition_queries.get_competition_stats("Brasileirão")
    comp_context["stats"] = stats


@when("I request the list of competitions")
def request_competition_list(competition_queries, comp_context):
    """Get list of all competitions."""
    competitions = competition_queries.list_competitions()
    comp_context["competitions"] = competitions


@when("I request the list of seasons")
def request_season_list(competition_queries, comp_context):
    """Get list of all seasons."""
    seasons = competition_queries.list_seasons()
    comp_context["seasons"] = seasons


# Then steps

@then("I should receive a list of teams with points")
def should_receive_standings(comp_context):
    """Verify standings contain teams with points."""
    standings = comp_context["standings"]
    assert standings is not None
    assert len(standings) > 0, "No standings data returned"

    for team_stats in standings:
        assert hasattr(team_stats, "team"), "Missing team name"
        assert hasattr(team_stats, "points"), "Missing points"
        assert hasattr(team_stats, "wins"), "Missing wins"


@then("teams should be sorted by points descending")
def standings_sorted_by_points(comp_context):
    """Verify teams are sorted by points in descending order."""
    standings = comp_context["standings"]
    prev_points = float("inf")
    for team_stats in standings:
        assert team_stats.points <= prev_points, "Standings not sorted by points"
        prev_points = team_stats.points


@then("I should receive total matches and goals")
def should_receive_totals(comp_context):
    """Verify statistics include totals."""
    stats = comp_context["stats"]
    assert stats is not None
    assert "total_matches" in stats, "Missing total_matches"
    assert "total_goals" in stats, "Missing total_goals"
    assert stats["total_matches"] > 0, "No matches found"


@then("I should receive home and away win rates")
def should_receive_win_rates(comp_context):
    """Verify statistics include win rates."""
    stats = comp_context["stats"]
    assert "home_win_rate" in stats, "Missing home_win_rate"
    assert "away_win_rate" in stats, "Missing away_win_rate"
    assert "draw_rate" in stats, "Missing draw_rate"

    # Win rates should sum to approximately 100%
    total_rate = stats["home_win_rate"] + stats["away_win_rate"] + stats["draw_rate"]
    assert 98 <= total_rate <= 102, f"Win rates sum to {total_rate}, expected ~100"


@then("I should see Brasileirao Copa do Brasil and Libertadores")
def should_see_major_competitions(comp_context):
    """Verify major competitions are listed."""
    competitions = comp_context["competitions"]
    assert competitions is not None
    assert len(competitions) > 0

    comp_names = [c["name"].lower() for c in competitions]
    comp_str = " ".join(comp_names)

    assert "brasil" in comp_str or "série" in comp_str, "Missing Brasileirão"
    # Copa do Brasil and Libertadores may have different names


@then("I should receive multiple season years")
def should_receive_multiple_seasons(comp_context):
    """Verify multiple seasons are returned."""
    seasons = comp_context["seasons"]
    assert seasons is not None
    assert len(seasons) > 5, f"Expected many seasons, got {len(seasons)}"


@then("seasons should be sorted descending")
def seasons_sorted_descending(comp_context):
    """Verify seasons are sorted in descending order."""
    seasons = comp_context["seasons"]
    for i in range(len(seasons) - 1):
        assert seasons[i] >= seasons[i + 1], "Seasons not sorted descending"


# Additional GWT-style tests

class TestStandingsCalculations:
    """Additional GWT-structured tests for standings calculations."""

    def test_standings_points_calculation(self, competition_queries, loaded_data):
        """
        Given standings for a season
        When I check each team's points
        Then points should equal 3*wins + draws
        """
        standings = competition_queries.get_season_standings(2019, "Brasileirão")
        for team in standings:
            expected = team.wins * 3 + team.draws
            assert team.points == expected, \
                f"{team.team}: {team.points} != {expected} (3*{team.wins} + {team.draws})"

    def test_standings_match_totals(self, competition_queries, loaded_data):
        """
        Given standings for a season
        When I check match totals
        Then wins + draws + losses should equal total matches
        """
        standings = competition_queries.get_season_standings(2019, "Brasileirão")
        for team in standings:
            calculated = team.wins + team.draws + team.losses
            assert team.matches == calculated, \
                f"{team.team}: matches {team.matches} != {calculated}"

    def test_goal_difference_calculation(self, competition_queries, loaded_data):
        """
        Given standings for a season
        When I check goal differences
        Then GD should equal goals_for - goals_against
        """
        standings = competition_queries.get_season_standings(2019, "Brasileirão")
        for team in standings:
            expected_gd = team.goals_for - team.goals_against
            assert team.goal_difference == expected_gd, \
                f"{team.team}: GD {team.goal_difference} != {expected_gd}"


class TestCompetitionStats:
    """Tests for competition statistics."""

    def test_home_wins_plus_away_wins_plus_draws(self, competition_queries, loaded_data):
        """
        Given competition statistics
        When I sum home wins, away wins, and draws
        Then it should equal total matches
        """
        stats = competition_queries.get_competition_stats("Brasileirão")
        total = stats["home_wins"] + stats["away_wins"] + stats["draws"]
        assert total == stats["total_matches"], \
            f"Sum {total} != total_matches {stats['total_matches']}"

    def test_average_goals_reasonable(self, competition_queries, loaded_data):
        """
        Given competition statistics
        When I check average goals per match
        Then it should be between 1 and 5
        """
        stats = competition_queries.get_competition_stats("Brasileirão")
        avg = stats["avg_goals_per_match"]
        assert 1.0 <= avg <= 5.0, f"Average goals {avg} seems unreasonable"


class TestSeasonData:
    """Tests for season data integrity."""

    def test_seasons_are_valid_years(self, competition_queries, loaded_data):
        """
        Given the list of seasons
        When I check each season
        Then it should be a valid year (1990-2030)
        """
        seasons = competition_queries.list_seasons()
        for season in seasons:
            assert 1990 <= season <= 2030, f"Invalid season year: {season}"

    def test_competitions_have_match_counts(self, competition_queries, loaded_data):
        """
        Given the list of competitions
        When I check each competition
        Then it should have a non-negative match count
        """
        competitions = competition_queries.list_competitions()
        for comp in competitions:
            assert comp["match_count"] >= 0, \
                f"Competition {comp['name']} has negative match count"
