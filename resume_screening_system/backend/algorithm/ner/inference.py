import json
from datetime import datetime
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
        self._max_length = 256

    def _ensure_ready(self):
        config_path = self.artifacts_dir / "inference_config.json"
        weights_path = self.artifacts_dir / "model.pt"
        labels_path = self.artifacts_dir / "label_map.json"
        tokenizer_path = self.artifacts_dir / "tokenizer"

        if not (config_path.exists() and weights_path.exists() and labels_path.exists() and tokenizer_path.exists()):
            raise ModelNotReadyError("分析资源暂不可用。")

        if self._model is not None:
            return

        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        with open(labels_path, "r", encoding="utf-8") as file:
            label_map = json.load(file)

        self._id2label = {int(key): value for key, value in label_map["id2label"].items()}
        self._model_version = config.get("model_version", DEFAULT_MODEL_VERSION)
        self._max_length = config.get("max_length", 256)
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
            max_length=self._max_length,
        )
        tokens = {key: value.to(self.device) for key, value in tokens.items() if key in {"input_ids", "attention_mask"}}

        with torch.no_grad():
            outputs = self._model(**tokens)

        decoded = outputs["decoded"][0]
        entities = self._decode_entities(text, decoded)
        return entities, self._model_version

    def get_model_status(self):
        config_path = self.artifacts_dir / "inference_config.json"
        weights_path = self.artifacts_dir / "model.pt"
        labels_path = self.artifacts_dir / "label_map.json"
        tokenizer_path = self.artifacts_dir / "tokenizer"
        evaluation_path = self.artifacts_dir / "evaluation_report.json"
        summary_path = self.artifacts_dir / "training_summary.json"
        dataset_manifest_path = self.artifacts_dir / "dataset_manifest.json"
        source_manifest_path = self.artifacts_dir / "source_manifest.json"

        required_paths = [config_path, weights_path, labels_path, tokenizer_path]
        missing = [path.name for path in required_paths if not path.exists()]
        if missing:
            return {
                "status": "artifacts_missing",
                "ready": False,
                "message": f"尚未检测到训练后的权重和推理资源：{', '.join(missing)}",
                "model_version": self._model_version,
                "overall_f1": None,
                "macro_f1": None,
                "per_label_metrics": {},
                "dataset_size": {},
                "dataset_source_breakdown": {},
                "paper_ready": False,
                "trained_at": None,
            }

        summary = self._read_json(summary_path)
        evaluation = self._read_json(evaluation_path)
        dataset_manifest = self._read_json(dataset_manifest_path)
        source_manifest = self._read_json(source_manifest_path)
        trained_at = summary.get("trained_at")
        if trained_at is None and weights_path.exists():
            trained_at = datetime.fromtimestamp(weights_path.stat().st_mtime).isoformat()

        return {
            "status": "ready",
            "ready": True,
            "message": "模型已就绪，可用于简历实体识别。",
            "model_version": summary.get("model_version", self._model_version),
            "overall_f1": evaluation.get("entity_micro_f1", summary.get("test_report", {}).get("entity_micro_f1")),
            "macro_f1": evaluation.get("entity_macro_f1", summary.get("test_report", {}).get("entity_macro_f1")),
            "per_label_metrics": evaluation.get("per_label_metrics", summary.get("test_report", {}).get("per_label_metrics", {})),
            "dataset_size": summary.get("dataset_size", {}),
            "dataset_source_breakdown": summary.get("dataset_source_breakdown", source_manifest.get("source_summary", {})),
            "paper_ready": summary.get("paper_ready", False),
            "trained_at": trained_at,
            "dataset_manifest": dataset_manifest,
        }

    @staticmethod
    def _read_json(path: Path):
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

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
