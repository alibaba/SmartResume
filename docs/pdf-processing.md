# PDF geometry and reading order

PDF pages are rendered at 144 DPI. Native text, image regions, masks, OCR boxes and layout regions use coordinates relative to the rendered page. Crop offsets and separate horizontal/vertical scaling ratios are included.

## Native text and OCR

Horizontal native word boxes form line segments. Large gaps start separate segments to avoid masking across columns or graphics. Each mask uses the union of its word boxes, expanded by two pixels and clipped to the page. Unreadable, rotated or fragmented native content remains available to OCR. OCR boxes from resized images are mapped back to the page coordinate system.

## Reading order

Text is grouped into rows using median text height and vertical centers, assigned to layout regions and sorted within the resulting regions. Unassigned text is associated with the nearest rectangle using Euclidean distance. When layout regions are unavailable, the parser falls back to geometric row order. These heuristics can still make mistakes on unusual writing directions, poorly detected regions or complex multi-column pages.

## Abnormal PDF routing

Producer/Creator metadata, garbling and fragmentation help select OCR and the analyzer's dual-text strategy. Readable native text can rescue an empty OCR result for a metadata-flagged file. Forced OCR and garbled native text do not reintroduce native content through that fallback.

The implementation uses pdfplumber, RapidOCR and the configured layout model.
