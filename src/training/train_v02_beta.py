"""Train Datumara v0.2-beta with prompt masking and validation tracking."""

from __future__ import annotations

import json
import random
import shutil
import time
from pathlib import Path

import pandas as pd
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "models" / "datumara-v02-beta"


def load_parquet_examples(path: Path, limit: int = None) -> list[dict[str, str]]:
    """Load examples from parquet file."""
    df = pd.read_parquet(path)
    if limit:
        df = df.head(limit)
    
    examples = []
    for _, row in df.iterrows():
        examples.append({
            "question": str(row["question"]),
            "sql": str(row["sql"]),
            "db_id": str(row["db_id"]) if "db_id" in row else "unknown"
        })
    return examples


def encode_examples_with_prompt_masking(tokenizer, examples, max_length: int) -> list[dict[str, torch.Tensor]]:
    """
    Encode examples with prompt masking - only train on SQL tokens.
    
    This is CRITICAL for v0.2: we mask the question/prompts so the model
    learns to generate SQL, not to predict the question.
    """
    encoded = []
    mask_stats = {"total_tokens": 0, "sql_tokens": 0, "masked_tokens": 0}
    
    for example in examples:
        # Format: [INST] question [/INST] SQL <eos>
        prompt_text = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": "You are Datumara, an expert SQL generation engine. Generate valid SQL that executes correctly on the given schema."},
                {"role": "user", "content": example["question"]},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        
        # Tokenize prompt and response separately
        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        response_text = f"{example['sql']}{tokenizer.eos_token}"
        response_ids = tokenizer(response_text, add_special_tokens=False)["input_ids"]
        
        # Combine with truncation if needed
        available_response_tokens = max(1, max_length - len(prompt_ids))
        response_ids = response_ids[:available_response_tokens]
        input_ids = prompt_ids + response_ids
        
        # Pad if needed
        if len(input_ids) < max_length:
            padding = max_length - len(input_ids)
            input_ids = input_ids + [tokenizer.pad_token_id] * padding
        
        input_ids = torch.tensor(input_ids, dtype=torch.long)
        attention_mask = (input_ids != tokenizer.pad_token_id).long()
        
        # CRITICAL: Mask out prompt tokens in labels (set to -100)
        # Only train on SQL tokens
        labels = input_ids.clone()
        labels[:] = -100  # Mask everything first
        
        # Unmask only the SQL tokens (after prompt)
        sql_start = len(prompt_ids)
        sql_end = sql_start + len(response_ids)
        labels[sql_start:sql_end] = input_ids[sql_start:sql_end]
        
        # Ensure masked tokens are -100
        labels[attention_mask == 0] = -100
        
        # Track stats
        mask_stats["total_tokens"] += (attention_mask == 1).sum().item()
        mask_stats["sql_tokens"] += (labels != -100).sum().item()
        mask_stats["masked_tokens"] += (labels == -100).sum().item()
        
        encoded.append({
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "sql_length": len(response_ids)
        })
    
    # Print masking statistics
    total = mask_stats["total_tokens"]
    sql = mask_stats["sql_tokens"]
    masked = mask_stats["masked_tokens"]
    print(f"\nPrompt masking stats:")
    print(f"  Total tokens: {total:,}")
    print(f"  SQL tokens (trained): {sql:,} ({100*sql/total:.1f}%)")
    print(f"  Question tokens (masked): {masked:,} ({100*masked/total:.1f}%)")
    
    return encoded


