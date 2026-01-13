"""
=============================================================================
File: src/brazilian_soccer_mcp/data_loader.py
Project: Brazilian Soccer MCP Server
Purpose: Load CSV data files into Neo4j graph database
Author: Gas Town Agent
Created: 2026-01-13

Description:
    Handles loading and transformation of Brazilian soccer data from CSV files
    into a Neo4j knowledge graph. Manages team name normalization, date parsing,
    and entity deduplication.

Data Files Processed:
    1. Brasileirao_Matches.csv - Serie A matches with state suffixes
    2. Brazilian_Cup_Matches.csv - Copa do Brasil knockout matches
    3. Libertadores_Matches.csv - Copa Libertadores with stages
    4. BR-Football-Dataset.csv - Extended stats (corners, shots, attacks)
    5. novo_campeonato_brasileiro.csv - Historical 2003-2019 with stadiums
    6. fifa_data.csv - FIFA player database with ratings

Graph Schema Created:
    Nodes:
        - (:Team {name, normalized_name, state})
        - (:Player {name, age, nationality, overall, potential, position, ...})
        - (:Match {datetime, home_goals, away_goals, round, stage})
        - (:Competition {name, type})
        - (:Season {year})

    Relationships:
        - (Match)-[:HOME_TEAM]->(Team)
        - (Match)-[:AWAY_TEAM]->(Team)
        - (Match)-[:PART_OF]->(Competition)
        - (Match)-[:IN_SEASON]->(Season)
        - (Player)-[:PLAYS_FOR]->(Team)

Team Name Normalization:
    Handles variations like:
    - "Palmeiras-SP" -> "Palmeiras"
    - "Sport Club Corinthians Paulista" -> "Corinthians"
    - "Flamengo-RJ" -> "Flamengo"
=============================================================================
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import pandas as pd

from .db import Neo4jConnection, get_connection


def safe_int(value: Union[str, int, float, None], default: int = 0) -> int:
    """
    Safely convert a value to integer, handling edge cases.

    Args:
        value: Value to convert (may be string, int, float, None, or invalid)
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    if value is None or pd.isna(value):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-", "N/A", "n/a", "null", "None"):
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    return default


# Team name normalization mapping
TEAM_ALIASES: Dict[str, str] = {
    "Sport Club Corinthians Paulista": "Corinthians",
    "Sociedade Esportiva Palmeiras": "Palmeiras",
    "São Paulo Futebol Clube": "São Paulo",
    "Santos Futebol Clube": "Santos",
    "Clube de Regatas do Flamengo": "Flamengo",
    "Fluminense Football Club": "Fluminense",
    "Botafogo de Futebol e Regatas": "Botafogo",
    "Club de Regatas Vasco da Gama": "Vasco",
    "Grêmio Foot-Ball Porto Alegrense": "Grêmio",
    "Sport Club Internacional": "Internacional",
    "Clube Atlético Mineiro": "Atlético-MG",
    "Cruzeiro Esporte Clube": "Cruzeiro",
    "Athletico Paranaense": "Athletico-PR",
    "Coritiba Foot Ball Club": "Coritiba",
}


