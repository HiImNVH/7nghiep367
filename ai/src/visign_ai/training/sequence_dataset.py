"""Strict loader for features emitted by extract_manifest."""

import numpy as np
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset

from visign_ai.dataset.manifest import confined_path
from visign_ai.landmarks.sequence_transform import schema_digest


class SequenceDataset(Dataset):
    def __init__(self, rows, root, class_labels, schema):
        self.samples = []
        self.rows = rows
        for row in rows:
            path = confined_path(root, row["landmarkPath"])
            with np.load(path, allow_pickle=False) as archive:
                for key in ("featureSchemaVersion", "extractorVersion"):
                    if str(archive[key].item()) != schema[key]:
                        raise ValueError(f"{key} mismatch for sample {row['sampleId']}")
                if str(archive["schemaSha256"].item()) != schema_digest(schema):
                    raise ValueError("Schema content hash mismatch")
                features = archive["features"].astype(np.float32)
            expected_width = len(schema["landmarkOrder"]) * 3
            if features.shape != (schema["targetFrameCount"], expected_width):
                raise ValueError("Feature shape mismatch")
            if not np.isfinite(features).all():
                raise ValueError("Non-finite features")
            if not np.isin(features[:, expected_width // 3 * 2 :], [0, 1]).all():
                raise ValueError("Invalid point mask")
            self.samples.append(
                (torch.from_numpy(features), class_labels.index(row["classLabel"]))
            )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        return self.samples[index]


def collate_sequences(samples):
    sequences, labels = zip(*samples)
    return (
        pad_sequence(sequences, batch_first=True),
        torch.tensor([len(item) for item in sequences], dtype=torch.long),
        torch.tensor(labels, dtype=torch.long),
    )
