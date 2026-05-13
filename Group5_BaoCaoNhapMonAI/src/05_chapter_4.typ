#import "../config.typ": callout, tbl, cellhead, cell, photo

= HUẤN LUYỆN MÔ HÌNH VÀ ĐÁNH GIÁ KẾT QUẢ

== Nguyên tắc đọc kết quả huấn luyện

Theo định hướng đánh giá thực nghiệm trong lĩnh vực trí tuệ nhân tạo, kết quả của mô hình không nên được kết luận chỉ bằng một chỉ số đơn lẻ. Báo cáo cần đọc đồng thời các nhóm thông tin gồm loss huấn luyện, loss kiểm chứng, Precision, Recall, mAP, ma trận nhầm lẫn và kết quả minh họa trực quan. Theo cách đánh giá thường dùng trong các hệ thống object detection và YOLO @redmon_yolo, @ultralytics_metrics, Precision phản ánh mức độ hạn chế dự đoán nhầm vùng nền thành biển số, Recall phản ánh khả năng không bỏ sót biển số thật, còn mAP50-95 đánh giá chất lượng khung phát hiện ở nhiều ngưỡng IoU khắt khe hơn. Vì đầu ra của detector còn được dùng làm đầu vào cho OCR, chất lượng bounding box có ảnh hưởng trực tiếp đến khả năng đọc đúng chuỗi ký tự biển số.

#callout([Nguyên tắc diễn giải kết quả], [
  Báo cáo xem các chỉ số định lượng là bằng chứng chính, nhưng không tuyệt đối hóa metric. Một mô hình có Precision, Recall và mAP cao vẫn cần được đối chiếu với ma trận nhầm lẫn, ảnh demo và kết quả OCR, vì mục tiêu cuối cùng của hệ thống là nhận dạng đúng biển số trong pipeline end-to-end, không chỉ phát hiện được vùng ảnh nghi ngờ là biển số.
])

== Diễn biến huấn luyện mốc Ver62

Mốc Ver62 được xem là thí nghiệm nền vì mô hình được huấn luyện từ đầu, không nạp lại checkpoint của các lần thử nghiệm trước. Biểu đồ kết quả cho thấy các thành phần loss chính giảm theo số epoch: box loss giảm dần, classification loss ổn định hơn ở giai đoạn cuối và DFL loss tiếp tục được cải thiện. Các chỉ số Precision, Recall và mAP50 nhanh chóng đạt vùng giá trị cao, trong khi mAP50-95 tăng chậm hơn do chỉ số này yêu cầu bounding box khít hơn với nhãn ground truth.

#photo("assets/results_scratch_v62.png", [Biểu đồ loss và metric của mốc huấn luyện Ver62 từ notebook đầu tiên], width: 100%)

#photo("assets/25EpochFirstCheckpoint.png", [Log 5 epoch cuối của mốc huấn luyện Ver62, thể hiện xu hướng hội tụ của loss và độ ổn định của metric validation], width: 100%)

#tbl(
  table(
    columns: (4.0cm, 2.0cm, 2.2cm, 2.2cm, 2.2cm, 2.4cm),
    inset: 4.5pt,
    stroke: 0.45pt,
    [#cellhead[Mốc chọn]], [#cellhead[Epoch]], [#cellhead[Precision]], [#cellhead[Recall]], [#cellhead[mAP50]], [#cellhead[mAP50-95]],
    [Last epoch], [25], [0.99332], [0.99271], [0.99439], [0.76497],
    [Best by mAP50-95], [25], [0.99332], [0.99271], [0.99439], [0.76497],
  ),
  [Kết quả định lượng của mốc Ver62],
)

Từ góc nhìn thực nghiệm, epoch 25 đồng thời là epoch tốt nhất theo mAP50-95. Điều này cho thấy quá trình huấn luyện 25 epoch chưa xuất hiện dấu hiệu suy giảm rõ rệt trên tập validation theo metric chính. Precision và mAP50 đạt mức cao, trong khi mAP50-95 thấp hơn do đây là chỉ số khắt khe hơn về độ khít của bounding box. Với pipeline OCR phía sau, nhận xét này có ý nghĩa quan trọng: bounding box càng ổn định và sát vùng biển số thì ảnh crop càng ít chứa nền dư, từ đó giảm nguy cơ OCR đọc nhầm ký tự.

== Diễn biến huấn luyện mốc tiếp tục từ checkpoint

Ở thí nghiệm tiếp tục từ checkpoint, mô hình được khởi tạo từ trọng số đã học ở mốc trước nên quá trình fine-tuning được thực hiện với learning rate thấp hơn để tránh làm thay đổi mạnh các đặc trưng đã ổn định. So với mốc huấn luyện đầu tiên, một số thành phần loss ở cuối quá trình thấp hơn và mAP50-95 tăng từ khoảng 0.765 lên 0.770. Mức tăng này không lớn về mặt tuyệt đối, nhưng có ý nghĩa thực nghiệm vì mAP50-95 là metric khắt khe, phản ánh tốt hơn chất lượng định vị bounding box.

