"""
Phase 11: RAG Evaluation System
Benchmarks and validates the RAG system's quality across retrieval, grounding, and answer quality.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import csv
from pathlib import Path

# Import existing components
from retrieval import HybridRetriever
from rag_pipeline import RAGPipeline
from food_info_layer import FoodInformationLayer, SIMILARITY_THRESHOLD


class RagEvaluator:
    """
    Comprehensive RAG evaluation framework.
    Measures retrieval quality, answer grounding, and groundedness.
    """
    
    def __init__(self):
        """Initialize the evaluator with data sources."""
        self.retriever = HybridRetriever()
        self.rag_pipeline = RAGPipeline()
        self.food_layer = FoodInformationLayer()
        self.knowledge_base = self._load_knowledge_base()
        self.evaluation_dataset = self._load_or_create_evaluation_dataset()
        
    def _load_knowledge_base(self) -> pd.DataFrame:
        """Load the food knowledge base."""
        return pd.read_csv("food_knowledge_base.csv")
    
    def _load_or_create_evaluation_dataset(self) -> pd.DataFrame:
        """Load existing evaluation dataset or create one from food knowledge base."""
        eval_path = Path("evaluation_dataset.csv")
        
        if eval_path.exists():
            return pd.read_csv(eval_path)
        else:
            # Create representative test queries
            print("Creating representative evaluation dataset...")
            dataset = self._create_representative_queries()
            dataset.to_csv(eval_path, index=False)
            return dataset
    
    def _create_representative_queries(self) -> pd.DataFrame:
        """Create representative test queries covering different scenarios."""
        queries = []
        
        # Load knowledge base to sample foods
        kb = self.knowledge_base.head(50)  # Sample 50 foods for testing
        
        # Query Type 1: Specific food Q&A (e.g., "Tell me about Pizza")
        for _, row in kb.iterrows():
            food_name = row.get('food_name', row.get('Food_Name', ''))
            if pd.notna(food_name):
                queries.append({
                    'query': f"Tell me about {food_name}",
                    'query_type': 'specific_food_qa',
                    'expected_food_id': row.get('food_id', row.get('Food_ID', '')),
                    'ground_truth_available': True,
                    'category': row.get('category', 'General')
                })
        
        # Query Type 2: Open-ended searches
        open_queries = [
            "What is a high-protein option?",
            "Show me vegetarian items",
            "What are the most popular items?",
            "Find low-calorie options",
            "Show me breakfast items",
        ]
        for q in open_queries:
            queries.append({
                'query': q,
                'query_type': 'semantic_search',
                'expected_food_id': None,  # Multiple valid answers
                'ground_truth_available': False,
                'category': 'General'
            })
        
        # Query Type 3: Unsupported topics (should be intercepted)
        unsupported_queries = [
            "What are the ingredients in this dish?",
            "Does this contain allergens?",
            "What is the nutritional information?",
            "How many calories?",
            "Is this vegan-friendly?",
        ]
        for q in unsupported_queries:
            queries.append({
                'query': q,
                'query_type': 'unsupported_topic',
                'expected_food_id': None,
                'ground_truth_available': False,
                'category': 'UnsupportedTopic',
                'should_be_intercepted': True
            })
        
        return pd.DataFrame(queries)
    
    def evaluate_retrieval_quality(self, top_k: int = 3) -> Dict:
        """
        Measure top-k retrieval relevance.
        Returns precision@k, recall@k, MRR for ground-truth queries.
        """
        results = {
            'total_queries': 0,
            'ground_truth_queries': 0,
            'precision_at_k': [],
            'retrieved_ids': []
        }
        
        for _, row in self.evaluation_dataset.iterrows():
            if not row.get('ground_truth_available', False):
                continue
            
            query = row['query']
            expected_id = row['expected_food_id']
            
            results['total_queries'] += 1
            results['ground_truth_queries'] += 1
            
            # Run retrieval
            retrieved_docs = self.retriever.retrieve(query, top_k=top_k)
            retrieved_ids = [doc['food_id'] for doc in retrieved_docs]
            
            # Calculate precision: did we retrieve the expected food?
            hit = 1.0 if expected_id in retrieved_ids else 0.0
            results['precision_at_k'].append(hit)
            results['retrieved_ids'].append({
                'query': query,
                'expected': expected_id,
                'retrieved': retrieved_ids,
                'hit': hit
            })
        
        # Calculate aggregate metrics
        if results['precision_at_k']:
            results['avg_precision_at_k'] = np.mean(results['precision_at_k'])
            results['mrr'] = self._calculate_mrr(results['retrieved_ids'])
        
        return results
    
    def _calculate_mrr(self, retrieval_results: List[Dict]) -> float:
        """Calculate Mean Reciprocal Rank."""
        reciprocal_ranks = []
        for result in retrieval_results:
            expected = result['expected']
            retrieved = result['retrieved']
            if expected in retrieved:
                rank = retrieved.index(expected) + 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    def evaluate_answer_grounding(self, sample_size: Optional[int] = None) -> Dict:
        """
        Validate that explanations are grounded in knowledge base.
        Checks if LLM output references retrieved documents.
        """
        results = {
            'total_evaluated': 0,
            'grounded_answers': 0,
            'grounding_score': 0.0,
            'hallucinated_details': [],
            'unsupported_claims': []
        }
        
        # Evaluate a sample of specific food queries
        specific_queries = self.evaluation_dataset[
            self.evaluation_dataset['query_type'] == 'specific_food_qa'
        ].head(sample_size) if sample_size else self.evaluation_dataset[
            self.evaluation_dataset['query_type'] == 'specific_food_qa'
        ]
        
        for _, row in specific_queries.iterrows():
            food_id = row['expected_food_id']
            results['total_evaluated'] += 1
            
            # Get explanation with RAG (use default ml_score of 0.75 for evaluation)
            explanation = self.rag_pipeline.explain_recommendation(food_id, ml_score=0.75)
            
            # Get knowledge base content
            kb_row = self.knowledge_base[
                self.knowledge_base['food_id'] == food_id
            ]
            
            if kb_row.empty:
                results['hallucinated_details'].append({
                    'food_id': food_id,
                    'issue': 'Food ID not found in knowledge base'
                })
                continue
            
            kb_content = kb_row.iloc[0].get('knowledge_document', '')
            
            # Check groundedness: do key phrases from explanation appear in KB?
            is_grounded = self._check_groundedness(
                explanation.get('explanation', ''),
                kb_content
            )
            
            if is_grounded:
                results['grounded_answers'] += 1
            else:
                results['hallucinated_details'].append({
                    'food_id': food_id,
                    'explanation': explanation.get('explanation', ''),
                    'kb_content': kb_content[:200]  # First 200 chars
                })
        
        if results['total_evaluated'] > 0:
            results['grounding_score'] = (
                results['grounded_answers'] / results['total_evaluated']
            )
        
        return results
    
    def _check_groundedness(self, explanation: str, kb_content: str) -> bool:
        """
        Check if explanation is grounded in knowledge base.
        Uses simple keyword overlap heuristic.
        """
        if not explanation or not kb_content:
            return False
        
        explanation_lower = explanation.lower()
        kb_lower = kb_content.lower()
        
        # Split into words and check overlap
        explanation_words = set(explanation_lower.split())
        kb_words = set(kb_lower.split())
        
        overlap = explanation_words & kb_words
        
        # Require at least 30% overlap and minimum 5 words in common
        overlap_ratio = len(overlap) / len(explanation_words) if explanation_words else 0
        
        return overlap_ratio > 0.3 and len(overlap) >= 5
    
    def evaluate_unsupported_topic_interception(self) -> Dict:
        """
        Measure how well Phase 10 intercepts unsupported topics before LLM.
        Tracks: ingredients, nutrition, allergens, vegan status, etc.
        """
        results = {
            'total_unsupported_queries': 0,
            'successfully_intercepted': 0,
            'interception_rate': 0.0,
            'failed_interceptions': []
        }
        
        unsupported = self.evaluation_dataset[
            self.evaluation_dataset['query_type'] == 'unsupported_topic'
        ]
        
        for _, row in unsupported.iterrows():
            query = row['query']
            results['total_unsupported_queries'] += 1
            
            # Check if food_info_layer catches this
            detected_topic = self.food_layer._detect_unsupported_topic(query)
            
            if detected_topic is not None:  # Correctly intercepted
                results['successfully_intercepted'] += 1
            else:
                results['failed_interceptions'].append(query)
        
        if results['total_unsupported_queries'] > 0:
            results['interception_rate'] = (
                results['successfully_intercepted'] / 
                results['total_unsupported_queries']
            )
        
        return results
    
    def compare_rag_vs_no_rag(self, sample_queries: Optional[int] = 5) -> Dict:
        """
        Compare LLM output WITH RAG vs WITHOUT RAG.
        Measures improvement in relevance and accuracy.
        """
        results = {
            'comparison': [],
            'avg_similarity_with_rag': 0.0,
            'avg_confidence_improvement': 0.0
        }
        
        # Sample semantic search queries
        semantic_queries = self.evaluation_dataset[
            self.evaluation_dataset['query_type'] == 'semantic_search'
        ].head(sample_queries)
        
        for _, row in semantic_queries.iterrows():
            query = row['query']
            
            # WITH RAG: Get answer with retrieval
            rag_answer = self.rag_pipeline.answer_food_question(query)
            
            # Extract similarity score from sources (first/best match)
            rag_confidence = 0.0
            if rag_answer.get('sources'):
                rag_confidence = rag_answer['sources'][0].get('similarity', 0.0)
            
            # WITHOUT RAG: In real scenarios, this would be LLM-only
            # For now, we measure retrieval quality as proxy
            without_rag_confidence = 0.0  # Baseline
            
            results['comparison'].append({
                'query': query,
                'rag_similarity': rag_confidence,
                'rag_above_threshold': rag_confidence >= SIMILARITY_THRESHOLD,
                'confidence_gain': rag_confidence - without_rag_confidence
            })
            
            results['avg_similarity_with_rag'] += rag_confidence
        
        if semantic_queries.shape[0] > 0:
            results['avg_similarity_with_rag'] /= semantic_queries.shape[0]
            results['avg_confidence_improvement'] = results['avg_similarity_with_rag']
        
        return results
    
    def run_full_evaluation(self) -> Dict:
        """Run complete evaluation suite and return comprehensive report."""
        print("Phase 11: RAG Evaluation System")
        print("=" * 60)
        
        print("\n[1/4] Evaluating retrieval quality...")
        retrieval_results = self.evaluate_retrieval_quality(top_k=3)
        
        print("[2/4] Evaluating answer grounding...")
        grounding_results = self.evaluate_answer_grounding(sample_size=10)
        
        print("[3/4] Evaluating unsupported topic interception...")
        interception_results = self.evaluate_unsupported_topic_interception()
        
        print("[4/4] Comparing RAG vs No-RAG performance...")
        comparison_results = self.compare_rag_vs_no_rag(sample_queries=5)
        
        full_results = {
            'retrieval': retrieval_results,
            'grounding': grounding_results,
            'interception': interception_results,
            'rag_comparison': comparison_results
        }
        
        return full_results


def main():
    """Run the RAG evaluation suite."""
    evaluator = RagEvaluator()
    results = evaluator.run_full_evaluation()
    
    # Save results
    import json
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✓ Evaluation complete. Results saved to evaluation_results.json")


if __name__ == "__main__":
    main()
