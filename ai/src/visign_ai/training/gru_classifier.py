"""GRU baseline with explicit sequence lengths and stable output order."""

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence


class GRUClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes, num_layers=1):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.classifier = nn.Linear(hidden_size, num_classes)

    def forward(self, sequences, lengths):
        if sequences.ndim != 3 or lengths.ndim != 1 or len(lengths) != len(sequences):
            raise ValueError("Expected [batch,time,features] and [batch] lengths")
        if torch.any(lengths < 1) or torch.any(lengths > sequences.shape[1]):
            raise ValueError("Sequence lengths are outside the padded time dimension")
        packed = pack_padded_sequence(
            sequences, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, hidden = self.gru(packed)
        return self.classifier(hidden[-1])
