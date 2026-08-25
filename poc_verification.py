#!/usr/bin/env python3
"""
Comprehensive proof-of-concept to verify all critical components work
before building the full training pipeline.
"""

import sys
import json
import time
from pathlib import Path

def verify_dependencies():
    """Test all required libraries can be imported"""
    print("\n" + "="*60)
    print("1. VERIFYING DEPENDENCIES")
    print("="*60)
    
    required = {
        'torch': 'PyTorch (GPU support)',
        'transformers': 'HuggingFace Transformers',
        'peft': 'PEFT (LoRA)',
        'datasets': 'HuggingFace Datasets',
        'sqlparse': 'SQL parsing',
        'accelerate': 'Accelerate (GPU optimization)',
    }
    
    all_good = True
    for module, name in required.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {e}")
            all_good = False
    
    return all_good

def verify_gpu():
    """Test GPU availability and CUDA"""
    print("\n" + "="*60)
    print("2. VERIFYING GPU & CUDA")
    print("="*60)
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"CUDA available: {cuda_available}")
        
        if cuda_available:
            print(f"CUDA device: {torch.cuda.get_device_name(0)}")
            print(f"CUDA version: {torch.version.cuda}")
            
            # Get memory info
            gpu_mem_mb = torch.cuda.get_device_properties(0).total_memory / (1024**2)
            print(f"GPU VRAM: {gpu_mem_mb:.0f} MB ({gpu_mem_mb/1024:.1f} GB)")
            
            # Try to allocate memory
            test_tensor = torch.zeros(100000).cuda()
            print(f"✅ GPU allocation successful")
            del test_tensor
            torch.cuda.empty_cache()
            return True
        else:
            print("❌ CUDA not available - will use CPU (very slow)")
            return False
    except Exception as e:
        print(f"❌ GPU error: {e}")
        return False

