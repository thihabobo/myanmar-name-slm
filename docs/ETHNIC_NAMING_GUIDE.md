# Myanmar & Ethnic Naming Systems: Linguistic & Romanization Guide
> A Comprehensive Reference for Software Engineers, Data Scientists, and Healthcare Informatics in Myanmar.

---

## 1. Overview & The "Burglish" Challenge

In Myanmar, personal names are traditionally non-patronymic (i.e. children do not inherit parental surnames, with few ethnic exceptions), and can consist of 1 to 5 individual syllables.

When names are written in Latin alphabet (**"Burglish"** or Romanized Burmese), there is **no single standardized orthography**. Transliteration is largely phonetic, colloquial, and variable. Consequently:
- The exact same Myanmar word can have 3 to 10 common Romanized spellings.
- Standard English algorithms (Soundex, Metaphone, Double-Metaphone) fail because they are calibrated for Anglo-Saxon or European phonetics.
- Traditional database queries (`WHERE name LIKE '%...%'`) fail when vowels, consonant clusters, or syllable concatenations differ.

---

## 2. Ethnic Naming Conventions

### 🇲🇲 1. Bamar (ဗမာ)
- **Structure:** 1 to 4 syllables, preceded by an honorific title according to age, status, or gender.
- **Honorifics:**
  - `U` (ဦး) / `Ko` (ကို) / `Mg` or `Maung` (မောင်) - Male honorifics.
  - `Daw` (ဒေါ်) / `Ma` (မ) - Female honorifics.
  - `Bo` (ဗိုလ်) / `Dr` (ဒေါက်တာ) - Professional / military honorifics.
- **Common Romanization Variations:**
  - `Kyaw` $\leftrightarrow$ `Zwar` $\leftrightarrow$ `Swar` (ကျော် / စွာ / ဇွာ)
  - `Myint` $\leftrightarrow$ `Myin` $\leftrightarrow$ `Myinnt` (မြင့်)
  - `Win` $\leftrightarrow$ `Wynn` $\leftrightarrow$ `Winn` (ဝင်း)
  - `Htun` $\leftrightarrow$ `Tun` $\leftrightarrow$ `Htoon` (ထွန်း)
  - `Aye` $\leftrightarrow$ `Ei` $\leftrightarrow$ `Ai` $\leftrightarrow$ `Ay` (အေး / အိ)
  - `Phyo` $\leftrightarrow$ `Pyae` $\leftrightarrow$ `Pyo` (ဖြိုး / ပြည့်)
  - `Thant` $\leftrightarrow$ `Sant` $\leftrightarrow$ `Than` (သန့် / စန်း)
  - `Thuzar` $\leftrightarrow$ `Thu Zar` $\leftrightarrow$ `Suzar` (သူဇာ)

---

### 🏔️ 2. Shan (ရှမ်း / Tai)
- **Structure:** Often starts with gender/caste prefixes, followed by Tai syllables denoting precious elements, nature, or radiance.
- **Honorifics & Prefixes:**
  - Male: `Sai` (စိုင်း), `Khun` (ခွန်), `Sao` (စဝ် - nobility), `Lung` (လုင်း - uncle/elder), `Sam` (သၢမ် - third son).
  - Female: `Nang` (နန်း), `Pa` (ပါ - aunt/elder), `Mae` (မဲ), `Nang Mwe` (နန်းမွေ).
- **Core Syllables:**
  - `Kham` (ခမ်း - Gold/Precious) $\leftrightarrow$ often Romanized as `Kham`, `Hkam`, `Kam`.
  - `Seng` (စိင်း / သႅင် - Gem/Jewel) $\leftrightarrow$ `Seng`, `Hseng`, `Sin`.
  - `Noung` (ၼွင် - Youngest) $\leftrightarrow$ `Noung`, `Naung`, `Nong`.
  - `Murng` (မိူင်း - Country/Land) $\leftrightarrow$ `Murng`, `Muang`, `Mong`.
  - `Leng` (လႅင်း - Light/Bright) $\leftrightarrow$ `Leng`, `Laing`.
  - `Tip` (ထိပ် - Peak/Summit) $\leftrightarrow$ `Tip`, `Htip`.
- **Examples:**
  - `Sai Sai Kham Leng`
  - `Nang Kham Noung` $\leftrightarrow$ `Nan Hkam Naung`
  - `Khun Htun Oo`

---

