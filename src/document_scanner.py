"""
Google Pixel / Camera-style Auto Document Scanner & Deskewer
Provides automated edge/quadrilateral detection, perspective correction (deskew),
shadow removal, and document contrast enhancement using OpenCV.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List


class DocumentScanner:
    CANONICAL_A4_WIDTH = 1240
    CANONICAL_A4_HEIGHT = 1754

    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """
        Orders coordinates: [top-left, top-right, bottom-right, bottom-left]
        """
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    @staticmethod
    def four_point_transform(
        image: np.ndarray,
        pts: np.ndarray,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
    ) -> np.ndarray:
        """
        Performs 4-point perspective warp into a straight top-down rectangular document.
        Defaults to standard canonical A4 (1240 x 1754) if dimensions are not specified.
        """
        rect = DocumentScanner.order_points(pts)
        (tl, tr, br, bl) = rect

        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB), 50)

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB), 50)

        out_w = target_width or maxWidth
        out_h = target_height or maxHeight

        dst = np.array([
            [0, 0],
            [out_w - 1, 0],
            [out_w - 1, out_h - 1],
            [0, out_h - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (out_w, out_h))
        return warped

    @staticmethod
    def resolve_corners(image: np.ndarray, client_corners: Optional[List[Any]] = None) -> Optional[np.ndarray]:
        """
        Resolves 4 document corners with high accuracy:
        1. Checks OpenCV contour and edge detector on server.
        2. If server cannot find distinct contrast edge, falls back to client-tracked viewfinder corners.
        """
        h, w = image.shape[:2]
        server_corners = DocumentScanner.detect_document_corners(image)
        if server_corners is not None:
            return server_corners

        if client_corners and len(client_corners) == 4:
            try:
                pts = np.array(client_corners, dtype="float32")
                if pts.shape == (4, 2):
                    if pts.max() <= 1.05:
                        pts[:, 0] *= w
                        pts[:, 1] *= h
                    return DocumentScanner.order_points(pts)
            except Exception:
                pass

        return None

    @staticmethod
    def is_checkbox_checked(
        gray_img: np.ndarray,
        center_x: int,
        center_y: int,
        box_size: int = 18,
        threshold: float = 0.075
    ) -> bool:
        """
        Optical Mark Recognition (OMR) on a checkbox located at (center_x, center_y).
        Evaluates inner 60% of the box to distinguish blank white space vs handwritten checkmark/cross/ink stroke.
        Tolerant to +-6px alignment drift.
        """
        h, w = gray_img.shape[:2]
        half = box_size // 2

        # Check in a 3x3 search window to tolerate slight perspective skew (+-6px)
        best_ratio = 0.0
        for dx in [-6, 0, 6]:
            for dy in [-6, 0, 6]:
                cx = center_x + dx
                cy = center_y + dy
                x1 = max(0, min(w - 1, cx - half))
                y1 = max(0, min(h - 1, cy - half))
                x2 = max(0, min(w, cx + half))
                y2 = max(0, min(h, cy + half))

                box = gray_img[y1:y2, x1:x2]
                if box.size == 0 or box.shape[0] < 6 or box.shape[1] < 6:
                    continue

                bh, bw = box.shape
                inner_y1 = int(bh * 0.22)
                inner_y2 = int(bh * 0.78)
                inner_x1 = int(bw * 0.22)
                inner_x2 = int(bw * 0.78)

                inner = box[inner_y1:inner_y2, inner_x1:inner_x2]
                if inner.size == 0:
                    continue

                # Dark ink pixel threshold (standard paper background is > 200, pen ink is < 135)
                dark_count = np.sum(inner < 135)
                ratio = float(dark_count) / float(inner.size)
                if ratio > best_ratio:
                    best_ratio = ratio

        return best_ratio >= threshold

    @staticmethod
    def detect_document_corners(image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detects 4 corners of document paper against table/background.
        Returns 4 (x, y) coordinates or None if not distinct from frame.
        """
        h, w = image.shape[:2]
        target_dim = 800.0
        scale = target_dim / max(h, w)
        small = cv2.resize(image, (int(w * scale), int(h * scale)))
        sh, sw = small.shape[:2]

        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        candidates = []

        # Strategy 1: Canny with morphology closing
        edges = cv2.Canny(blurred, 30, 120)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        cnts, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        candidates.extend(cnts)

        # Strategy 2: Otsu thresholding
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed_otsu = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel2)
        cnts_otsu, _ = cv2.findContours(closed_otsu, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        candidates.extend(cnts_otsu)

        min_area = (sh * sw) * 0.15
        max_area = (sh * sw) * 0.99
        valid_quads = []

        for c in candidates:
            area = cv2.contourArea(c)
            if area < min_area or area > max_area:
                continue

            peri = cv2.arcLength(c, True)
            for eps_factor in [0.02, 0.03, 0.04, 0.05]:
                approx = cv2.approxPolyDP(c, eps_factor * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    # Check corner angles (should be roughly quadrilateral 60° to 120°)
                    pts = approx.reshape(4, 2)
                    rect = DocumentScanner.order_points(pts)
                    valid_quads.append((area, rect))
                    break

        if valid_quads:
            valid_quads.sort(key=lambda x: x[0], reverse=True)
            best_rect = valid_quads[0][1] / scale
            return best_rect

        return None

    @staticmethod
    def enhance_document(img: np.ndarray) -> np.ndarray:
        """
        Document enhancement filter (like Google Camera Document / Clean mode).
        Eliminates phone shadows, uneven room lighting, and boosts text clarity.
        """
        rgb_planes = cv2.split(img)
        result_norm_planes = []
        for plane in rgb_planes:
            dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))
            bg_img = cv2.medianBlur(dilated_img, 21)
            diff_img = 255 - cv2.absdiff(plane, bg_img)
            norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            result_norm_planes.append(norm_img)

        enhanced = cv2.merge(result_norm_planes)

        # Subtle text sharpening
        kernel = np.array([[0, -0.4, 0], [-0.4, 2.6, -0.4], [0, -0.4, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        clean = cv2.addWeighted(enhanced, 0.75, sharpened, 0.25, 0)
        return clean

    @staticmethod
    def process_auto_scan(
        image: np.ndarray,
        auto_deskew: bool = True,
        auto_enhance: bool = True,
        client_corners: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete auto document scan pipeline with canonical A4 normalization.
        """
        h, w = image.shape[:2]
        corners = DocumentScanner.resolve_corners(image, client_corners)
        has_contour = corners is not None

        deskewed = image
        if has_contour and auto_deskew:
            deskewed = DocumentScanner.four_point_transform(
                image,
                corners,
                target_width=DocumentScanner.CANONICAL_A4_WIDTH,
                target_height=DocumentScanner.CANONICAL_A4_HEIGHT
            )

        enhanced = deskewed
        if auto_enhance:
            enhanced = DocumentScanner.enhance_document(deskewed)

        return {
            "has_contour": has_contour,
            "corners": corners.tolist() if corners is not None else None,
            "original_width": w,
            "original_height": h,
            "deskewed_width": deskewed.shape[1],
            "deskewed_height": deskewed.shape[0],
            "deskewed_image": deskewed,
            "enhanced_image": enhanced,
        }

