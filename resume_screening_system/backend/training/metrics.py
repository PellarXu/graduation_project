from collections import Counter

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


def evaluate_predictions(predictions, gold_labels, attention_masks, id2label):
    true_positive = 0
    false_positive = 0
    false_negative = 0
    entity_counter = Counter()

    for pred_tensor, gold_tensor, mask_tensor in zip(predictions, gold_labels, attention_masks):
        pred_entities = set(_sequence_to_entities(_collect_valid_positions(pred_tensor, mask_tensor), id2label))
        gold_entities = set(_sequence_to_entities(_collect_valid_positions(gold_tensor, mask_tensor), id2label))

        true_positive += len(pred_entities & gold_entities)
        false_positive += len(pred_entities - gold_entities)
        false_negative += len(gold_entities - pred_entities)

        for _, _, label in gold_entities:
            entity_counter[label] += 1

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "samples": len(predictions),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "entity_distribution": dict(sorted(entity_counter.items())),
    }


def evaluate_model(model, data_loader, device, id2label):
    model.eval()
    predictions = []
    gold_labels = []
    attention_masks = []

    with torch.no_grad():
        for batch in data_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            decoded = outputs["decoded"]

            for pred, labels, mask in zip(decoded, batch["labels"].cpu(), batch["attention_mask"].cpu()):
                predictions.append(torch.tensor(pred))
                gold_labels.append(labels)
                attention_masks.append(mask)

    return evaluate_predictions(predictions, gold_labels, attention_masks, id2label)
