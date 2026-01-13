"""
=============================================================================
File: src/brazilian_soccer_mcp/queries.py
Project: Brazilian Soccer MCP Server
Purpose: Query functions for retrieving soccer data from Neo4j
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Provides high-level query interfaces for the MCP server tools. Each query
    class handles a specific domain (matches, teams, players, competitions)
    and returns formatted results suitable for natural language responses.

Query Classes:
    - MatchQueries: Find matches by teams, date, competition
    - TeamQueries: Team statistics, head-to-head records
    - PlayerQueries: Player search by name, nationality, club
    - CompetitionQueries: Standings, season data

Performance Notes:
    - All queries use indexed fields for efficient lookups
    - Result limits are applied to prevent memory issues
    - Aggregations are performed in Cypher for efficiency
=============================================================================
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .db import Neo4jConnection, get_connection
from .data_loader import DataLoader


@dataclass
class MatchResult:
    """Structured match result for consistent formatting."""
    datetime: Optional[str]
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    competition: str
    round: Optional[str] = None
    stage: Optional[str] = None
    season: Optional[int] = None


@dataclass
class TeamStats:
    """Team statistics summary."""
    team: str
    matches: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


@dataclass
class PlayerInfo:
    """Player information summary."""
    name: str
    nationality: str
    club: Optional[str]
    position: Optional[str]
    overall: Optional[int]
    potential: Optional[int]
    age: Optional[int]


class MatchQueries:
    """
    Query interface for match data.

    Provides methods to search and retrieve match information from the
    Neo4j graph database.
    """

    def __init__(self, connection: Optional[Neo4jConnection] = None):
        """Initialize with database connection."""
        self.connection = connection or get_connection()
        self._loader = DataLoader(self.connection)

    def _normalize_team(self, name: str) -> str:
        """Normalize team name for consistent querying."""
        return self._loader.normalize_team_name(name)

    def find_matches_between_teams(
        self,
        team1: str,
        team2: str,
        limit: int = 50
    ) -> List[MatchResult]:
        """
        Find all matches between two teams.

        Args:
            team1: First team name
            team2: Second team name
            limit: Maximum results to return

        Returns:
            List of MatchResult objects
        """
        t1 = self._normalize_team(team1)
        t2 = self._normalize_team(team2)

        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        WHERE (home.normalized_name = $team1 AND away.normalized_name = $team2)
           OR (home.normalized_name = $team2 AND away.normalized_name = $team1)
        OPTIONAL MATCH (m)-[:IN_SEASON]->(s:Season)
        RETURN m.datetime as datetime,
               home.normalized_name as home_team,
               away.normalized_name as away_team,
               m.home_goals as home_goals,
               m.away_goals as away_goals,
               m.competition as competition,
               m.round as round,
               m.stage as stage,
               s.year as season
        ORDER BY m.datetime DESC
        LIMIT $limit
        """
        results = self.connection.execute_query(query, {
            "team1": t1,
            "team2": t2,
            "limit": limit
        })

        return [
            MatchResult(
                datetime=r.get("datetime"),
                home_team=r.get("home_team", ""),
                away_team=r.get("away_team", ""),
                home_goals=r.get("home_goals", 0),
                away_goals=r.get("away_goals", 0),
                competition=r.get("competition", ""),
                round=r.get("round"),
                stage=r.get("stage"),
                season=r.get("season")
            )
            for r in results
        ]

    def find_team_matches(
        self,
        team: str,
        season: Optional[int] = None,
        competition: Optional[str] = None,
        limit: int = 50
    ) -> List[MatchResult]:
        """
        Find all matches for a specific team.

        Args:
            team: Team name
            season: Filter by season year (optional)
            competition: Filter by competition name (optional)
            limit: Maximum results to return

        Returns:
            List of MatchResult objects
        """
        t = self._normalize_team(team)

        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        WHERE home.normalized_name = $team OR away.normalized_name = $team
        """

        params: Dict[str, Any] = {"team": t, "limit": limit}

        if season:
            query += """
            MATCH (m)-[:IN_SEASON]->(s:Season {year: $season})
            """
            params["season"] = season

        if competition:
            query += """
            AND m.competition CONTAINS $competition
            """
            params["competition"] = competition

        query += """
        OPTIONAL MATCH (m)-[:IN_SEASON]->(s:Season)
        RETURN m.datetime as datetime,
               home.normalized_name as home_team,
               away.normalized_name as away_team,
               m.home_goals as home_goals,
               m.away_goals as away_goals,
               m.competition as competition,
               m.round as round,
               m.stage as stage,
               s.year as season
        ORDER BY m.datetime DESC
        LIMIT $limit
        """

        results = self.connection.execute_query(query, params)

        return [
            MatchResult(
                datetime=r.get("datetime"),
                home_team=r.get("home_team", ""),
                away_team=r.get("away_team", ""),
                home_goals=r.get("home_goals", 0),
                away_goals=r.get("away_goals", 0),
                competition=r.get("competition", ""),
                round=r.get("round"),
                stage=r.get("stage"),
                season=r.get("season")
            )
            for r in results
        ]

    def find_matches_by_date_range(
        self,
        start_date: str,
        end_date: str,
        competition: Optional[str] = None,
        limit: int = 100
    ) -> List[MatchResult]:
        """
        Find matches within a date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            competition: Filter by competition (optional)
            limit: Maximum results

        Returns:
            List of MatchResult objects
        """
        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        WHERE m.datetime >= $start_date AND m.datetime <= $end_date
        """

        params: Dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }

        if competition:
            query += " AND m.competition CONTAINS $competition"
            params["competition"] = competition

        query += """
        OPTIONAL MATCH (m)-[:IN_SEASON]->(s:Season)
        RETURN m.datetime as datetime,
               home.normalized_name as home_team,
               away.normalized_name as away_team,
               m.home_goals as home_goals,
               m.away_goals as away_goals,
               m.competition as competition,
               m.round as round,
               m.stage as stage,
               s.year as season
        ORDER BY m.datetime
        LIMIT $limit
        """

        results = self.connection.execute_query(query, params)

        return [
            MatchResult(
                datetime=r.get("datetime"),
                home_team=r.get("home_team", ""),
                away_team=r.get("away_team", ""),
                home_goals=r.get("home_goals", 0),
                away_goals=r.get("away_goals", 0),
                competition=r.get("competition", ""),
                round=r.get("round"),
                stage=r.get("stage"),
                season=r.get("season")
            )
            for r in results
        ]

    def get_biggest_wins(self, limit: int = 10) -> List[MatchResult]:
        """
        Get matches with largest goal differences.

        Args:
            limit: Number of matches to return

        Returns:
            List of MatchResult objects sorted by goal difference
        """
        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        OPTIONAL MATCH (m)-[:IN_SEASON]->(s:Season)
        WITH m, home, away, s, abs(m.home_goals - m.away_goals) as goal_diff
        WHERE goal_diff > 0
        RETURN m.datetime as datetime,
               home.normalized_name as home_team,
               away.normalized_name as away_team,
               m.home_goals as home_goals,
               m.away_goals as away_goals,
               m.competition as competition,
               m.round as round,
               m.stage as stage,
               s.year as season
        ORDER BY goal_diff DESC
        LIMIT $limit
        """

        results = self.connection.execute_query(query, {"limit": limit})

        return [
            MatchResult(
                datetime=r.get("datetime"),
                home_team=r.get("home_team", ""),
                away_team=r.get("away_team", ""),
                home_goals=r.get("home_goals", 0),
                away_goals=r.get("away_goals", 0),
                competition=r.get("competition", ""),
                round=r.get("round"),
                stage=r.get("stage"),
                season=r.get("season")
            )
            for r in results
        ]


class TeamQueries:
    """
    Query interface for team statistics.

    Provides methods to calculate team performance metrics and
    head-to-head records.
    """

    def __init__(self, connection: Optional[Neo4jConnection] = None):
        """Initialize with database connection."""
        self.connection = connection or get_connection()
        self._loader = DataLoader(self.connection)

    def _normalize_team(self, name: str) -> str:
        """Normalize team name for consistent querying."""
        return self._loader.normalize_team_name(name)

    def get_team_stats(
        self,
        team: str,
        season: Optional[int] = None,
        competition: Optional[str] = None
    ) -> Optional[TeamStats]:
        """
        Calculate comprehensive statistics for a team.

        Args:
            team: Team name
            season: Filter by season (optional)
            competition: Filter by competition (optional)

        Returns:
            TeamStats object or None if no matches found
        """
        t = self._normalize_team(team)

        # Build query with optional filters
        where_clauses = ["(home.normalized_name = $team OR away.normalized_name = $team)"]
        params: Dict[str, Any] = {"team": t}

        if competition:
            where_clauses.append("m.competition CONTAINS $competition")
            params["competition"] = competition

        season_match = ""
        if season:
            season_match = "MATCH (m)-[:IN_SEASON]->(s:Season {year: $season})"
            params["season"] = season

        query = f"""
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        {season_match}
        WHERE {' AND '.join(where_clauses)}
        WITH m, home, away,
             CASE WHEN home.normalized_name = $team THEN 'home' ELSE 'away' END as position,
             CASE WHEN home.normalized_name = $team THEN m.home_goals ELSE m.away_goals END as goals_for,
             CASE WHEN home.normalized_name = $team THEN m.away_goals ELSE m.home_goals END as goals_against
        RETURN count(m) as matches,
               sum(CASE WHEN goals_for > goals_against THEN 1 ELSE 0 END) as wins,
               sum(CASE WHEN goals_for = goals_against THEN 1 ELSE 0 END) as draws,
               sum(CASE WHEN goals_for < goals_against THEN 1 ELSE 0 END) as losses,
               sum(goals_for) as goals_for,
               sum(goals_against) as goals_against
        """

        results = self.connection.execute_query(query, params)

        if not results or results[0].get("matches", 0) == 0:
            return None

        r = results[0]
        wins = r.get("wins", 0)
        draws = r.get("draws", 0)
        goals_for = r.get("goals_for", 0)
        goals_against = r.get("goals_against", 0)

        return TeamStats(
            team=t,
            matches=r.get("matches", 0),
            wins=wins,
            draws=draws,
            losses=r.get("losses", 0),
            goals_for=goals_for,
            goals_against=goals_against,
            goal_difference=goals_for - goals_against,
            points=wins * 3 + draws
        )

    def get_home_record(
        self,
        team: str,
        season: Optional[int] = None
    ) -> Optional[TeamStats]:
        """
        Get team's home record only.

        Args:
            team: Team name
            season: Filter by season (optional)

        Returns:
            TeamStats for home matches only
        """
        t = self._normalize_team(team)
        params: Dict[str, Any] = {"team": t}

        season_match = ""
        if season:
            season_match = "MATCH (m)-[:IN_SEASON]->(s:Season {year: $season})"
            params["season"] = season

        query = f"""
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team {{normalized_name: $team}})
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        {season_match}
        RETURN count(m) as matches,
               sum(CASE WHEN m.home_goals > m.away_goals THEN 1 ELSE 0 END) as wins,
               sum(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) as draws,
               sum(CASE WHEN m.home_goals < m.away_goals THEN 1 ELSE 0 END) as losses,
               sum(m.home_goals) as goals_for,
               sum(m.away_goals) as goals_against
        """

        results = self.connection.execute_query(query, params)

        if not results or results[0].get("matches", 0) == 0:
            return None

        r = results[0]
        wins = r.get("wins", 0)
        draws = r.get("draws", 0)
        goals_for = r.get("goals_for", 0)
        goals_against = r.get("goals_against", 0)

        return TeamStats(
            team=f"{t} (home)",
            matches=r.get("matches", 0),
            wins=wins,
            draws=draws,
            losses=r.get("losses", 0),
            goals_for=goals_for,
            goals_against=goals_against,
            goal_difference=goals_for - goals_against,
            points=wins * 3 + draws
        )

    def get_head_to_head(self, team1: str, team2: str) -> Dict[str, Any]:
        """
        Calculate head-to-head record between two teams.

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            Dictionary with head-to-head statistics
        """
        t1 = self._normalize_team(team1)
        t2 = self._normalize_team(team2)

        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        WHERE (home.normalized_name = $team1 AND away.normalized_name = $team2)
           OR (home.normalized_name = $team2 AND away.normalized_name = $team1)
        WITH m, home, away,
             CASE
               WHEN home.home_goals > away.away_goals THEN home.normalized_name
               WHEN away.away_goals > home.home_goals THEN away.normalized_name
               ELSE 'draw'
             END as winner,
             CASE
               WHEN home.normalized_name = $team1 THEN m.home_goals
               ELSE m.away_goals
             END as team1_goals,
             CASE
               WHEN home.normalized_name = $team2 THEN m.home_goals
               ELSE m.away_goals
             END as team2_goals
        RETURN count(m) as total_matches,
               sum(CASE WHEN m.home_goals > m.away_goals AND home.normalized_name = $team1 THEN 1
                        WHEN m.away_goals > m.home_goals AND away.normalized_name = $team1 THEN 1
                        ELSE 0 END) as team1_wins,
               sum(CASE WHEN m.home_goals > m.away_goals AND home.normalized_name = $team2 THEN 1
                        WHEN m.away_goals > m.home_goals AND away.normalized_name = $team2 THEN 1
                        ELSE 0 END) as team2_wins,
               sum(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) as draws,
               sum(team1_goals) as team1_total_goals,
               sum(team2_goals) as team2_total_goals
        """

        results = self.connection.execute_query(query, {"team1": t1, "team2": t2})

        if not results:
            return {
                "team1": t1,
                "team2": t2,
                "total_matches": 0,
                "team1_wins": 0,
                "team2_wins": 0,
                "draws": 0
            }

        r = results[0]
        return {
            "team1": t1,
            "team2": t2,
            "total_matches": r.get("total_matches", 0),
            "team1_wins": r.get("team1_wins", 0),
            "team2_wins": r.get("team2_wins", 0),
            "draws": r.get("draws", 0),
            "team1_total_goals": r.get("team1_total_goals", 0),
            "team2_total_goals": r.get("team2_total_goals", 0)
        }

    def list_teams(self, limit: int = 100) -> List[str]:
        """
        List all teams in the database.

        Args:
            limit: Maximum number of teams to return

        Returns:
            List of team names
        """
        query = """
        MATCH (t:Team)
        RETURN t.normalized_name as name
        ORDER BY name
        LIMIT $limit
        """
        results = self.connection.execute_query(query, {"limit": limit})
        return [r.get("name", "") for r in results if r.get("name")]


