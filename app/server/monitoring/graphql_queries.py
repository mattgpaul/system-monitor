"""
GraphQL queries for polling agent telemetry data.
Loads queries from separate .graphql files for better maintainability.
"""

from pathlib import Path
from typing import Dict

# Get the directory where this Python file is located
QUERIES_DIR = Path(__file__).parent / "queries"


def load_query_file(filename: str) -> str:
    """
    Load a GraphQL query from a .graphql file.

    Args:
        filename (str): Name of the .graphql file (without extension)

    Returns:
        str: GraphQL query string

    Raises:
        FileNotFoundError: If the query file doesn't exist
        IOError: If the file cannot be read
    """
    file_path = QUERIES_DIR / f"{filename}.graphql"

    if not file_path.exists():
        raise FileNotFoundError(f"Query file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except IOError as e:
        raise IOError(f"Cannot read query file {file_path}: {e}")


# Load all available queries at module import
_QUERIES_CACHE: Dict[str, str] = {}


def _load_all_queries() -> None:
    """Load all .graphql files into the cache."""
    if not QUERIES_DIR.exists():
        raise FileNotFoundError(f"Queries directory not found: {QUERIES_DIR}")

    for file_path in QUERIES_DIR.glob("*.graphql"):
        query_name = file_path.stem  # filename without extension
        try:
            _QUERIES_CACHE[query_name] = load_query_file(query_name)
        except (FileNotFoundError, IOError) as e:
            # Log error but don't fail module import
            print(f"Warning: Could not load query {query_name}: {e}")


# Load queries when module is imported
_load_all_queries()

# Query type mappings for easy access
QUERY_TYPES = {
    "basic": "telemetry_basic",
    "extended": "telemetry_extended",
    "health": "health_check",
}


def get_query(query_type: str = "basic") -> str:
    """
    Get a GraphQL query by type.

    Args:
        query_type (str): Type of query ('basic', 'extended', 'health')

    Returns:
        str: GraphQL query string

    Raises:
        ValueError: If query_type is not recognized
        FileNotFoundError: If the corresponding .graphql file wasn't loaded
    """
    if query_type not in QUERY_TYPES:
        available = ", ".join(QUERY_TYPES.keys())
        raise ValueError(f"Unknown query type '{query_type}'. Available: {available}")

    file_name = QUERY_TYPES[query_type]

    if file_name not in _QUERIES_CACHE:
        raise FileNotFoundError(f"Query '{query_type}' not loaded from {file_name}.graphql")

    return _QUERIES_CACHE[file_name]


def get_available_queries() -> list:
    """
    Get list of available query types.

    Returns:
        list: Available query type names
    """
    return list(QUERY_TYPES.keys())


def reload_queries() -> None:
    """
    Reload all queries from disk (useful for development).
    """
    _QUERIES_CACHE.clear()
    _load_all_queries()
