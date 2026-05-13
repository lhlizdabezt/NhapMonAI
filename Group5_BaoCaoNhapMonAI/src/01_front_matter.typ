#import "../config.typ": meta, members, centered_title, outline_entry, tbl, cellhead, cell

#let group_signature() = [
  #v(1.0cm)
  #align(right)[
    #block(width: 5.4cm)[
      #align(center)[#text(12pt, style: "italic")[Đại diện nhóm 05]]
      #v(1.3cm)
      #align(center)[#text(12.5pt, weight: "bold")[Lương Hải Long]]
    ]
  ]
]

#let acknowledgement_page() = [
  #outline_entry([Lời cảm ơn])
  #centered_title([LỜI CẢM ƠN])
  Nhóm 05 xin gửi lời cảm ơn đến TS. Đặng Lê Khoa, ThS. Nguyễn Thái Công Nghĩa và CN. Nguyễn Dũng đã phụ trách học phần Nhập môn Trí tuệ nhân tạo, định hướng quy trình thực hiện đồ án và góp ý để nhóm hoàn thiện hồ sơ nộp bài. Những góp ý trong quá trình học giúp nhóm hiểu rõ rằng báo cáo không chỉ trình bày kết quả, mà còn phải thể hiện được quy trình thực hiện, minh chứng demo và khả năng giải thích pipeline kỹ thuật.

  Nhóm cũng cảm ơn Khoa Điện tử - Viễn thông, Trường Đại học Khoa học Tự nhiên - ĐHQG TP.HCM đã cung cấp môi trường học tập giúp sinh viên tiếp cận các bài toán thị giác máy tính, học sâu và triển khai phần mềm. Trong quá trình thực hiện, các thành viên đã cùng chuẩn bị dữ liệu, huấn luyện mô hình, kiểm tra kết quả, xây dựng phần mềm demo và hoàn thiện báo cáo. Báo cáo này được viết theo hướng cô đọng nhưng đầy đủ, hạn chế phần lý thuyết xa đề và tập trung vào những nội dung nhóm trực tiếp thực hiện.

  #group_signature()
  #pagebreak()
]

#let commitment_page() = [
  #outline_entry([Cam kết tính trung thực])
  #centered_title([CAM KẾT TÍNH TRUNG THỰC])
  Nhóm 05 cam kết các nội dung trình bày trong báo cáo là kết quả tổng hợp từ quá trình thực hiện đồ án cuối kỳ môn Nhập môn Trí tuệ nhân tạo. Các số liệu huấn luyện, hình ảnh minh họa và phần mô tả phần mềm được trình bày dựa trên notebook, mã nguồn và dữ liệu demo của nhóm. Những tài liệu, mô hình hoặc công cụ bên ngoài được sử dụng trong báo cáo đều được trích dẫn hoặc nêu rõ ở phần tài liệu tham khảo.

  Nhóm không trình bày đồ án như một phần khảo sát thuần túy. Trọng tâm của đồ án là xây dựng pipeline phát hiện biển số bằng YOLO, kết hợp OCR để đọc ký tự, sau đó triển khai kiểm thử qua notebook, phần mềm Python, ứng dụng Android và video demo. Nhóm chịu trách nhiệm về tính trung thực của nội dung và các số liệu được đưa vào báo cáo.

  #group_signature()
  #pagebreak()
]

