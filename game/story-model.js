(function(root){
  'use strict';
  const fields = ['thematic','card','id','bearer','conditions','lockturn','weight','question','override_yes','answer_yes','yes_cash','yes_team','yes_market','yes_capital','yes_custom','override_no','answer_no','no_cash','no_team','no_market','no_capital','no_custom'];
  const resources = {cash:'现金流',team:'团队',market:'市场',capital:'资本'};
  const systemValues = new Set(['cash','money','team','market','capital','dynasty','turn','year','overall']);
  const themes = {
    rescue:['01','救命钱','现金危机与第一份承诺'], control:['02','谁的公司','控制权与联创的立场'],
    leak:['03','泄露之后','旧账、真相与责任'], reckoning:['04','最后一张表','上市与出售的清算'],
    aftermath:['05','余波','留给下一任的公司'], pressure:['!','危险区','资源边界与救急机会'],
    daily:['D','日常牌堆','经营节奏、资源与伏笔'], endings:['E','任期结局','离场方式与继任遗产'],
    split:['01','联创决裂','伙伴、控制权与竞争'], crisis:['02','资金链断裂','一笔救命钱的代价'], ipo:['04','上市前夜','敲钟之前的筹码']
  };
  const labels = {thematic:'故事线',card:'引用名',id:'ID',bearer:'人物',conditions:'出现条件',lockturn:'冷却 / 一次性',weight:'抽取权重',question:'卡面正文',override_yes:'右划选项',answer_yes:'右划回应',yes_custom:'右划状态 / 跳转',override_no:'左划选项',answer_no:'左划回应',no_custom:'左划状态 / 跳转',order:'表内位置',target_yes:'右划实际跳转',target_no:'左划实际跳转'};
  for (const side of ['yes','no']) for (const resource of Object.keys(resources)) labels[side+'_'+resource] = (side === 'yes' ? '右划 · ' : '左划 · ') + resources[resource];
  function normalize(cards){ return cards.map(card => Object.fromEntries(fields.map(field => [field,String(card[field] ?? '').trim()]))); }
  function key(card){ return card.id ? 'id:'+card.id : 'name:'+card.card; }
  function tokens(value){ return String(value || '').split(/\s+and\s+/).map(token => token.trim()).filter(Boolean); }
  function number(value){ const match = String(value || '').replace(/[?*]/g,'').trim().match(/^-?\d+/); return match ? Number(match[0]) : 0; }
  function weight(card){ return card.weight === 'max' ? 1e9 : parseInt(card.weight,10) || 0; }
  function parseCSV(text){
    const input = String(text).replace(/^\uFEFF/,'');
    const delimiter = input.split(/\r?\n/,1)[0].includes(';') ? ';' : ',';
    const rows = []; let row = [], cell = '', quoted = false;
    for (let position = 0; position < input.length; position++){
      const character = input[position];
      if (character === '"'){
        if (quoted && input[position+1] === '"'){ cell += '"'; position++; }
        else if (quoted || !cell) quoted = !quoted;
        else cell += character;
      } else if (character === delimiter && !quoted){ row.push(cell); cell = ''; }
      else if ((character === '\n' || character === '\r') && !quoted){
        if (character === '\r' && input[position+1] === '\n') position++;
        row.push(cell); if (row.some(value => value.trim())) rows.push(row); row = []; cell = '';
      } else cell += character;
    }
    if (quoted) throw Error('CSV 引号没有闭合，请检查多行正文。');
    row.push(cell); if (row.some(value => value.trim())) rows.push(row);
    if (rows.length < 2) throw Error('CSV 没有可读取的卡片。');
    const header = rows.shift().map(value => value.trim());
    if (new Set(header).size !== header.length || fields.some(field => !header.includes(field))) throw Error('CSV 必须包含 cards.csv 的 22 个不重复列名。');
    const cards = rows.map((values,index) => {
      if (values.length !== header.length) throw Error('CSV 第 '+(index+2)+' 行列数不匹配。');
      return Object.fromEntries(header.map((field,column) => [field,values[column].trim()]));
    }).filter(card => card.id);
    if (!cards.length) throw Error('CSV 中没有带 ID 的卡片。');
    const ids = new Set(), names = new Set();
    for (const card of cards){
      if (ids.has(card.id) || (card.card && names.has(card.card))) throw Error('ID 或卡片引用名重复：'+(card.card || card.id));
      ids.add(card.id); if (card.card) names.add(card.card);
    }
    return normalize(cards);
  }
  function resolveJump(cards,token,index,names){
    if (!token.startsWith('>')) return null;
    const lookup = names || new Map(cards.filter(card => card.card).map(card => [card.card,cards.indexOf(card)]));
    const arrows = token.match(/^>+/)[0].length, rest = token.slice(arrows);
    if (rest.startsWith('_')) return lookup.get(rest.slice(1)) ?? null;
    if (lookup.has(rest)) return lookup.get(rest);
    if (/^\d+$/.test(rest)) return index + Number(rest);
    return index + arrows;
  }
  function conditionParts(value){
    return tokens(value).map(raw => {
      const comparison = raw.match(/^([a-zA-Z_][\w]*)\s*(>=|<=|>|<|=)\s*(-?\d+)$/);
      if (comparison) return {raw,name:comparison[1],operator:comparison[2],value:Number(comparison[3]),valid:true};
      const boolean = raw.match(/^(!?)([a-zA-Z_][\w]*)$/);
      return boolean ? {raw,name:boolean[2],operator:boolean[1] ? '!' : 'truthy',valid:true} : {raw,name:raw,valid:false};
    });
  }
  function effects(cards,index,side,names){
    const card = cards[index], actions = [], jumps = []; let target = null, ending = null;
    for (const token of tokens(card[side+'_custom'])){
      if (token.startsWith('>')){
        const candidate = resolveJump(cards,token,index,names);
        jumps.push({token,target:candidate});
        if (candidate !== null) target = candidate;
      } else if (token.startsWith('end_') && card.thematic === 'endings') ending = token.slice(4);
      else if (token.startsWith('mus_')) continue;
      else if (token.endsWith('+')){ const flag = token.replace(/\++$/,''); actions.push({flag,op:'increment',amount:token.length-flag.length,token}); }
      else if (token.startsWith('!')) actions.push({flag:token.slice(1),op:'clear',amount:0,token});
      else actions.push({flag:token,op:'set',amount:1,token});
    }
    return {actions,jumps,target,ending,deltas:Object.fromEntries(Object.keys(resources).map(resource => [resource,number(card[side+'_'+resource])]))};
  }
  function build(input,options={}){
    const cards = normalize(input), names = new Map(), byKey = new Map(), issues = [], edges = [];
    const addIssue = (card,severity,code,message) => issues.push({key:key(card),severity,code,message});
    cards.forEach((card,index) => {
      if (byKey.has(key(card))) addIssue(card,'error','duplicate','卡片 ID 重复，无法稳定对比版本。');
      if (card.card && names.has(card.card)) addIssue(card,'error','duplicate-name','跳转引用名重复，引擎只会使用最后一张。');
      if (!card.card) addIssue(card,'warning','no-name','缺少引用名，冷却与已见记录可能和其他无名卡混用。');
      if (card.card) names.set(card.card,index);
      byKey.set(key(card),index);
    });
    const nodes = cards.map((card,index) => ({card,index,key:key(card),conditions:conditionParts(card.conditions),yes:effects(cards,index,'yes',names),no:effects(cards,index,'no',names),incoming:[],outgoing:[]}));
    const readers = new Map(), writers = new Map();
    for (const node of nodes){
      for (const condition of node.conditions){
        if (!condition.valid) addIssue(node.card,'warning','condition-syntax','无法静态解释条件：'+condition.raw);
        if (systemValues.has(condition.name)) continue;
        if (!readers.has(condition.name)) readers.set(condition.name,[]);
        readers.get(condition.name).push({node,condition});
      }
      for (const side of ['yes','no']){
        const effect = node[side];
        for (const jump of effect.jumps){
          if (jump.target === null || !nodes[jump.target]) addIssue(node.card,'error','broken-jump',(side === 'yes' ? '右划' : '左划')+'跳转不存在：'+jump.token);
          const rest = jump.token.replace(/^>+/,'');
          if (rest && !rest.startsWith('_') && !/^\d+$/.test(rest) && !names.has(rest)) addIssue(node.card,'warning','fallback-jump','未知跳转名 '+rest+' 会被引擎当作行偏移。');
        }
        if (effect.jumps.length > 1) addIssue(node.card,'warning','overridden-jump','同一选择含多个跳转，最后一次有效赋值覆盖前面跳转。');
        if (nodes[effect.target]) edges.push({from:node.key,to:nodes[effect.target].key,kind:'jump',side,label:side === 'yes' ? '右划' : '左划'});
        for (const action of effect.actions){
          if (!writers.has(action.flag)) writers.set(action.flag,[]);
          writers.get(action.flag).push({node,side,action});
        }
      }
      if (node.card.weight && weight(node.card) <= 0) addIssue(node.card,'warning','weight','非正数权重无法正常随机入池。');
    }
    for (const [flag,producers] of writers){
      for (const producer of producers) for (const reader of readers.get(flag) || []){
        if (producer.node.key === reader.node.key) continue;
        edges.push({from:producer.node.key,to:reader.node.key,kind:'flag',side:producer.side,flag,action:producer.action.op,predicate:reader.condition.raw,label:flag+' → '+reader.condition.raw});
      }
    }
    const compactEdges = [], edgeIndex = new Map();
    for (const edge of edges){
      const edgeKey = [edge.kind,edge.from,edge.to,edge.kind === 'jump' ? edge.side : '',edge.flag || '',edge.action || '',edge.predicate || ''].join('|');
      const previous = edgeIndex.get(edgeKey);
      if (previous){
        previous.sides = [...new Set(previous.sides.concat(edge.side).filter(Boolean))];
      } else {
        edge.sides = edge.side ? [edge.side] : [];
        edgeIndex.set(edgeKey,edge);
        compactEdges.push(edge);
      }
    }
    edges.length = 0;
    edges.push(...compactEdges);
    const indexByKey = new Map(nodes.map(node => [node.key,node]));
    edges.forEach((edge,index) => { edge.id = 'edge-'+index; indexByKey.get(edge.from).outgoing.push(edge); indexByKey.get(edge.to).incoming.push(edge); });
    const reached = new Set(nodes.filter(node => weight(node.card)>0).map(node => node.key));
    const queue = [...reached];
    for (let position=0; position<queue.length; position++) for (const edge of indexByKey.get(queue[position]).outgoing){
      if (edge.kind !== 'jump' || reached.has(edge.to)) continue;
      reached.add(edge.to); queue.push(edge.to);
    }
    const externalFlags = new Set(options.systemFlags || ['debt_keep','badrep_keep','public_keep']);
    for (const node of nodes){
      const direct = node.incoming.concat(node.outgoing).some(edge => edge.kind === 'jump');
      const stateful = node.conditions.some(condition => !systemValues.has(condition.name)) || node.yes.actions.length || node.no.actions.length;
      const numeric = ['yes','no'].some(side => Object.values(node[side].deltas).some(value => value !== 0));
      node.kind = node.yes.ending || node.no.ending ? 'ending' : direct ? 'story' : stateful ? 'state' : numeric ? 'resource' : 'flavor';
      if (!reached.has(node.key)) addIssue(node.card,'error','unreachable','没有随机入口能沿直接跳转到达这张续写卡（含封闭环）。');
      for (const condition of node.conditions){
        const positive = condition.operator === 'truthy' || ((condition.operator === '>' || condition.operator === '>=' || condition.operator === '=') && condition.value > 0);
        if (positive && !systemValues.has(condition.name) && !writers.has(condition.name) && !externalFlags.has(condition.name)) addIssue(node.card,'warning','no-writer','条件 '+condition.raw+' 没有在卡牌表或已知继任遗产中找到写入来源。');
      }
      const signature = side => JSON.stringify({target:node[side].target,ending:node[side].ending,actions:node[side].actions.map(action => action.token).sort(),deltas:node[side].deltas});
      node.sameOutcome = signature('yes') === signature('no');
      if (node.sameOutcome && node.kind !== 'ending') addIssue(node.card,'info','same-outcome','两侧机制结果相同；可能是语气或氛围选择，请人工判断叙事价值。');
      node.unusedFlags = [...new Set(node.yes.actions.concat(node.no.actions).filter(action => !readers.has(action.flag)).map(action => action.flag))];
      if (node.unusedFlags.length) addIssue(node.card,'info','unused-flags','写入的标记暂未被条件读取：'+node.unusedFlags.join('、')+'。可能是留白伏笔。');
      node.issues = issues.filter(issue => issue.key === node.key);
    }
    return {cards,nodes,byKey:indexByKey,edges,issues,readers,writers,themes:[...new Set(cards.map(card=>card.thematic || '未分类'))]};
  }
  function compare(currentModel,baselineModel){
    const changes = new Map();
    if (!baselineModel) return changes;
    const allKeys = new Set([...currentModel.byKey.keys(),...baselineModel.byKey.keys()]);
    for (const nodeKey of allKeys){
      const after = currentModel.byKey.get(nodeKey), before = baselineModel.byKey.get(nodeKey);
      const details = [];
      if (after && before){
        for (const field of fields) if (after.card[field] !== before.card[field]) details.push({field,before:before.card[field],after:after.card[field]});
        for (const side of ['yes','no']){
          const previousTarget = baselineModel.nodes[before[side].target]?.key || '', nextTarget = currentModel.nodes[after[side].target]?.key || '';
          if (previousTarget !== nextTarget) details.push({field:'target_'+side,before:baselineModel.nodes[before[side].target]?.card.card || previousTarget,after:currentModel.nodes[after[side].target]?.card.card || nextTarget});
        }
      }
      const status = !before ? 'added' : !after ? 'removed' : details.length ? 'changed' : 'same';
      if (status !== 'same') changes.set(nodeKey,{key:nodeKey,status,before,after,fields:details});
    }
    return changes;
  }
  function downstream(model,nodeKey){
    const visited = new Set([nodeKey]), result = [], queue = [nodeKey];
    for (let position=0; position<queue.length; position++){
      for (const edge of model.byKey.get(queue[position])?.outgoing || []){
        if (visited.has(edge.to)) continue;
        visited.add(edge.to); result.push(edge.to); queue.push(edge.to);
      }
    }
    return result;
  }
  function conditionValue(name,state){
    if (name === 'money') return state.cash || 0;
    if (name === 'overall') return Math.round(Object.keys(resources).reduce((sum,resource) => sum+(state[resource] || 0),0)/4);
    if (systemValues.has(name)) return state[name] || 0;
    if (name.startsWith('nb_')) return state.flags?.[name] | 0;
    return state.flags?.[name] ? 1 : 0;
  }
  function evaluate(condition,state){
    const value = conditionValue(condition.name,state);
    if (condition.operator === '!') return !value;
    if (condition.operator === 'truthy' || !condition.valid) return !!value;
    return {'>':value>condition.value,'<':value<condition.value,'=':value===condition.value,'>=':value>=condition.value,'<=':value<=condition.value}[condition.operator];
  }
  function eligibility(model,state,forced=null){
    const pool = model.nodes.filter(node => weight(node.card)>0 && !(state.lock?.[node.card.card] && state.turn<state.lock[node.card.card]) && node.conditions.every(condition=>evaluate(condition,state)));
    const highest = Math.max(0,...pool.map(node=>weight(node.card)));
    const active = forced !== null ? [model.nodes[forced]].filter(Boolean) : pool.filter(node=>highest>=1000 ? weight(node.card)===highest : weight(node.card)>=highest*.5);
    const total = active.reduce((sum,node)=>sum+weight(node.card),0);
    return new Map(model.nodes.map(node => [node.key,{conditions:node.conditions.map(condition=>({raw:condition.raw,pass:evaluate(condition,state)})),eligible:active.includes(node),probability:active.includes(node) ? forced !== null ? 1 : weight(node.card)/total : 0}]));
  }
  function csv(cards){
    const escapeCell = value => /[;"\r\n]/.test(value) ? '"'+value.replace(/"/g,'""')+'"' : value;
    return '\uFEFF'+[fields.join(';'),...normalize(cards).map(card => fields.map(field => escapeCell(card[field])).join(';'))].join('\r\n');
  }
  const api = {fields,labels,resources,themes,normalize,key,tokens,number,weight,parseCSV,resolveJump,conditionParts,build,compare,downstream,evaluate,eligibility,csv};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.StoryModel = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
