#import "../config.typ": meta, members

#let member_lines() = [
  #table(
    columns: (3.0cm, 4.2cm),
    stroke: none,
    inset: (x: 2pt, y: 2.2pt),
    [22207043], [Mai Xuân Khang],
    [22207106], [Trương Quang Vũ],
    [22207112], [Lý Phi Hùng],
    [22207063], [Văn Đình Nam],
    [22207062], [Trần Sĩ Nam],
    [22207056], [Lương Hải Long],
    [22207066], [Lê Tấn Phi Pha],
  )
]

#let outer_cover() = [
  #set page(numbering: none, footer: none)
  #rect(
    stroke: 4.2pt,
    inset: 7pt,
    width: 100%,
    height: 100%,
    [
      #rect(
        stroke: 1.1pt,
        inset: 13pt,
        width: 100%,
        height: 100%,
        [
          #align(center)[
            #stack(
              dir: ttb,
              spacing: 0.13cm,
              text(12pt, weight: "bold")[#meta.university_top],
              text(12pt, weight: "bold")[#meta.university_name],
              text(12pt, weight: "bold")[#meta.faculty_name],
            )
          ]

          #v(0.62cm)
          #align(center)[#text(13pt, weight: "bold")[#meta.report_type]]
          #v(0.16cm)
          #align(center)[#text(12pt, weight: "bold")[Học phần: #meta.course_name]]
          #v(0.10cm)
          #align(center)[#text(12pt)[Lớp: #meta.class_name #sym.space — #sym.space Nhóm: #meta.group_no]]

          #v(0.52cm)
          #align(center)[#rect(width: 3.8cm, height: 0.7pt, fill: black)]
          #v(0.24cm)
          #align(center)[
            #pad(left: 0.42cm, right: 0.42cm)[
              #text(16.6pt, weight: "bold")[#meta.title_upper_vi]
            ]
          ]
          #v(0.24cm)
          #align(center)[#rect(width: 10.8cm, height: 0.7pt, fill: black)]

          #v(0.42cm)
          #grid(
            columns: (4.0cm, 0.28cm, 1fr),
            row-gutter: 0.13cm,
            [Giảng viên phụ trách], [:], [#meta.lecturer_1],
            [], [], [#meta.lecturer_2],
            [], [], [#meta.lecturer_3],
          )

          #v(0.36cm)
          #align(center)[#text(12.5pt, weight: "bold")[DANH SÁCH THÀNH VIÊN NHÓM 05]]
          #v(0.10cm)
          #align(center)[#member_lines()]

          #v(1fr)
          #align(center)[#text(12pt, weight: "bold")[#meta.city – #meta.month_year]]
        ],
      )
    ],
  )
  #pagebreak()
]

#let inner_cover() = [
  #set page(numbering: none, footer: none)
  #align(center)[
    #stack(
      dir: ttb,
      spacing: 0.14cm,
      text(12pt, weight: "bold")[#meta.university_top],
      text(12pt, weight: "bold")[#meta.university_name],
      text(12pt, weight: "bold")[#meta.faculty_name],
      text(13pt, weight: "bold")[#meta.report_type],
    )
  ]

  #v(0.38cm)
  #align(center)[#text(12pt)[Học phần: #meta.course_name — #meta.class_name]]
  #align(center)[#text(12pt)[Nhóm thực hiện: #meta.group_no]]

  #v(0.56cm)
  #align(center)[#pad(left: 0.7cm, right: 0.7cm)[#text(16pt, weight: "bold")[#meta.title_upper_vi]]]
  #v(0.18cm)
  #align(center)[#pad(left: 1.0cm, right: 1.0cm)[#text(10.7pt, style: "italic")[#meta.title_en]]]

  #v(0.48cm)
  #grid(
    columns: (4.2cm, 0.28cm, 1fr),
    row-gutter: 0.16cm,
    [Giảng viên phụ trách], [:], [#meta.lecturer_1],
    [], [], [#meta.lecturer_2],
    [], [], [#meta.lecturer_3],
    [], [], [],
    [Định hướng đề tài], [:], [Thị giác máy tính, học sâu, nhận dạng ký tự],
    [Sản phẩm demo], [:], [Notebook huấn luyện, ứng dụng Python kiểm thử, trạm kiểm soát Python, ứng dụng Android liên kết và video minh họa],
    [Bộ dữ liệu], [:], [Vietnamese License Plates Detection],
  )

  #v(0.34cm)
  #align(center)[#text(12.5pt, weight: "bold")[DANH SÁCH THÀNH VIÊN NHÓM 05]]
  #v(0.10cm)
  #align(center)[#member_lines()]

  #v(1fr)
  #align(right)[#text(12pt)[#meta.city – #meta.month_year]]
  #pagebreak()
]

#let cover_pages() = [
  #outer_cover()
  #inner_cover()
]
