"""
Synthetic Training Dataset Generator for Myanmar & Ethnic Name Semantic Matching.
Generates comprehensive positive, negative, and hard-negative name pairs and triplets
covering Bamar, Shan, Kachin, Kayin, Chin, Mon, Kayah, and Rakhine naming systems.
"""

import json
import random
import os
from typing import List, Dict, Tuple, Any
from ethnic_data import ETHNIC_PREFIXES, ETHNIC_SYLLABLES, SYLLABLE_PHONETIC_VARIANTS


def get_syllable_variants(syl: str) -> List[str]:
    """Returns known phonetic variants for a syllable, or itself."""
    return SYLLABLE_PHONETIC_VARIANTS.get(syl, [syl])


def introduce_typo(text: str) -> str:
    """Simulates realistic human typing error (1-char deletion, insertion, transposition, substitution)."""
    if len(text) <= 3:
        return text
    action = random.choice(["delete", "duplicate", "swap", "substitute"])
    idx = random.randint(1, len(text) - 2)

    if action == "delete":
        return text[:idx] + text[idx + 1 :]
    elif action == "duplicate":
        return text[:idx] + text[idx] + text[idx:]
    elif action == "swap":
        return text[:idx] + text[idx + 1] + text[idx] + text[idx + 2 :]
    elif action == "substitute":
        near_keys = {"a": "s", "s": "a", "k": "j", "m": "n", "n": "m", "i": "o", "o": "i", "e": "w"}
        c = text[idx].lower()
        sub = near_keys.get(c, "a")
        return text[:idx] + sub + text[idx + 1 :]
    return text