### 🌲 3. Kachin (ကချင် / Jinghpaw, Rawang, Lisu, Lhaovo, Zaiwa)
- **Structure:** May include family/clan surnames (e.g. `Maran`, `Lahpai`, `Nhkum`, `Duwa`) followed by birth-order or status prefixes, and given names.
- **Male Prefixes & Birth Order:**
  - `Gam` (1st son), `Naw` (2nd son), `La` (3rd son), `Tu` (4th son), `Tang` (5th son).
  - Prominent male prefixes: `Ja` (ဂျာ), `Seng` (ဆိုင်း), `Brang` (ဘရန်), `Hpung` (ဖုန်).
- **Female Prefixes & Birth Order:**
  - `Kaw` (1st daughter), `Lu` (2nd daughter), `Roi` (3rd daughter), `Htu` (4th daughter), `Kai` (5th daughter).
  - Prominent female prefixes: `Ja` (ဂျာ), `Seng` (ဆိုင်း).
- **Common Romanization Variations:**
  - `Ja` $\leftrightarrow$ `Zha` $\leftrightarrow$ `Jar`
  - `Hpung` $\leftrightarrow$ `Pung` $\leftrightarrow$ `Hpoong`
  - `Htu` $\leftrightarrow$ `Htoo` $\leftrightarrow$ `Tu`
  - `Seng` $\leftrightarrow$ `Sin` $\leftrightarrow$ `Sing`
- **Examples:**
  - `Ja Seng Ing` $\leftrightarrow$ `Zha Sin Ing`
  - `Lahpai Naw Seng`
  - `Maran Brang Seng`
  - `Roi Ja`

---

### 🌊 4. Kayin (ကရင် / S'gaw, Pwo)
- **Structure:** Preceded by distinct gender markers, often containing virtues, brightness, or peace.
- **Prefixes:**
  - Male: `Saw` (စော), `Thra` (ဆရာ - teacher/pastor), `Saw Bo` (စောဗိုလ်).
  - Female: `Naw` (နော်), `Thramu` (ဆရာမ).
- **Core Syllables:**
  - `Eh` (အယ် - Love/Affection) $\leftrightarrow$ `Eh`, `Aung`, `Ay`.
  - `Htoo` (ထူး - Special/Gold) $\leftrightarrow$ `Htoo`, `Htu`, `Too`.
  - `Paw` / `Phaw` (ဖေါ / ပေါ - Flower/Blossom) $\leftrightarrow$ `Paw`, `Phaw`, `Phor`.
  - `Wah` (ဝါး - White/Pure) $\leftrightarrow$ `Wah`, `War`, `Wa`.
  - `Mu` (မူ - Feminine grace) $\leftrightarrow$ `Mu`, `Moo`.
  - `K'Nyaw` (ကညော - Human/People).
- **Examples:**
  - `Saw Eh Htoo` $\leftrightarrow$ `Saw Eh Htu`
  - `Naw Phaw Paw` $\leftrightarrow$ `Naw Paw Paw`
  - `Saw Hla Tun`

---

### ⛰️ 5. Chin (ချင်း / Tedim, Falam, Hakha, Matu, Mara, Mindat)
- **Structure:** Often preceded by formal markers, followed by historical lineage or clan syllables.
- **Prefixes:**
  - Male: `Salai` (ဆလိုင်း), `Pa` (ပါ), `Pu` (ပု).
  - Female: `Mai` (မိုင်), `Nu` (နု), `Pi` (ပီ).
- **Core Syllables:**
  - `Lian` (Greatness) $\leftrightarrow$ `Lian`, `Liang`, `Lyan`.
  - `Thang` (Fame) $\leftrightarrow$ `Thang`, `Tang`.
  - `Luai` (Abundance) $\leftrightarrow$ `Luai`, `Lway`, `Lwai`.
  - `Par` (Flower) $\leftrightarrow$ `Par`, `Pahr`.
  - `Cung` / `Ceu` (Light/Sun) $\leftrightarrow$ `Cung`, `Ceu`, `Kyung`.
  - `Bik` (Chief/Leader) $\leftrightarrow$ `Bik`, `Bick`.
- **Examples:**
  - `Salai Lian Luai` $\leftrightarrow$ `Salai Liang Lway`
  - `Mai Par Par`
  - `Thang Bik`

---

### 🕊️ 6. Mon (မွန်)
- **Structure:** Historical Mon prefixes honoring heritage, wisdom, and royal bloodlines.
- **Prefixes:**
  - Male: `Nai` (နိုင်), `Min` (မင်း).
  - Female: `Mi` (မိ), `Mi Kon` (မိကွန်).
