#import "../config.typ": callout, tbl, cellhead, cell, photo

= DỮ LIỆU VÀ PHƯƠNG PHÁP THỰC HIỆN

== Tổng quan quy trình thực hiện

Quy trình của nhóm được thiết kế theo hướng có thể kiểm tra từng bước. Trước hết, dữ liệu ảnh và nhãn được xác minh cấu trúc thư mục, số lượng ảnh, số lượng tệp nhãn và định dạng từng dòng nhãn. Sau đó, notebook tạo tệp `data.yaml` để Ultralytics YOLO đọc đúng đường dẫn train, validation và test. Mô hình được huấn luyện ở hai mốc: mốc đầu không nạp checkpoint từ lần thử nghiệm trước, mốc sau tiếp tục từ checkpoint đã có để cải thiện kết quả. Sau khi có mô hình, nhóm kiểm thử phát hiện biển số, cắt vùng biển số, đưa vào OCR và triển khai phần mềm demo.

#callout([Pipeline tổng quát], [
  Ảnh hoặc video đầu vào → YOLO phát hiện biển số → crop vùng biển số → OCR đọc ký tự → chuẩn hóa chuỗi biển số → vẽ bounding box và nhãn → lưu ảnh/video/CSV kết quả.
])

== Bộ dữ liệu

Notebook ghi nhận bộ dữ liệu Vietnamese License Plates Detection được đặt trong thư mục `v58_merged_dataset_real` @vietnamese_lp_dataset với ba tập train, validation và test. Mỗi ảnh tương ứng một tệp nhãn YOLO. Dữ liệu được khai báo với một lớp duy nhất là `license_plate`, phù hợp với mục tiêu phát hiện vị trí biển số trước khi đọc ký tự.

