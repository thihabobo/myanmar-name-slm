"""
Intake Form Parser for RapidOCR results.
Extracts structured patient demographics, NRC, phone, gender, and clinical terms.
Supports Canonical A4 Template matching with Optical Mark Recognition (OMR) on Checkboxes
and targeted Zone-based text extraction.
"""

import re
from typing import List, Dict, Any, Optional
import numpy as np

ALLERGEN_PRESETS = [
    "Penicillin", "Sulfa", "Paracetamol", "Aspirin", "NSAIDs", "Amoxicillin",
    "Ciprofloxacin", "Ceftriaxone", "Seafood", "Peanut", "Egg", "Contrast Media"
]

CONDITION_PRESETS = [
    "Hypertension", "Diabetes", "Asthma", "IHD", "Heart Disease", "CKD", "Kidney Disease",
    "Hepatitis B", "Hepatitis C", "Stroke", "Epilepsy", "Thyroid", "Peptic Ulcer", "TB", "Tuberculosis"
]

MM_DIGITS = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉']
EN_DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

# Canonical A4 Checkbox Coordinates (center_x, center_y, box_size)
ALLERGEN_CHECKBOXES = {
    "NKDA": (65, 726, 18),
    "Penicillin": (65, 764, 16),
    "Sulfa": (335, 764, 16),
    "Paracetamol": (65, 816, 16),
    "Aspirin": (335, 816, 16),
    "NSAIDs": (335, 816, 16),
    "Amoxicillin": (65, 868, 16),
    "Ciprofloxacin": (335, 868, 16),
    "Ceftriaxone": (65, 920, 16),
    "Seafood": (335, 920, 16),
    "Peanut": (65, 972, 16),
    "Egg": (335, 972, 16),
    "Contrast Media": (65, 1024, 16),
}

CONDITION_CHECKBOXES = {
    "No Chronic Illness": (645, 726, 18),
    "Hypertension": (645, 764, 16),
    "Diabetes": (915, 764, 16),
    "Asthma": (645, 816, 16),
    "IHD": (915, 816, 16),
    "CKD": (645, 868, 16),
    "Hepatitis B": (915, 868, 16),
    "Hepatitis C": (915, 868, 16),
    "Stroke": (645, 920, 16),
    "Epilepsy": (915, 920, 16),
    "Thyroid": (645, 972, 16),
    "Peptic Ulcer": (915, 972, 16),
    "TB": (645, 1024, 16),
}

DEMO_CHECKBOXES = {
    "citizen": (195, 498, 16),
    "foreigner": (345, 498, 16),
    "gender_male": (882, 484, 16),
    "gender_female": (982, 484, 16),
    "bg_a": (195, 542, 16),
    "bg_b": (260, 542, 16),
    "bg_ab": (325, 542, 16),
    "bg_o": (395, 542, 16),
    "bg_rh_pos": (525, 542, 16),
    "bg_rh_neg": (650, 542, 16),
}


def to_en_digits(text: str) -> str:
    if not text:
        return ""
    for mm, en in zip(MM_DIGITS, EN_DIGITS):
        text = text.replace(mm, en)
    return text


