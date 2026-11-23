# -*- coding: utf-8 -*-
"""探针：亿企赢余额表接口能否指定账套 cid（决定书签方案是否可行）"""
import os, sys, json

SRC = r"D:\onedrive\Work\金哪达\自动入账模板\账务复核\codes\src"
sys.path.insert(0, SRC)
sys.dont_write_bytecode = True

os.environ["YQW_USER"] = "18620772739"
os.environ["YQW_PWD"] = "Jie19910901"

from yqwin_session import open_finance_page          # noqa: E402
from fetch_balance import build_payload, API         # noqa: E402

A = "1906339837704"      # 金哪达贸易
B = "1906356153193"      # 超影拍

JS = """async ([url, payload, headers]) => {
  const ac = new AbortController();
  const tid = setTimeout(() => ac.abort(), 60000);
  try {
    const r = await fetch(url, {method:'POST',
      headers: Object.assign({'Content-Type':'application/json;charset=UTF-8'}, headers||{}),
      body: JSON.stringify(payload), credentials:'include', signal: ac.signal});
    const t = await r.text();
    let j = null; try { j = JSON.parse(t); } catch(e) {}
    return {status: r.status, head: j && j.head, n: j && j.body && (j.body.list||[]).length,
            total: j && j.body && j.body.total,
            sample: j && j.body && (j.body.list||[]).slice(0,2).map(x=>[x.titleCode,x.titleName,x.occurredDebit,x.occurredCredit]),
            codes: j && j.body ? (j.body.list||[]).filter(x=>x.titleCode&&String(x.titleCode).startsWith('5')).slice(0,6).map(x=>[x.titleCode,x.titleName,x.occurredCredit]) : null};
  } catch(e) { return {status:-1, err:String(e)}; }
  finally { clearTimeout(tid); }
}"""


def run(fin, label, headers=None, extra=None):
    p = build_payload("2026-10")
    if extra:
        p.update(extra)
    r = fin.evaluate(JS, [API, p, headers or {}])
    print(f"\n--- {label} | status={r.get('status')} head={(r.get('head') or {}).get('code')} n={r.get('n')} total={r.get('total')}")
    if r.get("err"):
        print("   ERR", r["err"])
    print("   5xx:", r.get("codes"))
    return r


with open_finance_page(A, headless=True) as fin:
    print("finance url:", fin.url)
    ck = fin.context.cookies()
    print("cookies:", sorted({c["name"] for c in ck if "compan" in c["name"].lower()
                              or "org" in c["name"].lower() or "tenant" in c["name"].lower()}))
    base = run(fin, "A 基准（无附加）")
    run(fin, "B header companyId", headers={"companyId": B})
    run(fin, "B header company-id", headers={"company-id": B})
    run(fin, "B header selectedCompanyId", headers={"selectedCompanyId": B})
    run(fin, "B header X-Company-Id", headers={"X-Company-Id": B})
    run(fin, "B payload companyId", extra={"companyId": B})
    run(fin, "B payload selectedCompanyId", extra={"selectedCompanyId": B})
    # 再取一次 A 基准，确认上面没把状态改掉
    run(fin, "A 基准复测")
