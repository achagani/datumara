"""
Datumara Data Acquisition Script

Based on research from bird-bench.github.io and HuggingFace

Available datasets (verified):
1. Mini-Dev: 500 examples (3 dialects: SQLite, MySQL, PostgreSQL)
2. BIRD-Critic-1.0-SQLite: 500 verified SQL issues
3. BIRD23-Filtered: 6,601 high-quality examples (70% of original train)
4. LiveSQLBench-Base-Lite: 270 tasks
5. BIRD-Interact: 600 interactive tasks

Note: Original BIRD Train/Dev require email subscription or special access
"""

import os
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm


def download_available_datasets():
    """Download all publicly available BIRD-related datasets"""
    
    print("="*80)
    print("Datumara Data Acquisition")
    print("Downloading available datasets from HuggingFace")
    print("="*80)
    
    # Verified available datasets
    datasets_config = {
        "mini_dev": {
            "id": "birdsql/bird_mini_dev",
            "splits": ["mini_dev_sqlite", "mini_dev_mysql", "mini_dev_pg"],
            "description": "500 high-quality examples, 3 dialects"
        },
        "bird_critic": {
            "id": "birdsql/bird-critic-1.0-sqlite",
            "splits": ["train"],
            "description": "500 verified SQL issues (single dialect)"
        },
        "bird23_filtered": {
            "id": "birdsql/bird23-train-filtered",
            "splits": ["train"],
            "description": "6,601 high-quality examples (70% retention)"
        },
        "livesqlbench_lite": {
            "id": "birdsql/livesqlbench-base-lite-sqlite",
            "splits": ["train"],
            "description": "270 tasks, SQLite dialect"
        },
        "effi_sql": {
            "id": "birdsql/effi-sql-training",
            "splits": ["train"],
            "description": "5,590 efficiency-focused examples"
        }
    }
    
    output_dir = "data/bird_raw"
    os.makedirs(output_dir, exist_ok=True)
    
    downloaded = {}
    
    for name, config in datasets_config.items():
        print(f"\n{'='*80}")
        print(f"Dataset: {name}")
        print(f"Source:  {config['id']}")
        print(f"Note:    {config['description']}")
        print('='*80)
        
        try:
            # Load dataset
            if config['splits'][0] != "train":
                # Multiple splits (like mini_dev)
                dataset_dict = load_dataset(config['id'])
                
                # Combine all splits
                all_data = []
                for split in config['splits']:
                    if split in dataset_dict:
                        split_data = pd.DataFrame(dataset_dict[split])
                        split_data['dialect'] = split.replace('mini_dev_', '')
                        all_data.append(split_data)
                        print(f"  Loaded {split}: {len(split_data):,} examples")
                
                if all_data:
                    df = pd.concat(all_data, ignore_index=True)
                else:
                    print(f"  ⚠ No valid splits found")
                    continue
            else:
                # Single split
                dataset = load_dataset(config['id'], split="train")
                df = pd.DataFrame(dataset)
                print(f"  Loaded train: {len(df):,} examples")
            
            # Analyze columns
            print(f"  Columns: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")
            
            # Check for required fields (handle column name variations)
            question_cols = ['question', 'Question']
            sql_cols = ['sql', 'SQL', 'query', 'Query', 'issue_sql', 'preprocess_sql', 'clean_up_sql', 'base_sql', 'optimized_sql']
            
            has_question = any(col in df.columns for col in question_cols)
            has_sql = any(col in df.columns for col in sql_cols)
            has_db = 'db_id' in df.columns
            
            print(f"  Has question: {has_question}")
            print(f"  Has SQL: {has_sql}")
            print(f"  Has DB ID: {has_db}")
            
            # Normalize column names
            if 'SQL' in df.columns and 'sql' not in df.columns:
                df.rename(columns={'SQL': 'sql'}, inplace=True)
            if 'Question' in df.columns and 'question' not in df.columns:
                df.rename(columns={'Question': 'question'}, inplace=True)
            if 'query' in df.columns and 'sql' not in df.columns:
                df.rename(columns={'query': 'sql'}, inplace=True)
            
            # Save to parquet
            output_path = os.path.join(output_dir, f"{name}.parquet")
            df.to_parquet(output_path, index=False)
            
            print(f"  ✓ Saved to: {output_path}")
            
            downloaded[name] = df
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print("DOWNLOAD SUMMARY")
    print('='*80)
    
    total_examples = 0
    for name, df in downloaded.items():
        print(f"{name:25s}: {len(df):>8,} examples")
        total_examples += len(df)
    
    print(f"{'-'*80}")
    print(f"TOTAL:                {total_examples:>8,} examples")
    print(f"\nData saved to: {output_dir}/")
    
    return downloaded


