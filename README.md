<p align="center">
  <img src="docs/logo.svg" alt="Datumara Logo" width="200"/>
  <h1 align="center">Datumara</h1>
  <p align="center">The faster path from question to insight</p>
  <p align="center">
    <a href="https://achagani.github.io/datumara/">View Landing Page</a> •
    <a href="#install">Install</a> •
    <a href="#training">Training</a> •
    <a href="#models">Models</a>
  </p>
</p>

---

**Datumara** is an open-source analytics language model that turns business questions into schema-aware SQL and decision-ready answers. Run locally with Ollama or deploy on your own infrastructure.

## Install

### One-Command Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/achagani/datumara/main/install.sh | bash
```

This checks for Ollama, pulls the `datumara-local` model, and gets you started immediately.

### Manual Install

```bash
ollama pull datumara-local
```

### Start Using

```bash
ollama run datumara-local
```

**Example:**
```bash
ollama run datumara-local "Return only SQL: show all users"
```

---

## Quick Start

### Docker Setup

```bash
# 1. Build Docker image
docker build -t datumara:latest .

# 2. Run with GPU support
docker run --gpus all -it -v $(pwd)/models:/workspace/models datumara:latest

# 3. Inside container
python poc_verification.py
python training/train.py --model qwen2.5-3.5b --config default
```

---

## Project Structure

```
llm-analytics/
├── data/                          # Training data
│   ├── spider/                    # Spider dataset (schema files + examples)
│   ├── spider_augmented_train.jsonl  # Augmented training data (7k examples)
│   ├── train_set.jsonl            # Training split (60%)
│   ├── val_set.jsonl              # Validation split (20%)
│   └── test_set.jsonl             # Test split (20%)
│
├── training/                      # Training pipeline
│   ├── config/
│   │   ├── model_configs.yaml     # Model presets (3.5B, 7B, 13B)
│   │   ├── training_configs.yaml  # Hyperparameter presets
│   │   └── lora_configs.yaml      # LoRA parameter presets
│   ├── train.py                   # Main training script
│   ├── train_configs.py           # Config loader
│   ├── complexity_classifier.py   # Complexity detection
│   ├── evaluate.py                # Evaluation metrics
│   ├── benchmark_baseline.py      # Baseline benchmark
│   ├── compare_models.py          # Model comparison
│   ├── hard_example_mining.py     # Hard example detection
│   └── export_to_ollama.py        # Export for Ollama deployment
│
├── models/                        # Saved models & checkpoints
├── logs/                          # Training logs
├── poc_verification.py            # PoC verification script
├── augment_spider_data.py         # Data augmentation script
├── requirements.txt               # Python dependencies
├── BACKLOG.md                     # Prioritized improvement backlog
├── pyproject.toml                 # Project metadata
├── setup.sh                       # Setup script
├── Dockerfile                     # Docker build file
└── README.md                      # This file
```

## Dependencies

### System Requirements
- Python 3.10+
- NVIDIA GPU with CUDA support
- 50GB+ disk space for models and checkpoints
- Model-specific VRAM and quantization requirements are defined in `training/config/model_configs.yaml`

### Verified Local Hardware

The compatibility table is a profile catalog, not a machine-specific result. Run `make hardware` on every machine; the probe detects CUDA, GPU VRAM, CPU count, and system RAM at runtime. This workstation exposes 3.63 GiB VRAM (4GB class). The smoke tests verify CUDA and LoRA mechanics with GPT-2; they do not prove that every supported Qwen model fits.

| Project profile | Actual model | Inference | LoRA training | Local status |
|---|---|---:|---:|---|
| `qwen2.5-3.5b` | Qwen2.5-3B-Instruct | 4-bit, about 3GB minimum | 4-bit QLoRA, 4GB minimum | Experimental |
| `qwen2.5-7b` | Qwen2.5-7B-Instruct | About 5GB minimum | About 8GB minimum | Unsupported |
| `qwen2.5-13b` | Qwen2.5-14B-Instruct | About 10GB minimum | About 16GB minimum | Unsupported |

The 3B-class training path requires a tested 4-bit backend such as `bitsandbytes`, batch size 1, short sequences, and gradient accumulation. Full-precision and 8-bit training are not viable within 4GB VRAM. The approximate thresholds are planning values; `make hardware` is the first eligibility check, followed by a real model-loading test.

### Python Dependencies
See `requirements.txt` for full list. Key packages:
- PyTorch >= 2.0.0
- Transformers >= 5.0.0 (HuggingFace)
- PEFT >= 0.4.0 (LoRA adapters)
- Datasets >= 2.0.0
- Accelerate >= 0.12.0 (GPU optimization)
- SQLParse >= 0.4.0 (SQL validation)

## Verification

Before training, run the PoC verification:

```bash
source venv/bin/activate
python poc_verification.py
```

This checks:
1. ✅ Dependencies installed correctly
2. ✅ GPU/CUDA availability
3. ✅ Model loading works
4. ✅ LoRA adapter setup
5. ✅ Data loading and format
6. ✅ Complexity classification
7. ✅ Evaluation metrics
8. ✅ Training loop (forward/backward pass)
9. ✅ Disk space available

To inspect hardware and profile eligibility on another machine:

```bash
source venv/bin/activate
python training/hardware.py
python training/hardware.py --json
```

## Training

### First Local Model

Use the small cached GPT-2 model to validate the complete training and checkpoint path on a low-VRAM machine:

```bash
source venv/bin/activate
make train-local
```

This creates `models/local-gpt2-lora`. It is an end-to-end pipeline smoke model, not the production analytics model. The hosted-GPU run should use the Qwen profile after the same runtime checks pass.

Each run prints `step` and `loss`, and writes one JSON record per step to `training_progress.jsonl`. GPU memory usage is included when CUDA is available:

```bash
tail -f models/local-gpt2-lora/training_progress.jsonl
```

When training completes, the trainer also writes `training_report.md`. To regenerate a report from an existing run:

```bash
make report-local
```

Open `models/local-tinyllama-lora/training_report.md` to review the model, device, examples, steps, loss change, best loss, and peak reserved GPU memory. The report explicitly covers training loss; SQL quality requires a separate evaluation step.

### Ollama-Compatible Local Model

GPT-2 is useful for validating training but is not an Ollama-supported export architecture. To create a local model that can be used by both Hugging Face and Ollama, train the TinyLlama profile. Stop any loaded Ollama model first so it does not consume GPU memory:

```bash
make train-local-ollama
python training/export_huggingface.py \
  --adapter models/local-tinyllama-lora \
  --base-model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --output-dir models/local-tinyllama-merged
