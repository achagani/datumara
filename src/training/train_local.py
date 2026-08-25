"""Train a small local LoRA adapter as an end-to-end pipeline smoke test."""

from __future__ import annotations

import argparse
import json
import random
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
    step = 0

    for epoch in range(args.epochs):
        for batch in batches:
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
            if step >= args.max_steps:
                break
        if step >= args.max_steps:
            break
    progress_handle.close()

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
    }
    (args.output_dir / "training_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    create_report(args.output_dir)
    print(f"saved={args.output_dir}")


if __name__ == "__main__":
    main()
