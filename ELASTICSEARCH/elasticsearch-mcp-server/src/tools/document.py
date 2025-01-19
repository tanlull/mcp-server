from typing import Any
from mcp.types import TextContent
from .base import BaseTools

class DocumentTools(BaseTools):
    def register_tools(self, mcp: Any):
        """Register document-related tools."""
        
        @mcp.tool(description="Search documents in an index with a custom query")
        async def search_documents(index: str, body: dict) -> list[TextContent]:
            """
            Search documents in a specified index using a custom query.
            
            Args:
                index: Name of the index to search
                body: Elasticsearch query DSL
            """
            self.logger.info(f"Searching in index: {index} with query: {body}")
            try:
                response = self.es_client.search(index=index, body=body)
                return [TextContent(type="text", text=str(response))]
            except Exception as e:
                self.logger.error(f"Error searching documents: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
