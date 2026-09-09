"""GPT 6 Astra 作品：现实商业世界的短卡创业故事，沿用原版 22 列格式。"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESOURCES = ('money', 'team', 'market', 'mind')
HEADER = ['thematic', 'card', 'id', 'bearer', 'conditions', 'lockturn', 'weight',
          'question', 'override_yes', 'answer_yes', 'yes_money', 'yes_team',
          'yes_market', 'yes_mind', 'yes_custom', 'override_no', 'answer_no',
          'no_money', 'no_team', 'no_market', 'no_mind', 'no_custom']
CARDS = []
META = {}


def option(label, reply, delta=(0, 0, 0, 0), flags=''):
    return dict(label=label, reply=reply, delta=delta, flags=flags)


def add(name, theme, bearer, question, left, right, condition='turn>=2',
        weight=140, kind='initiative', shared='', cooldown=0):
    card = dict.fromkeys(HEADER, '')
    visible = bearer + question + left['reply'] + right['reply']
    if '{maker}' in visible and theme != 'legacy':
        condition += ' and !partner_left_run'
    card.update(thematic=theme, card=name, id=str(len(CARDS) + 1), bearer=bearer,
                question=question, conditions=condition,
                lockturn=str(cooldown) if cooldown else 'del', weight=str(weight))
    for side, choice in [('no', left), ('yes', right)]:
        card[f'override_{side}'] = choice['label']
        card[f'answer_{side}'] = choice['reply']
        card[f'{side}_custom'] = ' and '.join(filter(None, [choice['flags'], shared]))
        for resource, amount in zip(RESOURCES, choice['delta']):
            card[f'{side}_{resource}'] = str(amount) if amount else ''
    CARDS.append(card)
    META[name] = dict(kind=kind, title=bearer.split(' · ')[0], keepsakes={})


add('first_move', 'opening', '财务总监',
    '大厂开价三亿，今晚要答复。',
    option('签框架', '钱还没到账，品牌先归他。', (18, -3, -5, -2), 'deal_run'),
    option('拒绝，扩产', '对手转身降价，工厂开始加班。', (-12, 4, 15, 4), 'independent_run'),
    'turn=1', 900000, shared='founder_run')

add('deal_follow', 'payoff', '大厂法务',
    '他们肯加价，但要你删掉主力款。',
    option('换现金', '你拿到钱，也交出最好卖的货。', (22, -4, -15, -3), 'deal_cash_run'),
    option('保产品，谈渠道', '合同没签，采购总监先来加你。', (-6, 2, 13, 6), 'deal_channel_run'),
    'deal_run and age_founder>=2', 3200, 'payoff', 'deal_done_run')

add('capacity_follow', 'payoff', '厂长',
    '拒绝大厂后，订单多到排不下。',
    option('先交老客', '销量慢一点，老客介绍来同行。', (10, -2, 12, 5), 'capacity_safe_run'),
    option('借线抢单', '产能上来了，供应商要预付款。', (-8, -8, 17, -3), 'delivery_run'),
    'independent_run and age_founder>=2', 3200, 'payoff', 'capacity_done_run and capacity_run')

add('delivery_crisis', 'pressure', '厂长',
    '你答应的货，还差一周才出厂。',
    option('分批交', '客户先收一半，尾款没扣。', (10, -5, 5, 2)),
    option('借线硬做', '你借来产线，利息也一起借来。', (-14, 7, 9, -5), 'debt_run'),
    'delivery_run and age_capacity>=3', 2800, 'payoff', 'delivery_done_run')

add('conference', 'initiative', '行业协会秘书长',
    '渠道商约你吃饭，对手也在桌上。',
    option('先聊价格', '你报得不低，他却带走试销单。', (-3, 3, 15, 3), 'conference_show_run'),
    option('先聊售后', '他不买广告，只问能不能退货。', (-5, 5, 12, 7), 'conference_deal_run'),
    'founder_run and turn>=4 and !conference_run', 2400, 'initiative', 'conference_run')

add('conference_show_payoff', 'payoff', '连锁采购',
    '你报得不低，他要看你能否交货。',
    option('先看样机', '样机过检，试销单进了系统。', (16, 4, 12, 3), 'conference_win_run'),
    option('先谈独家', '独家签了，渠道也被锁住了。', (21, -3, 9, -4), 'exclusive_run'),
    'conference_show_run and age_conference>=2', 2600, 'payoff', 'conference_done_run')

add('conference_deal_payoff', 'payoff', '连锁采购',
    '他愿意试销，但要你先垫货。',
    option('不垫，先收钱', '他走了，下午又打回来。', (12, 0, 4, 3), 'conference_win_run'),
    option('我先压库存', '首批交了，第二批要加价。', (-13, -4, 15, -4), 'inventory_run'),
    'conference_deal_run and age_conference>=2', 2600, 'payoff', 'conference_done_run')

add('rival_price', 'initiative', '销售总监',
    '对手把你的爆款拆开，价格砍了一半。',
    option('跟到最低', '他先没现金，你先没利润。', (-9, 2, 16, -2), 'price_war_run'),
    option('保服务提价格', '老客户没走，新客户在比较。', (12, 5, 8, 5), 'premium_run'),
    'founder_run and turn>=5 and !price_war_run and !premium_run', 2500)

add('price_counter', 'payoff', '对手渠道商',
    '对手没钱发货，渠道想改卖你的。',
    option('带预付款来', '钱到账，货架换了招牌。', (22, 0, 11, 2), 'channel_win_run'),
    option('自己开店', '利润留下，库存也留下。', (-8, 7, 14, 4), 'direct_run'),
    'price_war_run and age_price_war>=3', 2700, 'payoff', 'price_done_run')

add('premium_counter', 'payoff', '老客户',
    '你没跟着降价，客户要一份更硬的保证。',
    option('延长保修', '保修变长，续单也变长。', (-7, 6, 16, 3), 'warranty_run'),
    option('给服务定价', '有人嫌贵，核心客户留下。', (19, -2, 9, -3), 'service_fee_run'),
    'premium_run and age_premium>=3', 2700, 'payoff', 'premium_done_run')

add('national_order', 'power', '全国连锁采购',
    '他要包下三个月产能，条件是独家。',
    option('签独家，先收钱', '预付款进账，别的渠道关门。', (19, -4, 15, 2), 'national_cash_run'),
    option('留多个渠道', '少赚一点，客户没被一家拿走。', (10, 6, 8, 4), 'national_open_run'),
    'founder_run and turn>=7 and !national_run', 2300, 'initiative', 'national_run')

add('late_payment', 'payoff', '财务总监',
    '大客户拖了九十天，电话还在响。',
    option('保理拿钱', '钱少一点，工资准时。', (-7, 0, 0, -2), 'invoice_run'),
    option('亲自催款', '客户分期，第一笔今天到账。', (17, -2, -4, 4), 'collect_run'),
    'national_run and age_national>=3', 2700, 'payoff', 'receivable_run')

add('customer_reorg', 'payoff', '大客户财务',
    '客户申请重组，欠款只认六成。',
    option('拿现款六成', '少拿一点，现金活了。', (15, 2, -6, 1), 'credit_good_run'),
    option('拿仓库抵债', '仓库归你，货却卖不出去。', (5, -3, 5, -2), 'warehouse_debt_run'),
    'receivable_run and age_national>=5', 2500, 'payoff', 'receivable_done_run')

add('factory_expansion', 'power', '厂长',
    '订单排到明年，隔壁工厂正好要卖。',
    option('买下工厂', '厂房到手，旧债也到手。', (-18, 8, 14, 3), 'factory_buy_run'),
    option('只租半年', '产能够用，现金还在。', (-7, 2, 10, 1), 'factory_rent_run'),
    'founder_run and turn>=8 and !factory_run', 1900, 'initiative', 'factory_run')

add('factory_debt', 'payoff', '旧厂老板',
    '工厂交割了，工人的工资还欠三个月。',
    option('我来补发', '工人留下，供应商也愿意等。', (-16, 13, 4, -2), 'fair_pay_run and fair_pay_keep'),
    option('按合同切割', '钱省下了，人开始找下家。', (8, -11, -5, 4), 'labor_cut_run'),
    'factory_buy_run and age_factory>=3', 2600, 'payoff', 'factory_done_run')

add('star_sales', 'venture', '猎头',
    '对手的销售冠军来找你，要现金和决策权。',
    option('重金挖来', '他带走客户，也带来客户。', (-14, 9, 17, 3), 'star_hire_run'),
    option('提拔自己人', '老员工接住了大客户。', (7, 10, 9, -1), 'star_promote_run'),
    'founder_run and turn>=9 and !star_run', 1900, 'venture', 'star_run')

add('star_demand', 'payoff', '销售冠军',
    '我带来的大客户，要我单独算账。',
    option('给他分成', '分成写进合同，客户没走。', (-9, 10, 12, -2), 'commission_run'),
    option('统一归公司', '他留下，客户开始慢慢流失。', (8, -7, -8, 5), 'star_control_run'),
    'star_hire_run and age_star>=3', 2500, 'payoff', 'star_done_run')

add('star_promote_result', 'payoff', '销售总监',
    '你提拔的人，先要一笔签字费。',
    option('给他分成', '老客户留下，团队也学会卖。', (-6, 8, 11, 2), 'commission_run'),
    option('只给奖金', '人留下，客户归公司。', (8, -5, -3, 4), 'star_control_run'),
    'star_promote_run and age_star>=3', 2500, 'payoff', 'star_done_run')

add('partner_power', 'venture', '合伙人 · {maker}',
    '第二款爆品是他做的，股份怎么分？',
    option('给股份和投票权', '他拿到股份，也拿到一票。', (-8, 11, 8, -4), 'partner_equal_run'),
    option('给奖金不分权', '奖金到账，他开始看招聘网站。', (12, -8, 6, 6), 'partner_control_run'),
    'founder_run and turn>=10 and !partner_run', 1900, 'venture', 'partner_run')

add('partner_free_result', 'payoff', '合伙人 · {maker}',
    '他拿到股份，第一件事是要你签授权。',
    option('让他独立开线', '新业务跑起来，董事会多一张票。', (10, 13, 10, -3), 'partner_done_run'),
    option('我来盯预算', '他没走，报表开始每周更新。', (7, 6, 4, 4), 'partner_done_run'),
    'partner_equal_run and age_partner>=3', 2500, 'payoff')

add('partner_control_result', 'payoff', '合伙人 · {maker}',
    '他要的不是奖金，是董事会里那把椅子。',
    option('给他董事席', '椅子给了，产品线也保住了。', (-8, 12, 7, -4), 'partner_done_run'),
    option('让他带队走', '你保住品牌，也投资了一个对手。', (6, -15, 2, 7), 'partner_left_run and rival_keep and partner_done_run'),
    'partner_control_run and age_partner>=3', 2500, 'payoff')

add('buy_company', 'venture', '收购顾问',
    '同行现金流断了，整家公司只卖一块钱。',
    option('整家买下', '一块钱买来客户、合同和三箱文件。', (-15, 12, 8, 3), 'buy_whole_run'),
    option('只买团队', '人来了，旧合同没跟来。', (-10, 10, 1, 4), 'buy_team_run'),
    'founder_run and turn>=11 and !buy_run', 2000, 'venture', 'buy_run')

add('buy_whole_result', 'payoff', '法务总监',
    '收购合同里，还藏着一批未交付订单。',
    option('接下旧单', '旧客户留下，新客户也敢签了。', (-14, 8, 12, 2), 'buy_done_run and fair_pay_run'),
    option('只留赚钱的', '现金保住了，旧客户把你告上法庭。', (9, -7, -9, 5), 'buy_done_run and legal_run'),
    'buy_whole_run and age_buy>=3', 2600, 'payoff')

add('buy_team_result', 'payoff', '新团队负责人',
    '他们带来的代码，和你的产品完全不兼容。',
    option('停线重写', '进度慢了，系统终于统一。', (-9, 11, 4, -2), 'buy_done_run'),
    option('先拼起来卖', '版本按时上线，客服先忙起来。', (13, -5, 8, -5), 'buy_done_run'),
    'buy_team_run and age_buy>=3', 2600, 'payoff')

add('legal_claim', 'payoff', '法务总监',
    '被你留下的旧客户，真的起诉了。',
    option('和解，先交货', '钱花了，订单按时交。', (-14, 7, 8, -2), 'legal_settle_run'),
    option('打到底', '律师赢了一轮，客户没回来。', (-6, -3, -10, 6), 'legal_fight_run'),
    'legal_run and age_buy>=5', 2300, 'payoff', 'legal_done_run')

add('investor_offer', 'venture', '大股东',
    '基金要投一亿，条件是两席董事。',
    option('签，先扩张', '钱进账，董事会多了两张嘴。', (24, 4, 17, -7), 'investor_seat_run'),
    option('不签，慢慢赚', '扩张慢了，决策还在你手里。', (-7, 8, 6, 5), 'self_funded_run'),
    'founder_run and turn>=13 and !investor_run', 1900, 'venture', 'investor_run')

add('board_vote', 'payoff', '投资人代表',
    '董事会不让你开新线，却要你立刻增长。',
    option('买回表决权', '钱退回去，方向又回到你手上。', (-21, 4, -2, 10), 'control_back_run'),
    option('换一条更快的线', '旧项目关了，报表终于好看。', (13, -4, 9, -6), 'line_cut_run'),
    'investor_seat_run and age_investor>=3', 2500, 'payoff', 'investor_done_run')

add('valuation_window', 'power', '投行顾问',
    '估值涨了三倍，同行都在套现。',
    option('卖一小部分', '钱落袋，股份还在。', (21, 0, 5, -4), 'secondary_run'),
    option('继续押增长', '估值更高，账上还是一张规划表。', (-5, 5, 14, 7), 'growth_run'),
    'turn>=15 and !valuation_run', 1600, 'initiative', 'valuation_run', 14)

add('media_profile', 'power', '财经记者',
    '记者要写你的传奇，供应商却在催款。',
    option('讲真实账本', '故事不够漂亮，供应商先收到了钱。', (-10, 5, 5, 8), 'credit_good_run and credit_good_keep'),
    option('讲增长曲线', '标题很漂亮，审计开始问细节。', (8, -3, 10, -5), 'audit_run'),
    cooldown=8)

add('audit_follow', 'payoff', '审计师',
    '增长曲线很漂亮，底下的应收账款更漂亮。',
    option('把坏账写清楚', '估值掉了，账终于是真的。', (-12, 4, -6, 8), 'audit_clear_run'),
    option('再等一个季度', '股价没掉，现金先掉了。', (7, -4, 4, -8), 'audit_delay_run'),
    'audit_run and age_audit>=2', 2200, 'payoff')

add('founder_dinner', 'power', '同行老板',
    '饭局上人人问你，下一步会不会卖掉公司。',
    option('聊客户', '没人敬酒，两个采购留下来。', (12, 2, 15, 4), 'circle_sales_run'),
    option('先放出估值', '报价传开了，三个人来问下一轮。', (18, 0, 7, 5), 'circle_fund_run'),
    'deal_channel_run and turn>=6', 850, 'initiative', 'circle_event_run', 12)

add('supplier_game', 'power', '供应商老板',
    '供应商又涨价，说不涨就停供。',
    option('先付半年款', '价格锁住，工厂愿意替你排产。', (-14, 7, 8, 3), 'credit_good_run and credit_good_keep'),
    option('换一家试试', '报价便宜，第一批货先出了问题。', (9, -4, -7, 5), 'supplier_swap_run'),
    cooldown=7)

add('old_stock', 'power', '仓库主管',
    '旧款堆满仓库，网红却在问价。',
    option('改名收藏款', '库存清了，客户真当限量款买。', (18, 2, -7, -4), 'inventory_clear_run'),
    option('拆了卖零件', '售后省钱，旧客户也回来了。', (8, 7, 5, -1), 'parts_run'),
    cooldown=8)

add('price_raise', 'power', '财务总监',
    '成本涨了，价格还要装没事吗？',
    option('涨价十个点', '销量少了，利润没少。', (16, -2, -6, 4)),
    option('先不涨，抢份额', '订单漂亮，现金流变薄。', (-9, 4, 12, -3)),
    cooldown=7)

add('quality_return', 'power', '售后主管',
    '退货率上来了，问题只在一个零件。',
    option('全批次召回', '钱花了，口碑保住了。', (-17, 9, 7, 5), 'warranty_run'),
    option('只修坏的', '成本省了，论坛先炸了。', (8, -5, -12, -4), 'quality_risk_run'),
    cooldown=8)

add('channel_conflict', 'power', '渠道总监',
    '直营店和经销商，开始互相砍价。',
    option('统一价格', '渠道不高兴，品牌稳住了。', (7, 5, 9, 3)),
    option('谁便宜谁卖', '销量涨了，经销商开始撤。', (12, -4, 5, -3)),
    cooldown=8)

add('regional_deal', 'power', '区域经理',
    '外地团队说总部方法卖不动。',
    option('给预算自己试', '当地签下大单，总部学着改。', (-9, 8, 15, 4), 'regional_run'),
    option('照总部执行', '报表整齐，订单没涨。', (5, -3, -7, 5)),
    cooldown=8)

add('product_bet', 'venture', '产品总监',
    '下一代产品，先做便宜还是做高端？',
    option('做便宜款', '工程师开始拆成本。', (-12, 4, 9, 5), 'bet_cheap_run'),
    option('做高端款', '设计师开始找贵材料。', (-14, 3, 11, 7), 'bet_premium_run'),
    'founder_run and turn>=8 and !bet_run', 1800, 'venture', 'bet_run')

add('bet_cheap_hit', 'payoff', '产品总监',
    '便宜款冲上榜首，同行开始降价。',
    option('再降一点', '销量涨了，利润薄得透光。', (17, -4, 15, 4), 'bet_done_run and bet_hit_keep'),
    option('价格不动', '销量稳住，利润回来了。', (23, 3, 7, -2), 'bet_done_run and bet_hit_keep'),
    'bet_cheap_run and lucky_bet_run and age_bet>=4', 2300, 'payoff')

add('bet_premium_hit', 'payoff', '产品总监',
    '高端款卖空，客户开始排队验资。',
    option('继续加配置', '订单更少，单笔利润更厚。', (21, -5, 11, 5), 'bet_done_run and bet_hit_keep'),
    option('降一级门槛', '更多客户进来，工厂先忙起来。', (13, 6, 14, -3), 'bet_done_run and bet_hit_keep'),
    'bet_premium_run and lucky_bet_run and age_bet>=4', 2300, 'payoff')

add('bet_miss', 'payoff', '财务总监',
    '新产品卖不动，预算只够再赌一次。',
    option('停，保住现金', '样机封存，主力款继续供货。', (13, 4, -4, -5), 'bet_done_run and bet_wait_keep'),
    option('再赌一轮', '你签了字，没人再担保。', (-16, -5, 0, 9), 'bet_done_run and bet_wait_keep'),
    'bet_run and !lucky_bet_run and age_bet>=4', 2300, 'payoff')

add('launch_claim', 'initiative', '公关总监',
    '新款还有缺陷，发布会要延期吗？',
    option('延期，先修好', '发布会空了，老客户反而信你。', (-8, 6, 4, 5), 'honest_launch_run'),
    option('先发预告', '预订单涌来，缺陷也上热搜。', (14, -4, 13, -5), 'hype_debt_keep'),
    'founder_run and turn>=16 and !launch_run', 1700, 'initiative', 'launch_run')

add('launch_follow', 'payoff', '大客户',
    '预告卖爆了，但验货日提前了。',
    option('退订金', '钱退了，客户还给你留门。', (-16, 7, -8, -2), 'launch_clean_run'),
    option('按期交货', '工程师睡在工厂，货终于出门。', (-11, -8, 13, -6), 'launch_debt_run'),
    'hype_debt_keep and launch_run and age_launch>=3', 2500, 'payoff', 'launch_done_run')

add('launch_honest', 'payoff', '老客户',
    '你延期了，客户愿意帮你内测。',
    option('给他优先权', '他拿到首批，也带来同行。', (-7, 6, 16, 4), 'launch_done_run'),
    option('先卖旧款', '现金先回来，发布会再等等。', (15, 2, 4, -2), 'launch_done_run'),
    'honest_launch_run and launch_run and age_launch>=3', 2500, 'payoff')

add('founder_social', 'power', '公关总监',
    '你拒绝收购的截图，已经传遍行业。',
    option('讲客户和产品', '没人鼓掌，但采购商开始问交期。', (-4, 4, 14, 6), 'social_run'),
    option('点名对手降价', '热搜来了，法务也来了。', (9, -3, 11, -5), 'rival_callout_run'),
    'independent_run and turn>=7', 900, 'initiative', cooldown=12)

add('employee_options', 'power', '人事总监',
    '核心员工要期权，不想只拿工资。',
    option('给期权', '工资没涨，人心先稳住。', (-9, 12, 8, 3), 'option_run'),
    option('涨现金工资', '人留下，现金表变薄。', (-16, 10, 7, 1), 'cash_pay_run'),
    cooldown=8)

add('safety_line', 'power', '厂长',
    '安全员说，夜班再开就要出事。',
    option('停线检查', '少交一单，没少一个人。', (-13, 8, -5, 6), 'safety_run'),
    option('继续赶货', '货出了，工伤也上新闻。', (11, -12, 4, -8), 'safety_risk_run'),
    cooldown=8)

add('customer_data', 'power', '法务总监',
    '客户数据能卖，平台报价很高。',
    option('不卖，做服务', '钱慢一点，客户愿意续费。', (-6, 4, 11, 5), 'privacy_run'),
    option('卖一次补现金', '现金到了，客户开始问注销。', (19, -3, -12, -5), 'data_sale_run'),
    cooldown=10)

add('regional_store', 'power', '区域经理',
    '空门店很便宜，但离总部很远。',
    option('给他自己试', '当地团队签下大单。', (-9, 7, 14, 3), 'regional_run'),
    option('总部直接接管', '报表整齐，店里没客。', (5, -4, -8, 6)),
    cooldown=8)

add('board_packet', 'power', '董事会秘书',
    '董事会要增长，客户却要退款。',
    option('先解决退款', '数字难看，客户没离开。', (-12, 6, 5, 7), 'customer_first_run'),
    option('先交增长计划', '报告准时，客服熬到凌晨。', (8, -6, 9, -6), 'growth_first_run'),
    cooldown=8)

add('founder_visit', 'power', '销售总监',
    '你一年没见过真实客户了。',
    option('去门店站一天', '卖出三台，也听到十条抱怨。', (-3, 3, 12, 9), 'customer_visit_run'),
    option('让销售写报告', '报告完整，客户还是没见你。', (5, -2, 4, -5)),
    cooldown=7)

add('public_contract', 'power', '法务总监',
    '对手把你的合同模板发到全行业。',
    option('公开更好的版本', '同行照抄，客户开始找你。', (-7, 4, 14, 6), 'contract_standard_run'),
    option('发律师函', '律师赚到了，客户没多一个。', (9, -2, -5, 4), 'legal_notice_run'),
    cooldown=10)

add('founder_speech', 'breather', '财经记者',
    '采访要你讲一次失败。',
    option('讲现金断过', '标题很难看，供应商先放心。'),
    option('讲增长三倍', '标题很好看，财务开始补材料。'),
    'turn>=3', 170, 'expression')

add('office_move', 'breather', '行政总监',
    '办公室要搬进最贵的楼吗？',
    option('先别搬', '省下的钱够多招两个人。'),
    option('搬，客户会来', '客户来了，问你为何不扩招。'),
    'turn>=3', 170, 'expression')

add('award_dinner', 'breather', '行业协会',
    '奖杯没刻字，同行让你选。',
    option('增长最快', '同行鼓掌，财务先叹气。'),
    option('最会活下来', '没人鼓掌，供应商笑了。'),
    'turn>=3', 170, 'expression')

add('risk_money', 'pressure', '财务总监',
    '工资只够发一半，现金还在客户账上。',
    option('卖掉个人股份', '你少了一点控制权，工资准时发。', (26, 4, -5, -4), 'risk_money_run'),
    option('把应收卖掉', '少拿一点，先把工资发了。', (22, 1, 1, -2), 'risk_money_run'),
    'money<=18 and !risk_money_run', 90000, 'crisis', 'risk_money_run')

add('bridge_credit', 'pressure', '供应商老板',
    '账上见底，你以前的货款都按时付了。',
    option('赊一个月', '他先发货，财务终于松气。', (28, 5, 5, 2), 'credit_rescue_run'),
    option('签长期单', '他让了价，产线重新开。', (23, 2, 8, 1), 'credit_rescue_run'),
    'money=0 and credit_good_run and !credit_rescue_run', 100000, 'crisis')

add('credit_control', 'payoff', '供应商老板',
    '账期救了你，他要进董事会。',
    option('给观察席', '货不断，表决权少一票。', (-3, 6, 7, -3), 'supplier_seat_run'),
    option('换供应商', '控制权还在，产线先停。', (-8, -2, -10, 5), 'supplier_exit_run'),
    'credit_rescue_run and age_credit_rescue>=2', 3000, 'payoff', 'credit_control_run and credit_control_done_run')

add('supplier_vote', 'payoff', '供应商代表',
    '他不懂产品，却有一张董事票。',
    option('给他看账', '他看懂现金流，投了你的票。', (-4, 5, 5, 4), 'supplier_vote_run'),
    option('拉客户进来', '董事会多一张票，账期少一周。', (7, 2, 8, -2), 'customer_vote_run'),
    'supplier_seat_run and credit_control_run and age_credit_control>=3', 2600, 'payoff')

add('risk_team', 'pressure', '人事总监',
    '核心员工要走，离职信已经打印好了。',
    option('发利润分成', '分成到账，辞职信被撕了。', (-12, 29, -5, -4), 'risk_team_run and fair_pay_run and fair_pay_keep'),
    option('砍掉亏钱线', '少一条业务，人先留下。', (4, 22, -9, -5), 'risk_team_run'),
    'team<=20 and !risk_team_run', 90000, 'crisis', 'risk_team_run')

add('bridge_team', 'pressure', '老员工代表',
    '人都走光了，留下的人愿意回来帮你。',
    option('给旧团队股份', '他们回来，先把客户接住。', (2, 28, 6, 4), 'team_rescue_run'),
    option('先发三个月工资', '人回来了，扩张先暂停。', (-8, 23, 2, 1), 'team_rescue_run'),
    'team=0 and fair_pay_keep and !team_rescue_run', 100000, 'crisis')

add('risk_market_low', 'pressure', '销售总监',
    '一周只卖一台，买家还是你的亲戚。',
    option('老客换新', '门店重新排队，亲戚要补差价。', (-10, -3, 27, 5), 'customer_oath_run'),
    option('带样机拿大单', '你守住采购，机器卖出去了。', (5, 2, 23, 3), 'customer_oath_run'),
    'market<=15 and !risk_market_low_run', 90000, 'crisis', 'risk_market_low_run')

add('bridge_market', 'pressure', '老客户',
    '货架空了，老客户说愿意帮你重新铺货。',
    option('先发旧款', '旧款回到货架，新款有时间修。', (4, 3, 27, 2), 'market_rescue_run'),
    option('给老客独家', '渠道回来了，价格也被锁住。', (-4, 1, 23, 5), 'market_rescue_run'),
    'market=0 and customer_oath_run and !market_rescue_run', 100000, 'crisis')

add('risk_market_high', 'pressure', '厂长',
    '订单做不完，退款排队比抢购还长。',
    option('关预售，先交货', '按钮关了，旧单开始出厂。', (-6, 7, -30, -5), 'risk_market_high_run'),
    option('找同行代工', '利润分了，客户总算收到货。', (-11, 4, -27, -3), 'risk_market_high_run'),
    'market>=85 and !risk_market_high_run', 90000, 'crisis', 'risk_market_high_run')

add('market_overflow', 'pressure', '厂长',
    '订单冲到顶，工厂已经塞不下了。',
    option('关预售，先交货', '按钮关了，旧单一车车出厂。', (-7, 8, -34, -4), 'market_overflow_run'),
    option('分给同行做', '利润少了，交期终于保住。', (-12, 5, -29, -2), 'market_overflow_run'),
    'market=100 and !market_overflow_run', 100000, 'crisis')

add('risk_mind_low', 'pressure', '产品总监',
    '你只看报表，已经没人问你意见了。',
    option('去车间拆一台', '你拆到天亮，没问利润率。', (-9, 4, -4, 26), 'product_touch_run'),
    option('去门店卖一台', '客户骂了两句，你当场改机。', (6, 0, 5, 22), 'product_touch_run'),
    'mind<=18 and !risk_mind_low_run', 90000, 'crisis', 'risk_mind_low_run')

add('bridge_mind', 'pressure', '产品总监',
    '你停了手，产品总监把旧样机送回来了。',
    option('重新做它', '没人催融资，样机先活了。', (-8, 5, 7, 28), 'mind_rescue_run'),
    option('带它见客户', '客户一句抱怨，让你又有主意。', (8, 2, 11, 23), 'mind_rescue_run'),
    'mind=0 and product_touch_run and !mind_rescue_run', 100000, 'crisis')

add('risk_mind_high', 'pressure', '董事会秘书',
    '没人敢反对你，会议只剩下点头。',
    option('先听反对票', '第一票说：别再折腾了。', (4, 8, -5, -30), 'risk_mind_high_run'),
    option('锁公章一晚', '计划少了三个零，终于能执行。', (-3, 5, -2, -27), 'risk_mind_high_run'),
    'mind>=85 and !risk_mind_high_run', 90000, 'crisis', 'risk_mind_high_run')

add('mind_overflow', 'pressure', '董事会秘书',
    '你又有十个点子，团队只想先做完一个。',
    option('砍掉九个', '白板清空，主线终于交付。', (4, 7, 4, -36), 'mind_overflow_run'),
    option('只留一个试验', '其他想法入库，团队松了口气。', (-4, 4, 7, -31), 'mind_overflow_run'),
    'mind=100 and !mind_overflow_run', 100000, 'crisis')

add('cash_out', 'exit', '收购方',
    '公司我买，连你的麻烦一起买。',
    option('拿钱走人', '收购款到账，麻烦换了老板。', flags='end_sold'),
    option('我还没做完', '报价退回，团队继续等你拍板。', (-3, 4, 0, 5)),
    'money>=65 and turn>=16', 140, 'initiative', cooldown=18)

add('hand_over', 'exit', '合伙人 · {maker}',
    '公司能自己跑了，你要把椅子交出来吗？',
    option('交给你', '你走到门口，没人追出来。', flags='end_next'),
    option('一起管', '两张椅子，两个签字人。', (5, 8, 0, -10)),
    'partner_done_run and team>=65 and turn>=17', 140, 'initiative', cooldown=20)

add('take_break', 'exit', '助理',
    '工作群静音三天，你真想休息？',
    option('找人接手', '工作手机交出去，闹钟全关了。', flags='end_pause'),
    option('换个项目', '新样机进门，工作群重新响了。', (-8, 5, -4, 20)),
    'mind<=27 and turn>=16', 140, 'initiative', cooldown=14)

add('legacy_rival', 'legacy', '对手 · {rival}',
    '上次你把我逼走，这次我来抢你的客户。',
    option('放马过来', '两家公司把报价发给了同一个客户。', (8, -3, 8, 4), 'legacy_seen_run'),
    option('合并，别折腾', '两块招牌合成一块，客户没搬家。', (13, 4, -3, -5), 'legacy_seen_run'),
    'dynasty>1 and rival_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff')

add('legacy_paid', 'legacy', '猎头',
    '上家公司奖金发够了，老员工还记得。',
    option('整个队都来', '他们带着旧工牌，来领新的。', (-7, 18, 3, 3), 'legacy_seen_run'),
    option('先来三个人', '三个人先到，客户没等太久。', (-4, 11, 4, -2), 'legacy_seen_run'),
    'dynasty>1 and fair_pay_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff')

add('legacy_credit', 'legacy', '供应商老板',
    '上次你按时付钱，这次他愿意先发货。',
    option('照旧合作', '账期还在，产线先开。', (12, 5, 8, 3), 'legacy_seen_run'),
    option('签长期价', '价格锁住，扩张慢一点。', (16, 2, 4, -2), 'legacy_seen_run'),
    'dynasty>1 and credit_good_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff')

add('legacy_bet', 'legacy', '技术买家',
    '上次没做成的产品，现在有人想买技术。',
    option('只卖授权', '旧项目终于赚钱了。', (19, 0, 4, 3), 'legacy_seen_run'),
    option('收钱再开工', '订金到账，样机重新通电。', (12, 6, 7, 5), 'legacy_seen_run'),
    'dynasty>1 and bet_wait_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff')

add('legacy_sold', 'legacy', '投资人',
    '上家公司卖得不错，这家还要卖吗？',
    option('条件我来开', '她先拿你的条件回去谈。', (15, 0, 7, 5), 'legacy_seen_run'),
    option('先看产品', '她放下估值表，拿起了样机。', (5, 4, 3, -4), 'legacy_seen_run'),
    'dynasty>1 and last_sold_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff')

add('legacy_failed', 'legacy', '财务总监',
    '这次先留工资，别把保险柜也卖了。',
    option('留三个月', '工资锁好了，扩张慢一点。', (10, 9, -5, -4), 'legacy_seen_run'),
    option('先做赚钱的单', '场面小了，欠条也少了。', (14, 0, -8, 2), 'legacy_seen_run'),
    'dynasty>1 and last_failed_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff')

ENDINGS = {
    'closed': dict(title='现金断了', label='资金耗尽', body='工资发不出，供应商也不赊账。\n公司停了。', flag='last_failed_keep'),
    'alone': dict(title='创始人独角戏', label='团队耗尽', body='人走光了。\n你签下的订单，没人做。', flag='last_failed_keep'),
    'forgotten': dict(title='货架撤空', label='客户耗尽', body='最后一家门店撤了货。\n公司还在，客户没了。', flag='last_failed_keep'),
    'overload': dict(title='爆单之后', label='交付失控', body='订单越接越多，货却交不出。\n退款把公司拖垮了。', flag='hype_debt_keep'),
    'hollow': dict(title='最后一票', label='心气耗尽', body='公司还在。\n这次，你把工作群真的退了。', flag='last_failed_keep'),
    'allin': dict(title='方向被拿走', label='心气失控', body='你说再赌一次。\n银行说，这是最后一次。', flag='last_failed_keep'),
    'sold': dict(title='卖掉了公司', label='主动出售公司', body='收购款到账。\n交接清单比收购款还厚。', flag='last_sold_keep', win=True),
    'next': dict(title='交棒', label='主动交棒', body='你离开公司，没人拦。\n他们真的能自己干了。', win=True),
    'pause': dict(title='先休息', label='主动离开', body='接手的人来了。\n你第一次把闹钟全部关掉。'),
}


def export():
    with (HERE / 'cards.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, delimiter=';')
        writer.writeheader()
        writer.writerows(CARDS)
    story_data = dict(credit='GPT 6 Astra', edition='real-business-2', cards=META, endings=ENDINGS)
    (HERE / 'story-meta.json').write_text(json.dumps(story_data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sections = ['# 创始人 · GPT 6 Astra 作品', '', '产品已经卖爆。接下来是收购、产能、价格战、现金流、控制权和危机。', '',
                '每张卡只提一件具体的事；选择的后果会在几张卡后回来。没有固定任期，能经营就继续。', '']
    for card in CARDS:
        sections.extend([f"## {card['card']} · {card['bearer']}", '', card['question'].replace('\n', '  \n'), '',
                         f"- ← **{card['override_no']}**：{card['answer_no']}",
                         f"- → **{card['override_yes']}**：{card['answer_yes']}", '',
                         f"条件：{card['conditions']}；冷却：{card['lockturn']}", ''])
    sections.extend(['## 结局', ''])
    for ending in ENDINGS.values():
        sections.extend([f"### {ending['title']}", '', ending['label'], '', ending['body'], ''])
    (HERE / '故事手册.md').write_text('\n'.join(sections), encoding='utf-8')
    print(f'卡组 {len(CARDS)} 张；可循环经营卡 {sum(card["lockturn"] != "del" for card in CARDS)} 张；结局 {len(ENDINGS)} 种。')


if __name__ == '__main__':
    export()
