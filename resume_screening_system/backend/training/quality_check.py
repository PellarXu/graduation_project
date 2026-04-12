import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import ENTITY_LABELS


def parse_args():
    parser = argparse.ArgumentParser(description="Validate resume NER datasets.")
    parser.add_argument("--data-dir", default="data/annotations")
    parser.add_argument("--max-length", type=int, default=512)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_sample(sample: dict, split: str, index: int, max_length: int) -> list[str]:
    text = sample.get("text", "")
    entities = sample.get("entities", [])
    errors = []

    if not isinstance(text, str) or not text.strip():
        errors.append(f"{split}[{index}] empty text")
        return errors

    previous_end = -1
    seen = set()
    sorted_entities = sorted(entities, key=lambda entity: (entity["start"], entity["end"], entity["label"]))
    for entity in sorted_entities:
        start = entity.get("start")
        end = entity.get("end")
        label = entity.get("label")
        if label not in ENTITY_LABELS:
            errors.append(f"{split}[{index}] invalid label {label}")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"{split}[{index}] non-integer span {entity}")
            continue
        if start < 0 or end <= start or end > len(text):
            errors.append(f"{split}[{index}] out-of-range span {entity}")
        if start < previous_end:
            errors.append(f"{split}[{index}] overlapping span {entity}")
        key = (start, end, label)
        if key in seen:
            errors.append(f"{split}[{index}] duplicate span {entity}")
        seen.add(key)
        previous_end = max(previous_end, end)

    if len(text) >= max_length:
        for entity in sorted_entities:
            if entity["end"] >= max_length - 1:
                errors.append(f"{split}[{index}] entity truncated by max_length={max_length}: {entity}")
                break
    return errors


def main():
    args = parse_args()
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / args.data_dir
    split_paths = {split: data_dir / f"{split}.jsonl" for split in ("train", "dev", "test")}

    all_errors = []
    coverage = {split: Counter() for split in split_paths}

    for split, path in split_paths.items():
        if not path.exists():
            all_errors.append(f"missing split file: {path}")
            continue
        for index, sample in enumerate(load_jsonl(path)):
            all_errors.extend(validate_sample(sample, split, index, args.max_length))
            coverage[split].update(entity["label"] for entity in sample.get("entities", []))

    for label in ENTITY_LABELS:
        for split in ("train", "dev", "test"):
            if coverage[split][label] <= 0:
                all_errors.append(f"{split} missing label coverage: {label}")
        if coverage["test"][label] < 20:
            all_errors.append(f"test label coverage below threshold: {label}={coverage['test'][label]}")

    if all_errors:
        for error in all_errors:
            print(error)
        raise SystemExit(1)

    print(json.dumps({split: dict(sorted(counter.items())) for split, counter in coverage.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
