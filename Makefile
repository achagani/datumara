.PHONY: help setup verify hardware train train-local train-local-ollama report-local export-local-hf export-local-ollama train-7b benchmark evaluate compare clean

# Python interpreter
PYTHON := source venv/bin/activate && python

help:
	@echo "Datumara - Development Tasks"
	@echo ""
	@echo "Setup:"
	@echo "  make setup      - Create virtual environment and install dependencies"
	@echo ""
	@echo "Verification:"
	@echo "  make verify     - Run PoC verification (checks all components)"
	@echo "  make hardware   - Detect hardware and show eligible model profiles"
	@echo ""
	@echo "Data Preparation:"
	@echo "  make split      - Split augmented data into train/val/test"
	@echo ""
	@echo "Training:"
	@echo "  make train      - Train 3.5B model with default config"
	@echo "  make train-local - Train a small GPT-2 LoRA model on this machine"
	@echo "  make train-local-ollama - Train an Ollama-compatible TinyLlama adapter"
	@echo "  make report-local - Generate a Markdown report for a local run"
	@echo "  make export-local-hf - Merge the local adapter for Hugging Face"
	@echo "  make export-local-ollama - Build an Ollama model from a supported merge"
	@echo "  make train-7b   - Refuse unsupported 7B training on this 4GB GPU"
	@echo ""
	@echo "Evaluation:"
	@echo "  make benchmark  - Benchmark base Qwen 3.5 (baseline)"
	@echo "  make evaluate   - Evaluate trained model"
	@echo "  make compare    - Compare baseline vs trained model"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container with GPU"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean      - Remove pycache and temp files"
	@echo "  make clean-all  - Remove venv, models, checkpoints"

# Setup
setup:
	@echo "Setting up environment..."
	bash setup.sh

# Verification
verify:
	@echo "Running PoC verification..."
	source venv/bin/activate && python poc_verification.py

hardware:
	@echo "Detecting local hardware and model compatibility..."
	venv/bin/python training/hardware.py

# Data preparation
split:
	@echo "Splitting data into train/val/test..."
	source venv/bin/activate && python training/split_data.py

# Training
train:
	@echo "Training 3.5B model..."
	source venv/bin/activate && python training/train.py \
		--model qwen2.5-3.5b \
		--lora-config default \
		--training-config default

train-local:
	@echo "Training local GPT-2 LoRA model..."
	venv/bin/python training/train_local.py \
		--examples 64 \
		--max-steps 20 \
		--max-length 256 \
		--output-dir models/local-gpt2-lora

train-local-ollama:
	@echo "Training Ollama-compatible TinyLlama LoRA model..."
	venv/bin/python training/train_local.py \
		--model tinyllama \
		--examples 7000 \
		--max-steps 2000 \
		--max-length 256 \
		--output-dir models/local-tinyllama-lora

report-local:
	@echo "Generating local training report..."
	venv/bin/python training/report.py models/local-tinyllama-lora

export-local-hf:
	@echo "Merging local GPT-2 adapter for Hugging Face..."
	venv/bin/python training/export_huggingface.py \
		--adapter models/local-gpt2-lora \
		--base-model gpt2 \
		--output-dir models/local-gpt2-merged

export-local-ollama:
	@echo "Exporting Ollama-compatible local model..."
	venv/bin/python training/export_to_ollama.py \
		--model-dir models/local-tinyllama-merged \
		--name datumara-local

train-7b:
	@echo "qwen2.5-7b requires at least 8GB VRAM for QLoRA; this machine has 4GB."
	@echo "Use a larger GPU or update the model profile after validating CPU offload."
	@exit 1

# Evaluation
benchmark:
	@echo "Benchmarking base Qwen 3.5..."
	source venv/bin/activate && python training/benchmark_baseline.py \
		--model "Qwen/Qwen2.5-3.5B-Instruct" \
		--test-set data/test_set.jsonl \
		--output baseline_qwen3.5.json

evaluate:
	@echo "Evaluating trained model..."
	source venv/bin/activate && python training/evaluate.py \
		--model models/trained \
		--test-set data/test_set.jsonl \
		--output finetuned_results.json

compare:
	@echo "Comparing baseline vs trained..."
	source venv/bin/activate && python training/compare_models.py \
		--baseline baseline_qwen3.5.json \
		--finetuned finetuned_results.json \
		--report comparison_report.json

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t datumara:latest .
	@echo "✅ Built: datumara:latest"

docker-run:
	@echo "Running Docker container with GPU..."
	docker run --gpus all -it \
		-v $(PWD)/models:/workspace/models \
		-v $(PWD)/logs:/workspace/logs \
		datumara:latest

docker-shell:
	@echo "Opening shell in Docker container..."
	docker run --gpus all -it \
		-v $(PWD)/models:/workspace/models \
		-v $(PWD)/logs:/workspace/logs \
		datumara:latest bash

# Cleanup
clean:
	@echo "Cleaning pycache and temp files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	@echo "✅ Clean complete"

clean-all: clean
	@echo "Removing venv, models, and checkpoints..."
	rm -rf venv
	rm -rf models
	rm -rf checkpoints
	rm -rf logs
	@echo "✅ Full clean complete"
