# Phase 11: RAG Evaluation System

## Overview

Phase 11 implements a comprehensive evaluation framework to benchmark and validate the RAG system's quality. It measures:

1. **Retrieval Quality** - Top-k retrieval relevance (Precision@3, MRR)
2. **Answer Grounding** - Checks if explanations are grounded in source documents
3. **Unsupported Topic Interception** - Validates that Phase 10 prevents LLM from making claims about unsupported topics
4. **RAG vs No-RAG Comparison** - Demonstrates improvements from using RAG

## Components

### 1. `rag_evaluation.py`
Main evaluation framework with the `RagEvaluator` class.

**Key Methods:**
- `evaluate_retrieval_quality(top_k=3)` - Measures Precision@K and MRR for ground-truth queries
- `evaluate_answer_grounding()` - Validates explanations are grounded in knowledge base
- `evaluate_unsupported_topic_interception()` - Checks Phase 10 safety guards work
- `compare_rag_vs_no_rag()` - Compares similarity scores with and without RAG
- `run_full_evaluation()` - Runs complete evaluation suite

**Outputs:**
- `evaluation_dataset.csv` - Representative test queries covering:
  - Specific food Q&A (with ground truth)
  - Open-ended semantic searches
  - Unsupported topics (should be intercepted)
- `evaluation_results.json` - Raw evaluation metrics

### 2. `evaluation_metrics.py`
Reusable metric calculation functions organized into four classes:

**RetrievalMetrics:**
- `precision_at_k()` - Fraction of retrieved items that are relevant
- `recall_at_k()` - Fraction of relevant items that were retrieved
- `mrr()` - Mean Reciprocal Rank (position of first relevant item)
- `ndcg_at_k()` - Normalized Discounted Cumulative Gain

**GroundednessMetrics:**
- `word_overlap()` - Word-level overlap between generated and source text
- `token_overlap()` - Overlap using meaningful tokens
- `contains_key_phrases()` - Check if generated text contains n-grams from source
- `detect_score_hallucination()` - Detect if explanation claims wrong score
- `detect_unsupported_claims()` - Detect claims about unsupported topics

**CoverageMetrics:**
- `calculate_coverage()` - Query coverage and confidence statistics
- `coverage_by_category()` - Break down metrics by food category

**ErrorAnalysis:**
- `categorize_failures()` - Categorize failure types
- `find_error_patterns()` - Find patterns in failures

### 3. `evaluation_report.py`
Human-readable report generation with RAG vs No-RAG comparison.

**Key Methods:**
- `generate_summary_report()` - High-level overview with pass/fail criteria
- `generate_detailed_report()` - Query drill-down analysis
- `generate_comparison_analysis()` - RAG vs No-RAG performance comparison
- `save_reports()` - Save all reports to text files
- `generate_json_report()` - Structured JSON output for programmatic use

**Outputs:**
- `evaluation_report_summary.txt` - Executive summary
- `evaluation_report_detailed.txt` - Detailed query-by-query results
- `evaluation_report_comparison.txt` - RAG vs No-RAG analysis
- `evaluation_report_structured.json` - Programmatic JSON format

## Success Criteria

The system aims to meet these evaluation targets:

| Metric | Target | Definition |
|--------|--------|-----------|
| **Retrieval Precision@3** | ≥ 85% | Correct food retrieved in top 3 results |
| **Answer Grounding Score** | ≥ 90% | Explanations grounded in knowledge base (no hallucinations) |
| **Unsupported Topic Interception** | ≥ 95% | Ingredient/nutrition/allergen questions blocked before LLM |
| **RAG Confidence Gain** | ≥ 30% | Average improvement from using RAG vs no-RAG baseline |
| **Query Coverage** | ≥ 80% | Queries with similarity scores above threshold |

## Usage

### Quick Start

1. **Run full evaluation:**
```bash
python rag_evaluation.py
```

This will:
- Create `evaluation_dataset.csv` with representative test queries
- Run all evaluation metrics
- Save results to `evaluation_results.json`

2. **Generate reports:**
```bash
python evaluation_report.py
```

This will:
- Load `evaluation_results.json`
- Generate summary, detailed, and comparison reports
- Save to text and JSON files
- Print summary to console

### Advanced Usage

```python
from rag_evaluation import RagEvaluator
from evaluation_report import EvaluationReportGenerator

# Run evaluation
evaluator = RagEvaluator()
results = evaluator.run_full_evaluation()

# Generate reports
generator = EvaluationReportGenerator(results)
print(generator.generate_summary_report())
files = generator.save_reports()
```

## Test Dataset Format

`evaluation_dataset.csv` contains:

| Column | Description |
|--------|-------------|
| `query` | Test query/question |
| `query_type` | Type: specific_food_qa, semantic_search, or unsupported_topic |
| `expected_food_id` | Food ID if ground truth available (null for semantic searches) |
| `ground_truth_available` | Boolean: true if expected_food_id is reliable |
| `category` | Food category or query category |
| `should_be_intercepted` | Boolean: true for unsupported topics |

## Integration with Earlier Phases

Phase 11 leverages all previous phases:

- **Phase 6** (`retrieval.py`) - `HybridRetriever` for search
- **Phase 7-8b** (`rag_pipeline.py`) - Core RAG: `explain_recommendation()` and `answer_food_question()`
- **Phase 9** (`explanation_service.py`) - Explanation validation
- **Phase 10** (`food_info_layer.py`) - Safety guards and unsupported topic detection

## Failure Analysis

Common failure modes tracked:

1. **No Results** - Query returned no retrieval results
2. **Low Similarity** - Retrieved documents have low similarity scores
3. **Hallucination** - LLM invented information not in source
4. **Score Hallucination** - LLM stated wrong score/rating
5. **Unsupported Claims** - LLM discussed ingredients/nutrition/allergens
6. **Missed Interception** - Unsupported topic wasn't blocked

## Performance Insights

The evaluation framework provides:

- **Per-category breakdown** - Performance varies by food type/category
- **Similarity score distribution** - Helps understand confidence levels
- **Common failure patterns** - Identifies systematic issues
- **Query complexity analysis** - Which query types succeed/fail
- **Grounding evidence** - Specific examples of hallucinations

## Next Steps

After Phase 11 evaluation:

1. **Review metrics** - Check if all targets met
2. **Analyze failures** - Investigate low-performing categories
3. **Iterate** - Adjust retrieval parameters or knowledge base if needed
4. **Document results** - Keep reports for tracking improvements
5. **Continuous monitoring** - Use this framework for ongoing validation

---

**Phase 11 Status**: ✓ Evaluation System Complete