class DataLoader:
    """
    Loads Brazilian soccer CSV data into Neo4j graph database.

    Attributes:
        connection: Neo4j database connection
        data_dir: Path to directory containing CSV files
        teams_cache: Set of already-created team names for deduplication
    """

    def __init__(
        self,
        connection: Optional[Neo4jConnection] = None,
        data_dir: Optional[str] = None
    ):
        """
        Initialize the data loader.

        Args:
            connection: Neo4j connection (uses default if None)
            data_dir: Path to data directory (defaults to data/kaggle/)
        """
        self.connection = connection or get_connection()
        self.data_dir = Path(data_dir) if data_dir else Path("data/kaggle")
        self.teams_cache: Set[str] = set()
        self.competitions_cache: Set[str] = set()

    def normalize_team_name(self, name: str) -> str:
        """
        Normalize team name by removing state suffix and applying aliases.

        Args:
            name: Raw team name from CSV

        Returns:
            Normalized team name

        Examples:
            >>> loader.normalize_team_name("Palmeiras-SP")
            'Palmeiras'
            >>> loader.normalize_team_name("Sport Club Corinthians Paulista")
            'Corinthians'
        """
        if not name or pd.isna(name):
            return ""

        name = str(name).strip()

        # Check aliases first
        if name in TEAM_ALIASES:
            return TEAM_ALIASES[name]

        # Remove state suffix (e.g., "Palmeiras-SP" -> "Palmeiras")
        match = re.match(r"^(.+?)-[A-Z]{2}$", name)
        if match:
            name = match.group(1)

        # Check aliases again after suffix removal
        if name in TEAM_ALIASES:
            return TEAM_ALIASES[name]

        return name

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string handling multiple formats.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None if parsing fails

        Supported formats:
            - ISO: "2023-09-24"
            - ISO with time: "2012-05-19 18:30:00"
            - Brazilian: "29/03/2003"
        """
        if not date_str or pd.isna(date_str):
            return None

        date_str = str(date_str).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def clear_database(self) -> None:
        """Remove all nodes and relationships from the database."""
        self.connection.execute_write("MATCH (n) DETACH DELETE n")
        self.teams_cache.clear()
        self.competitions_cache.clear()

    def create_indexes(self) -> None:
        """Create indexes for efficient querying."""
        indexes = [
            "CREATE INDEX team_name IF NOT EXISTS FOR (t:Team) ON (t.name)",
            "CREATE INDEX team_normalized IF NOT EXISTS FOR (t:Team) ON (t.normalized_name)",
            "CREATE INDEX player_name IF NOT EXISTS FOR (p:Player) ON (p.name)",
            "CREATE INDEX player_nationality IF NOT EXISTS FOR (p:Player) ON (p.nationality)",
            "CREATE INDEX match_datetime IF NOT EXISTS FOR (m:Match) ON (m.datetime)",
            "CREATE INDEX competition_name IF NOT EXISTS FOR (c:Competition) ON (c.name)",
            "CREATE INDEX season_year IF NOT EXISTS FOR (s:Season) ON (s.year)",
        ]
        for index_query in indexes:
            try:
                self.connection.execute_write(index_query)
            except Exception:
                # Index may already exist
                pass

    def _ensure_team(self, name: str, state: Optional[str] = None) -> str:
        """Create team node if it doesn't exist, return normalized name."""
        normalized = self.normalize_team_name(name)
        if not normalized:
            return ""

        if normalized not in self.teams_cache:
            query = """
            MERGE (t:Team {normalized_name: $normalized})
            ON CREATE SET t.name = $name, t.state = $state
            """
            self.connection.execute_write(query, {
                "normalized": normalized,
                "name": name,
                "state": state
            })
            self.teams_cache.add(normalized)

        return normalized

    def _ensure_competition(self, name: str, comp_type: str = "league") -> None:
        """Create competition node if it doesn't exist."""
        if name not in self.competitions_cache:
            query = """
            MERGE (c:Competition {name: $name})
            ON CREATE SET c.type = $type
            """
            self.connection.execute_write(query, {"name": name, "type": comp_type})
            self.competitions_cache.add(name)

    def _ensure_season(self, year: int) -> None:
        """Create season node if it doesn't exist."""
        query = "MERGE (s:Season {year: $year})"
        self.connection.execute_write(query, {"year": year})

    def load_brasileirao_matches(self) -> int:
        """
        Load Brasileirao Serie A matches from CSV.

        Returns:
            Number of matches loaded
        """
        filepath = self.data_dir / "Brasileirao_Matches.csv"
        if not filepath.exists():
            return 0

        df = pd.read_csv(filepath, encoding="utf-8")
        count = 0

        self._ensure_competition("Brasileirão Série A", "league")

        for _, row in df.iterrows():
            home_team = self._ensure_team(
                row.get("home_team", ""),
                row.get("home_team_state")
            )
            away_team = self._ensure_team(
                row.get("away_team", ""),
                row.get("away_team_state")
            )

            if not home_team or not away_team:
                continue

            match_date = self.parse_date(row.get("datetime"))
            season = safe_int(row.get("season")) or None

            if season:
                self._ensure_season(season)

            query = """
            MATCH (home:Team {normalized_name: $home_team})
            MATCH (away:Team {normalized_name: $away_team})
            MATCH (comp:Competition {name: 'Brasileirão Série A'})
            CREATE (m:Match {
                datetime: $datetime,
                home_goals: $home_goals,
                away_goals: $away_goals,
                round: $round,
                competition: 'Brasileirão Série A'
            })
            CREATE (m)-[:HOME_TEAM]->(home)
            CREATE (m)-[:AWAY_TEAM]->(away)
            CREATE (m)-[:PART_OF]->(comp)
            """
            params = {
                "home_team": home_team,
                "away_team": away_team,
                "datetime": match_date.isoformat() if match_date else None,
                "home_goals": safe_int(row.get("home_goal")),
                "away_goals": safe_int(row.get("away_goal")),
                "round": safe_int(row.get("round")) or None,
            }

            if season:
                query += """
                WITH m
                MATCH (s:Season {year: $season})
                CREATE (m)-[:IN_SEASON]->(s)
                """
                params["season"] = season

            self.connection.execute_write(query, params)
            count += 1

        return count

    def load_copa_brasil_matches(self) -> int:
        """
        Load Copa do Brasil matches from CSV.

        Returns:
            Number of matches loaded
        """
        filepath = self.data_dir / "Brazilian_Cup_Matches.csv"
        if not filepath.exists():
            return 0

        df = pd.read_csv(filepath, encoding="utf-8")
        count = 0

        self._ensure_competition("Copa do Brasil", "cup")

        for _, row in df.iterrows():
            home_team = self._ensure_team(row.get("home_team", ""))
            away_team = self._ensure_team(row.get("away_team", ""))

            if not home_team or not away_team:
                continue

            match_date = self.parse_date(row.get("datetime"))
            season = safe_int(row.get("season")) or None

            if season:
                self._ensure_season(season)

            query = """
            MATCH (home:Team {normalized_name: $home_team})
            MATCH (away:Team {normalized_name: $away_team})
            MATCH (comp:Competition {name: 'Copa do Brasil'})
            CREATE (m:Match {
                datetime: $datetime,
                home_goals: $home_goals,
                away_goals: $away_goals,
                round: $round,
                competition: 'Copa do Brasil'
            })
            CREATE (m)-[:HOME_TEAM]->(home)
            CREATE (m)-[:AWAY_TEAM]->(away)
            CREATE (m)-[:PART_OF]->(comp)
            """
            params = {
                "home_team": home_team,
                "away_team": away_team,
                "datetime": match_date.isoformat() if match_date else None,
                "home_goals": safe_int(row.get("home_goal")),
                "away_goals": safe_int(row.get("away_goal")),
                "round": str(row.get("round", "")) if pd.notna(row.get("round")) else None,
            }

            if season:
                query += """
                WITH m
                MATCH (s:Season {year: $season})
                CREATE (m)-[:IN_SEASON]->(s)
                """
                params["season"] = season

            self.connection.execute_write(query, params)
            count += 1

        return count

    def load_libertadores_matches(self) -> int:
        """
        Load Copa Libertadores matches from CSV.

        Returns:
            Number of matches loaded
        """
        filepath = self.data_dir / "Libertadores_Matches.csv"
        if not filepath.exists():
            return 0

        df = pd.read_csv(filepath, encoding="utf-8")
        count = 0

        self._ensure_competition("Copa Libertadores", "cup")

        for _, row in df.iterrows():
            home_team = self._ensure_team(row.get("home_team", ""))
            away_team = self._ensure_team(row.get("away_team", ""))

            if not home_team or not away_team:
                continue

            match_date = self.parse_date(row.get("datetime"))
            season = safe_int(row.get("season")) or None

            if season:
                self._ensure_season(season)

            query = """
            MATCH (home:Team {normalized_name: $home_team})
            MATCH (away:Team {normalized_name: $away_team})
            MATCH (comp:Competition {name: 'Copa Libertadores'})
            CREATE (m:Match {
                datetime: $datetime,
                home_goals: $home_goals,
                away_goals: $away_goals,
                stage: $stage,
                competition: 'Copa Libertadores'
            })
            CREATE (m)-[:HOME_TEAM]->(home)
            CREATE (m)-[:AWAY_TEAM]->(away)
            CREATE (m)-[:PART_OF]->(comp)
            """
            params = {
                "home_team": home_team,
                "away_team": away_team,
                "datetime": match_date.isoformat() if match_date else None,
                "home_goals": safe_int(row.get("home_goal")),
                "away_goals": safe_int(row.get("away_goal")),
                "stage": str(row.get("stage", "")) if pd.notna(row.get("stage")) else None,
            }

            if season:
                query += """
                WITH m
                MATCH (s:Season {year: $season})
                CREATE (m)-[:IN_SEASON]->(s)
                """
                params["season"] = season

            self.connection.execute_write(query, params)
            count += 1

        return count

    def load_fifa_players(self) -> int:
        """
        Load FIFA player data from CSV.

        Returns:
            Number of players loaded
        """
        filepath = self.data_dir / "fifa_data.csv"
        if not filepath.exists():
            return 0

        df = pd.read_csv(filepath, encoding="utf-8")
        count = 0

        for _, row in df.iterrows():
            name = row.get("Name", "")
            if not name or pd.isna(name):
                continue

            club = row.get("Club", "")
            if club and pd.notna(club):
                self._ensure_team(club)
                normalized_club = self.normalize_team_name(club)
            else:
                normalized_club = None

            query = """
            CREATE (p:Player {
                name: $name,
                age: $age,
                nationality: $nationality,
                overall: $overall,
                potential: $potential,
                club: $club,
                position: $position,
                jersey_number: $jersey_number,
                height: $height,
                weight: $weight,
                preferred_foot: $preferred_foot,
                crossing: $crossing,
                finishing: $finishing,
                heading_accuracy: $heading_accuracy,
                short_passing: $short_passing,
                dribbling: $dribbling,
                ball_control: $ball_control,
                acceleration: $acceleration,
                sprint_speed: $sprint_speed,
                stamina: $stamina,
                strength: $strength
            })
            """
            params = {
                "name": str(name),
                "age": safe_int(row.get("Age")) or None,
                "nationality": str(row.get("Nationality", "")) if pd.notna(row.get("Nationality")) else None,
                "overall": safe_int(row.get("Overall")) or None,
                "potential": safe_int(row.get("Potential")) or None,
                "club": str(club) if club and pd.notna(club) else None,
                "position": str(row.get("Position", "")) if pd.notna(row.get("Position")) else None,
                "jersey_number": safe_int(row.get("Jersey Number")) or None,
                "height": str(row.get("Height", "")) if pd.notna(row.get("Height")) else None,
                "weight": str(row.get("Weight", "")) if pd.notna(row.get("Weight")) else None,
                "preferred_foot": str(row.get("Preferred Foot", "")) if pd.notna(row.get("Preferred Foot")) else None,
                "crossing": safe_int(row.get("Crossing")) or None,
                "finishing": safe_int(row.get("Finishing")) or None,
                "heading_accuracy": safe_int(row.get("HeadingAccuracy")) or None,
                "short_passing": safe_int(row.get("ShortPassing")) or None,
                "dribbling": safe_int(row.get("Dribbling")) or None,
                "ball_control": safe_int(row.get("BallControl")) or None,
                "acceleration": safe_int(row.get("Acceleration")) or None,
                "sprint_speed": safe_int(row.get("SprintSpeed")) or None,
                "stamina": safe_int(row.get("Stamina")) or None,
                "strength": safe_int(row.get("Strength")) or None,
            }

            if normalized_club:
                query += """
                WITH p
                MATCH (t:Team {normalized_name: $normalized_club})
                CREATE (p)-[:PLAYS_FOR]->(t)
                """
                params["normalized_club"] = normalized_club

            self.connection.execute_write(query, params)
            count += 1

        return count

    def load_all(self, clear: bool = True) -> Dict[str, int]:
        """
        Load all data files into the database.

        Args:
            clear: If True, clear existing data first

        Returns:
            Dictionary with counts of loaded records by type
        """
        if clear:
            self.clear_database()

        self.create_indexes()

        results = {
            "brasileirao_matches": self.load_brasileirao_matches(),
            "copa_brasil_matches": self.load_copa_brasil_matches(),
            "libertadores_matches": self.load_libertadores_matches(),
            "fifa_players": self.load_fifa_players(),
            "teams": len(self.teams_cache),
            "competitions": len(self.competitions_cache),
        }

        return results
