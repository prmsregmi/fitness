
import trafilatura
import logging
# ContentExtractor class for extracting main text content using trafilatura

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentExtractor:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def extract_text(self, url: str) -> str:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                return trafilatura.extract(downloaded) or ""
            else:
                logger.warning(f"Failed to download content from {url}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting from {url}: {e}")
            return ""

    def enrich_results(self, results: list[dict]) -> list[dict]:
        enriched = []
        for result in results:
            link = result.get("link")
            if link:
                content = self.extract_text(link)
                enriched.append({**result, "content": content})
            else:
                enriched.append({**result, "content": ""})
        return enriched