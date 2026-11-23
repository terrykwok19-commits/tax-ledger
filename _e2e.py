# -*- coding: utf-8 -*-
"""端到端：浏览器点「亿企赢取数」→ 预览 → 确认写入 → 撤销"""
import json
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8790/"
log = []


def out(t):
    log.append(t)
    print(t)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-proxy-server"])
    pg = b.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: out("CONSOLE " + m.text))
    pg.add_init_script("try{ localStorage.clear(); }catch(e){}")
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)

    pg.fill("#company", "广州金哪达贸易有限公司")
    pg.fill("#year", "2026")
    pg.dispatch_event("#year", "change")
    out("台账公司：" + pg.input_value("#company") + " 年度：" + pg.input_value("#year"))

    pg.click("#btnYqy")
    pg.wait_for_function("() => /服务|没启动|缺/.test(document.getElementById('yqyState').textContent)",
                         timeout=25000)
    out("状态：" + pg.inner_text("#yqyState"))

    pg.fill("#yqyFrom", "2026-08")
    pg.fill("#yqyTo", "2026-10")
    pg.click("#yqyGo")
    pg.wait_for_function("() => document.getElementById('balMask').classList.contains('on')", timeout=200000)

    out("预览标题：" + pg.inner_text("#balHead").replace("\n", " "))
    body = pg.inner_text("#balBody")
    out("预览正文：\n" + body[:800])

    pg.click("#balOk")
    pg.wait_for_timeout(800)
    got = pg.evaluate("""() => {
        const s = JSON.parse(localStorage.getItem('tax-ledger-v2'));
        return {m8: s.months[7], m9: s.months[8], m10: s.months[9], rows: s.rows.map(r=>r.name)};
    }""")
    out("写入后 10 月：" + json.dumps(got, ensure_ascii=False)[:800])

    pg.click("#balUndo")
    after = pg.evaluate("""() => {
        const s = JSON.parse(localStorage.getItem('tax-ledger-v2'));
        return {m8: s.months[7], m9: s.months[8], m10: s.months[9], rows: s.rows.length};
    }""")
    out("撤销后：" + json.dumps(after, ensure_ascii=False)[:300])
    out("页面错误：" + (json.dumps(errs[:3], ensure_ascii=False) if errs else "无"))
    b.close()

open("_e2e.log", "w", encoding="utf-8").write("\n".join(log))
