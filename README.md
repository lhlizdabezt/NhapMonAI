# NhapMonAI

Đồ án Nhập môn Trí tuệ Nhân tạo của Nhóm 5 về hệ thống phát hiện và nhận dạng biển số xe Việt Nam. Repository này gom đủ notebook huấn luyện, mô hình YOLO, ứng dụng Python OCR, ứng dụng PC mô phỏng mở trạm, báo cáo seminar, slide/hình minh họa và source Typst của báo cáo.

![Python GUI](HinhAnhBaoCao/AppPython/GUIPython.png)

## Điểm nổi bật

- Huấn luyện mô hình YOLO cho bài toán phát hiện biển số xe Việt Nam.
- Nhận dạng ký tự biển số bằng OCR, hỗ trợ FastALPR DefaultOCR và `fast_plate_ocr`.
- Ứng dụng Python desktop xử lý ảnh đơn, thư mục ảnh và video.
- Tích hợp FFmpeg để xuất video kết quả có annotate.
- Ứng dụng PC Gate nhận dữ liệu biển số qua HTTP và kiểm tra danh sách biển được phép.
- Notebook Kaggle cho hai giai đoạn: huấn luyện từ đầu và tiếp tục huấn luyện từ checkpoint.
- Bộ báo cáo, hình ảnh kết quả, confusion matrix, source Typst và PDF seminar.

## Cấu trúc repository

```text
NhapMonAI/
|-- AppPythonYOLO_OCR/                  # App Python YOLO + OCR, FFmpeg, model và demo assets
|-- AppPythonPlateGatePC/               # App PC Gate nhận biển số qua HTTP và kiểm tra allow-list
|-- Group5_Notebook_IPYNB/              # Notebook huấn luyện và continuation training
|-- Group5_BaoCaoNhapMonAI/             # Source Typst của báo cáo
|-- HinhAnhBaoCao/                      # Hình minh họa, biểu đồ, demo app
|-- Group5_BaoCaoSeminarNhapMonAI.pdf   # PDF báo cáo seminar
|-- v65.pt                              # Checkpoint YOLO chính
|-- vip pro level max python.py         # Bản app Python OCR đơn file
`-- README.md
```

## Ứng dụng Python YOLO OCR

Source chính nằm trong:

```text
AppPythonYOLO_OCR/
```

Các file đáng chú ý:

- `Group5_AppPython_YOLO_OCR.py`: app Python desktop chính.
- `app python vip pro kkkkkjsadljk.py`: bản app OCR nâng cấp/đơn file.
- `requirements.txt`: danh sách thư viện cần cài.
- `best.pt`, `best (1).pt`: checkpoint YOLO đi kèm app.
- `ffmpeg/bin/`: FFmpeg, FFprobe và FFplay phục vụ xử lý video.
- `outputs_hcmus_image_first_final/`: kết quả demo đã xuất ra từ app.

Cài thư viện:

```bash
cd AppPythonYOLO_OCR
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Chạy app:

```bash
python Group5_AppPython_YOLO_OCR.py
```

Hoặc chạy bằng batch file trên Windows:

```bash
run_Group5_AppPython_YOLO_OCR.bat
```

Trong giao diện, chọn model YOLO `.pt`, chọn ảnh/video/thư mục ảnh đầu vào, sau đó chạy nhận dạng. Kết quả được lưu trong thư mục output của app.

## Ứng dụng PC Gate

Source nằm trong:

```text
AppPythonPlateGatePC/PlateGatePC/
```

Ứng dụng này mô phỏng trạm PC nhận biển số từ thiết bị/app khác qua HTTP:

- Endpoint kiểm tra trạng thái: `GET /health`
- Endpoint nhận kết quả scan: `POST /scan`
- Port mặc định: `8765`
- File allow-list: `bien_so_duoc_phep.txt`

Chạy app:

```bash
cd AppPythonPlateGatePC/PlateGatePC
python Group5_AppPYMoRongThucTe.py
```

Hoặc chạy nhanh trên Windows:

```bash
mo_tram_pc.bat
```

## Notebook huấn luyện

Notebook nằm trong `Group5_Notebook_IPYNB/`:

- `Group5_Notebook01_FirstTraining.ipynb`: huấn luyện YOLO từ đầu cho 25 epoch.
- `Group5_Notebook02_ContinuationTraining.ipynb`: tiếp tục huấn luyện từ checkpoint để cải thiện kết quả.

Notebook được thiết kế theo môi trường Kaggle. Khi chạy lại ở môi trường khác, cần chỉnh đường dẫn dataset, checkpoint và thư mục output cho phù hợp.

## Báo cáo và tài liệu

- `Group5_BaoCaoSeminarNhapMonAI.pdf`: bản PDF báo cáo seminar.
- `Group5_BaoCaoNhapMonAI/`: source Typst của báo cáo, gồm `main.typ`, `config.typ`, `src/`, `assets/`, `fonts/` và file bibliography.
- `HinhAnhBaoCao/`: hình ảnh dùng trong báo cáo và demo.

## Kết quả minh họa

### Confusion Matrix

![Confusion Matrix](HinhAnhBaoCao/confusion_matrix.png)

### Kết quả continuation training

![Training Results](HinhAnhBaoCao/resultsOfVersion65ContinueFromCheckpoint.png)

### Demo OCR

![OCR Demo](HinhAnhBaoCao/DemoFromNotebook/OCRDemo.png)

### Demo Android

![Android Camera Mode](HinhAnhBaoCao/AppAndroid/AndroidCameraMode.jpg)

## Model và file lớn

Repository có chứa model, file nén và binary FFmpeg. Các file lớn mới được quản lý bằng Git LFS để tránh giới hạn file của GitHub.

Sau khi clone, nên chạy:

```bash
git lfs install
git lfs pull
```

Nếu chưa cài Git LFS, tải từ trang chính thức của Git LFS hoặc cài qua package manager phù hợp với hệ điều hành.

## Công nghệ sử dụng

- Python
- YOLO / Ultralytics
- OpenCV
- FastALPR
- fast_plate_ocr
- FFmpeg
- NumPy, Pandas, Pillow
- Kaggle Notebook
- Typst

## Ghi chú

Project này phục vụ học phần Nhập môn Trí tuệ Nhân tạo. Một số đường dẫn trong notebook/app có thể cần chỉnh lại khi chạy trên máy khác, đặc biệt là đường dẫn dataset Kaggle, checkpoint YOLO và thư mục FFmpeg.
