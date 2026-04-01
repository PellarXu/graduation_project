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


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train():
    root_dir = ROOT_DIR
    config = json.loads((root_dir / "training" / "configs" / "train_config.json").read_text(encoding="utf-8"))
    set_seed(config["seed"])

    train_dataset = ResumeNERDataset(
        file_path=str(root_dir / config["train_file"]),
        tokenizer_name=config["pretrained_model_name"],
        max_length=config["max_length"],
    )
    train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlbertBiGruCrf(
        pretrained_model_name=config["pretrained_model_name"],
        num_labels=len(build_bio_labels()),
        hidden_size=config["hidden_size"],
        dropout=config["dropout"],
    ).to(device)
    optimizer = AdamW(model.parameters(), lr=config["learning_rate"])

    output_dir = root_dir / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

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
        print(f"Epoch {epoch + 1}/{config['epochs']} - loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), output_dir / "model.pt")
    model.encoder.save_pretrained(output_dir / "encoder")
    train_dataset.tokenizer.save_pretrained(output_dir / "tokenizer")
    print(f"训练完成，权重已保存到 {output_dir}")


if __name__ == "__main__":
    train()
