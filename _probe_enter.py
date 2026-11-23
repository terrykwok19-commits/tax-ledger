# -*- coding: utf-8 -*-
"""探针3：抓「进账套」接口（能否用 cid 换 accountToken / 切账套）"""
import os, sys, json, io

SRC = r"D:\onedrive\Work\金哪达\自动入账模板\账务复核\codes\src"
sys.path.insert(0, SRC)
sys.dont_write_bytecode = True
os.environ["YQW_USER"] = "18620772739"
os.environ["YQW_PWD"] = "Jie19910901"

SKILL = os.path.join(os.path.expanduser("~"), ".workbuddy", "skills",
                     "yqwin-auto-voucher（亿企赢凭证生成）", "scripts")
sys.path.insert(0, SKILL)

from playwright.sync_api import sync_playwright           # noqa: E402
from yqwin_voucher import login_if_needed               # noqa: E402

B = "1906356153193"          # 超影拍（换一家，避免和缓存的 A 相同）
PROFILE = os.path.join(SRC, ".pw_profile_" + B)

hits = []

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(PROFILE, headless=True, viewport={"width": 1600, "height": 900})

    def on_req(r):
        u = r.url
        if "yqcs.17win.com" not in u:
            return
        if any(u.endswith(x) for x in (".js", ".css", ".png", ".jpg", ".svg", ".woff", ".woff2", ".ico")):
            return
        if r.resource_type in ("image", "stylesheet", "script", "font", "media"):
            return
        hits.append({"m": r.method, "url": u[:220], "post": (r.post_data or "")[:400]})

    ctx.on("request", on_req)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    login_if_needed(page, os.environ["YQW_USER"], os.environ["YQW_PWD"])
    page.goto(f"https://yqcs.17win.com/platform/yqjz?selectedCompanyId={B}",
              wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    # 点「进账套」
    pts = page.evaluate("""() => [...document.querySelectorAll('*')]
        .filter(e => e.children.length === 0 && (e.textContent||'').trim() === '进账套' && e.offsetParent)
        .map(e => { e.scrollIntoView({block:'center'}); const r = e.getBoundingClientRect();
                    return {x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)}; })""")
    print("进账套按钮:", pts)
    if pts:
        page.mouse.click(pts[0]["x"], pts[0]["y"])
        page.wait_for_timeout(10000)

    urls = [pg.url for pg in ctx.pages]
    print("\n打开的页面:")
    for u in urls:
        print("  ", u[:200])

    print("\n== 点击后发出的业务请求 ==")
    for h in hits:
        if any(k in h["url"] for k in ("account", "company", "token", "login", "enter", "switch", "yqjz")):
            print(json.dumps(h, ensure_ascii=False)[:600])

    io.open("_probe_enter.log", "w", encoding="utf-8").write(
        "\n".join("%s %s | %s" % (h["m"], h["url"], h["post"]) for h in hits))
    print("\n总请求数", len(hits), "→ _probe_enter.log")

    ctx.close()
