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
  assert.doesNotMatch(current + engine, /phaseBanner|notebook|shelf|journal|这一路|怎么活|LAST_TURN|还剩/);
});

test('the first decision spends existing power, not a business prologue', () => {
  for (const side of ['no', 'yes']) {
    const state = game.create(1);
    const card = game.pick(state, data.cards, data.meta.cards);
    assert.equal(card.card, 'first_move');
    assert.equal(card.question, '发布会上，机器人当众叫你骗子。');
    assert.equal(card.override_no, '让它说完');
    assert.equal(card.override_yes, '拔电源');
    assert.ok(state.money >= 60 && state.team >= 60);
    assert.ok(game.choose(state, card, side, data.meta.cards));
    assert.ok(state.flags[side === 'no' ? 'mouth_open_run' : 'mouth_cut_run']);
    assert.equal(game.choose(state, card, side, data.meta.cards), false);
    assert.deepEqual(restore(state), state);
  }
});

test('every card is a short request with short decisions and immediate feedback', () => {
  const limits = {bearer:10, question:24, override_no:7, override_yes:7, answer_no:20, answer_yes:20};
  for (const card of data.cards) {
    for (const [field, limit] of Object.entries(limits)) {
      const text = card[field].replace(/\{\w+\}/g, '名字四字');
      assert.ok(Array.from(text).length <= limit, `${card.card}.${field}: ${text}`);
      assert.doesNotMatch(text, /[\r\n]/, `${card.card}.${field}`);
    }
    assert.doesNotMatch(card.question, /你想把|你想拿|你决定|你准备|而不是等|这一路|怎么活/);
  }
  assert.equal(byName.slow_warehouse.question, '网红把库存当古董，卖了十倍价。');
  assert.equal(byName.slow_warehouse.override_no, '改叫收藏款');
  assert.equal(byName.slow_warehouse.override_yes, '拆了卖零件');
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
    if ([17, 18, 79, 80, 1199].includes(decision)) {
      assert.deepEqual(game.restore(JSON.stringify(state), cards, data.meta.endings), state);
    }
  }
  assert.equal(state.turn, 1201);
  assert.equal(state.status, 'ready');
  assert.equal(state.history.length, game.HISTORY_LIMIT);
  assert.ok(JSON.stringify(state).length < 100000);
});

test('every resource receives its own warning before a fatal boundary', () => {
  const state = game.create(3);
  const card = {...byName.first_move, no_money:'-1000', no_team:'-1000', no_market:'1000', no_mind:'1000'};
  state.money = 1;
  state.team = 1;
  state.market = 99;
  state.mind = 99;
  assert.deepEqual(game.projected(state, card, 'no'), {money:1, team:1, market:99, mind:99});
  for (const danger of Object.values(game.DANGER)) {
    state.flags[danger.flag] = 1;
    if (danger.highFlag) state.flags[danger.highFlag] = 1;
  }
  assert.deepEqual(game.projected(state, card, 'no'), {money:0, team:0, market:100, mind:100});
  for (const [resource, danger] of Object.entries(game.DANGER)) {
    const isolated = {...game.create(4), [resource]:0};
    assert.equal(game.resourceEnding(isolated), danger.ending);
    if (danger.high) {
      isolated[resource] = 100;
      assert.equal(game.resourceEnding(isolated), danger.highEnding);
    }
  }
  assert.equal(game.resourceEnding({...game.create(4), money:100, team:100}), null);
});

