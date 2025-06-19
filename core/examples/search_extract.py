"""Simple search and content extraction example."""

from typing import List, Dict, Any
import pprint
from core.tools import Search, ContentExtractor


def search_extract(query: str, num_results: int = 5) -> List[Dict[Any, Any]]:
    """Search for a query and extract enriched content from results.

    Args:
        query: Search query string
        num_results: Number of search results to return (default: 5)

    Returns:
        List of enriched search results
    """
    search_tool = Search(num_results=num_results)
    extractor = ContentExtractor()
    results = extractor.enrich_results(search_tool(query))
    return results


if __name__ == "__main__":
    results = search_extract("top end escooter in the US")
    pprint.pprint(results)