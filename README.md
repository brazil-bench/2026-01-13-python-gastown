# Brazilian Soccer MCP Server

An MCP (Model Context Protocol) server that provides a knowledge graph interface for Brazilian soccer data using Neo4j. Enables natural language queries about players, teams, matches, and competitions.

## Overview

This project implements an MCP server that:
- Loads Brazilian soccer data from CSV files into a Neo4j graph database
- Exposes query tools for matches, teams, players, and competitions
- Supports natural language queries via LLM integration

## Architecture

```
src/brazilian_soccer_mcp/
├── __init__.py        # Package initialization
├── db.py              # Neo4j connection management
├── data_loader.py     # CSV to Neo4j data loading
├── queries.py         # Query interfaces (Match, Team, Player, Competition)
└── server.py          # MCP server with tool definitions
```

### Graph Schema

**Nodes:**
- `Team` - Soccer teams with normalized names
- `Player` - FIFA player database with ratings and attributes
- `Match` - Individual matches with scores and metadata
- `Competition` - Competitions (Brasileirão, Copa do Brasil, Libertadores)
- `Season` - Season years

**Relationships:**
- `(Match)-[:HOME_TEAM]->(Team)`
- `(Match)-[:AWAY_TEAM]->(Team)`
- `(Match)-[:PART_OF]->(Competition)`
- `(Match)-[:IN_SEASON]->(Season)`
- `(Player)-[:PLAYS_FOR]->(Team)`

## Data Sources

All data is from Kaggle (pre-downloaded in `data/kaggle/`):

| File | Records | Description | License |
|------|---------|-------------|---------|
| `Brasileirao_Matches.csv` | 4,180 | Série A matches | CC BY 4.0 |
| `Brazilian_Cup_Matches.csv` | 1,337 | Copa do Brasil matches | CC BY 4.0 |
| `Libertadores_Matches.csv` | 1,255 | Copa Libertadores matches | CC BY 4.0 |
| `BR-Football-Dataset.csv` | 10,296 | Extended match statistics | CC0 |
| `novo_campeonato_brasileiro.csv` | 6,886 | Historical 2003-2019 | CC BY 4.0 |
| `fifa_data.csv` | 18,207 | FIFA player database | Apache 2.0 |

## Installation

### Prerequisites

- Python 3.10+
- Neo4j 5.x (Docker recommended)

### Setup

1. **Start Neo4j:**
```bash
docker run -d --name neo4j-soccer \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5.15.0
```

2. **Install Python package:**
```bash
pip install -e ".[dev]"
```

3. **Load data into Neo4j:**
```python
from brazilian_soccer_mcp import Neo4jConnection, DataLoader

conn = Neo4jConnection()
loader = DataLoader(conn, "data/kaggle")
stats = loader.load_all()
print(stats)
```

## MCP Tools

The server exposes these tools for LLM integration:

| Tool | Description |
|------|-------------|
| `search_matches` | Find matches by team, date range, competition, season |
| `get_team_stats` | Get win/loss/draw statistics for a team |
| `compare_teams` | Head-to-head comparison between two teams |
| `search_players` | Find players by name, nationality, club, position, rating |
| `get_standings` | Get league standings for a season |
| `get_competition_stats` | Aggregate competition statistics |
| `get_biggest_wins` | Matches with largest goal differences |
| `list_teams` | List all teams in database |
| `list_competitions` | List all competitions |
| `list_seasons` | List all seasons with data |

## Usage Examples

### Query Matches Between Teams
```python
from brazilian_soccer_mcp import MatchQueries, get_connection

conn = get_connection()
mq = MatchQueries(conn)

# Find Fla-Flu derby matches
matches = mq.find_matches_between_teams("Flamengo", "Fluminense")
for m in matches[:5]:
    print(f"{m.datetime[:10]}: {m.home_team} {m.home_goals}-{m.away_goals} {m.away_team}")
```

### Get Team Statistics
```python
from brazilian_soccer_mcp import TeamQueries, get_connection

conn = get_connection()
tq = TeamQueries(conn)

stats = tq.get_team_stats("Palmeiras", season=2019)
print(f"Palmeiras 2019: {stats.wins}W {stats.draws}D {stats.losses}L, {stats.points} pts")
```

### Search Players
```python
from brazilian_soccer_mcp import PlayerQueries, get_connection

conn = get_connection()
pq = PlayerQueries(conn)

# Top Brazilian players
players = pq.get_top_players(nationality="Brazil", limit=10)
for p in players:
    print(f"{p.name} - {p.overall} overall, {p.club}")
```

### Get League Standings
```python
from brazilian_soccer_mcp import CompetitionQueries, get_connection

conn = get_connection()
cq = CompetitionQueries(conn)

standings = cq.get_season_standings(2019, "Brasileirão")
for i, team in enumerate(standings[:5], 1):
    print(f"{i}. {team.team} - {team.points} pts")
```

## Testing

Tests use BDD (Behavior-Driven Development) with Given/When/Then scenarios via pytest-bdd.

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_matches.py -v

# Run with coverage
pytest tests/ --cov=brazilian_soccer_mcp
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures (Neo4j connection, data loading)
├── features/                # Gherkin feature files
│   ├── matches.feature
│   ├── teams.feature
│   ├── players.feature
│   └── competitions.feature
├── test_matches.py          # Match query tests
├── test_teams.py            # Team statistics tests
├── test_players.py          # Player search tests
└── test_competitions.py     # Competition/season tests
```

### Sample Test Output

```
tests/test_competitions.py::test_get_league_standings_for_a_season PASSED
tests/test_competitions.py::test_get_competition_statistics PASSED
tests/test_matches.py::test_find_matches_between_two_teams PASSED
tests/test_matches.py::test_find_matches_for_a_single_team PASSED
tests/test_players.py::test_search_players_by_nationality PASSED
tests/test_teams.py::test_get_team_statistics PASSED
...
============================== 40 passed ==============================
```

## Configuration

Environment variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Database username |
| `NEO4J_PASSWORD` | `password123` | Database password |
| `NEO4J_DATABASE` | `neo4j` | Target database |

## Running the MCP Server

```bash
# Start the server
python -m brazilian_soccer_mcp.server

# Or using the installed entry point
brazilian-soccer-mcp
```

## Project Structure

```
├── data/
│   └── kaggle/              # CSV data files
├── src/
│   └── brazilian_soccer_mcp/
│       ├── __init__.py
│       ├── db.py
│       ├── data_loader.py
│       ├── queries.py
│       └── server.py
├── tests/
│   ├── conftest.py
│   ├── features/
│   └── test_*.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## License

This project is for demo/non-commercial use. Data sources have individual licenses (CC BY 4.0, CC0, Apache 2.0).

## References

- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [pytest-bdd](https://pytest-bdd.readthedocs.io/)
