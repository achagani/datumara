"""Train a small local LoRA adapter with checkpointing and resume support."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

from report import create_report

DEFAULT_DATA = Path(__file__).parent.parent / "data" / "spider_augmented_train.jsonl"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "models" / "local-gpt2-lora"
MODEL_ALIASES = {"tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"}


def load_examples(path: Path, limit: int) -> list[dict[str, str]]:
    examples = []
    with path.open(encoding="utf-8") as data_file:
        for line in data_file:
            examples.append(json.loads(line))
            if len(examples) >= limit:
                break
    if not examples:
        raise ValueError(f"No examples found in {path}")
    return examples


def encode_examples(tokenizer, examples, max_length: int, chat_format: bool) -> list[dict[str, torch.Tensor]]:
    encoded = []
    for example in examples:
        if chat_format:
            prompt_text = tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": "You are Datumara, an expert SQL assistant."},
                    {"role": "user", "content": example["prompt"]},
                ],
                tokenize=False,
                add_generation_prompt=True,
            )
            prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
            response_ids = tokenizer(
                f"{example['response']}{tokenizer.eos_token}", add_special_tokens=False
            )["input_ids"]
        else:
            prompt_ids = tokenizer(f"{example['prompt']}\nSQL:\n", add_special_tokens=False)["input_ids"]
            response_ids = tokenizer(
                f"{example['response']}{tokenizer.eos_token}", add_special_tokens=False
            )["input_ids"]
        available_prompt_tokens = max(1, max_length - len(response_ids))
        input_ids = torch.tensor((prompt_ids[-available_prompt_tokens:] + response_ids)[:max_length])
        attention_mask = torch.ones_like(input_ids)
        padding = max_length - input_ids.numel()
        if padding:
            input_ids = torch.cat(
                [input_ids, torch.full((padding,), tokenizer.pad_token_id, dtype=torch.long)]
            )
            attention_mask = torch.cat([attention_mask, torch.zeros(padding, dtype=torch.long)])
        labels = input_ids.clone()
        labels[attention_mask == 0] = -100
        encoded.append(
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }
        )
    return encoded


def save_checkpoint(
    model,
    tokenizer,
    optimizer,
    epoch: int,
    step: int,
    loss: float,
    output_dir: Path,
    checkpoint_name: str,
    rng_state: dict,
):
    """Save a training checkpoint with model weights and optimizer state."""
    checkpoint_dir = output_dir / "checkpoints" / checkpoint_name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model and adapter
    model.save_pretrained(checkpoint_dir)
    tokenizer.save_pretrained(checkpoint_dir)
    
    # Save optimizer state
    torch.save({
        "epoch": epoch,
        "step": step,
        "loss": loss,
        "optimizer_state_dict": optimizer.state_dict(),
        "rng_state": rng_state,
    }, checkpoint_dir / "training_state.pt")
    
    # Save metadata
    metadata = {
        "checkpoint_name": checkpoint_name,
        "epoch": epoch,
        "step": step,
        "loss": loss,
        "timestamp": time.time(),
    }
    (checkpoint_dir / "checkpoint_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    
    print(f"✓ Saved checkpoint: {checkpoint_name} (loss={loss:.4f})")


def load_checkpoint(checkpoint_dir: Path, model, tokenizer, optimizer, device):
    """Load a checkpoint and return training state."""
    training_state = torch.load(checkpoint_dir / "training_state.pt", map_location=device)
    
    # Load optimizer state
    optimizer.load_state_dict(training_state["optimizer_state_dict"])
    
    print(f"✓ Loaded checkpoint: {checkpoint_dir.name} (step={training_state['step']}, loss={training_state['loss']:.4f})")
    
    return training_state


def cleanup_old_checkpoints(output_dir: Path, keep_last_n: int = 3):
    """Keep only the last N checkpoints to save disk space."""
    checkpoints_dir = output_dir / "checkpoints"
    if not checkpoints_dir.exists():
        return
    
    # Get all checkpoint directories sorted by modification time
    checkpoint_dirs = [
        d for d in checkpoints_dir.iterdir()
        if d.is_dir() and d.name.startswith("checkpoint_")
    ]
    checkpoint_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    
    # Remove old checkpoints
    for old_checkpoint in checkpoint_dirs[keep_last_n:]:
        print(f"Removing old checkpoint: {old_checkpoint.name}")
        shutil.rmtree(old_checkpoint)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt2", choices=("gpt2", "tinyllama"))
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--examples", type=int, default=7000)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--progress-file", type=Path)
    parser.add_argument("--checkpoint-every", type=int, default=100,
                        help="Save checkpoint every N steps (default: 100)")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume from checkpoint directory (e.g., checkpoints/checkpoint_1200)")
    parser.add_argument("--keep-checkpoints", type=int, default=3,
                        help="Number of recent checkpoints to keep (default: 3)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}")
    if device.type == "cuda":
        print(f"gpu={torch.cuda.get_device_name(0)}")

    model_name = MODEL_ALIASES.get(args.model, args.model)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    target_modules = ["c_attn"] if model.config.model_type == "gpt2" else [
        "q_proj", "k_proj", "v_proj", "o_proj"
    ]
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=target_modules,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config).to(device)
    model.print_trainable_parameters()

    random.seed(args.seed)
    examples = load_examples(args.data, args.examples)
    random.shuffle(examples)
    batches = encode_examples(
        tokenizer,
        examples,
        args.max_length,
        chat_format=model.config.model_type != "gpt2",
    )
    progress_file = args.progress_file or args.output_dir / "training_progress.jsonl"
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    progress_handle = progress_file.open("w", encoding="utf-8")
    started_at = time.time()
    optimizer = torch.optim.AdamW(
        (parameter for parameter in model.parameters() if parameter.requires_grad),
        lr=1e-4,
    )
    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")
    model.train()
    
    # Initialize training state
    start_epoch = 0
    step = 0
    best_loss = float("inf")
    best_checkpoint_dir = None
    
    # Resume from checkpoint if requested
    if args.resume:
        resume_path = args.output_dir / "checkpoints" / args.resume
        if not resume_path.exists():
            raise SystemExit(f"Checkpoint not found: {resume_path}")
        
        # Load model weights from checkpoint
        print(f"Resuming from checkpoint: {args.resume}")
        training_state = load_checkpoint(resume_path, model, tokenizer, optimizer, device)
        start_epoch = training_state["epoch"]
        step = training_state["step"]
        best_loss = training_state.get("loss", float("inf"))
        best_checkpoint_dir = resume_path
        
        # Restore RNG state for reproducibility
        if "rng_state" in training_state:
            random.setstate(training_state["rng_state"])
    
    # Track best checkpoint
    best_checkpoint_name = None

    for epoch in range(start_epoch, args.epochs):
        for batch_idx, batch in enumerate(batches):
            # Skip batches already processed in resumed training
            if epoch == start_epoch and batch_idx < (step % len(batches)):
                continue
                
            optimizer.zero_grad(set_to_none=True)
            batch = {key: value.unsqueeze(0).to(device) for key, value in batch.items()}
            with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
                loss = model(**batch).loss
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            step += 1
            
            progress = {
                "epoch": epoch + 1,
                "step": step,
                "max_steps": args.max_steps,
                "loss": round(loss.item(), 6),
                "elapsed_seconds": round(time.time() - started_at, 2),
            }
            if device.type == "cuda":
                progress["gpu_allocated_gb"] = round(
                    torch.cuda.memory_allocated() / (1024**3), 3
                )
                progress["gpu_reserved_gb"] = round(
                    torch.cuda.memory_reserved() / (1024**3), 3
                )
            progress_handle.write(json.dumps(progress) + "\n")
            progress_handle.flush()
            
            if step == 1 or step % 5 == 0:
                print(f"epoch={epoch + 1} step={step} loss={loss.item():.4f}")
            
            # Save checkpoint every N steps
            if args.checkpoint_every > 0 and step % args.checkpoint_every == 0:
                checkpoint_name = f"checkpoint_{step}"
                save_checkpoint(
                    model=model,
                    tokenizer=tokenizer,
                    optimizer=optimizer,
                    epoch=epoch,
                    step=step,
                    loss=loss.item(),
                    output_dir=args.output_dir,
                    checkpoint_name=checkpoint_name,
                    rng_state=random.getstate(),
                )
                
                # Track best checkpoint by loss
                if loss.item() < best_loss:
                    best_loss = loss.item()
                    best_checkpoint_name = checkpoint_name
                    print(f"⭐ New best checkpoint: {checkpoint_name} (loss={best_loss:.4f})")
                
                # Cleanup old checkpoints
                cleanup_old_checkpoints(args.output_dir, keep_last_n=args.keep_checkpoints)
            
            if step >= args.max_steps:
                break
        if step >= args.max_steps:
            break
    
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
        output_dir=args.output_dir,
        checkpoint_name=final_checkpoint_name,
        rng_state=random.getstate(),
    )
    
    # Save best checkpoint separately
    if best_checkpoint_name:
        best_checkpoint_dir = args.output_dir / "checkpoints" / best_checkpoint_name
        best_output_dir = args.output_dir / "best_checkpoint"
        best_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy best checkpoint to best_checkpoint directory
        for item in best_checkpoint_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, best_output_dir / item.name)
        
        # Add metadata
        best_metadata = {
            "description": "Best checkpoint by training loss",
            "original_checkpoint": best_checkpoint_name,
            "best_loss": best_loss,
            "step": step,
        }
        (best_output_dir / "best_checkpoint_info.json").write_text(
            json.dumps(best_metadata, indent=2) + "\n", encoding="utf-8"
        )
        print(f"⭐ Saved best checkpoint to: {best_output_dir}")

    # Save final adapter to output directory (for backward compatibility)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    metadata = {
        "base_model": model_name,
        "examples": min(args.examples, len(examples)),
        "steps": step,
        "max_length": args.max_length,
        "seed": args.seed,
        "device": str(device),
        "trainable_parameters": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "progress_file": str(progress_file),
        "best_loss": best_loss,
        "best_checkpoint": best_checkpoint_name,
        "checkpointing_enabled": args.checkpoint_every > 0,
    }
    (args.output_dir / "training_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    
    create_report(args.output_dir)
    print(f"\n✅ Training complete!")
    print(f"Final adapter saved to: {args.output_dir}")
    print(f"Best checkpoint: {best_checkpoint_name} (loss={best_loss:.4f})")
    print(f"\nTo resume training if interrupted:")
    print(f"  python {__file__} --resume {final_checkpoint_name}")


if __name__ == "__main__":
    main()
