# -*- coding: utf-8 -*-
"""给 收入税费表/index.html 打补丁：加「亿企赢取数」面板"""
import io, os

P = "D:/onedrive/Work/金哪达/自动入账模板/收入税费表/index.html"
s = io.open(P, encoding="utf-8").read()
n0 = len(s)


def rep(old, new, cnt=1):
    global s
    assert old in s, "NOT FOUND: " + old[:80]
    s = s.replace(old, new, cnt)


# ---------- 1) 工具栏按钮
rep('''    <button id="btnBalanceMulti" title="一次选多个余额表（一般是一家公司的 1–12 月），每个文件各写各的月份；先给汇总预览，确认后才动台账">批量导入</button>''',
'''    <button id="btnBalanceMulti" title="一次选多个余额表（一般是一家公司的 1–12 月），每个文件各写各的月份；先给汇总预览，确认后才动台账">批量导入</button>
    <button id="btnYqy" title="按台账公司绑定的亿企赢账套，自动取科目余额表填台账（要先双击「启动.bat」运行取数服务）">亿企赢取数</button>''')

# ---------- 2) CSS
rep('''.dlg-b table.batch td:first-child{word-break:break-all;max-width:260px;}''',
'''.dlg-b table.batch td:first-child{word-break:break-all;max-width:260px;}
.yqy-f{display:flex;gap:16px;flex-wrap:wrap;margin:4px 2px 12px;}
.yqy-f label{display:flex;align-items:center;gap:7px;font-size:12.5px;color:var(--muted);}
.yqy-f input{border:1px solid var(--line-strong);border-radius:7px;padding:5px 8px;
  font:inherit;font-size:12.5px;background:var(--card);color:var(--text);width:200px;}''')

# ---------- 3) 弹窗
rep('''<script>
(function(){
"use strict";''',
'''<div class="mask" id="yqyMask">
  <div class="dlg" style="max-width:560px" role="dialog" aria-modal="true">
    <div class="dlg-h">从亿企赢取数 <span class="muted" id="yqyState">检查服务…</span></div>
    <div class="dlg-b">
      <div class="yqy-f">
        <label>公司<input id="yqyCo" list="yqyCos" placeholder="广州金哪达贸易有限公司"></label>
        <datalist id="yqyCos"></datalist>
      </div>
      <div class="yqy-f">
        <label>起始月<input type="month" id="yqyFrom"></label>
        <label>结束月<input type="month" id="yqyTo"></label>
      </div>
      <div class="tip" id="yqyTip">取数只读，不动账。取回来的每月先给预览，确认后才写台账。</div>
    </div>
    <div class="dlg-f">
      <button class="left" id="yqyClose">取消</button>
      <button class="primary" id="yqyGo" disabled>开始取数</button>
    </div>
  </div>
</div>

<script>
(function(){
"use strict";''')

# ---------- 4) 批量预览支持标题 / 告警
rep('''  $("balHead").innerHTML = "批量导入预览 · " + balBatch.year + " 年" +''',
'''  $("balHead").innerHTML = (balBatch.title || "批量导入预览") + " · " + balBatch.year + " 年" +''')
rep('''  $("balBody").innerHTML = batchTable(false) +
    (st.out.length ? ''',
'''  $("balBody").innerHTML = batchTable(false) +
    (balBatch.warn ? '<div class="tip" style="color:var(--manual-bd)">余额表勾稽告警：' + esc(balBatch.warn) +
      "。数据照常可写，先看一眼再确认。</div>" : "") +
    (st.out.length ? ''')

