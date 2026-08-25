"""
Quick Data Quality Analysis

Following Zhu et al. (2026) key insight:
"61% of BIRD-Platinum instances had errors corrected"

This script quickly analyzes dataset quality without full execution verification.
"""

import pandas as pd
import os
from datasets import load_dataset


def quick_quality_check(dataset_name: str, dataset_id: str):
    """Quick quality assessment of a dataset"""
    
    print(f"\n{'='*80}")
    print(f"Dataset: {dataset_name}")
    print(f"Source:  {dataset_id}")
    print('='*80)
    
    try:
        # Load dataset
        dataset = load_dataset(dataset_id, split="train")
        df = pd.DataFrame(dataset)
        
        print(f"\n📊 Basic Stats:")
        print(f"  Total examples: {len(df):,}")
        
        # Check required columns
        required = ['question', 'sql', 'db_id']
        available = [col for col in required if col in df.columns]
        print(f"  Available columns: {available}")
        
        # Check for nulls
        if 'sql' in df.columns:
            null_sql = df['sql'].isnull().sum()
            null_pct = null_sql / len(df) * 100
            print(f"  Null SQL: {null_sql:,} ({null_pct:.1f}%)")
        
        # SQL length analysis
        if 'sql' in df.columns:
            df['sql_len'] = df['sql'].str.len()
            print(f"\n📏 SQL Length:")
            print(f"  Mean: {df['sql_len'].mean():.1f} chars")
            print(f"  Median: {df['sql_len'].median():.1f} chars")
            print(f"  Std dev: {df['sql_len'].std():.1f}")
        
        # Question length
        if 'question' in df.columns:
            df['q_len'] = df['question'].str.len()
            print(f"\n📏 Question Length:")
            print(f"  Mean: {df['q_len'].mean():.1f} chars")
            print(f"  Median: {df['q_len'].median():.1f} chars")
        
        # SQL keyword analysis (proxy for complexity)
        if 'sql' in df.columns:
            sql_upper = df['sql'].str.upper()
            
            has_count = (sql_upper.str.contains('COUNT')).sum()
            has_sum = (sql_upper.str.contains('SUM')).sum()
            has_avg = (sql_upper.str.contains('AVG')).sum()
            has_join = (sql_upper.str.contains('JOIN')).sum()
            has_group = (sql_upper.str.contains('GROUP BY')).sum()
            has_subquery = (sql_upper.str.contains('(SELECT')).sum()
            
            print(f"\n🔍 SQL Complexity:")
            print(f"  COUNT queries: {has_count:,} ({has_count/len(df)*100:.1f}%)")
            print(f"  SUM queries: {has_sum:,} ({has_sum/len(df)*100:.1f}%)")
            print(f"  AVG queries: {has_avg:,} ({has_avg/len(df)*100:.1f}%)")
            print(f"  JOIN queries: {has_join:,} ({has_join/len(df)*100:.1f}%)")
            print(f"  GROUP BY: {has_group:,} ({has_group/len(df)*100:.1f}%)")
            print(f"  Subqueries: {has_subquery:,} ({has_subquery/len(df)*100:.1f}%)")
        
        # Duplicate check
        if 'question' in df.columns and 'sql' in df.columns:
            dupes = df.duplicated(subset=['question', 'sql']).sum()
            dupe_pct = dupes / len(df) * 100
            print(f"\n🔄 Duplicates:")
            print(f"  Exact duplicates: {dupes:,} ({dupe_pct:.1f}%)")
        
        # Save sample for manual inspection
        sample = df.head(10)
        sample_path = f"data/samples/{dataset_name}_sample.csv"
        os.makedirs("data/samples", exist_ok=True)
        sample.to_csv(sample_path, index=False)
        print(f"\n💾 Sample saved to: {sample_path}")
        
        return df
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def main():
    """Quick analysis of available datasets"""
    
    print("="*80)
    print("Datumara Quick Data Quality Analysis")
    print("Based on Zhu et al. (2026) methodology")
    print("="*80)
    
    datasets_to_check = [
        ("BIRD Train", "birdsql/bird_sql_train"),
        ("BIRD Dev", "birdsql/bird_sql_dev"),
        ("Mini-Dev", "birdsql/bird_mini_dev"),
        ("BIRD-Critic", "birdsql/bird-critic-1.0-sqlite"),
        ("BIRD23-Filtered", "birdsql/bird23-train-filtered"),
    ]
    
    results = {}
    
    for name, dataset_id in datasets_to_check:
        df = quick_quality_check(name, dataset_id)
        if df is not None:
            results[name] = df
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    total_examples = sum(len(df) for df in results.values())
    print(f"Total datasets analyzed: {len(results)}")
    print(f"Total examples: {total_examples:,}")
    
    if len(results) > 0:
        print(f"\nBreakdown:")
        for name, df in results.items():
            print(f"  {name:20s}: {len(df):>8,} examples")
    
    print(f"\n{'='*80}")
    print("Next Steps:")
    print('='*80)
    print("1. Review samples in data/samples/")
    print("2. Run full cleaning: python data/acquire_and_clean.py")
    print("3. Download databases: bash data/download_databases.sh")
    print("")


if __name__ == "__main__":
    main()
