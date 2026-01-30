"""
Search Service Module
Handles document search and retrieval operations
"""

import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SearchService:
    """Service for handling document search and retrieval"""

    def __init__(self, backend_url: str, collection_name: str):
        self.backend_url = backend_url
        self.collection_name = collection_name

    def search(self, query: str, n_results: int = 5, rerank: bool = True, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Search documents using the backend API"""
        try:
            timeout_sec = float(os.getenv('RAG_TIMEOUT_SECONDS', '30'))
            url = f"{self.backend_url}/retrieve"
            payload = {
                "query": query,
                "collection_name": collection_name or self.collection_name,
                "n_results": n_results,
                "include_metadata": True,
                "rerank": rerank
            }
            response = requests.post(url, json=payload, timeout=timeout_sec)

            if response.status_code == 200:
                result = response.json()
                return {
                    'documents': result.get('documents', []),
                    'metadatas': result.get('metadatas', []),
                    'distances': result.get('distances', []),
                    'total_found': result.get('total_found', 0),
                    'filtered_results': result.get('filtered_results', 0),
                    'retrieval_ok': True
                }
            else:
                logger.error(f"Search API failed: {response.status_code} - {response.text}")
                return {
                    'documents': [],
                    'metadatas': [],
                    'distances': [],
                    'retrieval_ok': False,
                    'error': f"HTTP {response.status_code}: {response.text[:300]}"
                }

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'retrieval_ok': False, 'error': str(e)}


# Global instance will be created when needed
search_service = None