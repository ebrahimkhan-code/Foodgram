"""
Phase 11: Evaluation Metrics
Reusable metric calculation functions for RAG system evaluation.
"""

import numpy as np
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import re


class RetrievalMetrics:
    """Calculate retrieval quality metrics."""
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: Set[str], k: int = 3) -> float:
        """
        Precision@K: Fraction of retrieved items that are relevant.
        
        Args:
            retrieved: List of retrieved food IDs in rank order
            relevant: Set of relevant/expected food IDs
            k: Cutoff for top-k
        
        Returns:
            Precision score (0.0 to 1.0)
        """
        top_k = retrieved[:k]
        relevant_retrieved = len([item for item in top_k if item in relevant])
        return relevant_retrieved / k if k > 0 else 0.0
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: Set[str], k: int = 3) -> float:
        """
        Recall@K: Fraction of relevant items that were retrieved.
        
        Args:
            retrieved: List of retrieved food IDs in rank order
            relevant: Set of relevant/expected food IDs
            k: Cutoff for top-k
        
        Returns:
            Recall score (0.0 to 1.0)
        """
        if len(relevant) == 0:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_retrieved = len([item for item in top_k if item in relevant])
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def mrr(retrieved: List[str], relevant: Set[str]) -> float:
        """
        Mean Reciprocal Rank: Inverse of rank position of first relevant item.
        
        Args:
            retrieved: List of retrieved food IDs in rank order
            relevant: Set of relevant/expected food IDs
        
        Returns:
            MRR score (0.0 to 1.0)
        """
        for idx, item in enumerate(retrieved):
            if item in relevant:
                return 1.0 / (idx + 1)
        return 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevant: Set[str], k: int = 3) -> float:
        """
        Normalized Discounted Cumulative Gain@K.
        
        Args:
            retrieved: List of retrieved food IDs in rank order
            relevant: Set of relevant/expected food IDs
            k: Cutoff for top-k
        
        Returns:
            NDCG score (0.0 to 1.0)
        """
        top_k = retrieved[:k]
        
        # DCG calculation
        dcg = 0.0
        for idx, item in enumerate(top_k):
            relevance = 1.0 if item in relevant else 0.0
            dcg += relevance / np.log2(idx + 2)  # log2(idx + 2) for position
        
        # IDCG (ideal DCG)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))
        
        return dcg / idcg if idcg > 0 else 0.0