# ---------- 5) 取数逻辑（插在 balBatch 声明前）
rep('''let balBatch = null;                    // {year, company, rows:[{file, plan, why}], dupHint}''',
'''/* ================= 亿企赢取数（本地服务） =================
   服务：server.py（双击「启动.bat」）。同源托管时直接用当前 origin，file:// 打开时探
   8765–8776。取回的是接口原始行 → 合成一张「科目余额表」矩阵 → 完全走 planBalance
   那条链路，预览 / 项目同步 / 撤销都不另写。 */
let YQY_BASE = "", YQY_INFO = null;
async function yqyPing(base){
  const ac = new AbortController(), t = setTimeout(()=>ac.abort(), 2500);
  try{
    const r = await fetch(base + "/api/status", {signal: ac.signal});
    if(!r.ok) return null;
    const j = await r.json();
    return j && j.ok ? j : null;
  }catch(e){ return null; }
  finally{ clearTimeout(t); }
}
async function yqyDiscover(){
  if(YQY_BASE) return YQY_BASE;
  const bases = [];
  if(location.protocol === "http:" && location.port) bases.push(location.origin);
  for(let p = 8765; p <= 8776; p++) bases.push("http://127.0.0.1:" + p);
  const rs = await Promise.all(bases.map(async b => [b, await yqyPing(b)]));
  const hit = rs.find(x => x[1]);
  if(!hit) return "";
  YQY_BASE = hit[0]; YQY_INFO = hit[1];
  return YQY_BASE;
}
async function yqyOpen(){
  $("yqyCo").value = S.company || "";
  const d = new Date(), ym = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
  if(!$("yqyFrom").value) $("yqyFrom").value = ym;
  if(!$("yqyTo").value)   $("yqyTo").value = ym;
  $("yqyState").textContent = "检查服务…";
  $("yqyGo").disabled = true;
  $("yqyMask").classList.add("on");
  const base = await yqyDiscover();
  if(!base){
    $("yqyState").textContent = "取数服务没启动";
    $("yqyTip").innerHTML = "没连上本地取数服务。先双击项目里的 <b>启动.bat</b>（会开一个小黑窗，别关），" +
      "再回来点这里。<br>不想起服务就照旧用「导入余额表」，把亿企赢导出的 Excel 拖进来。";
    return;
  }
  YQY_INFO = await yqyPing(base) || YQY_INFO;
  $("yqyState").textContent = "服务已连接";
  $("yqyGo").disabled = false;
  $("yqyCos").innerHTML = ((YQY_INFO && YQY_INFO.companies) || [])
    .map(c => '<option value="' + esc(c.name) + '">').join("");
  $("yqyTip").innerHTML = (YQY_INFO && YQY_INFO.creds)
    ? "取数只读，不动账。按公司绑定的账套取「本期发生额」，取回来每月先给预览，确认后才写台账。"
    : '<span style="color:var(--red)">服务起来了，但缺 config/creds.json（亿企赢账号密码），补上再取。</span>';
}
async function yqyRun(){
  const co = $("yqyCo").value.trim(), a = $("yqyFrom").value, b = $("yqyTo").value;
  if(!co) return alert("先填公司名（要和台账里的公司对得上）");
  if(!a || !b) return alert("选起始月和结束月");
  $("yqyGo").disabled = true;
  $("yqyState").textContent = "取数中…（要登录 + 进账套，首次约 20–60 秒）";
  const ac = new AbortController(), t = setTimeout(()=>ac.abort(), 300000);
  try{
    const r = await fetch(YQY_BASE + "/api/fetch", {method:"POST", signal: ac.signal,
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({company: co, from: a, to: b})});
    const j = await r.json().catch(()=>({ok:false, error:"服务返回的不是 JSON"}));
    if(!r.ok || !j.ok) throw new Error(j.error || ("HTTP " + r.status));
    $("yqyMask").classList.remove("on");
    yqyApply(j);
  }catch(err){
    $("yqyState").textContent = "失败";
    $("yqyTip").innerHTML = '<span style="color:var(--red)">' + esc(err.message) + "</span>";
    $("yqyGo").disabled = false;
  }finally{ clearTimeout(t); }
}
/* 接口行 → 与科目余额表 xlsx 同构的矩阵（表头写两层，和真实导出一样） */
function yqyMatrix(m, company){
  const [y, mo] = m.period.split("-").map(Number);
  return [
    ["科目余额表", y + "年" + mo + "月"],
    ["核算单位：" + company],
    ["", "", "期初余额", "", "本期发生额", "", "本年累计发生额", "", "期末余额", ""],
    ["科目编码", "科目名称", "借方", "贷方", "借方", "贷方", "借方", "贷方", "借方", "贷方"]
  ].concat(m.rows.map(r => [r.code, r.name, "", "", r.debit, r.credit, "", "", "", ""]));
}
function yqyApply(res){
  balPending = null;
  balBatch = {
    title: "亿企赢取数预览",
    raw: res.months.map(m => ({file: res.key + " " + m.period + ".json",
                               matrix: yqyMatrix(m, res.company)})),
    rows: [], year: S.year, company: S.company || res.company, dupHint: "",
    warn: (res.warnings || []).slice(0, 3).join("；")
  };
  recomputeBatch();
  showBalBatchPreview();
}
$("btnYqy").addEventListener("click", yqyOpen);
$("yqyGo").addEventListener("click", yqyRun);
$("yqyClose").addEventListener("click", ()=>$("yqyMask").classList.remove("on"));
$("yqyMask").addEventListener("click", e=>{ if(e.target === $("yqyMask")) $("yqyMask").classList.remove("on"); });

let balBatch = null;                    // {year, company, rows:[{file, plan, why}], dupHint}''')

io.open(P, "w", encoding="utf-8").write(s)
print("patched: %d → %d bytes" % (n0, len(s)))
