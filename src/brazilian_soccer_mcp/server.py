"""
=============================================================================
File: src/brazilian_soccer_mcp/server.py
Project: Brazilian Soccer MCP Server
Purpose: MCP server implementation with tool definitions for soccer queries
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Implements the Model Context Protocol (MCP) server that exposes Brazilian
    soccer data through natural language query tools. The server provides
    tools for querying matches, teams, players, and competitions stored in
    the Neo4j graph database.

MCP Tools Exposed:
    - search_matches: Find matches by team, date range, competition
    - get_team_stats: Get statistics for a specific team
    - compare_teams: Head-to-head comparison between two teams
    - search_players: Find players by name, nationality, club, position
    - get_standings: Get league standings for a season
    - get_competition_stats: Get aggregate competition statistics

Usage:
    # Create and run the server
    server = create_server()
    server.run()

    # Or with custom connection
    from brazilian_soccer_mcp.db import Neo4jConnection
    conn = Neo4jConnection(uri="bolt://custom:7687")
    server = create_server(connection=conn)

Protocol:
    The server communicates via stdio using the MCP JSON-RPC protocol.
    It registers tools that LLMs can call to retrieve soccer data.
=============================================================================
"""

from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .db import Neo4jConnection, get_connection
from .queries import MatchQueries, TeamQueries, PlayerQueries, CompetitionQueries


