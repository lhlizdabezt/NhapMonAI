#import "../config.typ": callout, tbl, cellhead, cell

= CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN

== Bài toán nhận dạng biển số tự động

Nhận dạng biển số tự động, thường gọi là ALPR, có thể chia thành ba bài toán con. Bài toán thứ nhất là phát hiện vùng biển số trong ảnh. Bài toán thứ hai là tiền xử lý vùng ảnh đã cắt để giảm nhiễu, làm rõ ký tự và chuẩn hóa kích thước. Bài toán thứ ba là nhận dạng chuỗi ký tự trên biển số bằng OCR. Trong đồ án, YOLO đảm nhiệm phần phát hiện, còn OCR đảm nhiệm phần đọc chuỗi ký tự. Cách tách này giúp hệ thống dễ kiểm thử hơn: nếu biển số bị phát hiện sai vị trí thì lỗi nằm ở detector; nếu vùng biển số đã cắt đúng nhưng đọc sai thì lỗi nằm ở OCR hoặc tiền xử lý.

Các hệ thống ALPR truyền thống thường dùng đặc trưng thủ công như cạnh, hình chữ nhật, ngưỡng màu hoặc phân đoạn ký tự. Cách này có thể chạy nhanh nhưng nhạy với điều kiện ánh sáng và góc chụp. Hướng học sâu hiện đại học trực tiếp đặc trưng từ dữ liệu, nhờ vậy phù hợp hơn với ảnh thực tế có nền phức tạp. Tuy nhiên, học sâu cần dữ liệu gán nhãn tốt, quy trình đánh giá rõ ràng và cơ chế kiểm soát overfitting.

== Mô hình YOLO trong phát hiện đối tượng

YOLO là họ mô hình phát hiện đối tượng một giai đoạn, được giới thiệu theo hướng phát hiện thời gian thực và sau đó phát triển qua nhiều biến thể tối ưu tốc độ/độ chính xác @redmon_yolo @bochkovskiy_yolov4. Thay vì tách riêng bước đề xuất vùng và bước phân loại như một số kiến trúc hai giai đoạn, YOLO dự đoán trực tiếp bounding box và xác suất lớp trên ảnh đầu vào. Điểm mạnh của YOLO là tốc độ suy luận nhanh, cấu trúc triển khai gọn và có hệ sinh thái công cụ huấn luyện tương đối thuận tiện. Đối với bài toán biển số, YOLO chỉ cần học một lớp đối tượng nên phần phân loại không phức tạp; khó khăn chính nằm ở việc biển số có kích thước nhỏ, tỷ lệ dài/hẹp, có thể nghiêng và thường bị ảnh hưởng bởi ánh sáng.

Trong notebook của nhóm, detector được huấn luyện với lớp duy nhất là `license_plate`. Mô hình được đánh giá bằng các metric phổ biến trong phát hiện đối tượng: Precision, Recall, mAP50 và mAP50-95. Việc dùng nhiều metric giúp tránh kết luận vội dựa trên một chỉ số duy nhất. Ví dụ, Precision cao cho thấy ít false positive, nhưng nếu Recall thấp thì mô hình vẫn bỏ sót nhiều biển số; mAP50-95 khó hơn mAP50 vì yêu cầu chất lượng khung phát hiện tốt ở nhiều ngưỡng IoU.

== OCR cho biển số phương tiện

OCR trong bài toán biển số khác với OCR tài liệu; về mặt mô hình chuỗi ký tự, các hướng CNN/RNN/CTC như CRNN là nền tảng quan trọng để hiểu cách nhận dạng text trong ảnh @shi_crnn. Ảnh biển số thường có ít ký tự, nhưng ký tự có thể dính, bị nghiêng, phản sáng, mờ hoặc bị mất nét do nén video. Ngoài ra, biển số Việt Nam có các cấu trúc khác nhau giữa ô tô, xe máy, biển một dòng và hai dòng. Vì vậy, phần OCR trong đồ án không chỉ gọi mô hình nhận dạng rồi in kết quả, mà còn cần bước chuẩn hóa chuỗi, lọc ký tự không hợp lệ, kiểm tra mã tỉnh và lựa chọn kết quả tốt nhất giữa các biến thể xử lý ảnh.

Nhóm sử dụng hướng FastALPR DefaultOCR và có tùy chọn fast_plate_ocr trong phần mềm Python @fastalpr. Để tránh làm sai dữ liệu khi demo, quy tắc chuẩn hóa được thiết kế theo hướng bảo thủ: không tự động thêm ký tự đầu hoặc cuối nếu OCR không đọc được; ưu tiên giữ chuỗi OCR gốc đã làm sạch; chỉ áp dụng những hiệu chỉnh nhẹ liên quan đến dạng biển số hợp lệ.


