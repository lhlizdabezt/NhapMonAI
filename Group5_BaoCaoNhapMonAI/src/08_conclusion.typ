#import "../config.typ": callout, tbl, cellhead, cell

= KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

== Kết quả đạt được

Đồ án đã xây dựng được pipeline nhận dạng biển số theo hướng end-to-end: phát hiện vùng biển số bằng YOLO, cắt vùng ảnh biển số, nhận dạng ký tự bằng OCR, chuẩn hóa chuỗi kết quả và triển khai phần mềm demo. Nhóm đã chuẩn bị notebook huấn luyện với hai mốc thực nghiệm, ghi nhận thống kê dữ liệu, kiểm tra định dạng nhãn, lưu biểu đồ loss/metric, log 5 epoch cuối của hai mốc huấn luyện và xuất kết quả định lượng phục vụ báo cáo. Mốc huấn luyện tiếp từ checkpoint đạt Precision 0.99448, Recall 0.99373, mAP50 0.99450 và mAP50-95 0.77006 trên tập validation. Ma trận nhầm lẫn cho thấy số lỗi bỏ sót biển số thấp, nhưng vẫn tồn tại một lượng nhỏ trường hợp vùng nền bị dự đoán thành biển số; vì vậy báo cáo diễn giải kết quả theo hướng thận trọng, không tuyệt đối hóa metric của detector.

Về phần mềm, nhóm có ứng dụng Python kiểm thử hỗ trợ ảnh đơn, thư mục ảnh và video; có các chế độ xử lý cho ảnh nhiều biển, ảnh khó và video; có xuất CSV, crop và ảnh/video chú thích. Bên cạnh đó, nhóm xây dựng thêm trạm kiểm soát Python và ứng dụng Android liên kết để minh họa kịch bản mở rộng: Android gửi kết quả nhận dạng qua mạng LAN, trạm PC đối chiếu danh sách biển số được phép và trả quyết định cho qua hoặc từ chối.

== Hạn chế

Hệ thống vẫn có một số hạn chế. Thứ nhất, detector metric cao chưa đồng nghĩa với OCR luôn đúng, vì OCR chịu ảnh hưởng bởi chất lượng crop, độ mờ, góc nghiêng và phản sáng. Thứ hai, các fallback trong ứng dụng giúp demo ổn định hơn nhưng có thể làm tăng thời gian xử lý. Thứ ba, mô hình được đánh giá chủ yếu trên bộ dữ liệu hiện có, chưa kiểm chứng đầy đủ trên camera thực tế với điều kiện ban đêm, mưa, rung lắc hoặc biển số bị che khuất. Thứ tư, ứng dụng Android hiện dừng ở mức minh họa demo, chưa tối ưu model trực tiếp trên thiết bị di động.

== Hướng phát triển

Các hướng phát triển hợp lý gồm:

- Bổ sung bộ dữ liệu thực tế từ nhiều camera, nhiều điều kiện ánh sáng và nhiều góc chụp.
- Đánh giá end-to-end bằng chỉ số đọc đúng toàn bộ biển số, không chỉ metric phát hiện bounding box.
- Huấn luyện hoặc fine-tune OCR riêng cho biển số Việt Nam, đặc biệt cho biển xe máy hai dòng.
- Tối ưu model sang ONNX/TensorRT hoặc TFLite để tăng tốc suy luận.
- Cải thiện ứng dụng Android và trạm kiểm soát Python theo hướng giao tiếp HTTPS, xác thực thiết bị và cấu hình mạng ổn định hơn.
- Thêm cơ chế tìm kiếm biển số, lọc lịch sử và xuất báo cáo theo phiên demo.

== Kết luận chung

Đồ án phù hợp với mục tiêu học phần vì thể hiện được đầy đủ chuỗi công việc của một bài toán AI ứng dụng: hiểu bài toán, chuẩn bị dữ liệu, huấn luyện mô hình, đánh giá bằng metric, triển khai phần mềm và trình bày kết quả. Mức kết quả hiện tại đáp ứng mục tiêu trình bày cuối kỳ; phần rà soát mã nguồn FastALPR giúp nhóm giải thích pipeline theo đúng luồng detector-crop-OCR thay vì chỉ mô tả ở mức giao diện, đồng thời báo cáo vẫn giữ các giới hạn rõ ràng để phục vụ phần vấn đáp và tránh diễn giải quá mức so với dữ liệu kiểm thử. Nếu tiếp tục phát triển, nhóm nên ưu tiên đánh giá end-to-end trên dữ liệu ngoài và tối ưu OCR cho biển số Việt Nam.
