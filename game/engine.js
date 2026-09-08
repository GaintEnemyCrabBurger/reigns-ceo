/* 《任职》引擎 —— 照王权那套跑：读表、算条件、按权重抽、按 > 跳 */
'use strict';

const RES = [
  {k:'cash',   n:'现金流'},
  {k:'team',   n:'团队'},
  {k:'market', n:'市场'},
  {k:'capital',n:'资本'},
];

// 八种下台方式：留给下一任什么
const ENDINGS = {
  '破产清算': {kicker:'现金流 归零', body:'供应商堵在门口，账上一分钱没有。清算组进场那天，工牌是保安帮你摘的。',
    next:{cash:15,team:40,market:40,capital:35}, carry:'下一任接手：一身债，前十个回合催款不断。', flag:'debt_keep'},
  '守财奴':   {kicker:'现金流 爆表', body:'账上趴着十一个亿，两年没动过。董事会说，我们需要一个敢花钱的人。',
    next:{cash:85,team:50,market:25,capital:50}, carry:'下一任接手：钱很多，但整个窗口期已经错过了。'},
  '人去楼空': {kicker:'团队 归零', body:'最后三个人办完离职。整层楼的灯你自己关的。',
    next:{cash:45,team:15,market:35,capital:40}, carry:'下一任接手：行业里都知道这儿留不住人，招聘难度翻倍。', flag:'badrep_keep'},
  '大锅饭':   {kicker:'团队 爆表', body:'两千一百人，人力成本吃掉全部毛利。没人愿意做那个签裁员名单的人。',
    next:{cash:25,team:85,market:45,capital:45}, carry:'下一任接手：第一件事就是裁员。'},
  '无人问津': {kicker:'市场 归零', body:'官网昨天的访问量是十七，其中十四个是爬虫。产品还在，只是没有人需要它了。',
    next:{cash:40,team:45,market:15,capital:35}, carry:'下一任接手：得从头找一遍，客户到底要什么。'},
  '爆单崩盘': {kicker:'市场 爆表', body:'在手订单排到二十八个月后，客户开始集体索赔。签得越多，赔得越多。',
    next:{cash:45,team:20,market:80,capital:40}, carry:'下一任接手：单子满手，人全累垮了。'},
  '一致行动': {kicker:'资本 归零', body:'那个会你没参加。七个董事，七票通过。下午三点交接，你的门禁十五分钟后失效。',
    next:{cash:50,team:45,market:45,capital:20}, carry:'下一任接手：董事会盯得极紧，重大决策都要走流程。'},
  '功成身退': {kicker:'资本 爆表', body:'八号敲钟，解禁期谈到了最短。所有人都恭喜你，包括那个接你位子的人。\n\n这是唯一算赢的结局。你还是走了。',
    next:{cash:60,team:50,market:55,capital:85}, carry:'下一任接手：一家上市公司，处处受限。', flag:'public_keep', win:true},
};

let S;   // state
let byName = {};
let cur = null, curIdx = -1, forced = null, busy = false;

function initState(seed, dyn, keep){
  S = {
    cash:seed.cash, team:seed.team, market:seed.market, capital:seed.capital,
    dynasty:dyn, turn:0, month:0, year:2015 + (dyn-1)*2,
    flags:Object.assign({}, keep||{}),   // _keep 跨任保留
    lock:{},                            // card -> 解锁回合
    seen:{},
  };
}

/* ---------- 条件 ---------- */
function val(name){
  if (name==='cash'||name==='money')   return S.cash;
  if (name==='team')                   return S.team;
  if (name==='market')                 return S.market;
  if (name==='capital')                return S.capital;
  if (name==='dynasty')                return S.dynasty;
  if (name==='turn')                   return S.turn;
  if (name==='year')                   return S.year;
  if (name==='overall')                return Math.round((S.cash+S.team+S.market+S.capital)/4);
  if (/^nb_/.test(name))               return S.flags[name]|0;
  return S.flags[name] ? 1 : 0;
}