python training/export_to_ollama.py \
  --model-dir models/local-tinyllama-merged \
  --name datumara-local
ollama run datumara-local
```

The default local run uses all 7,000 examples, one shuffled pass capped at 2,000 steps, sequence length 256, batch size 1, gradient checkpointing, and LoRA. It is designed to use the available GPU while remaining bounded. The TinyLlama download is larger than GPT-2 and its 1.1B model still needs conservative settings on this 3.63 GiB GPU. The exporter validates the architecture before creating the Ollama model.

Do not run Ollama inference at the same time as training on this GPU. Check memory with `make hardware` before starting, and run `ollama stop datumara-local` if the model is loaded.

### Basic Training

```bash
source venv/bin/activate

# Train the experimental 3B-class QLoRA profile only after validating its backend
python training/train.py \
  --model qwen2.5-3.5b \
  --lora-config default \
  --training-config default

# Or with custom parameters
python training/train.py \
  --model qwen2.5-3.5b \
  --batch-size 4 \
  --learning-rate 1e-4 \
  --num-epochs 3 \
  --output-dir models/trained
```

### Training with Curriculum Learning

Curriculum learning gradually increases complexity:
- Epoch 1: Simple queries only
- Epoch 2: Simple + Medium queries
- Epoch 3: All complexity levels

Configured in `training/config/training_configs.yaml`

### Complexity-Aware Training

Model is weighted to focus on complex queries:
- Simple: 1x weight
- Medium: 2x weight
- Complex: 4x weight

## Evaluation

### Baseline Benchmark

Test base Qwen 3.5 (zero-shot) on Spider test set:

```bash
python training/benchmark_baseline.py \
  --model "Qwen/Qwen2.5-3.5B-Instruct" \
  --test-set data/test_set.jsonl \
  --output baseline_qwen3.5.json
