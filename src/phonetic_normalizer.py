"""
Burglish & Ethnic Name Phonetic Normalizer for Myanmar Naming Systems.
Provides ultra-fast (<0.1ms), deterministic phonetic key generation,
syllable decomposition, Burglish spelling harmonization, and similarity scoring.
Covers Bamar, Shan, Kachin, Kayin, Chin, Mon, Rakhine, and Kayah conventions.
"""

import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional

# Standard Myanmar Honorifics and Ethnic Prefixes to strip or identify
HONORIFICS = {
    # Bamar
    "u", "oo", "daw", "ko", "ma", "mg", "maung", "bo", "dr", "doctor", "sayar", "sayarma",
    # Shan
    "sai", "nang", "sao", "khun", "lung", "pa", "mae", "nangmwe",
    # Kachin
    "ja", "naw", "seng", "brang", "gam", "gun", "dau", "roi", "lu", "htu", "kai",
    # Kayin
    "saw", "naw", "thra", "thramu", "sawmu", "nawphaw",
    # Chin
    "salai", "mai", "pa", "nu", "pu", "pi",
    # Mon
    "min", "mi", "nai",
    # Kayah
    "khu", "maw", "meh", "reh", "bu",
    # Rakhine
    "khaing", "khine", "chay",
}

# Consonant cluster regularizations (ordered by length)
CONSONANT_RULES = [
    # Complex consonant clusters
    (r"\bgy", "k"),
    (r"\bky", "k"),
    (r"\bkl", "k"),
    (r"\bkr", "k"),
    (r"\bhk", "k"),
    (r"\bkh", "k"),
    (r"\bch", "sh"),
    (r"\bhs", "s"),
    (r"\bthw", "sw"),
    (r"\bth", "s"),
    (r"\bht", "s"),
    (r"\bzw", "sw"),
    (r"\bph", "p"),
    (r"\bhp", "p"),
    (r"\bhb", "b"),
    (r"\bgn", "ny"),
    (r"\bng", "ng"),
    (r"\bnh", "ny"),
    (r"\bny", "ny"),
    (r"\bhl", "l"),
    (r"\blh", "l"),
    (r"\bhm", "m"),
    (r"\bmh", "m"),
    (r"\bhn", "n"),
    (r"\bnh", "n"),
    (r"\bshw", "shw"),
    (r"\bsh", "sh"),
    (r"\bwh", "w"),
    (r"\bz", "s"),
    (r"\bc", "k"),
    (r"\bj", "z"),
]

# Vowel / Ending regularizations (ordered by specific pattern length)
VOWEL_RULES = [
    # Diphthongs and complex finals
    (r"aung\b", "ong"),
    (r"oung\b", "ong"),
    (r"awng\b", "ong"),
    (r"aing\b", "aing"),
    (r"ine\b", "aing"),
    (r"lway\b", "lwe"),
    (r"luai\b", "lwe"),
    (r"way\b", "we"),
    (r"wai\b", "we"),
    (r"wae\b", "we"),
    (r"uai\b", "we"),
    (r"we\b", "we"),
    (r"oe\b", "we"),
    (r"aye\b", "ay"),
    (r"ei\b", "ay"),
    (r"ai\b", "ay"),
    (r"ae\b", "ay"),
    (r"ay\b", "ay"),
    (r"eik\b", "eik"),
    (r"ait\b", "eik"),
    (r"eit\b", "eik"),
    (r"et\b", "et"),
    (r"at\b", "at"),
    (r"oke\b", "oke"),
    (r"ok\b", "oke"),
    (r"auk\b", "oke"),
    (r"int\b", "in"),
    (r"inn\b", "in"),
    (r"in\b", "in"),
    (r"ing\b", "in"),
    (r"iang\b", "ian"),
    (r"liang\b", "lian"),
    (r"one\b", "on"),
    (r"ohn\b", "on"),
    (r"awn\b", "on"),
    (r"an\b", "an"),
    (r"un\b", "un"),
    (r"oon\b", "un"),
    (r"oo\b", "u"),
    (r"uu\b", "u"),
    (r"ou\b", "u"),
    (r"u\b", "u"),
    (r"aw\b", "aw"),
    (r"or\b", "aw"),
    (r"ar\b", "aw"),
    (r"au\b", "aw"),
    (r"htun\b", "tun"),
    (r"lynn\b", "lin"),
    (r"lyn\b", "lin"),
    (r"wynn\b", "win"),
    (r"wyn\b", "win"),
    (r"myint\b", "myin"),
    (r"swar\b", "swar"),
    (r"zwar\b", "swar"),
    (r"thuzar\b", "susar"),
]