function testOne(t){
  t = t.trim();
  if (!t) return true;
  let m = t.match(/^([a-zA-Z_][\w]*)\s*(>=|<=|>|<|=)\s*(-?\d+)$/);
  if (m){
    const a = val(m[1]), b = parseInt(m[3],10);
    switch(m[2]){
      case '>':  return a >  b;
      case '<':  return a <  b;
      case '=':  return a === b;
      case '>=': return a >= b;
      case '<=': return a <= b;
    }
  }
  if (t[0]==='!') return !val(t.slice(1));
  return !!val(t);
}

function testCond(str){
  if (!str || !str.trim()) return true;
  return str.split(/\s+and\s+/).every(testOne);
}

/* ---------- 抽卡 ---------- */
function pick(){
  if (forced){
    const f = forced; forced = null;
    return f;
  }
  const pool = [];
  let best = 0;
  for (let i=0;i<CARDS.length;i++){
    const c = CARDS[i];
    if (!c.weight) continue;                       // 续写卡：永不随机抽中
    if (S.lock[c.card] && S.turn < S.lock[c.card]) continue;
    if (!testCond(c.conditions)) continue;
    const w = c.weight === 'max' ? 1e9 : parseInt(c.weight,10);
    if (!w || isNaN(w)) continue;
    if (w > best) best = w;
    pool.push([i,w]);
  }
  if (!pool.length) return -1;
  // 高权重压倒：只在最高一档里随机（死亡卡就是靠这个必出的）
  const top = pool.filter(p => p[1] >= best*0.5);
  const use = best >= 1000 ? pool.filter(p=>p[1]===best) : top;
  let sum = 0; use.forEach(p=>sum+=p[1]);
  let r = Math.random()*sum;
  for (const p of use){ r -= p[1]; if (r<=0) return p[0]; }
  return use[use.length-1][0];
}

/* ---------- 应用结果 ---------- */
function applyFlags(str, idx){
  if (!str) return;
  str.split(/\s+and\s+/).forEach(tok=>{
    let t = tok.trim();
    if (!t) return;
    if (t[0]==='>'){                                  // 跳转
      const arrows = t.match(/^>+/)[0].length;
      const rest = t.slice(arrows);
      if (rest && rest[0]==='_'){
        const tgt = byName[rest.slice(1)];
        if (tgt!==undefined) forced = tgt;
      } else if (rest && byName[rest]!==undefined){
        forced = byName[rest];
      } else if (rest && /^\d+$/.test(rest)){
        forced = idx + parseInt(rest,10);
      } else {
        forced = idx + arrows;
      }
      return;
    }
    if (t.slice(-1)==='+'){                            // 计数器
      const base = t.replace(/\++$/,'');
      S.flags[base] = (S.flags[base]|0) + (t.length - base.length);
      return;
    }
    if (t[0]==='!'){ delete S.flags[t.slice(1)]; return; }
    if (/^(del|add)_/.test(t)){ S.flags[t] = 1; return; }
    if (/^mus_/.test(t)) return;                       // 音乐指令，原型里忽略
    S.flags[t] = 1;
  });
}

function num(v){
  if (!v) return 0;
  v = String(v).replace(/[?*]/g,'').trim();
  if (!v) return 0;
  const m = v.match(/^-?\d+/);
  return m ? parseInt(m[0],10) : 0;
}

/* ---------- 渲染 ---------- */
const $ = s => document.querySelector(s);
const stage = $('#stage'), veil = $('#veil'), ansEl = $('#answer');

function drawBars(flashKeys){
  const box = $('#bars');
  if (!box.children.length){
    box.innerHTML = RES.map(r=>
      `<div class="bar" data-k="${r.k}">
         <div class="dot"></div>
         <div class="track"><div class="fill"></div></div>
         <div class="lbl">${r.n}</div><div class="num"></div></div>`).join('');
  }
  RES.forEach(r=>{
    const el = box.querySelector(`[data-k="${r.k}"]`);
    const v = Math.max(0, Math.min(100, S[r.k]));
    el.querySelector('.fill').style.width = v + '%';
    el.querySelector('.num').textContent = v;
    el.classList.toggle('warn', v<=20 || v>=80);
    if (flashKeys && flashKeys.indexOf(r.k)>=0){
      el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
    }
  });
  $('#mLeft').textContent  = `第 ${S.dynasty} 任`;
  $('#mRight').textContent = `在位 ${Math.floor(S.turn/6)} 年 ${S.turn%6*2} 月`;
}

