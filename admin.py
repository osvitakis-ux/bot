"""
Веб-панель адміна для бота «Константа»
Запускається разом з ботом через start.sh
"""

import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "konstanta2024")
ADMIN_PORT = int(os.environ.get("PORT", 8080))

_lock = threading.Lock()


def load_data():
    with _lock:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def save_data(data):
    with _lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ── HTML панелі (вбудовано прямо в admin.py) ──
ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Константа — Адмін</title>
<style>
:root{--bg:#0f1117;--s:#1a1d27;--s2:#222638;--b:#2d3148;--a:#5b6ef5;--ah:#7082ff;--as:rgba(91,110,245,.12);--g:#22c55e;--gs:rgba(34,197,94,.12);--r:#ef4444;--rs:rgba(239,68,68,.12);--am:#f59e0b;--t:#e8eaf0;--tm:#8b90a7;--td:#555870;--rad:10px;--radl:16px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--t);min-height:100vh;display:flex}
.sidebar{width:210px;background:var(--s);border-right:1px solid var(--b);display:flex;flex-direction:column;padding:20px 0;position:fixed;height:100vh}
.logo{padding:0 16px 20px;border-bottom:1px solid var(--b);margin-bottom:12px}
.logo h1{font-size:15px;font-weight:700}.logo span{font-size:11px;color:var(--tm)}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 16px;cursor:pointer;color:var(--tm);font-size:13px;font-weight:500;border-left:2px solid transparent;transition:.15s}
.nav-item:hover{color:var(--t);background:var(--as)}.nav-item.active{color:var(--a);background:var(--as);border-left-color:var(--a)}
.sidebar-footer{margin-top:auto;padding:14px 16px;border-top:1px solid var(--b);font-size:12px;color:var(--tm)}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--g);animation:pulse 2s infinite;margin-right:6px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.main{margin-left:210px;flex:1;padding:28px;max-width:calc(100vw - 210px)}
.page{display:none}.page.active{display:block}
.ph{margin-bottom:24px}.ph h2{font-size:20px;font-weight:700;letter-spacing:-.5px;margin-bottom:4px}.ph p{font-size:13px;color:var(--tm)}
.card{background:var(--s);border:1px solid var(--b);border-radius:var(--radl);padding:22px;margin-bottom:14px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}
.card-title{font-size:14px;font-weight:600}
label{display:block;font-size:11px;font-weight:600;color:var(--tm);margin-bottom:5px;text-transform:uppercase;letter-spacing:.5px}
input,textarea,select{width:100%;background:var(--s2);border:1px solid var(--b);border-radius:var(--rad);padding:9px 12px;color:var(--t);font-size:13px;font-family:inherit;outline:none;transition:border-color .15s}
input:focus,textarea:focus,select:focus{border-color:var(--a)}
textarea{resize:vertical;min-height:70px}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.fg3{grid-template-columns:1fr 1fr 1fr}.ffw{grid-column:1/-1}.field{margin-bottom:0}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:var(--rad);font-size:13px;font-weight:600;cursor:pointer;border:none;transition:.15s;font-family:inherit}
.btn-p{background:var(--a);color:#fff}.btn-p:hover{background:var(--ah);transform:translateY(-1px)}
.btn-g{background:transparent;color:var(--tm);border:1px solid var(--b)}.btn-g:hover{color:var(--t);border-color:var(--tm)}
.btn-d{background:var(--rs);color:var(--r)}.btn-d:hover{background:var(--r);color:#fff}
.btn-s{background:var(--gs);color:var(--g)}.btn-s:hover{background:var(--g);color:#fff}
.btn-sm{padding:5px 10px;font-size:11px}
.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.tc{background:var(--s2);border:1px solid var(--b);border-radius:var(--radl);padding:18px;transition:border-color .15s}.tc:hover{border-color:var(--a)}
.tav{width:50px;height:50px;border-radius:50%;background:var(--as);border:2px solid var(--a);display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:10px;overflow:hidden}
.tav img{width:100%;height:100%;object-fit:cover}
.tn{font-size:13px;font-weight:600;margin-bottom:3px}.tm{font-size:11px;color:var(--tm);margin-bottom:10px}
.tag{display:inline-flex;padding:2px 7px;border-radius:20px;font-size:11px;font-weight:500;background:var(--as);color:var(--a);margin:2px}
.tag.br{background:var(--gs);color:var(--g)}
.ta{display:flex;gap:6px;margin-top:12px;padding-top:12px;border-top:1px solid var(--b)}
.bi{background:var(--s2);border:1px solid var(--b);border-radius:var(--radl);padding:18px;display:grid;grid-template-columns:1fr auto;gap:14px;align-items:start;margin-bottom:10px}
.bn{font-size:14px;font-weight:600;margin-bottom:5px}.bd{font-size:12px;color:var(--tm);margin-bottom:2px}
.mo{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:100;align-items:center;justify-content:center}
.mo.open{display:flex}
.modal{background:var(--s);border:1px solid var(--b);border-radius:var(--radl);padding:26px;width:580px;max-width:95vw;max-height:90vh;overflow-y:auto}
.mh{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}
.mt{font-size:16px;font-weight:700}.xb{background:none;border:none;color:var(--tm);font-size:18px;cursor:pointer}
.sched{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:10px}
.dl{font-size:10px;font-weight:700;color:var(--tm);text-align:center;padding:3px 0;text-transform:uppercase}
.ts{background:var(--s2);border:1px solid var(--b);border-radius:5px;padding:3px 1px;font-size:10px;text-align:center;cursor:pointer;transition:.15s;margin-bottom:3px;color:var(--tm)}
.ts.on{background:var(--as);border-color:var(--a);color:var(--a);font-weight:700}.ts:hover{border-color:var(--a)}
.toast{position:fixed;bottom:20px;right:20px;background:var(--g);color:#fff;padding:10px 18px;border-radius:var(--rad);font-size:13px;font-weight:600;z-index:200;transform:translateY(60px);opacity:0;transition:.3s}
.toast.show{transform:translateY(0);opacity:1}
hr{border:none;border-top:1px solid var(--b);margin:18px 0}
.sl{font-size:10px;font-weight:700;color:var(--td);text-transform:uppercase;letter-spacing:1px;margin:20px 0 10px}
.pr{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;align-items:center;margin-bottom:7px}
.pr .gl{font-size:12px;color:var(--tm)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}
.sc{background:var(--s);border:1px solid var(--b);border-radius:var(--radl);padding:18px}
.sl2{font-size:12px;color:var(--tm);margin-bottom:6px}.sv{font-size:26px;font-weight:700;letter-spacing:-1px}.ss{font-size:11px;color:var(--tm);margin-top:3px}
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;width:100%;background:var(--bg)}
.login-box{background:var(--s);border:1px solid var(--b);border-radius:var(--radl);padding:36px;width:340px;text-align:center}
.login-box h2{margin-bottom:6px;font-size:18px}.login-box p{color:var(--tm);font-size:13px;margin-bottom:24px}
.login-box input{margin-bottom:14px}.login-err{color:var(--r);font-size:12px;margin-top:8px;display:none}
</style>
</head>
<body>

<!-- LOGIN -->
<div class="login-wrap" id="login-screen">
  <div class="login-box">
    <div style="font-size:36px;margin-bottom:12px">🎓</div>
    <h2>Константа</h2>
    <p>Адмін панель — введіть пароль</p>
    <label>Пароль</label>
    <input type="password" id="pwd" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()">
    <button class="btn btn-p" style="width:100%" onclick="doLogin()">Увійти</button>
    <div class="login-err" id="login-err">Невірний пароль</div>
  </div>
</div>

<!-- APP (hidden until login) -->
<div id="app" style="display:none;width:100%;display:none;flex-direction:row">

<aside class="sidebar">
  <div class="logo"><h1>🎓 Константа</h1><span>Адмін панель</span></div>
  <nav>
    <div class="nav-item active" onclick="showPage('dashboard',this)"><span>📊</span> Дашборд</div>
    <div class="nav-item" onclick="showPage('tutors',this)"><span>👩‍🏫</span> Репетитори</div>
    <div class="nav-item" onclick="showPage('branches',this)"><span>📍</span> Філіали</div>
    <div class="nav-item" onclick="showPage('subjects',this)"><span>📚</span> Предмети</div>
    <div class="nav-item" onclick="showPage('feedbacks',this)"><span>💬</span> Відгуки</div>
  </nav>
  <div class="sidebar-footer"><span class="dot"></span>Бот активний</div>
</aside>

<main class="main">

  <!-- DASHBOARD -->
  <div class="page active" id="page-dashboard">
    <div class="ph"><h2>Дашборд</h2><p>Загальний огляд</p></div>
    <div class="stats">
      <div class="sc"><div class="sl2">Репетиторів</div><div class="sv" id="s-tutors" style="color:var(--a)">—</div><div class="ss">У базі</div></div>
      <div class="sc"><div class="sl2">Філіалів</div><div class="sv" id="s-branches" style="color:var(--g)">3</div><div class="ss">Активних</div></div>
      <div class="sc"><div class="sl2">Предметів</div><div class="sv" id="s-subjects" style="color:var(--am)">—</div><div class="ss">У каталозі</div></div>
      <div class="sc"><div class="sl2">Відгуків</div><div class="sv" id="s-feedbacks" style="color:var(--g)">—</div><div class="ss">Від клієнтів</div></div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">💡 Швидкі дії</span></div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <button class="btn btn-p" onclick="showPage('tutors',document.querySelectorAll('.nav-item')[1]);openAddTutor()">＋ Додати репетитора</button>
        <button class="btn btn-g" onclick="showPage('branches',document.querySelectorAll('.nav-item')[2])">✏️ Редагувати філіали</button>
        <button class="btn btn-g" onclick="showPage('subjects',document.querySelectorAll('.nav-item')[3])">💰 Змінити ціни</button>
      </div>
    </div>
  </div>

  <!-- TUTORS -->
  <div class="page" id="page-tutors">
    <div class="ph"><h2>Репетитори</h2><p>Профілі, розклад, фото</p></div>
    <div style="margin-bottom:16px"><button class="btn btn-p" onclick="openAddTutor()">＋ Додати репетитора</button></div>
    <div class="tgrid" id="tutor-grid"></div>
  </div>

  <!-- BRANCHES -->
  <div class="page" id="page-branches">
    <div class="ph"><h2>Філіали</h2><p>Адреси, телефони, режим роботи</p></div>
    <div id="branch-list"></div>
  </div>

  <!-- SUBJECTS -->
  <div class="page" id="page-subjects">
    <div class="ph"><h2>Предмети та ціни</h2><p>Редагуйте ціни — зберігається автоматично</p></div>
    <div id="subjects-list"></div>
  </div>

  <!-- FEEDBACKS -->
  <div class="page" id="page-feedbacks">
    <div class="ph"><h2>Відгуки</h2><p>Всі відгуки від клієнтів через бота</p></div>
    <div id="feedbacks-list"></div>
  </div>

</main>
</div>

<!-- MODAL TUTOR -->
<div class="mo" id="modal-tutor">
  <div class="modal">
    <div class="mh"><span class="mt" id="modal-title">Додати репетитора</span><button class="xb" onclick="closeMod('modal-tutor')">✕</button></div>
    <div class="fg">
      <div class="field ffw"><label>ПІБ</label><input id="t-name" placeholder="Прізвище Ім'я По-батькові"></div>
      <div class="field"><label>Досвід</label><input id="t-exp" placeholder="5 років"></div>
      <div class="field"><label>Філіал</label><select id="t-branch" style=""></select></div>
      <div class="field ffw"><label>Освіта</label><input id="t-edu" placeholder="Університет, факультет"></div>
      <div class="field ffw"><label>Біографія</label><textarea id="t-bio" placeholder="2-3 речення про підхід та досягнення..."></textarea></div>
      <div class="field"><label>Ціна (від)</label><input id="t-price" placeholder="від 450 грн/год"></div>
      <div class="field"><label>Предмети</label><div id="subj-cb" style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px"></div></div>
      <div class="field ffw"><label>Фото — Telegram file_id</label><input id="t-photo" placeholder="AgACAgI... (надішліть фото боту)"><div style="font-size:11px;color:var(--tm);margin-top:5px">💡 Надішліть фото боту — він відповість file_id</div></div>
    </div>
    <div class="sl">Розклад вільних годин — клікніть для позначення</div>
    <div class="sched" id="sched-builder"></div>
    <hr>
    <div style="display:flex;gap:8px;justify-content:flex-end">
      <button class="btn btn-g" onclick="closeMod('modal-tutor')">Скасувати</button>
      <button class="btn btn-p" onclick="saveTutor()">💾 Зберегти</button>
    </div>
  </div>
</div>

<!-- MODAL BRANCH -->
<div class="mo" id="modal-branch">
  <div class="modal">
    <div class="mh"><span class="mt" id="bmodal-title">Редагувати філіал</span><button class="xb" onclick="closeMod('modal-branch')">✕</button></div>
    <div class="fg">
      <div class="field ffw"><label>Назва</label><input id="b-name"></div>
      <div class="field ffw"><label>Адреса</label><input id="b-address"></div>
      <div class="field"><label>Телефон</label><input id="b-phone"></div>
      <div class="field"><label>Транспорт</label><input id="b-transport"></div>
      <div class="field ffw"><label>Режим роботи</label><input id="b-schedule"></div>
      <div class="field ffw"><label>Google Maps URL</label><input id="b-map"></div>
    </div>
    <hr>
    <div style="display:flex;gap:8px;justify-content:flex-end">
      <button class="btn btn-g" onclick="closeMod('modal-branch')">Скасувати</button>
      <button class="btn btn-p" onclick="saveBranch()">💾 Зберегти</button>
    </div>
  </div>
</div>

<div class="toast" id="toast">✅ Збережено!</div>

<script>
const DAYS=["Пн","Вт","Ср","Чт","Пт","Сб","Нд"];
const TIMES=["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00"];
let D={tutors:{},branches:{},subjects:{},feedbacks:[]};
let editTid=null, editBid=null, schedState={};

// ── LOGIN ──
function doLogin(){
  const p=document.getElementById('pwd').value;
  fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p})})
    .then(r=>r.json()).then(r=>{
      if(r.ok){
        document.getElementById('login-screen').style.display='none';
        const app=document.getElementById('app');
        app.style.display='flex';
        loadData();
      } else {
        document.getElementById('login-err').style.display='block';
      }
    });
}

