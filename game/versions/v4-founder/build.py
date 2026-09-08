# -*- coding: utf-8 -*-
"""校验卡组，并把 cards.csv 塞进 index.html 生成可直接打开的 玩.html。"""
import collections
import csv
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

def load(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding='utf-8-sig') as f:
        return [r for r in csv.DictReader(f, delimiter=';') if (r.get('id') or '').strip()]

EXPECTED_HEADER = [
    'thematic', 'card', 'id', 'bearer', 'conditions', 'lockturn', 'weight',
    'question', 'override_yes', 'answer_yes', 'yes_cash', 'yes_team',
    'yes_market', 'yes_capital', 'yes_custom', 'override_no', 'answer_no',
    'no_cash', 'no_team', 'no_market', 'no_capital', 'no_custom',
]
BUILTIN_CONDITIONS = {
    'cash', 'money', 'team', 'market', 'capital', 'dynasty', 'turn', 'year', 'overall',
}

def check(name):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return ['%s 不存在' % name]
    with io.open(path, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f, delimiter=';'))
    if not rows:
        return ['%s 是空文件' % name]
    hdr = rows[0]
    problems = []
    if hdr != EXPECTED_HEADER:
        problems.append('%s 表头不是约定的 22 列' % name)
    for i, r in enumerate(rows[1:], start=2):
        if not any(x.strip() for x in r):
            continue
        if len(r) != len(hdr):
            problems.append('%s 第 %d 行列数=%d，card=%s' %
                            (name, i, len(r), r[1] if len(r) > 1 else '?'))
    if problems:
        print('!! %s 列数不符 (应为 %d):' % (name, len(hdr)))
        for problem in problems:
            print('   ' + problem)
    else:
        print('%s：22 列结构正常' % name)
    return problems

schema_problems = check('cards.csv') + check('cards-independent.csv')
cards = load('cards.csv')
for c in cards:
    if None in c:
        del c[None]
    for k in list(c.keys()):
        c[k] = (c[k] or '').strip() if not isinstance(c[k], list) else ''

