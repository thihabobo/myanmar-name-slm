"""
Linguistic knowledge base of Myanmar & Ethnic naming systems.
Comprehensive inventory of syllables, prefixes, and Romanized Burglish spelling variations
spanning Bamar, Shan, Kachin, Kayin, Chin, Mon, Kayah, and Rakhine.
"""

from typing import Dict, List, Tuple

# Ethnic-specific prefixes and honorifics
ETHNIC_PREFIXES = {
    "bamar": {
        "male": ["U", "Ko", "Mg", "Maung", "Bo"],
        "female": ["Daw", "Ma"],
        "neutral": ["Dr"],
    },
    "shan": {
        "male": ["Sai", "Khun", "Sao", "Lung", "Sam", "Sarm"],
        "female": ["Nang", "Pa", "Mae", "Nang Mwe"],
        "neutral": ["Sao"],
    },
    "kachin": {
        "male": ["Ja", "Naw", "Seng", "Brang", "Gam", "Gun", "Dau", "Hpung"],
        "female": ["Roi", "Lu", "Htu", "Kai", "Ja", "Seng"],
        "neutral": ["Duwa", "Maran", "Lahpai", "Nhkum", "Kareng"],
    },
    "kayin": {
        "male": ["Saw", "Thra", "Saw Eh", "Saw Bo"],
        "female": ["Naw", "Thramu", "Naw Phaw", "Naw Mu"],
        "neutral": [],
    },
    "chin": {
        "male": ["Salai", "Pa", "Pu", "Thang"],
        "female": ["Mai", "Nu", "Pi", "Dim"],
        "neutral": [],
    },
    "mon": {
        "male": ["Min", "Nai", "Nai Htaw"],
        "female": ["Mi", "Mi Kon"],
        "neutral": [],
    },
    "kayah": {
        "male": ["Khu", "Reh", "Khu Oo", "Bu"],
        "female": ["Maw", "Meh", "Maw Meh"],
        "neutral": [],
    },
    "rakhine": {
        "male": ["U", "Ko", "Maung", "Oo", "San", "Chay", "Khaing"],
        "female": ["Daw", "Ma", "Aye", "Khaing"],
        "neutral": ["Khaing", "Khine"],
    },
}

# Authentic syllables by ethnic group
ETHNIC_SYLLABLES: Dict[str, List[str]] = {
    "bamar": [
        "Kyaw", "Swar", "Win", "Htun", "Tun", "Aung", "Myint", "Lin", "Lynn", "Thant",
        "San", "Soe", "Su", "Zin", "Thin", "Wai", "Htet", "Thet", "Yan", "Naing",
        "Moe", "Mya", "Nwe", "Cho", "Lwin", "Tin", "Hla", "Than", "Sein", "Phyo",
        "Pyae", "Pyo", "Thida", "Thandar", "Thuzar", "Khin", "Aye", "Ei", "Mon", "Nu",
        "Nilar", "Ni", "Swe", "Swe", "Zayar", "Kaung", "Khant", "Min", "Ko", "Lay",
        "Kyi", "Shwe", "Hnin", "Yee", "Yu", "May", "Myat", "Noe", "Thiri", "Wint",
    ],
    "shan": [
        "Kham", "Seng", "Hseng", "Murng", "Moon", "Wan", "Leng", "Noung", "Naung",
        "Tip", "Mo", "Kyar", "Hpa", "Hein", "Kaw", "Jarm", "Keow", "Hom", "Nwe",
        "Pao", "Noom", "Hurn", "Hsen", "Pang", "Teng", "Sang", "Long", "La", "Pin",
    ],
    "kachin": [
        "Seng", "Naw", "Brang", "Ja", "Ing", "Htu", "Htoi", "Roi", "Lu", "Kai",
        "Hpung", "Gum", "Bawk", "Hpan", "Zau", "Awng", "Tu", "Dan", "La", "Hkun",
        "Hkawng", "Raw", "Hting", "Ging", "Tang", "Shing", "Kawn", "Mai", "San",
    ],
    "kayin": [
        "Eh", "Htoo", "Htu", "Paw", "Phaw", "Wah", "War", "Mu", "Moo", "K'Nyaw",
        "Plah", "Lar", "Soe", "Shwe", "Poe", "Gay", "Bwe", "Kler", "Dah", "Naw",
        "Ka", "Paw", "Mya", "Tha", "Blue", "Doh", "Ta", "Nay", "Say", "Khu",
    ],
    "chin": [
        "Lian", "Thang", "Sang", "Sung", "Par", "Tial", "Cung", "Bik", "Mang",
        "Kip", "Hnem", "Ceu", "Dim", "Za", "Khen", "Cin", "Cer", "Lal", "Kim",
        "Rem", "Sui", "Tha", "Val", "Bawm", "Khai", "Muan", "Nawn", "Pui", "Zing",
    ],
    "mon": [
        "Tala", "Kon", "Chan", "Htaw", "Sorn", "Mon", "Ong", "Non", "Rot", "Smeng",
        "Kao", "Banya", "Raja", "Nyi", "Kalyar", "Doi", "Pao", "Htaik", "Phat",
    ],
    "kayah": [
        "Reh", "Meh", "Plah", "Nye", "Boe", "Myar", "Dee", "Khu", "Poe", "Mo",
        "Shar", "Klo", "Lee", "Soe", "Nyo", "Tu", "Pay", "Htoo", "Pha", "Ray",
    ],
    "rakhine": [
        "Khaing", "Khine", "San", "Chay", "Gyi", "Nu", "Sein", "Zan", "Phyu", "Mra",
        "Than", "Maung", "Thein", "Tin", "Shwe", "Chay", "Aye", "Hla", "Pauk", "Baw",
    ],
}

