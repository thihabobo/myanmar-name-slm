"""
FastAPI Microservice for Myanmar & Ethnic Name Matching & Semantic Search.
Provides simple, standard JSON endpoints for integration into Laravel, POS, and Mobile apps.
"""

import os
import sys

# Ensure src directory is in sys.path
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from typing import List, Optional, Any
import base64
import cv2
import numpy as np
from fastapi import FastAPI, Query
from pydantic import BaseModel

from matcher import MyanmarNameMatcher
from phonetic_normalizer import BurglishPhoneticNormalizer
from intake_parser import IntakeFormParser
from document_scanner import DocumentScanner
from rapidocr_onnxruntime import RapidOCR

app = FastAPI(
    title="Myanmar & Ethnic Name Semantic Matcher & Intake OCR API",
    description="Intelligent phonetic normalizer, semantic embedding matcher, and local OCR scanner.",
    version="1.2.0",
)

matcher = MyanmarNameMatcher()
ocr_engine = RapidOCR(det_box_thresh=0.35, det_thresh=0.25, text_score=0.35)


class MatchRequest(BaseModel):
    name1: str
    name2: str


class CandidateSearchRequest(BaseModel):
    query: str
    candidates: List[str]
    threshold: float = 0.70
    limit: int = 10


class OcrIntakeRequest(BaseModel):
    image_base64: str
    mime_type: Optional[str] = "image/jpeg"
    auto_deskew: Optional[bool] = True
    auto_enhance: Optional[bool] = True
    corners: Optional[List[Any]] = None


class AutoScanRequest(BaseModel):
    image_base64: str
    auto_deskew: Optional[bool] = True
    auto_enhance: Optional[bool] = True
    corners: Optional[List[Any]] = None


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "myanmar-name-matcher-and-ocr",
        "has_neural": bool(matcher.onnx_session or matcher.torch_model),
        "has_ocr": True,
        "ocr_engine": "RapidOCR ONNX",
    }


@app.post("/auto-scan-document")
def auto_scan_document(req: AutoScanRequest):
    """
    Google Pixel / Camera-style Auto Document Scan & Deskewer.
    Detects document corners, corrects perspective tilt, and removes shadows.
    """
    try:
        raw_b64 = req.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"success": False, "message": "Failed to decode image buffer"}

        result = DocumentScanner.process_auto_scan(
            img,
            auto_deskew=bool(req.auto_deskew),
            auto_enhance=bool(req.auto_enhance),
            client_corners=req.corners
        )

        _, deskewed_buf = cv2.imencode(".jpg", result["deskewed_image"], [cv2.IMWRITE_JPEG_QUALITY, 88])
        deskewed_b64 = "data:image/jpeg;base64," + base64.b64encode(deskewed_buf).decode("utf-8")

        _, enhanced_buf = cv2.imencode(".jpg", result["enhanced_image"], [cv2.IMWRITE_JPEG_QUALITY, 88])
        enhanced_b64 = "data:image/jpeg;base64," + base64.b64encode(enhanced_buf).decode("utf-8")

        return {
            "success": True,
            "has_contour": result["has_contour"],
            "corners": result["corners"],
            "original_dims": [result["original_width"], result["original_height"]],
            "deskewed_dims": [result.get("deskewed_width"), result.get("deskewed_height")],
            "deskewed_image": deskewed_b64,
            "enhanced_image": enhanced_b64,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Auto-scan error: {str(e)}"
        }


@app.post("/ocr-intake")
def ocr_intake(req: OcrIntakeRequest):
    try:
        raw_b64 = req.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        was_deskewed = False

        if img is not None:
            # 1. Automatic Document Detection & Perspective Deskewing to Canonical A4
            if req.auto_deskew:
                corners = DocumentScanner.resolve_corners(img, req.corners)
                if corners is not None:
                    img = DocumentScanner.four_point_transform(
                        img,
                        corners,
                        target_width=DocumentScanner.CANONICAL_A4_WIDTH,
                        target_height=DocumentScanner.CANONICAL_A4_HEIGHT
                    )
                    was_deskewed = True

            # 2. Document Shadow Removal & Clean Filter
            if req.auto_enhance:
                img = DocumentScanner.enhance_document(img)

            ocr_results, _ = ocr_engine(img)
            parsed = IntakeFormParser.parse_ocr_results(ocr_results or [], img=img)
        else:
            ocr_results, _ = ocr_engine(img_bytes)
            parsed = IntakeFormParser.parse_ocr_results(ocr_results or [])

        preview_b64 = None
        if img is not None:
            try:
                success, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if success:
                    preview_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
            except Exception:
                pass

        return {
            "success": True,
            "engine": "rapidocr_offline",
            "was_deskewed": was_deskewed,
            "scanned_image_base64": preview_b64,
            "message": "Scanned successfully via Local RapidOCR Engine." + (" (Auto-Deskewed)" if was_deskewed else ""),
            "data": parsed,
            "detected_lines_count": len(ocr_results or []),
        }
    except Exception as e:
        return {
            "success": False,
            "engine": "rapidocr_offline",
            "message": f"OCR extraction error: {str(e)}",
            "data": {},
        }



@app.get("/phonetic-key")
def get_phonetic_key(name: str = Query(..., description="Name in English/Burglish")):
    key = BurglishPhoneticNormalizer.phonetic_key(name)
    tokens = BurglishPhoneticNormalizer.phonetic_tokens(name)
    return {
        "original_name": name,
        "phonetic_key": key,
        "tokens": tokens,
    }


@app.post("/match")
def match_two_names(req: MatchRequest):
    result = matcher.match(req.name1, req.name2)
    return {
        "name1": req.name1,
        "name2": req.name2,
        **result,
    }


@app.post("/search-candidates")
def search_candidates(req: CandidateSearchRequest):
    results = []
    for cand in req.candidates:
        res = matcher.match(req.query, cand)
        if res["score"] >= req.threshold:
            results.append({
                "candidate": cand,
                "score": res["score"],
                "is_duplicate": res["is_duplicate"],
                "confidence": res["confidence"],
                "match_reasons": res["match_reasons"],
            })

    # Sort by descending similarity score
    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": req.query,
        "total_matched": len(results),
        "results": results[: req.limit],
    }


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("SLM_PORT", 8005))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)

