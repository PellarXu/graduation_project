import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
THESIS_DIR = ROOT_DIR.parents[1] / "论文材料"


def markdown_table(headers, rows):
    head = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([head, divider, *body])


def main():
    checkpoint_dir = ROOT_DIR / "model" / "checkpoints" / "albert-bigru-crf-v2"
    comparison_path = ROOT_DIR / "model" / "comparison_report.json"
    dataset_manifest_path = ROOT_DIR / "data" / "annotations" / "dataset_manifest.json"
    summary_path = checkpoint_dir / "training_summary.json"
    evaluation_path = checkpoint_dir / "evaluation_report.json"

    if not all(path.exists() for path in [dataset_manifest_path, summary_path, evaluation_path]):
        raise FileNotFoundError("required training outputs are missing")

    dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    comparison = json.loads(comparison_path.read_text(encoding="utf-8")) if comparison_path.exists() else {}

    THESIS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = THESIS_DIR / "实验结果汇总.md"

    dataset_rows = [
        [split, info["samples"], info["avg_length"], info["max_length"]]
        for split, info in dataset_manifest["splits"].items()
    ]
    config_rows = [
        ["编码器", summary["pretrained_model_name"]],
        ["模型结构", summary["model_version"]],
        ["最大长度", summary["config"]["max_length"]],
        ["训练批次", summary["config"]["train_batch_size"]],
        ["验证批次", summary["config"]["eval_batch_size"]],
        ["梯度累积", summary["config"]["gradient_accumulation_steps"]],
        ["编码器学习率", summary["config"]["encoder_learning_rate"]],
        ["任务层学习率", summary["config"]["task_learning_rate"]],
        ["权重衰减", summary["config"]["weight_decay"]],
        ["warmup 比例", summary["config"]["warmup_ratio"]],
        ["训练轮数", summary["config"]["epochs"]],
    ]
    result_rows = [
        [label, metrics["precision"], metrics["recall"], metrics["f1"]]
        for label, metrics in evaluation["per_label_metrics"].items()
    ]
    compare_rows = []
    for name, report in comparison.items():
        compare_rows.append([name, report.get("entity_micro_f1", "-"), report.get("entity_macro_f1", "-")])

    content = [
        "# 模型实验结果汇总",
        "",
        "## 1. 数据集统计表",
        markdown_table(["Split", "样本数", "平均长度", "最大长度"], dataset_rows),
        "",
        "## 2. 训练配置表",
        markdown_table(["参数", "取值"], config_rows),
        "",
        "## 3. 总体结果",
        markdown_table(
            ["指标", "取值"],
            [
                ["整体 Micro-F1", evaluation["entity_micro_f1"]],
                ["整体 Macro-F1", evaluation["entity_macro_f1"]],
                ["是否达到论文达标线", "是" if summary.get("paper_ready") else "否"],
            ],
        ),
        "",
        "## 4. 14 类逐类结果表",
        markdown_table(["标签", "Precision", "Recall", "F1"], result_rows),
    ]

    if compare_rows:
        content.extend(
            [
                "",
                "## 5. 对比实验表",
                markdown_table(["实验组", "Micro-F1", "Macro-F1"], compare_rows),
            ]
        )

    output_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
