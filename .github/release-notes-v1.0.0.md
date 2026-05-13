# NhapMonAI v1.0.0 - Portfolio Submission

This release packages the Group 05 Introduction to Artificial Intelligence project as a reviewable engineering and academic portfolio.

## Highlights

- Vietnamese license plate detection with YOLO.
- OCR workflow using FastALPR DefaultOCR / `fast_plate_ocr` integration.
- Python desktop app for image, folder and video inference.
- PC gate-control demo that receives plate scans over HTTP and checks an allow-list.
- Kaggle notebooks for first training and continuation training.
- Typst report source, seminar PDF, slide deck and visual evidence.
- Git LFS configuration for large model, FFmpeg and app bundle assets.

## Validation Snapshot

| Metric | Result |
| --- | ---: |
| Precision | `0.99448` |
| Recall | `0.99373` |
| mAP50 | `0.99450` |
| mAP50-95 | `0.77006` |

## Reviewer Entry Points

- Start with `README.md` for the complete project map.
- Open `Group5_BaoCaoSeminarNhapMonAI.pdf` for the academic report.
- Review `Group5_BaoCaoNhapMonAI/` for Typst source and cited figures.
- Run `AppPythonYOLO_OCR/Group5_AppPython_YOLO_OCR.py` for the desktop OCR app.
- Run `AppPythonPlateGatePC/PlateGatePC/Group5_AppPYMoRongThucTe.py` for the PC gate demo.

## Scope Note

This is a course-grade proof of concept for model training, OCR integration and demo software. It is not claimed as a production traffic-control system.