// ── DATA ──
function loadData(){
  fetch('/api/data').then(r=>r.json()).then(d=>{
    D=d;
    updateStats();
  });
}

function saveSection(section, payload){
  fetch('/api/save',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({section, data: payload})
  }).then(r=>r.json()).then(r=>{
    if(r.ok) showToast('✅ Збережено!');
    else showToast('❌ Помилка збереження');
  });
}

function updateStats(){
  document.getElementById('s-tutors').textContent=Object.keys(D.tutors||{}).length;
  document.getElementById('s-subjects').textContent=Object.keys(D.subjects||{}).length;
  document.getElementById('s-feedbacks').textContent=(D.feedbacks||[]).length;
}

// ── NAVIGATION ──
function showPage(id, el){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  if(el) el.classList.add('active');
  if(id==='tutors') renderTutors();
  if(id==='branches') renderBranches();
  if(id==='subjects') renderSubjects();
  if(id==='feedbacks') renderFeedbacks();
}

// ── TUTORS ──
function renderTutors(){
  const g=document.getElementById('tutor-grid');
  g.innerHTML=Object.entries(D.tutors||{}).map(([id,t])=>`
    <div class="tc">
      <div class="tav">${t.photo_id?`<img src="${t.photo_id}" onerror="this.parentNode.innerHTML='👤'">`:'👤'}</div>
      <div class="tn">${t.name}</div>
      <div class="tm">📍 ${D.branches[t.branch]?.name||t.branch} · ${t.experience||''}</div>
      <div>${(t.subjects||[]).map(s=>`<span class="tag">${D.subjects[s]?.emoji||''} ${D.subjects[s]?.name||s}</span>`).join('')}</div>
      <div class="ta">
        <button class="btn btn-g btn-sm" onclick="editTutor('${id}')">✏️ Ред.</button>
        <button class="btn btn-s btn-sm" onclick="editTutor('${id}')">🗓 Розклад</button>
        <button class="btn btn-d btn-sm" onclick="deleteTutor('${id}')">🗑</button>
      </div>
    </div>`).join('');
}

