import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import build_bio_labels
from algorithm.ner.model import AlbertBiGruCrf
from training.dataset import ResumeNERDataset
from training.metrics import evaluate_model


def parse_args():
    parser = argparse.ArgumentParser(description="Validate a trained checkpoint on the dev set.")
    parser.add_argument("--config", default="training/configs/train_config.json")
    parser.add_argument("--checkpoint-dir", default=None)
    return parser.parse_args()


def validate_dataset():
    root_dir = ROOT_DIR
    args = parse_args()
    config = json.loads((root_dir / args.config).read_text(encoding="utf-8"))
    dataset = ResumeNERDataset(
        file_path=str(root_dir / config["dev_file"]),
        tokenizer_name=config["pretrained_model_name"],
        max_length=config["max_length"],
    )
    data_loader = DataLoader(dataset, batch_size=config["batch_size"], shuffle=False)
    checkpoint_dir = root_dir / (args.checkpoint_dir or config["output_dir"])
    weights_path = checkpoint_dir / "model.pt"
    if not weights_path.exists():
        raise FileNotFoundError(f"未找到模型权重：{weights_path}")

    labels = build_bio_labels()
    id2label = {idx: label for idx, label in enumerate(labels)}
    model = AlbertBiGruCrf(
        pretrained_model_name=config["pretrained_model_name"],
        num_labels=len(labels),
        hidden_size=config["hidden_size"],
        dropout=config["dropout"],
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.to(device)

    report = evaluate_model(model, data_loader, device, id2label)
    report.update(
        {
            "device": str(device),
            "batch_size": config["batch_size"],
            "max_length": config["max_length"],
            "checkpoint_dir": str(checkpoint_dir),
        }
    )
    (checkpoint_dir / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    validate_dataset()
