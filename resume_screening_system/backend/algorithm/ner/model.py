import torch
from TorchCRF import CRF
from torch import nn
from transformers import AutoModel


class BaseAlbertCrf(nn.Module):
    def __init__(self, pretrained_model_name: str, num_labels: int, dropout: float = 0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(pretrained_model_name)
        self.dropout = nn.Dropout(dropout)
        self.crf = CRF(num_labels, use_gpu=torch.cuda.is_available())

    def compute_loss(self, emissions, attention_mask, labels):
        return -self.crf(emissions, labels, attention_mask.bool()).mean()

    def decode(self, emissions, attention_mask):
        return self.crf.viterbi_decode(emissions, attention_mask.bool())


class AlbertCrf(BaseAlbertCrf):
    def __init__(self, pretrained_model_name: str, num_labels: int, hidden_size: int = 256, dropout: float = 0.1):
        super().__init__(pretrained_model_name, num_labels, dropout=dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask, labels=None):
        encoded = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        emissions = self.classifier(self.dropout(encoded))
        if labels is not None:
            return {"loss": self.compute_loss(emissions, attention_mask, labels), "emissions": emissions}
        return {"emissions": emissions, "decoded": self.decode(emissions, attention_mask)}


class AlbertBiGruCrf(BaseAlbertCrf):
    def __init__(self, pretrained_model_name: str, num_labels: int, hidden_size: int = 256, dropout: float = 0.1):
        super().__init__(pretrained_model_name, num_labels, dropout=dropout)
        encoder_hidden = self.encoder.config.hidden_size
        self.bigru = nn.GRU(
            input_size=encoder_hidden,
            hidden_size=hidden_size // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(self, input_ids, attention_mask, labels=None):
        encoded = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        encoded = self.dropout(encoded)
        sequence_output, _ = self.bigru(encoded)
        emissions = self.classifier(sequence_output)
        if labels is not None:
            return {"loss": self.compute_loss(emissions, attention_mask, labels), "emissions": emissions}
        return {"emissions": emissions, "decoded": self.decode(emissions, attention_mask)}


def build_ner_model(model_type: str, pretrained_model_name: str, num_labels: int, hidden_size: int = 256, dropout: float = 0.1):
    if model_type == "albert_crf":
        return AlbertCrf(pretrained_model_name, num_labels, hidden_size=hidden_size, dropout=dropout)
    return AlbertBiGruCrf(pretrained_model_name, num_labels, hidden_size=hidden_size, dropout=dropout)