- **Core Syllables:**
  - `Htaw` (Gold) $\leftrightarrow$ `Htaw`, `Taw`, `Htawr`.
  - `Sorn` (Elephant/Precious) $\leftrightarrow$ `Sorn`, `Son`, `Saung`.
  - `Chan` (Moon/Peace) $\leftrightarrow$ `Chan`, `Chann`.
  - `Tala` (High-born) $\leftrightarrow$ `Tala`, `Talar`.
- **Examples:**
  - `Nai Htaw Sorn` $\leftrightarrow$ `Nai Taw Son`
  - `Mi Kon Chan`
  - `Min Nyi Nyi`

---

### ☀️ 7. Kayah (ကယား)
- **Structure:** Traditional prefixes followed by distinct clan or birth order syllables.
- **Prefixes:**
  - Male: `Khu` (ခူး), `Reh` (ရေး), `Bu` (ဘူး).
  - Female: `Maw` (မော်), `Meh` (မဲ).
- **Core Syllables:**
  - `Reh` $\leftrightarrow$ `Reh`, `Ray`, `Rae`.
  - `Meh` $\leftrightarrow$ `Meh`, `May`, `Mae`.
  - `Plah` (Arrow/Warrior) $\leftrightarrow$ `Plah`, `Pla`.
  - `Nye` (Gentle) $\leftrightarrow$ `Nye`, `Nyeh`.
- **Examples:**
  - `Khu Reh` $\leftrightarrow$ `Khu Ray`
  - `Maw Meh` $\leftrightarrow$ `Maw May`
  - `Khu Oo Reh`

---

### 🌊 8. Rakhine (ရခိုင်)
- **Structure:** Shares similarities with Bamar naming but features distinct Rakhine phonetic spellings, regional honorifics, and traditional prefixes.
- **Markers & Syllables:**
  - `Khaing` / `Khine` (ခိုင် - Firm/Loyal).
  - `Chay` (ချေ - Affectionate diminutive / Youngest).
  - `San` (စံ - Exemplary).
  - `Oo` (ဦး - First/Supreme).
  - `Zan` (ဇံ - Spirit).
- **Examples:**
  - `Khaing San Aung` $\leftrightarrow$ `Khine San Aung`
  - `Oo Hla Saw`
  - `Maung Phyu Chay`

---

## 3. Systematic Romanization Mapping Rules

| Category | Typical Romanized Spellings | Canonical Phonetic Code | Typical Myanmar Words |
|---|---|---|---|
| **Consonant: KY/GY** | `ky`, `gy`, `kl`, `kj` | `K` | ကျော် (Kyaw), ဂျော် (Gyaw) |
| **Consonant: SW/ZW** | `sw`, `zw`, `thw` | `SW` | စွာ (Swar), ဇွာ (Zwar) |
| **Consonant: P/PH** | `ph`, `p`, `hp` | `P` | ဖြိုး (Phyo), ပိုး (Poe), ဖုန် (Hpung) |
| **Consonant: S/TH/HT** | `th`, `s`, `ht`, `hs` | `S` | သန့် (Thant), စန်း (San), ထွန်း (Htun), ဆိုင်း (Hseng) |
| **Consonant: NY/GN** | `ny`, `gn`, `nh` | `NY` | ညို (Nyo), ညာဏ် (Nyan) |
| **Consonant: HL/L** | `hl`, `l`, `lh` | `L` | လှ (Hla), လင်း (Lin) |
| **Consonant: HM/M** | `hm`, `m`, `mh` | `M` | မှူး (Hmu), မြင့် (Myint) |
| **Consonant: HN/N** | `hn`, `n`, `nh` | `N` | နှင်း (Hnin), နိုင် (Naing) |
| **Vowel: AY/EI/AI** | `aye`, `ei`, `ai`, `ay`, `ae` | `AY` | အေး (Aye), အိ (Ei), ခိုင် (Khaing/Khine) |
| **Vowel: U/OO** | `oo`, `u`, `uu`, `ou` | `U` | ဦး (U), ထူး (Htoo/Htu), ဆု (Su) |
| **Vowel: AW/OR/AR** | `aw`, `or`, `ar`, `au` | `AW` | အော် (Aw), ဇော် (Zaw/Zar) |
| **Vowel: WE/WAY** | `oe`, `we`, `way`, `wai`, `uai` | `WE` | ဝေ (Wai/Way), လွင် (Lwin), လျှမ်း (Lway/Luai) |
| **Final: ING/IN** | `int`, `inn`, `in`, `ing` | `IN` | မြင့် (Myint), ဝင်း (Win), လင်း (Lin) |
| **Final: ONG/AUNG**| `aung`, `awng`, `oung`, `ong` | `ONG` | အောင် (Aung), မောင် (Maung), နောင် (Naung/Noung) |
