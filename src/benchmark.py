"""
Benchmark evaluation suite comparing:
1. Baseline Exact Match (Standard SQL LIKE)
2. English Soundex
3. Burglish Phonetic Rule Matcher
4. Full Myanmar Name Matcher
Measures Accuracy, Precision, Recall, F1, and Latency.
"""

import json
import time
import os
from typing import List, Dict, Any
from phonetic_normalizer import BurglishPhoneticNormalizer


def english_soundex(name: str) -> str:
    """Standard English Soundex implementation."""
    name = name.upper().strip()
    if not name:
        return ""
    mapping = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6",
    }
    first_letter = name[0]
    tail = name[1:]
    encoded = []
    prev_code = mapping.get(first_letter, "")
    for char in tail:
        code = mapping.get(char, "")
        if code and code != prev_code:
            encoded.append(code)
        prev_code = code
    soundex = (first_letter + "".join(encoded) + "000")[:4]
    return soundex


def run_benchmark(val_file_path: str = "data/val_pairs.jsonl", max_eval: int = 2000):
    if not os.path.exists(val_file_path):
        print(f"Error: {val_file_path} not found. Run dataset_generator.py first.")
        return

    pairs = []
    with open(val_file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= max_eval:
                break
            pairs.append(json.loads(line))

    print(f"Running benchmark on {len(pairs)} evaluation pairs...")

    methods = {
        "Standard SQL LIKE / Exact": lambda n1, n2: n1.lower().strip() == n2.lower().strip(),
        "English Soundex": lambda n1, n2: english_soundex(n1) == english_soundex(n2),
        "Burglish Phonetic Rule Matcher": lambda n1, n2: BurglishPhoneticNormalizer.compare_names(n1, n2)["is_duplicate"],
    }

    # Add Hybrid Matcher if trained model is available
    try:
        from matcher import MyanmarNameMatcher
        hybrid_matcher = MyanmarNameMatcher(use_neural=True)
        methods["Hybrid SLM (Neural + Rules)"] = lambda n1, n2: hybrid_matcher.match(n1, n2)["is_duplicate"]
    except Exception as e:
        print(f"Notice: Hybrid matcher not loaded: {e}")

    results = {}

    for method_name, method_fn in methods.items():
        tp = fp = tn = fn = 0
        start_time = time.perf_counter()

        for p in pairs:
            actual = bool(p["label"] == 1.0)
            predicted = bool(method_fn(p["name1"], p["name2"]))

            if actual and predicted:
                tp += 1
            elif not actual and predicted:
                fp += 1
            elif not actual and not predicted:
                tn += 1
            elif actual and not predicted:
                fn += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        avg_us = (elapsed_ms / len(pairs)) * 1000

        accuracy = (tp + tn) / len(pairs) if pairs else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0

        results[method_name] = {
            "Accuracy": accuracy * 100,
            "Precision": precision * 100,
            "Recall": recall * 100,
            "F1-Score": f1 * 100,
            "Latency (μs/op)": avg_us,
        }

    print("\n" + "=" * 85)
    print(f"{'Method':<35} | {'Accuracy':<9} | {'Precision':<9} | {'Recall':<9} | {'F1':<7} | {'Speed':<10}")
    print("-" * 85)
    for name, m in results.items():
        print(f"{name:<35} | {m['Accuracy']:8.1f}% | {m['Precision']:8.1f}% | {m['Recall']:8.1f}% | {m['F1-Score']:6.1f}% | {m['Latency (μs/op)']:6.1f} μs")
    print("=" * 85)


if __name__ == "__main__":
    run_benchmark()
