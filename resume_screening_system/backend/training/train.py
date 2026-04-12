import argparse
import copy
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader, RandomSampler, Subset, WeightedRandomSampler
from transformers import get_linear_schedule_with_warmup

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import ENTITY_LABELS, build_bio_labels
from algorithm.ner.model import build_ner_model
from training.dataset import ResumeNERDataset
from training.metrics import evaluate_model


TAIL_LABELS = ["GENDER", "AGE", "HOMETOWN", "PROJECT", "COMPANY", "TITLE", "EXPERIENCE_YEARS"]


def parse_args():
    parser = argparse.ArgumentParser(description="Train ALBERT-BiGRU-CRF for Chinese resume NER.")
    parser.add_argument("--config", default="training/configs/train_config.json")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--epochs", type=int, default=None)
    return parser.parse_args()


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_config(root_dir: Path, args):
    config = json.loads((root_dir / args.config).read_text(encoding="utf-8"))
    if args.output_dir is not None:
        config["output_dir"] = args.output_dir
    if args.epochs is not None:
        config["epochs"] = args.epochs
    return config


def build_optimizer(model, config):
    no_decay = ["bias", "LayerNorm.weight"]
    encoder_params = []
    task_params = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        target = encoder_params if name.startswith("encoder.") else task_params
        target.append((name, parameter))

    optimizer_grouped_parameters = [
        {
            "params": [parameter for name, parameter in encoder_params if not any(term in name for term in no_decay)],
            "lr": config["encoder_learning_rate"],
            "weight_decay": config["weight_decay"],
        },
        {
            "params": [parameter for name, parameter in encoder_params if any(term in name for term in no_decay)],
            "lr": config["encoder_learning_rate"],
            "weight_decay": 0.0,
        },
        {
            "params": [parameter for name, parameter in task_params if not any(term in name for term in no_decay)],
            "lr": config["task_learning_rate"],
            "weight_decay": config["weight_decay"],
        },
        {
            "params": [parameter for name, parameter in task_params if any(term in name for term in no_decay)],
            "lr": config["task_learning_rate"],
            "weight_decay": 0.0,
        },
    ]
    return AdamW(optimizer_grouped_parameters)


def make_data_loader(dataset, batch_size, num_workers, shuffle=False, sampler=None):
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle if sampler is None else False,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )


def build_train_loader(dataset, config):
    if config.get("oversample_tail_labels"):
        weights = dataset.build_sample_weights(TAIL_LABELS)
        sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
        return make_data_loader(dataset, config["train_batch_size"], config["dataloader_num_workers"], sampler=sampler)
    return make_data_loader(dataset, config["train_batch_size"], config["dataloader_num_workers"], sampler=RandomSampler(dataset))


def build_warm_start_loaders(dataset, config):
    total = len(dataset)
    dev_size = max(1, int(total * 0.1))
    train_size = max(1, total - dev_size)
    generator = torch.Generator().manual_seed(config["seed"])
    train_subset, dev_subset = torch.utils.data.random_split(dataset, [train_size, dev_size], generator=generator)
    return (
        make_data_loader(train_subset, config["train_batch_size"], config["dataloader_num_workers"], shuffle=True),
        make_data_loader(dev_subset, config["eval_batch_size"], config["dataloader_num_workers"], shuffle=False),
    )


