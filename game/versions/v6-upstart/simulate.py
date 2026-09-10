"""Deterministic simulator for the independent 《上位》 deck."""
import argparse
import collections
import csv
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESOURCES = ("cash", "team", "market", "capital")


def load_cards():
    with (HERE / "cards.csv").open(encoding="utf-8-sig", newline="") as handle:
        cards = list(csv.DictReader(handle, delimiter=";"))
    from story import CARDS
    if cards != CARDS:
        raise RuntimeError("cards.csv 与 story.py 不同步；请先运行 story.py")
    return cards


CARDS = load_cards()
BY_NAME = {card["card"]: index for index, card in enumerate(CARDS)}
ENDING_KEYS = {
    card["card"].removeprefix("ending_")
    for card in CARDS
    if card["thematic"] == "endings"
}


def explicit_ending(value):
    for token in re.split(r"\s+and\s+", value or ""):
        token = token.strip()
        match = re.fullmatch(r">_ending_([A-Za-z_]\w*)", token)
        if not match:
            match = re.fullmatch(r"end_([A-Za-z_]\w*)", token)
        if match and match.group(1) in ENDING_KEYS:
            return match.group(1)
    return None


class Game:
    def __init__(self, seed=None):
        self.values = dict(cash=46, team=48, market=44, capital=42)
        self.flags = {"risk": 0, "evidence": 0}
        self.lock = {}
        self.seen = collections.Counter()
        self.turn = 0
        self.forced = None
        self.random = random.Random(seed)
        self.history = []
        self.recycle_guard = False
        self.decisions = 0

    def value(self, name):
        if name in ("cash", "money"):
            return self.values["cash"]
        if name in RESOURCES:
            return self.values[name]
        if name == "turn":
            return self.turn
        if name in ("risk", "evidence") or name.startswith("nb_"):
            return max(0, int(self.flags.get(name, 0)))
        value = self.flags.get(name, 0)
        return value if isinstance(value, int) else int(bool(value))

    def test_one(self, token):
        token = token.strip()
        match = re.fullmatch(r"([A-Za-z_]\w*)\s*(>=|<=|>|<|=)\s*(-?\d+)", token)
        if match:
            left, operator, right = self.value(match.group(1)), match.group(2), int(match.group(3))
            return {
                ">": left > right,
                "<": left < right,
                "=": left == right,
                ">=": left >= right,
                "<=": left <= right,
            }[operator]
        if token.startswith("!"):
            return not self.value(token[1:])
        return bool(self.value(token))

    def eligible(self, card):
        condition = card["conditions"].strip()
        return not condition or all(self.test_one(token) for token in re.split(r"\s+and\s+", condition))

    def resource_ending(self):
        for resource in RESOURCES:
            if self.values[resource] <= 0:
                return f"{resource}_zero"
            if self.values[resource] >= 100:
                return f"{resource}_max"
        return None

    def pick(self):
        if self.forced is not None:
            selected, self.forced = self.forced, None
            return selected
        pool = []
        best = 0
        for index, card in enumerate(CARDS):
            if not card["weight"]:
                continue
            if card["lockturn"].strip() == "del" and self.seen[card["card"]]:
                continue
            if self.lock.get(card["card"], 0) > self.turn:
                continue
            if not self.eligible(card):
                continue
            weight = int(card["weight"])
            best = max(best, weight)
            pool.append((index, weight))
        if not pool:
            if not self.recycle_guard:
                self.recycle_guard = True
                self.lock = {}
                for card in CARDS:
                    if card["thematic"] == "open" and card["lockturn"].strip() != "del":
                        self.seen.pop(card["card"], None)
                return self.pick()
            return None
        self.recycle_guard = False
        top = [(index, weight) for index, weight in pool if weight >= best * 0.5]
        choices = [(index, weight) for index, weight in pool if weight == best] if best >= 1000 else top
        needle = self.random.random() * sum(weight for _, weight in choices)
        for index, weight in choices:
            needle -= weight
            if needle <= 0:
                return index
        return choices[-1][0]

    def apply_flags(self, value, card_index):
        for raw in re.split(r"\s+and\s+", value or ""):
            token = raw.strip()
            if not token:
                continue
            if token.startswith(">"):
                arrows = len(token) - len(token.lstrip(">"))
                rest = token[arrows:].strip()
                if rest.startswith("_"):
                    self.forced = BY_NAME[rest[1:]]
                elif rest in BY_NAME:
                    self.forced = BY_NAME[rest]
                elif rest.isdigit():
                    self.forced = card_index + int(rest)
                else:
                    self.forced = card_index + arrows
                continue
            if token.endswith(("+", "-")):
                base = token[:-1].rstrip("+-")
                direction = 1 if token.endswith("+") else -1
                self.flags[base] = max(0, int(self.flags.get(base, 0)) + direction)
                continue
            if token.startswith("!"):
                self.flags.pop(token[1:], None)
                continue
            if token.startswith("end_"):
                continue
            self.flags[token] = 1

    def play(self, policy, max_turns=160):
        while self.turn < max_turns:
            self.turn += 1
            index = self.pick()
            if index is None:
                return self.resource_ending() or "no_cards"
            card = CARDS[index]
            if card["thematic"] == "endings":
                return card["card"].removeprefix("ending_")
            side = policy(self, card)
            for resource in RESOURCES:
                amount = int(card[f"{side}_{resource}"] or 0)
                self.values[resource] = max(0, min(100, self.values[resource] + amount))
            lockturn = card["lockturn"].strip()
            if lockturn == "del":
                self.lock[card["card"]] = 10**9
            elif lockturn:
                self.lock[card["card"]] = self.turn + int(lockturn)
            self.seen[card["card"]] += 1
            self.apply_flags(card[f"{side}_custom"], index)
            self.decisions += 1
            self.history.append((self.turn, card["card"], side, dict(self.values), dict(self.flags)))
            explicit = explicit_ending(card[f"{side}_custom"])
            ending = self.resource_ending() or explicit
            if ending:
                return ending
        return "timeout"


