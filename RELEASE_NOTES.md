# v1.0.4 - English Line-Free Portfolio Refresh

## Scope

This release refreshes `NhapMonAI` for US English HR and engineering review. The public README, release notes, captions, visible SVG text and visual asset labels are written in English and keep project claims tied to repository evidence.

## Main Updates

- Rewrote the README in US English with a five-minute review path, project profile, evidence map, system overview, quantitative results, run instructions, FAQ, team table and contact table.
- Regenerated the ALPR motion GIF as a line-free English asset with no animated connector lines, dotted paths or curved paths.
- Kept SVG-visible text ASCII-safe and English-only.
- Removed the remaining horizontal separator line from the SVG reviewer card so labels do not sit behind decorative paths.
- Preserved honest academic scope: team project, validation-set detector metrics, LAN prototype and no production traffic-enforcement claim.
- Added release-facing notes for report, slide, app archive, PlateGate PC archive, GIF, SVG and source snapshot review assets.

## Repository Evidence

- YOLO detector with reported mAP50 `0.99450` on the project validation set.
- OCR path using FastALPR / fast-plate-ocr concepts with plate-crop normalization.
- Python desktop app for image and video inference.
- PlateGate PC LAN prototype with `/health` and `/scan` endpoints on port `8765`.
- Typst report, seminar PDF, PPTX slide deck, Kaggle/IPYNB notebooks and release-backed visual assets.

## Scope Boundary

This repository remains an academic computer vision prototype and portfolio archive. Detector metrics are tied to the project validation set; OCR and gate-control behavior are demonstration evidence, not proof of a production traffic-enforcement system.
