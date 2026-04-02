"""
RAG Engine for Apex Residences Chatbot
Handles document retrieval and context management for company knowledge
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for company knowledge base.
    Loads markdown files, creates vector embeddings, and retrieves relevant context.
    Includes error handling for embedding and search operations.
    Supports multiple embeddings providers: OpenAI, HuggingFace.
    """

    def __init__(self, knowledge_file: str = "company_info.md", timeout: int = 30):
        """
        Initialize RAG Engine with available embeddings provider.

        Args:
            knowledge_file: Path to markdown file containing company information
            timeout: Timeout for API calls in seconds

        Raises:
            ValueError: If no embeddings provider is available
        """
        self.knowledge_file = knowledge_file
        self.timeout = timeout
        self.embeddings = None
        
        # Try to initialize embeddings with fallback chain
        self._init_embeddings()
        
        if not self.embeddings:
            raise ValueError(
                "No embeddings provider available. "
                "Please set OPENAI_API_KEY environment variable or install sentence-transformers."
            )
        
        self.vector_store = None
        self._load_knowledge_base()

    def _init_embeddings(self) -> None:
        """
        Initialize embeddings provider with fallback chain.
        Tries: OpenAI → HuggingFace local embeddings
        """
        # Try OpenAI API first
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from langchain_openai import OpenAIEmbeddings
                self.embeddings = OpenAIEmbeddings(
                    api_key=openai_key,
                    model="text-embedding-3-small",
                    request_timeout=self.timeout,
                )
                logger.info("Initialized embeddings with OpenAI API")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
        
        # Fall back to HuggingFace embeddings (free, local)
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
            )
            logger.info("Initialized embeddings with HuggingFace (all-MiniLM-L6-v2)")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFace embeddings: {e}")
        
        # If both fail, log error (will be caught in __init__)
        logger.error("No embeddings provider available - OpenAI API and HuggingFace both failed")

    def _load_knowledge_base(self) -> None:
        """Load company_info.md and create vector embeddings."""
        # Find knowledge file (could be in root or current directory)
        knowledge_path = None
        for candidate in [
            self.knowledge_file,
            os.path.join(os.path.dirname(__file__), "..", self.knowledge_file),
            os.path.join(os.getcwd(), self.knowledge_file),
        ]:
            if os.path.exists(candidate):
                knowledge_path = candidate
                break

        if not knowledge_path:
            raise FileNotFoundError(
                f"Knowledge file '{self.knowledge_file}' not found. "
                f"Searched: {self.knowledge_file}, parent dir, current working directory"
            )

        logger.info(f"Loading knowledge base from {knowledge_path}")

        # Read markdown file
        with open(knowledge_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into chunks (~500 chars with overlap)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n## ", "\n### ", "\n", " ", ""],
        )

        chunks = splitter.split_text(content)
        logger.info(f"Created {len(chunks)} chunks from knowledge base")

        # Create documents with metadata
        documents = [
            Document(page_content=chunk, metadata={"source": self.knowledge_file, "chunk_id": i})
            for i, chunk in enumerate(chunks)
        ]

        # Create vector store (FAISS - lightweight, in-memory)
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        logger.info("Vector store created successfully")

    def retrieve_context(self, query: str, top_k: int = 3) -> Tuple[List[str], List[float]]:
        """
        Retrieve relevant chunks from knowledge base with error handling.

        Args:
            query: User query/question
            top_k: Number of top results to return

        Returns:
            Tuple of (retrieved_chunks, similarity_scores)
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return [], []

        try:
            # Similarity search with scores
            results = self.vector_store.similarity_search_with_score(query, k=top_k)

            chunks = [doc.page_content for doc, score in results]
            scores = [score for doc, score in results]

            logger.debug(f"Retrieved {len(chunks)} chunks for query: {query}")
            return chunks, scores
        
        except Exception as e:
            logger.error(f"Error retrieving context from vector store: {e}")
            return [], []

    def format_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve and format context as a string for LLM.

        Args:
            query: User question
            top_k: Number of results

        Returns:
            Formatted context string
        """
        chunks, scores = self.retrieve_context(query, top_k)

        if not chunks:
            return ""

        context_parts = [f"**Relevant Information (Confidence: {1 - score:.1%})**\n{chunk}" 
                        for chunk, score in zip(chunks, scores)]
        
        return "\n\n---\n\n".join(context_parts)

    def is_company_question(self, query: str) -> bool:
        """
        Heuristic to determine if query is about company (not web search).
        Uses keyword matching as a simple router.

        Args:
            query: User question

        Returns:
            True if likely a company-specific question
        """
        company_keywords = [
            "service", "pricing", "price", "cost", "team", "staff", "contact", "hours",
            "availability", "fee", "package", "tier", "premium", "platinum", "elite",
            "offer", "specialize", "background", "experience", "expertise", "how much",
            "how many", "what service", "what do you", "do you offer", "do you provide",
            "event planning", "property management", "concierge", "vendor", "faq",
            "about", "philosophy", "mission", "values", "who is", "who are",
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in company_keywords)