```

### Evaluate Fine-tuned Model

```bash
python training/evaluate.py \
  --model models/trained \
  --test-set data/test_set.jsonl \
  --output finetuned_results.json
```

### Compare Models

```bash
python training/compare_models.py \
  --baseline baseline_qwen3.5.json \
  --finetuned finetuned_results.json \
  --report comparison_report.json
```

## Metrics

The model is evaluated on:

1. **SQL Validity** — Does the generated SQL parse correctly?
2. **Exact Match** — Does it match the expected query exactly?
3. **Semantic Match** — Does it represent the same query (accounting for formatting)?
4. **Schema Consistency** — Do all referenced tables/columns exist in the schema?

All metrics are reported by complexity level (simple, medium, complex).

## Model Profiles

The project profile names are preserved for compatibility, but the actual Qwen model IDs and hardware requirements are defined in `training/config/model_configs.yaml`:

- **qwen2.5-3.5b** maps to `Qwen/Qwen2.5-3B-Instruct`; experimental locally with 4-bit QLoRA
- **qwen2.5-7b** maps to `Qwen/Qwen2.5-7B-Instruct`; requires a larger GPU
- **qwen2.5-13b** maps to `Qwen/Qwen2.5-14B-Instruct`; requires a larger GPU

These are configuration profiles, not claims that all three models have been tested locally. Any additional HuggingFace model needs an explicit profile before it is used.

## Model Configuration

Edit `training/config/model_configs.yaml` to:
- Add new models
- Adjust LoRA ranks
- Configure quantization (8-bit, 4-bit)
- Set batch sizes and memory requirements

## Models

### Datumara Local (1.1B)

**Status:** ✅ Available  
**Use case:** Private local analytics  
**Runtime:** Ollama / 4GB GPU class

```bash
ollama run datumara-local
```

### Datumara SQL (3B class)

**Status:** 🚧 Coming next  
**Use case:** Production SQL workflows  
**Runtime:** Hosted GPU

### Datumara Scale (7B+)

**Status:** 📋 Roadmap  
**Use case:** Deep analytical workloads  
**Runtime:** High-memory GPU

---

## Training

### First Local Model

Use the small cached GPT-2 model to validate the complete training and checkpoint path on a low-VRAM machine:

```bash
source venv/bin/activate
make train-local
```

This creates `models/local-gpt2-lora`. It is an end-to-end pipeline smoke model, not the production analytics model. The hosted-GPU run should use the Qwen profile after the same runtime checks pass.

Each run prints `step` and `loss`, and writes one JSON record per step to `training_progress.jsonl`. GPU memory usage is included when CUDA is available:

```bash
tail -f models/local-gpt2-lora/training_progress.jsonl
```

When training completes, the trainer also writes `training_report.md`. To regenerate a report from an existing run:

```bash
make report-local
```

Open `models/local-tinyllama-lora/training_report.md` to review the model, device, examples, steps, loss change, best loss, and peak reserved GPU memory. The report explicitly covers training loss; SQL quality requires a separate evaluation step.

### Ollama-Compatible Local Model

GPT-2 is useful for validating training but is not an Ollama-supported export architecture. To create a local model that can be used by both Hugging Face and Ollama, train the TinyLlama profile. Stop any loaded Ollama model first so it does not consume GPU memory:

```bash
make train-local-ollama
python training/export_huggingface.py \
  --adapter models/local-tinyllama-lora \
  --base-model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --output-dir models/local-tinyllama-merged
python training/export_to_ollama.py \
  --model-dir models/local-tinyllama-merged \
  --name datumara-local
ollama run datumara-local
```

The default local run uses all 7,000 examples, one shuffled pass capped at 2,000 steps, sequence length 256, batch size 1, gradient checkpointing, and LoRA. It is designed to use the available GPU while remaining bounded. The TinyLlama download is larger than GPT-2 and its 1.1B model still needs conservative settings on this 3.63 GiB GPU. The exporter validates the architecture before creating the Ollama model.

Do not run Ollama inference at the same time as training on this GPU. Check memory with `make hardware` before starting, and run `ollama stop datumara-local` if the model is loaded.

### Basic Training

```bash
source venv/bin/activate

# Train the experimental 3B-class QLoRA profile only after validating its backend
python training/train.py \
  --model qwen2.5-3.5b \
  --lora-config default \
  --training-config default

