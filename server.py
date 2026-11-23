# -*- coding: utf-8 -*-
"""收入税费表 · 本地取数服务

在浏览器里点「从亿企赢取数」→ 本服务后台（headless）登录亿企赢 → 按台账公司绑定的
账套 cid 取指定月份的「科目余额表」→ 回给页面。

只读：不写账、不生成凭证、不申报。

启动：双击「启动.bat」，或 <带 playwright 的 python> server.py
      --no-browser  不自动开浏览器     --port 8790  指定端口
"""
import json
import os
import re
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("YQY_SRC") or r"D:\onedrive\Work\金哪达\自动入账模板\账务复核\codes\src"
HEADLESS = os.environ.get("YQY_HEADLESS", "1") != "0"

try:                                  # cmd 下按系统代码页输出，只做容错，不硬转 utf-8
    sys.stdout.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass


# ---------------------------------------------------------------- 配置 / 凭据
def load_companies():
    with open(os.path.join(ROOT, "config", "companies.json"), encoding="utf-8") as fh:
        return json.load(fh)["companies"]


def load_creds():
    """账号密码只在 config/creds.json 里，绝不写进代码"""
    p = os.path.join(ROOT, "config", "creds.json")
    if not os.path.isfile(p):
        raise RuntimeError("缺 config/creds.json（亿企赢账号密码）")
    with open(p, encoding="utf-8") as fh:
        c = json.load(fh)
    if not c.get("user") or not c.get("pwd"):
        raise RuntimeError("config/creds.json 里 user / pwd 不完整")
    os.environ.setdefault("YQW_USER", c["user"])
    os.environ.setdefault("YQW_PWD", c["pwd"])


def norm_co(s):
    s = re.sub(r"[\s\u3000（）()]", "", s or "")
    for suf in ("有限责任公司", "有限公司", "公司"):
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    return s


def pick_company(name):
    n = norm_co(name)
    if not n:
        raise RuntimeError("台账里没填公司名")
    for c in load_companies():
        cn = norm_co(c["name"])
        if n == cn or n in cn or cn in n:
            return c
    raise RuntimeError("台账公司「%s」没有绑定亿企赢账套，请在 config/companies.json 里补" % name)


# ---------------------------------------------------------------- 取数
def month_range(a, b):
    """'2026-08' ~ '2026-10' → ['2026-08','2026-09','2026-10']；只允许同一年、最多 12 个月"""
    pat = re.compile(r"^(20\d{2})-(0[1-9]|1[0-2])$")
    if not pat.match(a or "") or not pat.match(b or ""):
        raise RuntimeError("月份格式要 YYYY-MM，例如 2026-10")
    ya, ma = map(int, a.split("-"))
    yb, mb = map(int, b.split("-"))
    if ya != yb:
        raise RuntimeError("跨年不支持（一本台账记一年）：%s → %s" % (a, b))
    if ma > mb:
        raise RuntimeError("起始月晚于结束月：%s → %s" % (a, b))
    return ["%d-%02d" % (ya, m) for m in range(ma, mb + 1)]


def fetch_range(company, from_ym, to_ym):
    """一次登录进账套，取区间内每个月；任一月失败整体失败，不静默补 0"""
    periods = month_range(from_ym, to_ym)
    co = pick_company(company)
    load_creds()
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    from yqwin_session import open_finance_page      # noqa: PLC0415
    from fetch_balance import fetch_balance, verify  # noqa: PLC0415

    out, warns = [], []
    with open_finance_page(co["cid"], headless=HEADLESS) as fin:
        for p in periods:
            bal = fetch_balance(fin, p)
            for e in verify(bal):
                warns.append("%s 月：%s" % (p[5:], e))
            out.append({
                "period": p,
                "rows": [{"code": r["code"], "name": r["name"],
                          "debit": r["occurredDebit"], "credit": r["occurredCredit"]}
                         for r in bal["rows"]],
            })
    return {"company": co["name"], "key": co["key"], "cid": co["cid"],
            "months": out, "warnings": warns}


LOCK = threading.Lock()


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "TaxLedger"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):  # 安静点，只留取数结果
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/index.html"):
            with open(os.path.join(ROOT, "index.html"), "rb") as fh:
                self._send(200, fh.read(), "text/html; charset=utf-8")
        elif p == "/api/status":
            try:
                load_creds()
                cred = True
            except Exception:  # noqa: BLE001
                cred = False
            self._send(200, {"ok": True, "creds": cred, "headless": HEADLESS,
                             "companies": load_companies()})
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/fetch":
            self._send(404, {"ok": False, "error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as exc:  # noqa: BLE001
            self._send(400, {"ok": False, "error": "请求不是 JSON：%s" % exc})
            return
        if not LOCK.acquire(timeout=1):
            self._send(429, {"ok": False, "error": "正在跑另一批取数，等它结束再来"})
            return
        try:
            res = fetch_range(req.get("company") or "", req.get("from") or "", req.get("to") or "")
            print("[取数] %s %s~%s → %d 个月" % (res["key"], req["from"], req["to"], len(res["months"])))
            self._send(200, dict(ok=True, **res))
        except Exception as exc:  # noqa: BLE001
            print("[失败] %s" % exc)
            self._send(500, {"ok": False, "error": str(exc)})
        finally:
            LOCK.release()


def main():
    args = sys.argv[1:]
    port = int(args[args.index("--port") + 1]) if "--port" in args else 8765
    srv = None
    for p in range(port, port + 12):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if srv is None:
        raise SystemExit("8765–8776 端口全被占用，用 --port 换一个")
    url = "http://127.0.0.1:%d/" % port
    print("收入税费表 取数服务：%s   （关掉这个窗口就停）" % url)
    if "--no-browser" not in args:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