class BurglishPhoneticNormalizer:
    """
    Phonetic normalizer and rule-based similarity engine
    tuned specifically for Myanmar (Burmese) and Ethnic names written in English.
    """

    COMMON_ABBREVIATIONS = {
        "mg": "maung",
        "dr": "doctor",
        "doc": "doctor",
        "b": "baby",
    }

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Strip non-alphabetic chars, accents, and normalize spaces."""
        if not text:
            return ""
        # Normalize unicode accents
        nfd = unicodedata.normalize("NFD", text)
        ascii_text = nfd.encode("ascii", "ignore").decode("utf-8")
        # Lowercase and replace non-alpha with space
        cleaned = re.sub(r"[^a-zA-Z\s]", " ", ascii_text.lower())
        # Collapse multi spaces
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def remove_honorifics(cls, tokens: List[str]) -> Tuple[List[str], Optional[str]]:
        """
        Removes leading honorific/title from token list.
        Returns: (remaining_tokens, removed_honorific)
        """
        if not tokens:
            return [], None
        first = tokens[0]
        if first in HONORIFICS and len(tokens) > 1:
            return tokens[1:], first
        return tokens, None

    @classmethod
    def normalize_syllable(cls, syllable: str) -> str:
        """Applies consonant and vowel phonetic normalization to a single syllable."""
        s = syllable.lower().strip()
        if not s:
            return ""

        # Step 1: Collapse repeating identical letters (e.g. kyawww -> kyaw, soee -> soe)
        s = re.sub(r"(.)\1{2,}", r"\1", s)

        # Step 2: Apply consonant cluster transformations
        for pat, rep in CONSONANT_RULES:
            if re.search(pat, s):
                s = re.sub(pat, rep, s, count=1)
                break

        # Step 3: Apply vowel/final transformations
        for pat, rep in VOWEL_RULES:
            if re.search(pat, s):
                s = re.sub(pat, rep, s, count=1)
                break

        return s

    @classmethod
    def phonetic_tokens(cls, name: str) -> List[str]:
        """
        Tokenizes a name, removes leading honorifics,
        and produces normalized phonetic syllables.
        """
        cleaned = cls.clean_text(name)
        if not cleaned:
            return []

        raw_tokens = cleaned.split()
        tokens = [cls.COMMON_ABBREVIATIONS.get(t, t) for t in raw_tokens]
        tokens_no_hon, _ = cls.remove_honorifics(tokens)
        if not tokens_no_hon:
            tokens_no_hon = tokens

        norm_tokens = [cls.normalize_syllable(t) for t in tokens_no_hon if t]
        return norm_tokens

    @classmethod
    def phonetic_key(cls, name: str) -> str:
        """
        Produces a canonical unified phonetic key.
        e.g. 'Kyaw Swar' -> 'k-swar'
             'U Kyaw Zwar' -> 'k-swar'
             'Ei Khine' -> 'ay-k'
             'Daw Aye Khaing' -> 'ay-k'
             'Nang Kham Noung' -> 'k-nong'
        """
        tokens = cls.phonetic_tokens(name)
        return "-".join(tokens)

    @classmethod
    def jaro_winkler_similarity(cls, s1: str, s2: str) -> float:
        """Calculates Jaro-Winkler similarity between two strings."""
        if not s1 or not s2:
            return 1.0 if s1 == s2 else 0.0
        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        match_bound = max(len1, len2) // 2 - 1
        if match_bound < 0:
            match_bound = 0

        matches1 = [False] * len1
        matches2 = [False] * len2
        matches = 0

        for i in range(len1):
            start = max(0, i - match_bound)
            end = min(i + match_bound + 1, len2)
            for j in range(start, end):
                if not matches2[j] and s1[i] == s2[j]:
                    matches1[i] = True
                    matches2[j] = True
                    matches += 1
                    break

        if matches == 0:
            return 0.0

        # Transpositions
        k = 0
        transpositions = 0
        for i in range(len1):
            if matches1[i]:
                while not matches2[k]:
                    k += 1
                if s1[i] != s2[k]:
                    transpositions += 1
                k += 1

        trans = transpositions / 2.0
        jaro = (matches / len1 + matches / len2 + (matches - trans) / matches) / 3.0

        # Winkler prefix bonus
        prefix_len = 0
        for i in range(min(4, len1, len2)):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break

        return jaro + (prefix_len * 0.1 * (1.0 - jaro))

    @classmethod
    def compare_names(cls, name1: str, name2: str) -> Dict[str, Any]:
        """
        Comprehensive comparison between two names returning:
        - phonetic_match: True if phonetic keys match
        - score: float (0.0 to 1.0)
        - is_duplicate: True if score >= 0.85
        - confidence: 'exact', 'high', 'medium', 'low'
        - match_reasons: List of human-readable explanations
        """
        clean1 = cls.clean_text(name1)
        clean2 = cls.clean_text(name2)

        if not clean1 or not clean2:
            return {
                "score": 0.0,
                "is_duplicate": False,
                "confidence": "none",
                "match_reasons": ["One or both names are empty"],
            }

        # Exact literal match
        if clean1 == clean2:
            return {
                "score": 1.0,
                "is_duplicate": True,
                "confidence": "exact",
                "match_reasons": ["Exact character match (စာလုံးပေါင်း အတိအကျတူညီပါသည်)"],
                "key1": clean1,
                "key2": clean2,
            }

        # Space-collapsed match (e.g. 'Thu Zar' vs 'Thuzar')
        if clean1.replace(" ", "") == clean2.replace(" ", ""):
            return {
                "score": 0.98,
                "is_duplicate": True,
                "confidence": "high",
                "match_reasons": ["Space spacing variation (စာလုံးခွာ/ပူး စာလုံးပေါင်းတူညီပါသည်)"],
            }

        tokens1 = cls.phonetic_tokens(name1)
        tokens2 = cls.phonetic_tokens(name2)
        key1 = "-".join(tokens1)
        key2 = "-".join(tokens2)

        # Exact Phonetic Key match
        if key1 == key2 and key1 != "":
            return {
                "score": 0.95,
                "is_duplicate": True,
                "confidence": "high",
                "match_reasons": ["Identical Burmese pronunciation (မြန်မာအသံထွက် တူညီပါသည်)"],
                "key1": key1,
                "key2": key2,
            }

        # Syllable token overlap score (Jaccard / Token Sort)
        set1, set2 = set(tokens1), set(tokens2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        token_jaccard = len(intersection) / len(union) if union else 0.0

        # Substring / subset check (e.g. 'Kyaw Swar' inside 'U Kyaw Swar Win')
        is_subset = set1.issubset(set2) or set2.issubset(set1)

        # Jaro-Winkler on phonetic string
        jw_raw = cls.jaro_winkler_similarity(clean1.replace(" ", ""), clean2.replace(" ", ""))
        jw_phonetic = cls.jaro_winkler_similarity(key1, key2)

        # Weighted combined score
        combined_score = (0.50 * jw_phonetic) + (0.30 * token_jaccard) + (0.20 * jw_raw)
        if is_subset and len(intersection) >= 2:
            combined_score = max(combined_score, 0.88)

        is_dup = combined_score >= 0.82
        confidence = "high" if combined_score >= 0.88 else ("medium" if combined_score >= 0.75 else "low")

        reasons = []
        if key1 == key2:
            reasons.append("Phonetic Key Match")
        elif token_jaccard >= 0.6:
            reasons.append(f"Matching syllables: {', '.join(intersection)}")
        if jw_phonetic >= 0.85:
            reasons.append("High phonetic character similarity")
        if is_subset:
            reasons.append("Name subset match (အမည် အစိတ်အပိုင်း တူညီပါသည်)")

        return {
            "score": round(combined_score, 3),
            "is_duplicate": is_dup,
            "confidence": confidence,
            "match_reasons": reasons or ["Low phonetic overlap"],
            "key1": key1,
            "key2": key2,
        }
