#import "../config.typ": callout, tbl, cellhead, cell

= GIỚI THIỆU ĐỀ TÀI

== Bối cảnh và lý do chọn đề tài

Biển số phương tiện là một dạng thông tin ngắn nhưng có giá trị nhận dạng rất cao trong các hệ thống giao thông, bãi giữ xe, kiểm soát ra vào và quản lý an ninh. Trong thực tế, con người có thể đọc biển số tương đối nhanh khi ảnh rõ, nhưng hệ thống tự động lại gặp nhiều khó khăn vì biển số có thể nhỏ, nghiêng, mờ, bị che một phần, bị phản sáng hoặc xuất hiện trong khung hình có nhiều vật thể tương tự. Vì vậy, bài toán nhận dạng biển số không đơn giản là “đọc chữ trên ảnh”, mà cần một pipeline gồm phát hiện vùng biển số trước, sau đó mới nhận dạng ký tự bên trong vùng đã cắt.

Trong học phần Nhập môn Trí tuệ nhân tạo, đề tài này phù hợp vì kết hợp được nhiều nội dung cốt lõi: dữ liệu huấn luyện, mô hình học sâu, đánh giá bằng metric định lượng, xử lý ảnh, triển khai phần mềm và demo kết quả. Nếu chỉ dừng ở việc tìm hiểu lý thuyết YOLO hoặc OCR thì đồ án sẽ thiếu phần thực nghiệm. Vì vậy, nhóm 05 triển khai theo hướng hoàn chỉnh: có notebook huấn luyện, có số liệu train/validation, có ảnh minh họa, có ứng dụng Python kiểm thử thuật toán, có trạm kiểm soát Python, có ứng dụng Android liên kết với trạm và có video minh họa để trình bày trong thời lượng quy định.

== Phát biểu bài toán

Bài toán của đồ án được phát biểu như sau: với đầu vào là ảnh hoặc video chứa phương tiện, hệ thống cần phát hiện vị trí biển số, cắt vùng biển số, nhận dạng chuỗi ký tự và hiển thị kết quả trên ảnh/video đầu ra. Đầu ra của hệ thống gồm bounding box vùng biển số, độ tin cậy phát hiện, chuỗi ký tự OCR, độ tin cậy OCR, ảnh hoặc video đã chú thích, và tệp CSV tổng hợp kết quả nếu chạy trên nhiều ảnh.

#callout([Mục tiêu thực hiện], [
  Trọng tâm của đồ án không phải là xây dựng một sản phẩm thương mại hoàn chỉnh, mà là chứng minh quy trình AI end-to-end: dữ liệu → huấn luyện → đánh giá → suy luận → phần mềm demo. Báo cáo vì vậy ưu tiên giải thích các bước nhóm đã làm, các thông số chính, các kết quả đạt được và các giới hạn cần nêu khi vấn đáp.
])

== Mục tiêu của đồ án

Các mục tiêu chính của nhóm gồm:

- Chuẩn bị và kiểm tra bộ dữ liệu Vietnamese License Plates Detection theo định dạng YOLO.
- Huấn luyện mô hình phát hiện biển số bằng YOLO, có hai mốc kết quả để so sánh.
- Kết hợp mô hình phát hiện với OCR để đọc ký tự trên vùng biển số đã cắt.
- Xây dựng notebook có thể tái chạy trên môi trường Kaggle hoặc môi trường tương đương.
- Xây dựng ứng dụng Python kiểm thử hỗ trợ ảnh đơn, thư mục ảnh và video.
- Xây dựng trạm kiểm soát Python và ứng dụng Android liên kết để minh họa kịch bản kiểm soát ra/vào.

== Phạm vi và giới hạn

Phạm vi của đồ án tập trung vào biển số phương tiện Việt Nam trong dữ liệu ảnh và video phục vụ demo. Mô hình phát hiện chỉ học một lớp đối tượng là vùng biển số. Phần OCR được triển khai theo hướng sử dụng mô hình OCR có sẵn, sau đó nhóm bổ sung bước chuẩn hóa chuỗi, kiểm tra mã tỉnh, xử lý biển một dòng/hai dòng và lọc nhiễu trong phần mềm. Báo cáo không khẳng định hệ thống đã đạt chuẩn vận hành ngoài thực tế với mọi camera, mọi thời tiết và mọi góc nhìn.

Một số giới hạn cần nêu rõ gồm:

- Ảnh biển số quá nhỏ hoặc bị nhòe mạnh có thể được YOLO phát hiện nhưng OCR đọc sai.
- Ảnh bãi xe có nhiều ký tự nền, mã ô đậu xe hoặc biển quảng cáo dễ gây nhiễu cho OCR.
- Dữ liệu validation có độ tương đồng nhất định với dữ liệu huấn luyện nên metric cao cần được hiểu trong phạm vi bộ dữ liệu hiện tại.
- Phần mềm demo ưu tiên tính ổn định khi trình bày, chưa tối ưu tốc độ như một hệ thống nhúng thời gian thực.

== Cấu trúc báo cáo

Báo cáo gồm năm chương. Chương 1 giới thiệu đề tài, bối cảnh, mục tiêu và phạm vi. Chương 2 trình bày cơ sở lý thuyết liên quan đến ALPR, YOLO, OCR và metric đánh giá. Chương 3 mô tả dữ liệu, notebook, cấu hình huấn luyện và quy trình thực hiện. Chương 4 phân tích kết quả huấn luyện, so sánh hai mốc checkpoint và nhận xét metric. Chương 5 trình bày ứng dụng Python kiểm thử, trạm kiểm soát Python, Android liên kết và pipeline video. Phần cuối là kết luận và tài liệu tham khảo.
