import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("ربات سیگنال Bybit فعال است! ✅\n".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    print(f"✅ سرور Keep-Alive روی پورت {port} در حال اجراست...")
    server.serve_forever()

if __name__ == "__main__":
    # راه‌اندازی سرور HTTP در یک thread جداگانه
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    # اجرای ربات اصلی
    from main import main
    main()
