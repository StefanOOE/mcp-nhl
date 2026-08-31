"""mcp-nhl: an MCP server for the public NHL APIs."""

from .client import NHLAPIError, NHLClient
from .digest import format_players_digest

__version__ = "0.1.0"
__all__ = ["NHLClient", "NHLAPIError", "format_players_digest", "__version__"]
