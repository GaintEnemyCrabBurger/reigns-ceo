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
  {k:'cash',   n:'现金', icon:SVG.cash},
  {k:'team',   n:'人心', icon:SVG.team},
  {k:'market', n:'业绩', icon:SVG.market},
  {k:'capital',n:'权力', icon:SVG.capital},
];

// 资源结局与剧情结局。结局后重新开始时，所有资源和本局状态都会归零重置。
const ENDINGS = {
  cash_zero: {title:'现金断裂', kicker:'现金归零', body:'工资发不出来。公司停摆。',
    carry:'本局结束：现金断裂。'},
  cash_max: {title:'账目无法解释', kicker:'现金爆表', body:'账上钱太多，解释不清。审计进门。',
    carry:'本局结束：账目无法解释。'},
  team_zero: {title:'团队散伙', kicker:'人心归零', body:'最后一个人也走了。办公室空了。',
    carry:'本局结束：团队散伙。'},
  team_max: {title:'派系逼宫', kicker:'人心爆表', body:'所有人都听你的。所以所有人一起逼宫。',
    carry:'本局结束：派系逼宫。'},
  market_zero: {title:'失去价值', kicker:'业绩归零', body:'没人买你的东西。董事会换人。',
    carry:'本局结束：失去价值。'},
  market_max: {title:'爆单崩盘', kicker:'业绩爆表', body:'订单超过交付能力。客户开始索赔。',
    carry:'本局结束：爆单崩盘。'},
  capital_zero: {title:'被架空', kicker:'权力归零', body:'董事会七票换人。你被架空。',
    carry:'本局结束：被架空。'},
  capital_max: {title:'所有人联合防你', kicker:'权力爆表', body:'你拿了所有权力。所有人开始防你。',
    carry:'本局结束：所有人联合防你。'},
  arrest: {title:'东窗事发', kicker:'风险与证据同时爆表', body:'凌晨六点，门铃响。经侦带走了你。',
    carry:'本局结束：东窗事发。'},
  scapegoat: {title:'替罪羊', kicker:'签字的人留下了', body:'责任书上只有你的名字。你替所有人签了。',
    carry:'本局结束：替罪羊。'},
  clean_ceo: {title:'清白上位', kicker:'清白上位', body:'账清了，任命书来了。你坐稳 CEO。',
    carry:'本局结束：你真的坐稳了。', win:true},
  black_empire: {title:'黑账帝国', kicker:'黑账帝国', body:'灰账养大了公司。没人敢查你。',
    carry:'本局结束：你赢了，但不能退休。', win:true},
  whistle: {title:'举报者', kicker:'举报者', body:'你把录音和账本交了。旧领导先被带走。',
    carry:'本局结束：你保住了自由。', win:true},
  sold: {title:'卖掉一切', kicker:'卖掉一切', body:'三十亿到账。买家接手公司，旧账仍挂你名下。',
    carry:'本局结束：钱和旧账一起交割。', win:true},
  handover: {title:'主动交棒', kicker:'主动交棒', body:'接班人接过钥匙。公司不再等你。',
    carry:'本局结束：公司不再依赖你。', win:true},
  board_puppet: {title:'董事会木偶', kicker:'保住头衔，失去声音', body:'你还是 CEO，预算和人事归董事会。',
    carry:'本局结束：董事会替你做完了所有决定。'},
};

let S;   // state
let byName = {};
let cur = null, curIdx = -1, forced = null, busy = false;
let restoreCardFocus = false;