#photo("assets/results_continue_v65.png", [Biểu đồ loss và metric của mốc huấn luyện tiếp từ checkpoint], width: 100%)

#photo("assets/25EpochContiniousCheckpoint.png", [Log 5 epoch cuối của mốc huấn luyện tiếp từ checkpoint, cho thấy Precision, Recall và mAP duy trì ổn định ở vùng giá trị cao], width: 100%)


#tbl(
  table(
    columns: (4.0cm, 2.0cm, 2.2cm, 2.2cm, 2.2cm, 2.4cm),
    inset: 4.5pt,
    stroke: 0.45pt,
    [#cellhead[Mốc chọn]], [#cellhead[Epoch]], [#cellhead[Precision]], [#cellhead[Recall]], [#cellhead[mAP50]], [#cellhead[mAP50-95]],
    [Last epoch], [25], [0.99448], [0.99373], [0.99450], [0.77006],
    [Best by mAP50-95], [25], [0.99448], [0.99373], [0.99450], [0.77006],
  ),
  [Kết quả định lượng của mốc huấn luyện tiếp],
)

Log 5 epoch cuối cho thấy box loss, class loss và DFL loss tiếp tục giảm nhẹ, trong khi Precision, Recall và mAP50 duy trì quanh vùng 0.994. Kết quả này cho thấy mô hình không dao động mạnh ở giai đoạn cuối của fine-tuning, đồng thời vẫn giữ được khả năng tổng quát hóa trên tập validation. mAP50-95 đạt khoảng 0.770, thấp hơn mAP50 vì chỉ số này yêu cầu khung dự đoán khớp với ground truth ở nhiều ngưỡng IoU từ dễ đến khó.

== So sánh hai mốc huấn luyện

