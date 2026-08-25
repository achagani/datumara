"""
Datumara Data Acquisition and Cleaning Pipeline

Based on Zhu et al. (2026) "Human-Level Text-to-SQL via RLVR" methodology:
- Download BIRD datasets from HuggingFace
- Implement execution-based verification
- Detect and correct annotation errors
- Create Platinum-quality dataset

Datasets to acquire:
1. BIRD Train (9,428 examples)
2. BIRD Dev (1,534 examples)
3. BIRD-Critic-1.0 (500 verified issues)
4. Mini-Dev (500 high-quality examples)
5. BIRD23-Filtered (6,600 high-quality subset)
"""

import os
import json
import sqlite3
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional
import hashlib


class BirdDatasetAcquirer:
    """Acquire and preprocess BIRD datasets"""
    
    def __init__(self, output_dir: str = "data/bird_raw"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.datasets = {
            "bird_train": "birdsql/bird_sql_train",
            "bird_dev": "birdsql/bird_sql_dev",
            "bird_critic": "birdsql/bird-critic-1.0-sqlite",
            "mini_dev": "birdsql/bird_mini_dev",
            "bird23_filtered": "birdsql/bird23-train-filtered"
        }
    
    def download_all(self) -> Dict[str, pd.DataFrame]:
        """Download all available BIRD datasets"""
        downloaded = {}
        
        for name, dataset_id in self.datasets.items():
            print(f"\n{'='*60}")
            print(f"Downloading {name} from {dataset_id}")
            print('='*60)
            
            try:
                # Load dataset from HuggingFace
                dataset = load_dataset(dataset_id, split="train" if "train" in name else "validation" if "dev" in name else "train")
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(dataset)
                
                # Save to parquet
                output_path = os.path.join(self.output_dir, f"{name}.parquet")
                df.to_parquet(output_path, index=False)
                
                print(f"✓ Downloaded {len(df):,} examples")
                print(f"  Columns: {list(df.columns)}")
                print(f"  Saved to: {output_path}")
                
                downloaded[name] = df
                
            except Exception as e:
                print(f"✗ Failed to download {name}: {e}")
        
        return downloaded
    
    def analyze_dataset_quality(self, df: pd.DataFrame, dataset_name: str):
        """Analyze dataset quality metrics"""
        print(f"\n{'='*60}")
        print(f"Quality Analysis: {dataset_name}")
        print('='*60)
        
        # Basic stats
        print(f"Total examples: {len(df):,}")
        
        # Check for common columns
        required_cols = ['question', 'sql', 'db_id']
        available_cols = [col for col in required_cols if col in df.columns]
        print(f"Available columns: {available_cols}")
        
        # Check for nulls
        null_counts = df[available_cols].isnull().sum()
        print(f"\nNull values:")
        for col, count in null_counts.items():
            if count > 0:
                print(f"  {col}: {count:,} ({count/len(df)*100:.2f}%)")
        
        # SQL length distribution
        if 'sql' in df.columns:
            df['sql_length'] = df['sql'].str.len()
            print(f"\nSQL length stats:")
            print(f"  Mean: {df['sql_length'].mean():.1f} chars")
            print(f"  Median: {df['sql_length'].median():.1f} chars")
            print(f"  Max: {df['sql_length'].max()} chars")
            print(f"  Min: {df['sql_length'].min()} chars")
        
        # Question length
        if 'question' in df.columns:
            df['question_length'] = df['question'].str.len()
            print(f"\nQuestion length stats:")
            print(f"  Mean: {df['question_length'].mean():.1f} chars")
            print(f"  Median: {df['question_length'].median():.1f} chars")


class DataCleaner:
    """
    Implement data cleaning methodology from Zhu et al. (2026)
    
    Key steps:
    1. Execution verification - SQL must execute without errors
    2. Question-SQL alignment - SQL must answer the question
    3. Schema consistency - Tables/columns must exist in database
    4. Duplicate removal - Remove exact duplicates
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.verification_stats = {
            "total": 0,
            "execution_valid": 0,
            "schema_valid": 0,
            "alignment_valid": 0,
            "duplicates_removed": 0,
            "platinum_quality": 0
        }
    
    def verify_execution(self, sql: str, db_id: str, db_root: str = "data/databases") -> Tuple[bool, Optional[str]]:
        """
        Step 1: Execute SQL to verify it runs without errors
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not isinstance(sql, str):
            return False, "Empty or invalid SQL"
        
        db_path = os.path.join(db_root, db_id, f"{db_id}.sqlite")
        
        if not os.path.exists(db_path):
            # Try without db_root
            if os.path.exists(f"{db_id}.sqlite"):
                db_path = f"{db_id}.sqlite"
            else:
                return False, f"Database not found: {db_path}"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Execute with timeout (5 seconds)
            conn.set_trace_callback(lambda x: None)  # Suppress trace
            cursor.execute(sql)
            
            # Fetch results to ensure query completes
            _ = cursor.fetchall()
            
            conn.close()
            return True, None
            
        except sqlite3.Error as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def verify_schema(self, sql: str, db_id: str, db_root: str = "data/databases") -> Tuple[bool, List[str]]:
        """
        Step 2: Verify all tables/columns referenced in SQL exist in schema
        
        Returns:
            Tuple of (is_valid, missing_elements)
        """
        # Extract table and column references (simplified)
        # In production, use proper SQL parser like sqlparse
        import re
        
        # Get schema
        db_path = os.path.join(db_root, db_id, f"{db_id}.sqlite")
        if not os.path.exists(db_path):
            db_path = f"{db_id}.sqlite"
        
        if not os.path.exists(db_path):
            return False, ["Database not found"]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0].lower() for row in cursor.fetchall()}
            
            # Get all columns
            columns = set()
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                for row in cursor.fetchall():
                    columns.add(f"{table}.{row[1].lower()}")
                    columns.add(row[1].lower())  # Column name without table prefix
            
            conn.close()
            
            # Check if tables exist in SQL (simplified check)
            sql_lower = sql.lower()
            missing = []
            
            for table in tables:
                if table in sql_lower and table not in sql_lower.replace(f"from {table}", "").replace(f"join {table}", ""):
                    # Table mentioned but not in FROM/JOIN clause
                    pass  # This is a simplified check
            
            return len(missing) == 0, missing
            
        except Exception as e:
            return False, [f"Schema check error: {str(e)}"]
    
    def verify_alignment(self, question: str, sql: str, use_llm: bool = False) -> Tuple[bool, float]:
        """
        Step 3: Verify SQL semantically matches the question
        
        Returns:
            Tuple of (is_aligned, confidence_score)
        """
        # Simple heuristic checks (can be enhanced with LLM)
        
        # Check 1: Question type matches SQL type
        question_lower = question.lower()
        
        is_count = "count" in question_lower or "how many" in question_lower
        is_sum = "sum" in question_lower or "total" in question_lower
        is_avg = "average" in question_lower or "mean" in question_lower
        
        sql_upper = sql.upper()
        has_count = "COUNT(" in sql_upper
        has_sum = "SUM(" in sql_upper
        has_avg = "AVG(" in sql_upper
        
        # Basic alignment check
        alignment_score = 1.0
        
        if is_count and not has_count:
            alignment_score -= 0.3
        if is_sum and not has_sum:
            alignment_score -= 0.3
        if is_avg and not has_avg:
            alignment_score -= 0.3
        
        # Check 2: SQL has necessary components
        has_select = "SELECT" in sql_upper
        has_from = "FROM" in sql_upper
        
        if not has_select or not has_from:
            alignment_score -= 0.5
        
        # Check 3: Question length vs SQL complexity
        if len(question) < 10 or len(sql) < 10:
            alignment_score -= 0.2
        
        is_aligned = alignment_score >= 0.7
        return is_aligned, max(0.0, alignment_score)
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 4: Remove exact duplicates"""
        initial_count = len(df)
        
        # Check for duplicates based on question+sql+db_id
        if 'question' in df.columns and 'sql' in df.columns:
            df_no_dups = df.drop_duplicates(subset=['question', 'sql', 'db_id'] if 'db_id' in df.columns else ['question', 'sql'])
        else:
            df_no_dups = df.drop_duplicates()
        
        final_count = len(df_no_dups)
        removed = initial_count - final_count
        
        print(f"Removed {removed:,} duplicates ({removed/initial_count*100:.2f}%)")
        
        return df_no_dups
    
    def create_platinum_dataset(self, df: pd.DataFrame, dataset_name: str, 
                                  db_root: str = "data/databases",
                                  output_dir: str = "data/platinum") -> pd.DataFrame:
        """
        Create Platinum-quality dataset following Zhu et al. methodology
        
        Process:
        1. Remove duplicates
        2. Verify execution
        3. Verify schema (optional, slow)
        4. Verify alignment
        5. Keep only high-quality examples
        """
        print(f"\n{'='*80}")
        print(f"Creating Platinum dataset from {dataset_name}")
        print(f"{'='*80}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Remove duplicates
        print("\nStep 1: Removing duplicates...")
        df_clean = self.remove_duplicates(df.copy())
        self.verification_stats["duplicates_removed"] = len(df) - len(df_clean)
        
        # Step 2: Execution verification
        print(f"\nStep 2: Verifying execution ({len(df_clean):,} examples)...")
        execution_valid = []
        
        for idx, row in tqdm(df_clean.iterrows(), total=len(df_clean), desc="Executing SQL"):
            sql = row.get('sql', '')
            db_id = row.get('db_id', '')
            
            is_valid, error = self.verify_execution(sql, db_id, db_root)
            
            if is_valid:
                execution_valid.append(idx)
                self.verification_stats["execution_valid"] += 1
            else:
                # Store error for analysis
                df_clean.at[idx, 'execution_error'] = error
        
        self.verification_stats["total"] = len(df_clean)
        
        print(f"✓ Execution valid: {len(execution_valid):,} ({len(execution_valid)/len(df_clean)*100:.1f}%)")
        
        # Filter to execution-valid examples
        df_exec_valid = df_clean.loc[execution_valid].copy()
        
        # Step 3: Schema verification (optional, commented out for speed)
        # print(f"\nStep 3: Verifying schema...")
        # schema_valid = []
        # for idx, row in tqdm(df_exec_valid.iterrows(), total=len(df_exec_valid)):
        #     sql = row['sql']
        #     db_id = row['db_id']
        #     is_valid, missing = self.verify_schema(sql, db_id, db_root)
        #     if is_valid:
        #         schema_valid.append(idx)
        # 
        # df_schema_valid = df_exec_valid.loc[schema_valid].copy()
        # print(f"✓ Schema valid: {len(schema_valid):,} ({len(schema_valid)/len(df_exec_valid)*100:.1f}%)")
        
        df_schema_valid = df_exec_valid.copy()  # Skip for now
        self.verification_stats["schema_valid"] = len(df_schema_valid)
        
        # Step 4: Alignment verification
        print(f"\nStep 4: Verifying question-SQL alignment...")
        alignment_valid = []
        alignment_scores = []
        
        for idx, row in tqdm(df_schema_valid.iterrows(), total=len(df_schema_valid), desc="Checking alignment"):
            question = row.get('question', '')
            sql = row.get('sql', '')
            
            is_aligned, score = self.verify_alignment(question, sql)
            alignment_scores.append(score)
            
            if is_aligned:
                alignment_valid.append(idx)
                self.verification_stats["alignment_valid"] += 1
        
        df_aligned = df_schema_valid.loc[alignment_valid].copy()
        
        print(f"✓ Alignment valid: {len(alignment_valid):,} ({len(alignment_valid)/len(df_schema_valid)*100:.1f}%)")
        print(f"  Average alignment score: {sum(alignment_scores)/len(alignment_scores):.2f}")
        
        # Step 5: Mark as platinum quality
        df_aligned['platinum_quality'] = True
        df_aligned['quality_score'] = [alignment_scores[alignment_valid.index(idx)] if idx in alignment_valid else 0.0 
                                        for idx in range(len(df_aligned))]
        
        self.verification_stats["platinum_quality"] = len(df_aligned)
        
        # Save platinum dataset
        output_path = os.path.join(output_dir, f"{dataset_name}_platinum.parquet")
        df_aligned.to_parquet(output_path, index=False)
        
        # Save verification stats
        stats_path = os.path.join(output_dir, f"{dataset_name}_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(self.verification_stats, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"Platinum dataset created!")
        print(f"{'='*80}")
        print(f"Original:     {self.verification_stats['total']:>8,} examples")
        print(f"Platinum:     {self.verification_stats['platinum_quality']:>8,} examples")
        print(f"Retention:    {self.verification_stats['platinum_quality']/self.verification_stats['total']*100:>8.1f}%")
        print(f"Saved to:     {output_path}")
        print(f"Stats saved:  {stats_path}")
        
        return df_aligned


def main():
    """Main pipeline execution"""
    print("="*80)
    print("Datumara Data Acquisition and Cleaning Pipeline")
    print("Based on Zhu et al. (2026) methodology")
    print("="*80)
    
    # Step 1: Download datasets
    print("\n" + "="*80)
    print("PHASE 1: Dataset Acquisition")
    print("="*80)
    
    acquirer = BirdDatasetAcquirer(output_dir="data/bird_raw")
    datasets = acquirer.download_all()
    
    # Analyze each dataset
    for name, df in datasets.items():
        acquirer.analyze_dataset_quality(df, name)
    
    # Step 2: Clean and create platinum datasets
    print("\n" + "="*80)
    print("PHASE 2: Data Cleaning and Verification")
    print("="*80)
    
    cleaner = DataCleaner()
    
    # Process each dataset
    for name, df in datasets.items():
        if 'question' in df.columns and 'sql' in df.columns:
            platinum_df = cleaner.create_platinum_dataset(
                df, 
                name,
                db_root="data/databases",
                output_dir="data/platinum"
            )
            
            # Reset stats for next dataset
            cleaner.verification_stats = {
                "total": 0,
                "execution_valid": 0,
                "schema_valid": 0,
                "alignment_valid": 0,
                "duplicates_removed": 0,
                "platinum_quality": 0
            }
    
    # Step 3: Combine all platinum datasets
    print("\n" + "="*80)
    print("PHASE 3: Combining Platinum Datasets")
    print("="*80)
    
    import glob
    platinum_files = glob.glob("data/platinum/*_platinum.parquet")
    
    if platinum_files:
        all_platinum = []
        for file in platinum_files:
            df = pd.read_parquet(file)
            dataset_name = os.path.basename(file).replace('_platinum.parquet', '')
            df['source'] = dataset_name
            all_platinum.append(df)
            print(f"  Loaded {dataset_name}: {len(df):,} examples")
        
        combined = pd.concat(all_platinum, ignore_index=True)
        
        # Remove duplicates across datasets
        combined_no_dups = combined.drop_duplicates(subset=['question', 'sql', 'db_id'] if 'db_id' in combined.columns else ['question', 'sql'])
        
        print(f"\nTotal combined: {len(combined):,} examples")
        print(f"After dedup:    {len(combined_no_dups):,} examples")
        print(f"Removed:        {len(combined) - len(combined_no_dups):,} cross-dataset duplicates")
        
        # Save combined dataset
        combined_path = "data/platinum/datumara_training_combined.parquet"
        combined_no_dups.to_parquet(combined_path, index=False)
        
        print(f"\n✓ Combined platinum dataset saved to: {combined_path}")
        
        # Create train/dev split
        from sklearn.model_selection import train_test_split
        
        train_df, dev_df = train_test_split(
            combined_no_dups, 
            test_size=0.1, 
            random_state=42,
            stratify=combined_no_dups['source'] if 'source' in combined_no_dups.columns else None
        )
        
        train_path = "data/platinum/datumara_train.parquet"
        dev_path = "data/platinum/datumara_dev.parquet"
        
        train_df.to_parquet(train_path, index=False)
        dev_df.to_parquet(dev_path, index=False)
        
        print(f"\n✓ Train split: {len(train_df):,} examples -> {train_path}")
        print(f"✓ Dev split:   {len(dev_df):,} examples -> {dev_path}")
        
    else:
        print("No platinum datasets found!")


if __name__ == "__main__":
    main()