def score_option(game, card, side, mode):
    values = {
        resource: max(0, min(100, game.values[resource] + int(card[f"{side}_{resource}"] or 0)))
        for resource in RESOURCES
    }
    custom = card[f"{side}_custom"]
    risk = custom.count("risk+") - custom.count("risk-")
    evidence = custom.count("evidence+") - custom.count("evidence-")
    dirty = 1 if "dirty_route" in custom else 0
    edge = max(abs(value - 50) for value in values.values())
    death = any(value in (0, 100) for value in values.values())
    if mode == "clean":
        return (death, risk * 8 + evidence * 3 + dirty * 5, edge, -values["capital"])
    if mode == "dirty":
        return (death, -(risk * 5 + values["cash"] / 20 + values["capital"] / 20), edge)
    return (death, edge, risk + evidence)


def policy_for(mode):
    if mode == "random":
        return lambda game, card: game.random.choice(("no", "yes"))

    def choose(game, card):
        ranked = sorted((score_option(game, card, side, mode), side) for side in ("no", "yes"))
        return ranked[0][1]

    return choose


def run(mode, runs, max_turns, seed):
    endings = collections.Counter()
    lengths = []
    ceo_reached = 0
    first_ceo = []
    examples = {}
    for number in range(runs):
        game = Game(seed + number)
        result = game.play(policy_for(mode), max_turns=max_turns)
        endings[result] += 1
        lengths.append(game.turn)
        ceo_turns = [turn for turn, _, _, _, flags in game.history if flags.get("ceo_run")]
        if ceo_turns:
            ceo_reached += 1
            first_ceo.append(ceo_turns[0])
        examples.setdefault(result, game)
    lengths.sort()
    print(f"{mode}: {runs} 局")
    print(f"CEO 到达率 {ceo_reached / runs:.1%}; 到达回合 {min(first_ceo) if first_ceo else '-'}–{max(first_ceo) if first_ceo else '-'}")
    print(f"中位局长 {lengths[len(lengths)//2]}; 最长 {lengths[-1]}")
    print("结局：" + ", ".join(f"{name}={count}" for name, count in endings.most_common()))
    return examples


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=500)
    parser.add_argument("--max-turns", type=int, default=160)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--mode", choices=("random", "balanced", "clean", "dirty", "all"), default="all")
    args = parser.parse_args()
    modes = ("random", "balanced", "clean", "dirty") if args.mode == "all" else (args.mode,)
    for selected in modes:
        run(selected, args.runs, args.max_turns, args.seed)