def create_combined_dataset(downloaded_datasets: dict):
    """Combine all downloaded datasets into a single training file"""
    
    print(f"\n{'='*80}")
    print("Creating Combined Training Dataset")
    print('='*80)
    
    output_dir = "data/platinum"
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter datasets with required columns
    usable_datasets = []
    
    for name, df in downloaded_datasets.items():
        if 'question' in df.columns and 'sql' in df.columns:
            # Add source marker
            df['source'] = name
            usable_datasets.append(df)
            print(f"  ✓ {name}: {len(df):,} examples (has question + SQL)")
        else:
            print(f"  ⊘ {name}: Missing required columns")
    
    if not usable_datasets:
        print("  ⚠ No usable datasets found!")
        return None
    
    # Combine
    combined = pd.concat(usable_datasets, ignore_index=True)
    
    print(f"\n  Combined: {len(combined):,} examples")
    
    # Remove duplicates
    dedup_cols = ['question', 'sql']
    if 'db_id' in combined.columns:
        dedup_cols.append('db_id')
    
    before_dedup = len(combined)
    combined_no_dups = combined.drop_duplicates(subset=dedup_cols)
    after_dedup = len(combined_no_dups)
    
    print(f"  After dedup: {after_dedup:,} examples")
    print(f"  Removed: {before_dedup - after_dedup:,} duplicates ({(before_dedup - after_dedup)/before_dedup*100:.1f}%)")
    
    # Save combined dataset
    combined_path = os.path.join(output_dir, "datumara_combined.parquet")
    combined_no_dups.to_parquet(combined_path, index=False)
    print(f"\n  ✓ Saved combined dataset: {combined_path}")
    
    # Create train/dev split (90/10)
    from sklearn.model_selection import train_test_split
    
    train_df, dev_df = train_test_split(
        combined_no_dups,
        test_size=0.1,
        random_state=42,
        stratify=combined_no_dups['source'] if 'source' in combined_no_dups.columns else None
    )
    
    train_path = os.path.join(output_dir, "datumara_train.parquet")
    dev_path = os.path.join(output_dir, "datumara_dev.parquet")
    
    train_df.to_parquet(train_path, index=False)
    dev_df.to_parquet(dev_path, index=False)
    
    print(f"  ✓ Train split: {len(train_df):,} examples -> {train_path}")
    print(f"  ✓ Dev split:   {len(dev_df):,} examples -> {dev_path}")
    
    return combined_no_dups


def main():
    """Main execution"""
    
    # Step 1: Download datasets
    downloaded = download_available_datasets()
    
    if not downloaded:
        print("\n⚠ No datasets downloaded. Check your internet connection and HuggingFace access.")
        return
    
    # Step 2: Create combined dataset
    combined = create_combined_dataset(downloaded)
    
    if combined is not None:
        print(f"\n{'='*80}")
        print("✅ Data acquisition complete!")
        print('='*80)
        print(f"\nNext steps:")
        print(f"1. Review data: ls -lh data/platinum/")
        print(f"2. Run quality analysis: python data/quick_analysis.py")
        print(f"3. Start training with the acquired data")
        print("")


if __name__ == "__main__":
    main()