def create_server(connection: Optional[Neo4jConnection] = None) -> Server:
    """
    Create and configure the MCP server with all soccer query tools.

    Args:
        connection: Optional Neo4j connection (uses default if None)

    Returns:
        Configured MCP Server instance
    """
    conn = connection or get_connection()

    # Initialize query interfaces
    match_queries = MatchQueries(conn)
    team_queries = TeamQueries(conn)
    player_queries = PlayerQueries(conn)
    competition_queries = CompetitionQueries(conn)

    # Create the MCP server
    server = Server("brazilian-soccer-mcp")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """Return the list of available tools."""
        return [
            Tool(
                name="search_matches",
                description="Search for Brazilian soccer matches. Can filter by team(s), date range, season, and competition (Brasileirão, Copa do Brasil, Libertadores).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team": {
                            "type": "string",
                            "description": "Team name to search for matches"
                        },
                        "team2": {
                            "type": "string",
                            "description": "Second team for head-to-head matches (optional)"
                        },
                        "season": {
                            "type": "integer",
                            "description": "Season year (e.g., 2023)"
                        },
                        "competition": {
                            "type": "string",
                            "description": "Competition name: Brasileirão, Copa do Brasil, or Libertadores"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (ISO format: YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (ISO format: YYYY-MM-DD)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 20)"
                        }
                    }
                }
            ),
            Tool(
                name="get_team_stats",
                description="Get comprehensive statistics for a Brazilian soccer team including wins, losses, draws, goals scored/conceded.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team": {
                            "type": "string",
                            "description": "Team name (e.g., Flamengo, Palmeiras, Corinthians)"
                        },
                        "season": {
                            "type": "integer",
                            "description": "Season year (optional)"
                        },
                        "competition": {
                            "type": "string",
                            "description": "Competition name (optional)"
                        },
                        "home_only": {
                            "type": "boolean",
                            "description": "Only include home matches"
                        }
                    },
                    "required": ["team"]
                }
            ),
            Tool(
                name="compare_teams",
                description="Get head-to-head statistics and comparison between two Brazilian soccer teams.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team1": {
                            "type": "string",
                            "description": "First team name"
                        },
                        "team2": {
                            "type": "string",
                            "description": "Second team name"
                        }
                    },
                    "required": ["team1", "team2"]
                }
            ),
            Tool(
                name="search_players",
                description="Search for soccer players from the FIFA database. Can filter by name, nationality, club, position, and rating.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Player name (partial match)"
                        },
                        "nationality": {
                            "type": "string",
                            "description": "Country name (e.g., Brazil)"
                        },
                        "club": {
                            "type": "string",
                            "description": "Club name"
                        },
                        "position": {
                            "type": "string",
                            "description": "Position: GK, CB, LB, RB, CDM, CM, CAM, LW, RW, ST, etc."
                        },
                        "min_overall": {
                            "type": "integer",
                            "description": "Minimum overall rating (0-99)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 20)"
                        }
                    }
                }
            ),
            Tool(
                name="get_standings",
                description="Get league standings for a specific season. Calculates points, wins, draws, losses, and goal difference.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "season": {
                            "type": "integer",
                            "description": "Season year (e.g., 2019)"
                        },
                        "competition": {
                            "type": "string",
                            "description": "Competition name (default: Brasileirão)"
                        }
                    },
                    "required": ["season"]
                }
            ),
            Tool(
                name="get_competition_stats",
                description="Get aggregate statistics for a competition including total matches, goals, home/away win rates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "competition": {
                            "type": "string",
                            "description": "Competition name: Brasileirão, Copa do Brasil, or Libertadores"
                        }
                    },
                    "required": ["competition"]
                }
            ),
            Tool(
                name="get_biggest_wins",
                description="Get matches with the largest goal differences (biggest victories).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of matches to return (default: 10)"
                        }
                    }
                }
            ),
            Tool(
                name="list_teams",
                description="List all teams in the database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of teams (default: 50)"
                        }
                    }
                }
            ),
            Tool(
                name="list_competitions",
                description="List all competitions and their match counts.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="list_seasons",
                description="List all seasons with data in the database.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls from the LLM."""

        try:
            if name == "search_matches":
                return await _handle_search_matches(match_queries, arguments)
            elif name == "get_team_stats":
                return await _handle_get_team_stats(team_queries, arguments)
            elif name == "compare_teams":
                return await _handle_compare_teams(team_queries, match_queries, arguments)
            elif name == "search_players":
                return await _handle_search_players(player_queries, arguments)
            elif name == "get_standings":
                return await _handle_get_standings(competition_queries, arguments)
            elif name == "get_competition_stats":
                return await _handle_get_competition_stats(competition_queries, arguments)
            elif name == "get_biggest_wins":
                return await _handle_get_biggest_wins(match_queries, arguments)
            elif name == "list_teams":
                return await _handle_list_teams(team_queries, arguments)
            elif name == "list_competitions":
                return await _handle_list_competitions(competition_queries)
            elif name == "list_seasons":
                return await _handle_list_seasons(competition_queries)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    return server


async def _handle_search_matches(
    queries: MatchQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle search_matches tool call."""
    team = args.get("team")
    team2 = args.get("team2")
    season = args.get("season")
    competition = args.get("competition")
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    limit = args.get("limit", 20)

    if team and team2:
        # Head-to-head matches
        matches = queries.find_matches_between_teams(team, team2, limit)
        header = f"Matches between {team} and {team2}:"
    elif team:
        # Single team matches
        matches = queries.find_team_matches(team, season, competition, limit)
        header = f"Matches for {team}:"
    elif start_date and end_date:
        # Date range search
        matches = queries.find_matches_by_date_range(start_date, end_date, competition, limit)
        header = f"Matches from {start_date} to {end_date}:"
    else:
        return [TextContent(type="text", text="Please specify a team or date range to search.")]

    if not matches:
        return [TextContent(type="text", text="No matches found matching the criteria.")]

    lines = [header, ""]
    for m in matches:
        date_str = m.datetime[:10] if m.datetime else "Unknown date"
        comp_str = f" ({m.competition})" if m.competition else ""
        round_str = f" Round {m.round}" if m.round else ""
        stage_str = f" {m.stage}" if m.stage else ""
        lines.append(
            f"- {date_str}: {m.home_team} {m.home_goals}-{m.away_goals} {m.away_team}{comp_str}{round_str}{stage_str}"
        )

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_get_team_stats(
    queries: TeamQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle get_team_stats tool call."""
    team = args.get("team")
    season = args.get("season")
    competition = args.get("competition")
    home_only = args.get("home_only", False)

    if not team:
        return [TextContent(type="text", text="Please specify a team name.")]

    if home_only:
        stats = queries.get_home_record(team, season)
    else:
        stats = queries.get_team_stats(team, season, competition)

    if not stats:
        return [TextContent(type="text", text=f"No statistics found for {team}.")]

    season_str = f" ({season})" if season else ""
    comp_str = f" in {competition}" if competition else ""

    lines = [
        f"Statistics for {stats.team}{season_str}{comp_str}:",
        "",
        f"Matches: {stats.matches}",
        f"Wins: {stats.wins}",
        f"Draws: {stats.draws}",
        f"Losses: {stats.losses}",
        f"Goals For: {stats.goals_for}",
        f"Goals Against: {stats.goals_against}",
        f"Goal Difference: {stats.goal_difference:+d}",
        f"Points: {stats.points}",
        f"Win Rate: {stats.wins / stats.matches * 100:.1f}%" if stats.matches > 0 else "Win Rate: N/A"
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_compare_teams(
    team_queries: TeamQueries,
    match_queries: MatchQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle compare_teams tool call."""
    team1 = args.get("team1")
    team2 = args.get("team2")

    if not team1 or not team2:
        return [TextContent(type="text", text="Please specify both team1 and team2.")]

    h2h = team_queries.get_head_to_head(team1, team2)
    recent_matches = match_queries.find_matches_between_teams(team1, team2, 5)

    lines = [
        f"Head-to-Head: {h2h['team1']} vs {h2h['team2']}",
        "",
        f"Total Matches: {h2h['total_matches']}",
        f"{h2h['team1']} Wins: {h2h['team1_wins']}",
        f"{h2h['team2']} Wins: {h2h['team2_wins']}",
        f"Draws: {h2h['draws']}",
        f"Total Goals - {h2h['team1']}: {h2h.get('team1_total_goals', 'N/A')}",
        f"Total Goals - {h2h['team2']}: {h2h.get('team2_total_goals', 'N/A')}",
        "",
        "Recent Matches:",
    ]

    for m in recent_matches:
        date_str = m.datetime[:10] if m.datetime else "Unknown"
        lines.append(f"- {date_str}: {m.home_team} {m.home_goals}-{m.away_goals} {m.away_team}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_search_players(
    queries: PlayerQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle search_players tool call."""
    name = args.get("name")
    nationality = args.get("nationality")
    club = args.get("club")
    position = args.get("position")
    min_overall = args.get("min_overall")
    limit = args.get("limit", 20)

    players = queries.search_players(name, nationality, club, position, min_overall, limit)

    if not players:
        return [TextContent(type="text", text="No players found matching the criteria.")]

    # Build header based on search criteria
    criteria = []
    if nationality:
        criteria.append(f"from {nationality}")
    if club:
        criteria.append(f"at {club}")
    if position:
        criteria.append(f"playing {position}")
    if min_overall:
        criteria.append(f"rated {min_overall}+")

    header = "Players" + (" " + ", ".join(criteria) if criteria else "") + ":"

    lines = [header, ""]
    for i, p in enumerate(players, 1):
        rating = f"Overall: {p.overall}" if p.overall else ""
        club_str = f", Club: {p.club}" if p.club else ""
        pos_str = f", Position: {p.position}" if p.position else ""
        lines.append(f"{i}. {p.name} - {p.nationality}{pos_str}{club_str} ({rating})")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_get_standings(
    queries: CompetitionQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle get_standings tool call."""
    season = args.get("season")
    competition = args.get("competition", "Brasileirão")

    if not season:
        return [TextContent(type="text", text="Please specify a season year.")]

    standings = queries.get_season_standings(season, competition)

    if not standings:
        return [TextContent(type="text", text=f"No standings data found for {competition} {season}.")]

    lines = [f"{competition} {season} Standings:", "", "Pos | Team | P | W | D | L | GF | GA | GD | Pts"]
    lines.append("-" * 60)

    for i, s in enumerate(standings[:20], 1):
        lines.append(
            f"{i:3} | {s.team[:15]:15} | {s.matches:2} | {s.wins:2} | {s.draws:2} | {s.losses:2} | "
            f"{s.goals_for:3} | {s.goals_against:3} | {s.goal_difference:+3} | {s.points:3}"
        )

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_get_competition_stats(
    queries: CompetitionQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle get_competition_stats tool call."""
    competition = args.get("competition")

    if not competition:
        return [TextContent(type="text", text="Please specify a competition name.")]

    stats = queries.get_competition_stats(competition)

    lines = [
        f"Statistics for {stats['competition']}:",
        "",
        f"Total Matches: {stats['total_matches']}",
        f"Total Goals: {stats['total_goals']}",
        f"Average Goals per Match: {stats['avg_goals_per_match']}",
        f"Home Wins: {stats['home_wins']} ({stats['home_win_rate']}%)",
        f"Away Wins: {stats['away_wins']} ({stats['away_win_rate']}%)",
        f"Draws: {stats['draws']} ({stats['draw_rate']}%)"
    ]

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_get_biggest_wins(
    queries: MatchQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle get_biggest_wins tool call."""
    limit = args.get("limit", 10)
    matches = queries.get_biggest_wins(limit)

    if not matches:
        return [TextContent(type="text", text="No match data found.")]

    lines = ["Biggest Victories:", ""]
    for i, m in enumerate(matches, 1):
        date_str = m.datetime[:10] if m.datetime else "Unknown"
        diff = abs(m.home_goals - m.away_goals)
        winner = m.home_team if m.home_goals > m.away_goals else m.away_team
        lines.append(
            f"{i}. {date_str}: {m.home_team} {m.home_goals}-{m.away_goals} {m.away_team} "
            f"({winner} wins by {diff})"
        )

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_list_teams(
    queries: TeamQueries,
    args: Dict[str, Any]
) -> List[TextContent]:
    """Handle list_teams tool call."""
    limit = args.get("limit", 50)
    teams = queries.list_teams(limit)

    if not teams:
        return [TextContent(type="text", text="No teams found in database.")]

    lines = [f"Teams in database ({len(teams)} shown):", ""]
    for team in teams:
        lines.append(f"- {team}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_list_competitions(
    queries: CompetitionQueries
) -> List[TextContent]:
    """Handle list_competitions tool call."""
    competitions = queries.list_competitions()

    if not competitions:
        return [TextContent(type="text", text="No competitions found.")]

    lines = ["Competitions:", ""]
    for c in competitions:
        lines.append(f"- {c['name']} ({c['type']}): {c['match_count']} matches")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_list_seasons(
    queries: CompetitionQueries
) -> List[TextContent]:
    """Handle list_seasons tool call."""
    seasons = queries.list_seasons()

    if not seasons:
        return [TextContent(type="text", text="No season data found.")]

    lines = ["Seasons with data:", ""]
    lines.append(", ".join(str(s) for s in seasons))

    return [TextContent(type="text", text="\n".join(lines))]


async def run_server(connection: Optional[Neo4jConnection] = None) -> None:
    """
    Run the MCP server using stdio transport.

    Args:
        connection: Optional Neo4j connection
    """
    server = create_server(connection)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Entry point for running the server from command line."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
