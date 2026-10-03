"""
Training pipeline for Myanmar & Ethnic Name Semantic Embedding Model.
Fine-tunes a compact SentenceTransformer using Siamese/Triplet MultipleNegativesRankingLoss
on an NVIDIA GPU (RTX 4060) or CPU with mixed precision (FP16).
"""

import os
import json
import argparse
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from torch.utils.data import DataLoader


def load_triplets(file_path: str, max_samples: int = 40000):
    """Loads anchor-positive-negative triplets from jsonl."""
    examples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= max_samples:
                break
            data = json.loads(line)
            examples.append(
                InputExample(
                    texts=[data["anchor"], data["positive"], data["negative"]]
                )
            )
    return examples


def load_eval_pairs(file_path: str, max_samples: int = 5000):
    """Loads validation pairs with similarity scores (1.0 or 0.0)."""
    s1, s2, scores = [], [], []
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= max_samples:
                break
            data = json.loads(line)
            s1.append(data["name1"])
            s2.append(data["name2"])
            scores.append(float(data["label"]))
    return s1, s2, scores


def train(
    base_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    data_dir: str = "data",
    output_dir: str = "models/myanmar-name-encoder",
    batch_size: int = 64,
    epochs: int = 3,
    lr: float = 2e-5,
    max_train_samples: int = 40000,
):
    os.makedirs(output_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"==================================================")
    print(f"Training Myanmar Name Embedding Model")
    print(f"Base model : {base_model_name}")
    print(f"Device     : {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'})")
    print(f"Batch size : {batch_size}, Epochs: {epochs}, LR: {lr}")
    print(f"==================================================")

    # Load Base Model
    print("Loading base SentenceTransformer...")
    model = SentenceTransformer(base_model_name, device=device)

    # Load Triplet Dataset
    triplets_file = os.path.join(data_dir, "triplets.jsonl")
    print(f"Loading triplets from {triplets_file}...")
    train_examples = load_triplets(triplets_file, max_samples=max_train_samples)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    print(f"Loaded {len(train_examples):,} training triplets.")

    # MultipleNegativesRankingLoss optimizes embedding space such that
    # the positive is closest to the anchor while pushing all other negatives and in-batch items away
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # Load Evaluation Set
    val_file = os.path.join(data_dir, "val_pairs.jsonl")
    print(f"Loading validation pairs from {val_file}...")
    val_s1, val_s2, val_scores = load_eval_pairs(val_file)
    evaluator = evaluation.EmbeddingSimilarityEvaluator(
        val_s1, val_s2, val_scores, name="myanmar-val", batch_size=batch_size
    )

    warmup_steps = int(len(train_dataloader) * epochs * 0.1)

    print("Starting training loop...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=epochs,
        evaluation_steps=max(50, len(train_dataloader) // 4),
        warmup_steps=warmup_steps,
        output_path=output_dir,
        optimizer_params={"lr": lr},
        use_amp=torch.cuda.is_available(),  # Automatic Mixed Precision for RTX 4060
        show_progress_bar=True,
    )

    print("==================================================")
    print(f"Training completed successfully!")
    print(f"Model saved to: {output_dir}")
    print("==================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Myanmar Name Embedding Model")
    parser.add_argument("--base_model", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--data_dir", type=str, default="data")
    parser.add_argument("--output_dir", type=str, default="models/myanmar-name-encoder")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_samples", type=int, default=25000)

    args = parser.parse_args()
    train(
        base_model_name=args.base_model,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        max_train_samples=args.max_samples,
    )
