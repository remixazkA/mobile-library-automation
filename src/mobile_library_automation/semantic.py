from __future__ import annotations

import json
import tomllib
from pathlib import Path

from PIL import Image, ImageOps


def score_photos(root: Path, config_path: Path) -> list[dict[str, object]]:
    """Score images with local OpenCLIP; imported lazily to keep the core light."""
    try:
        import open_clip
        import torch
    except ImportError as exc:
        raise RuntimeError('Install the optional ML stack with: pip install -e ".[ml]"') from exc

    config = tomllib.loads(config_path.read_text(encoding="utf-8"))["photos"]
    prompt_groups = config["prompts"]
    labels = list(prompt_groups)
    prompts = [prompt for label in labels for prompt in prompt_groups[label]]
    slices: dict[str, slice] = {}
    cursor = 0
    for label in labels:
        slices[label] = slice(cursor, cursor + len(prompt_groups[label]))
        cursor += len(prompt_groups[label])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = config.get("model", "ViT-B-32")
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name,
        pretrained=config.get("pretrained", "laion2b_s34b_b79k"),
    )
    tokenizer = open_clip.get_tokenizer(model_name)
    model = model.to(device).eval()

    with torch.inference_mode():
        text = model.encode_text(tokenizer(prompts).to(device))
        text = text / text.norm(dim=-1, keepdim=True)
        prototypes = torch.stack([text[slices[label]].mean(dim=0) for label in labels])
        prototypes = prototypes / prototypes.norm(dim=-1, keepdim=True)

    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    paths = [path for path in sorted(root.rglob("*")) if path.is_file() and path.suffix.lower() in extensions]
    batch_size = int(config.get("batch_size_cuda" if device == "cuda" else "batch_size_cpu", 16))
    scale = float(config.get("logit_scale", 35.0))
    output: list[dict[str, object]] = []

    for start in range(0, len(paths), batch_size):
        tensors = []
        valid: list[Path] = []
        for path in paths[start : start + batch_size]:
            try:
                with Image.open(path) as opened:
                    tensors.append(preprocess(ImageOps.exif_transpose(opened).convert("RGB")))
                valid.append(path)
            except Exception:
                continue
        if not tensors:
            continue
        batch = torch.stack(tensors).to(device)
        with torch.inference_mode():
            features = model.encode_image(batch)
            features = features / features.norm(dim=-1, keepdim=True)
            probabilities = (scale * features @ prototypes.T).softmax(dim=-1).float().cpu()
        for path, values in zip(valid, probabilities.tolist()):
            scores = {label: round(float(value), 6) for label, value in zip(labels, values)}
            winner = max(scores, key=scores.get)
            output.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "category": winner,
                    "scores": scores,
                }
            )
    return output


def write_scores(scores: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
