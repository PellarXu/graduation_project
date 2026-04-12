import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import build_bio_labels


def export_artifacts():
    root_dir = ROOT_DIR
    config = json.loads((root_dir / "training" / "configs" / "train_config.json").read_text(encoding="utf-8"))
    checkpoint_dir = root_dir / config["output_dir"]
    artifacts_dir = root_dir / "model" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    for file_name in [
        "model.pt",
        "metrics.json",
        "evaluation_report.json",
        "training_summary.json",
        "error_cases.json",
    ]:
        source = checkpoint_dir / file_name
        if source.exists():
            shutil.copy2(source, artifacts_dir / file_name)

    tokenizer_dir = checkpoint_dir / "tokenizer"
    if tokenizer_dir.exists():
        if (artifacts_dir / "tokenizer").exists():
            shutil.rmtree(artifacts_dir / "tokenizer")
        shutil.copytree(tokenizer_dir, artifacts_dir / "tokenizer")

    label_map = {
        "labels": build_bio_labels(),
        "id2label": {str(index): label for index, label in enumerate(build_bio_labels())},
        "label2id": {label: index for index, label in enumerate(build_bio_labels())},
    }
    (artifacts_dir / "label_map.json").write_text(json.dumps(label_map, ensure_ascii=False, indent=2), encoding="utf-8")

    inference_config = {
        "model_version": config["model_version"],
        "pretrained_model_name": config["pretrained_model_name"],
        "hidden_size": config["hidden_size"],
        "dropout": config["dropout"],
        "max_length": config["max_length"],
    }
    (artifacts_dir / "inference_config.json").write_text(json.dumps(inference_config, ensure_ascii=False, indent=2), encoding="utf-8")

    for manifest_name in ["dataset_manifest.json", "source_manifest.json"]:
        source = root_dir / "data" / "annotations" / manifest_name
        if source.exists():
            shutil.copy2(source, artifacts_dir / manifest_name)

    print(f"artifacts exported to {artifacts_dir}")


if __name__ == "__main__":
    export_artifacts()
