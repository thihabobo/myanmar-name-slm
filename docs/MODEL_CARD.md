---
language:
- my
- en
tags:
- myanmar
- burglish
- name-matching
- deduplication
- healthcare
- phonetic-embedding
- sentence-transformers
license: mit
datasets:
- custom-myanmar-ethnic-names
metrics:
- f1
- precision
- recall
- accuracy
---

# Model Card: Myanmar Name Semantic Matcher & Embedding SLM (Burglish-SLM)

## Model Overview
- **Name:** Myanmar & Ethnic Name Semantic Matcher (`burglish-name-encoder`)
- **Version:** 1.0.0
- **Base Architecture:** Fine-tuned Transformer / Siamese Bi-Encoder (MiniLM / BGE-Small)
- **Parameter Count:** ~22 Million Parameters (INT8 Quantized: ~25 MB)
- **Primary Use Case:** Real-time semantic duplicate detection, fuzzy candidate ranking, and Burglish spelling harmonization across Myanmar and Ethnic personal names.
- **Latency:** ~1.2 milliseconds per pair on CPU via ONNX Runtime.

---

## 1. Intended Use & Scope

### Primary Intended Uses:
1. **Hospital & Clinical Informatics:** Preventing duplicate patient medical records when patients are registered with different English transliterations across departments (e.g. Counter POS vs Ultrasound vs OPD).
2. **Identity Deduplication:** Merging customer and patient profiles in POS, Banking, Telecom, and Government registries.
3. **Phonetic Autocomplete:** Enabling rapid search where typing `Kyaw Zwar` matches `Kyaw Swar`, or `Ei Khine` matches `Aye Khaing`.

---

## 2. Ethnic Coverage & Representation

The model and dataset specifically represent eight major Myanmar ethnic linguistic groups:
- **Bamar (ဗမာ):** 60+ core syllables, prefixes (`U`, `Daw`, `Ko`, `Ma`, `Mg`, `Dr`), diphthongs, and consonant clusters (`ky`, `sw`, `zw`, `ph`, `th`).
- **Shan (ရှမ်း):** Prefixes (`Sai`, `Nang`, `Sao`, `Khun`), Tai tone transliterations (`Kham`, `Seng`, `Leng`, `Noung`).
- **Kachin (ကချင်):** Clan surnames (`Maran`, `Lahpai`, `Nhkum`), birth order prefixes (`Ja`, `Naw`, `Seng`, `Brang`, `Roi`, `Lu`).
- **Kayin (ကရင်):** Prefixes (`Saw`, `Naw`, `Thra`, `Thramu`), S'gaw/Pwo syllables (`Eh`, `Htoo`, `Paw`, `Wah`, `Mu`).
- **Chin (ချင်း):** Lineage titles (`Salai`, `Mai`), Chin syllables (`Lian`, `Thang`, `Luai`, `Par`, `Bik`, `Cung`).
- **Mon (မွန်):** Historic prefixes (`Nai`, `Min`, `Mi`), Mon syllables (`Htaw`, `Sorn`, `Chan`, `Tala`).
- **Kayah (ကယား):** Prefixes (`Khu`, `Maw`, `Meh`, `Reh`), syllables (`Plah`, `Nye`, `Boe`).
- **Rakhine (ရခိုင်):** Regional variations (`Khaing`, `Khine`, `San`, `Chay`, `Zan`, `Oo`).

---

## 3. Training & Evaluation Methodology

### Training Objective:
- Trained using **Siamese Triplet MultipleNegativesRankingLoss**:
  $$\mathcal{L} = -\log \frac{e^{\text{sim}(a, p) / \tau}}{\sum_{j} e^{\text{sim}(a, n_j) / \tau}}$$
  Forces representations of phonetic variants of the same individual closer while actively repelling hard negatives (individuals with shared prefixes or single shared syllables).

### Evaluation Benchmarks (on 2,000 hold-out pairs):

| Method | Accuracy | Precision | Recall | F1-Score | Latency (CPU) |
|---|---|---|---|---|---|
| **Standard SQL LIKE / Exact** | 67.0% | 100.0% | 35.4% | 52.3% | 0.2 μs |
| **Standard English Soundex** | 73.8% | 82.2% | 62.0% | 70.7% | 2.5 μs |
| **Burglish Phonetic Rule Matcher** | 84.9% | 96.6% | 72.9% | 83.1% | 87.8 μs |
| **Neural Hybrid SLM (This Model)** | **94.2%** | **95.8%** | **92.6%** | **94.1%** | **1.2 ms** |

---

## 4. Hardware & Efficiency

- **Training Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM), CUDA 13.2.
- **Inference Runtime:** Supports pure CPU execution via ONNX Runtime (`onnxruntime-int8`), requiring **zero GPU** and less than 60 MB of system RAM.

---

## 5. Limitations & Bias

- **Non-Myanmar Foreign Names:** Foreign expatriate names (e.g. European, Japanese, Arabic) may not benefit from Myanmar-specific consonant/vowel rules.
- **Very Short Monosyllabic Names:** Names consisting of a single letter or 2 letters (e.g. `Bo`, `U`) should be coupled with phone numbers or age for robust identification.
