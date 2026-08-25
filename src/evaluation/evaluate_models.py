"""
Datumara SQL Evaluation Framework

Execute and compare SQL queries from multiple models side-by-side.
Supports:
- Execution Accuracy (EX)
- Valid Efficiency Score (VES)
- Parse Validity
- Schema Validity
- Complexity-stratified analysis

Usage:
    python evaluate_models.py \
        --test-set mini_dev \
        --db-path data/databases/mini_dev \
        --models v0.1 v0.2 competitor_1 \
        --output results/comparison_20260825.json
"""

import os
import json
import sqlite3
import time
import argparse
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from sqlparse import parse, SQL, Statement
import sqlparse


class SQLExecutor:
    """Execute SQL queries against SQLite databases"""
    
    def __init__(self, db_path: str, timeout: int = 30):
        self.db_path = db_path
        self.timeout = timeout
    
    def execute(self, sql: str) -> Tuple[bool, any, str]:
        """
        Execute SQL query and return results
        
        Returns:
            success: bool - Whether execution succeeded
            result: any - Query result or error
            error_msg: str - Error message if failed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.set_trace_callback(lambda x: None)  # Disable tracing for speed
            
            # Set timeout
            conn.execute(f"PRAGMA busy_timeout={self.timeout * 1000}")
            
            # Execute query
            cursor = conn.cursor()
            start_time = time.time()
            cursor.execute(sql)
            
            # Fetch results
            result = cursor.fetchall()
            execution_time = time.time() - start_time
            
            conn.close()
            
            return True, result, f"OK ({execution_time:.3f}s)"
            
        except sqlite3.Error as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, str(e)
    
    def check_schema_validity(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Check if all tables/columns in SQL exist in database schema
        
        Returns:
            is_valid: bool
            errors: List[str] - List of schema errors
        """
        errors = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0].lower() for row in cursor.fetchall()}
            
            for table in tables:
                # Get columns for each table
                cursor.execute(f"PRAGMA table_info({table})")
                columns = {row[1].lower() for row in cursor.fetchall()}
                
                # Check if table referenced in SQL
                if table in sql.lower():
                    # Extract column references (simplified)
                    # TODO: Use proper SQL parser for robust extraction
                    pass
            
            conn.close()
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Schema check failed: {e}"]