def run_stage(model, train_loader, eval_loader, config, stage_name, device, output_dir):
    optimizer = build_optimizer(model, config)
    optimizer_steps_per_epoch = max(len(train_loader) // max(config["gradient_accumulation_steps"], 1), 1)
    total_steps = optimizer_steps_per_epoch * config["epochs"]
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=max(1, int(total_steps * config["warmup_ratio"])),
        num_training_steps=max(total_steps, 1),
    )
    use_fp16 = torch.cuda.is_available() and config.get("fp16", False)
    scaler = torch.amp.GradScaler("cuda", enabled=use_fp16)
    id2label = {index: label for index, label in enumerate(build_bio_labels())}

    stage_dir = output_dir / stage_name
    stage_dir.mkdir(parents=True, exist_ok=True)

    best_metric = -1.0
    best_report = {}
    best_state_dict = None
    metrics_history = []
    patience = 0

    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0.0
        optimizer.zero_grad(set_to_none=True)
        for step, batch in enumerate(train_loader, start=1):
            tensor_batch = {key: value.to(device) for key, value in batch.items() if hasattr(value, "to")}
            with torch.amp.autocast("cuda", enabled=use_fp16):
                outputs = model(
                    input_ids=tensor_batch["input_ids"],
                    attention_mask=tensor_batch["attention_mask"],
                    labels=tensor_batch["labels"],
                )
                loss = outputs["loss"] / max(config["gradient_accumulation_steps"], 1)

            scaler.scale(loss).backward()
            total_loss += loss.item()

            if step % config["gradient_accumulation_steps"] == 0 or step == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), config["max_grad_norm"])
                previous_scale = scaler.get_scale()
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                if scaler.get_scale() <= previous_scale:
                    scheduler.step()

        avg_loss = total_loss / max(len(train_loader), 1)
        report = evaluate_model(model, eval_loader, device, id2label)
        report.update(
            {
                "stage": stage_name,
                "epoch": epoch + 1,
                "train_loss": round(avg_loss, 4),
                "device": str(device),
                "train_batch_size": config["train_batch_size"],
                "eval_batch_size": config["eval_batch_size"],
                "gradient_accumulation_steps": config["gradient_accumulation_steps"],
                "max_length": config["max_length"],
            }
        )
        metrics_history.append(report)
        print(
            f"[{stage_name}] epoch {epoch + 1}/{config['epochs']} "
            f"loss={avg_loss:.4f} micro_f1={report['entity_micro_f1']:.4f} macro_f1={report['entity_macro_f1']:.4f}"
        )

        metric_value = report.get(config["save_best_metric"], report["entity_micro_f1"])
        if metric_value >= best_metric:
            best_metric = metric_value
            best_report = report
            best_state_dict = copy.deepcopy(model.state_dict())
            torch.save(best_state_dict, stage_dir / "model.pt")
            (stage_dir / "best_report.json").write_text(json.dumps(best_report, ensure_ascii=False, indent=2), encoding="utf-8")
            patience = 0
        else:
            patience += 1
            if patience >= config["early_stopping_patience"]:
                break

    if best_state_dict is None:
        raise RuntimeError(f"stage {stage_name} did not produce a valid checkpoint")

    (stage_dir / "metrics.json").write_text(json.dumps(metrics_history, ensure_ascii=False, indent=2), encoding="utf-8")
    (stage_dir / "error_cases.json").write_text(
        json.dumps(best_report.get("error_cases", []), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    model.load_state_dict(best_state_dict)
    return model, best_report, metrics_history


def build_model(config, device):
    model = build_ner_model(
        model_type=config.get("model_type", "albert_bigru_crf"),
        pretrained_model_name=config["pretrained_model_name"],
        num_labels=len(build_bio_labels()),
        hidden_size=config["hidden_size"],
        dropout=config["dropout"],
    )
    model.to(device)
    return model


def train():
    args = parse_args()
    config = load_config(ROOT_DIR, args)
    set_seed(config["seed"])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output_dir = ROOT_DIR / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    train_dataset = ResumeNERDataset(str(ROOT_DIR / config["train_file"]), config["pretrained_model_name"], config["max_length"])
    dev_dataset = ResumeNERDataset(str(ROOT_DIR / config["dev_file"]), config["pretrained_model_name"], config["max_length"])
    test_dataset = ResumeNERDataset(str(ROOT_DIR / config["test_file"]), config["pretrained_model_name"], config["max_length"])
    train_loader = build_train_loader(train_dataset, config)
    dev_loader = make_data_loader(dev_dataset, config["eval_batch_size"], config["dataloader_num_workers"], shuffle=False)
    test_loader = make_data_loader(test_dataset, config["eval_batch_size"], config["dataloader_num_workers"], shuffle=False)

    model = build_model(config, device)
    all_history = []
    warm_start_report = None

    warm_start_path = ROOT_DIR / config["warm_start_file"]
    if warm_start_path.exists():
        warm_dataset = ResumeNERDataset(str(warm_start_path), config["pretrained_model_name"], config["max_length"])
        warm_train_loader, warm_eval_loader = build_warm_start_loaders(warm_dataset, {**config, "oversample_tail_labels": False, "epochs": config["warm_start_epochs"]})
        warm_stage_config = {**config, "oversample_tail_labels": False, "epochs": config["warm_start_epochs"]}
        model, warm_start_report, warm_history = run_stage(model, warm_train_loader, warm_eval_loader, warm_stage_config, "warm_start", device, output_dir)
        all_history.extend(warm_history)

    model, dev_report, train_history = run_stage(model, train_loader, dev_loader, config, "fine_tune", device, output_dir)
    all_history.extend(train_history)

    id2label = {index: label for index, label in enumerate(build_bio_labels())}
    test_report = evaluate_model(model, test_loader, device, id2label)
    test_report.update({"stage": "test", "device": str(device), "model_version": config["model_version"]})

    final_model_path = output_dir / "model.pt"
    torch.save(model.state_dict(), final_model_path)
    model.encoder.save_pretrained(output_dir / "encoder")
    train_dataset.tokenizer.save_pretrained(output_dir / "tokenizer")

    (output_dir / "evaluation_report.json").write_text(json.dumps(test_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "metrics.json").write_text(json.dumps(all_history, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "error_cases.json").write_text(json.dumps(test_report.get("error_cases", []), ensure_ascii=False, indent=2), encoding="utf-8")

    dataset_manifest_path = ROOT_DIR / "data" / "annotations" / "dataset_manifest.json"
    source_manifest_path = ROOT_DIR / "data" / "annotations" / "source_manifest.json"
    dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8")) if dataset_manifest_path.exists() else {}
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8")) if source_manifest_path.exists() else {}

    training_summary = {
        "model_version": config["model_version"],
        "pretrained_model_name": config["pretrained_model_name"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "device": str(device),
        "paper_ready": test_report["entity_micro_f1"] >= 0.70,
        "dataset_size": {
            "train": len(train_dataset),
            "dev": len(dev_dataset),
            "test": len(test_dataset),
        },
        "dataset_source_breakdown": source_manifest.get("source_summary", {}),
        "dataset_manifest": dataset_manifest,
        "core_label_targets": {label: 0.8 for label in ["NAME", "PHONE", "EMAIL", "DEGREE", "MAJOR", "SCHOOL", "SKILL", "EXPERIENCE_YEARS"]},
        "minimum_label_targets": {label: 0.6 for label in ENTITY_LABELS if label not in ["NAME", "PHONE", "EMAIL", "DEGREE", "MAJOR", "SCHOOL", "SKILL", "EXPERIENCE_YEARS"]},
        "warm_start_enabled": warm_start_report is not None,
        "warm_start_best": warm_start_report,
        "dev_best": dev_report,
        "test_report": test_report,
        "config": config,
    }
    (output_dir / "training_summary.json").write_text(json.dumps(training_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(training_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    train()
