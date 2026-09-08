# -*- coding: utf-8 -*-
"""复刻浏览器抽卡逻辑，检查开放任期牌组的生存长度和结局分布。"""
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
        self.f = dict(keep)  # 只模拟当前一局；重新开局时传入空字典
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
        # 与浏览器一致：牌堆耗尽后重置抽卡锁，不清空本局后果状态。
        if g.lock:
            g.lock.clear()
            return pick(g, forced)
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


RESOURCE_ENDINGS = {
    '破产清算', '守财奴', '人去楼空', '大锅饭',
    '无人问津', '爆单崩盘', '一致行动', '功成身退',
}

EPISODE_VARIANTS = {
    '市场': ('price_fight_run', 'price_hold_run', 'buy_rival_run', 'wait_rival_run',
             'live_go_run', 'live_skip_run', 'exclusive_run', 'exclusive_refuse_run',
             'product_bet_run', 'product_both_run'),
    '团队': ('founder_delete_run', 'founder_meeting_run', 'nephew_hired_run',
             'nephew_refused_run', 'layoff_signed_run', 'layoff_refused_run',
             'star_promoted_run', 'star_left_run', 'overtime_apology_run',
             'overtime_deny_run'),
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
    while n < 2000:
        # 浏览器在每次抽牌前增加 turn，首张牌的 turn 是 1。
        g.turn += 1
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
            for name in RESOURCE_ENDINGS:
                if name in cu:
                    return n, name
            return n, '未知结局'
    return n, '超时（模拟保护上限）'


def percentile(values, ratio):
    if not values:
        return 0
    return values[min(len(values) - 1, int(len(values) * ratio))]


def main(runs=500, smart=False, tenures=1):
    lens, ends, seen = [], collections.Counter(), collections.Counter()
    episode_triggers = collections.Counter()
    episode_variants = collections.defaultdict(collections.Counter)
    games = 0
    for _ in range(runs):
        games += 1
        g = G(dict(cash=50, team=55, market=45, capital=50), 1, {})
        n, e = run_one(g, smart)
        lens.append(n)
        ends[e] += 1
        for k in g.f:
            if k.endswith('_keep'):
                seen[k] += 1
        if g.f.get('slot_market_run'):
            episode_triggers['市场'] += 1
        if g.f.get('slot_people_run'):
            episode_triggers['团队'] += 1
        for theme, flags in EPISODE_VARIANTS.items():
            for flag in flags:
                if g.f.get(flag):
                    episode_variants[theme][flag] += 1

    lens.sort()
    tag = '会玩的人' if smart else '随机乱划'
    print('=== %s：每局任期能活多少张卡 (%d 局) ===' % (tag, len(lens)))
    print('  中位数 %d   平均 %.1f' % (lens[len(lens) // 2], sum(lens) / len(lens)))
    print('  10分位 %d   90分位 %d   最长 %d' %
          (percentile(lens, .1), percentile(lens, .9), lens[-1]))
    print('  10 张前结束 %.1f%%   30 张后仍在任 %.1f%%' %
          (100 * sum(n < 10 for n in lens) / len(lens),
           100 * sum(n > 30 for n in lens) / len(lens)))
    print('  资源结局 %.1f%%   模拟保护上限 %.1f%%' %
          (100 * sum(ends[name] for name in RESOURCE_ENDINGS) / len(lens),
           100 * ends.get('超时（模拟保护上限）', 0) / len(lens)))
    print()
    print('=== 短篇触发率 ===')
    total_games = games or 1
    for theme in ('市场', '团队'):
        count = episode_triggers[theme]
        variants = episode_variants[theme]
        print('  %-2s短篇：%4.1f%% 本局触发，%d 种后续选择出现' %
              (theme, 100 * count / total_games, len(variants)))
    print()
    print('=== 结局分布 ===')
    total = sum(ends.values())
    for name, count in ends.most_common():
        print('  %-10s %5d  %4.1f%%  %s' %
              (name, count, 100 * count / total, '#' * int(50 * count / total)))
    print()
    print('=== 本局后果状态出现次数（前十）===')
    for name, count in seen.most_common(10):
        print('  %-26s %5d' % (name, count))
    print()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=500)
    parser.add_argument('--tenures', type=int, default=1,
                        help='兼容旧命令；开放任期模式下每局独立，不跨任继承')
    parser.add_argument('--smart', action='store_true')
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    random.seed(args.seed)
    main(runs=args.runs, smart=args.smart, tenures=args.tenures)
