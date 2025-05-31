import os
import logging
from dotenv import load_dotenv
from serpapi import GoogleSearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Search:
    def __init__(self, num_results):
        load_dotenv()
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is not set in the environment.")
        if not isinstance(num_results, int) or num_results <= 0:
            raise ValueError("num_results must be a positive integer.")
        self.num_results = num_results
    
    def parse_results(self, results):
        return [
            {
                "title": r.get("title"),
                "snippet": r.get("snippet"),
                "link": r.get("link"),
            }
            for r in results
            if r.get("title") and r.get("link")
        ]

    def __call__(self, query, **kwargs):
        params = {
            "q": query,
            "num": self.num_results,
            "api_key": self.api_key,
        }
        params.update({k: v for k, v in kwargs.items() if k not in ["q", "num", "api_key"]})

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return self.parse_results(results.get("organic_results", []))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

# Example usage
if __name__ == "__main__":
    query = "python web scraping tutorial"
    Search(5)(query)