#import "config.typ": meta, body_leading, page_footer, centered_title, outline_entry
#import "src/00_cover.typ": cover_pages
#import "src/01_front_matter.typ": acknowledgement_page, commitment_page, abstract_vi_page, abstract_en_page, abbreviations_page
#import "@preview/codly:1.3.0": *
#import "@preview/codly-languages:0.1.10": *

#set document(title: meta.title_vi, author: meta.group_no)

#set page(
  paper: "a4",
  margin: (top: 2cm, bottom: 2cm, left: 2.5cm, right: 2cm),
)

#set text(font: "Times New Roman", size: 13pt, lang: "vi", top-edge: 0.8em, bottom-edge: -0.2em)
#show: codly-init.with()
#codly(
  languages: codly-languages,
  stroke: 0.55pt + rgb("#777777"),
  radius: 4pt,
)
#let accent_link = rgb("#0028d9")
#show link: set text(fill: accent_link)
#show link: underline
#show ref: it => {
  if it.element == none {
    return it
  }
  set text(fill: accent_link)
  it
}
#show cite: it => {
  show regex("\d+"): set text(fill: accent_link)
  it
}
#set figure.caption(separator: [: ])
#show figure.caption: c => [
  #context text(weight: "bold", size: 13pt)[
    #c.supplement #c.counter.display(c.numbering)
  ]
  #c.separator#c.body
  #v(0.4cm)
]
#show raw.where(block: false): box.with(
  fill: luma(240),
  stroke: rgb(239, 240, 243),
  inset: (x: 3pt, y: 1pt),
  outset: (y: 3pt),
  radius: 3pt,
)
#set par(justify: true, leading: body_leading, first-line-indent: (amount: 1.25cm, all: true))
#set heading(numbering: "1.1.1")
#show heading.where(level: 1): it => [
  #pagebreak(weak: true)
  #v(0.05cm)
  #align(center)[#text(16pt, weight: "bold")[CHƯƠNG #counter(heading).display()]]
  #v(0.10cm)
  #align(center)[#text(15pt, weight: "bold")[#it.body]]
  #v(0.12cm)
  #align(center)[#rect(width: 7.0cm, height: 0.65pt, fill: black)]
  #v(0.20cm)
]

#show heading.where(level: 2): it => block(width: 100%, breakable: true, [
  #set par(first-line-indent: 0pt, justify: false)
  #v(0.10cm)
  #text(13.5pt, weight: "bold")[#counter(heading).display(). #it.body]
  #v(0.05cm)
])

#cover_pages()

#set page(numbering: "i", footer: page_footer)
#counter(page).update(1)

#acknowledgement_page()
#commitment_page()
#abstract_vi_page()
#abstract_en_page()

#outline_entry([Mục lục])
#centered_title([MỤC LỤC])
#outline(title: none, depth: 3)
#pagebreak()

#abbreviations_page()

#outline_entry([Danh sách hình])
#centered_title([DANH SÁCH HÌNH])
#outline(title: none, target: figure.where(kind: image))
#pagebreak()

#outline_entry([Danh sách bảng])
#centered_title([DANH SÁCH BẢNG])
#outline(title: none, target: figure.where(kind: table))
#pagebreak()

#set page(numbering: "1", footer: page_footer)
#counter(page).update(1)
#counter(heading).update(0)

#include "src/02_chapter_1.typ"
#include "src/03_chapter_2.typ"
#include "src/04_chapter_3.typ"
#include "src/05_chapter_4.typ"
#include "src/06_chapter_5.typ"
#include "src/08_conclusion.typ"

#pagebreak()
#outline_entry([Tài liệu tham khảo])
#centered_title([TÀI LIỆU THAM KHẢO])
#bibliography("tai_lieu_tham_khao.bib", style: "ieee", title: none, full: true)
