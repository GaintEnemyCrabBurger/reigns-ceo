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
};

const RES = [
  {k:'cash',   n:'现金流', icon:SVG.cash},
  {k:'team',   n:'团队',   icon:SVG.team},
  {k:'market', n:'市场',   icon:SVG.market},
  {k:'capital',n:'资本',   icon:SVG.capital},
];

const BOARD_REVIEW_TURN = 18;

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
  '融资换帅': {kicker:'救命钱 到账', body:'钱在最后一天到账。董事会感谢你撑到现在，然后请下一位 CEO 进了会议室。',
    next:{cash:65,team:40,market:50,capital:70}, carry:'下一任接手：现金暂时安全，预算权和否决权留在投资人手里。'},
  '联创反杀': {kicker:'伙伴 倒戈', body:'联创带走了产品、团队或者董事会的票。你最后一次走出公司时，他没有来送。',
    next:{cash:42,team:35,market:40,capital:38}, carry:'下一任接手：核心团队分裂，竞对知道公司所有底牌。'},
  '替罪离场': {kicker:'旧账 追责', body:'公告把系统性问题写成了个人判断。公司继续营业，你的名字留在监管问询里。',
    next:{cash:35,team:35,market:25,capital:58}, carry:'下一任接手：调查仍在继续，每个人都保存着自己的证据。'},
  '止损离场': {kicker:'董事会 止损', body:'你按时公开，也控制住了事故。董事会仍然决定换一张没有上过新闻的脸。',
    next:{cash:42,team:45,market:35,capital:55}, carry:'下一任接手：处罚可控，但客户和媒体不会立刻忘记。'},
  '低价卖身': {kicker:'公司 被收购', body:'交易完成，投资人先拿回了钱。你的部门名称还在，工牌上的公司名已经换了。',
    next:{cash:70,team:30,market:60,capital:85}, carry:'下一任接手：公司成了别人的业务线，第一件事是做人员整合。'},
  '任满交棒': {kicker:'任期 届满', body:'没有保安，没有公告，也没有突然失效的门禁。你把交接箱放在桌上，自己关了灯。',
    next:{cash:50,team:50,market:50,capital:50}, carry:'下一任接手：旧账仍在，但这一次交接是完整的。'},
};

let S;   // state
let byName = {};
let cur = null, curIdx = -1, forced = null, busy = false;
let restoreCardFocus = false;

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
    el.querySelector('.fill').style.width = v + '%';
    el.querySelector('.track').setAttribute('aria-valuenow', v);
    el.classList.toggle('warn', v<=20 || v>=80);
    if (flashKeys && flashKeys.indexOf(r.k)>=0){
      el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
    }
  });
  $('#mLeft').textContent  = `第 ${S.dynasty} 任`;
  const reviewMonths = Math.max(0, BOARD_REVIEW_TURN - S.turn) * 2;
  $('#mRight').textContent = reviewMonths > 0 ? `复盘 ${reviewMonths} 月后` : '董事会复盘中';
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
    // 触摸屏更早显示选择，避免快速滑动时卡面先淡空。
    const absD = Math.abs(dx);
    const revealStart = pointerType === 'touch' ? 10 : 24;
    const revealFull = pointerType === 'touch' ? 52 : 72;
    const optOpacity = absD>revealStart
      ? Math.min(1,(absD-revealStart)/(revealFull-revealStart))
      : 0;
    const visibleOpacity = pointerType === 'touch' && absD > 18
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
    const source = inputSource;
    inputSource='';
    el.classList.remove('dragging');
    el.classList.add('anim');
    stage.classList.remove('is-dragging');
    if (!cancelled && Math.abs(dx) > 96){
      commit(dx>0);
    } else if (!cancelled && source === 'pointer' && pointerType === 'mouse' && Math.abs(dx) < 6){
      const rect = el.getBoundingClientRect();
      const x = clientX(e);
      commit(x !== null && x >= rect.left + rect.width/2);
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
  const revealDelay = 340;
  const replyDuration = 1650;

  drawBars(deltas);
  if (reply){
    ansEl.textContent = reply;
    positionAnswer();
    ansEl.classList.add('on');
  }
  setTimeout(()=>{
    if (ending){
      ansEl.classList.remove('on');
      step(ending);
      return;
    }
    const unlockDelay = reply ? replyDuration - revealDelay : 0;
    step(null,unlockDelay);
    if (reply) setTimeout(()=>ansEl.classList.remove('on'),unlockDelay);
  },revealDelay);
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
  const idx = pick();
  if (idx < 0){ showEnding('无人问津'); return; }
  show(idx,unlockDelay);
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
