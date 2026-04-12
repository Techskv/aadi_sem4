
# OCR Strategy & Testing Plan

## 1. Preprocessing Pipeline
We'll implement a robust image preprocessing pipeline to handle scanned answer sheets:

1. **Binarization**: Convert to black & white using adaptive thresholding (Otsu's method)
2. **Denoising**: Remove small speckles/noise
3. **Deskewing**: Correct rotation if the paper was scanned at an angle
4. **Rescaling**: Resize image if DPI is too low for Tesseract (< 300 DPI)

## 2. Text Extraction Strategy
- **Tesseract Configuration**: Use `--oem 3 --psm 6` (Assume a single uniform block of text)
- **Language**: English (`eng`)
- **Confidence Scoring**: Filter out low-confidence reads (< 40%)

## 3. PDF Handling
- Convert PDF pages to high-res images (300 DPI) using `pdf2image`
- Process each page individually
- Stitch results together

## 4. Testing Script
Create `scripts/test_ocr.py` to:
1. Generate a sample answer sheet image (using Pillow)
2. Run it through the OCR service
3. Verify extraction accuracy

## 5. Async Processing (Future)
- Once core logic works, wrap in Celery task
- Update Submission status: PENDING -> PROCESSING -> COMPLETED/FAILED
