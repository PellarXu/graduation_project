import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from training.corpus_builder import build_resume_corpus, write_jsonl
from training.public_data import (
    ensure_cluener_download,
    map_cluener_records,
    map_resume_ner_records,
    try_download_resume_ner,
)


DATA_DIR = ROOT_DIR / "data" / "annotations"
PUBLIC_DIR = ROOT_DIR / "data" / "public"


def build_warm_start_samples() -> tuple[list[dict], dict]:
    raw_dir = PUBLIC_DIR / "raw"

    warm_start_sources = {}
    cluener_samples = []
    cluener_files = ensure_cluener_download(raw_dir / "cluener")
    for split in ("train", "dev"):
        if split not in cluener_files:
            continue
        limit = 1200 if split == "train" else 300
        cluener_samples.extend(map_cluener_records(cluener_files[split], max_samples=limit))
    if cluener_samples:
        warm_start_sources["cluener2020"] = len(cluener_samples)

    resume_ner_dir = try_download_resume_ner(raw_dir)
    resume_ner_samples = map_resume_ner_records(resume_ner_dir, max_samples=400)
    if resume_ner_samples:
        warm_start_sources["resume_ner"] = len(resume_ner_samples)

    return cluener_samples + resume_ner_samples, warm_start_sources


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated = build_resume_corpus(seed=42, total_profiles=150, templates_per_profile=8)
    corpus = generated["corpus"]

    write_jsonl(DATA_DIR / "train.jsonl", corpus["train"])
    write_jsonl(DATA_DIR / "dev.jsonl", corpus["dev"])
    write_jsonl(DATA_DIR / "test.jsonl", corpus["test"])

    warm_start_samples, warm_start_sources = build_warm_start_samples()
    if warm_start_samples:
        write_jsonl(DATA_DIR / "warm_start.jsonl", warm_start_samples)

    source_manifest = {
        "sources": generated["source_manifest"],
        "source_summary": {
            **{
                split: generated["dataset_manifest"]["splits"][split]["source_breakdown"]
                for split in ("train", "dev", "test")
            },
            "public_mapped": warm_start_sources,
        },
    }
    (DATA_DIR / "source_manifest.json").write_text(json.dumps(source_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    dataset_manifest = generated["dataset_manifest"]
    dataset_manifest["warm_start"] = {"samples": len(warm_start_samples), "source_breakdown": warm_start_sources}
    (DATA_DIR / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(dataset_manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
