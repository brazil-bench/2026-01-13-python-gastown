# =============================================================================
# File: tests/features/players.feature
# Project: Brazilian Soccer MCP Server
# Purpose: BDD feature specification for player queries
# Author: Gas Town Agent
# Created: 2026-01-13
#
# Description:
#     Gherkin scenarios for testing player search functionality.
#     Covers searching by name, nationality, club, position, and rating.
# =============================================================================

Feature: Player Queries
    As a user of the Brazilian Soccer MCP Server
    I want to search for players in the FIFA database
    So that I can find player information

    Background:
        Given the player data is loaded

    Scenario: Search players by nationality
        When I search for players from "Brazil"
        Then I should receive a list of Brazilian players
        And all players should have nationality "Brazil"

    Scenario: Search players by club
        When I search for players at club "Flamengo"
        Then I should receive players from Flamengo

    Scenario: Search players by minimum rating
        When I search for players with minimum rating 85
        Then I should receive high-rated players
        And all players should have overall rating at least 85

    Scenario: Get top Brazilian players
        When I request top Brazilian players
        Then I should receive Brazilian players sorted by rating

    Scenario: Search players by name
        When I search for player named "Neymar"
        Then I should find Neymar in the results
