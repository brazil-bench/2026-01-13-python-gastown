# =============================================================================
# File: tests/features/competitions.feature
# Project: Brazilian Soccer MCP Server
# Purpose: BDD feature specification for competition queries
# Author: Gas Town Agent
# Created: 2026-01-13
#
# Description:
#     Gherkin scenarios for testing competition and season queries.
#     Covers league standings, competition statistics, and season listings.
# =============================================================================

Feature: Competition Queries
    As a user of the Brazilian Soccer MCP Server
    I want to retrieve competition and season data
    So that I can analyze league standings and competition history

    Background:
        Given the match data is loaded

    Scenario: Get league standings for a season
        When I request standings for Brasileirao in season 2019
        Then I should receive a list of teams with points
        And teams should be sorted by points descending

    Scenario: Get competition statistics
        When I request statistics for Brasileirao
        Then I should receive total matches and goals
        And I should receive home and away win rates

    Scenario: List all competitions
        When I request the list of competitions
        Then I should see Brasileirao Copa do Brasil and Libertadores

    Scenario: List all seasons
        When I request the list of seasons
        Then I should receive multiple season years
        And seasons should be sorted descending
