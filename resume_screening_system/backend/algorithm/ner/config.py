from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "model"
ARTIFACTS_DIR = MODEL_DIR / "artifacts"
TRAINING_DIR = BASE_DIR / "training"
DATA_DIR = BASE_DIR / "data" / "annotations"
DEFAULT_PRETRAINED_MODEL = "uer/albert-base-chinese-cluecorpussmall"
DEFAULT_MODEL_VERSION = "albert-bigru-crf-v2"