class IntakeFormParser:
    @staticmethod
    def parse_ocr_results(ocr_items: List[Any], img: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Parses OCR items and image features.
        If canonical warped image is provided, applies high-precision Zone-based
        extraction and Optical Mark Recognition (OMR) on Checkboxes.
        """
        lines = []
        for item in ocr_items:
            if len(item) >= 2:
                text = str(item[1]).strip()
                if text:
                    lines.append(text)

        full_text = "\n".join(lines)
        normalized_full_text = to_en_digits(full_text)

        data = {
            "citizenship": "citizen",
            "nationality": "Myanmar",
            "patient_name": "",
            "patient_name_mm": "",
            "father_name": "",
            "father_name_mm": "",
            "nrc": "",
            "passport": "",
            "phone": "",
            "emergency_contact": "",
            "gender": "M",
            "age": None,
            "age_unit": "Y",
            "dob": None,
            "blood_type": "",
            "address": "",
            "allergies": [],
            "conditions": [],
            "previous_surgeries": "",
            "daily_medications": "",
        }

        # Step 1: Optical Mark Recognition (OMR) on Checkboxes if image available
        if img is not None:
            IntakeFormParser._extract_omr_checkboxes(img, data)

        # Step 2: Zone-Based Text Extraction from OCR Bounding Boxes
        if ocr_items and img is not None:
            IntakeFormParser._extract_zone_texts(ocr_items, img.shape[1], img.shape[0], data)

        # Step 3: Fallback line cues and regex parsing for any missing fields
        IntakeFormParser._extract_line_fallbacks(lines, normalized_full_text, full_text, data)

        return data

    @staticmethod
    def _extract_omr_checkboxes(img: np.ndarray, data: Dict[str, Any]) -> None:
        """
        Extracts checkbox states using Optical Mark Recognition (OMR).
        """
        import cv2
        from document_scanner import DocumentScanner

        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        h, w = gray.shape[:2]
        scale_x = w / 1240.0
        scale_y = h / 1754.0

        # 1. Allergies & NKDA
        nkda_coords = ALLERGEN_CHECKBOXES["NKDA"]
        is_nkda = DocumentScanner.is_checkbox_checked(
            gray, int(nkda_coords[0] * scale_x), int(nkda_coords[1] * scale_y), int(nkda_coords[2] * scale_x), threshold=0.075
        )

        detected_allergies = []
        if not is_nkda:
            for allergen, (cx, cy, sz) in ALLERGEN_CHECKBOXES.items():
                if allergen == "NKDA":
                    continue
                if DocumentScanner.is_checkbox_checked(gray, int(cx * scale_x), int(cy * scale_y), int(sz * scale_x), threshold=0.070):
                    if allergen not in detected_allergies:
                        detected_allergies.append(allergen)

        data["allergies"] = detected_allergies

        # 2. Conditions & No Chronic Illness
        no_cond_coords = CONDITION_CHECKBOXES["No Chronic Illness"]
        is_no_cond = DocumentScanner.is_checkbox_checked(
            gray, int(no_cond_coords[0] * scale_x), int(no_cond_coords[1] * scale_y), int(no_cond_coords[2] * scale_x), threshold=0.075
        )

        detected_conditions = []
        if not is_no_cond:
            for cond, (cx, cy, sz) in CONDITION_CHECKBOXES.items():
                if cond == "No Chronic Illness":
                    continue
                if DocumentScanner.is_checkbox_checked(gray, int(cx * scale_x), int(cy * scale_y), int(sz * scale_x), threshold=0.070):
                    if cond not in detected_conditions:
                        detected_conditions.append(cond)

        data["conditions"] = detected_conditions

        # 3. Demographics: Citizenship
        cit_coords = DEMO_CHECKBOXES["citizen"]
        for_coords = DEMO_CHECKBOXES["foreigner"]
        is_for = DocumentScanner.is_checkbox_checked(gray, int(for_coords[0] * scale_x), int(for_coords[1] * scale_y), int(for_coords[2] * scale_x), threshold=0.08)
        if is_for:
            data["citizenship"] = "foreigner"

        # 4. Demographics: Gender
        male_coords = DEMO_CHECKBOXES["gender_male"]
        female_coords = DEMO_CHECKBOXES["gender_female"]
        is_female = DocumentScanner.is_checkbox_checked(gray, int(female_coords[0] * scale_x), int(female_coords[1] * scale_y), int(female_coords[2] * scale_x), threshold=0.075)
        is_male = DocumentScanner.is_checkbox_checked(gray, int(male_coords[0] * scale_x), int(male_coords[1] * scale_y), int(male_coords[2] * scale_x), threshold=0.075)
        if is_female and not is_male:
            data["gender"] = "F"
        elif is_male:
            data["gender"] = "M"

        # 5. Blood Group
        bg_rh_neg = DocumentScanner.is_checkbox_checked(gray, int(DEMO_CHECKBOXES["bg_rh_neg"][0] * scale_x), int(DEMO_CHECKBOXES["bg_rh_neg"][1] * scale_y), 16, threshold=0.075)
        sign = "-" if bg_rh_neg else "+"

        for bg_type in ["bg_ab", "bg_a", "bg_b", "bg_o"]:
            cx, cy, sz = DEMO_CHECKBOXES[bg_type]
            if DocumentScanner.is_checkbox_checked(gray, int(cx * scale_x), int(cy * scale_y), int(sz * scale_x), threshold=0.075):
                clean_type = bg_type.replace("bg_", "").upper()
                data["blood_type"] = clean_type + sign
                break

    @staticmethod
    def _extract_zone_texts(ocr_items: List[Any], img_w: int, img_h: int, data: Dict[str, Any]) -> None:
        """
        Maps RapidOCR bounding boxes to precise Canonical A4 form field zones.
        Coordinates are normalized to 1240 x 1754 canonical space.
        """
        scale_x = img_w / 1240.0
        scale_y = img_h / 1754.0

        for item in ocr_items:
            if len(item) < 2:
                continue
            box, text = item[0], str(item[1]).strip()
            if not text:
                continue

            try:
                # Center point normalized to 1240 x 1754
                cx = ((box[0][0] + box[2][0]) / 2.0) / scale_x
                cy = ((box[0][1] + box[2][1]) / 2.0) / scale_y
            except Exception:
                continue

            # Skip header branding banner
            if cy < 220:
                continue

            # Row 1: English Name: X: 190-580, Y: 250-315
            if 250 <= cy <= 315 and 190 <= cx <= 580:
                clean = re.sub(r'^(?:Full\s*Name|Patient\s*Name|Name|English)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                clean = re.sub(r'[_\.\-]+$', '', clean).strip()
                if clean and not re.match(r'^(?:Full|Name|English|\(?English\)?)$', clean, re.IGNORECASE):
                    if not data["patient_name"]:
                        data["patient_name"] = clean

            # Row 1: Myanmar Name: X: 780-1200, Y: 250-315
            elif 250 <= cy <= 315 and 780 <= cx <= 1200:
                clean = re.sub(r'^(?:လူနာအမည်|အမည်|မြန်မာ)\s*[:=]?\s*', '', text).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                clean = re.sub(r'[_\.\-]+$', '', clean).strip()
                if clean and re.search(r'[\u1000-\u1049]', clean):
                    if not data["patient_name_mm"]:
                        data["patient_name_mm"] = clean

            # Row 2: Father Name (English): X: 190-580, Y: 315-370
            elif 315 < cy <= 370 and 190 <= cx <= 580:
                clean = re.sub(r'^(?:Father(?:\'s)?\s*Name|Father|English)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                clean = re.sub(r'[_\.\-]+$', '', clean).strip()
                if clean and not re.match(r'^(?:Father|Name|English|\(?English\)?)$', clean, re.IGNORECASE):
                    if not data["father_name"]:
                        data["father_name"] = clean

            # Row 2: Father Name (Myanmar): X: 780-1200, Y: 315-370
            elif 315 < cy <= 370 and 780 <= cx <= 1200:
                clean = re.sub(r'^(?:အဘအမည်|အဘ|မြန်မာ)\s*[:=]?\s*', '', text).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                clean = re.sub(r'[_\.\-]+$', '', clean).strip()
                if clean and re.search(r'[\u1000-\u1049]', clean):
                    if not data["father_name_mm"]:
                        data["father_name_mm"] = clean

            # Row 3: Primary Phone: X: 190-580, Y: 370-425
            elif 370 < cy <= 425 and 190 <= cx <= 580:
                phone_num = to_en_digits(text)
                pm = re.search(r'(?:09|9)\d{7,10}', re.sub(r'[-\s]', '', phone_num))
                if pm:
                    p = pm.group(0)
                    if not p.startswith('09'):
                        p = '0' + p
                    data["phone"] = p

            # Row 3: Emergency Contact: X: 780-1200, Y: 370-425
            elif 370 < cy <= 425 and 780 <= cx <= 1200:
                phone_num = to_en_digits(text)
                pm = re.search(r'(?:09|9)\d{7,10}', re.sub(r'[-\s]', '', phone_num))
                if pm:
                    p = pm.group(0)
                    if not p.startswith('09'):
                        p = '0' + p
                    data["emergency_contact"] = p
                elif not data["emergency_contact"]:
                    clean = re.sub(r'^(?:Emergency\s*Contact|Emergency)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                    clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                    if clean:
                        data["emergency_contact"] = clean

            # Row 4: Date of Birth: X: 190-580, Y: 425-480
            elif 425 < cy <= 480 and 190 <= cx <= 580:
                dob_clean = to_en_digits(text)
                dm = re.search(r'(\d{1,2})\s*[\/\-]\s*(\d{1,2})\s*[\/\-]\s*(\d{4})', dob_clean)
                if dm:
                    d, m, y = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
                    if 1 <= d <= 31 and 1 <= m <= 12 and 1920 <= y <= 2026:
                        data["dob"] = f"{y:04d}-{m:02d}-{d:02d}"

            # Row 4: Age: X: 780-950, Y: 425-480
            elif 425 < cy <= 480 and 780 <= cx <= 950:
                age_clean = to_en_digits(text)
                am = re.search(r'(\d{1,3})\s*(?:နှစ်|Yrs|Years)?', age_clean, re.IGNORECASE)
                if am and not data["age"]:
                    val = int(am.group(1))
                    if 0 <= val <= 130:
                        data["age"] = val

            # Row 5: NRC / Passport: X: 780-1200, Y: 480-535
            elif 480 < cy <= 535 and 780 <= cx <= 1200:
                nrc_clean = to_en_digits(text)
                nm = re.search(
                    r'\b(\d{1,2}\s*/\s*[A-Za-z\u1000-\u102A]+\s*\(?(?:N|E|P|T|NAING|နိုင်|ဧည့်|ပြု|သာ|ရဟန်း)?\)?\s*\d{5,6})\b',
                    nrc_clean,
                    re.IGNORECASE
                )
                if nm:
                    data["nrc"] = re.sub(r'\s+', '', nm.group(1)).upper()

            # Row 7: Detail Address: X: 190-1200, Y: 585-665
            elif 585 < cy <= 665 and 190 <= cx <= 1200:
                clean = re.sub(r'^(?:Detail\s*Address|Address|နေရပ်လိပ်စာ)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                if clean and not re.search(r'^(?:အမှတ်|လမ်း|ရပ်ကွက်|မြို့နယ်|Detail|Address)', clean, re.IGNORECASE):
                    if data["address"]:
                        data["address"] += " " + clean
                    else:
                        data["address"] = clean

            # Other Allergies fill-line: Y: 1080-1160, X: 240-620
            elif 1080 <= cy <= 1160 and 240 <= cx <= 620:
                clean = re.sub(r'^(?:အခြား\s*မတည့်သည့်\s*အရာများ|Other)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                if clean and len(clean) > 2:
                    if clean not in data["allergies"]:
                        data["allergies"].append(clean)

            # Previous Surgery: Y: 1065-1120, X: 780-1200
            elif 1065 <= cy <= 1120 and 780 <= cx <= 1200:
                clean = re.sub(r'^(?:ခွဲစိတ်ဖူးသည့်\s*ရာဇဝင်|Surgery)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                if clean and len(clean) > 2:
                    data["previous_surgeries"] = clean

            # Medications: Y: 1120-1175, X: 780-1200
            elif 1120 <= cy <= 1175 and 780 <= cx <= 1200:
                clean = re.sub(r'^(?:လက်ရှိသောက်ဆေး|Medications)\s*[:=]?\s*', '', text, flags=re.IGNORECASE).strip()
                clean = re.sub(r'^[_\.\-:\(\)]+', '', clean).strip()
                if clean and len(clean) > 2:
                    data["daily_medications"] = clean

    @staticmethod
    def _extract_line_fallbacks(lines: List[str], normalized_full_text: str, full_text: str, data: Dict[str, Any]) -> None:
        """
        Fallback extraction for non-template scans or fields missed by zone matching.
        """
        HOSPITAL_PHONES = {"09259499720", "09259499727", "259499720", "259499727"}

        # Phone fallback
        if not data["phone"]:
            phones = re.findall(r'(?:09|9)[-\s]?\d{2,3}[-\s]?\d{3}[-\s]?\d{3,4}', normalized_full_text)
            for p in phones:
                clean = re.sub(r'[-\s]', '', p)
                if not clean.startswith('09'):
                    clean = '0' + clean
                if clean not in HOSPITAL_PHONES:
                    data["phone"] = clean
                    break

        # NRC fallback
        if not data["nrc"]:
            nrc_match = re.search(
                r'\b(\d{1,2}\s*/\s*[A-Za-z\u1000-\u102A]+\s*\(?(?:N|E|P|T|NAING|နိုင်|ဧည့်|ပြု|သာ|ရဟန်း)?\)?\s*\d{5,6})\b',
                normalized_full_text,
                re.IGNORECASE
            )
            if nrc_match:
                data["nrc"] = re.sub(r'\s+', '', nrc_match.group(1)).upper()

        # Blood group fallback
        if not data["blood_type"]:
            bg_sign = "+"
            if re.search(r'(?:\[[xXvV]\]|[✔✓☑])\s*Rh\s*Negative', full_text, re.IGNORECASE):
                bg_sign = "-"
            elif re.search(r'(?:\[[xXvV]\]|[✔✓☑]|rh)\s*(?:Rh\s*)?Positive', full_text, re.IGNORECASE):
                bg_sign = "+"

            if re.search(r'(?:\[[xXvV]\]|[✔✓☑]|α)\s*B\b', full_text) or re.search(r'\bB\s*(?:\[[xXvV]\]|[✔✓☑])', full_text):
                data["blood_type"] = "B" + bg_sign
            elif re.search(r'(?:\[[xXvV]\]|[✔✓☑]|α)\s*AB\b', full_text):
                data["blood_type"] = "AB" + bg_sign
            elif re.search(r'(?:\[[xXvV]\]|[✔✓☑]|α)\s*A\b', full_text):
                data["blood_type"] = "A" + bg_sign
            elif re.search(r'(?:\[[xXvV]\]|[✔✓☑]|α)\s*O\b', full_text):
                data["blood_type"] = "O" + bg_sign

        # Name fallbacks
        if not data["patient_name"]:
            for i, line in enumerate(lines):
                if re.search(r'(?:Full\s*Name|Patient\s*Name|Name\s*\(English\))\s*[:=]?\s*(.*)', line, re.IGNORECASE):
                    val = re.sub(r'^(?:Full\s*Name|Patient\s*Name|Name\s*\(English\)|English)\s*[:=]?\s*', '', line, flags=re.IGNORECASE).strip()
                    val = re.sub(r'^[_\.\-:\(\)]+', '', val).strip()
                    if val and not re.match(r'^(?:English|\(?English\)?|Name):?$', val, re.IGNORECASE):
                        data["patient_name"] = val
                        break

        if not data["patient_name_mm"]:
            for line in lines:
                if re.search(r'(?:လူနာအမည်|အမည်\s*\(မြန်မာ\))\s*[:=]?\s*(.*)', line):
                    val = re.sub(r'^(?:လူနာအမည်|အမည်\s*\(မြန်မာ\)|မြန်မာ)\s*[:=]?\s*', '', line).strip()
                    val = re.sub(r'^[_\.\-:\(\)]+', '', val).strip()
                    if val and re.search(r'[\u1000-\u1049]', val) and not re.match(r'^(?:မြန်မာ|\(?မြန်မာ\)?|အမည်):?$', val):
                        data["patient_name_mm"] = val
                        break

        if not data["father_name"]:
            for line in lines:
                if re.search(r'(?:Father(?:\'s)?\s*Name)\s*[:=]?\s*(.*)', line, re.IGNORECASE):
                    val = re.sub(r'^(?:Father(?:\'s)?\s*Name|English)\s*[:=]?\s*', '', line, flags=re.IGNORECASE).strip()
                    val = re.sub(r'^[_\.\-:\(\)]+', '', val).strip()
                    if val and not re.match(r'^(?:English|\(?English\)?|Father):?$', val, re.IGNORECASE):
                        data["father_name"] = val
                        break

        if not data["father_name_mm"]:
            for line in lines:
                if re.search(r'(?:အဘအမည်)\s*[:=]?\s*(.*)', line):
                    val = re.sub(r'^(?:အဘအမည်|မြန်မာ)\s*[:=]?\s*', '', line).strip()
                    val = re.sub(r'^[_\.\-:\(\)]+', '', val).strip()
                    if val and re.search(r'[\u1000-\u1049]', val):
                        data["father_name_mm"] = val
                        break
