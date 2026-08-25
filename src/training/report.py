"""Create a human-readable report from a local training run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def create_report(run_dir: Path) -> Path:
    progress_path = run_dir / "training_progress.jsonl"
    metadata_path = run_dir / "training_metadata.json"
    if not progress_path.exists():
        raise FileNotFoundError(f"Missing progress log: {progress_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing training metadata: {metadata_path}")

    records = [json.loads(line) for line in progress_path.read_text().splitlines() if line]
    metadata = json.loads(metadata_path.read_text())
    losses = [record["loss"] for record in records]
    first_loss = losses[0]
    final_loss = losses[-1]
    improvement = first_loss - final_loss
    gpu_records = [record for record in records if "gpu_allocated_gb" in record]
    peak_gpu = max((record["gpu_reserved_gb"] for record in gpu_records), default=None)
    report_path = run_dir / "training_report.md"

    lines = [
        "# Datumara Training Report",
        "",
        f"- Base model: `{metadata['base_model']}`",
        f"- Device: `{metadata['device']}`",
        f"- Examples: `{metadata['examples']}`",
        f"- Steps completed: `{metadata['steps']}`",
        f"- Sequence length: `{metadata['max_length']}`",
        f"- Trainable parameters: `{metadata['trainable_parameters']:,}`",
        "",
        "## Progress",
        "",
        f"- Initial loss: `{first_loss:.4f}`",
        f"- Final loss: `{final_loss:.4f}`",
        f"- Loss change: `{improvement:+.4f}`",
        f"- Best loss: `{min(losses):.4f}`",
    ]
    if peak_gpu is not None:
        lines.append(f"- Peak reserved GPU memory: `{peak_gpu:.3f} GB`")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Adapter: `{run_dir / 'adapter_model.safetensors'}`",
            f"- Progress log: `{progress_path}`",
            f"- Metadata: `{metadata_path}`",
            "",
            "This report reflects training loss only. It is not an evaluation of SQL correctness or generalization.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    print(f"report={create_report(args.run_dir)}")


if __name__ == "__main__":
    main()