# Or with custom parameters
python training/train.py \
  --model qwen2.5-3.5b \
  --batch-size 4 \
  --learning-rate 1e-4 \
  --num-epochs 3 \
  --output-dir models/trained
```

### Training with Curriculum Learning

Curriculum learning gradually increases complexity:
- Epoch 1: Simple queries only
- Epoch 2: Simple + Medium queries
- Epoch 3: All complexity levels

Configured in `training/config/training_configs.yaml`

### Complexity-Aware Training

Model is weighted to focus on complex queries:
- Simple: 1x weight
- Medium: 2x weight
- Complex: 4x weight

---

## Evaluation

### Baseline Benchmark

Test base Qwen 3.5 (zero-shot) on Spider test set:

```bash
python training/benchmark_baseline.py \
  --model "Qwen/Qwen2.5-3.5B-Instruct" \
  --test-set data/test_set.jsonl \
  --output baseline_qwen3.5.json
```

### Evaluate Fine-tuned Model

```bash
python training/evaluate.py \
  --model models/trained \
  --test-set data/test_set.jsonl \
  --output finetuned_results.json
```

### Compare Models

```bash
python training/compare_models.py \
  --baseline baseline_qwen3.5.json \
  --finetuned finetuned_results.json \
  --report comparison_report.json
```

## Metrics

The model is evaluated on:

1. **SQL Validity** — Does the generated SQL parse correctly?
2. **Exact Match** — Does it match the expected query exactly?
3. **Semantic Match** — Does it represent the same query (accounting for formatting)?
4. **Schema Consistency** — Do all referenced tables/columns exist in the schema?

All metrics are reported by complexity level (simple, medium, complex).

## Model Profiles

The project profile names are preserved for compatibility, but the actual Qwen model IDs and hardware requirements are defined in `training/config/model_configs.yaml`:

- **qwen2.5-3.5b** maps to `Qwen/Qwen2.5-3B-Instruct`; experimental locally with 4-bit QLoRA
- **qwen2.5-7b** maps to `Qwen/Qwen2.5-7B-Instruct`; requires a larger GPU
- **qwen2.5-13b** maps to `Qwen/Qwen2.5-14B-Instruct`; requires a larger GPU

These are configuration profiles, not claims that all three models have been tested locally. Any additional HuggingFace model needs an explicit profile before it is used.

## Model Configuration

Edit `training/config/model_configs.yaml` to:
- Add new models
- Adjust LoRA ranks
- Configure quantization (8-bit, 4-bit)
- Set batch sizes and memory requirements

---

## Troubleshooting

### Out of Memory (OOM)
- Reduce batch size
- Enable gradient checkpointing
- Use the quantization mode specified by the model profile
- Use the 3B-class profile instead of 7B or 14B
- Do not assume CPU offload makes training practical; measure it separately

### Slow Training
- Check GPU is being used: `nvidia-smi` while training
- Increase batch size if memory allows
- Enable mixed precision training

### Poor Accuracy
- Check complexity distribution in training data
- Verify curriculum learning is enabled
- Increase number of epochs
- Adjust learning rate

### Data Issues
- Verify Spider data downloaded: `ls data/spider/`
- Check JSONL format: `head -1 data/spider_augmented_train.jsonl`
- Verify train/val/test split was created

## Multi-Database Routing (Future)

The architecture is designed to support routing across multiple databases:
- Currently: SQL generation for single schema
- Planned: Database selection + SQL generation

To prepare your data for routing, augment examples with a `routing` field in the response JSONL.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test with PoC verification
4. Submit a pull request

## License

MIT — Open source under the MIT license

---

<p align="center">
  <strong>Datumara</strong> — Built for people who ask the next useful question.
</p>
<p align="center">
  <a href="https://achagani.github.io/datumara/">Visit datumara.dev</a> •
  <a href="https://github.com/achagani/datumara">GitHub</a> •
  <a href="https://docs.google.com/forms/d/e/1FAIpQLSfCbaGv-E5dhgbGUbUbYg9GCYMKXJrpQLq0-5IWtE-IPRM3iw/viewform">Join Early Access</a>
</p>

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review training logs in `logs/`
3. Run `poc_verification.py` to isolate the problem
4. Open an issue with debug info
