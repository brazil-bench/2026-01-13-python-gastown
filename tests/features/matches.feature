# =============================================================================
# File: tests/features/matches.feature
# Project: Brazilian Soccer MCP Server
# Purpose: BDD feature specification for match queries
# Author: Gas Town Agent
# Created: 2026-01-13
#
# Description:
#     Gherkin scenarios for testing match search and retrieval functionality.
#     Covers head-to-head matches, team matches, date range queries, and
#     statistical analysis queries.
# =============================================================================

Feature: Match Queries
    As a user of the Brazilian Soccer MCP Server
    I want to search for and retrieve match data
    So that I can analyze Brazilian soccer history

    Background:
        Given the match data is loaded

    Scenario: Find matches between two teams
        When I search for matches between "Flamengo" and "Fluminense"
        Then I should receive a list of matches
        And each match should have date scores and competition

    Scenario: Find matches for a single team
        When I search for matches for team "Palmeiras"
        Then I should receive a list of matches
        And all matches should include "Palmeiras"

    Scenario: Find matches by season
        When I search for matches for team "Corinthians" in season 2019
        Then I should receive a list of matches
        And all matches should be from season 2019

    Scenario: Get biggest wins
        When I request the biggest wins
        Then I should receive matches sorted by goal difference
        And the first match should have a large goal difference

    Scenario: Find matches by competition
        When I search for matches in competition "Copa do Brasil"
        Then I should receive matches from Copa do Brasil only
