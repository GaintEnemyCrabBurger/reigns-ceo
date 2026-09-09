'use strict';

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
  {k:'money',  n:'钱', icon:SVG.cash},
  {k:'team',   n:'人', icon:SVG.team},
  {k:'market', n:'客', icon:SVG.market},
  {k:'mind',   n:'心', icon:SVG.capital},
];


const $ = selector => document.querySelector(selector);
const stage = $('#stage'), veil = $('#veil'), ansEl = $('#answer');
const STORAGE_KEY = 'founder-astra-v7-save';
let state, cur = null, busy = false;
let restoreCardFocus = false;
let animationEpoch = 0;
const escape = text => String(text ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[character]));

function seed(){
  const values = new Uint32Array(1);
  return globalThis.crypto?.getRandomValues ? crypto.getRandomValues(values)[0] : Date.now() >>> 0;
}

function save(){
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
}

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
    const v = Math.max(0, Math.min(100, state[r.k]));
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
    const danger = Founder.DANGER[r.k];
    el.classList.toggle('warn', v <= danger.low || Boolean(danger.high && v >= danger.high));
  });
  $('#mLeft').textContent = `第 ${state.dynasty} 次创业 · ${Founder.LABELS[Founder.phase(state) - 1]}`;
  $('#mRight').textContent = `在任 ${tenure()}`;
}

function tenure(){
  const totalMonths = state.turn * 2;
  const years = Math.floor(totalMonths / 12);
  const months = totalMonths % 12;
  return years ? `${years}年${months ? months + '个月' : ''}` : `${totalMonths}个月`;
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

function show(card = Founder.pick(state, STORY.cards, STORY.meta.cards), locked = false){
  if (!card) throw new Error('没有可以展示的故事卡。');
  cur = {...card, yes: Founder.effect(state, card, 'yes'), no: Founder.effect(state, card, 'no')};
  for (const field of ['bearer', 'question', 'override_no', 'override_yes']) cur[field] = Founder.render(state, card[field]);
  ansEl.classList.remove('on');
  ansEl.textContent = '';
  ensureDeck();
  const element = document.createElement('div');
  element.className = 'card deal-in';
  element.innerHTML = `<div class="opt-label opt-no" aria-hidden="true"></div>
    <div class="opt-label opt-yes" aria-hidden="true"></div>
    <div class="who">${escape(cur.bearer)}</div>
    <div class="q">${escape(cur.question).replace(/\n/g, '<br>')}</div>
    <div class="hint">← 左划 · 右划 →</div>`;
  const clearDealIn = () => element.classList.remove('deal-in');
  element.addEventListener('animationend', clearDealIn, {once:true});
  stage.querySelectorAll('.card').forEach(previous => previous.remove());
  stage.appendChild(element);
  stage.classList.remove('is-committing','is-dragging');
  setDeckProgress(0);
  setTimeout(clearDealIn, 520);
  element.querySelector('.opt-no').textContent = cur.override_no;
  element.querySelector('.opt-yes').textContent = cur.override_yes;
  element.tabIndex = 0;
  element.setAttribute('role', 'group');
  element.setAttribute('aria-keyshortcuts', 'ArrowLeft ArrowRight');
  element.setAttribute('aria-label', `${cur.bearer}：${cur.question}。左选项：${cur.override_no}；右选项：${cur.override_yes}`);
  bindDrag(element);
  busy = locked;
  if (locked){
    element.classList.remove('deal-in');
    element.classList.add('waiting');
    element.setAttribute('aria-disabled', 'true');
    element.style.opacity = '0';
    element.style.transform = `translateX(${window.innerWidth + element.offsetWidth}px)`;
  } else if (restoreCardFocus) {
    element.focus();
  }
  drawBars();
  save();
}

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
  if (busy || state.status !== 'card') return;
  busy = true;
  if (!Founder.choose(state, cur, yes ? 'yes' : 'no', STORY.meta.cards)){
    busy = false;
    return;
  }
  save();
  showFeedback(true);
}

function showFeedback(animate = false){
  busy = true;
  hideImpactDots();
  drawBars(animate ? state.feedback.before : null);
  ansEl.textContent = state.feedback.reply;
  positionAnswer();
  ansEl.classList.add('on');
  const epoch = ++animationEpoch;
  setTimeout(() => {
    if (epoch !== animationEpoch || state.status !== 'feedback') return;
    ansEl.classList.remove('on');
    Founder.advance(state);
    save();
    if (state.status === 'ended') showEnding();
    else show();
  }, 1280);
}

function showEnding(){
  const ending = STORY.meta.endings[state.ending];
  busy = true;
  hideImpactDots();
  veil.innerHTML = `<div class="kicker">${escape(ending.label)}</div>
    <h1>${escape(ending.title)}</h1>
    <div class="body">${escape(Founder.render(state, ending.body)).replace(/\n/g, '<br>')}</div>
    <div class="carry">${escape(state.company)} · 本局在任 ${tenure()}<br>共做出 ${state.turn} 次决定。</div>
    <button id="go">再开一家</button>`;
  veil.classList.add('on');
  $('#go').onclick = () => {
    animationEpoch++;
    state = Founder.nextCompany(state, STORY.meta.endings);
    cur = null;
    veil.classList.remove('on');
    show();
  };
  if (restoreCardFocus) $('#go').focus();
  save();
}

window.addEventListener('resize', positionAnswer);

(function boot(){
  try {
    if (!STORY.cards?.length || !STORY.meta?.endings) throw new Error('请先运行 build.py，再打开生成的「玩.html」。');
    let stored = null;
    try { stored = localStorage.getItem(STORAGE_KEY); } catch {}
    state = stored ? Founder.restore(stored, STORY.cards, STORY.meta.endings) : null;
    const resumed = Boolean(state);
    const invalid = Boolean(stored && !state);
    state ||= Founder.create(seed());
    busy = true;
    drawBars();
    veil.innerHTML = `<div class="kicker">${escape(STORY.meta.credit)} 作品</div>
      <h1>创始人</h1>
      <div class="body">你是「${escape(state.company)}」的创始人。<br>
        公司正当红。<br>发布会开始了。</div>
      <div class="carry">左右划卡，做决定。${invalid ? '<br>存档未能完整读取，将重新开始。' : ''}</div>
      <button id="go">${resumed ? '继续' : '开始'}</button>`;
    veil.classList.add('on');
    $('#go').onclick = () => {
      veil.classList.remove('on');
      restoreCardFocus = true;
      if (state.status === 'ended') showEnding();
      else if (state.status === 'feedback'){
        show(STORY.cards.find(card => card.card === state.current), true);
        showFeedback();
      } else show();
    };
    $('#go').focus();
  } catch (error){
    busy = true;
    veil.innerHTML = `<h1>无法开始</h1><div class="body">${escape(error.message)}</div>`;
    veil.classList.add('on');
  }
})();
