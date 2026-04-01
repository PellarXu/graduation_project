import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from training.dataset import ResumeNERDataset


def validate_dataset():
    root_dir = ROOT_DIR
    config = json.loads((root_dir / "training" / "configs" / "train_config.json").read_text(encoding="utf-8"))
    dataset = ResumeNERDataset(
        file_path=str(root_dir / config["dev_file"]),
        tokenizer_name=config["pretrained_model_name"],
        max_length=config["max_length"],
    )
    print(f"验证集样本数：{len(dataset)}")
    if len(dataset):
        sample = dataset[0]
        print("首个样本张量键：", list(sample.keys()))


if __name__ == "__main__":
    validate_dataset()