def save_checkpoint(model, tokenizer, optimizer, epoch, step, loss, val_loss, output_dir, checkpoint_name, rng_state):
    """Save checkpoint with validation loss."""
    checkpoint_dir = output_dir / "checkpoints" / checkpoint_name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained(checkpoint_dir)
    tokenizer.save_pretrained(checkpoint_dir)
    
    torch.save({
        "epoch": epoch,
        "step": step,
        "loss": loss,
        "val_loss": val_loss,
        "optimizer_state_dict": optimizer.state_dict(),
        "rng_state": rng_state,
    }, checkpoint_dir / "training_state.pt")
    
    metadata = {
        "checkpoint_name": checkpoint_name,
        "epoch": epoch,
        "step": step,
        "train_loss": round(loss, 6),
        "val_loss": round(val_loss, 6) if val_loss else None,
        "timestamp": time.time(),
    }
    (checkpoint_dir / "checkpoint_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    
    print(f"✓ Saved checkpoint: {checkpoint_name} (train_loss={loss:.4f}, val_loss={val_loss:.4f if val_loss else 'N/A'})")


def evaluate_validation(model, val_batches, device, max_batches=20):
    """Compute validation loss on a subset of batches."""
    model.eval()
    val_losses = []
    
    with torch.no_grad():
        for i, batch in enumerate(val_batches[:max_batches]):
            batch = {key: value.unsqueeze(0).to(device) for key, value in batch.items()}
            loss = model(**batch).loss
            val_losses.append(loss.item())
    
    model.train()
    return sum(val_losses) / len(val_losses) if val_losses else None


def cleanup_old_checkpoints(output_dir, keep_last_n=3):
    """Keep only the last N checkpoints."""
    checkpoints_dir = output_dir / "checkpoints"
    if not checkpoints_dir.exists():
        return
    
    checkpoint_dirs = [
        d for d in checkpoints_dir.iterdir()
        if d.is_dir() and d.name.startswith("checkpoint_")
    ]
    checkpoint_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    
    for old_checkpoint in checkpoint_dirs[keep_last_n:]:
        print(f"Removing old checkpoint: {old_checkpoint.name}")
        shutil.rmtree(old_checkpoint)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train Datumara v0.2-beta")
    parser.add_argument("--train-data", type=Path, default=Path(__file__).parent.parent / "data" / "platinum" / "datumara_v02_training_combined.parquet")
    parser.add_argument("--val-data", type=Path, default=Path(__file__).parent.parent / "data" / "platinum" / "datumara_v02_dev_final.parquet")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-steps", type=int, default=3000)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--val-every", type=int, default=200, help="Evaluate validation every N steps")
    parser.add_argument("--keep-checkpoints", type=int, default=5)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}")
    if device.type == "cuda":
        print(f"gpu={torch.cuda.get_device_name(0)}")

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    # LoRA config
    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,  # Increased from 16 for better learning
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config).to(device)
    model.print_trainable_parameters()

    # Load data
    print(f"\nLoading training data from {args.train_data}...")
    train_examples = load_parquet_examples(args.train_data, limit=12000)
    print(f"Loaded {len(train_examples):,} training examples")
    
    print(f"\nLoading validation data from {args.val_data}...")
    val_examples = load_parquet_examples(args.val_data, limit=1500)
    print(f"Loaded {len(val_examples):,} validation examples")

    # Encode with prompt masking
    print("\nEncoding training examples with prompt masking...")
    random.seed(args.seed)
    random.shuffle(train_examples)
    train_batches = encode_examples_with_prompt_masking(tokenizer, train_examples, args.max_length)
    
    print("\nEncoding validation examples...")
    val_batches = encode_examples_with_prompt_masking(tokenizer, val_examples, args.max_length)

    # Setup training
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_file = output_dir / "training_progress.jsonl"
    progress_handle = progress_file.open("w", encoding="utf-8")
    
    started_at = time.time()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)  # Slightly higher LR
    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")
    model.train()
    
    step = 0
    best_val_loss = float("inf")
    best_checkpoint_name = None

    print(f"\n{'='*70}")
    print(f"Starting v0.2-beta training")
    print(f"Steps: {args.max_steps:,}, Checkpoint every: {args.checkpoint_every}, Val every: {args.val_every}")
    print(f"{'='*70}\n")

    epoch = 0
    while step < args.max_steps:
        for batch in train_batches:
            if step >= args.max_steps:
                break
                
            optimizer.zero_grad(set_to_none=True)
            batch_tensor = {key: value.unsqueeze(0).to(device) for key, value in batch.items()}
            
            with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
                loss = model(**batch_tensor).loss
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            step += 1
            
            # Progress tracking
            progress = {
                "step": step,
                "max_steps": args.max_steps,
                "train_loss": round(loss.item(), 6),
                "elapsed_seconds": round(time.time() - started_at, 2),
            }
            
            # Validation
            val_loss = None
            if step % args.val_every == 0:
                print(f"\nEvaluating validation loss at step {step}...")
                val_loss = evaluate_validation(model, val_batches, device)
                progress["val_loss"] = round(val_loss, 6)
                print(f"Validation loss: {val_loss:.4f}")
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_checkpoint_name = f"checkpoint_{step}"
                    print(f"⭐ New best validation: {val_loss:.4f}")
            
            progress_handle.write(json.dumps(progress) + "\n")
            progress_handle.flush()
            
            if step == 1 or step % 10 == 0:
                val_str = f", val_loss={val_loss:.4f}" if val_loss else ""
                print(f"step={step:,} train_loss={loss.item():.4f}{val_str}")
            
            # Checkpointing
            if step % args.checkpoint_every == 0:
                checkpoint_name = f"checkpoint_{step}"
                save_checkpoint(
                    model=model,
                    tokenizer=tokenizer,
                    optimizer=optimizer,
                    epoch=epoch,
                    step=step,
                    loss=loss.item(),
                    val_loss=val_loss,
                    output_dir=output_dir,
                    checkpoint_name=checkpoint_name,
                    rng_state=random.getstate(),
                )
                cleanup_old_checkpoints(output_dir, keep_last_n=args.keep_checkpoints)
        
        epoch += 1

    progress_handle.close()

    # Save final checkpoint
    print("\nSaving final checkpoint...")
    final_checkpoint_name = f"checkpoint_final_{step}"
    save_checkpoint(
        model=model,
        tokenizer=tokenizer,
        optimizer=optimizer,
        epoch=epoch,
        step=step,
        loss=loss.item(),
        val_loss=best_val_loss,
        output_dir=output_dir,
        checkpoint_name=final_checkpoint_name,
        rng_state=random.getstate(),
    )
    
    # Save best checkpoint
    if best_checkpoint_name:
        best_dir = output_dir / "best_checkpoint"
        best_dir.mkdir(parents=True, exist_ok=True)
        best_ckpt_dir = output_dir / "checkpoints" / best_checkpoint_name
        
        for item in best_ckpt_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, best_dir / item.name)
        
        (best_dir / "best_info.json").write_text(
            json.dumps({
                "description": "Best checkpoint by validation loss",
                "checkpoint": best_checkpoint_name,
                "val_loss": best_val_loss,
                "step": step,
            }, indent=2) + "\n"
        )
        print(f"⭐ Saved best checkpoint: {best_dir} (val_loss={best_val_loss:.4f})")
    
    # Create training report
    elapsed = time.time() - started_at
    report = {
        "model": MODEL_NAME,
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "max_steps": args.max_steps,
        "final_step": step,
        "final_train_loss": round(loss.item(), 6),
        "best_val_loss": round(best_val_loss, 6),
        "elapsed_hours": round(elapsed / 3600, 2),
        "steps_per_hour": round(step / (elapsed / 3600), 1),
    }
    (output_dir / "training_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    
    print(f"\n{'='*70}")
    print(f"✅ Training complete!")
    print(f"Final train loss: {loss.item():.4f}")
    print(f"Best val loss: {best_val_loss:.4f}")
    print(f"Total time: {elapsed/3600:.2f} hours")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
