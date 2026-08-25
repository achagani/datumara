#!/usr/bin/env python3
"""
Datumara v0.1 Smoke Test

Quick validation: Can the trained model generate SQL at all?

Tests:
1. Model loads successfully
2. Model generates non-empty output
3. Output looks like SQL (contains SELECT, FROM, etc.)
4. No obvious errors or hallucinations

Usage:
    python scripts/evaluation/smoke_test_v01.py
"""

import os
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    from peft import PeftModel
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the virtual environment: source .venv/bin/activate")
    sys.exit(1)


class DatumaraSmokeTest:
    """Quick smoke test for v0.1 model"""
    
    def __init__(self, model_path: str = "models/local-tinyllama-lora"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.pipe = None
        
    def load_model(self):
        """Load the trained model"""
        print("="*70)
        print("LOADING MODEL")
        print("="*70)
        
        base_model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        print(f"Loading base model: {base_model_id}")
        print(f"Loading adapter from: {self.model_path}")
        print(f"Device: {self.device}")
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
        )
        
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(
            self.model,
            self.model_path,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # Create pipeline
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=128,
            do_sample=False,
            temperature=0.0,
        )
        
        print("✅ Model loaded successfully\n")
        
    def test_generation(self, test_questions: list):
        """Test SQL generation on sample questions"""
        print("="*70)
        print("TESTING SQL GENERATION")
        print("="*70)
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*70}")
            print(f"Test {i}: {question}")
            print('-'*70)
            
            # Format prompt (same as training)
            prompt = f"""<|system|>
You are a text-to-SQL model. Generate SQL queries based on the question and database schema.
<|user|>
Question: {question}
Schema: CREATE TABLE users (id INTEGER, name TEXT, email TEXT);
<|assistant|>
SQL: """
            
            try:
                # Generate
                output = self.pipe(prompt)
                generated_text = output[0]['generated_text']
                
                # Extract SQL (everything after "SQL: ")
                sql_start = generated_text.find("SQL: ") + 5
                generated_sql = generated_text[sql_start:].strip()
                
                # Remove stop tokens
                generated_sql = generated_sql.split("<")[0].strip()
                
                print(f"Generated SQL: {generated_sql}")
                
                # Analyze
                analysis = self._analyze_sql(generated_sql)
                
                results.append({
                    'question': question,
                    'generated_sql': generated_sql,
                    'analysis': analysis
                })
                
                # Print analysis
                print(f"\nAnalysis:")
                for key, value in analysis.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {key}: {value}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                results.append({
                    'question': question,
                    'generated_sql': '',
                    'analysis': {'error': str(e)}
                })
        
        return results
    
    def _analyze_sql(self, sql: str) -> dict:
        """Quick SQL quality checks"""
        sql_upper = sql.upper()
        
        checks = {
            'non_empty': len(sql) > 0,
            'has_select': 'SELECT' in sql_upper,
            'has_from': 'FROM' in sql_upper,
            'looks_like_sql': sql_upper.startswith('SELECT'),
            'no_obvious_errors': not any(bad in sql_upper for bad in ['ERROR', 'INVALID', 'UNKNOWN']),
            'reasonable_length': 10 < len(sql) < 500,
        }
        
        return checks
    
    def print_summary(self, results: list):
        """Print summary of results"""
        print(f"\n{'='*70}")
        print("SUMMARY")
        print('='*70)
        
        total = len(results)
        successful = sum(1 for r in results if r['analysis'].get('has_select', False))
        
        print(f"\nTotal tests: {total}")
        print(f"Generated SELECT: {successful}/{total} ({successful/total*100:.1f}%)")
        
        # Show examples
        print(f"\n{'='*70}")
        print("GENERATED EXAMPLES")
        print('='*70)
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. Question: {result['question']}")
            print(f"   SQL: {result['generated_sql']}")
        
        print(f"\n{'='*70}")
        print("VERDICT")
        print('='*70)
        
        if successful >= total * 0.8:
            print("✅ PASS: Model generates SQL-like output")
        elif successful >= total * 0.5:
            print("⚠️  PARTIAL: Model generates something, but quality varies")
        else:
            print("❌ FAIL: Model does not generate valid SQL")


def main():
    """Run smoke test"""
    # Test questions
    test_questions = [
        "Show me all users",
        "Find users with email",
        "Count the number of users",
        "What is the name of user 1?",
        "List users ordered by name",
    ]
    
    # Run test
    tester = DatumaraSmokeTest()
    tester.load_model()
    results = tester.test_generation(test_questions)
    tester.print_summary(results)
    
    print("\n" + "="*70)
    print("SMOKE TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
