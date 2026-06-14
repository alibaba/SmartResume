"""
File processor module
"""
import math
import os
import re
import cv2
import base64
import io
import string
import uuid
import zipfile
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple
from smartresume.data.text_extractor import TextExtractor
from smartresume.utils.config import config
from smartresume.data.layout_detector import LayoutDetector

MAX_ZIP_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file
MAX_ZIP_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB total
MAX_ZIP_FILE_COUNT = 200
ALLOWED_ZIP_PREFIXES = ('word/document.xml', 'word/media/', 'word/header', 'word/footer')
ALLOWED_EXTENSIONS = {
    '.docx', '.doc', '.docm', '.dotx', '.dotm', '.xls',
    '.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp',
    '.txt', '.md', '.html'
}


class FileProcessor:
    """File processor responsible for handling different file formats"""

    def __init__(self, text_extractor: TextExtractor):
        self.text_extractor = text_extractor

        self.layout_detector = None
        if config.layout_detection.enabled:
            self.layout_detector = LayoutDetector()

    @staticmethod
    def _validate_zip_safety(zip_path: str) -> None:
        """Validate ZIP file against zip bomb and malicious entries."""
        with zipfile.ZipFile(zip_path, 'r') as z:
            total_size = 0
            file_count = 0
            for info in z.infolist():
                file_count += 1
                if file_count > MAX_ZIP_FILE_COUNT:
                    raise ValueError(f"ZIP file contains too many entries (>{MAX_ZIP_FILE_COUNT})")
                if info.file_size > MAX_ZIP_FILE_SIZE:
                    raise ValueError(
                        f"ZIP entry '{info.filename}' exceeds size limit "
                        f"({info.file_size} > {MAX_ZIP_FILE_SIZE})"
                    )
                total_size += info.file_size
                if total_size > MAX_ZIP_TOTAL_SIZE:
                    raise ValueError(
                        f"ZIP total uncompressed size exceeds "
                        f"limit (>{MAX_ZIP_TOTAL_SIZE})"
                    )

    @staticmethod
    def _is_allowed_zip_entry(name: str) -> bool:
        """Check if a ZIP entry path is in the whitelist."""
        return any(name.startswith(prefix) or name == prefix for prefix in ALLOWED_ZIP_PREFIXES)

    @staticmethod
    def _sanitize_file_path(file_path: str) -> str:
        """Sanitize file path by copying to a safe temp location with UUID name if needed."""
        basename = os.path.basename(file_path)
        if re.search(r'[;&|`$(){}!<>]', basename):
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(f"Unsupported file extension: {ext}")
            import tempfile
            import shutil
            safe_path = os.path.join(tempfile.gettempdir(), f"sr_{uuid.uuid4().hex}{ext}")
            shutil.copy2(file_path, safe_path)
            return safe_path
        return file_path

    @staticmethod
    def _garbled_ratio(text: str) -> float:
        """Compute garbled ratio in text supporting major language charsets"""
        if not text:
            return 1.0

        def is_valid(c: str) -> bool:
            return any([
                c in string.printable,
                '\u4e00' <= c <= '\u9fff',
                '\u0400' <= c <= '\u04FF',
                '\u00C0' <= c <= '\u024F',
                '\u1EA0' <= c <= '\u1EFF',
                '\u0600' <= c <= '\u06FF',
                '\u0900' <= c <= '\u097F',
                '\u0E00' <= c <= '\u0E7F',
                '\u3040' <= c <= '\u309F',
                '\u30A0' <= c <= '\u30FF',
                '\uAC00' <= c <= '\uD7AF',
            ])

        valid_chars = sum(1 for c in text if is_valid(c))
        ratio = 1.0 - valid_chars / len(text)
        return ratio

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a file, choosing the appropriate method based on type"""
        file_path = self._sanitize_file_path(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {file_ext}. Supported: "
                "PDF, images (.jpg/.jpeg/.png/.tiff/.bmp), "
                "Word (.docx/.doc/.docm/.dotx/.dotm/.xls), "
                "text (.txt/.md/.html)"
            )

        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self._process_image(file_path)
        elif file_ext in ['.docx', '.doc', '.docm', '.dotx', '.dotm', '.xls']:
            return self._process_word(file_path)
        elif file_ext == '.pdf':
            return self._process_pdf(file_path)
        elif file_ext in ['.txt', '.md', '.html']:
            return self._process_text(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {file_ext}. Supported: "
                "PDF, images (.jpg/.jpeg/.png/.tiff/.bmp), "
                "Word (.docx/.doc/.docm/.dotx/.dotm/.xls), "
                "text (.txt/.md/.html)"
            )

    def _process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process image file"""
        image = cv2.imread(image_path)
        h, w, _ = image.shape

        scale = max(1080 / min(h, w), 1)
        new_w = int(w * scale)
        new_h = int(h * scale)

        image = cv2.resize(image, (new_w, new_h))

        ocr_results = self.text_extractor.ocr_extract(image)
        ocr_results = self.restore_ocr_coordinates(ocr_results, scale)

        page_data = {
            'page_number': 1,
            'text': [],
            'source': 'image_ocr'
        }

        page_data = self.text_extractor.add_ocr_to_page_text(page_data, ocr_results)
        if config.layout_detection.enabled:
            layout_location = self.layout_detector.detect(image.copy())
            sorted_results = (
                self.text_extractor.resort_page_text_with_layout(
                    page_data['text'], 0, layout_location
                )
            )
        else:
            sorted_results = (
                self.text_extractor
                .resort_page_text_with_center_location(
                    page_data['text'], 0
                )
            )

        image_base64 = self._image_to_base64(image)
        return [{'text': sorted_results, 'image': image_base64}]

    def _process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process PDF file"""
        if config.processing.use_force_ocr:
            return self._process_pdf_ocr_only(pdf_path)

        text_info = self.text_extractor.extract_from_pdf_string(pdf_path)
        is_abnormal = False
        if isinstance(text_info, tuple):
            text = text_info[0]
            if len(text_info) > 1:
                is_abnormal = bool(text_info[1])
        else:
            text = text_info

        garbled_ratio = self._garbled_ratio(text)
        if garbled_ratio > 0.15 or is_abnormal:
            return self._process_pdf_ocr_only(pdf_path, garbled_ratio=garbled_ratio)

        if config.processing.use_pdf_raw_text:
            if text.strip() == "":
                return self._process_pdf_with_ocr(pdf_path)
            text_lines = text.split("\n")
            result = [{'text': [{'text': line} for line in text_lines]}]
            return result
        else:
            return self._process_pdf_with_ocr(pdf_path)

    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert image to base64 string"""
        buffered = io.BytesIO()
        Image.fromarray(image).save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def _process_word(self, word_path: str) -> List[Dict[str, Any]]:
        """Process Word document with XML text + embedded image OCR strategy."""
        file_ext = os.path.splitext(word_path)[1].lower()

        if file_ext == ".docx":
            try:
                xml_results = self._extract_leaf_tables_from_xml(word_path)
                all_text_lines: List[str] = []

                if xml_results:
                    for item in xml_results:
                        if item.get("type") == "paragraph":
                            all_text_lines.append(item.get("text", ""))
                        elif item.get("type") == "table":
                            all_text_lines.extend(item.get("text", "").split("\n"))

                ocr_lines = self._extract_docx_images_ocr(word_path)
                if ocr_lines:
                    all_text_lines.extend(ocr_lines)

                all_text_lines = [line.strip() for line in all_text_lines if line and line.strip()]
                if all_text_lines:
                    return [{'text': [{'text': line} for line in all_text_lines]}]
            except Exception:
                pass

        extracted_text = self._extract_word_text(word_path)
        if extracted_text.strip():
            return [{'text': [
                {'text': line}
                for line in extracted_text.split("\n")
                if line.strip()
            ]}]
        return [{'text': []}]

    def _extract_docx_images_ocr(self, docx_path: str) -> List[str]:
        """Extract images from docx package and run OCR on them."""
        import tempfile
        import shutil

        if not self.text_extractor.ocr:
            return []

        self._validate_zip_safety(docx_path)

        temp_dir = tempfile.mkdtemp(prefix="docx_extraction_")
        ocr_lines: List[str] = []

        try:
            with zipfile.ZipFile(docx_path, "r") as zip_ref:
                image_files = [f for f in zip_ref.namelist()
                               if self._is_allowed_zip_entry(f) and f.startswith("word/media/")]
                for img_path in image_files:
                    img_filename = os.path.basename(img_path)
                    if not img_filename:
                        continue
                    output_path = os.path.join(temp_dir, img_filename)
                    with zip_ref.open(img_path) as source, open(output_path, "wb") as target:
                        target.write(source.read())

                    image = cv2.imread(output_path)
                    if image is None:
                        continue

                    ocr_result = self.text_extractor.ocr_extract(np.array(image))
                    for item in ocr_result or []:
                        if len(item) >= 2:
                            text = item[1][0]
                            if isinstance(text, str) and text.strip():
                                ocr_lines.append(text.strip())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return ocr_lines

    def _extract_word_text(self, word_path: str) -> str:
        """Extract text from Word document using safe pure-Python parsers."""
        try:
            import docx2txt
            return docx2txt.process(word_path)
        except Exception:
            try:
                from docx import Document
                doc = Document(word_path)
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except Exception:
                return ""

    def _extract_leaf_tables_from_xml(self, docx_path: str) -> List[Dict[str, Any]]:
        """Extract paragraphs and leaf-table text blocks from docx XML."""
        try:
            from bs4 import BeautifulSoup
        except Exception:
            return []

        self._validate_zip_safety(docx_path)

        results = []
        try:
            with zipfile.ZipFile(docx_path, 'r') as z:
                if 'word/document.xml' not in z.namelist():
                    return []
                xml_content = z.read('word/document.xml')
                if len(xml_content) > 10 * 1024 * 1024:
                    raise ValueError("XML content exceeds 10MB size limit")
                soup = BeautifulSoup(xml_content, 'xml')
                body = soup.find('body')
                if not body:
                    return []

                all_tbls = soup.find_all('tbl')
                leaf_tables = [tbl for tbl in all_tbls if not tbl.find('tbl')]

                for child in body.find_all(['p', 'tbl'], recursive=False):
                    if child.name != 'p':
                        continue
                    parent = child.parent
                    in_table = False
                    in_pict = False
                    while parent and parent != body:
                        if parent.name == 'tbl':
                            in_table = True
                            break
                        if parent.name in ['pict', 'textbox', 'txbxContent']:
                            in_pict = True
                            break
                        parent = parent.parent

                    if child.find('pict') or child.find('textbox'):
                        in_pict = True

                    if not in_table and not in_pict:
                        para_text = "".join([t.get_text() for t in child.find_all('t')]).strip()
                        if para_text:
                            hex_chars = set('0123456789ABCDEFabcdef')
                            is_hex_blob = len(para_text) > 200 and all(
                                c in hex_chars or c.isspace() for c in para_text
                            )
                            if is_hex_blob:
                                continue
                            results.append({'type': 'paragraph', 'text': para_text})

                table_idx = 0
                for tbl in leaf_tables:
                    table_data = []
                    rows = tbl.find_all('tr', recursive=False) or tbl.find_all('tr')
                    for row in rows:
                        row_data = []
                        cells = row.find_all('tc', recursive=False) or row.find_all('tc')
                        for tc in cells:
                            cell_paragraphs = []
                            for p in tc.find_all('p'):
                                para_parts = []
                                for elem in p.descendants:
                                    if elem.name == 't' and elem.string:
                                        para_parts.append(elem.string)
                                    elif elem.name == 'br':
                                        para_parts.append('\n')

                                para_text = "".join(para_parts).strip()
                                if para_text:
                                    cell_paragraphs.append(para_text)

                            if not cell_paragraphs:
                                cell_text = tc.get_text(separator=" ", strip=True)
                                if cell_text:
                                    cell_paragraphs = [cell_text]

                            row_data.append("\n".join(cell_paragraphs).strip())
                        if any(row_data):
                            table_data.append(row_data)

                    if table_data:
                        table_text_lines = [" | ".join(row) for row in table_data]
                        results.append({
                            'type': 'table',
                            'table_index': table_idx,
                            'rows': table_data,
                            'text': "\n".join(table_text_lines),
                            'row_count': len(table_data),
                            'col_count': max(len(r) for r in table_data) if table_data else 0
                        })
                        table_idx += 1

            return results
        except Exception:
            return []

    def _process_pdf_with_ocr(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process PDF combining text extraction and OCR"""
        page_texts, images, _ = self._unpack_extract_with_positions(
            self.text_extractor.extract_with_positions(
                pdf_path, extract_text=True,
                extract_render_img=True
            )
        )
        # images = self._pdf_to_images(pdf_path)
        results = []

        for page_num, img in enumerate(images):
            blacked_out_image = self._blackout_text(img.copy(), page_texts[page_num])

            h, w, _ = blacked_out_image.shape

            new_size = 960 / min(h, w)
            new_w = int(w * new_size)
            new_h = int(h * new_size)

            blacked_out_image = cv2.resize(
                blacked_out_image, (new_w, new_h),
                interpolation=cv2.INTER_AREA
            )

            ocr_results = self.text_extractor.ocr_extract(blacked_out_image)
            ocr_results = self.restore_ocr_coordinates(ocr_results, new_size)

            page_data = {
                'page_number': page_num + 1,
                'text': page_texts[page_num],
                'source': 'pdf_text_with_ocr'
            }

            combined_page_data = self.text_extractor.add_ocr_to_page_text(page_data, ocr_results)

            if config.layout_detection.enabled:
                layout_location = self.layout_detector.detect(img.copy())
                sorted_texts = (
                    self.text_extractor
                    .resort_page_text_with_layout(
                        combined_page_data['text'],
                        page_num, layout_location
                    )
                )
            else:
                sorted_texts = (
                    self.text_extractor
                    .resort_page_text_with_center_location(
                        combined_page_data['text'], page_num
                    )
                )

            image_base64 = self._image_to_base64(img)

            page_result = {'text': sorted_texts, 'image': image_base64}

            results.append(page_result)

        return results

    def restore_ocr_coordinates(self, ocr_results: List[Any], scale: float) -> List[Any]:
        """
        Restore coordinates for nested OCR result structures by applying inverse scale.

        Args:
            ocr_results: OCR engine result list.
            scale: Scale used during OCR (i.e., new_size).

        Returns:
            OCR results with coordinates mapped back to original size, preserving structure.
        """
        if not ocr_results:
            return []

        if scale == 0:
            return []

        inverse_scale = 1.0 / scale
        restored_results = []

        for result in ocr_results:
            try:
                box_points_on_resized = result[0][0]
                text_info = result[1]

                if len(box_points_on_resized) >= 2:
                    p1, p2 = box_points_on_resized[0], box_points_on_resized[1]
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    angle = abs(math.degrees(math.atan2(dy, dx)))
                    if angle > 10:
                        continue

                restored_box_points = []
                for point in box_points_on_resized:
                    restored_x = int(round(point[0] * inverse_scale))
                    restored_y = int(round(point[1] * inverse_scale))
                    restored_box_points.append([restored_x, restored_y])

                restored_box_data = [restored_box_points]

                restored_results.append([restored_box_data, text_info])

            except (TypeError, IndexError):
                continue

        return restored_results

    def _process_pdf_ocr_only(
            self, pdf_path: str,
            garbled_ratio: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Process PDF in OCR-only mode.

        When PDF image-bbox metadata is available, also build `text_hybrid` by mixing
        PDF text and OCR text in image regions. Otherwise fallback to OCR-only output.
        """
        extracted = self.text_extractor.extract_with_positions(
            pdf_path, extract_text=True,
            extract_render_img=True
        )
        pdf_raw_texts, images, pages_image_bboxes = self._unpack_extract_with_positions(extracted)
        if not pdf_raw_texts:
            pdf_raw_texts = [[] for _ in range(len(images))]

        results = []

        for page_num, img in enumerate(images):
            h, w, _ = img.shape
            new_size = 960 / min(h, w)
            new_w = int(w * new_size)
            new_h = int(h * new_size)

            resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            ocr_results = self.text_extractor.ocr_extract(resized_img)
            ocr_results = self.restore_ocr_coordinates(ocr_results, new_size)

            page_data_ocr = {
                'page_number': page_num + 1,
                'text': [],
                'source': 'pdf_ocr'
            }
            page_data_ocr = self.text_extractor.add_ocr_to_page_text(page_data_ocr, ocr_results)
            if config.layout_detection.enabled:
                layout_location = self.layout_detector.detect(
                    resized_img.copy()
                )
                sorted_texts_ocr = (
                    self.text_extractor
                    .resort_page_text_with_layout(
                        page_data_ocr['text'],
                        page_num, layout_location
                    )
                )
            else:
                sorted_texts_ocr = (
                    self.text_extractor
                    .resort_page_text_with_center_location(
                        page_data_ocr['text'], page_num
                    )
                )

            if garbled_ratio > 0.15:
                sorted_texts_hybrid = sorted_texts_ocr
            else:
                page_pdf_texts = (
                    pdf_raw_texts[page_num]
                    if page_num < len(pdf_raw_texts) else []
                )
                page_image_bboxes = (
                    pages_image_bboxes[page_num]
                    if page_num < len(pages_image_bboxes)
                    else []
                )
                hybrid_texts = []
                pattern = r'^[a-zA-Z0-9\-~_]{40,}$'
                for pdf_text_item in page_pdf_texts:
                    if isinstance(pdf_text_item, dict) and 'text' in pdf_text_item:
                        text = pdf_text_item.get('text', '')
                        if text and re.match(pattern, text):
                            continue
                        hybrid_texts.append(pdf_text_item)
                    else:
                        hybrid_texts.append(pdf_text_item)

                if page_image_bboxes and ocr_results:
                    hybrid_texts.extend(
                        self._filter_ocr_in_image_regions(
                            ocr_results, page_image_bboxes
                        )
                    )

                hybrid_text_length = sum(
                    len(item.get('text', '').strip())
                    for item in hybrid_texts
                    if isinstance(item, dict)
                )
                if hybrid_text_length < 20:
                    sorted_texts_hybrid = sorted_texts_ocr
                else:
                    if config.layout_detection.enabled:
                        layout_location = (
                            self.layout_detector.detect(
                                resized_img.copy()
                            )
                        )
                        sorted_texts_hybrid = (
                            self.text_extractor
                            .resort_page_text_with_layout(
                                hybrid_texts, page_num,
                                layout_location
                            )
                        )
                    else:
                        sorted_texts_hybrid = (
                            self.text_extractor
                            .resort_page_text_with_center_location(
                                hybrid_texts, page_num
                            )
                        )

            image_base64 = self._image_to_base64(resized_img)

            page_result = {
                'text': sorted_texts_ocr,
                'text_hybrid': sorted_texts_hybrid,
                'image': image_base64,
                'is_abnormal_pdf': garbled_ratio > 0.15
            }

            results.append(page_result)

        return results

    def _unpack_extract_with_positions(
            self, extracted: Tuple[Any, ...]
    ) -> Tuple[List[List[Dict[str, Any]]], List[np.ndarray], List[List[List[float]]]]:
        """Unpack extractor outputs supporting both 2-value and 3-value return formats."""
        if not isinstance(extracted, tuple):
            return [], [], []
        if len(extracted) == 3:
            page_texts, images, pages_image_bboxes = extracted
            return page_texts or [], images or [], pages_image_bboxes or []
        if len(extracted) == 2:
            page_texts, images = extracted
            return page_texts or [], images or [], []
        return [], [], []

    def _filter_ocr_in_image_regions(
            self, ocr_results: List[Any],
            image_bboxes: List[List[float]]
    ) -> List[Dict[str, Any]]:
        """Filter OCR blocks whose center falls in an image bbox region."""
        ocr_in_images = []
        for item in ocr_results:
            try:
                if len(item) >= 2 and isinstance(item[1], list) and len(item[1]) >= 2:
                    xs = [p[0] for p in item[0][0]]
                    ys = [p[1] for p in item[0][0]]
                    ocr_x_min, ocr_x_max = min(xs), max(xs)
                    ocr_y_min, ocr_y_max = min(ys), max(ys)
                    ocr_center_x = (ocr_x_min + ocr_x_max) / 2
                    ocr_center_y = (ocr_y_min + ocr_y_max) / 2

                    is_in_image = False
                    for img_bbox in image_bboxes:
                        img_x0, img_y0, img_x1, img_y1 = img_bbox
                        if img_x0 <= ocr_center_x <= img_x1 and img_y0 <= ocr_center_y <= img_y1:
                            is_in_image = True
                            break

                    if is_in_image:
                        text = item[1][0]
                        confidence = float(item[1][1])
                        if text and isinstance(text, str) and text.strip():
                            ocr_in_images.append({
                                'bbox': [ocr_x_min, ocr_y_min, ocr_x_max, ocr_y_max],
                                'text': text.strip(),
                                'confidence': confidence,
                                'source': 'image_ocr'
                            })
            except (TypeError, ValueError, IndexError):
                continue
        return ocr_in_images

    def _process_text(self, text_path: str) -> List[Dict[str, Any]]:
        """Process text file"""
        with open(text_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return [{'text': text}]

    def _blackout_text(
            self, image: np.ndarray,
            page_text: List[Dict], color=(0, 0, 0)
    ) -> np.ndarray:
        """Black out text regions in image"""

        for item in page_text:
            bbox = item['bbox']
            x0, y0, x1, y1 = [int(coord) for coord in bbox]
            cv2.rectangle(image, (x0, y0), (x1, y1), color, -1)
        return image
