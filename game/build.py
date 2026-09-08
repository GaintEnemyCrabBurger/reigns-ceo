# -*- coding: utf-8 -*-
"""把 cards.csv 塞进 index.html，生成可以直接双击打开的 玩.html"""
import csv, json, io, os

HERE = os.path.dirname(os.path.abspath(__file__))

def load(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding='utf-8-sig') as f:
        return [r for r in csv.DictReader(f, delimiter=';') if (r.get('id') or '').strip()]

NCOL = 22

def check(name):
    with io.open(os.path.join(HERE, name), encoding='utf-8-sig') as f:
        rows = list(csv.reader(f, delimiter=';'))
    hdr = rows[0]
    bad = []
    for i, r in enumerate(rows[1:], start=2):
        if not any(x.strip() for x in r):
            continue
        if len(r) != len(hdr):
            bad.append((i, len(r), (r[1] if len(r) > 1 else '?')))
    if bad:
        print('!! %s 列数不符 (应为 %d):' % (name, len(hdr)))
        for i, n, cid in bad:
            print('   行%-4d 列数=%-3d card=%s' % (i, n, cid))
    return len(hdr), bad

check('cards.csv')
cards = load('cards.csv')
for c in cards:
    if None in c:
        del c[None]
    for k in list(c.keys()):
        c[k] = (c[k] or '').strip() if not isinstance(c[k], list) else ''

def validate(cards):
    names = {c['card']: i for i, c in enumerate(cards) if c['card']}
    problems = []
    # 1. 跳转目标必须存在
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
    # 2. 续写卡必须有人能跳进来
    targets = set()
    for c in cards:
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
                    j = cards.index(c) + off
                    if 0 <= j < len(cards) and cards[j]['card']:
                        targets.add(cards[j]['card'])
    for c in cards:
        if not c['weight'] and c['card'] and c['card'] not in targets:
            problems.append('%s 是续写卡，但没有任何卡跳向它 —— 永远出不来' % c['card'])
    # 3. 数值幅度体检
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
    if problems:
        print('!! 校验问题 %d 条:' % len(problems))
        for p in problems:
            print('   ' + p)
    else:
        print('校验通过：所有跳转目标存在，所有续写卡可达')
    if deltas:
        deltas.sort()
        print('数值幅度：中位数 %d，90分位 %d，最大 %d' %
              (deltas[len(deltas)//2], deltas[int(len(deltas)*0.9)], deltas[-1]))
    print('零数值选择占比：%d%%  (王权实测 48%%)' % round(100*zero/(len(cards)*2)))
    return problems

validate(cards)

tpl = io.open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
eng = io.open(os.path.join(HERE, 'engine.js'), encoding='utf-8').read()
out = tpl.replace('/*__CARDS__*/[]', json.dumps(cards, ensure_ascii=False))
out = out.replace('<script src="engine.js"></script>', '<script>\n' + eng + '\n</script>')
io.open(os.path.join(HERE, '玩.html'), 'w', encoding='utf-8').write(out)
print('cards: %d' % len(cards))
print('themes: %s' % sorted(set(c['thematic'] for c in cards)))
entry = [c for c in cards if c['weight']]
print('entry: %d  continuation: %d' % (len(entry), len(cards) - len(entry)))
print('-> 玩.html')