class PlayerQueries:
    """
    Query interface for player data.

    Provides methods to search and retrieve player information from
    the FIFA player database.
    """

    def __init__(self, connection: Optional[Neo4jConnection] = None):
        """Initialize with database connection."""
        self.connection = connection or get_connection()

    def search_players(
        self,
        name: Optional[str] = None,
        nationality: Optional[str] = None,
        club: Optional[str] = None,
        position: Optional[str] = None,
        min_overall: Optional[int] = None,
        limit: int = 50
    ) -> List[PlayerInfo]:
        """
        Search for players matching criteria.

        Args:
            name: Player name (partial match)
            nationality: Country name
            club: Club name
            position: Playing position
            min_overall: Minimum overall rating
            limit: Maximum results

        Returns:
            List of PlayerInfo objects
        """
        where_clauses = []
        params: Dict[str, Any] = {"limit": limit}

        if name:
            where_clauses.append("toLower(p.name) CONTAINS toLower($name)")
            params["name"] = name

        if nationality:
            where_clauses.append("toLower(p.nationality) CONTAINS toLower($nationality)")
            params["nationality"] = nationality

        if club:
            where_clauses.append("toLower(p.club) CONTAINS toLower($club)")
            params["club"] = club

        if position:
            where_clauses.append("p.position CONTAINS $position")
            params["position"] = position

        if min_overall:
            where_clauses.append("p.overall >= $min_overall")
            params["min_overall"] = min_overall

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
        MATCH (p:Player)
        WHERE {where_clause}
        RETURN p.name as name,
               p.nationality as nationality,
               p.club as club,
               p.position as position,
               p.overall as overall,
               p.potential as potential,
               p.age as age
        ORDER BY p.overall DESC
        LIMIT $limit
        """

        results = self.connection.execute_query(query, params)

        return [
            PlayerInfo(
                name=r.get("name", ""),
                nationality=r.get("nationality", ""),
                club=r.get("club"),
                position=r.get("position"),
                overall=r.get("overall"),
                potential=r.get("potential"),
                age=r.get("age")
            )
            for r in results
        ]

    def get_top_players(
        self,
        nationality: Optional[str] = None,
        limit: int = 20
    ) -> List[PlayerInfo]:
        """
        Get top-rated players, optionally filtered by nationality.

        Args:
            nationality: Filter by country (optional)
            limit: Number of players to return

        Returns:
            List of top players sorted by overall rating
        """
        if nationality:
            return self.search_players(
                nationality=nationality,
                min_overall=70,
                limit=limit
            )
        else:
            return self.search_players(min_overall=80, limit=limit)

    def get_brazilian_players(self, limit: int = 50) -> List[PlayerInfo]:
        """
        Get all Brazilian players in the database.

        Args:
            limit: Maximum number of players

        Returns:
            List of Brazilian players
        """
        return self.search_players(nationality="Brazil", limit=limit)

    def get_players_by_club(self, club: str, limit: int = 30) -> List[PlayerInfo]:
        """
        Get all players for a specific club.

        Args:
            club: Club name
            limit: Maximum number of players

        Returns:
            List of players at the club
        """
        return self.search_players(club=club, limit=limit)


class CompetitionQueries:
    """
    Query interface for competition data.

    Provides methods to retrieve competition standings, statistics,
    and season information.
    """

    def __init__(self, connection: Optional[Neo4jConnection] = None):
        """Initialize with database connection."""
        self.connection = connection or get_connection()
        self._loader = DataLoader(self.connection)

    def get_season_standings(
        self,
        season: int,
        competition: str = "Brasileirão"
    ) -> List[TeamStats]:
        """
        Calculate league standings for a season.

        Args:
            season: Season year
            competition: Competition name

        Returns:
            List of TeamStats sorted by points
        """
        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        MATCH (m)-[:IN_SEASON]->(s:Season {year: $season})
        WHERE m.competition CONTAINS $competition
        WITH home, away, m
        UNWIND [
            {team: home.normalized_name, gf: m.home_goals, ga: m.away_goals},
            {team: away.normalized_name, gf: m.away_goals, ga: m.home_goals}
        ] as match_data
        WITH match_data.team as team,
             match_data.gf as gf,
             match_data.ga as ga,
             CASE WHEN match_data.gf > match_data.ga THEN 3
                  WHEN match_data.gf = match_data.ga THEN 1
                  ELSE 0 END as points,
             CASE WHEN match_data.gf > match_data.ga THEN 1 ELSE 0 END as win,
             CASE WHEN match_data.gf = match_data.ga THEN 1 ELSE 0 END as draw,
             CASE WHEN match_data.gf < match_data.ga THEN 1 ELSE 0 END as loss
        RETURN team,
               count(*) as matches,
               sum(win) as wins,
               sum(draw) as draws,
               sum(loss) as losses,
               sum(gf) as goals_for,
               sum(ga) as goals_against,
               sum(gf) - sum(ga) as goal_difference,
               sum(points) as points
        ORDER BY points DESC, goal_difference DESC, goals_for DESC
        """

        results = self.connection.execute_query(query, {
            "season": season,
            "competition": competition
        })

        return [
            TeamStats(
                team=r.get("team", ""),
                matches=r.get("matches", 0),
                wins=r.get("wins", 0),
                draws=r.get("draws", 0),
                losses=r.get("losses", 0),
                goals_for=r.get("goals_for", 0),
                goals_against=r.get("goals_against", 0),
                goal_difference=r.get("goal_difference", 0),
                points=r.get("points", 0)
            )
            for r in results
        ]

    def get_competition_stats(self, competition: str) -> Dict[str, Any]:
        """
        Get aggregate statistics for a competition.

        Args:
            competition: Competition name

        Returns:
            Dictionary with competition statistics
        """
        query = """
        MATCH (m:Match)-[:HOME_TEAM]->(home:Team)
        MATCH (m)-[:AWAY_TEAM]->(away:Team)
        WHERE m.competition CONTAINS $competition
        RETURN count(m) as total_matches,
               sum(m.home_goals + m.away_goals) as total_goals,
               avg(m.home_goals + m.away_goals) as avg_goals_per_match,
               sum(CASE WHEN m.home_goals > m.away_goals THEN 1 ELSE 0 END) as home_wins,
               sum(CASE WHEN m.away_goals > m.home_goals THEN 1 ELSE 0 END) as away_wins,
               sum(CASE WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END) as draws
        """

        results = self.connection.execute_query(query, {"competition": competition})

        if not results:
            return {"competition": competition, "total_matches": 0}

        r = results[0]
        total = r.get("total_matches", 0)

        return {
            "competition": competition,
            "total_matches": total,
            "total_goals": r.get("total_goals", 0),
            "avg_goals_per_match": round(r.get("avg_goals_per_match", 0), 2),
            "home_wins": r.get("home_wins", 0),
            "away_wins": r.get("away_wins", 0),
            "draws": r.get("draws", 0),
            "home_win_rate": round(r.get("home_wins", 0) / total * 100, 1) if total > 0 else 0,
            "away_win_rate": round(r.get("away_wins", 0) / total * 100, 1) if total > 0 else 0,
            "draw_rate": round(r.get("draws", 0) / total * 100, 1) if total > 0 else 0
        }

    def list_seasons(self) -> List[int]:
        """
        List all seasons in the database.

        Returns:
            List of season years, sorted descending
        """
        query = """
        MATCH (s:Season)
        RETURN s.year as year
        ORDER BY year DESC
        """
        results = self.connection.execute_query(query, {})
        return [r.get("year") for r in results if r.get("year")]

    def list_competitions(self) -> List[Dict[str, Any]]:
        """
        List all competitions in the database.

        Returns:
            List of competition info dictionaries
        """
        query = """
        MATCH (c:Competition)
        OPTIONAL MATCH (m:Match)-[:PART_OF]->(c)
        RETURN c.name as name, c.type as type, count(m) as match_count
        ORDER BY match_count DESC
        """
        results = self.connection.execute_query(query, {})
        return [
            {
                "name": r.get("name", ""),
                "type": r.get("type", ""),
                "match_count": r.get("match_count", 0)
            }
            for r in results
        ]