function show(idx){
  curIdx = idx;
  cur = CARDS[idx];
  const el = document.createElement('div');
  el.className = 'card';
  el.innerHTML = `<div class="opt-label opt-left"></div>
    <div class="opt-label opt-right"></div>
    <div class="who">${cur.bearer||''}</div>
    <div class="q">${(cur.question||'').replace(/\n/g,'<br>')}</div>
    <div class="hint">← 左划 · 右划 →</div>`;
  stage.querySelectorAll('.card').forEach(n=>n.remove());
  stage.appendChild(el);
  el.querySelector('.opt-left').textContent = cur.override_no  || '否';
  el.querySelector('.opt-right').textContent = cur.override_yes || '是';
  bindDrag(el);
  busy = false;
  drawBars();
  dbg();
}

function dbg(){
  const ks = Object.keys(S.flags).filter(k=>S.flags[k]).slice(-6);
  $('#dbg').textContent = `${cur? cur.thematic+'/'+(cur.card||cur.id) : ''}\n${ks.join(' ')}`;
}

/* ---------- 交互 ---------- */
function bindDrag(el){
  let sx=0, dx=0, drag=false;
  const L=el.querySelector('.opt-left'), R=el.querySelector('.opt-right');
  const down = e => {
    if (busy) return;
    drag=true; sx=(e.touches?e.touches[0]:e).clientX; el.classList.remove('anim');
  };
  const move = e => {
    if(!drag) return;
    dx=(e.touches?e.touches[0]:e).clientX - sx;
    el.style.transform=`translateX(${dx}px) rotate(${dx/26}deg)`;
    // 选项标签渐显：滑动 30px 开始显示，80px 完全不透明
    const absD = Math.abs(dx);
    const optOpacity = absD>30 ? Math.min(1,(absD-30)/50) : 0;
    // 卡片内容渐隐：滑动 30px 开始淡出，80px 完全透明
    const contentOpacity = absD>30 ? Math.max(0, 1-(absD-30)/50) : 1;

    R.style.opacity = dx>30 ? optOpacity : 0;
    L.style.opacity = dx<-30 ? optOpacity : 0;
    el.querySelector('.who').style.opacity = contentOpacity;
    el.querySelector('.q').style.opacity = contentOpacity;
    el.querySelector('.hint').style.opacity = contentOpacity;

    // 显示影响圆点
    if (absD > 30) {
      const choice = dx > 0 ? cur.yes : cur.no;
      RES.forEach(r => {
        const dot = $('#bars').querySelector(`[data-k="${r.k}"] .dot`);
        if (!dot) {
          console.error('Dot not found for', r.k);
          return;
        }
        const delta = Math.abs(choice[r.k] || 0);
        console.log('Delta for', r.k, ':', delta);
        if (delta > 0) {
          // 圆点大小：影响值 5 -> 6px, 10 -> 8px, 15 -> 10px, 20+ -> 12px
          const size = Math.min(12, 6 + delta * 0.3);
          dot.style.width = size + 'px';
          dot.style.height = size + 'px';
          dot.style.backgroundColor = '#d4af37';
          dot.classList.add('show');
          console.log('Showing dot for', r.k, 'size:', size);
        } else {
          dot.classList.remove('show');
        }
      });
    } else {
      // 隐藏所有圆点
      RES.forEach(r => {
        const dot = $('#bars').querySelector(`[data-k="${r.k}"] .dot`);
        if (dot) dot.classList.remove('show');
      });
    }
  };
  const up = () => {
    if(!drag) return; drag=false;
    el.classList.add('anim');
    // 判定阈值提高到 120px，增加回弹区间
    if (Math.abs(dx) > 120){
      const yes = dx>0;
      el.style.transform=`translateX(${yes?520:-520}px) rotate(${yes?26:-26}deg)`;
      el.style.opacity='0';
      L.style.opacity=R.style.opacity='0';
      choose(yes);
    } else {
      // 回弹到中间，标签淡出，内容重新显示
      el.style.transform='';
      L.style.opacity=R.style.opacity='0';
      el.querySelector('.who').style.opacity='1';
      el.querySelector('.q').style.opacity='1';
      el.querySelector('.hint').style.opacity='1';
      // 隐藏所有影响圆点
      RES.forEach(r => {
        $('#bars').querySelector(`[data-k="${r.k}"] .dot`).classList.remove('show');
      });
    }
    dx=0;
  };
  el.addEventListener('mousedown',down); el.addEventListener('touchstart',down,{passive:true});
  window.addEventListener('mousemove',move); window.addEventListener('touchmove',move,{passive:true});
  window.addEventListener('mouseup',up);    window.addEventListener('touchend',up);
}

