#import "../config.typ": callout, tbl, cellhead, cell, photo

= TRIỂN KHAI VÀ DEMO PHẦN MỀM

== Vai trò của phần mềm demo

Theo yêu cầu nộp đồ án môn học, ngoài báo cáo và slide trình bày, nhóm còn phải chuẩn bị mã nguồn, dữ liệu, mô hình đã huấn luyện và phần mềm triển khai nếu có. Trong bối cảnh đó, phần mềm demo đóng vai trò chuyển kết quả nghiên cứu từ notebook sang dạng có thể trình diễn trực tiếp trước lớp. Nếu chỉ dừng ở notebook, quá trình demo sẽ phụ thuộc mạnh vào môi trường chạy như Kaggle hoặc Colab. Ngược lại, phần mềm cục bộ cho phép nạp mô hình đã huấn luyện, chọn ảnh/video thật và quan sát kết quả ngay trong buổi báo cáo.

Nhóm tổ chức phần mềm thành hai lớp. Lớp thứ nhất là ứng dụng Python desktop dùng để kiểm thử thuật toán YOLO + OCR trên ảnh, thư mục ảnh và video; đây là công cụ chính để đánh giá nhanh, sinh ảnh/video kết quả và xuất CSV. Lớp thứ hai là trạm kiểm soát Python, đóng vai trò mở rộng ứng dụng: nhận kết quả từ Android qua mạng LAN, đối chiếu danh sách biển số được phép và trả quyết định cho qua hoặc từ chối. Cách tách này giúp báo cáo không trộn lẫn công cụ kiểm thử mô hình với kịch bản ứng dụng thực tế.