class MyanmarNameDatasetGenerator:
    """Generates rich semantic pairs and triplets for training Small Language Models."""

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate_random_name(self, ethnic_group: str, length: int = 2) -> Tuple[str, str, List[str]]:
        """
        Generates an authentic random name for an ethnic group.
        Returns: (full_name_with_honorific, base_name, syllables)
        """
        syllables_pool = ETHNIC_SYLLABLES.get(ethnic_group, ETHNIC_SYLLABLES["bamar"])
        selected_syls = random.sample(syllables_pool, min(length, len(syllables_pool)))
        base_name = " ".join(selected_syls)

        # Prefix
        prefixes_dict = ETHNIC_PREFIXES.get(ethnic_group, ETHNIC_PREFIXES["bamar"])
        gender = random.choice(["male", "female", "neutral"])
        prefixes = prefixes_dict.get(gender, [""])
        prefix = random.choice(prefixes) if prefixes else ""

        full_name = f"{prefix} {base_name}".strip() if prefix else base_name
        return full_name, base_name, selected_syls

    def generate_phonetic_variant(self, syllables: List[str], prefix: str = "") -> str:
        """Transforms a name using known Burglish phonetic rules."""
        variant_syls = []
        for syl in syllables:
            variants = get_syllable_variants(syl)
            variant_syls.append(random.choice(variants))

        # Randomly choose prefix variation (e.g. strip it, keep it, or change U -> Ko)
        if prefix:
            prefix_choice = random.choice(["keep", "strip", "variant"])
            if prefix_choice == "strip":
                prefix = ""
            elif prefix_choice == "variant":
                if prefix.lower() == "u":
                    prefix = random.choice(["Ko", "U", "Oo"])
                elif prefix.lower() == "daw":
                    prefix = random.choice(["Daw", "Ma"])
                elif prefix.lower() == "nang":
                    prefix = random.choice(["Nang", "Nan"])
                elif prefix.lower() == "sai":
                    prefix = random.choice(["Sai", "Say"])
                elif prefix.lower() == "saw":
                    prefix = random.choice(["Saw", "Sor"])

        name_str = " ".join(variant_syls)
        # Randomly concatenate (e.g. Thu Zar -> Thuzar)
        if len(variant_syls) == 2 and random.random() < 0.25:
            name_str = "".join(variant_syls)

        # Randomly add minor human typo
        if random.random() < 0.15:
            name_str = introduce_typo(name_str)

        return f"{prefix} {name_str}".strip() if prefix else name_str

    def load_hospital_names(self, file_path: str) -> List[str]:
        """Loads and cleans real hospital patient names from text file."""
        if not os.path.exists(file_path):
            return []
        names = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                n = line.strip()
                if len(n) >= 2 and not n.isdigit() and n.lower() != "unknown":
                    # Title case for standard representation
                    names.append(" ".join(w.capitalize() for w in n.split()))
        return list(set(names))

    def build_dataset(
        self, num_samples: int = 50000, hospital_names_file: str = "data/hospital_raw_names.txt"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Builds a comprehensive balanced dataset combining:
        1. 43,000+ authentic hospital patient names with real-world distribution
        2. Synthetic permutations across 8 Myanmar ethnic naming systems
        """
        pairs = []
        triplets = []
        ethnic_groups = list(ETHNIC_SYLLABLES.keys())

        # Load real hospital names if available
        hospital_names = self.load_hospital_names(hospital_names_file)
        if hospital_names:
            print(f"Loaded {len(hospital_names):,} authentic hospital patient names!")

        print(f"Generating {num_samples} training samples across 8 Myanmar ethnic groups and hospital records...")

        # Half from real hospital names, half from ethnic generators
        for i in range(num_samples):
            use_real = bool(hospital_names and random.random() < 0.55)

            if use_real:
                full_name = random.choice(hospital_names)
                tokens = full_name.split()
                if len(tokens) > 1 and tokens[0].lower() in ["u", "daw", "ko", "ma", "mg", "dr"]:
                    prefix = tokens[0]
                    syls = tokens[1:]
                else:
                    prefix = ""
                    syls = tokens
                ethnic_group = "hospital_real_patient"
            else:
                ethnic_group = random.choice(ethnic_groups)
                name_len = random.choice([2, 3, 2, 3, 4])
                full_name, base_name, syls = self.generate_random_name(ethnic_group, name_len)
                prefix = full_name.split()[0] if len(full_name.split()) > len(syls) else ""

            # Positive variant (Same person with Burglish / phonetic spelling variation)
            positive_variant = self.generate_phonetic_variant(syls, prefix)

            # Hard Negative (Same prefix or shared syllable, but completely different person)
            if use_real and hospital_names:
                # Find another real patient that shares at least one syllable or prefix
                candidates = [h for h in random.sample(hospital_names, min(50, len(hospital_names))) if h != full_name]
                shared = [c for c in candidates if any(s.lower() in c.lower() for s in syls)]
                hard_negative = shared[0] if shared else random.choice(candidates)
            else:
                diff_syls_pool = [s for s in ETHNIC_SYLLABLES[ethnic_group] if s not in syls]
                if diff_syls_pool:
                    shared_syl = random.choice(syls)
                    neg_syl2 = random.choice(diff_syls_pool)
                    neg_syls = [shared_syl, neg_syl2] if random.random() < 0.5 else [neg_syl2, shared_syl]
                    hard_negative = f"{prefix} {' '.join(neg_syls)}".strip()
                else:
                    hard_negative, _, _ = self.generate_random_name(random.choice(ethnic_groups), 2)

            # Random completely different negative
            other_ethnic = random.choice([e for e in ethnic_groups if e != ethnic_group] or [ethnic_group])
            easy_negative, _, _ = self.generate_random_name(other_ethnic, 2)

            # Record positive pair (label = 1.0)
            pairs.append({
                "name1": full_name,
                "name2": positive_variant,
                "label": 1.0,
                "pair_type": "phonetic_equivalent",
                "ethnicity": ethnic_group,
            })

            # Record hard negative pair (label = 0.0)
            pairs.append({
                "name1": full_name,
                "name2": hard_negative,
                "label": 0.0,
                "pair_type": "hard_negative_shared_syllable",
                "ethnicity": ethnic_group,
            })

            # Record Triplet (anchor, positive, negative)
            triplets.append({
                "anchor": full_name,
                "positive": positive_variant,
                "negative": hard_negative if random.random() < 0.7 else easy_negative,
                "ethnicity": ethnic_group,
            })

        random.shuffle(pairs)
        random.shuffle(triplets)

        return {"pairs": pairs, "triplets": triplets}

    def save_to_disk(self, data: Dict[str, List[Dict[str, Any]]], output_dir: str):
        """Saves generated dataset to jsonl files."""
        os.makedirs(output_dir, exist_ok=True)

        pairs = data["pairs"]
        triplets = data["triplets"]

        split_idx = int(len(pairs) * 0.85)
        train_pairs = pairs[:split_idx]
        val_pairs = pairs[split_idx:]

        # Save train pairs
        train_path = os.path.join(output_dir, "train_pairs.jsonl")
        with open(train_path, "w", encoding="utf-8") as f:
            for p in train_pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        # Save val pairs
        val_path = os.path.join(output_dir, "val_pairs.jsonl")
        with open(val_path, "w", encoding="utf-8") as f:
            for p in val_pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        # Save triplets
        triplet_path = os.path.join(output_dir, "triplets.jsonl")
        with open(triplet_path, "w", encoding="utf-8") as f:
            for t in triplets:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")

        print(f"Dataset saved successfully!")
        print(f"  - Train pairs: {len(train_pairs):,} samples -> {train_path}")
        print(f"  - Validation pairs: {len(val_pairs):,} samples -> {val_path}")
        print(f"  - Triplet samples: {len(triplets):,} samples -> {triplet_path}")


if __name__ == "__main__":
    generator = MyanmarNameDatasetGenerator()
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    hosp_file = os.path.join(data_dir, "hospital_raw_names.txt")
    dataset = generator.build_dataset(num_samples=40000, hospital_names_file=hosp_file)
    generator.save_to_disk(dataset, data_dir)

