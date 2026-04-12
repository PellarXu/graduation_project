import argparse
import json
import sys
from pathlib import Path

import torch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import build_bio_labels
from algorithm.ner.model import build_ner_model
from training.dataset import ResumeNERDataset
from training.metrics import evaluate_model


def parse_args():
    parser = argparse.ArgumentParser(description="Validate a trained checkpoint on a dataset split.")
    parser.add_argument("--config", default="training/configs/train_config.json")
    parser.add_argument("--checkpoint-dir", default=None)
    parser.add_argument("--split", choices=["dev", "test"], default="test")
    return parser.parse_args()


def validate_dataset():
    args = parse_args()
    config = json.loads((ROOT_DIR / args.config).read_text(encoding="utf-8"))
    checkpoint_dir = ROOT_DIR / (args.checkpoint_dir or config["output_dir"])
    weights_path = checkpoint_dir / "model.pt"
    if not weights_path.exists():
        raise FileNotFoundError(f"checkpoint not found: {weights_path}")

    dataset_key = f"{args.split}_file"
    dataset = ResumeNERDataset(str(ROOT_DIR / config[dataset_key]), config["pretrained_model_name"], config["max_length"])
    data_loader = torch.utils.data.DataLoader(dataset, batch_size=config["eval_batch_size"], shuffle=False)
    labels = build_bio_labels()
    id2label = {idx: label for idx, label in enumerate(labels)}

    model = build_ner_model(
        model_type=config.get("model_type", "albert_bigru_crf"),
        pretrained_model_name=config["pretrained_model_name"],
        num_labels=len(labels),
        hidden_size=config["hidden_size"],
        dropout=config["dropout"],
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.to(device)

    report = evaluate_model(model, data_loader, device, id2label)
    report.update({"device": str(device), "split": args.split, "checkpoint_dir": str(checkpoint_dir)})
    output_name = "evaluation_report.json" if args.split == "test" else f"{args.split}_report.json"
    (checkpoint_dir / output_name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    validate_dataset()