function choose(yes){
  if (busy) return;
  busy = true;
  const p = yes ? 'yes' : 'no';
  const deltas = [];
  RES.forEach(r=>{
    const d = num(cur[p+'_'+r.k]);
    if (d){ S[r.k] = Math.max(0, Math.min(100, S[r.k]+d)); deltas.push(r.k); }
  });
  if (cur.lockturn === 'del')      S.lock[cur.card] = 1e9;
  else if (cur.lockturn)           S.lock[cur.card] = S.turn + parseInt(cur.lockturn,10);
  S.seen[cur.card] = 1;
  applyFlags(cur[p+'_custom'], curIdx);

  const ending = cur.thematic === 'endings' ? endingOf(cur[p+'_custom']) : null;
  const reply  = cur['answer_'+p];

  drawBars(deltas);
  if (reply){
    ansEl.textContent = reply; ansEl.classList.add('on');
    setTimeout(()=>{ ansEl.classList.remove('on'); step(ending); }, 1650);
  } else {
    setTimeout(()=>step(ending), 380);
  }
}

function endingOf(str){
  if (!str) return null;
  const m = str.match(/end_(.+?)(?:\s|$)/);
  if (m && ENDINGS[m[1]]) return m[1];
  for (const k in ENDINGS) if (str.indexOf(k)>=0) return k;
  return null;
}

function step(ending){
  if (ending){ showEnding(ending); return; }
  S.turn++;
  const idx = pick();
  if (idx < 0){ showEnding('无人问津'); return; }
  show(idx);
}

/* ---------- 结局与继任 ---------- */
let pendingEnd = null;

function showEnding(key){
  const e = ENDINGS[key];
  pendingEnd = key;
  const years = Math.floor(S.turn/6), months = S.turn%6*2;
  veil.innerHTML =
    `<div class="kicker">${e.kicker}</div>
     <h1>${key}</h1>
     <div class="body">${e.body.replace(/\n/g,'<br>')}</div>
     <div class="carry">在位 ${years} 年 ${months} 个月 · 第 ${S.dynasty} 任<br><br>${e.carry}</div>
     <button id="go">${e.win?'再来一次':'下一任'}</button>`;
  veil.classList.add('on');
  $('#go').onclick = succeed;
}

function succeed(){
  const e = ENDINGS[pendingEnd];
  // 只保留 _keep 标记，_run 和其他一律清空
  const keep = {};
  for (const k in S.flags){
    if (S.flags[k] && /_keep$/.test(k)) keep[k] = S.flags[k];
    if (S.flags[k] && /^nb_/.test(k))   keep[k] = S.flags[k];   // 计数器也留
  }
  if (e.flag) keep[e.flag] = 1;
  const dyn = S.dynasty + 1;
  initState(e.next, dyn, keep);
  veil.classList.remove('on');
  step(null);
}

/* ---------- 启动 ---------- */
(function boot(){
  CARDS.forEach((c,i)=>{ if (c.card) byName[c.card] = i; });
  initState({cash:50,team:55,market:45,capital:50}, 1, {});
  veil.innerHTML =
    `<div class="kicker">商业经营 · 卡牌</div>
     <h1>任 职</h1>
     <div class="body">你是这家公司的 CEO。<br><br>
       四条槽 —— 现金流、团队、市场、资本。<br>
       任意一条见底或者爆表，你就会被换掉。<br><br>
       换掉之后，公司还在。<br>烂摊子留给下一任。</div>
     <div class="carry">左右滑动卡片做决定，桌面上点左右半边也行。<br>
       没有正确答案，只有代价。</div>
     <button id="go">开始</button>`;
  veil.classList.add('on');
  $('#go').onclick = ()=>{ veil.classList.remove('on'); step(null); };
})();
