import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from playwright.sync_api import sync_playwright

class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        b = b'{"ok":1}'
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self._cors(); self.send_header("Content-Length", str(len(b))); self.end_headers()
        self.wfile.write(b)
    def log_message(self, *a): pass

s = HTTPServer(("127.0.0.1", 8799), H)
threading.Thread(target=s.serve_forever, daemon=True).start()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-proxy-server"])
    pg = b.new_page()
    pg.goto("https://terrykwok19-commits.github.io/tax-ledger/", timeout=60000, wait_until="domcontentloaded")
    r = pg.evaluate("""async () => {
        try { const r = await fetch('http://127.0.0.1:8799/x'); return 'OK ' + r.status + ' ' + await r.text(); }
        catch(e) { return 'FAIL ' + e.message; }
    }""")
    print("https 页面 fetch 127.0.0.1 →", r)
    b.close()
s.shutdown()
