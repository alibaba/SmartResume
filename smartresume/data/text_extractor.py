import logging
import math
import re
from statistics import median
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union, Tuple

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from smartresume.data.ocr_provider import ocr_provider_manager
from smartresume.data.pdf_checker import pdf_checker
from smartresume.utils.config import config


class TextExtractor:

    def __init__(self, init_ocr: bool = True):

        self.ocr = None

        if init_ocr:
            try:
                self.ocr = ocr_provider_manager

            except Exception:
                pass

    def extract_text(self, file_path: str) -> List[Dict[str, Any]]:

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = file_path.suffix.lower()

        try:
            if file_ext == ".pdf":
                return self._extract_from_pdf(str(file_path))
            elif file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                return self._extract_from_image(str(file_path))
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

        except Exception:
            raise

    @staticmethod
    def _native_line_bboxes(page_texts):

        rows = []
        for item in sorted(
            page_texts, key=lambda t: (t["bbox"][1] + t["bbox"][3]) / 2
        ):
            box = item["bbox"]
            cy = (box[1] + box[3]) / 2
            height = box[3] - box[1]
            if rows:
                row = rows[-1]
                median = sorted(b[3] - b[1] for b in row)[len(row) // 2]
                row_y = sum((b[1] + b[3]) / 2 for b in row) / len(row)
                if abs(cy - row_y) <= min(height, median) * 0.35:
                    row.append(box)
                    continue
            rows.append([box])
        masks = []
        for row in rows:
            segment = None
            for box in sorted(row, key=lambda b: b[0]):
                if segment is not None:
                    gap = box[0] - segment[2]
                    height = min(box[3] - box[1], segment[3] - segment[1])
                    if gap <= height * 1.5:
                        segment = [
                            min(segment[0], box[0]),
                            min(segment[1], box[1]),
                            max(segment[2], box[2]),
                            max(segment[3], box[3]),
                        ]
                        continue
                    masks.append(segment)
                segment = list(box)
            if segment is not None:
                masks.append(segment)
        return masks

    def extract_with_positions(
        self,
        pdf_path: str,
        extract_text: bool = True,
        extract_render_img: bool = True,
        include_regions: bool = False,
    ) -> Tuple[Any, ...]:

        if pdfplumber is None:
            raise ImportError(
                "PDFplumber is not installed; cannot process PDF files"
            )
        from smartresume.utils.config import config

        pages_data, images, image_regions, line_regions = [], [], [], []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[: config.processing.page_limit]:
                rendered = (
                    page.to_image(resolution=144)
                    if extract_render_img
                    else None
                )
                if rendered is not None:
                    image = np.array(rendered.original.convert("RGB"))
                    images.append(image)
                    x0, top, x1, bottom = rendered.bbox
                    sx = image.shape[1] / (x1 - x0)
                    sy = image.shape[0] / (bottom - top)
                else:
                    x0 = top = 0.0
                    sx = sy = 1.0

                def project(box):
                    if len(box) != 4 or not all(
                        math.isfinite(float(v)) for v in box
                    ):
                        return None
                    left, upper, right, lower = box
                    box = [
                        (left - x0) * sx,
                        (upper - top) * sy,
                        (right - x0) * sx,
                        (lower - top) * sy,
                    ]
                    if rendered is not None:
                        box = [
                            max(0.0, box[0]),
                            max(0.0, box[1]),
                            min(float(image.shape[1]), box[2]),
                            min(float(image.shape[0]), box[3]),
                        ]
                    return box if box[2] > box[0] and box[3] > box[1] else None

                page_texts, page_images = [], []
                if extract_text:
                    try:

                        for word in page.extract_words():
                            text = word["text"].strip()
                            if not text or not word.get("upright", True):
                                continue
                            box = project(
                                [
                                    word["x0"],
                                    word["top"],
                                    word["x1"],
                                    word["bottom"],
                                ]
                            )
                            if box is not None:
                                page_texts.append(
                                    {
                                        "text": text,
                                        "bbox": box,
                                        "confidence": 1.0,
                                        "source": "pdf_text",
                                    }
                                )

                        lines = [
                            v.strip()
                            for v in (page.extract_text() or "").splitlines()
                            if v.strip()
                        ]
                        if (
                            len(lines) >= 40
                            and sum(len(v) <= 2 for v in lines)
                            >= len(lines) * 0.55
                        ):
                            page_texts = []
                    except Exception as exc:
                        logging.getLogger(__name__).warning(
                            "Native PDF text unavailable on page %s; "
                            "using unmasked OCR: %s",
                            page.page_number,
                            exc,
                        )
                        page_texts = []
                try:
                    for item in page.images:
                        box = project(
                            [
                                item["x0"],
                                item["top"],
                                item["x1"],
                                item["bottom"],
                            ]
                        )
                        if box is not None:
                            page_images.append(box)
                except Exception as exc:
                    logging.getLogger(__name__).warning(
                        "PDF image metadata unavailable on page %s: %s",
                        page.page_number,
                        exc,
                    )
                pages_data.append(page_texts)
                image_regions.append(page_images)
                line_regions.append(self._native_line_bboxes(page_texts))

        if include_regions:
            return pages_data, images, image_regions, line_regions
        return pages_data, images

    def extract_from_pdf_string(
        self, pdf_path: str
    ) -> Union[str, Tuple[str, bool]]:

        if pdfplumber is None:
            raise ImportError(
                "PDFplumber is not installed; cannot process PDF files"
            )

        is_abnormal = False
        try:
            is_abnormal, _ = pdf_checker.check_pdf_abnormal(pdf_path)
        except Exception:
            pass

        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []

                from smartresume.utils.config import config

                total_pages = len(pdf.pages)
                max_pages = min(total_pages, config.processing.page_limit)

                for page_num in range(max_pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text.strip())

                text_result = "\n\n".join(text_parts)
                return (text_result, is_abnormal)

        except Exception:
            return ("", is_abnormal)

    def ocr_extract(self, image: np.ndarray) -> List[Any]:

        if not self.ocr:
            return []

        try:
            result = self.ocr.ocr_extract(image)
            return result if result else []

        except Exception:
            return []

    def resort_page_text_with_location(
        self, page_texts: List[Dict[str, Any]], page_num: int
    ) -> List[Dict[str, Any]]:

        if not page_texts:
            return []

        try:
            sorted_texts = sorted(
                page_texts,
                key=lambda x: (
                    x.get("bbox", [0, 0, 0, 0])[1],
                    x.get("bbox", [0, 0, 0, 0])[0],
                ),
            )

            _texts = list(sorted_texts)
            for i in range(len(_texts) - 1):
                bbox_i = _texts[i].get("bbox", [0, 0, 0, 0])
                bbox_next = _texts[i + 1].get("bbox", [0, 0, 0, 0])
                y_i, y_next = bbox_i[1], bbox_next[1]
                x_i, x_next = bbox_i[0], bbox_next[0]
                if abs(y_next - y_i) < 10 and x_next < x_i:
                    _texts[i], _texts[i + 1] = _texts[i + 1], _texts[i]
            return _texts
        except Exception:
            return page_texts

    def resort_page_text_with_center_location(
        self, page_texts: List[Dict[str, Any]], page_num: int
    ) -> List[Dict[str, Any]]:

        if not page_texts:
            return []

        try:
            for text in page_texts:
                bbox = text.get("bbox", [0, 0, 0, 0])
                text["_center_y"] = (bbox[1] + bbox[3]) / 2
                text["_center_x"] = (bbox[0] + bbox[2]) / 2
                text["_height"] = bbox[3] - bbox[1]

            texts_by_y = sorted(page_texts, key=lambda x: x["_center_y"])
            lines = []
            current_line = []

            for text in texts_by_y:
                if not current_line:
                    current_line.append(text)
                else:
                    heights = sorted(t["_height"] for t in current_line)
                    tolerance = max(heights[len(heights) // 2] * 0.5, 10)
                    line_y = sum(t["_center_y"] for t in current_line) / len(
                        current_line
                    )
                    if abs(text["_center_y"] - line_y) <= tolerance:
                        current_line.append(text)
                    else:
                        lines.append(current_line)
                        current_line = [text]
            if current_line:
                lines.append(current_line)

            sorted_texts = []
            for line in lines:
                line_sorted = sorted(line, key=lambda x: x["_center_x"])
                sorted_texts.extend(line_sorted)

            for text in sorted_texts:
                text.pop("_center_y", None)
                text.pop("_center_x", None)
                text.pop("_height", None)
            return sorted_texts
        except Exception:
            return page_texts

    @staticmethod
    def _text_density(box, items):
        area = (box["x2"] - box["x1"]) * (box["y2"] - box["y1"])
        if area <= 0:
            return 0.0
        return (
            sum(
                (t["bbox"][2] - t["bbox"][0]) * (t["bbox"][3] - t["bbox"][1])
                for t in items
            )
            / area
        )

    @staticmethod
    def _column_bands(layouts, page_texts):
        """Find separate columns with aligned body text and a heading."""
        section = re.compile(
            r"工作|教育|经历|技能|证书|培训|项目|联系|基本信息|个人信息|"
            r"experience|education|skills|contact|projects|training", re.I
        )
        candidates = []
        for idx, box in enumerate(layouts):
            items = [t for t in page_texts if t["layout_idx"] == idx]
            body = [t for t in items if len(t["text"].strip()) >= 4
                    and any(c.isalpha() for c in t["text"])]
            if len(body) < 3:
                continue
            height = median(t["bbox"][3] - t["bbox"][1] for t in body)
            left = median(t["bbox"][0] for t in body)
            aligned = [
                t for t in body if abs(t["bbox"][0] - left) <= 2 * height
            ]
            if (
                len(aligned) < 3
                or max(t["y_center"] for t in aligned)
                - min(t["y_center"] for t in aligned)
                < 3 * height
            ):
                continue
            titled = any(
                len(t["text"].strip()) <= 28 and section.search(t["text"])
                for t in items
            )
            sparse = TextExtractor._text_density(box, items) < 0.075
            candidates.append((idx, box, height, titled, sparse))

        bands = {}
        for i, (a, left, ha, title_a, sparse_a) in enumerate(candidates):
            for b, right, hb, title_b, sparse_b in candidates[i + 1:]:
                if not (title_a or title_b) or not (sparse_a or sparse_b):
                    continue
                gap = max(left["x1"] - right["x2"], right["x1"] - left["x2"])
                overlap = min(left["y2"], right["y2"]) - max(
                    left["y1"], right["y1"]
                )
                tallest = max(
                    left["y2"] - left["y1"], right["y2"] - right["y1"]
                )
                if gap >= 0.5 * min(ha, hb) and overlap >= 0.75 * tallest:
                    center = (
                        min(left["y1"], right["y1"])
                        + max(left["y2"], right["y2"])
                    ) / 2
                    bands[a] = bands[b] = center
        return bands

    def resort_page_text_with_layout(
        self,
        page_texts: List[Dict[str, Any]],
        page_num: int,
        layout_location: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not layout_location:
            return self.resort_page_text_with_center_location(
                page_texts, page_num
            )

        if not page_texts:
            return []

        try:
            for text in page_texts:
                tx1, ty1, tx2, ty2 = text.get("bbox", [0, 0, 0, 0])
                tx_center = (tx1 + tx2) / 2
                ty_center = (ty1 + ty2) / 2
                assigned = False

                for idx, layout in enumerate(layout_location):
                    lx1, ly1, lx2, ly2 = (
                        layout["x1"],
                        layout["y1"],
                        layout["x2"],
                        layout["y2"],
                    )
                    if lx1 <= tx_center <= lx2 and ly1 <= ty_center <= ly2:
                        text["x_center"] = tx_center
                        text["y_center"] = ty_center
                        text["lx_center"] = (lx1 + lx2) / 2
                        text["ly_center"] = (ly1 + ly2) / 2
                        text["layout_idx"] = idx
                        assigned = True
                        break

                if not assigned:
                    text["x_center"] = tx_center
                    text["y_center"] = ty_center
                    text["lx_center"] = tx_center
                    text["ly_center"] = ty_center
                    text["layout_idx"] = -1

            column_bands = (
                self._column_bands(layout_location, page_texts)
                if config.layout_detection.protect_sparse_columns else {}
            )
            for idx, layout in enumerate(layout_location):
                layout_texts = [
                    text
                    for text in page_texts
                    if text.get("layout_idx") == idx
                ]
                if not layout_texts:
                    continue

                if idx in column_bands:
                    for text in layout_texts:
                        text["ly_center"] = column_bands[idx]
                elif self._text_density(layout, layout_texts) < 0.075:
                    for text in layout_texts:
                        text["lx_center"] = text["x_center"]
                        text["ly_center"] = text["y_center"]
                        text["layout_idx"] = -1

            active_layouts = []
            for idx, layout in enumerate(layout_location):
                if any(text.get("layout_idx") == idx for text in page_texts):
                    active_layouts.append((idx, layout))

            unassigned_texts = [
                text for text in page_texts if text.get("layout_idx") == -1
            ]
            for text in unassigned_texts:
                tx_center = text["x_center"]
                ty_center = text["y_center"]
                min_distance = float("inf")
                closest_idx = -1
                closest_center = (tx_center, ty_center)

                for layout_idx, layout in active_layouts:
                    lx1, ly1, lx2, ly2 = (
                        layout["x1"],
                        layout["y1"],
                        layout["x2"],
                        layout["y2"],
                    )

                    dx = max(lx1 - tx_center, 0.0, tx_center - lx2)
                    dy = max(ly1 - ty_center, 0.0, ty_center - ly2)
                    dist = math.hypot(dx, dy)
                    if dist < min_distance:
                        min_distance = dist
                        closest_idx = layout_idx
                        closest_center = (
                            (lx1 + lx2) / 2,
                            column_bands.get(layout_idx, (ly1 + ly2) / 2),
                        )

                if closest_idx != -1:
                    text["layout_idx"] = closest_idx
                    text["lx_center"] = closest_center[0]
                    text["ly_center"] = closest_center[1]

            sorted_texts = sorted(
                page_texts,
                key=lambda x: (
                    x.get("ly_center", 0),
                    x.get("lx_center", 0),
                    x.get("y_center", 0),
                    x.get("x_center", 0),
                ),
            )

            heights = sorted(t["bbox"][3] - t["bbox"][1] for t in sorted_texts)
            row_tolerance = (
                max(heights[len(heights) // 2] * 0.5, 10) if heights else 10
            )
            swapped = True
            max_iterations = len(sorted_texts)
            iteration = 0
            while swapped and iteration < max_iterations:
                swapped = False
                iteration += 1
                for i in range(len(sorted_texts) - 1):
                    text_i = sorted_texts[i]
                    text_next = sorted_texts[i + 1]
                    y_center_i = text_i.get("y_center", 0)
                    y_center_next = text_next.get("y_center", 0)
                    x_center_i = text_i.get("x_center", 0)
                    x_center_next = text_next.get("x_center", 0)
                    if (
                        abs(y_center_next - y_center_i) < row_tolerance
                        and x_center_next < x_center_i
                        and (
                            text_i["layout_idx"] == text_next["layout_idx"]
                            or not (
                                {text_i["layout_idx"], text_next["layout_idx"]}
                                & column_bands.keys()
                            )
                        )
                    ):
                        sorted_texts[i], sorted_texts[i + 1] = (
                            sorted_texts[i + 1],
                            sorted_texts[i],
                        )
                        swapped = True

            return sorted_texts
        except Exception:
            return page_texts

    def _extract_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:

        if pdfplumber is None:
            raise ImportError(
                "PDFplumber is not installed; cannot process PDF files"
            )

        pages_data = []

        try:
            with pdfplumber.open(file_path) as pdf:
                from smartresume.utils.config import config

                total_pages = len(pdf.pages)
                max_pages = min(total_pages, config.processing.page_limit)

                for page_num in range(max_pages):
                    page = pdf.pages[page_num]

                    text = page.extract_text()

                    page_data = {
                        "page_number": page_num + 1,
                        "text": (
                            [{"text": text, "confidence": 1.0}]
                            if text and text.strip()
                            else []
                        ),
                        "source": "pdf_text",
                    }

                    if len((text or "").strip()) < 50 and self.ocr:
                        try:

                            img = page.to_image()
                            if img:
                                img_array = np.array(img.original)
                                ocr_result = self.ocr.ocr_extract(img_array)
                                if ocr_result:
                                    page_data = self.add_ocr_to_page_text(
                                        page_data, ocr_result
                                    )

                        except Exception:
                            pass

                    pages_data.append(page_data)

        except Exception:
            raise

        return pages_data

    def _extract_from_image(self, file_path: str) -> List[Dict[str, Any]]:

        if not self.ocr:
            raise RuntimeError(
                "OCR is not initialized; cannot process image files"
            )

        try:
            with open(file_path, "rb") as f:
                img_data = f.read()

            ocr_result = self.ocr.ocr(img_data)

            page_data = {"page_number": 1, "text": [], "source": "image_ocr"}

            if ocr_result:
                page_data = self.add_ocr_to_page_text(page_data, ocr_result)

            return [page_data]

        except Exception:
            raise

    def add_ocr_to_page_text(
        self, page_data: Dict[str, Any], ocr_result: List[Any]
    ) -> Dict[str, Any]:

        try:
            ocr_texts = []

            for item in ocr_result:
                try:
                    if (
                        len(item) >= 2
                        and isinstance(item[1], list)
                        and len(item[1]) >= 2
                    ):

                        xs = [p[0] for p in item[0][0]]
                        ys = [p[1] for p in item[0][0]]

                        x_min = min(xs)
                        x_max = max(xs)
                        y_min = min(ys)
                        y_max = max(ys)

                        bbox = [x_min, y_min, x_max, y_max]

                        text = item[1][0]
                        confidence = float(item[1][1])

                        if text and text.strip():
                            ocr_texts.append(
                                {
                                    "bbox": bbox,
                                    "text": text.strip(),
                                    "confidence": confidence,
                                }
                            )
                except (IndexError, ValueError, TypeError):
                    continue

            if ocr_texts:

                if page_data["text"]:
                    page_data["text"].extend(ocr_texts)
                else:
                    page_data["text"] = ocr_texts

                page_data["source"] = f"{page_data['source']}_with_ocr"

            return page_data

        except Exception:
            return page_data

    def get_text_content(self, pages_data: List[Dict[str, Any]]) -> str:

        text_parts = []

        for page_data in pages_data:
            page_texts = []

            if "text" in page_data and isinstance(page_data["text"], list):
                for text_item in page_data["text"]:
                    if isinstance(text_item, dict) and "text" in text_item:
                        text = text_item["text"]
                        if text and text.strip():
                            page_texts.append(text.strip())
                    elif isinstance(text_item, str) and text_item.strip():
                        page_texts.append(text_item.strip())

            if page_texts:
                text_parts.append("\n".join(page_texts))

        return "\n\n".join(text_parts)