#tbl(
  table(
    columns: (1fr, 1fr, 1fr),
    inset: 4.5pt,
    stroke: 0.45pt,
    [#cellhead[Thành phần]], [#cellhead[Vai trò]], [#cellhead[Ý nghĩa trong demo]],
    [Ứng dụng Python kiểm thử], [#cell[Chạy YOLO + OCR trên ảnh, thư mục ảnh và video; xuất ảnh/video có bounding box, crop biển số và CSV.]], [#cell[Dùng để kiểm tra chất lượng mô hình, thử nhiều trường hợp đầu vào và trình bày chức năng FFMPEG.]],
    [Trạm kiểm soát Python], [#cell[Nhận dữ liệu từ Android qua HTTP LAN, chuẩn hóa biển số, đối chiếu danh sách cho phép và ghi lịch sử quyết định.]], [#cell[Dùng để minh họa hướng mở rộng thành hệ thống kiểm soát ra/vào có phản hồi theo thời gian thực.]],
    [Ứng dụng Android], [#cell[Thu nhận ảnh, nhận dạng biển số và gửi kết quả đến trạm kiểm soát Python.]], [#cell[Đóng vai trò thiết bị đầu cuối trong kịch bản triển khai gần với thực tế.]],
  ),
  [Phân tách vai trò giữa công cụ kiểm thử và phần mềm mở rộng],
)

== Ứng dụng Python kiểm thử và demo thuật toán

Ứng dụng Python được thiết kế theo hướng tối giản thao tác cho buổi demo: chọn mô hình YOLO `.pt`, chọn ảnh/video hoặc thư mục ảnh, chạy nhận dạng và mở thư mục output. Phần mềm tự phân loại input là ảnh đơn, thư mục ảnh hay video. Kết quả được lưu trong thư mục output gồm ảnh/video đã vẽ bounding box, crop biển số và tệp CSV tổng hợp.

#photo("assets/python_gui.png", [Giao diện phần mềm Python dùng cho demo phát hiện và OCR biển số], width: 100%)

Các đặc điểm chính của app gồm:

- Hỗ trợ ảnh đơn, thư mục ảnh và video nhiều định dạng như mp4, mkv, webm, mov, avi.
- Dùng YOLO `.pt` để phát hiện biển số.
- Dùng FastALPR DefaultOCR hoặc fast_plate_ocr tùy môi trường cài đặt.
- Có các preset như Balanced, Image/Multi plates, Low confidence rescue, Fast video và Slow video.
- Có fallback xoay, gamma, chia tile, xử lý ảnh ghép và lọc vùng gây nhiễu.
- Có cơ chế xử lý video với smoothing, voting OCR và xuất video đầu ra bằng FFMPEG.
- Xuất CSV để kiểm tra kết quả nhiều ảnh hoặc nhiều frame.

== Luồng xử lý trong ứng dụng Python kiểm thử

Về mặt kỹ thuật, app khởi tạo mô hình YOLO và OCR backend, sau đó điều phối nhánh xử lý tương ứng với loại đầu vào; cách tổ chức này giúp tách rõ phần phát hiện đối tượng, phần OCR và phần xuất kết quả. Với ảnh, phần mềm duyệt từng ảnh, thực hiện phát hiện biển số, cắt vùng biển số, OCR và lưu kết quả. Với video, phần mềm đọc tuần tự các frame, suy luận theo tần suất lấy mẫu phù hợp, duy trì thông tin track giữa các frame và cuối cùng mã hóa video đầu ra bằng FFMPEG. Việc sử dụng FFMPEG có ý nghĩa thực tiễn vì giúp chuẩn hóa quá trình xuất video kết quả, giữ khả năng tương thích với nhiều định dạng đầu vào/đầu ra và thuận tiện cho phần demo trên lớp.

Kết quả OCR không được hiển thị trực tiếp ngay sau mỗi lần đọc ký tự, mà phải qua bước làm sạch chuỗi, kiểm tra tính hợp lý của biển số Việt Nam và ước lượng độ tin cậy tổng hợp. Việc rà soát mã nguồn FastALPR cũng củng cố lựa chọn này: backend OCR trả về chuỗi ký tự cùng confidence, trong đó confidence có thể là danh sách xác suất theo từng ký tự. Vì vậy, ứng dụng Python cần gom và diễn giải confidence một cách nhất quán trước khi hiển thị. Cách xử lý này giúp giao diện demo ổn định hơn và hạn chế các chuỗi nhiễu xuất hiện trên video đầu ra.

```python
# Mã giả rút gọn từ luồng ứng dụng Python kiểm thử
model = load_yolo_model(pt_path)
ocr = load_ocr_backend()

if input_is_image_or_folder:
    for image in images:
        boxes = model(image)
        for box in boxes:
            crop = crop_plate(image, box)
            text, ocr_conf = ocr.read(crop)
            text = normalize_plate(text)
            save_result(image, box, text, ocr_conf)
elif input_is_video:
    for frame in video:
        boxes = model(frame)
        update_tracks_and_votes(boxes)
        draw_stable_results(frame)
```

== Trạm kiểm soát Python và Android liên kết

Để kiểm tra khả năng vận hành ngoài notebook, nhóm bổ sung kịch bản demo mở rộng trong đó thiết bị Android đảm nhiệm bước thu nhận ảnh, phát hiện biển số và gửi kết quả OCR đến một trạm kiểm soát viết bằng Python trên PC. Ở bản demo hiện tại, hai thiết bị giao tiếp qua HTTP trong cùng mạng LAN; khi triển khai ở môi trường thật, lớp truyền thông này có thể được đặt sau HTTPS hoặc mạng nội bộ có kiểm soát để tăng an toàn dữ liệu. Trạm PC duy trì danh sách biển số được phép, chuẩn hóa chuỗi nhận dạng bằng cách loại bỏ khoảng trắng, dấu gạch ngang và dấu chấm, sau đó trả về quyết định cho ứng dụng Android.

Android trong kịch bản này không chỉ hiển thị kết quả OCR cục bộ, mà còn tham gia vào một quy trình có phản hồi từ server Python. Nhờ vậy, hệ thống demo thể hiện rõ hơn hướng ứng dụng: thiết bị đầu cuối gửi dữ liệu, trạm kiểm soát ra quyết định, lịch sử xe qua trạm được lưu lại để kiểm tra sau buổi demo.

#figure(
  align(center)[
    #grid(
      columns: (0.72fr, 1.28fr),
      gutter: 0.35cm,
      [#image("../assets/android_gate_scan_demo.jpg", width: 100%, height: 12.4cm, fit: "contain")],
      [#image("../assets/pc_gate_control_demo.png", width: 100%, height: 12.4cm, fit: "contain")],
    )
  ],
  kind: image,
  caption: [Minh chứng luồng kiểm soát end-to-end: ứng dụng Android phát hiện biển số 64K89380, gửi kết quả qua HTTP LAN và trạm kiểm soát Python đối chiếu danh sách để trả quyết định “CHO QUA”],
)

Cụm hình trên minh họa luồng hoạt động end-to-end của hệ thống trong điều kiện demo thực tế. Ở phía Android, biển số được khoanh vùng và nhận dạng với độ tin cậy khoảng 0.92, sau đó kết quả được gửi đến endpoint của PC. Ở phía trạm kiểm soát, biển số `64K89380` có trong danh sách cho phép nên hệ thống trả về quyết định “CHO QUA” và lưu lại thời gian, biển số, quyết định cùng độ tin cậy. Minh chứng này không thay thế cho đánh giá định lượng trên tập validation, nhưng cho thấy pipeline có thể được ghép thành một quy trình kiểm soát hoàn chỉnh gồm nhận ảnh, OCR, truyền dữ liệu, đối chiếu danh sách và phản hồi quyết định.

== Tính năng xử lý video và FFMPEG trong ứng dụng Python kiểm thử

Đối với video, bài toán không chỉ là phát hiện biển số ở từng frame mà còn phải duy trì tính ổn định của kết quả theo thời gian. Nếu hiển thị chuỗi OCR độc lập ở mỗi frame, văn bản trên video đầu ra sẽ thay đổi liên tục do ảnh hưởng của rung lắc, nhiễu, thay đổi góc nhìn và độ mờ do chuyển động. Vì vậy, ứng dụng Python áp dụng cơ chế *track smoothing* và *OCR voting*: các vùng biển số gần nhau theo không gian và thời gian được liên kết thành một track, nhiều kết quả OCR trong cùng track được tổng hợp theo độ tin cậy, và kết quả có trọng số tốt hơn sẽ được giữ lại trong một khoảng thời gian ngắn.

Bên cạnh đó, FFMPEG được dùng ở giai đoạn xuất video đầu ra. Đây là một thành phần kỹ thuật đáng chú ý của phần mềm, vì nó cho phép giữ đúng tốc độ khung hình, hỗ trợ nhiều định dạng và encoder, đồng thời tạo tệp video kết quả có thể phát ổn định khi trình bày trên lớp. Do đó, khi mô tả phần mềm trong báo cáo, cần nhấn mạnh rằng chức năng video không chỉ là suy luận YOLO + OCR trên từng frame, mà còn bao gồm bước hậu xử lý và đóng gói video đầu ra bằng FFMPEG.

#figure(
  align(center)[
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35cm,
      [#image("../assets/video_yolo_ocr_fastalpr.png", width: 100%, height: 12.6cm, fit: "contain")],
      [#image("../assets/video_fastalpr_screenshot.png", width: 100%, height: 12.6cm, fit: "contain")],
    )
  ],
  kind: image,
  caption: [Minh họa kết quả xử lý video trong ứng dụng Python kiểm thử: detector khoanh vùng biển số, OCR hiển thị chuỗi nhận dạng kèm độ tin cậy và FFMPEG đóng gói video đầu ra để phục vụ demo],
)

== Các tình huống lỗi và cách xử lý

Trong quá trình thử nghiệm, nhóm ghi nhận một số lỗi thường gặp:

- YOLO bỏ sót biển số nhỏ hoặc biển số ở vùng rìa ảnh.
- OCR đọc nhầm ký tự giống nhau như O/0, I/1, S/5 hoặc B/8.
- Ảnh bãi xe có mã ô đậu xe gây nhiễu, ví dụ D28 hoặc D29, dễ bị nhận nhầm thành biển số.
- Video có motion blur làm biển số rõ ở frame này nhưng mờ ở frame khác.
- Ảnh quá tối hoặc quá sáng làm crop biển số thiếu tương phản.

Các xử lý trong app gồm giảm ngưỡng confidence ở preset cứu ảnh khó, tile fallback để tìm biển nhỏ, gamma fallback cho ảnh tối, lọc chuỗi không giống biển số Việt Nam và voting OCR trong video. Tuy nhiên, báo cáo vẫn cần nêu giới hạn thay vì khẳng định phần mềm luôn đúng.

== Đóng gói sản phẩm nộp

Khi nộp bài, nhóm cần tách bạch các thành phần theo đúng yêu cầu: báo cáo PDF/Word theo mẫu quy định, slide phục vụ trình bày và demo trong thời lượng tối đa 15 phút, mã nguồn nén thành một tệp, dữ liệu theo tệp hoặc liên kết có mở quyền truy cập, mô hình đã huấn luyện và phần mềm triển khai nếu có. Việc tách riêng các thành phần này giúp hồ sơ nộp bài rõ ràng, đồng thời thuận lợi cho giảng viên kiểm tra từng hạng mục. Báo cáo Typst chỉ đóng vai trò là nguồn biên soạn để xuất PDF; không nên gộp dữ liệu lớn, mô hình và toàn bộ mã nguồn vào cùng gói báo cáo.