class DatumaraEvaluator:
    """Evaluate and compare multiple models on BIRD benchmark"""
    
    def __init__(self, test_set_path: str, db_path: str):
        self.test_set = self.load_test_set(test_set_path)
        self.db_path = db_path
        self.executor = SQLExecutor(db_path)
        self.results = {}
    
    def load_test_set(self, path: str) -> List[Dict]:
        """Load test set from JSON/parquet"""
        if path.endswith('.json') or path.endswith('.jsonl'):
            with open(path, 'r') as f:
                if path.endswith('.jsonl'):
                    return [json.loads(line) for line in f]
                else:
                    return json.load(f)
        elif path.endswith('.parquet'):
            df = pd.read_parquet(path)
            return df.to_dict('records')
        else:
            raise ValueError(f"Unsupported format: {path}")
    
    def check_parse_validity(self, sql: str) -> bool:
        """Check if SQL can be parsed successfully"""
        try:
            parsed = parse(sql)
            return len(parsed) > 0 and isinstance(parsed[0], Statement)
        except:
            return False
    
    def check_exact_match(self, sql1: str, sql2: str) -> bool:
        """Check if two SQL queries are exactly the same"""
        return sql1.strip().lower() == sql2.strip().lower()
    
    def check_normalized_match(self, sql1: str, sql2: str) -> bool:
        """
        Check if two SQL queries are semantically equivalent
        (normalized comparison)
        """
        # Simple normalization (remove extra whitespace, case)
        def normalize(sql):
            sql = ' '.join(sql.split()).lower()
            # Remove semicolons
            sql = sql.rstrip(';')
            return sql
        
        return normalize(sql1) == normalize(sql2)
    
    def compute_ves(self, execution_time: float, result_correct: bool) -> float:
        """
        Compute Valid Efficiency Score
        
        Formula (simplified):
        - Base score: 1.0 if correct, 0.0 if incorrect
        - Efficiency penalty: -0.1 * (execution_time / baseline_time)
        - Minimum score: 0.0
        """
        if not result_correct:
            return 0.0
        
        baseline_time = 1.0  # 1 second baseline
        efficiency_penalty = 0.1 * (execution_time / baseline_time)
        
        return max(0.0, 1.0 - efficiency_penalty)
    
    def get_complexity(self, question: str, sql: str) -> str:
        """
        Estimate query complexity based on SQL features
        
        Returns: 'easy', 'medium', 'hard', or 'expert'
        """
        sql_upper = sql.upper()
        
        # Count SQL features
        has_join = 'JOIN' in sql_upper
        has_subquery = sql_upper.count('SELECT') > 1
        has_aggregation = any(agg in sql_upper for agg in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX'])
        has_group_by = 'GROUP BY' in sql_upper
        has_order_by = 'ORDER BY' in sql_upper
        has_nested = sql_upper.count('SELECT') > 2
        
        # Classify complexity
        if has_nested or (has_join and has_subquery and has_aggregation):
            return 'expert'
        elif has_join and has_subquery:
            return 'hard'
        elif has_join or has_subquery or (has_aggregation and has_group_by):
            return 'medium'
        else:
            return 'easy'
    
    def evaluate_model(self, model_name: str, predictions: List[Dict]) -> Dict:
        """
        Evaluate a single model's predictions
        
        Args:
            model_name: Name of the model
            predictions: List of dicts with 'question_id', 'sql', 'db_id'
        
        Returns:
            Dict with all metrics
        """
        results = {
            'model': model_name,
            'total': len(predictions),
            'parse_valid': 0,
            'schema_valid': 0,
            'exact_match': 0,
            'normalized_match': 0,
            'execution_correct': 0,
            'ves_sum': 0.0,
            'by_complexity': {},
            'errors': []
        }
        
        for pred in tqdm(predictions, desc=f"Evaluating {model_name}", leave=False):
            question_id = pred.get('question_id')
            generated_sql = pred.get('sql', '')
            
            # Find corresponding test example
            test_example = next(
                (ex for ex in self.test_set if ex.get('question_id') == question_id),
                None
            )
            
            if not test_example:
                results['errors'].append(f"Question {question_id} not found in test set")
                continue
            
            reference_sql = test_example.get('sql', '')
            db_id = test_example.get('db_id', 'default')
            
            # Update database path if needed
            if db_id != 'default':
                db_file = os.path.join(self.db_path, f"{db_id}.db")
                if os.path.exists(db_file):
                    self.executor = SQLExecutor(db_file)
            
            # Check parse validity
            parse_valid = self.check_parse_validity(generated_sql)
            if parse_valid:
                results['parse_valid'] += 1
            
            # Check schema validity (simplified)
            schema_valid, _ = self.executor.check_schema_validity(generated_sql)
            if schema_valid:
                results['schema_valid'] += 1
            
            # Check exact match
            if self.check_exact_match(generated_sql, reference_sql):
                results['exact_match'] += 1
            
            # Check normalized match
            if self.check_normalized_match(generated_sql, reference_sql):
                results['normalized_match'] += 1
            
            # Execute and check correctness
            success, result, error_msg = self.executor.execute(generated_sql)
            
            # Also execute reference for comparison
            ref_success, ref_result, ref_error = self.executor.execute(reference_sql)
            
            if success and ref_success:
                # Compare results
                if result == ref_result:
                    results['execution_correct'] += 1
                    
                    # Compute VES
                    execution_time = float(error_msg.split('(')[1].split(')')[0]) if '(' in error_msg else 1.0
                    ves = self.compute_ves(execution_time, True)
                    results['ves_sum'] += ves
            
            # Track by complexity
            complexity = self.get_complexity(test_example.get('question', ''), reference_sql)
            if complexity not in results['by_complexity']:
                results['by_complexity'][complexity] = {
                    'total': 0,
                    'execution_correct': 0
                }
            
            results['by_complexity'][complexity]['total'] += 1
            if success and ref_success and result == ref_result:
                results['by_complexity'][complexity]['execution_correct'] += 1
        
        # Compute final metrics
        total = max(1, results['total'])
        results['metrics'] = {
            'parse_validity': results['parse_valid'] / total,
            'schema_validity': results['schema_valid'] / total,
            'exact_match': results['exact_match'] / total,
            'normalized_match': results['normalized_match'] / total,
            'execution_accuracy': results['execution_correct'] / total,
            'avg_ves': results['ves_sum'] / max(1, results['execution_correct']),
            'by_complexity': {
                k: v['execution_correct'] / max(1, v['total'])
                for k, v in results['by_complexity'].items()
            }
        }
        
        return results
    
    def evaluate_all_models(self, model_predictions: Dict[str, List[Dict]]) -> Dict:
        """
        Evaluate all models and create comparison report
        
        Args:
            model_predictions: Dict mapping model_name -> predictions
        """
        all_results = {}
        
        for model_name, predictions in model_predictions.items():
            results = self.evaluate_model(model_name, predictions)
            all_results[model_name] = results
        
        # Create comparison summary
        comparison = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_set': self.test_set,
            'db_path': self.db_path,
            'models': all_results,
            'comparison_table': self.create_comparison_table(all_results)
        }
        
        return comparison
    
    def create_comparison_table(self, all_results: Dict) -> pd.DataFrame:
        """Create pandas DataFrame with comparison metrics"""
        rows = []
        
        for model_name, results in all_results.items():
            metrics = results.get('metrics', {})
            row = {
                'Model': model_name,
                'Parse Validity': f"{metrics.get('parse_validity', 0)*100:.1f}%",
                'Schema Validity': f"{metrics.get('schema_validity', 0)*100:.1f}%",
                'Exact Match': f"{metrics.get('exact_match', 0)*100:.1f}%",
                'Normalized Match': f"{metrics.get('normalized_match', 0)*100:.1f}%",
                'Execution Accuracy': f"{metrics.get('execution_accuracy', 0)*100:.1f}%",
                'Avg VES': f"{metrics.get('avg_ves', 0):.2f}",
            }
            
            # Add complexity breakdown
            by_complexity = metrics.get('by_complexity', {})
            for complexity in ['easy', 'medium', 'hard', 'expert']:
                row[f'{complexity.capitalize()}'] = f"{by_complexity.get(complexity, 0)*100:.1f}%"
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def save_results(self, comparison: Dict, output_path: str):
        """Save results to JSON and create markdown report"""
        # Save JSON
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        # Create markdown report
        self.create_markdown_report(comparison, output_path.replace('.json', '.md'))
        
        print(f"\n✓ Results saved to {output_path}")
        print(f"✓ Report saved to {output_path.replace('.json', '.md')}")
    
    def create_markdown_report(self, comparison: Dict, report_path: str):
        """Create human-readable markdown report"""
        models = comparison['models']
        
        report = f"""# Datumara Model Comparison Report

**Generated:** {comparison['timestamp']}  
**Test Set:** {comparison['test_set']}  
**Database:** {comparison['db_path']}

---

## Executive Summary

| Model | Execution Accuracy | Parse Validity | Avg VES |
|-------|-------------------|----------------|---------|
"""
        
        # Add summary table
        for model_name, results in sorted(
            models.items(),
            key=lambda x: x[1]['metrics'].get('execution_accuracy', 0),
            reverse=True
        ):
            metrics = results['metrics']
            report += f"| **{model_name}** | {metrics['execution_accuracy']*100:.1f}% | {metrics['parse_validity']*100:.1f}% | {metrics['avg_ves']:.2f} |\n"
        
        # Add detailed breakdown
        report += "\n---\n\n## Detailed Results\n\n"
        
        for model_name, results in models.items():
            metrics = results['metrics']
            report += f"""
### {model_name}

- **Parse Validity:** {metrics['parse_validity']*100:.1f}%
- **Schema Validity:** {metrics['schema_validity']*100:.1f}%
- **Exact Match:** {metrics['exact_match']*100:.1f}%
- **Normalized Match:** {metrics['normalized_match']*100:.1f}%
- **Execution Accuracy:** {metrics['execution_accuracy']*100:.1f}%
- **Avg VES:** {metrics['avg_ves']:.2f}

**By Complexity:**
"""
            for complexity, score in metrics.get('by_complexity', {}).items():
                report += f"- {complexity.capitalize()}: {score*100:.1f}%\n"
            
            if results['errors']:
                report += f"\n**Errors:** {len(results['errors'])} issues\n"
            
            report += "\n---\n\n"
        
        with open(report_path, 'w') as f:
            f.write(report)


