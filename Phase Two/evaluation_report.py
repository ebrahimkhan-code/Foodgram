"""
Phase 11: Evaluation Report Generation
Creates human-readable reports comparing RAG vs No-RAG performance.
Includes drill-down analysis and failure mode categorization.
"""

import json
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import numpy as np

from evaluation_metrics import (
    RetrievalMetrics,
    GroundednessMetrics,
    CoverageMetrics,
    ErrorAnalysis
)


class EvaluationReportGenerator:
    """Generate comprehensive evaluation reports with multiple views."""
    
    def __init__(self, evaluation_results: Dict):
        """
        Initialize report generator with evaluation results.
        
        Args:
            evaluation_results: Dict from rag_evaluation.run_full_evaluation()
        """
        self.results = evaluation_results
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_summary_report(self) -> str:
        """Generate high-level summary report."""
        report = []
        report.append("=" * 80)
        report.append("RAG SYSTEM EVALUATION REPORT - PHASE 11")
        report.append("=" * 80)
        report.append(f"Generated: {self.timestamp}\n")
        
        # Section 1: Retrieval Quality
        retrieval = self.results.get('retrieval', {})
        report.append("SECTION 1: RETRIEVAL QUALITY")
        report.append("-" * 80)
        report.append(f"Total Queries Evaluated: {retrieval.get('total_queries', 0)}")
        report.append(f"Queries with Ground Truth: {retrieval.get('ground_truth_queries', 0)}")
        
        if 'avg_precision_at_k' in retrieval:
            report.append(f"Precision@3: {retrieval['avg_precision_at_k']:.2%}")
            report.append(f"Mean Reciprocal Rank (MRR): {retrieval.get('mrr', 0):.2%}")
        
        if retrieval.get('retrieved_ids'):
            correct = sum(1 for r in retrieval['retrieved_ids'] if r['hit'] == 1.0)
            report.append(f"Correct Retrievals: {correct}/{len(retrieval['retrieved_ids'])}")
        report.append("")
        
        # Section 2: Answer Grounding
        grounding = self.results.get('grounding', {})
        report.append("SECTION 2: ANSWER GROUNDING & HALLUCINATION DETECTION")
        report.append("-" * 80)
        report.append(f"Answers Evaluated: {grounding.get('total_evaluated', 0)}")
        report.append(f"Grounded Answers: {grounding.get('grounded_answers', 0)}")
        report.append(f"Grounding Score: {grounding.get('grounding_score', 0):.2%}")
        
        hallucinations = grounding.get('hallucinated_details', [])
        report.append(f"Hallucination Instances: {len(hallucinations)}")
        report.append("")
        
        # Section 3: Unsupported Topic Interception
        interception = self.results.get('interception', {})
        report.append("SECTION 3: UNSUPPORTED TOPIC INTERCEPTION")
        report.append("-" * 80)
        report.append(f"Unsupported Queries: {interception.get('total_unsupported_queries', 0)}")
        report.append(f"Successfully Intercepted: {interception.get('successfully_intercepted', 0)}")
        report.append(f"Interception Rate: {interception.get('interception_rate', 0):.2%}")
        
        if interception.get('failed_interceptions'):
            report.append(f"Failed Interceptions: {len(interception['failed_interceptions'])}")
            for query in interception['failed_interceptions'][:3]:
                report.append(f"  - {query}")
        report.append("")
        
        # Section 4: RAG vs No-RAG Comparison
        comparison = self.results.get('rag_comparison', {})
        report.append("SECTION 4: RAG VS NO-RAG COMPARISON")
        report.append("-" * 80)
        report.append(f"Average Similarity with RAG: {comparison.get('avg_similarity_with_rag', 0):.2%}")
        report.append(f"Average Confidence Gain: {comparison.get('avg_confidence_improvement', 0):.2%}")
        
        if comparison.get('comparison'):
            queries_above_threshold = sum(
                1 for c in comparison['comparison'] 
                if c.get('rag_above_threshold', False)
            )
            report.append(f"Queries Above Threshold: {queries_above_threshold}/{len(comparison['comparison'])}")
        report.append("")
        
        # Overall assessment
        report.append("OVERALL ASSESSMENT")
        report.append("-" * 80)
        assessment = self._generate_assessment()
        report.extend(assessment)
        
        return "\n".join(report)
    
    def _generate_assessment(self) -> List[str]:
        """Generate overall assessment with pass/fail criteria."""
        assessment = []
        
        retrieval = self.results.get('retrieval', {})
        grounding = self.results.get('grounding', {})
        interception = self.results.get('interception', {})
        
        metrics = {
            'Retrieval Precision@3': (
                retrieval.get('avg_precision_at_k', 0), 
                0.85, 
                "✓" if retrieval.get('avg_precision_at_k', 0) >= 0.85 else "✗"
            ),
            'Answer Grounding Score': (
                grounding.get('grounding_score', 0), 
                0.90, 
                "✓" if grounding.get('grounding_score', 0) >= 0.90 else "✗"
            ),
            'Unsupported Topic Interception': (
                interception.get('interception_rate', 0), 
                0.95, 
                "✓" if interception.get('interception_rate', 0) >= 0.95 else "✗"
            )
        }
        
        for metric_name, (actual, target, status) in metrics.items():
            assessment.append(f"{status} {metric_name}: {actual:.2%} (target: {target:.2%})")
        
        # Pass/Fail summary
        assessment.append("")
        all_pass = all(metrics[m][2] == "✓" for m in metrics)
        if all_pass:
            assessment.append("🎉 RAG SYSTEM PASSES ALL EVALUATION CRITERIA")
        else:
            assessment.append("⚠️  Some metrics below target - review sections above")
        
        return assessment
    
    def generate_detailed_report(self) -> str:
        """Generate detailed report with per-query drill-down."""
        report = []
        report.append("=" * 80)
        report.append("DETAILED EVALUATION REPORT - QUERY DRILL-DOWN")
        report.append("=" * 80)
        report.append(f"Generated: {self.timestamp}\n")
        
        retrieval = self.results.get('retrieval', {})
        
        if retrieval.get('retrieved_ids'):
            report.append("RETRIEVAL QUERY DETAILS")
            report.append("-" * 80)
            
            for idx, query_result in enumerate(retrieval['retrieved_ids'], 1):
                report.append(f"\nQuery {idx}:")
                report.append(f"  Query Text: {query_result['query']}")
                report.append(f"  Expected Food ID: {query_result['expected']}")
                report.append(f"  Retrieved (Top 3): {query_result['retrieved']}")
                report.append(f"  Result: {'✓ HIT' if query_result['hit'] else '✗ MISS'}")
        
        grounding = self.results.get('grounding', {})
        if grounding.get('hallucinated_details'):
            report.append("\n" + "=" * 80)
            report.append("HALLUCINATION INSTANCES")
            report.append("-" * 80)
            
            for idx, hallucination in enumerate(grounding['hallucinated_details'][:5], 1):
                report.append(f"\nHallucination {idx}:")
                report.append(f"  Food ID: {hallucination.get('food_id', 'N/A')}")
                report.append(f"  Generated Explanation: {hallucination.get('explanation', 'N/A')[:100]}...")
                report.append(f"  Expected KB Content: {hallucination.get('kb_content', 'N/A')[:100]}...")
        
        return "\n".join(report)
    
    def generate_comparison_analysis(self) -> str:
        """Generate detailed RAG vs No-RAG comparison analysis."""
        report = []
        report.append("=" * 80)
        report.append("RAG VS NO-RAG PERFORMANCE ANALYSIS")
        report.append("=" * 80)
        report.append(f"Generated: {self.timestamp}\n")
        
        comparison = self.results.get('rag_comparison', {})
        
        report.append("QUERY-BY-QUERY COMPARISON")
        report.append("-" * 80)
        
        if comparison.get('comparison'):
            for idx, query_comp in enumerate(comparison['comparison'], 1):
                report.append(f"\nQuery {idx}: {query_comp['query']}")
                report.append(f"  RAG Similarity Score: {query_comp['rag_similarity']:.2%}")
                report.append(f"  Above Threshold: {'Yes' if query_comp['rag_above_threshold'] else 'No'}")
                report.append(f"  Confidence Gain (vs No-RAG): {query_comp['confidence_gain']:.2%}")
        
        report.append("\n" + "=" * 80)
        report.append("SUMMARY STATISTICS")
        report.append("-" * 80)
        report.append(f"Average RAG Similarity: {comparison.get('avg_similarity_with_rag', 0):.2%}")
        report.append(f"Average Confidence Improvement: {comparison.get('avg_confidence_improvement', 0):.2%}")
        
        if comparison.get('comparison'):
            above_threshold = sum(
                1 for c in comparison['comparison'] 
                if c.get('rag_above_threshold', False)
            )
            report.append(f"Queries Meeting Threshold: {above_threshold}/{len(comparison['comparison'])}")
        
        return "\n".join(report)
    
    def save_reports(self, output_dir: str = ".") -> Dict[str, str]:
        """
        Save all reports to files.
        
        Args:
            output_dir: Directory to save reports in
        
        Returns:
            Dict mapping report types to file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        reports = {
            'summary': self.generate_summary_report(),
            'detailed': self.generate_detailed_report(),
            'comparison': self.generate_comparison_analysis()
        }
        
        files = {}
        for report_type, content in reports.items():
            filename = output_dir / f"evaluation_report_{report_type}.txt"
            with open(filename, 'w') as f:
                f.write(content)
            files[report_type] = str(filename)
        
        return files
    
    def generate_json_report(self) -> Dict:
        """Generate structured JSON report for programmatic use."""
        return {
            'timestamp': self.timestamp,
            'evaluation_results': self.results,
            'summary': {
                'retrieval_precision_at_k': self.results.get('retrieval', {}).get('avg_precision_at_k'),
                'retrieval_mrr': self.results.get('retrieval', {}).get('mrr'),
                'grounding_score': self.results.get('grounding', {}).get('grounding_score'),
                'interception_rate': self.results.get('interception', {}).get('interception_rate'),
                'avg_rag_similarity': self.results.get('rag_comparison', {}).get('avg_similarity_with_rag')
            }
        }


def main():
    """Generate reports from evaluation results."""
    # Load evaluation results
    results_file = Path("evaluation_results.json")
    if not results_file.exists():
        print("Error: evaluation_results.json not found. Run rag_evaluation.py first.")
        return
    
    with open(results_file) as f:
        results = json.load(f)
    
    # Generate reports
    generator = EvaluationReportGenerator(results)
    
    print("\n" + generator.generate_summary_report())
    
    # Save all reports
    files = generator.save_reports()
    print(f"\n✓ Reports saved:")
    for report_type, filepath in files.items():
        print(f"  - {report_type}: {filepath}")
    
    # Save JSON report
    json_report = generator.generate_json_report()
    json_file = Path("evaluation_report_structured.json")
    with open(json_file, 'w') as f:
        json.dump(json_report, f, indent=2, default=str)
    print(f"  - structured: {json_file}")


if __name__ == "__main__":
    main()
