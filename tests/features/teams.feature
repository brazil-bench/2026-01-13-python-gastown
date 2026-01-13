# =============================================================================
# File: tests/features/teams.feature
# Project: Brazilian Soccer MCP Server
# Purpose: BDD feature specification for team queries
# Author: Gas Town Agent
# Created: 2026-01-13
#
# Description:
#     Gherkin scenarios for testing team statistics and comparison
#     functionality. Covers team stats, home records, head-to-head
#     comparisons, and team listings.
# =============================================================================

Feature: Team Queries
    As a user of the Brazilian Soccer MCP Server
    I want to retrieve team statistics and comparisons
    So that I can analyze team performance

    Background:
        Given the match data is loaded

    Scenario: Get team statistics
        When I request statistics for team "Palmeiras"
        Then I should receive wins losses draws and goals
        And the statistics should have valid point calculations

    Scenario: Get home record for a team
        When I request home record for team "Flamengo"
        Then I should receive home-only statistics
        And the team name should indicate home record

    Scenario: Compare two teams head to head
        When I compare "Palmeiras" and "Santos"
        Then I should receive head to head statistics
        And the result should show wins for each team

    Scenario: List all teams
        When I request the list of all teams
        Then I should receive multiple team names
        And common Brazilian teams should be present
