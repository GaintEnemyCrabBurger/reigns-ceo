# -*- coding: utf-8 -*-
"""Build and validate the independent 《上位》 deck."""
import argparse
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEADER = [
    "thematic", "card", "id", "bearer", "conditions", "lockturn", "weight",
    "question", "override_yes", "answer_yes", "yes_cash", "yes_team",
    "yes_market", "yes_capital", "yes_custom", "override_no", "answer_no",
    "no_cash", "no_team", "no_market", "no_capital", "no_custom",
]
BUILTINS = {
    "cash", "money", "team", "market", "capital", "dynasty", "turn", "year",
    "overall", "risk", "evidence",
}
IMPLICIT_ENDINGS = {
    "ending_cash_zero", "ending_cash_max", "ending_team_zero", "ending_team_max",
    "ending_market_zero", "ending_market_max", "ending_capital_zero", "ending_capital_max",
}
CONDITION_RE = re.compile(r"!?[A-Za-z_]\w*(?:\s*(?:>=|<=|>|<|=)\s*-?\d+)?$")


def load_cards():
    with (HERE / "cards.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames != HEADER:
            raise SystemExit("cards.csv 表头不符合 22 列协议")
        cards = []
        for row in reader:
            if not (row.get("id") or "").strip():
                continue
            cards.append({key: (value or "").strip() for key, value in row.items()})
        return cards


def source_cards():
    from story import CARDS
    return [dict(card) for card in CARDS]


def assert_source_fresh(cards):
    expected = source_cards()
    if cards != expected:
        raise SystemExit("cards.csv 与 story.py 不同步；请先运行 python -X utf8 story.py")


def artifact_digest(cards, template, engine):
    payload = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256((payload + "\n" + template + "\n" + engine).encode("utf-8")).hexdigest()[:16]


def tokens(value):
    return [token.strip() for token in (value or "").split(" and ") if token.strip()]


def validate(cards):
    errors = []
    names = {card["card"] for card in cards if card["card"]}
    for field in ("id", "card"):
        counts = collections.Counter(card[field] for card in cards if card[field])
        for value, count in counts.items():
            if count > 1:
                errors.append(f"{field}={value} 重复 {count} 次")

    targets = set()
    for index, card in enumerate(cards):
        for field in ("yes_custom", "no_custom"):
            for token in tokens(card[field]):
                if not token.startswith(">"):
                    continue
                rest = token.lstrip(">").strip()
                if rest.startswith("_"):
                    target = rest[1:]
                elif rest in names:
                    target = rest
                elif rest.isdigit():
                    target_index = index + int(rest)
                    target = cards[target_index]["card"] if 0 <= target_index < len(cards) else ""
                else:
                    target = ""
                if target not in names:
                    errors.append(f"{card['card']} 跳转到不存在的卡 {target or rest}")
                else:
                    targets.add(target)
    for card in cards:
        if not card["weight"] and card["card"] not in targets and card["card"] not in IMPLICIT_ENDINGS:
            errors.append(f"{card['card']} 是续写卡但没有入口")

    reads = collections.defaultdict(list)
    writes = collections.defaultdict(list)
    for card in cards:
        source = card["card"] or card["id"]
        for token in tokens(card["conditions"]):
            if not CONDITION_RE.fullmatch(token):
                errors.append(f"{source} 条件语法不支持：{token}")
                continue
            match = re.match(r"^!?([A-Za-z_]\w*)", token)
            if match and match.group(1) not in BUILTINS:
                reads[match.group(1)].append(source)
        for field in ("yes_custom", "no_custom"):
            for token in tokens(card[field]):
                if token.startswith(">") or token.startswith("end_"):
                    continue
                if token.startswith("!"):
                    continue
                elif token.endswith(("+", "-")):
                    writes[token.rstrip("+-")].append(source)
                elif re.match(r"^[A-Za-z_]\w*$", token):
                    writes[token].append(source)
    for name, sources in sorted(reads.items()):
        if name not in writes:
            errors.append(f"条件状态 {name} 从未写入（{sources[0]}）")
    return errors


def build(cards):
    template = (HERE / "source-index.html").read_text(encoding="utf-8")
    engine = (HERE / "engine.js").read_text(encoding="utf-8")
    if "/*__CARDS__*/[]" not in template:
        raise SystemExit("index.html 缺少卡牌占位符")
    digest = artifact_digest(cards, template, engine)
    if "<!--__UPSTART_BUILD__*/" not in template:
        raise SystemExit("index.html 缺少构建指纹占位符")
    output = template.replace("<!--__UPSTART_BUILD__*/", f"<!-- upstart-build:{digest} -->")
    output = output.replace("/*__CARDS__*/[]", json.dumps(cards, ensure_ascii=False))
    output = output.replace('<script src="engine.js"></script>', f"<script>\n{engine}\n</script>")
    (HERE / "玩.html").write_text(output, encoding="utf-8")
    (HERE / "index.html").write_text(output, encoding="utf-8")


def artifact_is_fresh(cards):
    template = (HERE / "source-index.html").read_text(encoding="utf-8")
    engine = (HERE / "engine.js").read_text(encoding="utf-8")
    output = (HERE / "玩.html").read_text(encoding="utf-8")
    expected = artifact_digest(cards, template, engine)
    return f"<!-- upstart-build:{expected} -->" in output


def assert_artifacts_consistent(cards):
    names = [card["card"] for card in cards]

    meta = json.loads((HERE / "story-meta.json").read_text(encoding="utf-8"))
    meta_names = list((meta.get("cards") or {}).keys())
    if meta_names != names:
        raise SystemExit("story-meta.json 与 story.py 的卡牌顺序不一致")
    for name in names:
        if name not in meta["cards"]:
            raise SystemExit(f"story-meta.json 缺少卡牌 {name}")

    expected_entries = {
        card["card"].removeprefix("ending_"): []
        for card in cards
        if card["thematic"] == "endings"
    }
    for card in cards:
        if card["thematic"] == "endings":
            continue
        for side in ("no", "yes"):
            for raw_token in (card[f"{side}_custom"] or "").split(" and "):
                token = raw_token.strip()
                if token.startswith(">_ending_"):
                    key = token[len(">_ending_"):]
                elif token.startswith("end_"):
                    key = token[len("end_"):]
                else:
                    continue
                if key not in expected_entries:
                    continue
                expected_entries[key].append({
                    "card": card["card"],
                    "side": side,
                    "choice": card[f"override_{side}"],
                    "condition": card["conditions"],
                })
    for key, expected in expected_entries.items():
        ending_meta = meta["cards"][f"ending_{key}"]
        actual = ending_meta.get("entries", [])
        if actual != expected:
            raise SystemExit(f"ending_{key} 的显式入口元数据与卡组不一致")
        if expected:
            if ending_meta.get("trigger_type") != "explicit_choice":
                raise SystemExit(f"ending_{key} 缺少 explicit_choice trigger_type")
            if ending_meta.get("trigger") != "显式选择":
                raise SystemExit(f"ending_{key} 的 trigger 不是显式选择")
        elif ending_meta.get("trigger_type") != "resource_edge":
            raise SystemExit(f"ending_{key} 缺少 resource_edge trigger_type")

    manual = (HERE / "故事手册.md").read_text(encoding="utf-8")
    manual_names = re.findall(r"^### (.+)$", manual, flags=re.MULTILINE)
    if manual_names != names:
        raise SystemExit("故事手册.md 与 story.py 的卡牌顺序不一致")

    output = (HERE / "玩.html").read_text(encoding="utf-8")
    embedded = re.search(r"const CARDS = (.*?);\r?\n</script>", output, flags=re.DOTALL)
    if not embedded:
        raise SystemExit("玩.html 缺少内嵌卡组")
    if json.loads(embedded.group(1)) != cards:
        raise SystemExit("玩.html 内嵌卡组与 cards.csv 不一致")
    if not artifact_is_fresh(cards):
        raise SystemExit("玩.html 构建指纹过期；请重新运行 build.py")
    if (HERE / "index.html").read_text(encoding="utf-8") != output:
        raise SystemExit("index.html 与 玩.html 发布内容不一致")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="同步生成 docs/shangwei 独立发布入口")
    arguments = parser.parse_args()
    cards = load_cards()
    assert_source_fresh(cards)
    errors = validate(cards)
    if errors:
        print("校验失败：")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    build(cards)
    assert_artifacts_consistent(cards)
    print(f"校验通过：{len(cards)} 张卡；续写 {sum(not c['weight'] for c in cards)} 张；已生成 玩.html")
    if arguments.publish:
        destination = HERE.parents[2] / "docs" / "shangwei"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(
            (HERE / "index.html").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        print("已发布：docs/shangwei/index.html")


if __name__ == "__main__":
    main()