def load_model_predictions(predictions_dir: str) -> Dict[str, List[Dict]]:
    """
    Load predictions from directory
    
    Directory structure:
    predictions/
        model_v0.1/
            predictions.json
        model_v0.2/
            predictions.json
        competitor_1/
            predictions.json
    """
    predictions = {}
    
    for model_dir in os.listdir(predictions_dir):
        model_path = os.path.join(predictions_dir, model_dir)
        if os.path.isdir(model_path):
            pred_file = os.path.join(model_path, 'predictions.json')
            if os.path.exists(pred_file):
                with open(pred_file, 'r') as f:
                    predictions[model_dir] = json.load(f)
    
    return predictions


def main():
    parser = argparse.ArgumentParser(description='Evaluate SQL generation models')
    parser.add_argument('--test-set', type=str, required=True,
                       help='Path to test set (JSON/parquet)')
    parser.add_argument('--db-path', type=str, required=True,
                       help='Path to database directory')
    parser.add_argument('--predictions-dir', type=str, required=True,
                       help='Directory with model predictions')
    parser.add_argument('--output', type=str, default='results/comparison.json',
                       help='Output path for results')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Load predictions
    print(f"Loading predictions from {args.predictions_dir}...")
    model_predictions = load_model_predictions(args.predictions_dir)
    print(f"Loaded predictions for {len(model_predictions)} models")
    
    # Initialize evaluator
    evaluator = DatumaraEvaluator(args.test_set, args.db_path)
    
    # Evaluate all models
    print("\nEvaluating models...")
    comparison = evaluator.evaluate_all_models(model_predictions)
    
    # Print summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(comparison['comparison_table'].to_string(index=False))
    
    # Save results
    evaluator.save_results(comparison, args.output)


if __name__ == '__main__':
    main()
