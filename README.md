# NhapMonAI

<p align="center">
  <img src="assets/alpr-pipeline-motion.gif" alt="Animated NhapMonAI YOLO OCR pipeline" width="900" />
</p>

<p align="center">
  <a href="https://github.com/lhlizdabezt/NhapMonAI/releases/latest">
    <img src="https://img.shields.io/github/v/release/lhlizdabezt/NhapMonAI?style=for-the-badge&logo=github&label=release" alt="Latest release" />
  </a>
  <img src="https://img.shields.io/badge/HCMUS-FETEL%2022DTV__CLC1-2563eb?style=for-the-badge" alt="HCMUS FETEL 22DTV CLC1" />
  <img src="https://img.shields.io/badge/AI-YOLO%20%2B%20OCR-0f766e?style=for-the-badge" alt="YOLO OCR" />
  <img src="https://img.shields.io/badge/Apps-Python%20Desktop%20%2B%20PC%20Gate-D95319?style=for-the-badge" alt="Python desktop and PC gate apps" />
  <img src="https://img.shields.io/badge/Docs-Typst%20Report%20%2B%20Slides-334155?style=for-the-badge" alt="Typst report and slides" />
</p>

<p align="center">
  <b>Vehicle License Plate Detection and Recognition Using YOLO and OCR on the Vietnamese License Plates Detection Dataset</b><br/>
  <sub>Group 05 - Introduction to Artificial Intelligence - VNUHCM University of Science, Faculty of Electronics and Telecommunications</sub>
</p>

## 🚀 Project Snapshot

`NhapMonAI` is an end-to-end applied AI coursework project for Vietnamese vehicle license plate detection and recognition. The repository packages the full engineering trail: Kaggle notebooks, YOLO checkpoints, Python desktop OCR app, PC gate-control demo, Typst report source, seminar PDF, slides and visual evidence.

| Area | Evidence |
| --- | --- |
| Problem | Detect Vietnamese license plates, crop plate regions, run OCR, normalize plate text and export annotated results |
| AI stack | YOLO / Ultralytics, OpenCV, FastALPR DefaultOCR, `fast_plate_ocr`, Python |
| Applications | Desktop image/video OCR tool and LAN-based PC gate-control demo |
| Academic assets | Typst report source, PDF report, seminar slides, result figures, notebook logs |
| Portfolio signal | Reproducible file structure, Git LFS for large model/binary assets, release packaging and documented limitations |

## 🧠 Results

The continuation checkpoint reported in the final report reaches:

| Metric | Validation result |
| --- | ---: |
| Precision | `0.99448` |
| Recall | `0.99373` |
| mAP50 | `0.99450` |
| mAP50-95 | `0.77006` |

The detector performs strongly on the project validation split, while the README and report intentionally keep the OCR and real-world deployment limitations explicit. This project is a course-grade proof of concept, not a production traffic-control system.

## 🖼️ Visual Evidence

| Python Desktop App | YOLO + OCR Video Pipeline |
| --- | --- |
| ![Python desktop GUI](Group5_BaoCaoNhapMonAI/assets/python_gui.png) | ![YOLO OCR video result](Group5_BaoCaoNhapMonAI/assets/video_yolo_ocr_fastalpr.png) |

| Confusion Matrix | Android / Gate Demo |
| --- | --- |
| ![Confusion matrix](Group5_BaoCaoNhapMonAI/assets/confusion_matrix.png) | ![Android gate scan demo](Group5_BaoCaoNhapMonAI/assets/android_gate_scan_demo.jpg) |

## 🗂️ Repository Structure

