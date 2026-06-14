import logging
from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

logger = logging.getLogger(__name__)

class WebSearchPlugin(BasePlugin):
    def __init__(self):
        self.bus = None
        self.is_running = False

    def get_metadata(self) -> dict:
        return {
            "name": "web_search_plugin",
            "version": "1.0",
            "description": "Search for information on the Internet via DuckDuckGo.",
            "permissions": ["network"],
            "tools": [
                {
                    "name": "web_search",
                    "description": "Search for information on the Internet via DuckDuckGo.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keyword (e.g., 'Hanoi weather today')"}
                        },
                        "required": ["query"]
                    }
                }
            ]
        }

    async def on_load(self):
        logger.info("[WebSearchPlugin] Loaded configuration.")

    async def on_start(self, event_bus: IEventBus):
        self.bus = event_bus
        self.is_running = True
        logger.info("[WebSearchPlugin] Started.")

    async def execute_tool(self, tool_name: str, payload: dict):
        if tool_name == "web_search":
            query = payload.get("query")
            if not query:
                return {"status": "Error", "message": "Missing 'query' parameter."}
            if DDGS is None:
                return {
                    "status": "Error",
                    "message": "Missing optional dependency 'ddgs'. Install it to enable web search."
                }
                
            logger.info(f"[WebSearchPlugin] Searching web for: {query}")
            try:
                results = []
                # Initialize DDGS and get text results
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=3):
                        results.append({
                            "title": r.get("title"),
                            "body": r.get("body"),
                            "href": r.get("href")
                        })
                        
                logger.info(f"[WebSearchPlugin] Search success, found {len(results)} results.")
                return {"status": "Success", "results": results}
            except Exception as e:
                logger.error(f"[WebSearchPlugin] Search failed: {e}")
                return {"status": "Error", "message": str(e)}

        raise ValueError(f"Unknown tool {tool_name}")

    async def on_stop(self):
        self.is_running = False
        logger.info("[WebSearchPlugin] Stopped.")
