"""
Generate SQL Predictions from Datumara Models

This script loads a trained model and generates SQL predictions for a test set.
Supports:
- Ollama models (local deployment)
- HuggingFace models (direct inference)
- API-based models (GPT-4, Claude, etc.)

Usage:
    python generate_predictions.py \
        --model datumara-local \
        --test-set mini_dev \
        --output predictions/datumara_v0.1/predictions.json
"""

import os
import json
import argparse
from typing import List, Dict
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import ollama


class PredictionGenerator:
    """Generate SQL predictions from various model types"""
    
    def __init__(self, model_name: str, model_type: str = "ollama"):
        self.model_name = model_name
        self.model_type = model_type
        
        if model_type == "ollama":
            self.client = ollama.Client()
        elif model_type == "huggingface":
            self._load_huggingface_model()
        elif model_type == "api":
            self._setup_api()
    
    def _load_huggingface_model(self):
        """Load model from HuggingFace"""
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def _setup_api(self):
        """Setup API client for GPT-4/Claude"""
        import openai
        self.api_client = openai.OpenAI()
    
    def generate_sql(self, question: str, schema: str, evidence: str = "") -> str:
        """Generate SQL for a single question"""
        
        if self.model_type == "ollama":
            return self._generate_ollama(question, schema, evidence)
        elif self.model_type == "huggingface":
            return self._generate_huggingface(question, schema, evidence)
        elif self.model_type == "api":
            return self._generate_api(question, schema, evidence)
    
    def _generate_ollama(self, question: str, schema: str, evidence: str) -> str:
        """Generate SQL using Ollama"""
        
        prompt = self._create_prompt(question, schema, evidence)
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.0,  # Deterministic for evaluation
                    'top_p': 0.9,
                    'num_predict': 512
                }
            )
            
            sql = response['response'].strip()
            
            # Extract SQL from response (handle markdown formatting)
            if '```sql' in sql:
                sql = sql.split('```sql')[1].split('```')[0].strip()
            elif '```' in sql:
                sql = sql.split('```')[1].split('```')[0].strip()
            
            return sql
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return ""
    
    def _generate_huggingface(self, question: str, schema: str, evidence: str) -> str:
        """Generate SQL using HuggingFace model"""
        import torch
        
        prompt = self._create_prompt(question, schema, evidence)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.0,
                do_sample=False
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract SQL from response
        sql = generated_text[len(prompt):].strip()
        
        if '```sql' in sql:
            sql = sql.split('```sql')[1].split('```')[0].strip()
        
        return sql
    
    def _generate_api(self, question: str, schema: str, evidence: str) -> str:
        """Generate SQL using API (GPT-4)"""
        
        prompt = self._create_prompt(question, schema, evidence)
        
        response = self.api_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate only valid SQL."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=512
        )
        
        sql = response.choices[0].message.content.strip()
        
        if '```sql' in sql:
            sql = sql.split('```sql')[1].split('```')[0].strip()
        
        return sql
    
    def _create_prompt(self, question: str, schema: str, evidence: str) -> str:
        """Create prompt for SQL generation"""
        
        prompt = f"""Given the following database schema, generate a SQL query to answer the question.

Schema:
{schema}

"""
        
        if evidence:
            prompt += f"""Evidence:
{evidence}

"""
        
        prompt += f"""Question:
{question}

SQL Query:
"""
        
        return prompt
    
    def generate_all(self, test_set: List[Dict]) -> List[Dict]:
        """Generate predictions for entire test set"""
        predictions = []
        
        for example in tqdm(test_set, desc="Generating predictions"):
            question = example.get('question', '')
            schema = example.get('schema', '')
            evidence = example.get('evidence', '')
            question_id = example.get('question_id', len(predictions))
            db_id = example.get('db_id', 'default')
            
            sql = self.generate_sql(question, schema, evidence)
            
            predictions.append({
                'question_id': question_id,
                'db_id': db_id,
                'question': question,
                'predicted_sql': sql,
                'reference_sql': example.get('sql', '')
            })
        
        return predictions


def load_test_set(test_set_name: str) -> List[Dict]:
    """Load test set by name"""
    
    # Try to load from parquet
    parquet_path = f"data/bird_raw/{test_set_name}.parquet"
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
        return df.to_dict('records')
    
    # Try JSON
    json_path = f"data/bird_raw/{test_set_name}.json"
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    
    raise FileNotFoundError(f"Test set not found: {test_set_name}")


def main():
    parser = argparse.ArgumentParser(description='Generate SQL predictions')
    parser.add_argument('--model', type=str, default='datumara-local',
                       help='Model name (Ollama or HuggingFace)')
    parser.add_argument('--model-type', type=str, default='ollama',
                       choices=['ollama', 'huggingface', 'api'],
                       help='Model type')
    parser.add_argument('--test-set', type=str, default='mini_dev',
                       help='Test set name')
    parser.add_argument('--output', type=str, default='predictions/predictions.json',
                       help='Output path')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Load test set
    print(f"Loading test set: {args.test_set}")
    test_set = load_test_set(args.test_set)
    print(f"Loaded {len(test_set)} examples")
    
    # Initialize generator
    print(f"Initializing model: {args.model}")
    generator = PredictionGenerator(args.model, args.model_type)
    
    # Generate predictions
    print("Generating predictions...")
    predictions = generator.generate_all(test_set)
    
    # Save predictions
    with open(args.output, 'w') as f:
        json.dump(predictions, f, indent=2)
    
    print(f"\n✓ Saved {len(predictions)} predictions to {args.output}")
    
    # Quick stats
    valid_sqls = sum(1 for p in predictions if p['predicted_sql'])
    print(f"Valid SQL generated: {valid_sqls}/{len(predictions)} ({valid_sqls/len(predictions)*100:.1f}%)")


if __name__ == '__main__':
    main()
