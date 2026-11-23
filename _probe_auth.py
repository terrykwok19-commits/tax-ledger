# -*- coding: utf-8 -*-
"""探针2：余额表接口靠什么鉴权 / 账套 token 从哪来"""
import os, sys, json

SRC = r"D:\onedrive\Work\金哪达\自动入账模板\账务复核\codes\src"
sys.path.insert(0, SRC)
sys.dont_write_bytecode = True
os.environ["YQW_USER"] = "18620772739"
os.environ["YQW_PWD"] = "Jie19910901"

from yqwin_session import open_finance_page   # noqa: E402
from fetch_balance import build_payload, API  # noqa: E402

A = "1906339837704"

with open_finance_page(A, headless=True) as fin:
    seen = []

    def on_req(r):
        if "accountBalanceSheet" in r.url or "balance" in r.url.lower():
            h = {k: v for k, v in r.headers.items() if k.lower() not in ("cookie",)}
            seen.append({"url": r.url, "headers": h, "post": (r.post_data or "")[:300]})

    fin.on("request", on_req)
    fin.evaluate("""async ([url, payload]) => {
        await fetch(url, {method:'POST', credentials:'include',
          headers:{'Content-Type':'application/json;charset=UTF-8'},
          body: JSON.stringify(payload)});
    }""", [API, build_payload("2026-10")])

    print("== 请求头 ==")
    for s in seen[:3]:
        print(json.dumps(s, ensure_ascii=False)[:900])

    print("\n== localStorage keys ==")
    print(fin.evaluate("() => Object.keys(localStorage)"))
    print("== sessionStorage keys ==")
    print(fin.evaluate("() => Object.keys(sessionStorage)"))
    print("\n== 含 token/company 的存储值 ==")
    print(fin.evaluate("""() => {
        const out = {};
        for (const st of [localStorage, sessionStorage]) {
          for (let i=0;i<st.length;i++) {
            const k = st.key(i), v = String(st.getItem(k)||'');
            if (/token|compan|account|org/i.test(k) && v.length < 300) out[k] = v;
          }
        }
        return out;
    }"""))
    print("\n== cookies ==")
    print([c["name"] for c in fin.context.cookies()])
