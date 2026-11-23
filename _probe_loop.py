import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        body = json.dumps({"ok": 1, "rows": 181}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

s = HTTPServer(("127.0.0.1", 8799), H)
threading.Thread(target=s.serve_forever, daemon=True).start()

# 用 headless chrome 打开 file:// 页面测试 fetch
import subprocess, os, tempfile
html = """<!doctype html><meta charset=utf-8><body><pre id=o>wait</pre><script>
fetch('http://127.0.0.1:8799/x').then(r=>r.json()).then(j=>{document.getElementById('o').textContent='OK '+JSON.stringify(j)})
 .catch(e=>{document.getElementById('o').textContent='FAIL '+e.message});
</script>"""
p = os.path.join(tempfile.gettempdir(), "_cors_test.html")
open(p, "w", encoding="utf-8").write(html)

CHROME = r"C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe"
out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                      "--no-proxy-server", "--virtual-time-budget=6000", "--dump-dom",
                      "file:///" + p.replace("\\", "/")],
                     capture_output=True, text=True, timeout=90).stdout
import re
m = re.search(r"<pre id=\"o\">(.*?)</pre>", out, re.S)
print("file:// 页面 fetch 127.0.0.1 →", m.group(1) if m else out[:200])
s.shutdown()
