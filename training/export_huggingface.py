"""Merge a LoRA adapter into its base model for Hugging Face distribution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--push-to-hub", metavar="REPO_ID")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.adapter)
    base_model = AutoModelForCausalLM.from_pretrained(args.base_model)
    model = PeftModel.from_pretrained(base_model, args.adapter)
    merged_model = model.merge_and_unload()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(args.output_dir, safe_serialization=True)
    tokenizer.save_pretrained(args.output_dir)
    metadata = {
        "base_model": args.base_model,
        "source_adapter": str(args.adapter),
        "format": "merged Hugging Face Transformers model",
    }
    (args.output_dir / "export_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    if args.push_to_hub:
        merged_model.push_to_hub(args.push_to_hub)
        tokenizer.push_to_hub(args.push_to_hub)
        print(f"uploaded={args.push_to_hub}")
    else:
        print(f"saved={args.output_dir}")
        print("Upload later with: huggingface-cli upload <repo-id> <output-dir>")


if __name__ == "__main__":
    main()
