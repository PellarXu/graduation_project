import json
from pathlib import Path

import torch
from transformers import AutoTokenizer

from algorithm.ner.config import ARTIFACTS_DIR, DEFAULT_MODEL_VERSION
from algorithm.ner.labels import build_bio_labels
from algorithm.ner.model import AlbertBiGruCrf


class ModelNotReadyError(RuntimeError):
    def __init__(self, message: str, model_version: str = DEFAULT_MODEL_VERSION):
        super().__init__(message)
        self.model_version = model_version


class NERInferenceService:
    def __init__(self):
        self.artifacts_dir = ARTIFACTS_DIR
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        self._tokenizer = None
        self._id2label = None
        self._model_version = DEFAULT_MODEL_VERSION

    def _ensure_ready(self):
        config_path = self.artifacts_dir / "inference_config.json"
        weights_path = self.artifacts_dir / "model.pt"
        labels_path = self.artifacts_dir / "label_map.json"
        tokenizer_path = self.artifacts_dir / "tokenizer"

        if not (config_path.exists() and weights_path.exists() and labels_path.exists() and tokenizer_path.exists()):
            raise ModelNotReadyError("模型未就绪：尚未检测到训练后的权重和推理资源。")

        if self._model is not None:
            return

        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        with open(labels_path, "r", encoding="utf-8") as file:
            label_map = json.load(file)

        self._id2label = {int(key): value for key, value in label_map["id2label"].items()}
        self._model_version = config.get("model_version", DEFAULT_MODEL_VERSION)
        self._tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))
        self._model = AlbertBiGruCrf(
            pretrained_model_name=config["pretrained_model_name"],
            num_labels=len(self._id2label),
            hidden_size=config.get("hidden_size", 256),
            dropout=config.get("dropout", 0.1),
        )
        self._model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self._model.to(self.device)
        self._model.eval()

    def predict(self, text: str):
        self._ensure_ready()
        tokens = self._tokenizer(
            list(text),
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        tokens = {key: value.to(self.device) for key, value in tokens.items() if key in {"input_ids", "attention_mask"}}

        with torch.no_grad():
            outputs = self._model(**tokens)

        decoded = outputs["decoded"][0]
        entities = self._decode_entities(text, decoded)
        return entities, self._model_version

    def _decode_entities(self, text: str, decoded_labels):
        if not decoded_labels:
            return []

        entities = []
        current_label = None
        current_text = []
        start = 0
        bio_labels = build_bio_labels()

        for index, label_id in enumerate(decoded_labels[1:-1], start=0):
            label = self._id2label.get(label_id, bio_labels[label_id] if label_id < len(bio_labels) else "O")
            char = text[index] if index < len(text) else ""

            if label == "O":
                if current_label and current_text:
                    entities.append(
                        {
                            "text": "".join(current_text),
                            "label": current_label,
                            "start": start,
                            "end": index,
                            "score": None,
                        }
                    )
                current_label = None
                current_text = []
                continue

            prefix, entity_label = label.split("-", 1)
            if prefix == "B" or entity_label != current_label:
                if current_label and current_text:
                    entities.append(
                        {
                            "text": "".join(current_text),
                            "label": current_label,
                            "start": start,
                            "end": index,
                            "score": None,
                        }
                    )
                current_label = entity_label
                current_text = [char]
                start = index
            else:
                current_text.append(char)

        if current_label and current_text:
            entities.append(
                {
                    "text": "".join(current_text),
                    "label": current_label,
                    "start": start,
                    "end": start + len(current_text),
                    "score": None,
                }
            )
        return entities
