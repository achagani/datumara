"""Detect local hardware and compare it with model capability profiles."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path(__file__).parent / "config" / "model_configs.yaml"


def _system_ram_gb() -> float | None:
    """Read total RAM without adding a platform-specific dependency."""
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) / (1024 * 1024)
    except (OSError, ValueError):
        return None
    return None


def detect_hardware() -> dict[str, Any]:
    """Return hardware facts available to the current Python environment."""
    hardware: dict[str, Any] = {
        "cpu_count": os.cpu_count(),
        "system_ram_gb": _system_ram_gb(),
        "cuda_available": False,
        "gpus": [],
    }

    try:
        import torch

        hardware["cuda_available"] = bool(torch.cuda.is_available())
        if hardware["cuda_available"]:
            for index in range(torch.cuda.device_count()):
                properties = torch.cuda.get_device_properties(index)
                hardware["gpus"].append(
                    {
                        "index": index,
                        "name": properties.name,
                        "vram_gb": properties.total_memory / (1024**3),
                    }
                )
    except ImportError:
        hardware["torch_installed"] = False
    else:
        hardware["torch_installed"] = True

    hardware["max_gpu_vram_gb"] = max(
        (gpu["vram_gb"] for gpu in hardware["gpus"]), default=0.0
    )
    return hardware


def load_profiles(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Load model profiles from YAML."""
    with config_path.open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def assess_profiles(
    hardware: dict[str, Any], profiles: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Calculate runtime compatibility from detected hardware."""
    results = {}
    vram_gb = hardware["max_gpu_vram_gb"]

    for name, profile in profiles["models"].items():
        training = profile["lora_training"]
        inference = profile["inference"]
        results[name] = {
            "model_id": profile["model_id"],
            "inference_vram_ok": vram_gb >= inference["min_vram_gb"],
            "training_vram_ok": vram_gb >= training["min_vram_gb"],
            "inference_min_vram_gb": inference["min_vram_gb"],
            "training_min_vram_gb": training["min_vram_gb"],
            "configured_status": training["status_on_local_gpu"],
            "runtime_status": (
                "eligible"
                if hardware["cuda_available"] and vram_gb >= training["min_vram_gb"]
                else "unsupported"
            ),
        }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    hardware = detect_hardware()
    results = assess_profiles(hardware, load_profiles(args.config))
    report = {"hardware": hardware, "profiles": results}

    if args.as_json:
        print(json.dumps(report, indent=2))
        return

    print(f"CUDA available: {hardware['cuda_available']}")
    print(f"System RAM: {hardware['system_ram_gb'] or 'unknown'} GB")
    print(f"Max GPU VRAM: {hardware['max_gpu_vram_gb']:.2f} GB")
    for name, result in results.items():
        print(
            f"{name}: {result['runtime_status']} "
            f"(training requires {result['training_min_vram_gb']} GB VRAM; "
            f"{result['model_id']})"
        )


if __name__ == "__main__":
    main()