function initState(seed, dyn, keep){
  S = {
    cash:seed.cash, team:seed.team, market:seed.market, capital:seed.capital,
    dynasty:dyn, turn:0, month:0, year:2015 + (dyn-1)*2,
    flags:Object.assign({risk:0,evidence:0}, keep||{}),
    lock:{},                            // card -> 解锁回合
    seen:{},
    history:[],
    recycleGuard:false,
    decisions:0,
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
  if (name==='risk'||name==='evidence') return Math.max(0, S.flags[name]|0);
  if (/^nb_/.test(name))               return S.flags[name]|0;
  return typeof S.flags[name] === 'number' ? S.flags[name] : (S.flags[name] ? 1 : 0);
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

function resourceEnding(){
  for (const r of RES){
    if (S[r.k] <= 0) return r.k + '_zero';
    if (S[r.k] >= 100) return r.k + '_max';
  }
  return null;
}

/* ---------- 抽卡 ---------- */
function pick(){
  if (forced !== null && forced !== undefined){
    const f = forced; forced = null;
    return f;
  }
  const pool = [];
  let best = 0;
  for (let i=0;i<CARDS.length;i++){
    const c = CARDS[i];
    if (!c.weight) continue;                       // 续写卡：永不随机抽中
    if (c.lockturn === 'del' && S.seen[c.card]) continue;
    if (S.lock[c.card] && S.turn < S.lock[c.card]) continue;
    if (!testCond(c.conditions)) continue;
    const w = c.weight === 'max' ? 1e9 : parseInt(c.weight,10);
    if (!w || isNaN(w)) continue;
    if (w > best) best = w;
    pool.push([i,w]);
  }
  if (!pool.length){
    if (!S.recycleGuard){
      S.recycleGuard = true;
      S.lock = {};
      CARDS.forEach(c=>{
        if (c.thematic === 'open' && c.lockturn !== 'del') delete S.seen[c.card];
      });
      return pick();
    }
    return -1;
  }
  S.recycleGuard = false;
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
    if (/[+-]$/.test(t)){                              // 隐藏计数器
      const direction = t.slice(-1) === '+' ? 1 : -1;
      const base = t.slice(0,-1).replace(/[+-]+$/,'');
      S.flags[base] = Math.max(0, (S.flags[base]|0) + direction);
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
  const rank = S.flags.ceo_run ? 'CEO'
    : S.flags.acting_ceo ? '代理 CEO'
    : S.flags.director_role ? '总监'
    : S.flags.manager_role ? '项目经理'
    : '实习生';
  $('#mLeft').textContent  = rank;
  $('#mRight').textContent = `第 ${S.turn} 次决定`;
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
  const previousValues = {cash:S.cash, team:S.team, market:S.market, capital:S.capital};
  RES.forEach(r=>{
    const d = num(cur[p+'_'+r.k]);
    if (d) S[r.k] = Math.max(0, Math.min(100, S[r.k]+d));
  });
  if (cur.lockturn === 'del')      S.lock[cur.card] = 1e9;
  else if (cur.lockturn)           S.lock[cur.card] = S.turn + parseInt(cur.lockturn,10);
  S.seen[cur.card] = 1;
  applyFlags(cur[p+'_custom'], curIdx);
  if (cur.thematic !== 'endings') S.decisions++;
  if (!S.flags.first_dirty && S.flags.dirty_route) S.flags.first_dirty = cur.card;
  S.history.push({turn:S.turn, card:cur.card, side:p});

  const explicitEnding = endingOf(cur[p+'_custom']);
  if (explicitEnding) forced = null;
  const ending = resourceEnding() || explicitEnding;
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
  for (const raw of str.split(/\s+and\s+/)){
    const token = raw.trim();
    let match = token.match(/^>_ending_([A-Za-z_]\w*)$/);
    if (!match) match = token.match(/^end_([A-Za-z_]\w*)$/);
    if (match && ENDINGS[match[1]]) return match[1];
  }
  return null;
}

function step(ending, unlockDelay=0){
  if (ending){ showEnding(ending); return; }
  S.turn++;
  const idx = pick();
  if (idx < 0){ showEnding(resourceEnding() || 'market_zero'); return; }
  show(idx,unlockDelay);
}

/* ---------- 结局与继任 ---------- */
let pendingEnd = null;

function escapeHTML(value){
  return String(value == null ? '' : value).replace(/[&<>\"]/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;'
  }[char]));
}

function routeSummary(){
  if (S.flags.dirty_route && S.flags.shared_secret) return '把回扣分给全组，再把全组带上董事会';
  if (S.flags.dirty_route) return '把灰账换成晋升，最后独自保管证据';
  if (S.flags.clean_route && S.flags.audit_closed) return '把证据留在审计邮箱，靠清账坐上 CEO';
  if (S.flags.clean_route) return '从干净的流程上位，却始终被旧账追问';
  return '靠一次次取舍把自己推上 CEO';
}

function rankSummary(){
  if (S.flags.ceo_run) return 'CEO';
  if (S.flags.acting_ceo) return '代理 CEO';
  if (S.flags.director_role) return '总监';
  if (S.flags.manager_role) return '项目经理';
  return '实习生';
}

function traceSummary(){
  const traces = [];
  const firstDirty = {
    intern_open:'八万元报销单', intern_fix:'咨询费差额', intern_gift:'领导的手表',
    manager_team:'删掉故障告警', manager_team_review:'漂亮路线图', manager_power:'替副总扛债',
    manager_power_review:'替副总签字', manager_day1:'供应商回扣', manager_dirty_bid:'项目奖金',
    manager_leader:'会所买单', manager_crisis:'供应商背锅', manager_report:'交换总监位置',
    manager_promotion:'接下必败项目', director_budget:'未签订单', director_leader:'替副总挡账',
    director_audit_dirty:'烧掉文件', director_media:'买下版面', director_board:'旧账换授权',
    acting_ceo:'把旧账压进并购', ceo_crowning:'宣布增长', ceo_first_reckoning:'锁起原件'
  };
  if (S.flags.first_dirty) traces.push(`第一次妥协：${firstDirty[S.flags.first_dirty] || S.flags.first_dirty}`);
  const finalTrace = S.flags.final_whistle ? '最后把证据交了出去'
    : S.flags.final_arrest ? '最后替所有人扛下了'
    : S.flags.scapegoat_taken ? '最后替公司签了字'
    : S.flags.final_black_empire ? '最后把灰账做成了帝国'
    : S.flags.final_clean_ceo ? '最后签下长期任命'
    : S.flags.company_sold ? '最后把公司卖给了大厂'
    : S.flags.final_handover ? '最后把椅子交给了接班人'
    : S.flags.final_board_puppet ? '最后把权力赌到了尽头'
    : null;
  if (finalTrace) traces.push(finalTrace);
  if (S.flags.credit_hog) traces.push('抢过许棠的功劳');
  if (S.flags.leader_favor) traces.push('替周启明挡过账');
  if (S.flags.shared_secret) traces.push('让团队共享秘密');
  if (S.flags.media_bought) traces.push('买过一次沉默');
  if (S.flags.recording_kept) traces.push('手里留着录音');
  if (S.flags.audit_closed) traces.push('完成过一次清账');
  return traces.slice(0, 3).join(' · ') || '没有留下可追溯的秘密';
}

function showEnding(key){
  const e = ENDINGS[key] || ENDINGS.market_zero;
  pendingEnd = key;
  const totalMonths = Math.max(1, S.decisions) * 2;
  const years = Math.floor(totalMonths / 12);
  const months = totalMonths % 12;
  const tenure = years
    ? `${years} 年${months ? ` ${months} 个月` : ''}`
    : `${totalMonths} 个月`;
  const shareLine = `${rankSummary() === 'CEO' ? '实习生 → CEO' : `实习生 → ${rankSummary()}`} · ${S.decisions} 次决定 · ${routeSummary()}`;
  veil.innerHTML =
    `<div class="kicker">${escapeHTML(e.kicker)}</div>
     <h1>${escapeHTML(e.title || key)}</h1>
     <div class="body">${escapeHTML(e.body).replace(/\n/g,'<br>')}</div>
     <div class="carry">本局在任 ${escapeHTML(tenure)}<br><br>${escapeHTML(e.carry)}<br>
       <span class="share-line">${escapeHTML(shareLine)}</span><br>
       <span class="trace-line">${escapeHTML(traceSummary())}</span></div>
     <button id="go">再来一局</button>`;
  veil.classList.add('on');
  $('#go').onclick = succeed;
  if (restoreCardFocus) $('#go').focus();
}

function succeed(){
  // 每局都是独立挑战；资源、短篇后果和计数器全部从初始状态开始。
  forced = null;
  cur = null;
  curIdx = -1;
  busy = false;
  initState({cash:46,team:48,market:44,capital:42}, 1, {});
  veil.classList.remove('on');
  step(null);
}

/* ---------- 启动 ---------- */
(function boot(){
  CARDS.forEach((c,i)=>{ if (c.card) byName[c.card] = i; });
  initState({cash:46,team:48,market:44,capital:42}, 1, {});
  veil.innerHTML =
    `<div class="kicker">职场卡牌</div>
     <h1>上 位</h1>
     <div class="body">你是实习生。<br><br>
       第一张报销单，差八万元。<br>
       今晚之前，决定谁来签。</div>
     <div class="carry">左右滑动做决定。<br>
       现金、人心、业绩、权力，任一归零或爆表，本局结束。<br>
       升上 CEO，旧账才找上门。</div>
     <button id="go">开始</button>`;
  veil.classList.add('on');
  $('#go').onclick = ()=>{ veil.classList.remove('on'); step(null); };
})();
