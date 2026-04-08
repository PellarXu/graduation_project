import torch
from TorchCRF import CRF
from torch import nn
from transformers import AutoModel


class AlbertBiGruCrf(nn.Module):
    def __init__(self, pretrained_model_name: str, num_labels: int, hidden_size: int = 256, dropout: float = 0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(pretrained_model_name)
        encoder_hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.bigru = nn.GRU(
            input_size=encoder_hidden,
            hidden_size=hidden_size // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.classifier = nn.Linear(hidden_size, num_labels)
        self.crf = CRF(num_labels, use_gpu=torch.cuda.is_available())

    def forward(self, input_ids, attention_mask, labels=None):
        encoded = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        encoded = self.dropout(encoded)
        sequence_output, _ = self.bigru(encoded)
        emissions = self.classifier(sequence_output)
        mask = attention_mask.bool()

        if labels is not None:
            loss = -self.crf(emissions, labels, mask).mean()
            return {"loss": loss, "emissions": emissions}

        decoded = self.crf.viterbi_decode(emissions, mask)
        return {"emissions": emissions, "decoded": decoded}
