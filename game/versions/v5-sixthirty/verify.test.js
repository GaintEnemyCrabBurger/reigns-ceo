'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const game = require('./logic.js');
const data = require('./deck.json');
const byName = Object.fromEntries(data.cards.map(card => [card.card, card]));
const restore = state => game.restore(JSON.stringify(state), data.cards, data.meta.endings);

test('original UI, icons and complete swipe handler are retained', () => {
  const original = fs.readFileSync(path.join(__dirname, '../../index.html'), 'utf8').replace(/\r\n/g, '\n');
  const current = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8').replace(/\r\n/g, '\n');
  assert.equal(current.match(/<style>([\s\S]*?)<\/style>/)[1], original.match(/<style>([\s\S]*?)<\/style>/)[1]);
  assert.equal(current.split('<body>')[1].split('<script>')[0], original.split('<body>')[1].split('<script>')[0]);
  const originalEngine = fs.readFileSync(path.join(__dirname, '../../engine.js'), 'utf8').replace(/\r\n/g, '\n');
  const engine = fs.readFileSync(path.join(__dirname, 'engine.js'), 'utf8');
  for (const [start, end] of [['const SVG =', 'const RES ='], ['function bindDrag(el){', 'function choose(yes)']]) {
    assert.equal(engine.split(start)[1].split(end)[0], originalEngine.split(start)[1].split(end)[0]);
  }
  assert.match(engine, /}, 1280\);/);
  assert.doesNotMatch(current + engine, /phaseBanner|notebook|shelf|journal|这一路|怎么活|LAST_TURN|还剩|机器人当CEO/);
});

test('the opening starts with an established company and an immediate power play', () => {
  const state = game.create(1);
  const card = game.pick(state, data.cards, data.meta.cards);
  assert.equal(card.card, 'first_move');
  assert.equal(card.question, '大厂开价三亿，今晚要答复。');
  assert.equal(card.override_no, '签框架');
  assert.equal(card.override_yes, '拒绝，扩产');
  assert.ok(state.money >= 60 && state.team >= 60);
  assert.ok(game.choose(state, card, 'no', data.meta.cards));
  assert.equal(game.choose(state, card, 'no', data.meta.cards), false);
  assert.ok(state.flags.deal_run);
  assert.ok(state.flags.founder_run);
  assert.deepEqual(restore(state), state);
});

test('all cards stay within the Reigns-style reading budget', () => {
  const limits = {bearer:10, question:24, override_no:7, override_yes:7, answer_no:20, answer_yes:20};
  for (const card of data.cards) {
    for (const [field, limit] of Object.entries(limits)) {
      const text = card[field].replace(/\{\w+\}/g, '名字四字');
      assert.ok(Array.from(text).length <= limit, card.card + '.' + field + ': ' + text);
      assert.doesNotMatch(text, /[\r\n]/, card.card + '.' + field);
    }
    assert.doesNotMatch(card.question, /你想把|你想拿|你决定|你准备|而不是等|这一路|怎么活/);
  }
  assert.equal(byName.old_stock.question, '旧款堆满仓库，网红却在问价。');
  assert.equal(byName.old_stock.override_no, '改名收藏款');
  assert.equal(byName.old_stock.override_yes, '拆了卖零件');
});

test('turn 18 does not end anything and long saves remain bounded', () => {
  const cards = ['first', 'second'].map(name => ({...byName.first_move, card:name, thematic:'breather', conditions:'', lockturn:'2', weight:'100', no_money:'', no_team:'', no_market:'', no_mind:'', no_custom:''}));
  const metadata = Object.fromEntries(cards.map(card => [card.card, {kind:'expression'}]));
  const state = game.create(2);
  for (let decision = 0; decision < 1200; decision++) {
    const card = game.pick(state, cards, metadata);
    assert.ok(game.choose(state, card, 'no', metadata));
    assert.equal(state.feedback.ending, null);
    assert.ok(game.advance(state));
  }
  assert.equal(state.turn, 1201);
  assert.equal(state.status, 'ready');
  assert.equal(state.history.length, game.HISTORY_LIMIT);
  assert.ok(JSON.stringify(state).length < 100000);
});