class GroundednessMetrics:
    """Evaluate answer grounding and hallucination detection."""
    
    @staticmethod
    def word_overlap(generated_text: str, source_text: str) -> float:
        """
        Calculate word-level overlap between generated and source text.
        
        Args:
            generated_text: LLM-generated answer
            source_text: Source knowledge base text
        
        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        if not generated_text or not source_text:
            return 0.0
        
        gen_words = set(generated_text.lower().split())
        src_words = set(source_text.lower().split())
        
        overlap = gen_words & src_words
        
        # Use Jaccard similarity
        if len(gen_words | src_words) == 0:
            return 0.0
        
        return len(overlap) / len(gen_words | src_words)
    
    @staticmethod
    def token_overlap(generated_text: str, source_text: str, min_token_length: int = 4) -> float:
        """
        Calculate overlap using meaningful tokens (words >= min_token_length).
        Filters out stopwords and short tokens.
        
        Args:
            generated_text: LLM-generated answer
            source_text: Source knowledge base text
            min_token_length: Minimum token length to consider
        
        Returns:
            Token overlap ratio (0.0 to 1.0)
        """
        if not generated_text or not source_text:
            return 0.0
        
        # Extract meaningful tokens
        gen_tokens = set(
            token.lower() for token in generated_text.split()
            if len(token) >= min_token_length and token.isalpha()
        )
        src_tokens = set(
            token.lower() for token in source_text.split()
            if len(token) >= min_token_length and token.isalpha()
        )
        
        if len(gen_tokens) == 0:
            return 0.0
        
        overlap = gen_tokens & src_tokens
        return len(overlap) / len(gen_tokens)
    
    @staticmethod
    def contains_key_phrases(generated_text: str, source_text: str, 
                            phrase_length: int = 2) -> float:
        """
        Check if generated text contains n-grams from source text.
        
        Args:
            generated_text: LLM-generated answer
            source_text: Source knowledge base text
            phrase_length: Length of n-grams to extract
        
        Returns:
            Phrase overlap ratio (0.0 to 1.0)
        """
        if not generated_text or not source_text:
            return 0.0
        
        # Extract n-grams
        def get_ngrams(text, n):
            words = text.lower().split()
            return set(tuple(words[i:i+n]) for i in range(len(words) - n + 1))
        
        gen_ngrams = get_ngrams(generated_text, phrase_length)
        src_ngrams = get_ngrams(source_text, phrase_length)
        
        if len(gen_ngrams) == 0:
            return 0.0
        
        overlap = gen_ngrams & src_ngrams
        return len(overlap) / len(gen_ngrams)
    
    @staticmethod
    def detect_score_hallucination(generated_text: str, 
                                   expected_score_range: Tuple[float, float]) -> bool:
        """
        Detect if explanation claims a score outside the expected range.
        
        Args:
            generated_text: LLM-generated explanation
            expected_score_range: (min, max) expected score range
        
        Returns:
            True if hallucination detected (score outside range)
        """
        # Find numeric scores in the text (e.g., "0.85", "85%", "9.2/10")
        score_patterns = [
            r'(\d+\.?\d*)\s*(?:/\s*10|\s*out of\s*10|%)?',  # Decimal or percentage
            r'score\s*(?:is|of|:)?\s*(\d+\.?\d*)',  # "score is 0.85"
            r'rating\s*(?:is|of|:)?\s*(\d+\.?\d*)',  # "rating is 0.85"
        ]
        
        scores_found = []
        for pattern in score_patterns:
            matches = re.findall(pattern, generated_text.lower())
            scores_found.extend([float(m) for m in matches])
        
        min_expected, max_expected = expected_score_range
        
        # Check if any claimed score falls outside expected range
        for score in scores_found:
            # Normalize to 0-1 range if needed
            if score > 10:
                score = score / 100  # Convert percentage
            
            if score < min_expected or score > max_expected:
                return True
        
        return False
    
    @staticmethod
    def detect_unsupported_claims(generated_text: str, 
                                  unsupported_topics: List[str]) -> List[str]:
        """
        Detect if explanation makes claims about unsupported topics.
        
        Args:
            generated_text: LLM-generated explanation
            unsupported_topics: List of unsupported topic keywords
                              (e.g., ['ingredients', 'allergens', 'vegan'])
        
        Returns:
            List of detected unsupported claims
        """
        detected = []
        
        for topic in unsupported_topics:
            # Case-insensitive search
            if re.search(r'\b' + topic + r'\b', generated_text, re.IGNORECASE):
                detected.append(topic)
        
        return detected


class CoverageMetrics:
    """Evaluate system coverage and confidence."""
    
    @staticmethod
    def calculate_coverage(similarity_scores: List[float], threshold: float) -> Dict:
        """
        Calculate query coverage and confidence statistics.
        
        Args:
            similarity_scores: List of similarity scores
            threshold: Confidence threshold (e.g., 0.3)
        
        Returns:
            Dict with coverage metrics
        """
        if not similarity_scores:
            return {'coverage': 0.0, 'avg_similarity': 0.0, 'high_confidence': 0}
        
        scores = np.array(similarity_scores)
        high_confidence = np.sum(scores >= threshold)
        
        return {
            'coverage': len(similarity_scores),
            'avg_similarity': float(np.mean(scores)),
            'high_confidence': int(high_confidence),
            'high_confidence_rate': float(high_confidence / len(scores)),
            'min_similarity': float(np.min(scores)),
            'max_similarity': float(np.max(scores)),
            'std_similarity': float(np.std(scores))
        }
    
    @staticmethod
    def coverage_by_category(queries: List[Dict], category_field: str = 'category') -> Dict:
        """
        Break down coverage metrics by category.
        
        Args:
            queries: List of query dicts with results
            category_field: Field name for category
        
        Returns:
            Dict with per-category metrics
        """
        categories = defaultdict(lambda: {'total': 0, 'successful': 0})
        
        for query in queries:
            category = query.get(category_field, 'Unknown')
            categories[category]['total'] += 1
            if query.get('retrieved_successfully', False):
                categories[category]['successful'] += 1
        
        # Calculate rates
        for category in categories:
            total = categories[category]['total']
            successful = categories[category]['successful']
            categories[category]['success_rate'] = (
                successful / total if total > 0 else 0.0
            )
        
        return dict(categories)


class ErrorAnalysis:
    """Analyze and categorize failure modes."""
    
    @staticmethod
    def categorize_failures(failures: List[Dict]) -> Dict[str, int]:
        """
        Categorize retrieval/answer failures.
        
        Args:
            failures: List of failed queries with metadata
        
        Returns:
            Dict with failure type counts
        """
        categories = defaultdict(int)
        
        for failure in failures:
            # Infer failure type
            if failure.get('no_results'):
                categories['no_results'] += 1
            elif failure.get('low_similarity'):
                categories['low_similarity'] += 1
            elif failure.get('hallucination'):
                categories['hallucination'] += 1
            elif failure.get('unsupported_topic'):
                categories['unsupported_topic'] += 1
            else:
                categories['unknown'] += 1
        
        return dict(categories)
    
    @staticmethod
    def find_error_patterns(failures: List[Dict]) -> Dict[str, List[str]]:
        """
        Find patterns in failures (e.g., common query types that fail).
        
        Args:
            failures: List of failed queries
        
        Returns:
            Dict mapping failure patterns to example queries
        """
        patterns = defaultdict(list)
        
        for failure in failures:
            pattern_key = f"{failure.get('query_type')}_{failure.get('failure_reason')}"
            patterns[pattern_key].append(failure.get('query', ''))
        
        return dict(patterns)
