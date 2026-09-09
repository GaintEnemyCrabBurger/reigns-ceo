'use strict';

const Founder = (() => {
  const VERSION = 8;
  const HISTORY_LIMIT = 80;
  const RESOURCES = ['money', 'team', 'market', 'mind'];
  const MAKERS = ['韩涛', '顾言', '邱白', '林工', '郑然', '叶舟'];
  const COMPANIES = ['野火', '逆流', '锋芒', '破晓', '无限', '再起'];
  const LABELS = ['经营期', '风口', '退潮', '逆风'];
  const DANGER = {
    money: {low:18, flag:'risk_money_run', ending:'closed'},
    team: {low:20, flag:'risk_team_run', ending:'alone'},
    market: {low:15, high:92, flag:'risk_market_low_run', highFlag:'risk_market_high_run', ending:'forgotten', highEnding:'overload'},
    mind: {low:18, high:92, flag:'risk_mind_low_run', highFlag:'risk_mind_high_run', ending:'hollow', highEnding:'allin'},
  };
  const REVIVAL = {
    money: {prerequisite:'credit_good_run', used:'credit_rescue_run'},
    team: {prerequisite:'fair_pay_keep', used:'team_rescue_run'},
    market: {prerequisite:'customer_oath_run', used:'market_rescue_run'},
    mind: {prerequisite:'product_touch_run', used:'mind_rescue_run'},
  };
  const OVERFLOW = {
    market: {used:'market_overflow_run'},
    mind: {used:'mind_overflow_run'},
  };

  function random(state){
    state.rng = (state.rng + 0x6D2B79F5) >>> 0;
    let value = state.rng;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  }

  function create(seed, dynasty = 1, keep = {}, archive = [], recent = [], rival = ''){
    const state = {
      version:VERSION, seed:seed >>> 0, rng:seed >>> 0, dynasty, turn:1,
      money:68, team:62, market:48, mind:58,
      flags:{...keep}, marked:{}, lock:{}, history:[],
      archive:archive.slice(-8), recent:recent.slice(-54), rival,
      company:COMPANIES[(dynasty - 1) % COMPANIES.length],
      maker:MAKERS[(dynasty - 1) % MAKERS.length],
      status:'ready', current:null, feedback:null, ending:null,
    };
    if (state.maker === rival) state.maker = MAKERS[dynasty % MAKERS.length];
    state.windStart = 5 + Math.floor(random(state) * 3);
    state.windEnd = state.windStart + 4 + Math.floor(random(state) * 2);
    state.flags.lucky_bet_run = random(state) < 0.48 ? 1 : 0;
    return state;
  }

  function phase(state){
    const cycleTurn = (state.turn - 1) % 24 + 1;
    if (cycleTurn < state.windStart) return 1;
    if (cycleTurn < state.windEnd) return 2;
    if (cycleTurn < state.windEnd + 3) return 3;
    return 4;
  }

  function value(state, name){
    if (RESOURCES.includes(name) || name === 'turn' || name === 'dynasty') return state[name];
    if (name === 'phase') return phase(state);
    if (name.startsWith('age_')){
      const marked = state.marked[`${name.slice(4)}_run`];
      return marked === undefined ? -1 : state.turn - marked;
    }
    return state.flags[name] || 0;
  }

  function condition(state, expression){
    if (!expression) return true;
    return expression.split(/\s+and\s+/).every(token => {
      const term = token.trim();
      const match = term.match(/^([A-Za-z_]\w*)\s*(>=|<=|>|<|=)\s*(-?\d+)$/);
      if (match){
        const actual = value(state, match[1]);
        const expected = Number(match[3]);
        switch (match[2]){
          case '>': return actual > expected;
          case '<': return actual < expected;
          case '>=': return actual >= expected;
          case '<=': return actual <= expected;
          default: return actual === expected;
        }
      }
      if (!/^!?[A-Za-z_]\w*$/.test(term)) throw new Error(`Unknown condition: ${term}`);
      return term.startsWith('!') ? !value(state, term.slice(1)) : Boolean(value(state, term));
    });
  }

  function render(state, text){
    const replacements = {company:state.company, maker:state.maker, rival:state.rival || '韩涛'};
    return String(text || '').replace(/\{(\w+)\}/g, (match, key) => replacements[key] || match);
  }

  function pick(state, cards, metadata){
    if (state.status === 'card') return cards.find(card => card.card === state.current);
    if (state.status !== 'ready') return null;
    const available = card => !state.lock[card.card] || (typeof state.lock[card.card] === 'number' && state.turn >= state.lock[card.card]);
    let pool = cards.filter(card => available(card) && condition(state, card.conditions));
    if (!pool.length) throw new Error(`No eligible card at turn ${state.turn}`);
    const highest = Math.max(...pool.map(card => Number(card.weight)));
    pool = pool.filter(card => highest >= 1000 ? Number(card.weight) === highest : Number(card.weight) >= highest * 0.5);
    const last = state.history.at(-1);
    const weighted = pool.map(card => {
      let weight = Number(card.weight);
      if (state.recent.includes(card.card)) weight *= 0.35;
      if (state.history.slice(-6).some(entry => entry.card === card.card)) weight *= 0.2;
      if (highest < 1000 && last && metadata[card.card]?.kind === metadata[last.card]?.kind) weight *= 0.6;
      return {card, weight};
    });
    let ticket = random(state) * weighted.reduce((sum, item) => sum + item.weight, 0);
    const selected = weighted.find(item => (ticket -= item.weight) <= 0)?.card || weighted.at(-1).card;
    state.current = selected.card;
    state.status = 'card';
    return selected;
  }

  function effect(state, card, side){
    const currentPhase = phase(state);
    const operating = state.turn > 3 && !['pressure', 'exit', 'breather', 'legacy'].includes(card.thematic);
    const upkeep = operating ? {money:currentPhase === 4 ? -4 : currentPhase === 2 ? -2 : -3, team:-1, market:currentPhase === 4 ? -2 : -1, mind:0} : {};
    const changes = {};
    for (const resource of RESOURCES){
      const raw = Number(card[`${side}_${resource}`]) || 0;
      let multiplier = 1;
      if (!['pressure', 'exit', 'legacy'].includes(card.thematic)){
        if (currentPhase === 2 && resource === 'money') multiplier = raw > 0 ? 1.4 : 0.8;
        if (resource === 'market' && raw > 0) multiplier = currentPhase === 2 ? 0.75 : 0.65;
        if (currentPhase === 4 && resource === 'money') multiplier = raw > 0 ? 0.85 : 1.15;
      }
      changes[resource] = Math.sign(raw) * Math.round(Math.abs(raw) * multiplier) + (upkeep[resource] || 0);
    }
    return changes;
  }

  function projected(state, card, side){
    const changes = effect(state, card, side);
    return Object.fromEntries(RESOURCES.map(resource => {
      const danger = DANGER[resource];
      let next = Math.max(0, Math.min(100, state[resource] + changes[resource]));
      if (next === 0 && !state.flags[danger.flag] && !hasRevivalPromise(state, resource)) next = 1;
      if (danger.high && next === 100 && !state.flags[danger.highFlag]) next = 99;
      return [resource, next];
    }));
  }

  function canRevive(state, resource){
    const revival = REVIVAL[resource];
    return Boolean(revival && state[resource] === 0 && state.flags[revival.prerequisite] && !state.flags[revival.used]);
  }

  function hasRevivalPromise(state, resource){
    const revival = REVIVAL[resource];
    return Boolean(revival && state.flags[revival.prerequisite] && !state.flags[revival.used]);
  }

  function canHandleOverflow(state, resource){
    const overflow = OVERFLOW[resource];
    return Boolean(overflow && state[resource] >= 100 && !state.flags[overflow.used]);
  }

  function resourceEnding(state){
    for (const resource of RESOURCES){
      if (state[resource] <= 0 && !canRevive(state, resource)) return DANGER[resource].ending;
      if (DANGER[resource].high && state[resource] >= 100 && !canHandleOverflow(state, resource)) return DANGER[resource].highEnding;
    }
    return null;
  }

  function applyFlags(state, expression){
    let ending = null;
    for (const token of (expression || '').split(/\s+and\s+/)){
      if (!token) continue;
      if (token.startsWith('end_')) ending = token.slice(4);
      else if (token.startsWith('!')) delete state.flags[token.slice(1)];
      else {
        const name = token.replace(/\++$/, '');
        if (!Object.hasOwn(state.marked, name)) state.marked[name] = state.turn;
        state.flags[name] = token.endsWith('+') ? (state.flags[name] || 0) + 1 : 1;
      }
    }
    return ending;
  }

  function choose(state, card, side, metadata){
    if (state.status !== 'card' || state.current !== card.card || !['no', 'yes'].includes(side)) return false;
    const before = Object.fromEntries(RESOURCES.map(resource => [resource, state[resource]]));
    const after = projected(state, card, side);
    Object.assign(state, after);
    const scriptedEnding = applyFlags(state, card[`${side}_custom`]);
    if (state.flags.partner_left_run) state.rival = state.maker;
    const entry = {
      turn:state.turn, phase:phase(state), card:card.card, side,
      bearer:render(state, card.bearer), question:render(state, card.question),
      option:render(state, card[`override_${side}`]), reply:render(state, card[`answer_${side}`]), before, after,
    };
    state.history.push(entry);
    state.history = state.history.slice(-HISTORY_LIMIT);
    state.lock[card.card] = card.lockturn === 'del' ? true : state.turn + Number(card.lockturn);
    state.feedback = {...entry, ending:resourceEnding(state) || scriptedEnding};
    state.status = 'feedback';
    return true;
  }

  function advance(state){
    if (state.status !== 'feedback') return false;
    if (state.feedback.ending){
      state.ending = state.feedback.ending;
      state.status = 'ended';
    } else {
      state.turn++;
      state.current = null;
      state.status = 'ready';
    }
    return true;
  }

  function nextCompany(state, endings){
    if (state.status !== 'ended') throw new Error('The current company has not ended');
    const keep = Object.fromEntries(Object.entries(state.flags).filter(([name, amount]) => name.endsWith('_keep') && !name.startsWith('last_') && amount));
    if (endings[state.ending]?.flag) keep[endings[state.ending].flag] = 1;
    const archive = [...state.archive, {company:state.company, maker:state.maker, dynasty:state.dynasty, ending:state.ending, turns:state.turn}];
    return create(Math.floor(random(state) * 4294967296), state.dynasty + 1, keep, archive,
      [...state.recent, ...state.history.map(entry => entry.card)], state.rival);
  }

  function restore(serialized, cards, endings){
    try {
      const state = JSON.parse(serialized);
      const names = new Set(cards.map(card => card.card));
      const plain = object => object !== null && typeof object === 'object' && !Array.isArray(object);
      const integer = (amount, minimum = 0, maximum = Number.MAX_SAFE_INTEGER) => Number.isSafeInteger(amount) && amount >= minimum && amount <= maximum;
      const resources = object => plain(object) && RESOURCES.every(resource => integer(object[resource], 0, 100));
      const entry = item => plain(item) && names.has(item.card) && integer(item.turn, 1) && integer(item.phase, 1, 4)
        && ['no', 'yes'].includes(item.side) && ['bearer', 'question', 'option', 'reply'].every(field => typeof item[field] === 'string')
        && resources(item.before) && resources(item.after);
      if (!plain(state) || state.version !== VERSION || !resources(state)) return null;
      if (!integer(state.turn, 1) || !integer(state.dynasty, 1) || !integer(state.seed, 0, 4294967295) || !integer(state.rng, 0, 4294967295)) return null;
      if (![5, 6, 7].includes(state.windStart) || ![4, 5].includes(state.windEnd - state.windStart)) return null;
      if (!MAKERS.includes(state.maker) || !COMPANIES.includes(state.company) || (state.rival !== '' && !MAKERS.includes(state.rival))) return null;
      if (['flags', 'marked', 'lock'].some(key => !plain(state[key]))) return null;
      if (Object.entries(state.flags).some(([name, amount]) => !/^[A-Za-z_]\w*_(run|keep)$/.test(name) || !integer(amount))) return null;
      if (Object.values(state.marked).some(turn => !integer(turn, 1, state.turn))) return null;
      if (Object.entries(state.lock).some(([name, locked]) => !names.has(name) || (locked !== true && !integer(locked, 1)))) return null;
      if (['history', 'archive', 'recent'].some(key => !Array.isArray(state[key]))) return null;
      if (!['ready', 'card', 'feedback', 'ended'].includes(state.status)) return null;
      const decided = state.status === 'feedback' || state.status === 'ended';
      const completed = state.turn - (decided ? 0 : 1);
      if (state.history.length !== Math.min(HISTORY_LIMIT, completed) || state.archive.length > 8 || state.recent.length > 54) return null;
      if (state.history.some((item, index) => !entry(item) || item.turn !== completed - state.history.length + index + 1)) return null;
      if (state.status === 'ready' ? state.current !== null : !names.has(state.current)) return null;
      if (state.status === 'card'){
        const locked = state.lock[state.current];
        if (locked === true || (typeof locked === 'number' && state.turn < locked)) return null;
        if (!condition(state, cards.find(card => card.card === state.current).conditions)) return null;
      }
      if (state.status === 'ended' ? !Object.hasOwn(endings, state.ending) : state.ending !== null) return null;
      const last = state.history.at(-1);
      if (last){
        if (!entry(state.feedback) || ![null, ...Object.keys(endings)].includes(state.feedback.ending)) return null;
        if (Object.keys(last).some(key => JSON.stringify(state.feedback[key]) !== JSON.stringify(last[key]))) return null;
        if (RESOURCES.some(resource => state[resource] !== last.after[resource])) return null;
        if (decided && state.current !== state.feedback.card) return null;
        if (state.status === 'ended' && state.ending !== state.feedback.ending) return null;
        if (!decided && state.feedback.ending) return null;
      } else if (state.feedback !== null) return null;
      if (state.history.some(item => !state.lock[item.card]) || state.recent.some(name => !names.has(name))) return null;
      if (state.archive.some(item => !plain(item) || !COMPANIES.includes(item.company) || !MAKERS.includes(item.maker)
        || !integer(item.dynasty, 1, state.dynasty - 1) || !integer(item.turns, 1) || !Object.hasOwn(endings, item.ending))) return null;
      return state;
    } catch { return null; }
  }

    return {VERSION, HISTORY_LIMIT, RESOURCES, LABELS, DANGER, REVIVAL, OVERFLOW, create, random, phase, value,
    condition, render, pick, effect, projected, resourceEnding, choose, advance, nextCompany, restore};
})();

if (typeof module !== 'undefined' && module.exports) module.exports = Founder;
