#let meta = (
  university_top: "ĐẠI HỌC QUỐC GIA THÀNH PHỐ HỒ CHÍ MINH",
  university_name: "TRƯỜNG ĐẠI HỌC KHOA HỌC TỰ NHIÊN",
  faculty_name: "KHOA ĐIỆN TỬ - VIỄN THÔNG",
  course_name: "NHẬP MÔN TRÍ TUỆ NHÂN TẠO",
  class_name: "22DTV_CLC1",
  report_type: "BÁO CÁO ĐỒ ÁN CUỐI KỲ",
  group_no: "05",
  title_vi: "Phát hiện và nhận dạng biển số phương tiện dựa trên mô hình YOLO và kỹ thuật OCR trên bộ dữ liệu Vietnamese License Plates Detection",
  title_upper_vi: "PHÁT HIỆN VÀ NHẬN DẠNG BIỂN SỐ PHƯƠNG TIỆN DỰA TRÊN MÔ HÌNH YOLO VÀ KỸ THUẬT OCR TRÊN BỘ DỮ LIỆU VIETNAMESE LICENSE PLATES DETECTION",
  title_en: "Vehicle License Plate Detection and Recognition Using YOLO and OCR on the Vietnamese License Plates Detection Dataset",
  lecturer_1: "TS. ĐẶNG LÊ KHOA",
  lecturer_2: "ThS. NGUYỄN THÁI CÔNG NGHĨA",
  lecturer_3: "CN. NGUYỄN DŨNG",
  city: "Thành phố Hồ Chí Minh",
  month_year: "Tháng 5 năm 2026",
)

#let members = (
  (id: "22207043", name: "Mai Xuân Khang"),
  (id: "22207106", name: "Trương Quang Vũ"),
  (id: "22207112", name: "Lý Phi Hùng"),
  (id: "22207063", name: "Văn Đình Nam"),
  (id: "22207062", name: "Trần Sĩ Nam"),
  (id: "22207056", name: "Lương Hải Long"),
  (id: "22207066", name: "Lê Tấn Phi Pha"),
)

#let body_leading = 0.86em
#let page_footer = context align(right)[#counter(page).display()]

#let title_rule(rule_width: 4.2cm, thickness: 0.65pt) = [
  #align(center)[#rect(width: rule_width, height: thickness, fill: black)]
]

#let centered_title(text_value) = [
  #align(center)[#text(16pt, weight: "bold")[#text_value]]
  #v(0.12cm)
  #title_rule()
  #v(0.18cm)
]

#let outline_entry(title) = [
  #{
    show heading: none
    heading(numbering: none)[#title]
  }
]

#let noindent(body) = [
  #set par(first-line-indent: 0pt)
  #body
]

#let compact(body) = [
  #set par(first-line-indent: 0pt, leading: 0.70em)
  #body
]

#let cellhead(body) = [
  #set par(first-line-indent: 0pt, justify: false)
  #text(weight: "bold")[#body]
]
#let cell(body) = [
  #set par(first-line-indent: 0pt, justify: true)
  #body
]

#let callout(title, body) = block(
  width: 100%,
  inset: 9pt,
  fill: rgb("#f7f7f7"),
  stroke: 0.55pt + rgb("#777777"),
  radius: 4pt,
  breakable: true,
  [
    #set par(first-line-indent: 0pt, justify: true)
    #text(12.5pt, weight: "bold")[#title]
    #v(0.06cm)
    #body
  ],
)

#let photo(path, cap, width: 100%, height: auto) = figure(
  align(center)[#image(path, width: width, height: height, fit: "contain")],
  kind: image,
  caption: cap,
)

#let photo2(path_a, path_b, cap, height: 10.8cm) = figure(
  align(center)[
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.35cm,
      [#image(path_a, width: 100%, height: height, fit: "contain")],
      [#image(path_b, width: 100%, height: height, fit: "contain")],
    )
  ],
  kind: image,
  caption: cap,
)

#let tbl(body, cap) = figure(
  body,
  kind: table,
  caption: cap,
)