# Phonetic variant transformation rules (Simulates how Burglish is typed)
SYLLABLE_PHONETIC_VARIANTS: Dict[str, List[str]] = {
    "Kyaw": ["Kyaw", "Kyaww", "Gyaw", "Kjaw", "Kyau"],
    "Swar": ["Swar", "Zwar", "Thwar", "Sar", "Zar"],
    "Htun": ["Htun", "Tun", "Htoon", "Toon", "Tunn"],
    "Lin": ["Lin", "Lynn", "Lyn", "Linn", "Lynne"],
    "Win": ["Win", "Wynn", "Wyn", "Winn"],
    "Myint": ["Myint", "Myin", "Myinnt", "Myinte"],
    "Aung": ["Aung", "Awng", "Ang", "Oung"],
    "Khin": ["Khin", "Kheng", "Hkin", "Kin", "Khinn"],
    "Aye": ["Aye", "Ei", "Ai", "Ay", "Ae"],
    "Ei": ["Ei", "Aye", "Ai", "Ay", "Eii"],
    "Thant": ["Thant", "Sant", "Than", "San", "Thantt"],
    "San": ["San", "Sant", "Sann", "Thann"],
    "Phyo": ["Phyo", "Pyo", "Pyae", "Phyoe", "Pyoe"],
    "Pyae": ["Pyae", "Pyo", "Phyo", "Pyai", "Phyae"],
    "Thuzar": ["Thuzar", "Thu Zar", "Thuzarr", "Suzar", "Su Zar"],
    "Thida": ["Thida", "Thi Da", "Sida", "Theeda"],
    "Thandar": ["Thandar", "Than Dar", "Sandar", "San Dar"],
    "Wai": ["Wai", "Way", "Wei", "We"],
    "Htet": ["Htet", "Tet", "Htatt", "Tt"],
    "Thet": ["Thet", "Tet", "Thatt"],
    "Yan": ["Yan", "Yann", "Rann", "Ran"],
    "Naing": ["Naing", "Nine", "Naen", "Naine"],
    "Nilar": ["Nilar", "Ni Lar", "Neelar", "Nee Lar"],
    "Shwe": ["Shwe", "Shway", "Shwea", "Shwai"],
    "Moe": ["Moe", "Mo", "Moee"],
    "Mya": ["Mya", "Myar", "Myaa"],
    "Su": ["Su", "Sue", "Soe", "Soo"],
    "Soe": ["Soe", "Su", "Soee", "Sow"],
    "Zin": ["Zin", "Zinn", "Zing", "Sin"],
    "Thin": ["Thin", "Thinn", "Shin", "Sin"],
    "Cho": ["Cho", "Choe", "Qho"],
    "Lwin": ["Lwin", "Lwinn", "Lwyn"],
    "Hla": ["Hla", "La", "Lha"],
    "Hnin": ["Hnin", "Nin", "Hninn"],
    "Kham": ["Kham", "Hkam", "Kam", "Khamm"],
    "Seng": ["Seng", "Hseng", "Sin", "Sing", "Sen"],
    "Noung": ["Noung", "Naung", "Nong", "Naungg"],
    "Htoo": ["Htoo", "Htu", "Tu", "Too"],
    "Phaw": ["Phaw", "Paw", "Phor"],
    "Lian": ["Lian", "Liang", "Lyan", "Leen"],
    "Thang": ["Thang", "Tang", "Than"],
    "Reh": ["Reh", "Ray", "Rae", "Rehh"],
    "Meh": ["Meh", "May", "Mae"],
}