def validate(cards):
    names = {c['card']: i for i, c in enumerate(cards) if c['card']}
    problems = []
    warnings = []

    # 1. id 和 card 都是稳定引用，不允许重复。
    for field in ('id', 'card'):
        counts = collections.Counter(c[field] for c in cards if c[field])
        for value, count in sorted(counts.items()):
            if count > 1:
                problems.append('%s=%s 重复 %d 次' % (field, value, count))

    # 2. 跳转目标必须存在。
    for i, c in enumerate(cards):
        for side in ('yes_custom', 'no_custom'):
            for tok in (c.get(side) or '').split(' and '):
                t = tok.strip()
                if not t.startswith('>'):
                    continue
                rest = t.lstrip('>')
                if rest.startswith('_'):
                    if rest[1:] not in names:
                        problems.append('%s.%s 跳转到不存在的卡 %s' % (c['card'] or c['id'], side, rest[1:]))
                elif rest and not rest.isdigit() and rest not in names:
                    problems.append('%s.%s 跳转目标可疑 %s' % (c['card'] or c['id'], side, rest))
    # 3. 续写卡必须有人能跳进来。
    targets = set()
    for i, c in enumerate(cards):
        for side in ('yes_custom', 'no_custom'):
            for tok in (c.get(side) or '').split(' and '):
                t = tok.strip()
                if not t.startswith('>'):
                    continue
                rest = t.lstrip('>')
                arrows = len(t) - len(rest)
                if rest.startswith('_'):
                    targets.add(rest[1:])
                elif rest in names:
                    targets.add(rest)
                else:
                    off = int(rest) if rest.isdigit() else arrows
                    j = i + off
                    if 0 <= j < len(cards) and cards[j]['card']:
                        targets.add(cards[j]['card'])
    for c in cards:
        if not c['weight'] and c['card'] and c['card'] not in targets:
            problems.append('%s 是续写卡，但没有任何卡跳向它 —— 永远出不来' % c['card'])
    # 4. 条件 flag 和写入 flag 配对。未读写入可以用于未来内容，只警告；
    #    从未写入的条件会让卡永久不可达，视为错误。
    reads = collections.defaultdict(list)
    writes = collections.defaultdict(list)
    for c in cards:
        source = c['card'] or c['id']
        for raw in (c.get('conditions') or '').split(' and '):
            match = re.match(r'^!?([A-Za-z_]\w*)', raw.strip())
            if match and match.group(1) not in BUILTIN_CONDITIONS:
                reads[match.group(1)].append(source)
        for side in ('yes_custom', 'no_custom'):
            for raw in (c.get(side) or '').split(' and '):
                token = raw.strip()
                if not token or token.startswith('>') or token.startswith('mus_') or token.startswith('end_'):
                    continue
                name = token[1:] if token.startswith('!') else token.rstrip('+')
                if re.match(r'^[A-Za-z_]\w*$', name):
                    writes[name].append(source)

    engine_text = io.open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
    engine_writes = set(re.findall(r"flag:\s*'([A-Za-z_]\w*)'", engine_text))
    for name in sorted(set(reads) - set(writes) - engine_writes):
        problems.append('条件 flag %s 从未被任何选择写入（见 %s）' %
                        (name, ', '.join(reads[name][:3])))
    for name in sorted(set(writes) - set(reads)):
        warnings.append('状态 %s 被写入但尚未用于条件（首次见 %s）' %
                        (name, writes[name][0]))

    # 5. 数值幅度与阅读长度体检。
    deltas = []
    for c in cards:
        for side in ('yes', 'no'):
            for k in ('cash', 'team', 'market', 'capital'):
                v = (c.get('%s_%s' % (side, k)) or '').strip()
                if v.lstrip('-').isdigit():
                    deltas.append(abs(int(v)))
    zero = sum(1 for c in cards for side in ('yes', 'no')
               if not any((c.get('%s_%s' % (side, k)) or '').strip()
                          for k in ('cash', 'team', 'market', 'capital')))
    long_questions = sorted(
        ((len(c['question']), c['card']) for c in cards if len(c['question']) > 52),
        reverse=True,
    )
    long_choices = sorted(
        (len(c[field]), c['card'], field)
        for c in cards for field in ('override_yes', 'override_no')
        if len(c[field]) > 8
    )
    if problems:
        print('!! 校验问题 %d 条:' % len(problems))
        for p in problems:
            print('   ' + p)
    else:
        print('校验通过：所有跳转目标存在，所有续写卡可达')
    if warnings:
        print('状态提示 %d 条:' % len(warnings))
        for warning in warnings:
            print('   ' + warning)
    if deltas:
        deltas.sort()
        print('数值幅度：中位数 %d，90分位 %d，最大 %d' %
              (deltas[len(deltas)//2], deltas[int(len(deltas)*0.9)], deltas[-1]))
    print('零数值选择占比：%d%%  (王权实测 48%%)' % round(100*zero/(len(cards)*2)))
    if long_questions:
        print('长问题提示：%d 张超过 52 字，最长为 %s (%d 字)' %
              (len(long_questions), long_questions[0][1], long_questions[0][0]))
    if long_choices:
        print('长选项提示：%d 个超过 8 字，最长为 %s.%s (%d 字)' %
              (len(long_choices), long_choices[-1][1], long_choices[-1][2],
               long_choices[-1][0]))
    return problems

problems = schema_problems + validate(cards)
if problems:
    raise SystemExit(1)

tpl = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
eng = io.open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
private_markers = (
    'story-control', 'story_server', 'story-model',
    '/api/story', '/api/cards',
)
leaked_markers = [marker for marker in private_markers if marker in tpl or marker in eng]
if leaked_markers:
    print('!! 玩家页包含后台入口：%s' % ', '.join(leaked_markers))
    raise SystemExit(1)
out = tpl.replace('/*__CARDS__*/[]', json.dumps(cards, ensure_ascii=False))
out = out.replace('<script src="engine.js"></script>', '<script>\n' + eng + '\n</script>')
io.open(os.path.join(HERE, '玩.html'), 'w', encoding='utf-8').write(out)
print('cards: %d' % len(cards))
print('themes: %s' % sorted(set(c['thematic'] for c in cards)))
entry = [c for c in cards if c['weight']]
print('entry: %d  continuation: %d' % (len(entry), len(cards) - len(entry)))
print('-> 玩.html')
