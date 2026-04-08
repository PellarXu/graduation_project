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
    config_path = root_dir / "training" / "configs" / "train_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    output_dir = root_dir / config["output_dir"]
    artifacts_dir = root_dir / "model" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "model.pt"
    tokenizer_dir = output_dir / "tokenizer"
    if not model_path.exists():
        raise FileNotFoundError("未找到训练后的 model.pt，请先完成训练。")

    shutil.copy2(model_path, artifacts_dir / "model.pt")
    if (artifacts_dir / "tokenizer").exists():
        shutil.rmtree(artifacts_dir / "tokenizer")
    shutil.copytree(tokenizer_dir, artifacts_dir / "tokenizer")

    labels = build_bio_labels()
    label_map = {
        "label2id": {label: idx for idx, label in enumerate(labels)},
        "id2label": {idx: label for idx, label in enumerate(labels)},
    }
    (artifacts_dir / "label_map.json").write_text(
        json.dumps(label_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifacts_dir / "inference_config.json").write_text(
        json.dumps(
            {
                "model_version": config["model_version"],
                "pretrained_model_name": config["pretrained_model_name"],
                "hidden_size": config["hidden_size"],
                "dropout": config["dropout"],
                "max_length": config["max_length"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    eval_report_path = output_dir / "eval_report.json"
    if eval_report_path.exists():
        shutil.copy2(eval_report_path, artifacts_dir / "eval_report.json")
    print(f"推理资源已导出到 {artifacts_dir}")


if __name__ == "__main__":
    export_artifacts()
