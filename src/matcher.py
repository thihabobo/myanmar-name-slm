"""
Unified Myanmar & Ethnic Name Matcher.
Combines rule-based phonetic normalizer with dense neural embeddings (ONNX or PyTorch)
for ultra-fast, high-precision duplicate detection and semantic search.
"""

import os
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from phonetic_normalizer import BurglishPhoneticNormalizer

try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class MyanmarNameMatcher:
    """
    High-level API for semantic matching, phonetic deduplication,
    and similarity scoring of Myanmar & Ethnic names.
    """

    def __init__(
        self,
        onnx_model_path: Optional[str] = None,
        pytorch_model_path: Optional[str] = None,
        use_neural: bool = True,
    ):
        self.use_neural = use_neural
        self.normalizer = BurglishPhoneticNormalizer
        self.onnx_session = None
        self.tokenizer = None
        self.torch_model = None

        if not use_neural:
            return

        # Attempt 1: Load ONNX model if specified or exists
        default_onnx = "models/myanmar-name-encoder-int8.onnx"
        chosen_onnx = onnx_model_path or (default_onnx if os.path.exists(default_onnx) else None)

        if chosen_onnx and os.path.exists(chosen_onnx) and HAS_ONNX:
            try:
                self.onnx_session = ort.InferenceSession(chosen_onnx, providers=["CPUExecutionProvider"])
                tok_path = pytorch_model_path or "models/myanmar-name-encoder"
                if os.path.exists(tok_path):
                    self.tokenizer = AutoTokenizer.from_pretrained(tok_path)
                print(f"Loaded ONNX model from {chosen_onnx}")
                return
            except Exception as e:
                print(f"Warning: Failed to load ONNX model: {e}")

        # Attempt 2: Load PyTorch SentenceTransformer
        default_pt = "models/myanmar-name-encoder"
        chosen_pt = pytorch_model_path or (default_pt if os.path.exists(default_pt) else None)
        if chosen_pt and os.path.exists(chosen_pt) and HAS_TORCH:
            try:
                self.torch_model = SentenceTransformer(chosen_pt)
                print(f"Loaded PyTorch SentenceTransformer from {chosen_pt}")
            except Exception as e:
                print(f"Warning: Failed to load PyTorch model: {e}")

    def encode_onnx(self, texts: List[str]) -> np.ndarray:
        """Computes embeddings using ONNX runtime and mean pooling."""
        inputs = self.tokenizer(texts, padding=True, truncation=True, max_length=32, return_tensors="np")
        ort_inputs = {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"],
        }
        ort_outs = self.onnx_session.run(None, ort_inputs)
        # Mean pooling
        last_hidden = ort_outs[0]
        mask = np.expand_dims(inputs["attention_mask"], -1)
        sum_embeddings = np.sum(last_hidden * mask, axis=1)
        sum_mask = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask
        # Normalize to unit length
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.clip(norms, a_min=1e-9, a_max=None)

    def compute_neural_similarity(self, name1: str, name2: str) -> float:
        """Computes cosine similarity between embeddings of two names."""
        if self.onnx_session and self.tokenizer:
            embs = self.encode_onnx([name1, name2])
            sim = float(np.dot(embs[0], embs[1]))
            return max(0.0, min(1.0, sim))

        if self.torch_model:
            embs = self.torch_model.encode([name1, name2], normalize_embeddings=True)
            sim = float(np.dot(embs[0], embs[1]))
            return max(0.0, min(1.0, sim))

        return 0.0

    def match(self, name1: str, name2: str) -> Dict[str, Any]:
        """
        Calculates hybrid similarity between two names combining
        rule-based phonetic score and neural embedding similarity.
        """
        # Step 1: Rule-based phonetic evaluation (takes ~0.05ms)
        rule_res = self.normalizer.compare_names(name1, name2)

        # If exact literal match or identical phonetic pronunciation, return immediately
        if rule_res["confidence"] in ["exact", "high"] and rule_res["score"] >= 0.90:
            return rule_res

        # Step 2: Neural embedding evaluation
        neural_sim = 0.0
        if self.use_neural and (self.onnx_session or self.torch_model):
            neural_sim = self.compute_neural_similarity(name1, name2)
            rule_res["neural_similarity"] = round(neural_sim, 3)

            # Combined hybrid score (take the stronger of phonetic rule or balanced hybrid)
            hybrid_score = (0.50 * neural_sim) + (0.50 * rule_res["score"])
            final_score = max(hybrid_score, rule_res["score"]) if rule_res["score"] >= 0.85 else hybrid_score
            rule_res["score"] = round(final_score, 3)
            rule_res["is_duplicate"] = bool(rule_res["is_duplicate"] or final_score >= 0.70 or neural_sim >= 0.75)
            rule_res["confidence"] = "high" if final_score >= 0.85 else ("medium" if final_score >= 0.70 else "low")
            if neural_sim >= 0.75:
                rule_res["match_reasons"].append(f"Neural Semantic Similarity: {neural_sim:.2f}")

        return rule_res
