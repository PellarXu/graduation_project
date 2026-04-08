import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import build_bio_labels
from algorithm.ner.model import AlbertBiGruCrf
from training.dataset import ResumeNERDataset
from training.metrics import evaluate_model


def parse_args():
    parser = argparse.ArgumentParser(description="Train ALBERT-BiGRU-CRF for Chinese resume NER.")
    parser.add_argument("--config", default="training/configs/train_config.json")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--max-length", type=int, default=None)
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_config(root_dir: Path, args):
    config = json.loads((root_dir / args.config).read_text(encoding="utf-8"))
    if args.epochs is not None:
        config["epochs"] = args.epochs
    if args.batch_size is not None:
        config["batch_size"] = args.batch_size
    if args.max_length is not None:
        config["max_length"] = args.max_length
    if args.output_dir is not None:
        config["output_dir"] = args.output_dir
    return config


def train():
    root_dir = ROOT_DIR
    args = parse_args()
    config = load_config(root_dir, args)
    set_seed(config["seed"])

    train_dataset = ResumeNERDataset(
        file_path=str(root_dir / config["train_file"]),
        tokenizer_name=config["pretrained_model_name"],
        max_length=config["max_length"],
    )
    dev_dataset = ResumeNERDataset(
        file_path=str(root_dir / config["dev_file"]),
        tokenizer_name=config["pretrained_model_name"],
        max_length=config["max_length"],
    )
    train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=True)
    dev_loader = DataLoader(dev_dataset, batch_size=config["batch_size"], shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    labels = build_bio_labels()
    id2label = {idx: label for idx, label in enumerate(labels)}
    model = AlbertBiGruCrf(
        pretrained_model_name=config["pretrained_model_name"],
        num_labels=len(labels),
        hidden_size=config["hidden_size"],
        dropout=config["dropout"],
    ).to(device)
    optimizer = AdamW(model.parameters(), lr=config["learning_rate"])

    output_dir = root_dir / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    best_f1 = -1.0
    best_report = {}
    best_state_dict = None

    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs["loss"]
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / max(len(train_loader), 1)
        report = evaluate_model(model, dev_loader, device, id2label)
        report.update(
            {
                "epoch": epoch + 1,
                "train_loss": round(avg_loss, 4),
                "device": str(device),
                "batch_size": config["batch_size"],
                "max_length": config["max_length"],
            }
        )
        print(
            f"Epoch {epoch + 1}/{config['epochs']} - loss: {avg_loss:.4f} - "
            f"precision: {report['precision']:.4f} - recall: {report['recall']:.4f} - f1: {report['f1_score']:.4f}"
        )

        if report["f1_score"] >= best_f1:
            best_f1 = report["f1_score"]
            best_report = report
            best_state_dict = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state_dict is None:
        raise RuntimeError("训练未产生有效模型权重。")

    torch.save(best_state_dict, output_dir / "model.pt")
    (output_dir / "eval_report.json").write_text(
        json.dumps(best_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    model.load_state_dict(torch.load(output_dir / "model.pt", map_location=device))
    model.encoder.save_pretrained(output_dir / "encoder")
    train_dataset.tokenizer.save_pretrained(output_dir / "tokenizer")
    print(f"训练完成，最佳权重已保存到 {output_dir}")


if __name__ == "__main__":
    train()
