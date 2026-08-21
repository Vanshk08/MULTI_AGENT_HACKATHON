import asyncio
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, quote
from datetime import datetime
from loguru import logger
from langchain.tools import BaseTool

# Crawl4AI is optional. If it is unavailable or uses an incompatible API, fall back gracefully.
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    CRAWL4AI_AVAILABLE = True
except Exception:
    AsyncWebCrawler = None
    CrawlerRunConfig = None
    CacheMode = None
    JsonCssExtractionStrategy = None
    CRAWL4AI_AVAILABLE = False


class WebSearchTool(BaseTool):
    """
    A tool to perform web searches using Crawl4AI to scrape DuckDuckGo.
    It extracts search results including title, URL, and snippet.
    Falls back to a no-crawl response when Crawl4AI is unavailable.
    """

    name: str = "web_search"
    description: str = "Search the web using DuckDuckGo"
    search_engine_url: str = "https://html.duckduckgo.com/html/"
    extraction_strategy: Optional[Any] = None
    
    def __init__(self):
        super().__init__()

        if not CRAWL4AI_AVAILABLE:
            logger.warning("Crawl4AI is not available. WebSearchTool will return fallback results.")
            return

        # Schema to extract search results from DuckDuckGo's HTML version.
        # The output JSON will have a top-level key 'results'
        # containing a list of the extracted items.
        schema = {
            "name": "Search Results",
            "baseSelector": "div.result",
            "collection_name": "results",
            "fields": [
                {"name": "title", "selector": "h2.result__title > a.result__a", "type": "text"},
                {"name": "url", "selector": "h2.result__title > a.result__a", "type": "attribute", "attribute": "href"},
                {"name": "snippet", "selector": "a.result__snippet", "type": "text"}
            ]
        }
        object.__setattr__(self, 'extraction_strategy', JsonCssExtractionStrategy(schema))

    def _run(self, query: str) -> Dict[str, Any]:
        """Synchronous web search - required by BaseTool"""
        raise NotImplementedError("Please use _arun for asynchronous execution")

    async def _arun(self, query: str) -> Dict[str, Any]:
        """
        Performs a web search on DuckDuckGo and returns structured results.

        Args:
            query: The search query string.

        Returns:
            A dictionary containing structured search results with keys:
            - results: List of dictionaries with 'title', 'url', and 'snippet'
            - count: Number of results found
            - query: Original search query
            - summary: Human-readable summary of the search
            - timestamp: When the search was performed
        """
        if not CRAWL4AI_AVAILABLE:
            logger.warning(f"Crawl4AI unavailable; returning fallback web search result for '{query}'")
            return {
                "results": [],
                "count": 0,
                "query": query,
                "summary": f"Crawl4AI is unavailable; web search skipped for '{query}'.",
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            }

        search_url = f"{self.search_engine_url}?q={quote(query)}"
        logger.info(f"Performing web search for: '{query}'")
        logger.debug(f"Searching at URL: {search_url}")

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Ensure fresh results for every search
            extraction_strategy=self.extraction_strategy
        )

        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=search_url, config=config)

                if not result or not result.extracted_content:
                    logger.warning(f"No content extracted for query: '{query}'")
                    return {
                        "results": [],
                        "count": 0,
                        "query": query,
                        "summary": f"No results found for '{query}'.",
                        "timestamp": datetime.now().isoformat()
                    }

                # The result from JsonCssExtractionStrategy is a JSON string
                data = json.loads(result.extracted_content)

                search_results = []
                if isinstance(data, dict):
                    # The schema defines 'results' as the collection name
                    search_results = data.get("results", [])
                elif isinstance(data, list):
                    # Sometimes the extractor might return a list directly
                    search_results = data

                if not isinstance(search_results, list):
                    logger.warning(f"Unexpected response structure for query: '{query}'. Expected a list of results.")
                    return {
                        "results": [],
                        "count": 0,
                        "query": query,
                        "summary": f"Unexpected response structure for '{query}'.",
                        "timestamp": datetime.now().isoformat()
                    }
                if not search_results:
                    logger.info(f"No search results found for query: '{query}'")
                    return {
                        "results": [],
                        "count": 0,
                        "query": query,
                        "summary": f"No search results for '{query}'.",
                        "timestamp": datetime.now().isoformat()
                    }

                cleaned_results = []
                for item in search_results:
                    if not isinstance(item, dict):
                        continue
                        
                    raw_url = item.get("url")
                    if not raw_url:
                        continue

                    try:
                        parsed_url = urlparse(raw_url)
                        query_params = parse_qs(parsed_url.query)
                        real_url = query_params.get("uddg", [None])[0]

                        if real_url:
                            cleaned_results.append({
                                "title": (item.get("title") or "").strip(),
                                "url": real_url,
                                "snippet": (item.get("snippet") or "").strip().replace("\n", " ")
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse URL from DDG result: {raw_url}. Error: {e}")
                        continue

                logger.success(f"Found {len(cleaned_results)} results for query: '{query}'")
                # Return a structured dict instead of a list to make it easier to work with
                return {
                    "results": cleaned_results,
                    "count": len(cleaned_results),
                    "query": query,
                    "summary": f"Found {len(cleaned_results)} results for '{query}'.",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"An error occurred during web search for query '{query}': {e}")
            return {
                "results": [],
                "count": 0,
                "query": query,
                "summary": f"Error occurred for '{query}': {str(e)[:100]}...",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
