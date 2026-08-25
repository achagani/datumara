# Datumara Backlog

This is the working backlog for improving Datumara. Items are ordered by priority and should be checked off only after implementation and validation.

## P0: Make The Local Model Useful

- [ ] **Add checkpoint saving and resume support so interrupted runs do not lose progress.** ← Critical after 1192-step interruption
  - Save adapter weights every N steps (e.g., every 100 steps)
  - Save `last_checkpoint.txt` with step number for resume
  - Add `--resume` flag to training script to continue from last checkpoint
  - Keep only last 3 checkpoints to save disk space
- [ ] Add a held-out train/validation/test split with deterministic seed and complexity stratification.
- [ ] Mask prompt tokens from the loss so training scores the SQL completion rather than reproducing the prompt.
- [ ] Add validation loss during training and report train/validation curves.
- [ ] Add rolling loss averages and an ETA/steps-remaining display to live monitoring.
- [ ] Save the best checkpoint by validation loss instead of using only the final checkpoint.
- [ ] Add SQL-generation evaluation: parse validity, exact match, normalized match, and schema consistency.
- [ ] Add a post-training inference smoke test with bounded tokens and assert non-empty output.
- [ ] Fix the Ollama prompt template and stop tokens; verify output with a bounded automated inference test.
- [ ] Run a meaningful local TinyLlama experiment and record quality metrics, not only training loss.
- [ ] Compare training loss against validation loss to detect memorization and overfitting.

## P1: Complete The Hosted Training Path

- [ ] Implement `training/train.py` using the shared model, LoRA, training, and hardware configuration.
- [ ] Add runtime hardware eligibility checks before model loading and fail with actionable guidance.
- [ ] Add 4-bit QLoRA dependency and verify it on the target hosted GPU.
- [ ] Support configurable sequence length, micro-batch size, gradient accumulation, precision, and checkpoint interval.
- [ ] Add automatic batch-size/context-length recommendations from detected free VRAM.
- [ ] Implement curriculum learning and complexity-weighted loss only after baseline training is measurable.
- [ ] Add experiment configuration snapshots, random seeds, git revision, and environment metadata to every run.
- [ ] Add graceful handling for OOM, interruptions, and insufficient disk space.

## P1: Data And Evaluation Quality

- [ ] Validate every augmented example against its database schema and SQLite execution where possible.
- [ ] Detect and remove duplicate or contradictory examples across splits.
- [ ] Preserve the SQL answer when tokenizing long schema prompts; measure truncation rates by complexity.
- [ ] Use native chat templates for chat-tuned bases and verify prompt/response token boundaries.
- [ ] Report how many examples are processed per run when a step cap stops before the full dataset.
- [ ] Add a fixed evaluation set that is never used for training decisions.
- [ ] Implement Qwen baseline benchmarking and side-by-side comparison reports.
- [ ] Add hard-example mining from failed validation and test predictions.

## P2: Distribution And Operations

- [ ] Add one-command export from adapter to merged Hugging Face format.
- [ ] Add optional authenticated Hugging Face upload with model card, license, dataset attribution, and training metadata.
- [ ] Keep Ollama export architecture-aware and validate the created model with automated inference.
- [ ] Add a Datumara Ollama Modelfile with SQL-focused system instructions and conservative generation settings.
- [ ] Add model versioning and a changelog for published checkpoints.
- [ ] Add CI checks for Python syntax, YAML validity, report generation, and export smoke tests.

## P3: Product Improvements

- [ ] Add database dialect profiles for SQLite, PostgreSQL, BigQuery, Snowflake, and DuckDB.
- [ ] Add schema-aware SQL repair and validation before returning a query.
- [ ] Add analytics tasks beyond SQL generation: metric definitions, statistical summaries, and anomaly detection.
- [ ] Add a routing task for selecting the correct database or dialect.
- [ ] Add a simple local API or CLI with structured JSON output.
- [ ] Publish benchmark results with clear hardware, dataset, and reproducibility details.

## Completed Foundations

- [x] Runtime hardware detection and model capability profiles.
- [x] Local TinyLlama LoRA training on the Quadro T2000.
- [x] Per-step progress JSONL and Markdown training report.
- [x] Merged Hugging Face export.
- [x] Ollama registration for the TinyLlama-based local artifact.
