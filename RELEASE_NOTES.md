# v1.1.1 - Evidence-First Portfolio Visual Fix

## Purpose

This release provides a concise, US English portfolio record of the Group 05 Vietnamese automatic license plate recognition project. Technical claims remain tied to notebooks, source code, model outputs, reports, screenshots, and versioned release assets.

## Updates

- Corrected the ALPR review-card footer by centering both lines, adding fixed side padding, and shortening the prototype boundary so neither line exceeds its panel.
- Reorganized the README around project scope, verified contribution, system pipeline, detector metrics, reproducibility, limitations, and reviewable evidence.
- Expanded the evidence gallery from four to eight repository images covering desktop inference, training curves, the confusion matrix, OCR, checkpoint continuation, and PlateGate demonstrations.
- Preserved the complete tracked project tree, including notebooks, Python applications, Typst sources, PDF and PPTX deliverables, checkpoints, archives, and report images.
- Kept large binaries under Git LFS and verified the local LFS object store.
- Kept all visible SVG text in ASCII-safe English and retained line-free SVG/GIF layouts so decorative paths cannot obstruct labels.
- Preserved the academic boundary: validation-set detector metrics and a LAN prototype do not establish production OCR or traffic-enforcement performance.

## Reported Detector Results

| Metric | Validation Result |
|---|---:|
| Precision | `0.99448` |
| Recall | `0.99373` |
| mAP50 | `0.99450` |
| mAP50-95 | `0.77006` |

## Verification Record

- Three Jupyter notebooks passed structural validation.
- The Typst report compiled successfully from the tracked source.
- Git LFS integrity checks passed for the designated large assets.
- Python entry points passed static bytecode compilation.
- The 44-page seminar PDF passed text extraction and sample-page visual inspection.
- The repository images and 32-frame motion GIF passed visual inspection for clipping and label overlap.
- The corrected ALPR review card passed native-width and scaled visual inspection with ASCII-safe English text.

## Scope Boundary

This repository is a public academic portfolio archive. Dataset permissions, environment-specific notebook paths, OCR limitations, and the absence of an open-source license remain documented in the README.
