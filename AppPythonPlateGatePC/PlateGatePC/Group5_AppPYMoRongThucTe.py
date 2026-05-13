from __future__ import annotations

import json
import re
import socket
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tkinter import END, StringVar, Text, Tk, ttk


APP_DIR = Path(__file__).resolve().parent
ALLOW_LIST_FILE = APP_DIR / "bien_so_duoc_phep.txt"
HOST = "0.0.0.0"
PORT = 8765


def normalize_plate(text: str) -> str:
    text = (text or "").upper()
    text = text.replace(" ", "").replace("-", "").replace(".", "")
    return re.sub(r"[^A-Z0-9]", "", text)


def local_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = item[4][0]
            if not ip.startswith("127.") and ip not in addresses:
                addresses.append(ip)
    except socket.gaierror:
        pass
    return addresses


class GateRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.rstrip("/") in {"", "/health"}:
            self._send_json({"ok": True, "service": "Group5_AppPYMoRongThucTe"})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/scan":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"allowed": False, "message": "JSON không hợp lệ"}, status=400)
            return

        plate = normalize_plate(str(payload.get("plate", "")))
        score = payload.get("score", "")
        source = str(payload.get("source", "android"))
        allowed = self.server.app.check_plate(plate, score, source)
        self._send_json(
            {
                "allowed": allowed,
                "plate": plate,
                "message": "CHO QUA" if allowed else "KHÔNG CHO QUA",
            }
        )

    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args) -> None:
        return


class PlateGateApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Group5_AppPYMoRongThucTe")
        self.root.geometry("1180x720")
        self.root.minsize(1040, 650)

        self.allowed_plates: set[str] = set()
        self.total_count = 0
        self.allowed_count = 0
        self.denied_count = 0

        self.http_url_var = StringVar(value=f"http://127.0.0.1:{PORT}/scan")
        self.server_status_var = StringVar(value="Đang khởi động server...")
        self.allowed_count_var = StringVar(value="0 biển hợp lệ")
        self.total_count_var = StringVar(value="0")
        self.pass_count_var = StringVar(value="0")
        self.deny_count_var = StringVar(value="0")
        self.decision_var = StringVar(value="CHỜ XE")
        self.plate_var = StringVar(value="---")
        self.detail_var = StringVar(value="Chưa có dữ liệu từ Android")

        self._build_ui()
        self._load_allow_list()
        self._start_server()

    def _build_ui(self) -> None:
        self.root.configure(bg="#eef2f7")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#eef2f7")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Header.TLabel", background="#111827", foreground="#ffffff", font=("Segoe UI", 18, "bold"))
        style.configure("HeaderSub.TLabel", background="#111827", foreground="#cbd5e1", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 11, "bold"))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 9))
        style.configure("Value.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 18, "bold"))
        style.configure("Decision.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 34, "bold"))
        style.configure("Plate.TLabel", background="#ffffff", foreground="#0f172a", font=("Consolas", 34, "bold"))
        style.configure("Good.TLabel", background="#ffffff", foreground="#15803d", font=("Segoe UI", 34, "bold"))
        style.configure("Bad.TLabel", background="#ffffff", foreground="#b91c1c", font=("Segoe UI", 34, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        header = ttk.Frame(self.root, style="Root.TFrame")
        header.pack(fill="x")
        header_inner = ttk.Frame(header, style="Root.TFrame")
        header_inner.pack(fill="x", padx=14, pady=(12, 8))

        header_band = ttk.Frame(header_inner, style="Root.TFrame")
        header_band.pack(fill="x")
        title_box = ttk.Frame(header_band, style="Card.TFrame")
        title_box.pack(fill="x")
        title_box.configure(style="Card.TFrame")

        dark = ttk.Frame(title_box)
        dark.pack(fill="x")
        dark.configure(style="Root.TFrame")
        title = ttk.Label(dark, text="TRẠM KIỂM SOÁT BIỂN SỐ", style="Header.TLabel", anchor="w")
        title.pack(fill="x", ipady=10)
        subtitle = ttk.Label(
            dark,
            text="Nhận dữ liệu từ Android qua HTTP LAN, đối chiếu danh sách và quyết định cho xe qua",
            style="HeaderSub.TLabel",
            anchor="w",
        )
        subtitle.pack(fill="x", ipady=6)

        http_bar = ttk.Frame(header_inner, style="Root.TFrame")
        http_bar.pack(fill="x", pady=(8, 0))
        ttk.Label(http_bar, text="HTTP:", style="Muted.TLabel").pack(side="left")
        self.http_entry = ttk.Entry(http_bar, textvariable=self.http_url_var, font=("Consolas", 10), width=42)
        self.http_entry.pack(side="left", padx=(8, 6))
        ttk.Button(http_bar, text="Copy", command=self.copy_http_url).pack(side="left", padx=(0, 6))
        ttk.Button(http_bar, text="IP", command=self.refresh_http_urls).pack(side="left", padx=(0, 12))
        ttk.Label(http_bar, textvariable=self.server_status_var, style="Muted.TLabel").pack(side="left", fill="x", expand=True)

        content = ttk.Frame(self.root, style="Root.TFrame")
        content.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=5)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=3)

        self._build_stats_card(content)
        self._build_allow_card(content)
        self._build_result_card(content)

    def _build_connection_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="Kết nối Android", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.server_status_var, style="Muted.TLabel").grid(
            row=0, column=1, columnspan=3, sticky="e"
        )

        ttk.Label(card, text="HTTP endpoint", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.http_entry = ttk.Entry(card, textvariable=self.http_url_var, font=("Consolas", 11))
        self.http_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=(10, 0))
        ttk.Button(card, text="Copy URL", command=self.copy_http_url, style="Primary.TButton").grid(
            row=1, column=2, padx=(0, 8), pady=(10, 0)
        )
        ttk.Button(card, text="Làm mới IP", command=self.refresh_http_urls).grid(row=1, column=3, pady=(10, 0))

    def _build_stats_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=0, column=1, sticky="new", padx=(12, 0), pady=(0, 12))
        for idx in range(3):
            card.columnconfigure(idx, weight=1)

        self._stat_item(card, "Tổng lượt quét", self.total_count_var, 0)
        self._stat_item(card, "Cho qua", self.pass_count_var, 1)
        self._stat_item(card, "Từ chối", self.deny_count_var, 2)

    def _stat_item(self, parent: ttk.Frame, label: str, variable: StringVar, column: int) -> None:
        box = ttk.Frame(parent, style="Card.TFrame")
        box.grid(row=0, column=column, sticky="ew", padx=6)
        ttk.Label(box, text=label, style="Muted.TLabel").pack(anchor="center")
        ttk.Label(box, textvariable=variable, style="Value.TLabel").pack(anchor="center", pady=(4, 0))

    def _build_allow_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=0, column=0, rowspan=2, sticky="nsew")
        card.rowconfigure(3, weight=1)
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Danh sách biển số được phép", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.allowed_count_var, style="Muted.TLabel").grid(row=0, column=1, sticky="e")
        ttk.Label(card, text="Mỗi dòng một biển số. Hệ thống tự bỏ dấu cách, gạch ngang và dấu chấm.", style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 8)
        )

        button_row = ttk.Frame(card, style="Card.TFrame")
        button_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Button(button_row, text="Áp dụng danh sách", command=self.update_allow_list, style="Primary.TButton").pack(
            side="left"
        )
        ttk.Button(button_row, text="Lưu danh sách", command=self.save_allow_list).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Xóa lịch sử", command=self.clear_history).pack(side="left", padx=(8, 0))

        text_frame = ttk.Frame(card, style="Card.TFrame")
        text_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.allow_text = Text(
            text_frame,
            height=12,
            font=("Consolas", 12),
            bg="#f8fafc",
            fg="#0f172a",
            insertbackground="#0f172a",
            relief="flat",
            padx=10,
            pady=10,
        )
        self.allow_text.grid(row=0, column=0, sticky="nsew")
        allow_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.allow_text.yview)
        self.allow_text.configure(yscrollcommand=allow_scrollbar.set)
        allow_scrollbar.grid(row=0, column=1, sticky="ns")

    def _build_result_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        card.rowconfigure(3, weight=1)
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Kết quả kiểm soát", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        decision_box = ttk.Frame(card, style="Card.TFrame", padding=(0, 8, 0, 12))
        decision_box.grid(row=1, column=0, sticky="ew")
        self.decision_label = ttk.Label(decision_box, textvariable=self.decision_var, style="Decision.TLabel")
        self.decision_label.pack(anchor="w")
        ttk.Label(decision_box, textvariable=self.plate_var, style="Plate.TLabel").pack(anchor="w")
        ttk.Label(decision_box, textvariable=self.detail_var, style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

        ttk.Label(card, text="Lịch sử xe qua trạm", style="CardTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 8))
        columns = ("time", "decision", "plate", "score")
        self.history_table = ttk.Treeview(card, columns=columns, show="headings", height=10)
        headings = {
            "time": "Thời gian",
            "decision": "Quyết định",
            "plate": "Biển số",
            "score": "Độ tin cậy",
        }
        widths = {"time": 90, "decision": 130, "plate": 150, "score": 110}
        for col in columns:
            self.history_table.heading(col, text=headings[col])
            self.history_table.column(col, width=widths[col], minwidth=50, anchor="center", stretch=True)
        self.history_table.tag_configure("allow", foreground="#15803d")
        self.history_table.tag_configure("deny", foreground="#b91c1c")
        self.history_table.grid(row=3, column=0, sticky="nsew")
        y_scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.history_table.yview)
        x_scrollbar = ttk.Scrollbar(card, orient="horizontal", command=self.history_table.xview)
        self.history_table.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        y_scrollbar.grid(row=3, column=1, sticky="ns")
        x_scrollbar.grid(row=4, column=0, sticky="ew")

    def _load_allow_list(self) -> None:
        if not ALLOW_LIST_FILE.exists():
            ALLOW_LIST_FILE.write_text("51F22261\n38L123157\n", encoding="utf-8")

        content = ALLOW_LIST_FILE.read_text(encoding="utf-8")
        self.allow_text.delete("1.0", END)
        self.allow_text.insert("1.0", content)
        self.update_allow_list(show_message=False)

    def update_allow_list(self, show_message: bool = True) -> None:
        lines = self.allow_text.get("1.0", END).splitlines()
        self.allowed_plates = {normalize_plate(line) for line in lines if normalize_plate(line)}
        self.allowed_count_var.set(f"{len(self.allowed_plates)} biển hợp lệ")
        if show_message:
            self.server_status_var.set(f"Đã áp dụng {len(self.allowed_plates)} biển số được phép")

    def save_allow_list(self) -> None:
        self.update_allow_list(show_message=False)
        text = "\n".join(sorted(self.allowed_plates)) + ("\n" if self.allowed_plates else "")
        ALLOW_LIST_FILE.write_text(text, encoding="utf-8")
        self.allow_text.delete("1.0", END)
        self.allow_text.insert("1.0", text)
        self.server_status_var.set(f"Đã lưu {len(self.allowed_plates)} biển số vào file")

    def clear_history(self) -> None:
        for row in self.history_table.get_children():
            self.history_table.delete(row)
        self.total_count = 0
        self.allowed_count = 0
        self.denied_count = 0
        self._update_stats()
        self.decision_var.set("CHỜ XE")
        self.plate_var.set("---")
        self.detail_var.set("Đã xóa lịch sử quét")
        self.decision_label.configure(style="Decision.TLabel")

    def check_plate(self, plate: str, score, source: str) -> bool:
        self.update_allow_list(show_message=False)
        allowed = plate in self.allowed_plates
        self.root.after(0, lambda: self._add_scan_result(plate, score, source, allowed))
        return allowed

    def _add_scan_result(self, plate: str, score, source: str, allowed: bool) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        decision = "CHO QUA" if allowed else "TỪ CHỐI"
        tag = "allow" if allowed else "deny"

        self.total_count += 1
        if allowed:
            self.allowed_count += 1
            self.decision_label.configure(style="Good.TLabel")
        else:
            self.denied_count += 1
            self.decision_label.configure(style="Bad.TLabel")
        self._update_stats()

        self.decision_var.set(decision)
        self.plate_var.set(plate or "UNKNOWN")
        self.detail_var.set(f"{now} | nguồn: {source} | độ tin cậy: {score}")
        self.history_table.insert("", 0, values=(now, decision, plate or "UNKNOWN", score), tags=(tag,))

    def _update_stats(self) -> None:
        self.total_count_var.set(str(self.total_count))
        self.pass_count_var.set(str(self.allowed_count))
        self.deny_count_var.set(str(self.denied_count))

    def _start_server(self) -> None:
        self.server = ThreadingHTTPServer((HOST, PORT), GateRequestHandler)
        self.server.app = self
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.refresh_http_urls()

    def refresh_http_urls(self) -> None:
        ips = local_ipv4_addresses()
        urls = [f"http://{ip}:{PORT}/scan" for ip in ips]
        if urls:
            self.http_url_var.set(urls[0])
            self.server_status_var.set("Server sẵn sàng: " + "  |  ".join(urls))
        else:
            self.http_url_var.set(f"http://127.0.0.1:{PORT}/scan")
            self.server_status_var.set(f"Server đang chạy cổng {PORT}. Kiểm tra IP LAN của máy PC.")

    def copy_http_url(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self.http_url_var.get())
        self.server_status_var.set("Đã copy URL HTTP để dán vào app Android")


def main() -> None:
    root = Tk()
    PlateGateApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
