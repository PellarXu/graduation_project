import json
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd
from huggingface_hub import snapshot_download


CLUENER_URLS = {
    "train": "https://raw.githubusercontent.com/CLUEbenchmark/CLUENER2020/master/train.json",
    "dev": "https://raw.githubusercontent.com/CLUEbenchmark/CLUENER2020/master/dev.json",
}

CLUENER_LABEL_MAP = {
    "name": "NAME",
    "company": "COMPANY",
    "organization": "COMPANY",
    "position": "TITLE",
}


def ensure_cluener_download(raw_dir: Path) -> dict[str, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_map = {}
    for split, url in CLUENER_URLS.items():
        target = raw_dir / f"cluener_{split}.json"
        try:
            if not target.exists():
                urlretrieve(url, target)
            file_map[split] = target
        except Exception:
            continue
    return file_map


def map_cluener_records(file_path: Path, max_samples: int | None = None) -> list[dict]:
    mapped = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            text = item["text"]
            entities = []
            for raw_label, spans in item.get("label", {}).items():
                mapped_label = CLUENER_LABEL_MAP.get(raw_label)
                if not mapped_label:
                    continue
                for value_spans in spans.values():
                    for start, end in value_spans:
                        entities.append({"start": start, "end": end + 1, "label": mapped_label})
            if not entities:
                continue
            entities.sort(key=lambda entity: (entity["start"], entity["end"], entity["label"]))
            deduped = []
            seen = set()
            overlap = False
            for entity in entities:
                key = (entity["start"], entity["end"], entity["label"])
                if key in seen:
                    continue
                if deduped and entity["start"] < deduped[-1]["end"]:
                    overlap = True
                    break
                deduped.append(entity)
                seen.add(key)
            if overlap:
                continue
            mapped.append({"text": text, "entities": deduped})
            if max_samples and len(mapped) >= max_samples:
                break
    return mapped


def try_download_resume_ner(raw_dir: Path) -> Path | None:
    dataset_dir = raw_dir / "resume_ner"
    if dataset_dir.exists():
        return dataset_dir
    try:
        snapshot_download(
            repo_id="PassbyGrocer/resume-ner",
            repo_type="dataset",
            local_dir=dataset_dir,
            local_dir_use_symlinks=False,
        )
        return dataset_dir
    except Exception:
        return None


def map_resume_ner_records(dataset_dir: Path | None, max_samples: int | None = None) -> list[dict]:
    if not dataset_dir or not dataset_dir.exists():
        return []

    label_map = {
        "NAME": "NAME",
        "ORG": "COMPANY",
        "TITLE": "TITLE",
    }
    tag_names = {
        0: "O",
        1: "B-CONT",
        2: "I-CONT",
        3: "B-EDU",
        4: "I-EDU",
        5: "B-LOC",
        6: "I-LOC",
        7: "B-NAME",
        8: "I-NAME",
        9: "B-ORG",
        10: "I-ORG",
        11: "B-PRO",
        12: "I-PRO",
        13: "B-RACE",
        14: "I-RACE",
        15: "B-TITLE",
        16: "I-TITLE",
    }
    mapped = []

    for file_path in sorted(dataset_dir.rglob("*.parquet")):
        frame = pd.read_parquet(file_path)
        for row in frame.itertuples(index=False):
            tokens = list(row.tokens)
            tags = list(row.ner_tags)
            text = "".join(tokens)
            entities = []
            current_label = None
            start = None
            cursor = 0

            for token, tag_id in zip(tokens, tags):
                tag = tag_names.get(int(tag_id), "O")
                token_length = len(token)
                if tag == "O":
                    if current_label is not None and start is not None:
                        entities.append({"start": start, "end": cursor, "label": current_label})
                    current_label = None
                    start = None
                    cursor += token_length
                    continue

                prefix, raw_label = tag.split("-", 1)
                mapped_label = label_map.get(raw_label)
                if mapped_label is None:
                    if current_label is not None and start is not None:
                        entities.append({"start": start, "end": cursor, "label": current_label})
                    current_label = None
                    start = None
                    cursor += token_length
                    continue

                if prefix == "B" or mapped_label != current_label:
                    if current_label is not None and start is not None:
                        entities.append({"start": start, "end": cursor, "label": current_label})
                    current_label = mapped_label
                    start = cursor
                cursor += token_length

            if current_label is not None and start is not None:
                entities.append({"start": start, "end": cursor, "label": current_label})

            if entities:
                mapped.append({"text": text, "entities": entities})
                if max_samples and len(mapped) >= max_samples:
                    return mapped

    return mapped