== Liên hệ mã nguồn FastALPR với mô hình toán học

Khi rà soát mã nguồn FastALPR, nhóm nhận thấy thư viện không viết trực tiếp các phép biến đổi ma trận hoặc tích phân trong mã Python cấp cao. Phần mã nguồn chủ yếu đóng vai trò ghép nối các khối đã huấn luyện: detector phát hiện biển số, bước cắt vùng ảnh, OCR nhận dạng ký tự và bước trả kết quả có cấu trúc. Tuy vậy, cách triển khai này vẫn có thể diễn giải học thuật bằng mô hình tensor ảnh và phép ánh xạ theo pipeline @fastalpr.

Xét ảnh đầu vào $I$ như một tensor ảnh màu kích thước $H times W times 3$. Detector trả về tập kết quả $D(I) = {(b_i, s_i)}$, trong đó $b_i = (x_1, y_1, x_2, y_2)$ là bounding box và $s_i$ là độ tin cậy phát hiện. Source FastALPR sau đó chặn tọa độ để không vượt biên ảnh, rồi cắt vùng biển số theo chỉ số ma trận ảnh:

#tbl(
  table(
    columns: (4.1cm, 1fr),
    inset: 5pt,
    stroke: 0.45pt,
    [#cellhead[Thành phần]], [#cellhead[Diễn giải học thuật]],
    [Ảnh đầu vào], [#cell[$I in RR^(H times W times 3)$, với $H$ và $W$ lần lượt là chiều cao và chiều rộng ảnh.]],
    [Detector], [#cell[$D(I) = {(b_i, s_i)}$; mỗi $b_i$ là một vùng nghi ngờ chứa biển số, $s_i$ là confidence của detector.]],
    [Chặn biên ảnh], [#cell[$x'_1 = max(x_1, 0)$, $y'_1 = max(y_1, 0)$, $x'_2 = min(x_2, W)$, $y'_2 = min(y_2, H)$.]],
    [Crop biển số], [#cell[$C_i = I[y'_1 : y'_2, x'_1 : x'_2]$; đây là phép lấy lát cắt trên ma trận ảnh.]],
    [OCR], [#cell[$"OCR"(C_i) arrow (t_i, p_1, ..., p_n)$, trong đó $t_i$ là chuỗi ký tự và $p_k$ là độ tin cậy từng ký tự.]],
    [Confidence OCR], [#cell[$"conf"_"OCR" = frac(1, n) sum_(k=1)^n p_k$. Source FastALPR dùng trung bình các confidence ký tự khi OCR trả về một danh sách xác suất.]],
  ),
  [Diễn giải toán học phù hợp với luồng detector-crop-OCR trong FastALPR],
)

Điểm quan trọng là báo cáo không cần gán thêm các phép toán không xuất hiện trong bài toán, chẳng hạn tích phân liên tục. Với bài toán này, phần “toán” hợp lý nhất là mô hình ảnh như tensor, phép cắt ma trận theo bounding box, các xác suất ký tự của OCR và các metric đánh giá detector như Precision, Recall, IoU, mAP. Cách trình bày này đủ học thuật nhưng vẫn bám sát mã nguồn, giúp nhóm trả lời vấn đáp tốt hơn khi giảng viên hỏi vì sao crop biển số, confidence OCR và hậu xử lý chuỗi lại ảnh hưởng đến kết quả cuối.

#callout([Ý nghĩa đưa vào báo cáo], [
  Phần mã nguồn FastALPR nên được dùng để làm rõ tính đúng đắn của pipeline, không nên phóng đại thành một mô hình toán học quá phức tạp. Nội dung phù hợp nhất để đưa vào báo cáo là: detector sinh bounding box, crop là phép lấy lát cắt ảnh, OCR sinh chuỗi ký tự kèm confidence từng ký tự, và confidence cuối có thể lấy trung bình hoặc kết hợp với score detector trong phần mềm demo.
])

== Tiền xử lý ảnh và hậu xử lý chuỗi

Tiền xử lý ảnh có mục đích làm tăng khả năng OCR đọc đúng vùng biển số. Một số thao tác dùng trong demo gồm chuyển đổi màu, cân bằng histogram, phóng to vùng cắt, làm mờ nhẹ và ngưỡng Otsu cho trường hợp cần debug. Tuy nhiên, không phải lúc nào tiền xử lý mạnh cũng tốt. Một mô hình OCR đã được huấn luyện trên ảnh màu hoặc ảnh xám tự nhiên có thể hoạt động tốt hơn khi nhận crop BGR bình thường. Vì vậy, ứng dụng Python ưu tiên đưa crop BGR trực tiếp cho OCR theo đúng hành vi của backend, chỉ dùng biến thể tiền xử lý như một hướng thử bổ sung.

Hậu xử lý chuỗi gồm các bước làm sạch ký tự, kiểm tra dạng biển, tính độ tin cậy và bỏ các kết quả gây nhiễu. Ví dụ, mã ô đậu xe như D28, D29 hoặc chuỗi quá ngắn không nên được hiển thị như biển số. Với video, kết quả OCR từng frame có thể dao động nên app dùng voting hoặc smoothing để giữ kết quả ổn định hơn.

== Các metric đánh giá

#tbl(
  table(
    columns: (3.0cm, 1fr),
    inset: 5pt,
    stroke: 0.45pt,
    [#cellhead[Metric]], [#cellhead[Ý nghĩa]],
    [Precision], [#cell[Tỷ lệ phát hiện đúng trong số các khung mà mô hình dự đoán. Precision cao nghĩa là ít dự đoán nhầm.]],
    [Recall], [#cell[Tỷ lệ đối tượng thật được mô hình phát hiện. Recall cao nghĩa là ít bỏ sót biển số.]],
    [mAP50], [#cell[Mean Average Precision tại ngưỡng IoU 0.50. Đây là chỉ số tương đối dễ hơn, phản ánh khả năng phát hiện đúng vị trí ở mức chấp nhận được.]],
    [mAP50-95], [#cell[Trung bình AP trên nhiều ngưỡng IoU từ 0.50 đến 0.95. Đây là chỉ số khó hơn vì yêu cầu bounding box chính xác hơn.]],
    [Loss], [#cell[Hàm mất mát trong quá trình huấn luyện, gồm box loss, classification loss và distribution focal loss. Loss giảm ổn định là dấu hiệu quá trình học diễn ra hợp lý.]],
  ),
  [Ý nghĩa các chỉ số đánh giá được dùng trong đồ án],
)


Các chỉ số phân loại được hiểu từ các đại lượng cơ bản gồm TP (True Positive), FP (False Positive) và FN (False Negative). Với lớp `license_plate`, TP là trường hợp biển số thật được dự đoán đúng là biển số; FP là trường hợp nền hoặc vùng không phải biển số nhưng bị dự đoán là biển số; FN là trường hợp có biển số thật nhưng mô hình bỏ sót. Các công thức sử dụng trong phần phân tích kết quả được viết như sau:

#tbl(
  table(
    columns: (4.0cm, 1fr),
    inset: 5pt,
    stroke: 0.45pt,
    [#cellhead[Chỉ số]], [#cellhead[Công thức và ý nghĩa]],
    [Precision], [#cell[$"Precision" = frac("TP", "TP" + "FP")$. Chỉ số này phản ánh mức độ ít báo nhầm vùng nền thành biển số.]],
    [Recall], [#cell[$"Recall" = frac("TP", "TP" + "FN")$. Chỉ số này phản ánh mức độ ít bỏ sót biển số thật.]],
    [F1-score], [#cell[$F_1 = frac(2 dot "Precision" dot "Recall", "Precision" + "Recall")$. Chỉ số này cân bằng giữa Precision và Recall.]],
    [IoU], [#cell[$"IoU" = frac("Area"("box"_"pred" inter "box"_"true"), "Area"("box"_"pred" union "box"_"true"))$. IoU càng cao thì bounding box càng khít với nhãn thật.]],
  ),
  [Các công thức đánh giá cơ bản dùng trong phân tích detector],
)

== Công nghệ triển khai

Đồ án dùng Python làm môi trường chính cho huấn luyện và triển khai demo. Thư viện Ultralytics được dùng cho YOLO, OpenCV dùng xử lý ảnh/video, pandas dùng lưu kết quả CSV, Tkinter dùng giao diện desktop, FFMPEG dùng mã hóa video đầu ra, FastALPR hoặc fast_plate_ocr dùng nhận dạng ký tự. Bên cạnh ứng dụng Python kiểm thử thuật toán, nhóm xây dựng thêm trạm kiểm soát Python nhận dữ liệu từ Android qua mạng LAN để minh họa kịch bản ra quyết định. Cách triển khai này giúp nhóm có đủ ba lớp kết quả: notebook định lượng, phần mềm kiểm thử mô hình và phần mềm mở rộng gần với tình huống ứng dụng.

#callout([Nhận xét chọn công nghệ], [
  Nhóm không đặt mục tiêu đưa toàn bộ pipeline lên thiết bị nhúng hoặc điện thoại ở mức production. Với phạm vi môn Nhập môn trí tuệ nhân tạo, hướng hợp lý là huấn luyện và đánh giá mô hình rõ ràng trước, sau đó xây dựng demo phần mềm đủ ổn định để chứng minh khả năng ứng dụng.
])
