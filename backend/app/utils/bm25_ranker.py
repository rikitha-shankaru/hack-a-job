"""
BM25 (Best Matching 25) ranking algorithm for job search relevance
"""
import re
from typing import List, Dict, Any
from collections import Counter
import math


class BM25Ranker:
    """
    BM25 ranking algorithm implementation for ranking job postings by relevance to search query.
    BM25 is a probabilistic ranking function that improves upon TF-IDF.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 ranker
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_freqs = []
        self.idf = {}
        self.avg_doc_len = 0
        self.doc_lengths = []
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words (lowercase, alphanumeric only)"""
        if not text:
            return []
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return words
    
    def _get_document_text(self, job: Any) -> str:
        """
        Extract searchable text from a job object.
        Combines title, company, location, description, and keywords with weights.
        """
        parts = []
        
        # Title (highest weight - repeat 3x)
        if job.title:
            parts.extend([job.title] * 3)
        
        # Company name (medium weight - repeat 2x)
        if job.company:
            parts.extend([job.company] * 2)
        
        # Location (medium weight - repeat 2x)
        if job.location:
            parts.extend([job.location] * 2)
        
        # Job description (full weight)
        if job.jd_text:
            parts.append(job.jd_text)
        
        # Keywords (high weight - repeat 2x each)
        if job.jd_keywords:
            for keyword in job.jd_keywords:
                parts.extend([keyword] * 2)
        
        return " ".join(parts)
    
    def fit(self, jobs: List[Any]):
        """
        Fit the BM25 model on a collection of jobs.
        This precomputes document frequencies and IDF values.
        
        Args:
            jobs: List of Job objects to index
        """
        self.documents = []
        self.doc_lengths = []
        
        # Tokenize all documents
        for job in jobs:
            doc_text = self._get_document_text(job)
            tokens = self._tokenize(doc_text)
            self.documents.append(tokens)
            self.doc_lengths.append(len(tokens))
        
        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_len = sum(self.doc_lengths) / len(self.doc_lengths)
        else:
            self.avg_doc_len = 0
        
        # Calculate document frequencies (how many docs contain each term)
        self.doc_freqs = []
        all_terms = set()
        
        for doc_tokens in self.documents:
            term_counts = Counter(doc_tokens)
            self.doc_freqs.append(term_counts)
            all_terms.update(doc_tokens)
        
        # Calculate IDF (Inverse Document Frequency) for each term
        num_docs = len(self.documents)
        for term in all_terms:
            # Count how many documents contain this term
            doc_count = sum(1 for df in self.doc_freqs if term in df)
            # IDF formula: log((N - df + 0.5) / (df + 0.5))
            # Add 0.5 to avoid division by zero
            idf_value = math.log((num_docs - doc_count + 0.5) / (doc_count + 0.5) + 1.0)
            self.idf[term] = idf_value
    
    def score(self, query: str, doc_index: int) -> float:
        """
        Calculate BM25 score for a query against a document.
        
        Args:
            query: Search query string
            doc_index: Index of the document in the fitted documents
            
        Returns:
            BM25 relevance score
        """
        if doc_index >= len(self.documents):
            return 0.0
        
        query_terms = self._tokenize(query)
        doc_tokens = self.documents[doc_index]
        doc_len = self.doc_lengths[doc_index]
        term_freqs = self.doc_freqs[doc_index]
        
        score = 0.0
        
        for term in query_terms:
            if term not in self.idf:
                continue
            
            # Term frequency in this document
            tf = term_freqs.get(term, 0)
            
            if tf == 0:
                continue
            
            # BM25 formula:
            # score = IDF(term) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
            idf = self.idf[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len if self.avg_doc_len > 0 else 1))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def rank(self, jobs: List[Any], query: str, top_k: int = None) -> List[tuple]:
        """
        Rank jobs by relevance to query using BM25.
        
        Args:
            jobs: List of Job objects to rank
            query: Search query string
            top_k: Return only top K results (None = return all)
            
        Returns:
            List of tuples (job, score) sorted by score (descending)
        """
        # Fit the model on the jobs
        self.fit(jobs)
        
        # Score each job
        scored_jobs = []
        for idx, job in enumerate(jobs):
            score = self.score(query, idx)
            scored_jobs.append((job, score))
        
        # Sort by score (descending)
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K if specified
        if top_k:
            return scored_jobs[:top_k]
        
        return scored_jobs

