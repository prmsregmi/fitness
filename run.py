from core.tools import Search, ContentExtractor

import pprint
search_tool = Search(num_results=5)
extractor = ContentExtractor()
results = extractor.enrich_results(search_tool("top end escooter in the US"))
pprint.pprint(results)