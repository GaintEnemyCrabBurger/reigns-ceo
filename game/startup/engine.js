/* 《任职》引擎 —— 照王权那套跑：读表、算条件、按权重抽、按 > 跳 */
'use strict';

// 四条资源。icon 是手画的线条 SVG，黑白，跟细边框那套统一
const SVG = {
  // 叠起来的硬币
  cash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true" focusable="false"
    stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="12" cy="6.5" rx="7.5" ry="3"/>
    <path d="M4.5 6.5v4c0 1.66 3.36 3 7.5 3s7.5-1.34 7.5-3v-4"/>
    <path d="M4.5 12.5v4c0 1.66 3.36 3 7.5 3s7.5-1.34 7.5-3v-4"/>
  </svg>`,
  // 两个人
  team: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true" focusable="false"
    stroke-linecap="round" stroke-linejoin="round">
    <circle cx="9" cy="7.5" r="3.2"/>
    <path d="M2.8 20v-1.4C2.8 16 5.6 14 9 14s6.2 2 6.2 4.6V20"/>
    <path d="M16.4 5.2a3.2 3.2 0 010 5.9"/>
    <path d="M18.4 14.4c1.7.7 2.8 2.1 2.8 3.9V20"/>
  </svg>`,
  // 店面招牌
  market: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true" focusable="false"
    stroke-linecap="round" stroke-linejoin="round">
    <path d="M3.4 8.6h17.2L18.8 4H5.2z"/>
    <path d="M4.6 8.6V20h14.8V8.6"/>
    <path d="M9.4 20v-6.2h5.2V20"/>
  </svg>`,
  // 银行立柱
  capital: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true" focusable="false"
    stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 3.2L21 8H3z"/>
    <path d="M5.6 8v9M10.5 8v9M13.5 8v9M18.4 8v9"/>
    <path d="M3 20.4h18"/>
  </svg>`,
  // 心气：一簇火。既能表达"还烧着"，也能表达"烧过头"
  mind: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true" focusable="false"
    stroke-linecap="round" stroke-linejoin="round">
    <path d="M13.4 2.8c.6 3-1.2 4.2-2.6 5.8-1.6 1.8-2.9 3.5-2.9 6a6.1 6.1 0 0012.2 0c0-3.4-2.3-5.4-4-7.6"/>
    <path d="M12 20.8a2.9 2.9 0 01-1.5-5.2c1-.7 1.7-1.5 1.7-2.9 1.4 1.2 2.4 2.6 2.4 4.2A2.9 2.9 0 0112 20.8z"/>
  </svg>`,
};

const RES = [
  {k:'money',  n:'钱', icon:SVG.cash},
  {k:'team',   n:'人', icon:SVG.team},
  {k:'market', n:'客', icon:SVG.market},
  {k:'mind',   n:'心', icon:SVG.mind},
];

const BOARD_REVIEW_TURN = 18;

/* ---------- 市场周期 ----------
   一局自带情绪曲线：起步 → 风口 → 退潮 → 寒冬。
   改的是数值乘数，不是卡池 —— 同一张卡在风口和寒冬里的后果不一样。
   风口自己来自己走，跟玩家做得好不好无关。 */
const PHASES = {
  1:{name:'起步', gain:1.0, loss:0.85, tip:'刚开始，错了也还有机会'},
  2:{name:'风口', gain:1.35, loss:0.8, tip:'风来了'},
  3:{name:'退潮', gain:1.0, loss:1.0, tip:'风停了'},
  4:{name:'寒冬', gain:0.75, loss:1.35, tip:'活下去'},
};

// 风口在第 4-7 回合之间开始，持续 4-7 回合。每局不同，所以不会按部就班。
function rollWindow(){
  return {start: 4 + Math.floor(Math.random()*4), len: 4 + Math.floor(Math.random()*4)};
}

function phaseOf(turn, win){
  if (turn < win.start) return 1;
  if (turn < win.start + win.len) return 2;
  if (turn < win.start + win.len + 4) return 3;
  return 4;
}

// 八种下台方式：留给下一任什么
const ENDINGS = {
  '关门':     {kicker:'钱 归零', body:'工资发不出来了。你把办公室钥匙交给房东，最后一个走。\n\n三年，一场空。',
    next:{money:30,team:35,market:20,mind:55}, carry:'下一次：行业里有人记得你亏过钱。', flag:'failed_keep'},
  '躺在钱上': {kicker:'钱 爆表', body:'账上很多钱，两年没动过。风口那阵你没敢押，现在风停了，钱也不值那么多了。',
    next:{money:70,team:40,market:25,mind:40}, carry:'下一次：你有本钱，但错过了一整个周期。'},
  '人走空':   {kicker:'人 归零', body:'最后两个人办完离职。工位上还留着没带走的杯子。',
    next:{money:40,team:20,market:35,mind:45}, carry:'下一次：行业里都知道你留不住人。', flag:'badrep_keep'},
  '全在开会': {kicker:'人 爆表', body:'两百个人，每天开十四个会。没有人记得上一次发版是什么时候。',
    next:{money:25,team:70,market:40,mind:40}, carry:'下一次：第一件事是裁员。'},
  '没人要':   {kicker:'客 归零', body:'后台昨天的活跃是十一个，其中八个是你们自己人。',
    next:{money:35,team:40,market:20,mind:50}, carry:'下一次：得重新想清楚谁要这东西。'},
  '接不过来': {kicker:'客 爆表', body:'订单排到两年后，退款单堆到了门口。所有人都在道歉。',
    next:{money:40,team:20,market:70,mind:45}, carry:'下一次：单子满手，人全累垮了。'},
  '交给专业的人': {kicker:'心 归零', body:'你最近的决定都很稳。稳到投资人觉得，换个职业经理人也能做，而且更便宜。\n\n你留在董事会里，但公司不再是你的了。',
    next:{money:55,team:50,market:50,mind:45}, carry:'下一次：你还在行业里，但不再是主角。', flag:'hollow_keep'},
  '一把梭':   {kicker:'心 爆表', body:'你把所有筹码推上去了。所有人都劝过你，你一个字也没听。\n\n赢了，你会是那个传奇。输了，没人会记得你为什么那么确定。',
    next:{money:20,team:35,market:60,mind:75}, carry:'下一次：你赌上了一切，行业还在议论。', flag:'allin_keep', win:true},
  '敲钟':     {kicker:'第 18 个月', body:'钟敲完了。账上进来的钱，比你爸这辈子见过的总数还多。\n\n所有人都恭喜你。你想起三年前那间三十平的房子。',
    next:{money:75,team:55,market:65,mind:48}, carry:'下一次：你已经证明过一次了。', flag:'ipo_keep', win:true},
  '卖掉了':   {kicker:'第 18 个月', body:'签字那天来了很多律师。团队每个人都分到了钱，有人当场哭了。\n\n三个月后，买方把你们的产品并进了他们的主线。名字没了。',
    next:{money:70,team:45,market:40,mind:40}, carry:'下一次：你有钱，但那个东西已经不在了。', flag:'sold_keep'},
  '融资换帅': {kicker:'第 18 个月', body:'钱到了，位置没了。新 CEO 很专业，你留在董事会里。\n\n第一次开会你举手了，后来就不举了。',
    next:{money:60,team:45,market:50,mind:35}, carry:'下一次：你知道被换掉是什么感觉了。', flag:'hollow_keep'},
  '联创出走': {kicker:'第 18 个月', body:'他带走了七个人，其中三个是你亲自招的。\n\n半年后他们的产品上线，跟你们做的很像，但更快。',
    next:{money:45,team:28,market:40,mind:58}, carry:'下一次：他现在是你的竞争对手。', flag:'rival_keep'},
  '卖身还债': {kicker:'第 18 个月', body:'公司还在，但已经不是你的了。你留任一年，负责交接。\n\n那一年你每天照常上班。',
    next:{money:35,team:35,market:35,mind:42}, carry:'下一次：你还欠着人情。', flag:'failed_keep'},
  '还开着':   {kicker:'第 18 个月', body:'没有敲钟，没有被收，也没有关门。三年过去了，你们还开着。\n\n这在这个行业里已经不容易了。',
    next:{money:50,team:50,market:45,mind:50}, carry:'下一次：你活下来了，这就是本钱。', flag:'survivor_keep'},
};

let S;   // state
let byName = {};
let cur = null, curIdx = -1, forced = null, busy = false;
let restoreCardFocus = false;

function initState(seed, dyn, keep){
  S = {
    money:seed.money, team:seed.team, market:seed.market, mind:seed.mind,
    dynasty:dyn, turn:0, month:0, year:2015 + (dyn-1)*2,
    flags:Object.assign({}, keep||{}),   // _keep 跨局保留
    lock:{},                            // card -> 解锁回合
    seen:{},
    win:rollWindow(),                   // 本局的风口窗口
    phase:1,
    lastPhase:1,
  };
}

/* ---------- 条件 ---------- */
function val(name){
  if (name==='money'||name==='cash')   return S.money;
  if (name==='team')                   return S.team;
  if (name==='market')                 return S.market;
  if (name==='mind')                   return S.mind;
  if (name==='dynasty')                return S.dynasty;
  if (name==='turn')                   return S.turn;
  if (name==='year')                   return S.year;
  if (name==='phase')                  return S.phase;
  if (name==='overall')                return Math.round((S.money+S.team+S.market+S.mind)/4);
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

function feedbackMarkup(reply){
  // 结果区只承担一句解释；具体的得失由上方资源槽的动画表达。
  return String(reply || '');
}

/* ---------- 渲染 ---------- */
const $ = s => document.querySelector(s);
const stage = $('#stage'), veil = $('#veil'), ansEl = $('#answer');


function drawBars(previousValues){
  const box = $('#bars');
  if (!box.children.length){
    box.innerHTML = RES.map(r=>
      `<div class="bar" data-k="${r.k}" aria-label="${r.n}">
         <div class="impact"><span class="dot"></span></div>
         <div class="icon">${r.icon}</div>
         <div class="lbl">${r.n}</div>
         <div class="track" role="progressbar" aria-label="${r.n}" aria-valuemin="0" aria-valuemax="100"><div class="fill"></div></div>
       </div>`).join('');
  }
  RES.forEach(r=>{
    const el = box.querySelector(`[data-k="${r.k}"]`);
    const v = Math.max(0, Math.min(100, S[r.k]));
    const fill = el.querySelector('.fill');
    const track = el.querySelector('.track');
    const before = previousValues && Number.isFinite(previousValues[r.k])
      ? Math.max(0, Math.min(100, previousValues[r.k])) : null;
    const changed = before !== null && before !== v;
    if (changed){
      const direction = v < before ? 'impact-down' : 'impact-up';
      el.classList.remove('impact-down','impact-up','flash');
      void el.offsetWidth;
      el.classList.add(direction,'flash');
      // 先停在旧位置，再在下一帧明显退进，避免瞬间跳变。
      fill.style.transition = 'none';
      fill.style.width = before + '%';
      void fill.offsetWidth;
      fill.style.transition = '';
      requestAnimationFrame(()=>{
        if (fill.isConnected) fill.style.width = v + '%';
      });
      window.setTimeout(()=>{
        if (el.isConnected) el.classList.remove('impact-down','impact-up','flash');
      }, 980);
    } else {
      fill.style.width = v + '%';
      if (!previousValues) el.classList.remove('impact-down','impact-up','flash');
    }
    track.setAttribute('aria-valuenow', v);
    el.classList.toggle('warn', v<=20 || v>=80);
  });
  $('#mLeft').textContent  = `第 ${S.dynasty} 任`;
  const remaining = Math.max(0, BOARD_REVIEW_TURN - S.turn);
  $('#mRight').textContent = remaining > 0 ? `还剩 ${remaining} 次` : '本任结束';
}

const DECK_LAYERS = [
  {className:'back-far', y:-18, compactY:-14, scale:.93, angle:-2.4, settle:6},
  {className:'back-mid', y:-12, compactY:-9,  scale:.965, angle:1.5, settle:7},
  {className:'back-near',y:-6,  compactY:-5,  scale:.985, angle:-.8, settle:6},
];

function ensureDeck(){
  let deck = stage.querySelector('.deck');
  if (deck) return deck;
  deck = document.createElement('div');
  deck.className = 'deck';
  deck.setAttribute('aria-hidden','true');
  deck.innerHTML = DECK_LAYERS.map(layer =>
    `<div class="deck-card ${layer.className}"></div>`
  ).join('');
  stage.prepend(deck);
  setDeckProgress(0);
  return deck;
}

function setDeckProgress(progress){
  const deck = stage.querySelector('.deck');
  if (!deck) return;
  const p = Math.max(0, Math.min(1, progress));
  const compact = window.innerHeight <= 620;
  DECK_LAYERS.forEach(layer=>{
    const el = deck.querySelector('.' + layer.className);
    if (!el) return;
    const startY = compact ? layer.compactY : layer.y;
    const y = startY + p * Math.min(Math.abs(startY), layer.settle);
    const scale = layer.scale + p * (1 - layer.scale) * .45;
    const angle = layer.angle * (1 - p * .18);
    el.style.transform = `translate3d(0,${y}px,0) scale(${scale}) rotate(${angle}deg)`;
  });
}

function positionAnswer(){
  const activeCard = stage.querySelector('.card');
  if (!activeCard) return;
  const compact = window.innerHeight <= 620;
  const gap = compact ? 18 : 24;
  const cardTop = activeCard.offsetTop;
  const cardBottom = cardTop + activeCard.offsetHeight;
  const answerHeight = ansEl.offsetHeight;
  const below = cardBottom + gap;
  const above = cardTop - gap - answerHeight;
  const top = below + answerHeight <= stage.clientHeight ? below : Math.max(0,above);
  ansEl.style.top = `${top}px`;
}

function show(idx, unlockDelay=0){
  curIdx = idx;
  cur = CARDS[idx];

  ansEl.classList.remove('on');
  ansEl.innerHTML = '';

  // 构建 yes 和 no 对象，包含资源变化
  cur.yes = {
    cash: parseInt(cur.yes_cash) || 0,
    team: parseInt(cur.yes_team) || 0,
    market: parseInt(cur.yes_market) || 0,
    capital: parseInt(cur.yes_capital) || 0
  };
  cur.no = {
    cash: parseInt(cur.no_cash) || 0,
    team: parseInt(cur.no_team) || 0,
    market: parseInt(cur.no_market) || 0,
    capital: parseInt(cur.no_capital) || 0
  };

  ensureDeck();
  const el = document.createElement('div');
  el.className = 'card deal-in';
  el.innerHTML = `<div class="opt-label opt-no" aria-hidden="true"></div>
    <div class="opt-label opt-yes" aria-hidden="true"></div>
    <div class="who">${cur.bearer||''}</div>
    <div class="q">${(cur.question||'').replace(/\n/g,'<br>')}</div>
    <div class="hint">← 左划 · 右划 →</div>`;
  const clearDealIn = ()=>el.classList.remove('deal-in');
  el.addEventListener('animationend',clearDealIn,{once:true});
  stage.querySelectorAll('.card').forEach(n=>n.remove());
  stage.appendChild(el);
  stage.classList.remove('is-committing','is-dragging');
  setDeckProgress(0);
  setTimeout(clearDealIn,520);
  el.querySelector('.opt-no').textContent = cur.override_no  || '否';
  el.querySelector('.opt-yes').textContent = cur.override_yes || '是';
  el.tabIndex = 0;
  el.setAttribute('role', 'group');
  el.setAttribute('aria-keyshortcuts', 'ArrowLeft ArrowRight');
  el.setAttribute('aria-label', `${cur.bearer||'决策'}：${cur.question||''}。左选项：${cur.override_no||'否'}；右选项：${cur.override_yes||'是'}`);
  bindDrag(el);
  const unlock = ()=>{
    if (!el.isConnected) return;
    busy = false;
    el.classList.remove('waiting');
    el.removeAttribute('aria-disabled');
    if (restoreCardFocus) el.focus();
  };
  if (unlockDelay > 0){
    busy = true;
    el.classList.add('waiting');
    el.setAttribute('aria-disabled','true');
    setTimeout(unlock,unlockDelay);
  } else {
    unlock();
  }
  drawBars();
  dbg();
}

function dbg(){
  const ks = Object.keys(S.flags).filter(k=>S.flags[k]).slice(-6);
  $('#dbg').textContent = `${cur? cur.thematic+'/'+(cur.card||cur.id) : ''}\n${ks.join(' ')}`;
}

/* ---------- 交互 ---------- */
function hideImpactDots(){
  RES.forEach(r=>{
    const dot = $('#bars').querySelector(`[data-k="${r.k}"] .dot`);
    if (dot) dot.classList.remove('show');
  });
}

function showImpactDots(choice){
  RES.forEach(r=>{
    const dot = $('#bars').querySelector(`[data-k="${r.k}"] .dot`);
    if (!dot) return;
    const delta = Math.abs(choice[r.k] || 0);
    if (!delta){
      dot.classList.remove('show');
      return;
    }
    const size = delta >= 20 ? 12 : delta >= 15 ? 10 : delta >= 10 ? 8 : 6;
    dot.style.width = size + 'px';
    dot.style.height = size + 'px';
    dot.classList.add('show');
  });
}

function bindDrag(el){
  let sx=0, dx=0, drag=false, pointerId=null, pointerType='', inputSource='';
  const choiceNo = el.querySelector('.opt-no');
  const choiceYes = el.querySelector('.opt-yes');
  const who = el.querySelector('.who');
  const question = el.querySelector('.q');
  const hint = el.querySelector('.hint');

  const isTouchEvent = e => e.type.indexOf('touch') === 0;
  const pointFrom = e => {
    const point = isTouchEvent(e)
      ? ((e.touches && e.touches[0]) || (e.changedTouches && e.changedTouches[0]))
      : e;
    return point && Number.isFinite(point.clientX) ? point : null;
  };
  const clientX = e => {
    const point = pointFrom(e);
    return point ? point.clientX : null;
  };

  const reset = ()=>{
    el.style.transform='';
    choiceNo.style.opacity = choiceYes.style.opacity = '0';
    choiceNo.classList.remove('revealed');
    choiceYes.classList.remove('revealed');
    who.style.opacity = question.style.opacity = hint.style.opacity = '1';
    stage.classList.remove('is-dragging','is-committing');
    el.classList.remove('touch-dragging');
    setDeckProgress(0);
    hideImpactDots();
  };

  const down = e => {
    const touch = isTouchEvent(e) || e.pointerType === 'touch' || e.pointerType === 'pen';
    // Touch pointer events commonly use button=-1; only reject non-primary mice.
    if (busy || drag || (!touch && e.button !== 0)) return;
    const x = clientX(e);
    if (x === null) return;
    restoreCardFocus = false;
    // 区分事件来源（pointer/touch）与指针类型（mouse/touch/pen）。
    // 有些浏览器会同时派发两套事件，来源锁定可避免重复提交。
    drag=true; inputSource=isTouchEvent(e) ? 'touch' : 'pointer';
    pointerId=e.pointerId == null ? null : e.pointerId;
    pointerType=touch ? 'touch' : (e.pointerType || 'mouse');
    sx=x; dx=0;
    el.classList.remove('anim','deal-in');
    el.classList.add('dragging');
    if (touch) el.classList.add('touch-dragging');
    stage.classList.add('is-dragging');
    if (e.pointerId != null && el.setPointerCapture){
      try { el.setPointerCapture(e.pointerId); } catch (_) { /* older WebKit */ }
    }
    if (touch && e.cancelable) e.preventDefault();
  };
  const move = e => {
    if(!drag) return;
    const eventSource = isTouchEvent(e) ? 'touch' : 'pointer';
    // 触摸指针在部分 WebView 中会交替派发 pointermove/touchmove，两者都可用。
    if (pointerType !== 'touch' && eventSource !== inputSource) return;
    if (!isTouchEvent(e) && pointerId !== null && e.pointerId !== pointerId) return;
    const x = clientX(e);
    if (x === null) return;
    dx=x - sx;
    if (isTouchEvent(e) && e.cancelable) e.preventDefault();
    const visualDx = Math.max(-112, Math.min(112, dx));
    el.style.transform=`translateX(${visualDx}px) rotate(${visualDx/26}deg)`;
    setDeckProgress(Math.min(1, Math.abs(dx) / 120));
    // 中立区先保留回弹空间；只有明显偏向一侧时才让选项变得醒目。
    const absD = Math.abs(dx);
    const revealStart = pointerType === 'touch' ? 24 : 30;
    const revealFull = pointerType === 'touch' ? 86 : 96;
    const optOpacity = absD>revealStart
      ? Math.min(1,(absD-revealStart)/(revealFull-revealStart))
      : 0;
    const visibleOpacity = pointerType === 'touch' && absD > 48
      ? Math.max(.88,optOpacity) : optOpacity;
    // 卡片内容渐隐，但不影响上方的选择徽标。
    const contentStart = pointerType === 'touch' ? 24 : 30;
    const contentFull = pointerType === 'touch' ? 76 : 80;
    const contentOpacity = absD>contentStart
      ? Math.max(0, 1-(absD-contentStart)/(contentFull-contentStart))
      : 1;

    choiceYes.style.opacity = dx>revealStart ? visibleOpacity : 0;
    choiceNo.style.opacity = dx<-revealStart ? visibleOpacity : 0;
    choiceYes.classList.toggle('revealed',dx>revealStart);
    choiceNo.classList.toggle('revealed',dx<-revealStart);
    who.style.opacity = question.style.opacity = hint.style.opacity = contentOpacity;

    // 显示影响圆点
    if (absD > revealStart) {
      showImpactDots(dx > 0 ? cur.yes : cur.no);
    } else {
      hideImpactDots();
    }
  };
  const commit = yes=>{
    const fly = window.innerWidth + el.offsetWidth;
    const direction = yes ? 1 : -1;
    el.style.transform=`translate3d(${direction*fly}px,-${Math.min(76,Math.max(34,Math.abs(dx)*.22))}px,0) rotate(${direction*22}deg) scale(.96)`;
    el.style.opacity='0';
    choiceNo.style.opacity = choiceYes.style.opacity = '0';
    choiceNo.classList.remove('revealed');
    choiceYes.classList.remove('revealed');
    stage.classList.remove('is-dragging');
    el.classList.remove('touch-dragging');
    stage.classList.add('is-committing');
    setDeckProgress(1);
    hideImpactDots();
    choose(yes);
  };

  const finish = (e, cancelled=false) => {
    if(!drag) return;
    drag=false;
    inputSource='';
    el.classList.remove('dragging');
    el.classList.add('anim');
    stage.classList.remove('is-dragging');
    // 提交阈值约为卡片宽度的一半。阈值以内始终回到中立位。
    const commitThreshold = Math.max(136, Math.min(164, el.offsetWidth * .48));
    if (!cancelled && Math.abs(dx) >= commitThreshold){
      commit(dx>0);
    } else {
      reset();
    }
    dx=0;
  };
  el.addEventListener('pointerdown',down);
  el.addEventListener('pointermove',move);
  el.addEventListener('pointerup',e=>finish(e,false));
  el.addEventListener('pointercancel',e=>finish(e,true));
  // Older iOS/WebView builds may expose touch events without reliable PointerEvents.
  el.addEventListener('touchstart',down,{passive:false});
  el.addEventListener('touchmove',move,{passive:false});
  el.addEventListener('touchend',e=>finish(e,false),{passive:false});
  el.addEventListener('touchcancel',e=>finish(e,true),{passive:false});
  el.addEventListener('keydown',e=>{
    if (busy || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return;
    e.preventDefault();
    restoreCardFocus = true;
    el.classList.add('anim');
    commit(e.key === 'ArrowRight');
  });
}

function choose(yes){
  if (busy) return;
  busy = true;
  const p = yes ? 'yes' : 'no';
  const previousValues = {money:S.money, team:S.team, market:S.market, mind:S.mind};
  const ph = PHASES[S.phase] || PHASES[1];
  RES.forEach(r=>{
    let d = num(cur[p+'_'+r.k]);
    if (!d) return;
    // 心气不受周期影响 —— 你的偏执跟大盘没关系
    if (r.k !== 'mind') d = d > 0 ? Math.round(d*ph.gain) : Math.round(d*ph.loss);
    if (d) S[r.k] = Math.max(0, Math.min(100, S[r.k]+d));
  });
  if (cur.lockturn === 'del')      S.lock[cur.card] = 1e9;
  else if (cur.lockturn)           S.lock[cur.card] = S.turn + parseInt(cur.lockturn,10);
  S.seen[cur.card] = 1;
  applyFlags(cur[p+'_custom'], curIdx);

  const ending = cur.thematic === 'endings' ? endingOf(cur[p+'_custom']) : null;
  const reply  = cur['answer_'+p];
  const feedbackDuration = 1280;

  drawBars(previousValues);
  ansEl.textContent = feedbackMarkup(reply);
  if (reply){
    positionAnswer();
    ansEl.classList.add('on');
  } else {
    ansEl.classList.remove('on');
  }
  setTimeout(()=>{
    if (ending){
      ansEl.classList.remove('on');
      step(ending);
      return;
    }
    ansEl.classList.remove('on');
    step(null);
  },feedbackDuration);
}

function endingOf(str){
  if (!str) return null;
  const m = str.match(/end_(.+?)(?:\s|$)/);
  if (m && ENDINGS[m[1]]) return m[1];
  for (const k in ENDINGS) if (str.indexOf(k)>=0) return k;
  return null;
}

function step(ending, unlockDelay=0){
  if (ending){ showEnding(ending); return; }
  S.turn++;
  S.lastPhase = S.phase;
  S.phase = phaseOf(S.turn, S.win);
  const idx = pick();
  if (idx < 0){ showEnding('没人要'); return; }
  show(idx,unlockDelay);
  // 周期切换要让玩家明确感觉到，否则风口白给
  if (S.phase !== S.lastPhase) announcePhase(S.phase);
}

// 周期切换横幅。风来了、风停了，是这局最重要的两个时刻。
function announcePhase(phase){
  const ph = PHASES[phase];
  if (!ph) return;
  let el = document.getElementById('phaseBanner');
  if (!el){
    el = document.createElement('div');
    el.id = 'phaseBanner';
    document.getElementById('app').appendChild(el);
  }
  el.className = 'phase-' + phase;
  el.innerHTML = `<span class="pn">${ph.name}</span><span class="pt">${ph.tip}</span>`;
  el.classList.remove('on');
  void el.offsetWidth;
  el.classList.add('on');
  window.setTimeout(()=>{ el.classList.remove('on'); }, 2100);
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
  if (restoreCardFocus) $('#go').focus();
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
  initState({money:45,team:55,market:38,mind:52}, 1, {});
  veil.innerHTML =
    `<div class="kicker">创业 · 卡牌</div>
     <h1>创 业</h1>
     <div class="body">三个人，一间三十平的房子，账上十七万。<br><br>
       四条槽 —— <b>钱</b>还剩几个月，<b>人</b>还剩几个，<br>
       <b>客</b>要不要，还有<b>心</b>：你还剩多少自己的偏执。<br><br>
       任意一条见底或者爆表，你就出局。<br>
       但风口会来，也会走，跟你做得好不好没关系。</div>
     <div class="carry">左右明显拖动卡片做决定，轻轻碰一下会回到中间。<br>
       风来的时候敢不敢押，是这局最重要的一次决定。</div>
     <button id="go">开始</button>`;
  veil.classList.add('on');
  $('#go').onclick = ()=>{ veil.classList.remove('on'); step(null); };
})();