#let abstract_vi_page() = [
  #outline_entry([Tóm tắt])
  #centered_title([TÓM TẮT])
  Đồ án thực hiện bài toán phát hiện và nhận dạng biển số phương tiện Việt Nam dựa trên mô hình YOLO và kỹ thuật OCR. Pipeline tổng quát gồm bốn bước chính: chuẩn bị dữ liệu theo định dạng YOLO, huấn luyện mô hình phát hiện vùng biển số, cắt vùng biển số để đưa vào bộ nhận dạng ký tự, và triển khai phần mềm demo cho ảnh, thư mục ảnh, video và ứng dụng di động. Bộ dữ liệu sử dụng trong notebook có ba tập train, validation và test; nhãn được kiểm tra theo định dạng phát hiện đối tượng gồm năm cột: lớp, tọa độ tâm, chiều rộng và chiều cao.

  Hai mốc huấn luyện được trình bày trong báo cáo. Mốc đầu tiên là quá trình huấn luyện không nạp checkpoint từ các lần thử nghiệm trước, dùng kiến trúc YOLO từ tệp cấu hình, chạy 25 epoch với kích thước đầu vào 768. Mốc thứ hai là huấn luyện tiếp từ checkpoint trước đó với learning rate thấp hơn để ổn định mô hình. Kết quả tốt nhất của mốc huấn luyện tiếp đạt Precision 0.99448, Recall 0.99373, mAP50 0.99450 và mAP50-95 0.77006 trên tập validation. Ngoài notebook, nhóm xây dựng phần mềm Python tích hợp YOLO, FastALPR hoặc fast_plate_ocr, có các chế độ xử lý ảnh, thư mục ảnh, video, lưu CSV và xuất ảnh/video đã chú thích.

  Kết quả cho thấy mô hình phát hiện biển số đạt độ chính xác cao trên tập validation, đồng thời pipeline OCR đủ ổn định để trình diễn trong điều kiện demo. Hạn chế chính nằm ở các trường hợp biển số nhỏ, mờ, nghiêng, bị che khuất hoặc ảnh bãi xe có nhiều ký tự gây nhiễu. Báo cáo cũng trình bày các điểm cần lưu ý khi demo và các hạn chế kỹ thuật để phục vụ phần vấn đáp sau khi trình bày.

  #pagebreak()
]

#let abstract_en_page() = [
  #outline_entry([Abstract])
  #centered_title([ABSTRACT])
  This final project addresses Vietnamese vehicle license plate detection and recognition using a YOLO-based detector and an OCR stage. The workflow consists of dataset preparation, YOLO-format label checking, detector training, plate cropping, OCR recognition, and deployment through notebooks, a Python desktop application, an Android demo, and a video processing pipeline. The detector is evaluated with Precision, Recall, mAP50, and mAP50-95, while the software demo focuses on practical usability for images, image folders, and videos.

  Two training milestones are reported. The first run trains the detector without loading a previous project checkpoint, using a YOLO architecture file and 25 epochs. The second run continues from a checkpoint with a smaller learning rate to improve stability. The continuation run reaches Precision 0.99448, Recall 0.99373, mAP50 0.99450, and mAP50-95 0.77006 on the validation set. The Python application integrates YOLO detection with FastALPR or fast_plate_ocr, supports rotation and enhancement fallback, video smoothing, OCR voting, CSV export, and annotated outputs.

  The final result demonstrates a complete end-to-end ALPR pipeline suitable for final course assessment and demo. The report focuses on the technical workflow, experimental settings, implementation details, quantitative results, and system limitations so that the project can be defended with clear technical arguments during the oral presentation.

  #pagebreak()
]

#let abbreviations_page() = [
  #outline_entry([Danh mục chữ viết tắt])
  #centered_title([DANH MỤC CHỮ VIẾT TẮT])
  #tbl(
    table(
      columns: (3.0cm, 1fr),
      inset: 5pt,
      stroke: 0.45pt,
      [#cellhead[Chữ viết tắt]], [#cellhead[Diễn giải]],
      [AI], [Artificial Intelligence - trí tuệ nhân tạo],
      [ALPR], [Automatic License Plate Recognition - nhận dạng biển số tự động],
      [CNN], [Convolutional Neural Network - mạng nơ-ron tích chập],
      [CTC], [Connectionist Temporal Classification - kỹ thuật huấn luyện chuỗi ký tự không cần căn hàng ký tự thủ công],
      [OCR], [Optical Character Recognition - nhận dạng ký tự quang học],
      [YOLO], [You Only Look Once - họ mô hình phát hiện đối tượng một giai đoạn],
      [mAP], [Mean Average Precision - độ chính xác trung bình],
      [GUI], [Graphical User Interface - giao diện người dùng đồ họa],
      [FPS], [Frames Per Second - số khung hình mỗi giây],
      [NMS], [Non-Maximum Suppression - loại bỏ các khung phát hiện trùng lặp],
    ),
    [Danh mục chữ viết tắt sử dụng trong báo cáo],
  )
  #pagebreak()
]
