'use strict';

const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const game = require('./logic.js');
const data = require('./deck.json');
const argumentsList = process.argv.slice(2);
const argument = (name, fallback) => {
  const position = argumentsList.indexOf(name);
  return position < 0 ? fallback : argumentsList[position + 1];
};
const mode = argumentsList.includes('--smart') ? 'smart' : argument('--policy', 'random');
const runs = Number(argument('--runs', 200));
const generations = Number(argument('--generations', 3));
const horizon = Number(argument('--max-turns', 300));
const traceSeed = argument('--trace', null);
assert.ok(['smart', 'random', 'left', 'right'].includes(mode), 'Unknown policy');
for (const amount of [runs, generations, horizon]) assert.ok(Number.isSafeInteger(amount) && amount > 0, 'Counts must be positive integers');

function score(state, card, side){
  if (/\bend_/.test(card[`${side}_custom`])) return -1e9;
  const projected = game.projected(state, card, side);
  let result = 0;
  for (const resource of game.RESOURCES){
    const amount = projected[resource];
    if (amount <= 0 || (['market', 'mind'].includes(resource) && amount >= 100)) result -= 100000;
    if (resource === 'money' || resource === 'team'){
      result += Math.min(amount, 70) * 1.1;
      result -= Math.max(0, 30 - amount) ** 2;
    } else {
      result -= (amount - 50) ** 2 * 0.07;
      result -= Math.max(0, 24 - amount) ** 2;
      result -= Math.max(0, amount - 76) ** 2;
    }
  }
  return result;
}

function play(initial, policy, choiceSeed = 1){
  let chooser = choiceSeed >>> 0;
  const nextChoice = () => {
    chooser = (Math.imul(1664525, chooser) + 1013904223) >>> 0;
    return chooser / 4294967296;
  };
  const state = initial;
  const events = [];
  const once = new Set();
  const lastSeen = {};
  for (let decision = 0; decision < horizon && state.status !== 'ended'; decision++){
    const card = game.pick(state, data.cards, data.meta.cards);
    assert.ok(card, `Missing card at seed=${state.seed} turn=${state.turn}`);
    if (card.lockturn === 'del'){
      assert.ok(!once.has(card.card), `One-shot repeated: ${card.card}`);
      once.add(card.card);
    } else if (lastSeen[card.card]){
      assert.ok(state.turn - lastSeen[card.card] >= Number(card.lockturn), `Cooldown ignored: ${card.card}`);
    }
    lastSeen[card.card] = state.turn;
    let side;
    if (policy === 'smart'){
      const difference = score(state, card, 'yes') - score(state, card, 'no');
      side = difference === 0 ? (nextChoice() > 0.5 ? 'yes' : 'no') : difference > 0 ? 'yes' : 'no';
    } else if (policy === 'left') side = 'no';
    else if (policy === 'right') side = 'yes';
    else side = nextChoice() > 0.5 ? 'yes' : 'no';
    const snapshot = JSON.stringify(state);
    game.effect(state, card, side);
    game.projected(state, card, side);
    assert.equal(JSON.stringify(state), snapshot, 'Preview mutated state');
    if (decision < 3 || decision % 25 === 0) assert.deepEqual(game.restore(snapshot, data.cards, data.meta.endings), state, 'Card save drift');
    assert.ok(game.choose(state, card, side, data.meta.cards));
    assert.equal(game.choose(state, card, side, data.meta.cards), false, 'Duplicate decision');
    if (decision < 3 || decision % 25 === 0) assert.deepEqual(game.restore(JSON.stringify(state), data.cards, data.meta.endings), state, 'Feedback save drift');
    events.push(state.feedback);
    assert.ok(game.advance(state));
    assert.equal(game.advance(state), false, 'Duplicate advance');
  }
  assert.deepEqual(game.restore(JSON.stringify(state), data.cards, data.meta.endings), state, 'Final snapshot drift');
  if (state.status === 'ended') assert.ok(data.meta.endings[state.ending]);
  else assert.equal(events.length, horizon);
  assert.ok(state.history.length <= game.HISTORY_LIMIT);
  return {state, events};
}

if (traceSeed !== null){
  const result = play(game.create(Number(traceSeed)), mode, Number(traceSeed) * 17 + 11);
  for (const event of result.events){
    console.log(`\n${event.turn}. [${game.LABELS[event.phase - 1]}] ${event.bearer}\n${event.question}`);
    console.log(`${event.side === 'no' ? '←' : '→'} ${event.option}\n${event.reply}\n${JSON.stringify(event.after)}`);
  }
  console.log(result.state.ending ? data.meta.endings[result.state.ending].title : `Still operating after ${horizon} decisions; simulation horizon only.`);
} else {
  const coverage = new Set();
  const endings = {};
  const lengths = [];
  const counts = {total:0, alive:0, passed18:0, expressions:0, crises:0};
  for (let seed = 1; seed <= runs; seed++){
    let initial = game.create(seed);
    for (let generation = 0; generation < generations; generation++){
      const snapshot = JSON.parse(JSON.stringify(initial));
      const choiceSeed = seed * 17 + generation * 31 + 11;
      const result = play(initial, mode, choiceSeed);
      if (seed <= 2) assert.deepEqual(play(snapshot, mode, choiceSeed), result, 'Seeded replay drift');
      counts.total++;
      lengths.push(result.events.length);
      if (result.events.length > 18) counts.passed18++;
      for (const event of result.events){
        coverage.add(event.card);
        const kind = data.meta.cards[event.card].kind;
        if (kind === 'expression') counts.expressions++;
        if (kind === 'crisis') counts.crises++;
      }
      if (!result.state.ending){ counts.alive++; break; }
      endings[result.state.ending] = (endings[result.state.ending] || 0) + 1;
      initial = game.nextCompany(result.state, data.meta.endings);
    }
  }
  lengths.sort((first, second) => first - second);
  const report = {
    policy:mode, runs:counts.total, simulationHorizon:horizon,
    stillOperatingAtHorizon:counts.alive, horizonSurvivalRate:+(counts.alive / counts.total * 100).toFixed(2),
    beyond18Decisions:counts.passed18, medianDecisions:lengths[Math.floor(lengths.length / 2)],
    minimumDecisions:lengths[0], maximumDecisions:lengths.at(-1),
    meanExpressionChoices:+(counts.expressions / counts.total).toFixed(2), meanCrisisChoices:+(counts.crises / counts.total).toFixed(2),
    cardsSeen:coverage.size, cardsTotal:data.cards.length, endings,
    unseen:data.cards.filter(card => !coverage.has(card.card)).map(card => card.card),
  };
  console.log(JSON.stringify(report, null, 2));
  if (argumentsList.includes('--report')) fs.writeFileSync(path.join(__dirname, `simulation-${mode}.json`), JSON.stringify(report, null, 2) + '\n');
}
