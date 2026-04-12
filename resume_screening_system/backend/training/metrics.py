from collections import Counter, defaultdict

import torch


def _sequence_to_entities(label_ids, id2label):
    entities = []
    current_label = None
    start = None

    for index, label_id in enumerate(label_ids):
        label = id2label.get(int(label_id), "O")
        if label == "O":
            if current_label is not None and start is not None:
                entities.append((start, index, current_label))
            current_label = None
            start = None
            continue

        prefix, entity_label = label.split("-", 1)
        if prefix == "B" or entity_label != current_label:
            if current_label is not None and start is not None:
                entities.append((start, index, current_label))
            current_label = entity_label
            start = index

    if current_label is not None and start is not None:
        entities.append((start, len(label_ids), current_label))
    return entities


def _collect_valid_positions(label_tensor, mask_tensor):
    valid_length = int(mask_tensor.sum().item())
    if valid_length <= 2:
        return []
    return label_tensor[1 : valid_length - 1].tolist()


def _entity_metrics(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def evaluate_predictions(predictions, gold_labels, attention_masks, id2label, texts=None, max_error_cases=20):
    overall_tp = 0
    overall_fp = 0
    overall_fn = 0
    gold_counter = Counter()
    label_totals = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    confusion_pairs = Counter()
    error_cases = []

    for row_index, (pred_tensor, gold_tensor, mask_tensor) in enumerate(zip(predictions, gold_labels, attention_masks)):
        pred_entities = set(_sequence_to_entities(_collect_valid_positions(pred_tensor, mask_tensor), id2label))
        gold_entities = set(_sequence_to_entities(_collect_valid_positions(gold_tensor, mask_tensor), id2label))

        true_positive = pred_entities & gold_entities
        false_positive = pred_entities - gold_entities
        false_negative = gold_entities - pred_entities

        overall_tp += len(true_positive)
        overall_fp += len(false_positive)
        overall_fn += len(false_negative)

        for _, _, label in gold_entities:
            gold_counter[label] += 1
        for _, _, label in true_positive:
            label_totals[label]["tp"] += 1
        for _, _, label in false_positive:
            label_totals[label]["fp"] += 1
        for _, _, label in false_negative:
            label_totals[label]["fn"] += 1

        for pred_start, pred_end, pred_label in false_positive:
            for gold_start, gold_end, gold_label in false_negative:
                overlap = min(pred_end, gold_end) - max(pred_start, gold_start)
                if overlap > 0:
                    confusion_pairs[f"{gold_label}->{pred_label}"] += 1

        if texts is not None and (false_positive or false_negative) and len(error_cases) < max_error_cases:
            error_cases.append(
                {
                    "text": texts[row_index],
                    "gold": [{"start": start, "end": end, "label": label} for start, end, label in sorted(gold_entities)],
                    "pred": [{"start": start, "end": end, "label": label} for start, end, label in sorted(pred_entities)],
                }
            )

    micro_metrics = _entity_metrics(overall_tp, overall_fp, overall_fn)
    per_label_metrics = {label: _entity_metrics(values["tp"], values["fp"], values["fn"]) for label, values in sorted(label_totals.items())}
    macro_f1 = (
        round(sum(item["f1"] for item in per_label_metrics.values()) / max(len(per_label_metrics), 1), 4)
        if per_label_metrics
        else 0.0
    )

    return {
        "samples": len(predictions),
        "precision": micro_metrics["precision"],
        "recall": micro_metrics["recall"],
        "f1_score": micro_metrics["f1"],
        "entity_micro_f1": micro_metrics["f1"],
        "entity_macro_f1": macro_f1,
        "per_label_metrics": per_label_metrics,
        "entity_distribution": dict(sorted(gold_counter.items())),
        "confusion_pairs": dict(confusion_pairs.most_common(15)),
        "error_cases": error_cases,
    }


def evaluate_model(model, data_loader, device, id2label, max_error_cases=20):
    model.eval()
    predictions = []
    gold_labels = []
    attention_masks = []
    texts = []

    with torch.no_grad():
        for batch in data_loader:
            tensor_batch = {key: value.to(device) for key, value in batch.items() if hasattr(value, "to")}
            outputs = model(input_ids=tensor_batch["input_ids"], attention_mask=tensor_batch["attention_mask"])
            decoded = outputs["decoded"]

            for pred, labels, mask, text in zip(decoded, tensor_batch["labels"].cpu(), tensor_batch["attention_mask"].cpu(), batch["text"]):
                predictions.append(torch.tensor(pred))
                gold_labels.append(labels)
                attention_masks.append(mask)
                texts.append(text)

    return evaluate_predictions(predictions, gold_labels, attention_masks, id2label, texts=texts, max_error_cases=max_error_cases)