#tbl(
  table(
    columns: (2.8cm, 2.35cm, 1.9cm, 1.9cm, 2.35cm, 4.6cm),
    inset: 4.5pt,
    stroke: 0.45pt,
    [#cellhead[Run]], [#cellhead[Precision]], [#cellhead[Recall]], [#cellhead[mAP50]], [#cellhead[mAP50-95]], [#cellhead[Nhận xét]],
    [Ver62 scratch], [0.99332], [0.99271], [0.99439], [0.76497], [#cell[Mốc nền, không nạp checkpoint từ lần thử nghiệm trước.]],
    [Ver65/V63 continue], [0.99448], [0.99373], [0.99450], [0.77006], [#cell[Cải thiện nhẹ ở cả Precision, Recall và mAP50-95.]],
    [Chênh lệch], [+0.00116], [+0.00102], [+0.00011], [+0.00509], [#cell[Cải thiện rõ nhất ở mAP50-95, tức chất lượng khung phát hiện khắt khe hơn.]],
  ),
  [So sánh kết quả giữa hai mốc huấn luyện],
)

Kết quả cho thấy mốc huấn luyện tiếp tốt hơn mốc đầu ở tất cả metric chính, nhưng mức tăng cần được diễn giải thận trọng vì mốc Ver62 ban đầu đã đạt vùng hiệu năng rất cao. Sự cải thiện Precision và Recall nhỏ vì mốc đầu đã đạt mức rất cao. Chênh lệch đáng chú ý nhất nằm ở mAP50-95, tăng 0.00509, tức mô hình cải thiện chủ yếu ở mức độ khít của bounding box thay vì chỉ tăng số lượng phát hiện đúng ở ngưỡng IoU dễ. Trong bối cảnh phát hiện biển số, cải thiện này có ý nghĩa vì OCR phụ thuộc nhiều vào chất lượng crop. Một box phát hiện đúng nhưng lệch nhiều có thể vẫn được tính đúng ở IoU 0.50, nhưng khi đưa vào OCR thì nền thừa hoặc mất một phần ký tự sẽ làm giảm độ chính xác đọc biển.

#callout([Giải thích điểm “checkpoint”], [
  Hai hình kết quả có thể nhìn giống nhau vì đều là đồ thị loss/metric của YOLO sau 25 epoch. Khác biệt nằm ở trạng thái khởi tạo: mốc Ver62 chạy theo hướng không nạp checkpoint từ lần thử nghiệm trước; mốc Ver65/V63 nạp checkpoint `v62.pt` rồi huấn luyện tiếp với learning rate thấp hơn. Vì vậy, báo cáo mô tả rõ đây là hai mốc thực nghiệm khác nhau, không phải hai file kết quả bị trùng.
])

== Phân tích ma trận nhầm lẫn

Ma trận nhầm lẫn giúp đọc rõ hơn bản chất lỗi của detector. Với lớp chính `license_plate`, ô đường chéo thể hiện số trường hợp mô hình dự đoán đúng biển số. Các ô ngoài đường chéo thể hiện lỗi báo nhầm hoặc bỏ sót. Trong bài toán phát hiện đối tượng, cột/hàng `background` không nên được hiểu giống hoàn toàn với bài toán phân loại nhị phân thông thường vì số lượng nền thật không được đếm như một tập negative độc lập; nó chủ yếu biểu diễn unmatched prediction hoặc unmatched ground truth.

#photo("assets/confusion_matrix.png", [Ma trận nhầm lẫn dạng số đếm của detector biển số], width: 92%)

Từ ma trận số đếm, có thể đọc được 8.451 trường hợp biển số được dự đoán đúng, 63 trường hợp nền hoặc vùng không khớp nhãn bị dự đoán thành biển số và 12 trường hợp biển số thật bị đưa về background. Nếu tính gần đúng theo lớp `license_plate`, ta có:

#tbl(
  table(
    columns: (4.4cm, 4.5cm, 1fr),
    inset: 4.5pt,
    stroke: 0.45pt,
    [#cellhead[Đại lượng]], [#cellhead[Công thức]], [#cellhead[Giá trị xấp xỉ]],
    [$"TP"$], [$8451$], [#cell[Số biển số được phát hiện đúng.]],
    [$"FP"$], [$63$], [#cell[Số dự đoán biển số nhưng không khớp biển số thật.]],
    [$"FN"$], [$12$], [#cell[Số biển số thật bị bỏ sót.]],
    [Precision theo ma trận], [$frac(8451, 8451 + 63)$], [$0.9926$],
    [Recall theo ma trận], [$frac(8451, 8451 + 12)$], [$0.9986$],
  ),
  [Tính nhanh Precision và Recall từ ma trận nhầm lẫn],
)

Hai giá trị tính nhanh từ ma trận có thể lệch nhẹ so với bảng metric YOLO vì cách tổng hợp kết quả phụ thuộc ngưỡng confidence, ngưỡng IoU và quy tắc matching của thư viện đánh giá. Tuy vậy, xu hướng chung vẫn nhất quán: mô hình có khả năng phát hiện biển số rất cao, số lỗi bỏ sót nhỏ, còn lỗi báo nhầm nền vẫn cần được theo dõi khi triển khai ngoài dữ liệu validation.

#photo("assets/confusion_matrix_normalized.png", [Ma trận nhầm lẫn chuẩn hóa của detector biển số], width: 92%)

Ma trận chuẩn hóa giúp quan sát tỷ lệ lỗi theo từng cột nhãn thật. Giá trị 1.00 ở ô `license_plate` không nên được diễn giải máy móc là mô hình tuyệt đối đúng trong mọi trường hợp; nó là kết quả làm tròn khi tỷ lệ đúng của lớp biển số rất cao. Cột `background` cho thấy các dự đoán nhầm nền thành biển số vẫn tồn tại, vì vậy khi demo cần giữ các bước lọc hậu xử lý như kiểm tra chuỗi biển số hợp lệ, ngưỡng confidence và loại bỏ các vùng ký tự nền quá ngắn.

== Nhận xét về độ tin cậy của kết quả

Metric validation cao là tín hiệu tích cực nhưng không nên hiểu là hệ thống sẽ luôn đọc đúng mọi biển số ngoài đời. Detector chỉ đánh giá vùng biển số, chưa đánh giá toàn bộ chuỗi OCR. Nếu YOLO phát hiện đúng nhưng OCR nhầm ký tự, kết quả cuối vẫn sai. Ngược lại, nếu OCR mạnh nhưng detector bỏ sót hoặc crop lệch thì OCR không có đầu vào tốt. Vì vậy, phần demo phần mềm và hình ảnh OCR trong chương 5 là cần thiết để chứng minh pipeline hoạt động end-to-end chứ không chỉ có metric detection.

== Kết quả demo từ notebook

Notebook có các hình preview để kiểm tra trực quan việc phát hiện biển số và OCR. Một số ảnh cho thấy bounding box bám tương đối sát vùng biển số, OCR đọc được chuỗi hợp lệ. Một số trường hợp khác minh họa khó khăn của ảnh thực tế: biển nghiêng, ảnh nhỏ hoặc nhiều đối tượng xung quanh. Việc đưa các hình này vào báo cáo giúp phần kết quả có minh chứng trực quan cho pipeline, đồng thời hỗ trợ liên hệ giữa chỉ số định lượng và hiệu năng thực tế của hệ thống trong bài toán ALPR end-to-end.

#figure(
  align(center)[
    #grid(
      columns: (1fr, 1fr),
      gutter: 8pt,
      [#image("../assets/yolo_demo_02.png", width: 100%, height: 4.4cm, fit: "contain")],
      [#image("../assets/yolo_demo_03.png", width: 100%, height: 4.4cm, fit: "contain")],
      [#image("../assets/ocr_demo_01.png", width: 100%, height: 4.4cm, fit: "contain")],
      [#image("../assets/ocr_demo_02.png", width: 100%, height: 4.4cm, fit: "contain")],
    )
  ],
  kind: image,
  caption: [Một số kết quả demo YOLO và OCR từ notebook],
)