test('opening choices unlock separate commercial follow-ups', () => {
  for (const side of ['no', 'yes']) {
    const state = game.create(3);
    const opening = game.pick(state, data.cards, data.meta.cards);
    game.choose(state, opening, side, data.meta.cards);
    game.advance(state);
    state.turn = 3;
    assert.equal(game.condition(state, byName.deal_follow.conditions), side === 'no');
    assert.equal(game.condition(state, byName.capacity_follow.conditions), side === 'yes');
  }
});

test('the price war changes the next card and leaves the premium path closed', () => {
  const state = game.create(4);
  state.turn = 6;
  state.flags.founder_run = 1;
  state.marked.founder_run = 1;
  state.current = 'rival_price';
  state.status = 'card';
  game.choose(state, byName.rival_price, 'no', data.meta.cards);
  assert.ok(state.flags.price_war_run);
  state.turn = 9;
  assert.equal(game.condition(state, byName.price_counter.conditions), true);
  assert.equal(game.condition(state, byName.premium_counter.conditions), false);
});

test('a past promise enables a real zero-cash revival', () => {
  const state = game.create(5);
  state.money = 1;
  state.flags.credit_good_run = 1;
  state.current = 'price_raise';
  state.status = 'card';
  state.turn = 10;
  const drain = {...byName.price_raise, no_money:'-10', no_team:'', no_market:'', no_mind:''};
  assert.equal(game.projected(state, drain, 'no').money, 0);
  assert.ok(game.choose(state, drain, 'no', data.meta.cards));
  assert.equal(state.money, 0);
  assert.equal(game.resourceEnding(state), null);
  assert.equal(game.condition(state, byName.bridge_credit.conditions), true);
  state.current = 'bridge_credit';
  state.status = 'card';
  assert.ok(game.choose(state, byName.bridge_credit, 'no', data.meta.cards));
  assert.equal(state.money, 28);
  assert.ok(state.flags.credit_rescue_run);
  const dead = game.create(6);
  dead.money = 0;
  dead.flags.credit_good_run = 1;
  dead.flags.credit_rescue_run = 1;
  assert.equal(game.resourceEnding(dead), 'closed');
});

test('team, market and mind can each return once from zero with a prior promise', () => {
  const cases = [
    ['team', 'fair_pay_keep', 'team_rescue_run', 'bridge_team', 'alone'],
    ['market', 'customer_oath_run', 'market_rescue_run', 'bridge_market', 'forgotten'],
    ['mind', 'product_touch_run', 'mind_rescue_run', 'bridge_mind', 'hollow'],
  ];
  for (const [resource, prerequisite, used, cardName, ending] of cases) {
    const state = game.create(7);
    state[resource] = 0;
    state.flags[prerequisite] = 1;
    assert.equal(game.resourceEnding(state), null);
    assert.equal(game.condition(state, byName[cardName].conditions), true);
    state.current = cardName;
    state.status = 'card';
    game.choose(state, byName[cardName], 'no', data.meta.cards);
    assert.ok(state[resource] > 0);
    assert.ok(state.flags[used]);
    const dead = game.create(8);
    dead[resource] = 0;
    dead.flags[prerequisite] = 1;
    dead.flags[used] = 1;
    assert.equal(game.resourceEnding(dead), ending);
  }
});

test('a market or mind peak gets one visible overflow decision before ending', () => {
  for (const [resource, cardName, used, ending] of [
    ['market', 'market_overflow', 'market_overflow_run', 'overload'],
    ['mind', 'mind_overflow', 'mind_overflow_run', 'allin'],
  ]) {
    const state = game.create(13);
    state[resource] = 100;
    assert.equal(game.resourceEnding(state), null);
    assert.equal(game.condition(state, byName[cardName].conditions), true);
    state.current = cardName;
    state.status = 'card';
    game.choose(state, byName[cardName], 'no', data.meta.cards);
    assert.ok(state.flags[used]);
    const dead = game.create(14);
    dead[resource] = 100;
    dead.flags[used] = 1;
    assert.equal(game.resourceEnding(dead), ending);
  }
});

