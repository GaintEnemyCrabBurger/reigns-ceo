"""导出并校验故事，生成无需联网或服务器的单文件游戏。"""
import argparse
import collections
import csv
import json
import re
from pathlib import Path

import story

HERE = Path(__file__).resolve().parent
BUILTINS = {'money', 'team', 'market', 'mind', 'turn', 'phase', 'dynasty', 'lucky_bet_run'}
PLACEHOLDERS = {'company', 'maker', 'rival'}
COPY_LIMITS = {'bearer': 10, 'question': 24, 'override_yes': 7, 'override_no': 7,
               'answer_yes': 20, 'answer_no': 20}


def validate(cards, meta):
    problems = []
    names = set()
    identifiers = set()
    reads = set()
    writes = {ending.get('flag') for ending in meta['endings'].values()}
    for card in cards:
        name = card['card']
        if name in names or card['id'] in identifiers:
            problems.append(f'重复 card/id: {name}')
        names.add(name)
        identifiers.add(card['id'])
        if name not in meta['cards']:
            problems.append(f'缺少元数据: {name}')
        if not card['weight'].isdigit() or int(card['weight']) <= 0:
            problems.append(f'没有抽取来源: {name}')
        if card['lockturn'] != 'del' and (not card['lockturn'].isdigit() or int(card['lockturn']) < 2):
            problems.append(f'非法冷却: {name}')
        for token in card['conditions'].split(' and '):
            if not token:
                continue
            match = re.fullmatch(r'!?([A-Za-z_]\w*)(?:\s*(?:>=|<=|>|<|=)\s*-?\d+)?', token)
            if not match or (token.startswith('!') and re.search(r'[<>=]', token)):
                problems.append(f'条件语法不支持: {name}: {token}')
            elif match[1].startswith('age_'):
                reads.add(match[1][4:] + '_run')
            elif match[1] not in BUILTINS:
                reads.add(match[1])
        for side in ('yes', 'no'):
            if not card[f'override_{side}'] or not card[f'answer_{side}']:
                problems.append(f'缺选项或反馈: {name}.{side}')
            for resource in story.RESOURCES:
                raw = card[f'{side}_{resource}']
                if raw and not re.fullmatch(r'-?\d+', raw):
                    problems.append(f'非法资源变化: {name}.{side}.{resource}')
            for token in card[f'{side}_custom'].split(' and '):
                if not token:
                    continue
                if token.startswith('>'):
                    problems.append(f'本版不允许强制剧情跳转: {name}')
                elif token.startswith('end_'):
                    if token[4:] not in meta['endings']:
                        problems.append(f'未知结局: {name}: {token}')
                    if card['thematic'] != 'exit':
                        problems.append(f'非主动退场卡结束游戏: {name}')
                elif not re.fullmatch(r'!?[A-Za-z_]\w*\+*', token):
                    problems.append(f'非法状态写入: {name}: {token}')
                elif not token.startswith('!'):
                    writes.add(token.rstrip('+'))
        if all('end_' in card[f'{side}_custom'] for side in ('yes', 'no')):
            problems.append(f'没有继续经营的选项: {name}')
        for field, limit in COPY_LIMITS.items():
            for placeholder in re.findall(r'\{(\w+)\}', card[field]):
                if placeholder not in PLACEHOLDERS:
                    problems.append(f'未知占位符: {name}: {placeholder}')
            rendered = re.sub(r'\{\w+\}', '名字四字', card[field])
            if len(rendered) > limit:
                problems.append(f'超出阅读预算: {name}.{field}: {len(rendered)}/{limit}')
            if '\n' in rendered or '\r' in rendered:
                problems.append(f'卡面只保留一句话，不分段讲故事: {name}.{field}')
    for flag in sorted(reads - writes):
        problems.append(f'没有正向写入来源的条件: {flag}')
    for name, ending in meta['endings'].items():
        for field in ('title', 'label', 'body'):
            if not ending.get(field):
                problems.append(f'缺少结局字段: {name}.{field}')
            for placeholder in re.findall(r'\{(\w+)\}', ending.get(field, '')):
                if placeholder not in PLACEHOLDERS:
                    problems.append(f'未知结局占位符: {name}: {placeholder}')
    if problems:
        raise SystemExit('\n'.join(problems))
    count = collections.Counter(meta['cards'][card['card']]['kind'] for card in cards)
    zero = sum(all(not card[f'{side}_{resource}'] for resource in story.RESOURCES)
               for card in cards if card['thematic'] != 'exit' for side in ('yes', 'no'))
    print('校验通过：22 列、唯一引用、状态来源、终局与反馈完整；无强制跳转。')
    print(f'叙事类型: {dict(count)}；非退场零数值选项: {zero} 个。')
    lengths = [len(card['question']) for card in cards]
    print(f'卡面平均 {sum(lengths) / len(lengths):.1f} 字符，最长 {max(lengths)}；选项最多 7，反馈最多 20。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='生成 docs/gpt-6-astra 独立发布入口，不覆盖其他版本')
    arguments = parser.parse_args()
    story.export()
    with (HERE / 'cards.csv').open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.reader(handle, delimiter=';'))
    if rows[0] != story.HEADER or any(len(row) != 22 for row in rows):
        raise SystemExit('卡表必须严格满足约定的 22 列结构。')
    cards = [dict(zip(rows[0], row)) for row in rows[1:]]
    meta = json.loads((HERE / 'story-meta.json').read_text(encoding='utf-8'))
    validate(cards, meta)
    payload = dict(cards=cards, meta=meta)
    (HERE / 'deck.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    page = (HERE / 'index.html').read_text(encoding='utf-8')
    if page.count('/*__STORY__*/{}') != 1:
        raise SystemExit('故事数据入口缺失或重复。')
    packed = json.dumps(payload, ensure_ascii=False).replace('</', '<\\/')
    page = page.replace('/*__STORY__*/{}', packed)
    for filename in ('logic.js', 'engine.js'):
        if page.count(f'<script src="{filename}"></script>') != 1:
            raise SystemExit(f'脚本入口缺失或重复: {filename}')
        source = (HERE / filename).read_text(encoding='utf-8').replace('</script', '<\\/script')
        page = page.replace(f'<script src="{filename}"></script>', f'<script>\n{source}\n</script>')
    if any(marker in page for marker in ('/api/story', '/api/cards', 'story-control', '/*__STORY__*/')):
        raise SystemExit('玩家页面仍有未替换占位符或后台入口。')
    if 'const STORY =' not in page or 'const Founder =' not in page:
        raise SystemExit('界面尚未接入故事数据。')
    (HERE / '玩.html').write_text(page, encoding='utf-8')
    print(f'-> 玩.html ({len(page.encode("utf-8")):,} bytes)')
    if arguments.publish:
        destination = HERE.parents[2] / 'docs' / 'gpt-6-astra'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'index.html').write_text(page, encoding='utf-8')
        print('-> docs/gpt-6-astra/index.html (GPT 6 Astra 作品)')


if __name__ == '__main__':
    main()