test('retirement is optional on every exit card', () => {
  for (const card of data.cards.filter(card => card.thematic === 'exit')) {
    const keepPlaying = ['no', 'yes'].find(side => !/\bend_/.test(card[`${side}_custom`]));
    assert.ok(keepPlaying, card.card);
    const state = game.create(5);
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

test('opening choices have distinct conditional follow-ups', () => {
  for (const side of ['no', 'yes']) {
    const state = game.create(6);
    const card = game.pick(state, data.cards, data.meta.cards);
    game.choose(state, card, side, data.meta.cards);
    game.advance(state);
    assert.equal(state.turn, 2);
    assert.equal(game.condition(state, byName.mouth_fans.conditions), side === 'no');
    assert.equal(game.condition(state, byName.battery_live.conditions), side === 'yes');
    assert.equal(game.pick(state, data.cards, data.meta.cards).card, side === 'no' ? 'mouth_fans' : 'battery_live');
  }
});

test('the same bet produces both hit and miss without preview changing its odds', () => {
  const outcomes = new Set();
  for (let seed = 1; seed <= 20; seed++) {
    const state = game.create(seed);
    state.flags.bet_run = 1;
    state.flags.bet_meeting_run = 1;
    state.marked.bet_run = 3;
    state.turn = 8;
    const snapshot = JSON.stringify(state);
    game.projected(state, byName.bet_start, 'no');
    assert.equal(JSON.stringify(state), snapshot);
    const hits = game.condition(state, byName.bet_meeting_hit.conditions);
    const misses = game.condition(state, byName.bet_miss.conditions);
    assert.notEqual(hits, misses);
    outcomes.add(hits ? 'hit' : 'miss');
  }
  assert.deepEqual(outcomes, new Set(['hit', 'miss']));
});

test('departed partners do not resume their old role', () => {
  const state = game.create(7);
  state.turn = 100;
  state.flags.partner_left_run = 1;
  state.flags.partner_equal_run = 1;
  for (const card of data.cards) {
    if (card.thematic !== 'legacy' && /\{maker\}/.test(card.bearer + card.question + card.answer_yes + card.answer_no)) {
      assert.equal(game.condition(state, card.conditions), false, card.card);
    }
  }
});

test('all sixteen scandal and robot power paths reach their own aftermath', () => {
  const visitedClimaxes = new Set();
  for (const opening of ['no', 'yes']) {
    for (const scandal of ['no', 'yes']) {
      for (const board of ['no', 'yes']) {
        for (const response of ['no', 'yes']) {
          const state = game.create(17);
          const forced = {first_move:opening, mouth_fans:scandal, battery_live:scandal, board_robot:board, robot_nightshift:response, robot_union:response};
          const expected = board === 'no'
            ? (response === 'no' ? 'nightshift_fame' : 'reboot_crowdfund')
            : (response === 'no' ? 'union_bill' : 'robot_return');
          const seen = new Set();
          for (let step = 0; step < 40 && !state.flags.board_done_run; step++) {
            assert.notEqual(state.status, 'ended', `${opening}/${scandal}/${board}/${response}`);
            const card = game.pick(state, data.cards, data.meta.cards);
            seen.add(card.card);
            const safetyScore = side => {
              const projected = game.projected(state, card, side);
              return Math.min(projected.money, 70) + Math.min(projected.team, 70)
                - (projected.market - 50) ** 2 - (projected.mind - 50) ** 2
                - Math.max(0, 20 - projected.money) ** 3 - Math.max(0, 20 - projected.team) ** 3;
            };
            const side = forced[card.card] || (safetyScore('no') >= safetyScore('yes') ? 'no' : 'yes');
            game.choose(state, card, side, data.meta.cards);
            game.advance(state);
          }
          assert.ok(state.flags.board_done_run, `${opening}/${scandal}/${board}/${response}`);
          assert.ok(seen.has(expected), expected);
          assert.equal(seen.has('mouth_fans'), opening === 'no');
          assert.equal(seen.has('battery_live'), opening === 'yes');
          assert.equal(seen.has('robot_nightshift'), board === 'no');
          assert.equal(seen.has('robot_union'), board === 'yes');
          visitedClimaxes.add(expected);
        }
      }
    }
  }
  assert.equal(visitedClimaxes.size, 4);
});

test('rehiring the runaway prototype pays off instead of abandoning the promise', () => {
  const state = game.create(18);
  state.flags.bet_run = 1;
  state.flags.lucky_bet_run = 0;
  state.marked.bet_run = 5;
  state.turn = 9;
  assert.equal(game.condition(state, byName.bet_rehire.conditions), false);
  state.status = 'card';
  state.current = 'bet_miss';
  game.choose(state, byName.bet_miss, 'yes', data.meta.cards);
  game.advance(state);
  assert.ok(state.flags.bet_rehire_run);
  assert.equal(state.flags.bet_done_run, undefined);
  state.turn = 12;
  assert.equal(game.condition(state, byName.bet_rehire.conditions), true);
  state.status = 'card';
  state.current = 'bet_rehire';
  game.choose(state, byName.bet_rehire, 'no', data.meta.cards);
  assert.ok(state.flags.bet_done_run);
});

test('resolved fake orders clear debt and the new edition preserves the old save namespace', () => {
  for (const side of ['no', 'yes']) {
    const state = game.create(19);
    state.flags.hype_debt_keep = 1;
    state.current = 'fake_orders_audit';
    state.status = 'card';
    game.choose(state, byName.fake_orders_audit, side, data.meta.cards);
    assert.equal(state.flags.hype_debt_keep, undefined);
  }
  assert.equal(data.meta.credit, 'GPT 6 Astra');
  const engine = fs.readFileSync(path.join(__dirname, 'engine.js'), 'utf8');
  assert.match(engine, /founder-astra-v7-save/);
  assert.doesNotMatch(engine, /removeItem|localStorage\.clear/);
  const old = game.create(20);
  old.version = 6;
  assert.equal(restore(old), null);
});

test('corrupt nested feedback and invalid clocks cannot break the renderer', () => {
  const state = game.create(8);
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

test('resource endings carry relevant history into another already-established company', () => {
  const state = game.create(9);
  state.status = 'ended';
  state.ending = 'closed';
  state.turn = 240;
  state.flags.rival_keep = 1;
  state.flags.war_run = 1;
  state.rival = state.maker;
  const next = game.nextCompany(state, data.meta.endings);
  assert.equal(next.turn, 1);
  assert.equal(next.dynasty, 2);
  assert.equal(next.flags.war_run, undefined);
  assert.equal(next.flags.last_failed_keep, 1);
  assert.equal(next.flags.rival_keep, 1);
  assert.equal(next.archive[0].turns, 240);
  assert.notEqual(next.maker, next.rival);
  assert.deepEqual(restore(next), next);
});
