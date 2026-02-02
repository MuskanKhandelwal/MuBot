"""
Retrieval-Augmented Generation (RAG) Engine

This module implements semantic search over past outreach emails and
related content. It enables the agent to:
- Find similar past emails for inspiration
- Retrieve context about companies and roles
- Learn from previous successful outreach
- Avoid repetitive messaging

The RAG engine uses:
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Cosine similarity for retrieval
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from mubot.config.settings import Settings
from mubot.memory.models import OutreachEntry


class RAGEngine:
    """
    Semantic search engine for outreach context retrieval.
    
    The RAG engine maintains a vector database of:
    - Past cold email threads
    - Job descriptions
    - Company information
    - Response outcomes
    
    This enables context-aware email generation by retrieving
    relevant examples from past successful outreach.
    
    Usage:
        rag = RAGEngine(settings)
        await rag.initialize()
        
        # Index an email
        await rag.index_outreach(entry)
        
        # Search for similar emails
        results = await rag.search_similar(
            query="Senior Engineer at fintech startup",
            filter_criteria={"outcome": "positive"},
        )
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the RAG engine.
        
        Args:
            settings: Application settings
        """
        self.settings = settings or Settings()
        self.db_path = self.settings.chroma_db_path
        self.model_name = self.settings.embedding_model
        
        self.client: Optional[chromadb.Client] = None
        self.collection = None
        self.embedding_model: Optional[SentenceTransformer] = None
    
    async def initialize(self) -> bool:
        """
        Initialize the vector database and embedding model.
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="outreach_emails",
                metadata={"description": "Job search cold email history"},
            )
            
            # Load embedding model
            print(f"Loading embedding model: {self.model_name}...")
            self.embedding_model = SentenceTransformer(self.model_name)
            
            print(f"✓ RAG engine initialized with {self.collection.count()} documents")
            return True
            
        except Exception as e:
            print(f"✗ RAG initialization failed: {e}")
            return False
    
    async def index_outreach(self, entry: OutreachEntry) -> bool:
        """
        Index an outreach entry for retrieval.
        
        Args:
            entry: OutreachEntry to index
        
        Returns:
            True if indexed successfully
        """
        if not self.collection or not self.embedding_model:
            raise RuntimeError("RAG engine not initialized")
        
        try:
            # Create document from entry
            document = self._entry_to_document(entry)
            
            # Generate embedding
            embedding = self.embedding_model.encode(document).tolist()
            
            # Create unique ID
            doc_id = self._generate_id(entry)
            
            # Metadata for filtering
            metadata = {
                "company": entry.company_name,
                "role": entry.role_title,
                "status": entry.status.value,
                "response_category": entry.response_category.value if entry.response_category else "none",
                "sent_at": entry.sent_at.isoformat() if entry.sent_at else "",
                "has_response": entry.response_body is not None,
            }
            
            # Add to collection
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )
            
            return True
            
        except Exception as e:
            print(f"Error indexing outreach: {e}")
            return False
    
    async def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filter_criteria: Optional[dict] = None,
    ) -> list[dict]:
        """
        Search for similar outreach emails.
        
        Args:
            query: Search query (can be natural language)
            n_results: Number of results to return
            filter_criteria: Optional metadata filters
                e.g., {"response_category": "positive"}
        
        Returns:
            List of result dicts with document, metadata, and distance
        """
        if not self.collection or not self.embedding_model:
            raise RuntimeError("RAG engine not initialized")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Build where clause for filtering
            where_clause = self._build_where_clause(filter_criteria)
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )
            
            # Format results
            formatted = []
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Convert to similarity
                })
            
            return formatted
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    async def get_company_context(
        self,
        company_name: str,
        n_results: int = 10,
    ) -> list[dict]:
        """
        Get all indexed emails for a specific company.
        
        Args:
            company_name: Company to look up
            n_results: Max results to return
        
        Returns:
            List of outreach entries for this company
        """
        return await self.search_similar(
            query=f"company:{company_name}",
            n_results=n_results,
            filter_criteria={"company": company_name},
        )
    
    async def get_successful_templates(
        self,
        role_type: Optional[str] = None,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Retrieve templates that got positive responses.
        
        Args:
            role_type: Optional role filter (e.g., "engineer", "manager")
            n_results: Number of templates to return
        
        Returns:
            List of successful outreach templates
        """
        query = "positive response reply interested"
        if role_type:
            query += f" {role_type}"
        
        return await self.search_similar(
            query=query,
            n_results=n_results,
            filter_criteria={"response_category": "positive"},
        )
    
    async def index_batch(
        self,
        entries: list[OutreachEntry],
    ) -> tuple[int, int]:
        """
        Index multiple outreach entries efficiently.
        
        Args:
            entries: List of OutreachEntry to index
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for entry in entries:
            if await self.index_outreach(entry):
                successful += 1
            else:
                failed += 1
        
        return successful, failed
    
    async def refresh_index(
        self,
        memory_manager,
        days: int = 90,
    ) -> tuple[int, int]:
        """
        Refresh the vector index from memory files.
        
        This should be run periodically to ensure the index is up-to-date
        with the latest memory entries.
        
        Args:
            memory_manager: MemoryManager to load entries from
            days: How many days back to index
        
        Returns:
            Tuple of (indexed_count, errors)
        """
        # TODO: Implement loading from memory files
        # For now, placeholder
        return 0, 0
    
    def get_stats(self) -> dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dict with count and other stats
        """
        if not self.collection:
            return {"total_documents": 0}
        
        return {
            "total_documents": self.collection.count(),
            "db_path": str(self.db_path),
            "embedding_model": self.model_name,
        }
    
    # ======================================================================
    # Helper Methods
    # ======================================================================
    
    def _entry_to_document(self, entry: OutreachEntry) -> str:
        """
        Convert an OutreachEntry to a searchable document string.
        
        This combines all relevant fields into a single text representation
        that can be embedded and searched.
        """
        parts = [
            f"Company: {entry.company_name}",
            f"Role: {entry.role_title}",
            f"Subject: {entry.subject}",
            f"Body: {entry.body}",
        ]
        
        if entry.personalization_elements:
            parts.append(f"Personalization: {'; '.join(entry.personalization_elements)}")
        
        if entry.response_body:
            parts.append(f"Response: {entry.response_body[:500]}")  # Truncate
        
        return "\n\n".join(parts)
    
    def _generate_id(self, entry: OutreachEntry) -> str:
        """Generate a unique ID for an entry."""
        # Use entry ID if available, otherwise hash the content
        if entry.id:
            return f"outreach_{entry.id}"
        
        content = f"{entry.company_name}:{entry.role_title}:{entry.created_at}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _build_where_clause(
        self,
        filter_criteria: Optional[dict],
    ) -> Optional[dict]:
        """
        Build ChromaDB where clause from filter criteria.
        
        ChromaDB uses a specific syntax for filtering:
        - Equality: {"key": "value"}
        - Logical AND: {"$and": [{...}, {...}]}
        - Logical OR: {"$or": [{...}, {...}]}
        """
        if not filter_criteria:
            return None
        
        # Simple equality filters
        conditions = []
        for key, value in filter_criteria.items():
            conditions.append({key: value})
        
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return {"$and": conditions}
        
        return None
