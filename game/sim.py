# -*- coding: utf-8 -*-
"""用 Python 复刻引擎跑几千局，看平均能活多少张卡、八种结局分布是否均衡。
王权的目标区间是一局 40-80 张。"""
import csv, io, os, random, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
K = ['cash', 'team', 'market', 'capital']
with io.open(os.path.join(HERE, 'cards.csv'), encoding='utf-8-sig') as f:
    CARDS = [r for r in csv.DictReader(f, delimiter=';') if (r.get('id') or '').strip()]
BY = {c['card']: i for i, c in enumerate(CARDS) if c['card']}


def num(v):
    v = (v or '').replace('?', '').replace('*', '').strip()
    m = re.match(r'^-?\d+', v)
    return int(m.group(0)) if m else 0


class G:
    def __init__(self, seed, dyn, keep):
        self.v = dict(seed)
        self.dyn = dyn
        self.turn = 0
        self.f = dict(keep)
        self.lock = {}

    def val(self, n):
        if n in ('cash', 'money'):
            return self.v['cash']
        if n in K:
            return self.v[n]
        if n == 'dynasty':
            return self.dyn
        if n == 'turn':
            return self.turn
        if n == 'overall':
            return sum(self.v.values()) // 4
        if n.startswith('nb_'):
            return self.f.get(n, 0)
        return 1 if self.f.get(n) else 0

    def test1(self, t):
        t = t.strip()
        if not t:
            return True
        m = re.match(r'^([A-Za-z_]\w*)\s*(>=|<=|>|<|=)\s*(-?\d+)$', t)
        if m:
            a, op, b = self.val(m.group(1)), m.group(2), int(m.group(3))
            return {'>': a > b, '<': a < b, '=': a == b, '>=': a >= b, '<=': a <= b}[op]
        if t[0] == '!':
            return not self.val(t[1:])
        return bool(self.val(t))

    def test(self, s):
        return all(self.test1(x) for x in (s or '').split(' and ')) if (s or '').strip() else True


def pick(g, forced):
    if forced is not None:
        return forced
    pool = []
    best = 0
    for i, c in enumerate(CARDS):
        if not c['weight'].strip():
            continue
        if g.lock.get(c['card'], 0) > g.turn:
            continue
        if not g.test(c['conditions']):
            continue
        w = 10 ** 9 if c['weight'] == 'max' else int(c['weight'])
        best = max(best, w)
        pool.append((i, w))
    if not pool:
        return None
    use = [p for p in pool if p[1] == best] if best >= 1000 else [p for p in pool if p[1] >= best * 0.5]
    tot = sum(w for _, w in use)
    r = random.random() * tot
    for i, w in use:
        r -= w
        if r <= 0:
            return i
    return use[-1][0]


def apply_flags(g, s, idx):
    forced = None
    for tok in (s or '').split(' and '):
        t = tok.strip()
        if not t:
            continue
        if t[0] == '>':
            arrows = len(t) - len(t.lstrip('>'))
            rest = t.lstrip('>')
            if rest.startswith('_'):
                forced = BY.get(rest[1:])
            elif rest in BY:
                forced = BY[rest]
            elif rest.isdigit():
                forced = idx + int(rest)
            else:
                forced = idx + arrows
            continue
        if t.endswith('+'):
            base = t.rstrip('+')
            g.f[base] = g.f.get(base, 0) + (len(t) - len(base))
            continue
        if t[0] == '!':
            g.f.pop(t[1:], None)
            continue
        if t.startswith('mus_'):
            continue
        g.f[t] = 1
    return forced


ENDNEXT = {
    '破产清算': dict(cash=15, team=40, market=40, capital=35),
    '守财奴': dict(cash=85, team=50, market=25, capital=50),
    '人去楼空': dict(cash=45, team=15, market=35, capital=40),
    '大锅饭': dict(cash=25, team=85, market=45, capital=45),
    '无人问津': dict(cash=40, team=45, market=15, capital=35),
    '爆单崩盘': dict(cash=45, team=20, market=80, capital=40),
    '一致行动': dict(cash=50, team=45, market=45, capital=20),
    '功成身退': dict(cash=60, team=50, market=55, capital=85),
}