#tbl(
  table(
    columns: (2.8cm, 2.6cm, 4.7cm, 1fr),
    inset: 5pt,
    stroke: 0.45pt,
    [#cellhead[Tập dữ liệu]], [#cellhead[Số ảnh]], [#cellhead[Số tệp nhãn]], [#cellhead[Ghi chú]],
    [Train], [49.417], [49.417], [#cell[Dùng huấn luyện mô hình YOLO.]],
    [Validation], [9.465], [9.465], [#cell[Dùng theo dõi metric trong quá trình huấn luyện và chọn checkpoint.]],
    [Test], [3.340], [3.340], [#cell[Dùng kiểm thử bổ sung khi cần đánh giá ngoài validation.]],
  ),
  [Thống kê số lượng ảnh và nhãn trong notebook],
)

#photo("assets/dataset_total_files.png", [Thống kê dung lượng và loại tệp của bộ dữ liệu trong thư mục làm việc], width: 82%)

Kiểm tra nhãn cho thấy định dạng tệp nhãn hợp lệ: mỗi dòng gồm năm cột theo chuẩn YOLO, không có tệp nhãn sai định dạng trong ba tập. Số lượng box được đếm trong notebook là 67.940 box cho train, 13.718 box cho validation và 5.185 box cho test. Trong quá trình Ultralytics quét dữ liệu, một số ảnh bị đánh dấu corrupt hoặc trùng nhãn, nhưng phần kiểm tra nhãn định dạng vẫn không phát hiện lỗi cột. Điều này cho thấy vấn đề chủ yếu nằm ở khả năng đọc ảnh hoặc duplicate label, không phải do cấu trúc nhãn YOLO bị sai.

== Tạo tệp cấu hình dữ liệu

Tệp `data.yaml` được tạo từ notebook với các trường cơ bản: đường dẫn gốc của dataset, thư mục ảnh train, thư mục ảnh validation, thư mục ảnh test, số lớp `nc: 1` và tên lớp `license_plate`. Cách tạo tự động giúp giảm lỗi gõ sai đường dẫn, đồng thời khiến notebook có thể tái chạy nếu người dùng chuyển dataset sang một thư mục khác nhưng giữ nguyên cấu trúc.

```yaml
path: /kaggle/input/datasets/triuthanhhng/vn-plate-lastpt-checkpoint/v58_merged_dataset_real
train: train/images
val: valid/images
test: test/images
names:
  0: license_plate
nc: 1
```

== Notebook huấn luyện lần đầu

Notebook đầu tiên được dùng làm mốc huấn luyện từ cấu hình mô hình, không nạp các checkpoint từ lần thử nghiệm trước như `last.pt`, `best.pt` hoặc `detector_used.pt`. Thiết lập chính của lần chạy này gồm 25 epoch, kích thước đầu vào 768, batch 16, learning rate ban đầu 0.006, cosine learning rate, mosaic augmentation 0.60 và đóng mosaic ở 5 epoch cuối. Thiết lập này phù hợp để mô hình học đặc trưng biển số từ dữ liệu mà vẫn có augmentation đủ mạnh ở giai đoạn đầu.

#tbl(
  table(
    columns: (5.0cm, 1fr),
    inset: 5pt,
    stroke: 0.45pt,
    [#cellhead[Thông số]], [#cellhead[Giá trị]],
    [Version], [`V60_SCRATCH_25E` / mốc báo cáo Ver62],
    [Mô hình], [`yolov9s.yaml`],
    [Epoch], [25],
    [Image size], [768],
    [Batch], [16],
    [Learning rate ban đầu], [0.006],
    [Mosaic], [0.60],
    [Close mosaic], [5 epoch cuối],
    [Seed], [22],
  ),
  [Cấu hình chính của notebook huấn luyện đầu tiên],
)

== Notebook huấn luyện tiếp từ checkpoint

Notebook thứ hai tiếp tục từ checkpoint `v62.pt`. Trong báo cáo, mốc này được xem là mốc huấn luyện tiếp sau Ver62; trong log có tên `V63_CONTINUE_25E_FROM_CHECKPOINT`, còn phần ghi chú nhóm gọi là Ver65. Điểm quan trọng về mặt kỹ thuật là notebook nạp checkpoint bằng `YOLO(checkpoint).train(...)` với `resume: false`, nghĩa là tạo một lượt huấn luyện tiếp mới từ trọng số đã có thay vì nối trực tiếp trạng thái optimizer của run cũ. Learning rate được hạ xuống 0.002 và mosaic giảm còn 0.35 để quá trình fine-tuning ổn định hơn.

#photo("assets/version_checkpoint_v65.png", [Thông số checkpoint và chế độ huấn luyện tiếp được ghi trong notebook], width: 100%)

#tbl(
  table(
    columns: (5.0cm, 1fr),
    inset: 5pt,
    stroke: 0.45pt,
    [#cellhead[Thông số]], [#cellhead[Giá trị]],
    [Version], [`V63_CONTINUE_25E_FROM_CHECKPOINT` / mốc báo cáo Ver65],
    [Checkpoint], [`v62.pt`],
    [Epoch thêm], [25],
    [Image size], [768],
    [Batch], [16],
    [Learning rate ban đầu], [0.002],
    [Mosaic], [0.35],
    [Close mosaic], [5 epoch cuối],
    [Seed], [22],
  ),
  [Cấu hình chính của notebook huấn luyện tiếp từ checkpoint],
)

== Quy trình OCR và chuẩn hóa kết quả

Sau khi YOLO trả về bounding box, vùng biển số được mở rộng nhẹ rồi cắt khỏi ảnh gốc. Crop BGR được đưa vào OCR. Phần mềm Python ưu tiên FastALPR DefaultOCR nếu có, nếu không thì dùng fast_plate_ocr như backend thay thế. Kết quả OCR được làm sạch bằng cách chỉ giữ chữ cái và chữ số, chuyển về chữ hoa, kiểm tra dạng biển số Việt Nam và tính điểm tin cậy tổng hợp từ detector confidence, OCR confidence và mức độ hợp lệ của chuỗi.

Các fallback được thiết kế để tăng tính ổn định khi demo: xoay crop 90/270 độ cho biển dọc, thử gamma cho ảnh tối, chia ảnh ghép hoặc ảnh nhiều biển thành vùng nhỏ, và dùng voting cho video. Tuy nhiên, nhóm tránh “sửa quá tay”, ví dụ không tự thêm ký tự đầu/cuối chỉ vì muốn biển số có vẻ hợp lệ. Cách này giúp kết quả demo trung thực hơn, nhất là khi trả lời vấn đáp về lỗi OCR.

== Kiểm thử phần mềm

Kiểm thử được chia thành ba nhóm. Nhóm thứ nhất kiểm thử trên ảnh đơn và ảnh trong thư mục để xem YOLO có phát hiện đủ biển số không. Nhóm thứ hai kiểm thử OCR trên các crop biển số rõ, mờ, nghiêng và có nhiều dòng. Nhóm thứ ba kiểm thử video để đánh giá độ ổn định khi khung hình thay đổi theo thời gian. Các hình minh họa trong chương sau được lấy từ ảnh kết quả notebook và phần mềm demo.
