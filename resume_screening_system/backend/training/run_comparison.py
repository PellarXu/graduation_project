import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algorithm.ner.labels import ENTITY_LABELS
from training.corpus_builder import BLUEPRINTS


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def entity_prf(pred_entities: set[tuple], gold_entities: set[tuple]) -> tuple[int, int, int]:
    tp = len(pred_entities & gold_entities)
    fp = len(pred_entities - gold_entities)
    fn = len(gold_entities - pred_entities)
    return tp, fp, fn


def summarize_metrics(label_totals):
    per_label = {}
    total_tp = total_fp = total_fn = 0
    for label, values in label_totals.items():
        tp, fp, fn = values["tp"], values["fp"], values["fn"]
        total_tp += tp
        total_fp += fp
        total_fn += fn
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_label[label] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if (micro_precision + micro_recall) else 0.0
    macro_f1 = sum(item["f1"] for item in per_label.values()) / max(len(per_label), 1)
    return {
        "entity_micro_f1": round(micro_f1, 4),
        "entity_macro_f1": round(macro_f1, 4),
        "per_label_metrics": per_label,
    }


def find_spans(text: str, value: str, label: str) -> list[tuple[int, int, str]]:
    spans = []
    start = text.find(value)
    while start != -1:
        spans.append((start, start + len(value), label))
        start = text.find(value, start + len(value))
    return spans


def rule_extract_entities(text: str) -> set[tuple[int, int, str]]:
    entities = set()
    known_titles = sorted({blueprint.title for blueprint in BLUEPRINTS}, key=len, reverse=True)
    known_schools = sorted({school for blueprint in BLUEPRINTS for school in blueprint.schools}, key=len, reverse=True)
    known_majors = sorted({major for blueprint in BLUEPRINTS for major in blueprint.majors}, key=len, reverse=True)
    known_companies = sorted({company for blueprint in BLUEPRINTS for company in blueprint.companies}, key=len, reverse=True)
    known_projects = sorted({project for blueprint in BLUEPRINTS for project in blueprint.projects}, key=len, reverse=True)
    known_skills = sorted({skill for blueprint in BLUEPRINTS for skill_set in blueprint.skill_sets for skill in skill_set}, key=len, reverse=True)

    for pattern, label in [
        (r"1[3-9]\d{9}", "PHONE"),
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "EMAIL"),
        (r"\d年(?:开发|前端|测试|算法|分析|产品|项目|运营|电商|设计|招聘|财务|工作)?经验", "EXPERIENCE_YEARS"),
        (r"\d岁", "AGE"),
    ]:
        for match in re.finditer(pattern, text):
            start, end = match.span()
            entities.add((start, end, label))

    for match in re.finditer(r"(男|女)", text):
        entities.add((match.start(), match.end(), "GENDER"))

    for keyword, label in [("本科", "DEGREE"), ("硕士", "DEGREE")]:
        for start, end, mapped_label in find_spans(text, keyword, label):
            entities.add((start, end, mapped_label))

    for label, values in [
        ("TITLE", known_titles),
        ("SCHOOL", known_schools),
        ("MAJOR", known_majors),
        ("COMPANY", known_companies),
        ("PROJECT", known_projects),
        ("SKILL", known_skills),
    ]:
        for value in values:
            for span in find_spans(text, value, label):
                entities.add(span)

    for home in ["湖北武汉", "湖南长沙", "河南郑州", "江西南昌", "安徽合肥", "广东深圳", "江苏苏州", "浙江杭州", "四川成都", "福建厦门", "山东济南", "河北石家庄"]:
        for span in find_spans(text, home, "HOMETOWN"):
            entities.add(span)

    name_patterns = [
        r"候选人([\u4e00-\u9fa5]{2,3})",
        r"基本信息：([\u4e00-\u9fa5]{2,3})",
        r"姓名：([\u4e00-\u9fa5]{2,3})",
        r"^([\u4e00-\u9fa5]{2,3})[，。]",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            entities.add((match.start(1), match.end(1), "NAME"))
            break
    return entities


def evaluate_rule_baseline(test_path: Path):
    samples = load_jsonl(test_path)
    label_totals = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for sample in samples:
        gold_entities = {(entity["start"], entity["end"], entity["label"]) for entity in sample.get("entities", [])}
        pred_entities = rule_extract_entities(sample["text"])
        tp, fp, fn = entity_prf(pred_entities, gold_entities)

        for label in ENTITY_LABELS:
            pred_label_entities = {item for item in pred_entities if item[2] == label}
            gold_label_entities = {item for item in gold_entities if item[2] == label}
            label_tp, label_fp, label_fn = entity_prf(pred_label_entities, gold_label_entities)
            label_totals[label]["tp"] += label_tp
            label_totals[label]["fp"] += label_fp
            label_totals[label]["fn"] += label_fn

    return summarize_metrics(label_totals)


def run_training_variant(base_config: dict, model_type: str, model_version: str, output_dir: str):
    config = {**base_config, "model_type": model_type, "model_version": model_version, "output_dir": output_dir}
    report_path = ROOT_DIR / output_dir / "evaluation_report.json"
    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))
    temp_path = ROOT_DIR / "training" / "configs" / f"{model_version}.json"
    temp_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, "training/train.py", "--config", str(temp_path.relative_to(ROOT_DIR))], cwd=ROOT_DIR, check=True)
    return json.loads(report_path.read_text(encoding="utf-8"))


def main():
    config_path = ROOT_DIR / "training" / "configs" / "train_config.json"
    base_config = json.loads(config_path.read_text(encoding="utf-8"))
    reports = {
        "rule_baseline": evaluate_rule_baseline(ROOT_DIR / base_config["test_file"]),
        "albert_crf": run_training_variant(base_config, "albert_crf", "albert-crf-baseline", "model/checkpoints/albert-crf-baseline"),
        "albert_bigru_crf": run_training_variant(base_config, "albert_bigru_crf", "albert-bigru-crf-v2", base_config["output_dir"]),
    }
    output_path = ROOT_DIR / "model" / "comparison_report.json"
    output_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