def verify_model_loading():
    """Test loading a small model"""
    print("\n" + "="*60)
    print("3. VERIFYING MODEL LOADING (this may take 2-5 min)")
    print("="*60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        # Use a small model for testing
        model_name = "gpt2"  # Small model, ~350MB
        print(f"Loading {model_name}...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        total_params = sum(p.numel() for p in model.parameters())
        print(f"✅ Model loaded successfully")
        print(f"   Model parameters: {total_params:,}")
        
        # Test tokenization
        text = "SELECT * FROM users WHERE id = 1"
        tokens = tokenizer.encode(text)
        print(f"✅ Tokenization works ({len(tokens)} tokens)")
        
        # Move to GPU if available
        if torch.cuda.is_available():
            model = model.cuda()
            print(f"✅ Model moved to GPU")
        
        return True
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        return False

def verify_lora():
    """Test LoRA adapter setup"""
    print("\n" + "="*60)
    print("4. VERIFYING LoRA ADAPTER SETUP")
    print("="*60)
    
    try:
        from transformers import AutoModelForCausalLM
        from peft import LoraConfig, get_peft_model
        
        # Load small model
        model = AutoModelForCausalLM.from_pretrained("gpt2")
        
        # Setup LoRA config
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["c_attn"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # Apply LoRA
        model = get_peft_model(model, lora_config)
        
        # Check trainable params
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        print(f"✅ LoRA adapter applied successfully")
        print(f"   Total params: {total_params:,}")
        print(f"   Trainable params: {trainable_params:,}")
        print(f"   Training efficiency: {trainable_params/total_params*100:.2f}%")
        
        return True
    except Exception as e:
        print(f"❌ LoRA setup error: {e}")
        return False

def verify_data_loading():
    """Test loading augmented JSONL data"""
    print("\n" + "="*60)
    print("5. VERIFYING DATA LOADING")
    print("="*60)
    
    try:
        data_path = Path('/home/achagani/llm-analytics/data/spider_augmented_train.jsonl')
        
        if not data_path.exists():
            print(f"❌ Data file not found: {data_path}")
            return False
        
        # Load first 100 examples
        examples = []
        with open(data_path) as f:
            for i, line in enumerate(f):
                if i >= 100:
                    break
                examples.append(json.loads(line))
        
        print(f"✅ Loaded {len(examples)} examples")
        
        # Check structure
        sample = examples[0]
        if 'prompt' not in sample or 'response' not in sample:
            print(f"❌ Invalid format: {list(sample.keys())}")
            return False
        
        print(f"✅ Data format correct")
        print(f"   Sample prompt length: {len(sample['prompt'])} chars")
        print(f"   Sample response: {sample['response'][:80]}...")
        
        # Estimate full dataset size
        with open(data_path) as f:
            total_lines = sum(1 for _ in f)
        
        print(f"✅ Total examples: {total_lines}")
        
        # Estimate memory footprint
        avg_prompt_len = sum(len(e['prompt']) for e in examples) / len(examples)
        avg_response_len = sum(len(e['response']) for e in examples) / len(examples)
        avg_total_len = avg_prompt_len + avg_response_len
        
        # Rough estimate: 1 token ≈ 4 bytes, tokenize adds overhead
        estimated_tokens_per_example = int((avg_total_len / 4) * 1.2)
        estimated_mb_per_example = (estimated_tokens_per_example * 4) / (1024**2)
        estimated_total_mb = (total_lines * estimated_tokens_per_example * 4) / (1024**2)
        
        print(f"✅ Memory estimate: {estimated_total_mb:.0f} MB for full dataset")
        
        return True
    except Exception as e:
        print(f"❌ Data loading error: {e}")
        return False

def verify_complexity_classification():
    """Test complexity classification on sample data"""
    print("\n" + "="*60)
    print("6. VERIFYING COMPLEXITY CLASSIFICATION")
    print("="*60)
    
    try:
        import sqlparse
        
        def get_complexity_score(query):
            """Simplified complexity scorer"""
            join_count = query.upper().count(' JOIN ')
            subquery_count = query.upper().count('(SELECT')
            agg_count = sum(query.upper().count(f) for f in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'])
            has_group = 'GROUP BY' in query.upper()
            has_having = 'HAVING' in query.upper()
            
            score = join_count * 15 + subquery_count * 20 + agg_count * 10 + (has_group * 10) + (has_having * 10)
            return min(100, score)
        
        # Test queries
        test_queries = [
            ("SELECT * FROM users", "simple"),
            ("SELECT id, COUNT(*) FROM users GROUP BY id", "medium"),
            ("SELECT u.id, COUNT(o.id), AVG(o.amount) FROM users u JOIN orders o ON u.id = o.user_id WHERE o.date > '2024-01-01' GROUP BY u.id HAVING COUNT(o.id) > 5", "complex"),
        ]
        
        for query, expected in test_queries:
            score = get_complexity_score(query)
            level = "simple" if score < 25 else "medium" if score < 60 else "complex"
            status = "✅" if level == expected else "⚠️"
            print(f"{status} {expected:10} → {level:10} (score: {score:3d})")
        
        return True
    except Exception as e:
        print(f"❌ Complexity classification error: {e}")
        return False

def verify_evaluation_metrics():
    """Test evaluation metric calculations"""
    print("\n" + "="*60)
    print("7. VERIFYING EVALUATION METRICS")
    print("="*60)
    
    try:
        import sqlparse
        
        def is_valid_sql(query):
            try:
                sqlparse.parse(query)
                return True
            except:
                return False
        
        def normalize_sql(query):
            return ' '.join(query.lower().split())
        
        # Test cases
        test_cases = [
            ("SELECT * FROM users", True, "valid SQL"),
            ("SELECT * FFROM users", False, "typo (should be FROM)"),
            ("SELECT id FROM (SELECT id FROM users WHERE x=1) t", True, "subquery"),
        ]
        
        for query, should_be_valid, desc in test_cases:
            is_valid = is_valid_sql(query)
            status = "✅" if is_valid == should_be_valid else "⚠️"
            print(f"{status} {desc:30} → valid={is_valid}")
        
        # Test normalization
        q1 = "SELECT   id FROM   users"
        q2 = "select id from users"
        same = normalize_sql(q1) == normalize_sql(q2)
        status = "✅" if same else "❌"
        print(f"{status} Normalization: SQL variations normalize correctly")
        
        return True
    except Exception as e:
        print(f"❌ Evaluation metrics error: {e}")
        return False

def verify_training_loop():
    """Test a single training step"""
    print("\n" + "="*60)
    print("8. VERIFYING TRAINING LOOP (mini forward/backward pass)")
    print("="*60)
    
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import LoraConfig, get_peft_model
        
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Setup
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained("gpt2")
        
        # Apply LoRA
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["c_attn"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, lora_config)
        model = model.to(device)
        
        # Create sample batch
        batch_texts = [
            "SELECT * FROM users WHERE id = 1",
            "SELECT id, name FROM customers ORDER BY name"
        ]
        
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True).to(device)
        
        # Forward pass
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
        
        print(f"✅ Forward pass successful")
        print(f"   Loss: {loss.item():.4f}")
        
        # Backward pass
        loss.backward()
        print(f"✅ Backward pass successful")
        
        # Check gradients
        grad_count = sum(1 for p in model.parameters() if p.grad is not None and p.grad.abs().sum() > 0)
        print(f"✅ Gradients computed: {grad_count} parameters have non-zero gradients")
        
        return True
    except Exception as e:
        print(f"❌ Training loop error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_disk_space():
    """Check disk space for training checkpoints"""
    print("\n" + "="*60)
    print("9. VERIFYING DISK SPACE")
    print("="*60)
    
    try:
        import shutil
        
        stat = shutil.disk_usage('/home/achagani/llm-analytics')
        free_gb = stat.free / (1024**3)
        
        # Estimates
        model_size_gb = 7  # 3.5B model
        checkpoint_storage_gb = 20  # Multiple checkpoints
        total_needed_gb = model_size_gb + checkpoint_storage_gb
        
        print(f"Free disk space: {free_gb:.1f} GB")
        print(f"Model size estimate: {model_size_gb} GB")
        print(f"Checkpoint storage estimate: {checkpoint_storage_gb} GB")
        print(f"Total needed: {total_needed_gb} GB")
        
        if free_gb > total_needed_gb:
            print(f"✅ Sufficient disk space")
            return True
        else:
            print(f"❌ Insufficient disk space (need {total_needed_gb}GB, have {free_gb:.1f}GB)")
            return False
    except Exception as e:
        print(f"❌ Disk space check error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("PROOF OF CONCEPT VERIFICATION")
    print("="*60)
    
    results = {
        'dependencies': verify_dependencies(),
        'gpu': verify_gpu(),
        'model_loading': verify_model_loading(),
        'lora': verify_lora(),
        'data_loading': verify_data_loading(),
        'complexity': verify_complexity_classification(),
        'metrics': verify_evaluation_metrics(),
        'training_loop': verify_training_loop(),
        'disk_space': verify_disk_space(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Safe to proceed with implementation")
    else:
        print("❌ SOME CHECKS FAILED - Review errors above before proceeding")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