test('a risky product bet can hit or miss without preview changing luck', () => {
  const outcomes = new Set();
  for (let seed = 1; seed <= 20; seed++) {
    const state = game.create(seed);
    state.flags.bet_run = 1;
    state.flags.bet_cheap_run = 1;
    state.marked.bet_run = 3;
    state.turn = 8;
    const snapshot = JSON.stringify(state);
    game.projected(state, byName.product_bet, 'no');
    assert.equal(JSON.stringify(state), snapshot);
    const hits = game.condition(state, byName.bet_cheap_hit.conditions);
    const misses = game.condition(state, byName.bet_miss.conditions);
    assert.notEqual(hits, misses);
    outcomes.add(hits ? 'hit' : 'miss');
  }
  assert.deepEqual(outcomes, new Set(['hit', 'miss']));
});

test('departed partners do not resume their old role', () => {
  const state = game.create(9);
  state.turn = 100;
  state.flags.partner_left_run = 1;
  state.flags.partner_equal_run = 1;
  for (const card of data.cards) {
    if (card.thematic !== 'legacy' && /\{maker\}/.test(card.bearer + card.question + card.answer_yes + card.answer_no)) {
      assert.equal(game.condition(state, card.conditions), false, card.card);
    }
  }
});

test('voluntary exits always provide a continuing option', () => {
  for (const card of data.cards.filter(card => card.thematic === 'exit')) {
    const keepPlaying = ['no', 'yes'].find(side => !/\bend_/.test(card[side + '_custom']));
    assert.ok(keepPlaying, card.card);
    const state = game.create(10);
    state.turn = 200;
    state.current = card.card;
    state.status = 'card';
    assert.ok(game.choose(state, card, keepPlaying, data.meta.cards));
    assert.equal(state.feedback.ending, null);
    game.advance(state);
    assert.equal(state.status, 'ready');
    assert.equal(state.turn, 201);
  }
});

test('corrupt nested feedback and invalid clocks cannot break the renderer', () => {
  const state = game.create(11);
  const card = game.pick(state, data.cards, data.meta.cards);
  game.choose(state, card, 'yes', data.meta.cards);
  const mutations = [
    corrupted => { corrupted.feedback.before = null; },
    corrupted => { corrupted.feedback.after.money = '68'; },
    corrupted => { corrupted.history[0].option = null; },
    corrupted => { corrupted.turn = -1; },
    corrupted => { corrupted.turn = 1.5; },
    corrupted => { corrupted.history = []; },
    corrupted => { corrupted.feedback.ending = 'unknown'; },
    corrupted => { corrupted.archive.push({ending:'sold', turns:4}); },
  ];
  for (const mutate of mutations) {
    const corrupted = JSON.parse(JSON.stringify(state));
    mutate(corrupted);
    assert.equal(restore(corrupted), null);
  }
  assert.equal(game.restore('{broken', data.cards, data.meta.endings), null);
  assert.deepEqual(restore(state), state);
  game.advance(state);
  state.status = 'card';
  state.current = card.card;
  assert.equal(restore(state), null);
});

test('relevant promises carry into the next established company', () => {
  const state = game.create(12);
  state.status = 'ended';
  state.ending = 'closed';
  state.turn = 240;
  state.flags.rival_keep = 1;
  state.flags.credit_good_keep = 1;
  state.rival = state.maker;
  const next = game.nextCompany(state, data.meta.endings);
  assert.equal(next.turn, 1);
  assert.equal(next.dynasty, 2);
  assert.equal(next.flags.credit_good_keep, 1);
  assert.equal(next.flags.last_failed_keep, 1);
  assert.equal(next.archive[0].turns, 240);
  assert.notEqual(next.maker, next.rival);
  assert.deepEqual(restore(next), next);
});