def smart_side(g, c):
    """模拟一个会玩的人：选让四条槽离危险线更远的那边。
    真人不会往死路上划，所以随机模拟会严重低估存活长度。"""
    best, bestscore = None, None
    for side in ('yes', 'no'):
        v = dict(g.v)
        for k in K:
            v[k] = max(0, min(100, v[k] + num(c['%s_%s' % (side, k)])))
        # 分数 = 最危险那条槽离 50 的距离（越小越安全）
        risk = max(abs(v[k] - 50) for k in K)
        dead = any(v[k] <= 0 or v[k] >= 100 for k in K)
        score = (1 if dead else 0, risk)
        if bestscore is None or score < bestscore:
            bestscore, best = score, side
    # 留一点噪声，真人也会犯错 / 也会为了看剧情乱选
    return best if random.random() > 0.25 else random.choice(['yes', 'no'])


def run_one(g, smart=False):
    """跑一任，返回 (活了几张卡, 结局名)"""
    forced = None
    n = 0
    while n < 400:
        idx = pick(g, forced)
        forced = None
        if idx is None:
            return n, '无人问津'
        c = CARDS[idx]
        n += 1
        side = smart_side(g, c) if smart else random.choice(['yes', 'no'])
        for k in K:
            d = num(c['%s_%s' % (side, k)])
            if d:
                g.v[k] = max(0, min(100, g.v[k] + d))
        lt = c['lockturn'].strip()
        if lt == 'del':
            g.lock[c['card']] = 10 ** 9
        elif lt:
            g.lock[c['card']] = g.turn + int(lt)
        forced = apply_flags(g, c['%s_custom' % side], idx)
        if c['thematic'] == 'endings':
            cu = c['%s_custom' % side] or ''
            for name in ENDNEXT:
                if name in cu:
                    return n, name
            return n, '未知结局'
        g.turn += 1
    return n, '超时'


def main(runs=3000, smart=False):
    lens, ends, seen = [], collections.Counter(), collections.Counter()
    for _ in range(runs):
        g = G(dict(cash=50, team=55, market=45, capital=50), 1, {})
        for _t in range(8):        # 连续玩 8 任
            n, e = run_one(g, smart)
            lens.append(n)
            ends[e] += 1
            for k in g.f:
                if k.endswith('_keep'):
                    seen[k] += 1
            nxt = ENDNEXT.get(e)
            if not nxt:
                break
            keep = {k: v for k, v in g.f.items() if k.endswith('_keep') or k.startswith('nb_')}
            g = G(nxt, g.dyn + 1, keep)
    lens.sort()
    tag = '会玩的人' if smart else '随机乱划'
    print('=== %s：一任能活多少张卡 (%d 局) ===' % (tag, len(lens)))
    print('  中位数 %d   平均 %.1f' % (lens[len(lens) // 2], sum(lens) / len(lens)))
    print('  10分位 %d   90分位 %d   最长 %d' % (lens[len(lens) // 10], lens[int(len(lens) * .9)], lens[-1]))
    print('  王权目标区间 40-80 张')
    print()
    print('=== 八种结局分布 ===')
    tot = sum(ends.values())
    for k, v in ends.most_common():
        print('  %-10s %5d  %4.1f%%  %s' % (k, v, 100 * v / tot, '#' * int(50 * v / tot)))
    print()
    print('=== 剧情线触达率（每局至少见到一次）===')
    for k, v in seen.most_common(10):
        print('  %-22s %4.1f%%' % (k, 100 * v / runs))


if __name__ == '__main__':
    import sys
    random.seed(7)
    main(smart='smart' in sys.argv)
