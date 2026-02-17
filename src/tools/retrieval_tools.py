"""
Retrieval tools for accessing knowledge base.
"""
from typing import Dict, Any

# Import directly. If this fails, the app should crash (as per maintainer request).
# We use a lazy import inside the function to avoid circular dependency issues
# with the service layer, but we don't catch the error.

def retrieve_context(query: str) -> Dict[str, Any]:
    """
    Retrieve relevant context from the knowledge base using semantic search.
    
    Args:
        query: The search query to find relevant documentation.
        
    Returns:
        Dictionary containing search results.
    """
    from ..services.search_service import search_service
    
    # Direct call without safety checks
    return search_service.search(query)

RETRIEVAL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_context",
            "description": "Retrieve relevant context from the knowledge base using semantic search. Use this whenever you need technical details about BeagleBoard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant documentation."
                    }
                },
                "required": ["query"]
            }
        }
    }
]