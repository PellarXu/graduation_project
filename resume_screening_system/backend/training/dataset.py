import json
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

from algorithm.ner.labels import build_bio_labels


class ResumeNERDataset(Dataset):
    def __init__(self, file_path: str, tokenizer_name: str, max_length: int = 512):
        self.file_path = Path(file_path)
        self.samples = [json.loads(line) for line in self.file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.labels = build_bio_labels()
        self.label2id = {label: idx for idx, label in enumerate(self.labels)}
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.max_length = max_length

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        text = sample["text"]
        entities = sample.get("entities", [])
        char_labels = ["O"] * len(text)

        for entity in entities:
            start = entity["start"]
            end = entity["end"]
            label = entity["label"]
            if start >= len(text):
                continue
            char_labels[start] = f"B-{label}"
            for pointer in range(start + 1, min(end, len(text))):
                char_labels[pointer] = f"I-{label}"

        encoded = self.tokenizer(
            list(text),
            is_split_into_words=True,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].squeeze(0)
        attention_mask = encoded["attention_mask"].squeeze(0)
        labels = torch.full_like(input_ids, fill_value=self.label2id["O"])

        for idx, label in enumerate(char_labels, start=1):
            if idx >= self.max_length - 1:
                break
            labels[idx] = self.label2id[label]

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }
