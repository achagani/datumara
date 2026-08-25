"""Create an Ollama model from a supported merged model directory."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

# Ollama's Safetensors support is architecture-specific. Keep this allowlist explicit.
SUPPORTED_ARCHITECTURES = {"LlamaForCausalLM", "MistralForCausalLM", "GemmaForCausalLM"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--name", required=True, help="Ollama model name")
    parser.add_argument("--modelfile", type=Path, default=Path("Modelfile"))
    args = parser.parse_args()

    config_path = args.model_dir / "config.json"
    if not config_path.exists():
        raise SystemExit(f"Missing merged Hugging Face config: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    architecture = config.get("architectures", [None])[0]
    if architecture not in SUPPORTED_ARCHITECTURES:
        supported = ", ".join(sorted(SUPPORTED_ARCHITECTURES))
        raise SystemExit(
            f"Architecture {architecture!r} is not enabled for Ollama export. "
            f"Supported architectures: {supported}. GPT-2 must be retrained on an Ollama-supported base."
        )

    if shutil.which("ollama") is None:
        raise SystemExit("Ollama is not installed or is not on PATH.")

    args.modelfile.write_text(
        f"FROM {args.model_dir.resolve()}\n"
        "PARAMETER temperature 0.1\n"
        "PARAMETER stop \"<|endoftext|>\"\n",
        encoding="utf-8",
    )
    subprocess.run(["ollama", "create", args.name, "-f", str(args.modelfile)], check=True)
    print(f"created={args.name}")


if __name__ == "__main__":
    main()