```text
NhapMonAI/
|-- AppPythonYOLO_OCR/                 # Python YOLO + OCR desktop app, demo outputs, FFmpeg and checkpoints
|-- AppPythonPlateGatePC/              # PC gate-control demo receiving plate scans over HTTP
|-- Group5_Notebook_IPYNB/             # Kaggle notebooks for first training and continuation training
|-- Group5_BaoCaoNhapMonAI/            # Typst source, figures, bibliography and report assets
|-- HinhAnhBaoCao/                     # Presentation-ready visual evidence
|-- Academic_Deliverables/             # Seminar slide deck and work-assignment PDF
|-- assets/                            # README motion/visual assets
|-- Group5_BaoCaoSeminarNhapMonAI.pdf  # Final seminar report PDF
|-- v65.pt                             # Main YOLO checkpoint
`-- README.md
```

## ⚙️ Quick Start

Install Git LFS before cloning because the repo contains checkpoints and app bundles:

```bash
git lfs install
git clone https://github.com/lhlizdabezt/NhapMonAI.git
cd NhapMonAI
git lfs pull
```

Run the main Python OCR app:

```bash
cd AppPythonYOLO_OCR
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python Group5_AppPython_YOLO_OCR.py
```

Windows shortcut:

```bash
cd AppPythonYOLO_OCR
run_Group5_AppPython_YOLO_OCR.bat
```

Run the PC gate-control demo:

```bash
cd AppPythonPlateGatePC/PlateGatePC
python Group5_AppPYMoRongThucTe.py
```

Default endpoints:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Check server status |
| `POST /scan` | Submit detected plate text |
| Port `8765` | Local LAN demo port |
| `bien_so_duoc_phep.txt` | Allow-list for gate decisions |

## 📓 Notebooks

| Notebook | Purpose |
| --- | --- |
| `Group5_Notebook_IPYNB/Group5_Notebook01_FirstTraining.ipynb` | First YOLO training run from scratch |
| `Group5_Notebook_IPYNB/Group5_Notebook02_ContinuationTraining.ipynb` | Continuation training from checkpoint |
| `AppPythonYOLO_OCR/group-5-vietnamese-license-plates-detection-lhl.ipynb` | Kaggle-oriented experiment notebook and output trace |

The notebooks were designed for Kaggle paths. When running outside Kaggle, update dataset, checkpoint and output paths before executing cells.

## 👥 Team

| Student ID | Name |
| --- | --- |
| `22207043` | Mai Xuân Khang |
| `22207106` | Trương Quang Vũ |
| `22207112` | Lý Phi Hùng |
| `22207063` | Văn Đình Nam |
| `22207062` | Trần Sĩ Nam |
| `22207056` | Lương Hải Long |
| `22207066` | Lê Tấn Phi Pha |

## 🧰 Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,opencv,tensorflow,pytorch,git,github,vscode,linux,latex&perline=9" alt="Tech stack icons" />
</p>

- Python, Tkinter, OpenCV, NumPy, Pandas, Pillow
- YOLO / Ultralytics model training and inference
- FastALPR DefaultOCR and `fast_plate_ocr`
- FFmpeg / FFprobe / FFplay for video handling
- Kaggle Notebook workflow
- Typst report source and academic PDF packaging
- GitHub CLI, Git LFS, releases and tags

## 📦 Release Assets

The GitHub release is intended as the HR/reviewer entry point:

- Final seminar PDF
- Seminar slide deck
- Python OCR source/app bundle
- PC gate-control source/app bundle
- Android APK demo package, when distributed as a release asset
- Git tag `v1.0.0` for the submitted portfolio snapshot

## 📌 Notes

- The repository keeps large binary assets in Git LFS where appropriate.
- Raw dataset archives are intentionally not treated as the main public review surface; dataset references and demo outputs are documented instead.
- Some code paths in notebooks and apps may need adjustment on another machine, especially dataset paths, checkpoint paths and FFmpeg paths.
- No explicit open-source license has been added yet, so treat this as an academic portfolio archive unless a license is added later.

---

<p align="center">
  <b>Built by Group 05 for Introduction to Artificial Intelligence - HCMUS FETEL.</b><br/>
  <sub>From detector training to OCR demo to a reviewable engineering portfolio.</sub>
</p>
