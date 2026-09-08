(function(){
  'use strict';

  const M = window.StoryModel;
  const $ = id => document.getElementById(id);
  const clone = value => JSON.parse(JSON.stringify(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  })[character]);
  const compact = (value, limit=110) => {
    const result = String(value || '').replace(/\s+/g, ' ').trim();
    return result.length > limit ? result.slice(0, limit - 1) + '…' : result;
  };
  const baselineStorage = 'regins-story-control-baseline-v1';
  const reviewStorage = 'regins-story-control-reviews-v1';
  const reviewLabels = {key:'关键剧情', pace:'节奏卡', rewrite:'待重写', remove:'无效 / 待删除'};
  const severityOrder = {error:0, warning:1, info:2};

  const state = {
    cards:[], savedCards:[], projectBaseline:[], baseline:[],
    source:'cards.csv', baselineSource:null, version:'', modifiedAt:'',
    model:null, savedModel:null, baselineModel:null,
    changes:new Map(), dirty:new Map(), reviews:{},
    view:'graph', theme:'all', kind:'all', search:'', showFlags:true,
    zoom:.8, selected:null, selectedChange:null, focus:false,
    editing:null, loading:false, saving:false, confirmAction:null,
  };

  function readStorage(key){
    try { return JSON.parse(localStorage.getItem(key) || 'null'); }
    catch { return null; }
  }

  function themeTitle(theme){
    return M.themes[theme]?.[1] || theme || '未分类';
  }

  function kindTitle(kind){
    return ({story:'剧情连接', state:'状态 / 伏笔', resource:'资源调节', flavor:'氛围 / 对话', ending:'结局'})[kind] || kind;
  }

  function reviewFor(key){
    return state.reviews[key] || {value:'', note:''};
  }

  function changeFor(key){
    return state.changes.get(key);
  }

  function dirtyFor(key){
    return state.dirty.get(key);
  }

  function nodeFor(key){
    return state.model?.byKey.get(key) || null;
  }

  function issuesFor(key){
    return state.model?.issues.filter(issue => issue.key === key) || [];
  }

  function hardIssueCount(){
    return state.model?.issues.filter(issue => issue.severity === 'error').length || 0;
  }

  function reviewCount(){
    return Object.values(state.reviews).filter(review => review.value === 'rewrite' || review.value === 'remove').length;
  }

  function loadCustomBaseline(){
    const stored = readStorage(baselineStorage);
    return stored?.cards?.length ? stored : null;
  }

  function rebuild(){
    state.model = M.build(state.cards);
    state.savedModel = M.build(state.savedCards);
    state.baselineModel = state.baseline.length ? M.build(state.baseline) : null;
    state.changes = M.compare(state.model, state.baselineModel);
    state.dirty = M.compare(state.model, state.savedModel);
    if (state.selected && !nodeFor(state.selected)) state.selected = null;
    refreshThemeOptions();
  }

  async function loadStory({quiet=false}={}){
    if (state.dirty.size && !quiet){
      ask('放弃未保存修改', '重新载入会丢弃当前尚未写回 cards.csv 的改动。', () => loadStory({quiet:true}));
      return;
    }
    state.loading = true;
    updateButtons();
    try {
      const response = await fetch('/api/story', {cache:'no-store'});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || '无法读取牌库');
      state.cards = M.normalize(payload.cards);
      state.savedCards = clone(state.cards);
      state.projectBaseline = M.normalize(payload.baseline || []);
      state.source = payload.source || 'cards.csv';
      state.baselineSource = payload.baselineSource;
      state.version = payload.version;
      state.modifiedAt = payload.modifiedAt || '';
      const custom = loadCustomBaseline();
      state.baseline = custom ? M.normalize(custom.cards) : clone(state.projectBaseline);
      state.reviews = readStorage(reviewStorage) || {};
      state.selected = null;
      state.selectedChange = null;
      state.editing = null;
      state.focus = false;
      rebuild();
      render();
      if (!quiet) toast(`已读取 ${state.cards.length} 张卡`);
    } catch (error) {
      showLoadError(error);
    } finally {
      state.loading = false;
      updateButtons();
    }
  }

  function showLoadError(error){
    $('scSource').textContent = '连接失败';
    $('scCardList').innerHTML = '<div class="sc-empty">无法读取 cards.csv。<br><br>请通过 story_server.py 打开这个页面。<br><br>'+esc(error.message)+'</div>';
    $('scInspector').innerHTML = '<div class="sc-inspector-empty">后台服务未连接。</div>';
    toast('后台服务未连接');
  }

  function refreshThemeOptions(){
    const select = $('scTheme');
    const previous = state.theme;
    select.innerHTML = '<option value="all">全部故事线</option>' + state.model.themes.map(theme =>
      `<option value="${esc(theme)}">${esc(themeTitle(theme))}</option>`
    ).join('');
    if ([...select.options].some(option => option.value === previous)) select.value = previous;
    else { state.theme = 'all'; select.value = 'all'; }
  }

  function updateButtons(){
    const dirty = state.dirty.size > 0;
    $('scSave').disabled = !dirty || state.loading || state.saving;
    $('scUndoAll').disabled = !dirty || state.loading || state.saving;
    $('scReload').disabled = state.loading || state.saving;
    $('scSave').textContent = state.saving ? '正在写回…' : '写回 cards.csv';
  }

  function render(){
    if (!state.model) return;
    renderOverview();
    renderTabs();
    renderList();
    renderMain();
    renderInspector();
    updateButtons();
  }

  function renderOverview(){
    $('scCardCount').textContent = state.model.nodes.length;
    $('scThemeCount').textContent = state.model.themes.length;
    $('scChangeCount').textContent = state.changes.size;
    $('scDirtyCount').textContent = state.dirty.size;
    $('scErrorCount').textContent = hardIssueCount();
    $('scReviewCount').textContent = reviewCount();
    $('scSource').textContent = `${state.source} · ${state.modifiedAt.replace('T',' ')}`;
    const custom = loadCustomBaseline();
    $('scBaseline').textContent = custom
      ? `对比基线：${custom.name}`
      : state.baselineSource ? `对比基线：${state.baselineSource}` : '对比基线：未设置';
  }

  function renderTabs(){
    document.querySelectorAll('[data-view]').forEach(button => {
      const active = button.dataset.view === state.view;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function nodeMatches(node){
    if (state.theme !== 'all' && node.card.thematic !== state.theme) return false;
    const review = reviewFor(node.key).value;
    if (state.kind === 'unreviewed' && review) return false;
    if (['key','pace','rewrite','remove'].includes(state.kind) && review !== state.kind) return false;
    if (!['all','unreviewed','key','pace','rewrite','remove'].includes(state.kind) && node.kind !== state.kind) return false;
    if (state.search){
      const haystack = M.fields.map(field => node.card[field]).join(' ').toLowerCase();
      const reviewText = (reviewFor(node.key).note || '').toLowerCase();
      if (!haystack.includes(state.search.toLowerCase()) && !reviewText.includes(state.search.toLowerCase())) return false;
    }
    if (state.view === 'changes' && !changeFor(node.key)) return false;
    if (state.view === 'audit' && !issuesFor(node.key).length) return false;
    return true;
  }

  function renderList(){
    const nodes = state.model.nodes.filter(nodeMatches);
    $('scListTitle').textContent = state.view === 'changes' ? '改动卡片' : state.view === 'audit' ? '体检卡片' : '卡片索引';
    $('scListCount').textContent = nodes.length;
    if (!nodes.length){
      $('scCardList').innerHTML = '<div class="sc-empty">没有符合当前筛选的卡片。</div>';
      return;
    }
    $('scCardList').innerHTML = nodes.map(node => {
      const change = changeFor(node.key);
      const dirty = dirtyFor(node.key);
      const review = reviewFor(node.key).value;
      const badge = dirty ? '未存' : change?.status === 'added' ? '新增' : change ? '改' : review ? reviewLabels[review].slice(0,2) : node.card.weight ? '入' : '续';
      return `<button class="sc-card-item ${node.key === state.selected ? 'selected' : ''} ${change ? 'changed' : ''}" data-card-key="${esc(node.key)}" type="button">
        <i class="sc-card-dot ${node.kind}"></i>
        <span><strong class="sc-card-name">${esc(node.card.card || node.card.id)}</strong><small class="sc-card-meta">${esc(themeTitle(node.card.thematic))} · ${esc(node.card.id)} · ${esc(kindTitle(node.kind))}</small></span>
        <em class="sc-card-badge">${esc(badge)}</em>
      </button>`;
    }).join('');
    $('scCardList').querySelectorAll('[data-card-key]').forEach(button =>
      button.addEventListener('click', () => selectCard(button.dataset.cardKey))
    );
  }

  function graphLayout(){
    const groups = new Map();
    state.model.nodes.forEach(node => {
      const theme = node.card.thematic || '未分类';
      if (!groups.has(theme)) groups.set(theme, []);
      groups.get(theme).push(node);
    });
    const order = [...groups.keys()];
    const positions = new Map();
    const nodeWidth = 140;
    const nodeHeight = 46;
    const columnGap = 22;
    const rowGap = 20;
    const columns = 11;
    const left = 178;
    let y = 18;
    const lanes = [];
    order.forEach(theme => {
      const nodes = groups.get(theme);
      const rows = Math.ceil(nodes.length / columns);
      const laneHeight = 48 + rows * (nodeHeight + rowGap);
      lanes.push({theme, y, height:laneHeight, nodes});
      nodes.forEach((node, index) => positions.set(node.key, {
        x:left + (index % columns) * (nodeWidth + columnGap),
        y:y + 36 + Math.floor(index / columns) * (nodeHeight + rowGap),
        w:nodeWidth,
        h:nodeHeight,
      }));
      y += laneHeight + 12;
    });
    return {groups, order, positions, lanes, width:left + columns * (nodeWidth + columnGap) + 18, height:y + 8};
  }

  function graphPath(a, b, offset=0){
    const x1 = a.x + a.w;
    const y1 = a.y + a.h / 2 + offset;
    const x2 = b.x;
    const y2 = b.y + b.h / 2 + offset;
    if (x2 >= x1){
      const bend = Math.max(24, (x2 - x1) * .45);
      return `M ${x1} ${y1} C ${x1+bend} ${y1}, ${x2-bend} ${y2}, ${x2} ${y2}`;
    }
    const side = Math.max(x1, x2) + 28 + Math.abs(y2-y1) * .05;
    return `M ${x1} ${y1} C ${side} ${y1}, ${side} ${y2}, ${x2} ${y2}`;
  }

  function relatedKeys(){
    if (!state.focus || !state.selected) return null;
    const selected = nodeFor(state.selected);
    if (!selected) return null;
    const keys = new Set([selected.key]);
    const queue = [{key:selected.key, depth:0}];
    while (queue.length){
      const current = queue.shift();
      if (current.depth >= 3 || keys.size >= 80) continue;
      for (const edge of nodeFor(current.key)?.outgoing || []){
        if (edge.kind === 'flag' && current.depth > 0) continue;
        if (!keys.has(edge.to)){
          keys.add(edge.to);
          queue.push({key:edge.to, depth:current.depth+1});
        }
      }
    }
    selected.incoming.forEach(edge => keys.add(edge.from));
    selected.outgoing.forEach(edge => keys.add(edge.to));
    return keys;
  }

  function renderGraph(){
    const layout = graphLayout();
    const filterKeys = new Set(state.model.nodes.filter(nodeMatches).map(node => node.key));
    const focusKeys = relatedKeys();
    const visible = key => filterKeys.has(key) && (!focusKeys || focusKeys.has(key));
    const laneMarkup = layout.lanes.map((lane, index) => {
      const core = lane.nodes.filter(node => node.kind !== 'flavor').length;
      return `<g opacity="${lane.nodes.some(node => visible(node.key)) ? 1 : .22}">
        <rect class="lane ${index % 2 ? 'alt' : ''}" x="0" y="${lane.y}" width="${layout.width}" height="${lane.height}" rx="2"></rect>
        <text class="lane-title" x="14" y="${lane.y+25}">${esc(themeTitle(lane.theme))}</text>
        <text class="lane-meta" x="14" y="${lane.y+44}">${esc(lane.theme)} · ${lane.nodes.length} 张 · ${core} 张机制相关</text>
      </g>`;
    }).join('');
    const edgeMarkup = state.model.edges.filter(edge => {
      if (edge.kind !== 'flag') return true;
      if (!state.showFlags || !state.selected) return false;
      if (edge.from === state.selected || edge.to === state.selected) return true;
      return !!focusKeys && focusKeys.has(edge.from) && focusKeys.has(edge.to);
    }).map((edge, index) => {
      const from = layout.positions.get(edge.from);
      const to = layout.positions.get(edge.to);
      if (!from || !to) return '';
      const hot = state.selected && (edge.from === state.selected || edge.to === state.selected);
      const dim = !visible(edge.from) || !visible(edge.to);
      return `<path class="edge ${edge.side} ${edge.kind} ${hot ? 'hot' : ''} ${dim ? 'dim' : ''}" d="${graphPath(from,to,(index%3-1)*2)}"></path>`;
    }).join('');
    const nodeMarkup = state.model.nodes.map(node => {
      const position = layout.positions.get(node.key);
      const change = changeFor(node.key);
      const dirty = dirtyFor(node.key);
      const review = reviewFor(node.key).value;
      const classes = [node.kind, node.key === state.selected ? 'selected' : '', visible(node.key) ? '' : 'dim', change ? 'changed' : '', dirty ? 'dirty' : '', review ? 'review-'+review : ''].filter(Boolean).join(' ');
      return `<g class="node ${classes}" data-graph-key="${esc(node.key)}" tabindex="0" role="button" aria-label="${esc(node.card.card || node.card.id)}" transform="translate(${position.x},${position.y})">
        <rect width="${position.w}" height="${position.h}"></rect>
        <circle class="node-mark" cx="12" cy="14" r="4"></circle>
        ${dirty ? '<rect class="node-dirty-mark" x="130" y="5" width="5" height="5" rx="0"></rect>' : ''}
        <text class="node-id" x="22" y="17">${esc(node.card.id)}</text>
        <text class="node-name" x="12" y="34">${esc(compact(node.card.card || '未命名', 22))}</text>
      </g>`;
    }).join('');
    $('scGraph').innerHTML = `<div class="sc-graph-world" style="width:${layout.width}px;height:${layout.height}px;transform:scale(${state.zoom})"><svg class="sc-graph-svg" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}" aria-label="故事卡片关系图">${laneMarkup}<g>${edgeMarkup}</g><g>${nodeMarkup}</g></svg></div>`;
    $('scGraph').style.width = `${layout.width * state.zoom}px`;
    $('scGraph').style.height = `${layout.height * state.zoom}px`;
    $('scZoomLabel').textContent = `${Math.round(state.zoom * 100)}%`;
    $('scGraph').querySelectorAll('[data-graph-key]').forEach(group => {
      group.addEventListener('click', () => selectCard(group.dataset.graphKey));
      group.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' '){
          event.preventDefault();
          selectCard(group.dataset.graphKey);
        }
      });
    });
  }

  function renderMain(){
    const graphView = state.view === 'graph';
    $('scViewport').hidden = !graphView;
    $('scReport').hidden = graphView;
    $('scGraphActions').hidden = !graphView;
    $('scMainTitle').textContent = graphView ? (state.focus && state.selected ? '影响范围' : '故事全局') : state.view === 'changes' ? '版本改动' : '叙事体检';
    $('scMainSubtitle').textContent = graphView ? '实线是直接跳转，虚线是状态标记牵动的后续' : state.view === 'changes' ? '逐字段查看当前牌库相对旧版的差异' : '机器只报告结构风险，叙事价值由人工标记';
    $('scBreadcrumb').textContent = state.theme === 'all' ? 'ALL THREADS' : state.theme.toUpperCase();
    $('scFocus').disabled = !state.selected;
    $('scFocus').classList.toggle('active', state.focus);
    if (graphView) renderGraph();
    else renderReport();
  }

  function renderReport(){
    if (state.view === 'changes'){
      const changes = [...state.changes.values()].sort((a,b) => ({added:0,changed:1,removed:2})[a.status]-({added:0,changed:1,removed:2})[b.status]);
      const visible = changes.filter(change => {
        const node = change.after;
        if (!node) return state.theme === 'all' && !state.search;
        return nodeMatches(node);
      });
      $('scReport').innerHTML = `<div class="sc-report-intro"><div><strong>${visible.length} 张卡有变化</strong>新增、删除与字段级修改</div><div>${state.baselineModel ? `${state.baselineModel.nodes.length} → ${state.model.nodes.length} 张` : '未设置基线'}</div></div>` +
        (visible.length ? visible.map(change => {
          const node = change.after || change.before;
          const fields = change.fields.map(item => M.labels[item.field] || item.field);
          return `<div class="sc-report-row" data-change-key="${esc(change.key)}"><span class="sc-report-state ${change.status}">${change.status === 'added' ? '新增' : change.status === 'removed' ? '删除' : '修改'}</span><div><div class="sc-report-name">${esc(node.card.card || node.card.id)}</div><div class="sc-report-meta">${esc(themeTitle(node.card.thematic))} · ${esc(compact(node.card.question, 100))}</div></div><div class="sc-report-fields">${esc(fields.slice(0,5).join(' / ') || '整张卡')} ${fields.length>5 ? `+${fields.length-5}` : ''}</div></div>`;
        }).join('') : '<div class="sc-empty">当前筛选下没有版本改动。</div>');
      $('scReport').querySelectorAll('[data-change-key]').forEach(row => row.addEventListener('click', () => selectChange(row.dataset.changeKey)));
      return;
    }
    const issues = [...state.model.issues].sort((a,b) => severityOrder[a.severity]-severityOrder[b.severity]);
    const visible = issues.filter(issue => {
      const node = nodeFor(issue.key);
      return node && nodeMatches(node);
    });
    const errors = issues.filter(issue => issue.severity === 'error').length;
    const warnings = issues.filter(issue => issue.severity === 'warning').length;
    $('scReport').innerHTML = `<div class="sc-report-intro"><div><strong>${errors} 个错误 · ${warnings} 个警告</strong>不可达、断裂跳转、悬空状态与相同机制结果</div><div>${issues.length} 条提示</div></div>` +
      (visible.length ? visible.map(issue => {
        const node = nodeFor(issue.key);
        return `<div class="sc-report-row" data-issue-key="${esc(issue.key)}"><span class="sc-report-state ${issue.severity}">${issue.severity === 'error' ? '错误' : issue.severity === 'warning' ? '警告' : '提示'}</span><div><div class="sc-report-name">${esc(node?.card.card || issue.key)}</div><div class="sc-report-meta">${esc(issue.message)}</div></div><div class="sc-report-fields">${esc(issue.code)}</div></div>`;
      }).join('') : '<div class="sc-empty">当前筛选下没有体检提示。</div>');
    $('scReport').querySelectorAll('[data-issue-key]').forEach(row => row.addEventListener('click', () => selectCard(row.dataset.issueKey)));
  }

  function selectCard(key){
    if (!nodeFor(key)) return;
    state.selected = key;
    state.selectedChange = null;
    state.editing = null;
    document.body.classList.add('inspector-open');
    render();
    if (state.view === 'graph') scrollNodeIntoView(key);
  }

  function selectChange(key){
    const change = changeFor(key);
    if (!change) return;
    if (change.after){ selectCard(key); return; }
    state.selected = null;
    state.selectedChange = key;
    state.editing = null;
    document.body.classList.add('inspector-open');
    renderInspector();
  }

  function scrollNodeIntoView(key){
    const layout = graphLayout();
    const position = layout.positions.get(key);
    const viewport = $('scViewport');
    if (!position) return;
    viewport.scrollTo({
      left:Math.max(0, position.x * state.zoom - viewport.clientWidth / 2),
      top:Math.max(0, position.y * state.zoom - viewport.clientHeight / 2),
      behavior:'smooth',
    });
  }

  function statusText(node){
    if (dirtyFor(node.key)) return '本次修改尚未写回';
    const change = changeFor(node.key);
    if (change?.status === 'added') return '相对旧版：新增';
    if (change) return `相对旧版：${change.fields.length} 项修改`;
    if (issuesFor(node.key).some(issue => issue.severity === 'error')) return '存在结构问题';
    return node.card.weight ? '随机入口卡' : '续写卡';
  }

  function deltaText(deltas){
    const values = Object.entries(deltas).filter(([,value]) => value).map(([resource,value]) => `${M.resources[resource]}${value>0?'+':''}${value}`);
    return values.length ? values.join(' · ') : '不改资源数值';
  }

  function effectText(effect){
    const parts = [];
    if (effect.target !== null) parts.push(`跳到 ${state.model.nodes[effect.target]?.card.card || '#'+effect.target}`);
    else parts.push('回到随机牌堆');
    if (effect.ending) parts.push(`结局 ${effect.ending}`);
    if (effect.actions.length) parts.push(effect.actions.map(action => action.token).join(' · '));
    return parts.join(' / ');
  }

  function relationMarkup(label, edges, direction){
    if (!edges.length) return `<div class="sc-relations"><strong>${label}</strong><span class="sc-inspector-sub">无</span></div>`;
    return `<div class="sc-relations"><strong>${label}</strong><div>${edges.slice(0,12).map(edge => {
      const key = direction === 'out' ? edge.to : edge.from;
      const node = nodeFor(key);
      const sides = (edge.sides || [edge.side]).filter(Boolean).map(side => side === 'yes' ? '右划' : '左划').join(' / ');
      const prefix = edge.kind === 'flag' ? `${edge.flag} → ` : `${sides} → `;
      return `<button type="button" data-relation-key="${esc(key)}">${esc(prefix + (node?.card.card || key))}</button>`;
    }).join('')}</div></div>`;
  }

  function diffMarkup(change){
    if (!change) return '';
    if (change.status === 'added') return '<div class="sc-section"><div class="sc-section-title"><span>版本改动</span></div><div class="sc-diff"><code>新增卡片</code></div></div>';
    return `<div class="sc-section"><div class="sc-section-title"><span>版本改动</span><span>${change.fields.length} 项</span></div>${change.fields.map(item => `<div class="sc-diff"><code>${esc(M.labels[item.field] || item.field)}</code><del>${esc(compact(item.before || '（空）', 120))}</del><ins>${esc(compact(item.after || '（空）', 120))}</ins></div>`).join('')}</div>`;
  }

  function renderInspector(){
    if (state.editing){ renderEditor(); return; }
    if (state.selectedChange && !state.selected){ renderRemovedInspector(); return; }
    const node = state.selected ? nodeFor(state.selected) : null;
    if (!node){
      $('scInspector').innerHTML = '<div class="sc-inspector-empty">从左侧或图谱选择一张卡片。</div>';
      return;
    }
    const card = node.card;
    const issues = issuesFor(node.key);
    const review = reviewFor(node.key);
    $('scInspector').innerHTML = `<div class="sc-inspector-inner">
      <div class="sc-inspector-top"><div><div class="sc-inspector-kicker">${esc(themeTitle(card.thematic))} / ${esc(card.id)}</div><h3>${esc(card.card || '未命名')}</h3></div><button id="scInspectorClose" class="icon-button" type="button" aria-label="关闭详情" title="关闭详情">×</button></div>
      <div class="sc-inspector-sub">${esc(card.bearer || '未署名')}<br>条件：${esc(card.conditions || '始终可见')}<br>${card.weight ? `入口卡 · 权重 ${esc(card.weight)}` : '续写卡 · 只能由跳转进入'} · ${esc(kindTitle(node.kind))}</div>
      <span class="sc-status">${esc(statusText(node))}</span>
      <div class="sc-inspector-actions"><button id="scEditCard" class="primary" type="button">编辑卡片</button><button id="scDuplicateCard" type="button">复制</button><button id="scDeleteCard" type="button">删除</button></div>
      <section class="sc-section"><div class="sc-section-title"><span>卡面正文</span></div><div class="sc-copy">${esc(card.question || '（空）')}</div></section>
      <section class="sc-section"><div class="sc-section-title"><span>选择与后果</span></div>
        <div class="sc-choice"><strong>右划 · ${esc(card.override_yes || '是')}</strong><p><span class="delta">${esc(deltaText(node.yes.deltas))}</span><br>${esc(effectText(node.yes))}<br>${esc(card.answer_yes || '无回应')}</p></div>
        <div class="sc-choice no"><strong>左划 · ${esc(card.override_no || '否')}</strong><p><span class="delta">${esc(deltaText(node.no.deltas))}</span><br>${esc(effectText(node.no))}<br>${esc(card.answer_no || '无回应')}</p></div>
      </section>
      <section class="sc-section"><div class="sc-section-title"><span>故事关系</span><span>${node.incoming.length + node.outgoing.length}</span></div>${relationMarkup('流向',node.outgoing,'out')}${relationMarkup('来源',node.incoming,'in')}</section>
      ${node.unusedFlags.length ? `<section class="sc-section"><div class="sc-section-title"><span>暂未回收的状态</span></div>${node.unusedFlags.map(flag => `<span class="sc-tag">${esc(flag)}</span>`).join('')}</section>` : ''}
      <section class="sc-section"><div class="sc-section-title"><span>人工叙事判断</span></div>
        <div class="sc-review-buttons">${['key','pace','rewrite','remove'].map(value => `<button type="button" data-review-value="${value}" class="${review.value===value?'active':''}">${esc(reviewLabels[value])}</button>`).join('')}</div>
        <textarea id="scReviewNote" class="sc-review-note" placeholder="记录这张卡为什么保留、要改什么，或它影响了哪条线">${esc(review.note || '')}</textarea>
      </section>
      ${issues.length ? `<section class="sc-section"><div class="sc-section-title"><span>叙事体检</span><span>${issues.length}</span></div>${issues.map(issue => `<div class="sc-issue ${issue.severity}">${esc(issue.message)}<br><span class="sc-card-meta">${esc(issue.code)}</span></div>`).join('')}</section>` : ''}
      ${diffMarkup(changeFor(node.key))}
    </div>`;
    $('scInspectorClose').addEventListener('click', closeInspector);
    $('scEditCard').addEventListener('click', () => { state.editing = {mode:'edit', key:node.key}; renderInspector(); });
    $('scDuplicateCard').addEventListener('click', () => duplicateCard(node));
    $('scDeleteCard').addEventListener('click', () => deleteCard(node));
    $('scInspector').querySelectorAll('[data-relation-key]').forEach(button => button.addEventListener('click', () => selectCard(button.dataset.relationKey)));
    $('scInspector').querySelectorAll('[data-review-value]').forEach(button => button.addEventListener('click', () => updateReview(node.key, button.dataset.reviewValue)));
    $('scReviewNote').addEventListener('change', event => updateReviewNote(node.key, event.target.value));
  }

  function renderRemovedInspector(){
    const change = changeFor(state.selectedChange);
    const node = change?.before;
    if (!node){ state.selectedChange = null; renderInspector(); return; }
    $('scInspector').innerHTML = `<div class="sc-inspector-inner"><div class="sc-inspector-top"><div><div class="sc-inspector-kicker">已从当前牌库删除</div><h3>${esc(node.card.card || node.card.id)}</h3></div><button id="scInspectorClose" class="icon-button" type="button" aria-label="关闭详情">×</button></div><div class="sc-inspector-sub">${esc(themeTitle(node.card.thematic))} · ${esc(node.card.id)}</div><section class="sc-section"><div class="sc-section-title"><span>旧版正文</span></div><div class="sc-copy">${esc(node.card.question || '（空）')}</div></section><div class="sc-diff"><code>删除卡片</code><del>${esc(compact(node.card.question,180))}</del></div></div>`;
    $('scInspectorClose').addEventListener('click', closeInspector);
  }

  function closeInspector(){
    document.body.classList.remove('inspector-open');
    state.editing = null;
  }

  function updateReview(key, value){
    const current = reviewFor(key);
    state.reviews[key] = {value:current.value === value ? '' : value, note:current.note || ''};
    localStorage.setItem(reviewStorage, JSON.stringify(state.reviews));
    renderOverview();
    renderList();
    renderGraph();
    renderInspector();
  }

  function updateReviewNote(key, note){
    const current = reviewFor(key);
    state.reviews[key] = {value:current.value || '', note:String(note || '').trim()};
    localStorage.setItem(reviewStorage, JSON.stringify(state.reviews));
    toast('审阅备注已保存在浏览器');
  }

  function nextId(){
    return String(Math.max(0, ...state.cards.map(card => /^\d+$/.test(card.id) ? Number(card.id) : 0)) + 1);
  }

  function uniqueName(base){
    const names = new Set(state.cards.map(card => card.card));
    let value = base || 'new_card';
    let suffix = 2;
    while (names.has(value)) value = `${base || 'new_card'}_${suffix++}`;
    return value;
  }

  function blankCard(){
    const card = Object.fromEntries(M.fields.map(field => [field,'']));
    card.id = nextId();
    card.card = uniqueName(`new_${card.id}`);
    card.thematic = state.theme === 'all' ? 'daily' : state.theme;
    card.lockturn = 'del';
    return card;
  }

  function duplicateCard(node){
    const sourceIndex = state.cards.findIndex(card => M.key(card) === node.key);
    const copy = clone(node.card);
    copy.id = nextId();
    copy.card = uniqueName(`${copy.card || 'card'}_copy`);
    state.cards.splice(sourceIndex + 1, 0, copy);
    rebuild();
    state.selected = M.key(copy);
    state.editing = {mode:'edit', key:state.selected};
    render();
    toast('已复制卡片，尚未写回');
  }

  function deleteCard(node){
    ask('删除卡片', `删除 ${node.card.card || node.card.id}？引用它的跳转会在体检中标红。`, () => {
      state.cards = state.cards.filter(card => M.key(card) !== node.key);
      state.selected = null;
      state.editing = null;
      rebuild();
      render();
      toast('卡片已从工作区删除，尚未写回');
    });
  }

  function fieldMarkup(field, label, value, {wide=false, textarea=false}={}){
    const content = textarea
      ? `<textarea data-field="${field}">${esc(value)}</textarea>`
      : `<input data-field="${field}" value="${esc(value)}">`;
    return `<label class="sc-field ${wide?'wide':''}">${label}${content}</label>`;
  }

  function renderEditor(){
    const isNew = state.editing.mode === 'new';
    const card = isNew ? state.editing.card : nodeFor(state.editing.key)?.card;
    if (!card){ state.editing = null; renderInspector(); return; }
    $('scInspector').innerHTML = `<form id="scEditForm" class="sc-edit-form">
      <div class="sc-edit-head"><div><div class="sc-inspector-kicker">${isNew?'NEW CARD':'EDIT CARD'}</div><h3>${esc(card.card || card.id)}</h3></div><button id="scEditorClose" class="icon-button" type="button" aria-label="关闭编辑">×</button></div>
      <div class="sc-form-grid">
        ${fieldMarkup('thematic','故事线',card.thematic)}${fieldMarkup('id','ID',card.id)}
        ${fieldMarkup('card','引用名',card.card,{wide:true})}${fieldMarkup('bearer','人物',card.bearer,{wide:true})}
        ${fieldMarkup('conditions','出现条件',card.conditions,{wide:true})}${fieldMarkup('lockturn','冷却 / 一次性',card.lockturn)}${fieldMarkup('weight','抽取权重',card.weight)}
        ${fieldMarkup('question','卡面正文',card.question,{wide:true,textarea:true})}
      </div>
      <div class="sc-form-group"><h4>右划选择</h4><div class="sc-form-grid">
        ${fieldMarkup('override_yes','按钮文字',card.override_yes,{wide:true})}${fieldMarkup('answer_yes','人物回应',card.answer_yes,{wide:true,textarea:true})}
        ${fieldMarkup('yes_cash','现金流',card.yes_cash)}${fieldMarkup('yes_team','团队',card.yes_team)}${fieldMarkup('yes_market','市场',card.yes_market)}${fieldMarkup('yes_capital','资本',card.yes_capital)}
        ${fieldMarkup('yes_custom','状态 / 跳转',card.yes_custom,{wide:true,textarea:true})}
      </div></div>
      <div class="sc-form-group"><h4>左划选择</h4><div class="sc-form-grid">
        ${fieldMarkup('override_no','按钮文字',card.override_no,{wide:true})}${fieldMarkup('answer_no','人物回应',card.answer_no,{wide:true,textarea:true})}
        ${fieldMarkup('no_cash','现金流',card.no_cash)}${fieldMarkup('no_team','团队',card.no_team)}${fieldMarkup('no_market','市场',card.no_market)}${fieldMarkup('no_capital','资本',card.no_capital)}
        ${fieldMarkup('no_custom','状态 / 跳转',card.no_custom,{wide:true,textarea:true})}
      </div></div>
      <div id="scEditorError" class="sc-inline-error" hidden></div>
      <div class="sc-form-actions"><button id="scCancelEdit" type="button">取消</button><button class="primary" type="submit">保存到工作区</button></div>
    </form>`;
    $('scEditorClose').addEventListener('click', cancelEdit);
    $('scCancelEdit').addEventListener('click', cancelEdit);
    $('scEditForm').addEventListener('submit', saveEdit);
  }

  function cancelEdit(){
    state.editing = null;
    renderInspector();
  }

  function saveEdit(event){
    event.preventDefault();
    const card = Object.fromEntries(M.fields.map(field => [field, String(event.currentTarget.querySelector(`[data-field="${field}"]`)?.value || '').trim()]));
    const originalKey = state.editing.mode === 'edit' ? state.editing.key : null;
    const duplicateId = state.cards.find(item => item.id === card.id && M.key(item) !== originalKey);
    const duplicateName = card.card && state.cards.find(item => item.card === card.card && M.key(item) !== originalKey);
    const error = !card.id ? 'ID 不能为空。' : duplicateId ? `ID ${card.id} 已存在。` : duplicateName ? `引用名 ${card.card} 已存在。` : '';
    if (error){
      $('scEditorError').hidden = false;
      $('scEditorError').textContent = error;
      return;
    }
    if (state.editing.mode === 'new') state.cards.push(card);
    else {
      const index = state.cards.findIndex(item => M.key(item) === originalKey);
      if (index < 0) return;
      state.cards[index] = card;
      if (originalKey !== M.key(card) && state.reviews[originalKey]){
        state.reviews[M.key(card)] = state.reviews[originalKey];
        delete state.reviews[originalKey];
        localStorage.setItem(reviewStorage, JSON.stringify(state.reviews));
      }
    }
    state.selected = M.key(card);
    state.editing = null;
    rebuild();
    render();
    toast('卡片已更新到工作区，尚未写回');
  }

  function ask(title, message, action){
    state.confirmAction = action;
    $('scConfirmTitle').textContent = title;
    $('scConfirmText').textContent = message;
    $('scConfirmDialog').showModal();
  }

  async function saveCards(){
    if (!state.dirty.size || state.saving) return;
    state.saving = true;
    updateButtons();
    try {
      const response = await fetch('/api/cards', {
        method:'PUT',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({cards:state.cards, expectedVersion:state.version}),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || '保存失败');
      state.version = payload.version;
      state.modifiedAt = payload.modifiedAt || new Date().toISOString().slice(0,19);
      state.savedCards = clone(state.cards);
      rebuild();
      render();
      toast(`已写回 cards.csv；备份 ${payload.backup}`);
    } catch (error) {
      toast(error.message);
    } finally {
      state.saving = false;
      updateButtons();
    }
  }

  function undoAll(){
    if (!state.dirty.size) return;
    ask('放弃未保存修改', `将撤销 ${state.dirty.size} 张卡的工作区改动。`, () => {
      state.cards = clone(state.savedCards);
      state.selected = null;
      state.editing = null;
      rebuild();
      render();
      toast('未保存修改已撤销');
    });
  }

  function download(filename, content, type){
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function exportCsv(){
    download('cards-edited.csv', M.csv(state.cards), 'text/csv;charset=utf-8');
    toast('已导出当前工作区 CSV');
  }

  function exportReview(){
    const payload = {
      generatedAt:new Date().toISOString(),
      source:state.source,
      baseline:loadCustomBaseline()?.name || state.baselineSource,
      summary:{cards:state.cards.length, changes:state.changes.size, dirty:state.dirty.size, issues:state.model.issues.length},
      reviews:state.reviews,
      changes:[...state.changes.values()].map(change => ({key:change.key,status:change.status,fields:change.fields})),
      issues:state.model.issues,
    };
    download('story-review.json', JSON.stringify(payload,null,2), 'application/json;charset=utf-8');
    toast('已导出审阅记录');
  }

  function setCurrentBaseline(){
    $('scBaselineDialog').showModal();
  }

  function confirmBaseline(event){
    event.preventDefault();
    const name = $('scBaselineName').value.trim() || '故事版本';
    localStorage.setItem(baselineStorage, JSON.stringify({name, cards:state.cards, savedAt:new Date().toISOString()}));
    state.baseline = clone(state.cards);
    rebuild();
    $('scBaselineDialog').close();
    render();
    toast('已设置新的浏览器对比基线');
  }

  function resetBaseline(){
    localStorage.removeItem(baselineStorage);
    state.baseline = clone(state.projectBaseline);
    rebuild();
    render();
    toast('已恢复项目基线');
  }

  function importBaseline(file){
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const raw = String(reader.result || '');
        const parsed = raw.trim().startsWith('{') ? JSON.parse(raw) : M.parseCSV(raw);
        const cards = Array.isArray(parsed) ? parsed : parsed.cards;
        if (!cards?.length) throw new Error('文件中没有卡片');
        const normalized = M.normalize(cards);
        localStorage.setItem(baselineStorage, JSON.stringify({name:file.name,cards:normalized,savedAt:new Date().toISOString()}));
        state.baseline = normalized;
        rebuild();
        render();
        toast(`已载入基线 ${file.name}`);
      } catch (error) {
        toast(`基线载入失败：${error.message}`);
      }
    };
    reader.readAsText(file, 'utf-8');
  }

  function setView(view){
    state.view = view;
    state.focus = false;
    render();
  }

  function fitGraph(){
    const layout = graphLayout();
    const viewport = $('scViewport');
    state.zoom = Math.max(.45, Math.min(1, (viewport.clientWidth - 22) / layout.width, (viewport.clientHeight - 22) / layout.height));
    renderGraph();
    viewport.scrollTo({left:0,top:0});
  }

  function bindPan(){
    const viewport = $('scViewport');
    let active = false;
    let start = null;
    let origin = null;
    viewport.addEventListener('pointerdown', event => {
      if (event.target.closest('[data-graph-key]')) return;
      active = true;
      start = {x:event.clientX,y:event.clientY};
      origin = {x:viewport.scrollLeft,y:viewport.scrollTop};
      viewport.classList.add('dragging');
      viewport.setPointerCapture(event.pointerId);
    });
    viewport.addEventListener('pointermove', event => {
      if (!active) return;
      viewport.scrollLeft = origin.x - (event.clientX - start.x);
      viewport.scrollTop = origin.y - (event.clientY - start.y);
    });
    const stop = () => { active = false; viewport.classList.remove('dragging'); };
    viewport.addEventListener('pointerup', stop);
    viewport.addEventListener('pointercancel', stop);
  }

  function toast(message){
    const element = $('scToast');
    element.textContent = message;
    element.classList.add('on');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => element.classList.remove('on'), 3000);
  }

  function wire(){
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
    $('scSearch').addEventListener('input', event => { state.search = event.target.value.trim(); render(); });
    $('scTheme').addEventListener('change', event => { state.theme = event.target.value; render(); });
    $('scKind').addEventListener('change', event => { state.kind = event.target.value; render(); });
    $('scShowFlags').addEventListener('change', event => { state.showFlags = event.target.checked; renderGraph(); });
    $('scReload').addEventListener('click', () => loadStory());
    $('scSave').addEventListener('click', saveCards);
    $('scUndoAll').addEventListener('click', undoAll);
    $('scAddCard').addEventListener('click', () => { state.editing={mode:'new',card:blankCard()}; document.body.classList.add('inspector-open'); renderInspector(); });
    $('scClearFocus').addEventListener('click', () => { state.focus=false;state.selected=null;render();$('scViewport').scrollTo({left:0,top:0,behavior:'smooth'}); });
    $('scFocus').addEventListener('click', () => { state.focus=!state.focus;renderMain(); });
    $('scZoomIn').addEventListener('click', () => { state.zoom=Math.min(1.4,+(state.zoom+.1).toFixed(2));renderGraph(); });
    $('scZoomOut').addEventListener('click', () => { state.zoom=Math.max(.45,+(state.zoom-.1).toFixed(2));renderGraph(); });
    $('scFit').addEventListener('click', fitGraph);
    $('scMore').addEventListener('click', event => { event.stopPropagation();$('scMoreMenu').hidden=!$('scMoreMenu').hidden; });
    document.addEventListener('click', event => { if (!event.target.closest('.sc-header-actions')) $('scMoreMenu').hidden=true; });
    $('scExportCsv').addEventListener('click', exportCsv);
    $('scExportReview').addEventListener('click', exportReview);
    $('scImportBaseline').addEventListener('click', () => $('scBaselineFile').click());
    $('scResetBaseline').addEventListener('click', resetBaseline);
    $('scBaselineFile').addEventListener('change', event => { if(event.target.files[0]) importBaseline(event.target.files[0]);event.target.value=''; });
    $('scSetBaseline').addEventListener('click', setCurrentBaseline);
    $('scBaselineConfirm').addEventListener('click', confirmBaseline);
    $('scConfirmAction').addEventListener('click', event => {
      event.preventDefault();
      const action = state.confirmAction;
      state.confirmAction = null;
      $('scConfirmDialog').close();
      action?.();
    });
    window.addEventListener('beforeunload', event => { if(state.dirty.size){event.preventDefault();event.returnValue='';} });
    bindPan();
  }

  wire();
  loadStory({quiet:true});
})();