function buildSchedGrid(schedule={}){
  schedState={};
  DAYS.forEach(d=>{ schedState[d]={}; TIMES.forEach(t=>{ schedState[d][t]=(schedule[d]||[]).includes(t); }); });
  return `<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px">
    ${DAYS.map(d=>`<div><div class="dl">${d}</div>${TIMES.map(t=>`<div class="ts ${schedState[d][t]?'on':''}" onclick="togSlot('${d}','${t}',this)">${t.slice(0,5)}</div>`).join('')}</div>`).join('')}
  </div>`;
}

function togSlot(d,t,el){ schedState[d][t]=!schedState[d][t]; el.classList.toggle('on'); }

function buildBranchOpts(selected=''){
  return Object.entries(D.branches||{}).map(([k,b])=>`<option value="${k}" ${k===selected?'selected':''}>${b.name}</option>`).join('');
}

function buildSubjCbs(selected=[]){
  return Object.entries(D.subjects||{}).map(([k,s])=>`
    <label style="display:inline-flex;align-items:center;gap:4px;cursor:pointer;font-size:12px;color:var(--t);text-transform:none;letter-spacing:0;margin:2px">
      <input type="checkbox" value="${k}" ${selected.includes(k)?'checked':''} style="width:auto"> ${s.emoji} ${s.name}
    </label>`).join('');
}

function openAddTutor(){
  editTid=null;
  document.getElementById('modal-title').textContent='Додати репетитора';
  ['t-name','t-exp','t-edu','t-bio','t-price','t-photo'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('t-branch').innerHTML=buildBranchOpts();
  document.getElementById('subj-cb').innerHTML=buildSubjCbs();
  document.getElementById('sched-builder').innerHTML=buildSchedGrid();
  document.getElementById('modal-tutor').classList.add('open');
}

function editTutor(id){
  editTid=id; const t=D.tutors[id];
  document.getElementById('modal-title').textContent='Редагувати репетитора';
  document.getElementById('t-name').value=t.name||'';
  document.getElementById('t-exp').value=t.experience||'';
  document.getElementById('t-edu').value=t.education||'';
  document.getElementById('t-bio').value=t.bio||'';
  document.getElementById('t-price').value=t.price_note||'';
  document.getElementById('t-photo').value=t.photo_id||'';
  document.getElementById('t-branch').innerHTML=buildBranchOpts(t.branch);
  document.getElementById('subj-cb').innerHTML=buildSubjCbs(t.subjects||[]);
  document.getElementById('sched-builder').innerHTML=buildSchedGrid(t.schedule||{});
  document.getElementById('modal-tutor').classList.add('open');
}

function saveTutor(){
  const name=document.getElementById('t-name').value.trim();
  if(!name){alert('Введіть ПІБ'); return;}
  const subjects=[...document.querySelectorAll('#subj-cb input:checked')].map(i=>i.value);
  const schedule={};
  DAYS.forEach(d=>{ const h=TIMES.filter(t=>schedState[d]?.[t]); if(h.length) schedule[d]=h; });
  const tutor={name,experience:document.getElementById('t-exp').value,education:document.getElementById('t-edu').value,
    bio:document.getElementById('t-bio').value,price_note:document.getElementById('t-price').value,
    photo_id:document.getElementById('t-photo').value,branch:document.getElementById('t-branch').value,subjects,schedule};
  if(editTid) D.tutors[editTid]=tutor;
  else D.tutors['t'+Date.now()]=tutor;
  saveSection('tutors', D.tutors);
  closeMod('modal-tutor');
  renderTutors();
  updateStats();
}

function deleteTutor(id){
  if(!confirm(`Видалити ${D.tutors[id].name}?`)) return;
  delete D.tutors[id];
  saveSection('tutors', D.tutors);
  renderTutors();
  showToast('🗑 Видалено');
}

// ── BRANCHES ──
function renderBranches(){
  document.getElementById('branch-list').innerHTML=Object.entries(D.branches||{}).map(([id,b])=>`
    <div class="bi">
      <div><div class="bn">📍 ${b.name}</div><div class="bd">🏠 ${b.address}</div><div class="bd">📞 ${b.phone}</div><div class="bd">🕐 ${b.schedule}</div><div class="bd">${b.transport}</div></div>
      <button class="btn btn-g btn-sm" onclick="editBranch('${id}')">✏️ Редагувати</button>
    </div>`).join('');
}

function editBranch(id){
  editBid=id; const b=D.branches[id];
  document.getElementById('bmodal-title').textContent='Редагувати: '+b.name;
  document.getElementById('b-name').value=b.name||'';
  document.getElementById('b-address').value=b.address||'';
  document.getElementById('b-phone').value=b.phone||'';
  document.getElementById('b-transport').value=b.transport||'';
  document.getElementById('b-schedule').value=b.schedule||'';
  document.getElementById('b-map').value=b.map_url||'';
  document.getElementById('modal-branch').classList.add('open');
}

function saveBranch(){
  D.branches[editBid]={name:document.getElementById('b-name').value,address:document.getElementById('b-address').value,
    phone:document.getElementById('b-phone').value,transport:document.getElementById('b-transport').value,
    schedule:document.getElementById('b-schedule').value,map_url:document.getElementById('b-map').value};
  saveSection('branches', D.branches);
  closeMod('modal-branch');
  renderBranches();
}

// ── SUBJECTS ──
function renderSubjects(){
  document.getElementById('subjects-list').innerHTML=Object.entries(D.subjects||{}).map(([key,s])=>`
    <div class="card" style="margin-bottom:12px">
      <div class="card-header"><span class="card-title">${s.emoji} ${s.name}</span></div>
      <div class="fg" style="margin-bottom:10px">
        <div class="field ffw"><label>Опис</label><input value="${s.desc||''}" onchange="D.subjects['${key}'].desc=this.value" onblur="saveSection('subjects',D.subjects)"></div>
      </div>
      <div class="sl">Ціни (грн / 60 хв)</div>
      ${Object.entries(s.prices||{}).map(([grade,p])=>`
        <div class="pr">
          <span class="gl">${grade}</span>
          <div><label>Індивід.</label><input type="number" value="${p['індив']||0}" style="width:90px" onchange="D.subjects['${key}'].prices['${grade}']['індив']=+this.value" onblur="saveSection('subjects',D.subjects)"></div>
          <div><label>Група</label><input type="number" value="${p['група']||0}" style="width:90px" onchange="D.subjects['${key}'].prices['${grade}']['група']=+this.value" onblur="saveSection('subjects',D.subjects)"></div>
        </div>`).join('')}
    </div>`).join('');
}

// ── FEEDBACKS ──
function renderFeedbacks(){
  const fb=D.feedbacks||[];
  document.getElementById('feedbacks-list').innerHTML=fb.length
    ? fb.slice().reverse().map(f=>`
        <div class="card" style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <b>${f.user||'Анонім'}</b><span style="color:var(--am)">${'⭐'.repeat(+f.rating||0)}</span>
          </div>
          <div style="font-size:13px;color:var(--tm);margin-bottom:6px">${f.text||''}</div>
          <div style="font-size:11px;color:var(--td)">${f.date||''}</div>
        </div>`).join('')
    : '<div style="color:var(--tm);text-align:center;padding:40px">Відгуків ще немає</div>';
}

// ── UTILS ──
function closeMod(id){ document.getElementById(id).classList.remove('open'); }
function showToast(msg){ const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),3000); }
</script>
</body>
</html>"""


class AdminHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # вимкнути стандартні логи

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/admin":
            self._send(200, "text/html", ADMIN_HTML.encode("utf-8"))
        elif path == "/api/data":
            d = load_data()
            self._send(200, "application/json", json.dumps(d, ensure_ascii=False).encode())
        else:
            self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/login":
            ok = body.get("password") == ADMIN_PASSWORD
            self._send(200, "application/json", json.dumps({"ok": ok}).encode())

        elif path == "/api/save":
            section = body.get("section")
            payload = body.get("data")
            if section and payload is not None:
                d = load_data()
                d[section] = payload
                save_data(d)
                self._send(200, "application/json", b'{"ok":true}')
            else:
                self._send(400, "application/json", b'{"ok":false}')
        else:
            self._send(404, "text/plain", b"Not found")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_admin_server():
    server = HTTPServer(("0.0.0.0", ADMIN_PORT), AdminHandler)
    logging.info(f"🌐 Адмін панель запущена на порту {ADMIN_PORT}")
    server.serve_forever()


def start_admin_in_thread():
    t = threading.Thread(target=run_admin_server, daemon=True)
    t.start()
