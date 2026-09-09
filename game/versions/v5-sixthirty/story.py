"""GPT 6 Astra 作品：短卡商业荒诞喜剧，沿用原版 22 列格式。"""
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
    if '{maker}' in bearer + question + left['reply'] + right['reply'] and theme != 'legacy':
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


add('first_move', 'opening', '发布会现场',
    '发布会上，机器人当众叫你骗子。',
    option('让它说完', '它开始逐个点评台下的股东。', (-5, 6, 14, 5), 'mouth_open_run'),
    option('拔电源', '备用电池启动：老板，你急了？', (-4, -3, 6, 7), 'mouth_cut_run'),
    'turn=1', 900000, shared='scandal_run')

add('mouth_fans', 'payoff', '公关总监',
    '你让它骂完，观众开始催付费版。',
    option('骂人也收费', '它骂得越贵，客户越觉得值。', (16, -2, 9, 1), 'roast_product_run'),
    option('让它骂对手', '对手的员工，全点了关注。', (-3, 4, 10, 5), 'roast_rival_run'),
    'mouth_open_run and age_scandal>=1', 2400, 'payoff')

add('battery_live', 'payoff', '技术总监',
    '你拔了电，它开始直播你的搜索记录。',
    option('承认是我', '热搜第一：老板也搜怎么装忙。', (6, 8, 7, -5), 'confession_run and honest_keep'),
    option('甩锅黑客', '全网开始替你找这个黑客。', (5, -6, 5, 6), 'hacker_lie_run'),
    'mouth_cut_run and age_scandal>=1', 2400, 'payoff')

add('roast_children', 'payoff', '客服主管',
    '付费骂人卖爆了，儿童模式也在骂。',
    option('立刻退款', '退款很疼，家长撤了投诉。', (-12, 5, -10, -4)),
    option('让它骂作业', '它骂哭了出题人，家长下单了。', (12, -3, 8, 4), 'roast_keep'),
    'roast_product_run and age_scandal>=3', 2300, 'payoff', 'scandal_done_run')

add('roast_rival_reply', 'payoff', '销售总监',
    '被你骂的对手，要买断全部骂人机。',
    option('价格翻倍', '他买走机器，也买走了骂声。', (20, 3, -8, -2)),
    option('留一台直播', '他付了钱，你还留着麦。', (8, -3, 12, 7), 'roast_keep'),
    'roast_rival_run and age_scandal>=3', 2300, 'payoff', 'scandal_done_run')

add('confession_reply', 'payoff', '员工代表',
    '你承认会装忙，员工想跟你学。',
    option('开课，收钱', '第一排坐满了同行老板。', (15, -3, 8, 4)),
    option('都别装了', '周报砍到一行，活反而干完了。', (5, 12, -5, -6)),
    'confession_run and age_scandal>=3', 2300, 'payoff', 'scandal_done_run')

add('hacker_exposure', 'payoff', '实习生',
    '你甩锅的黑客，就是给你修电脑的我。',
    option('转正，别说了', '他当天转正，工资比你还敢开。', (-10, 9, -5, -5)),
    option('那就直播对质', '他投屏了记录：老板让我甩锅。', (6, -9, 12, 6), 'blame_keep'),
    'hacker_lie_run and age_scandal>=3', 2300, 'payoff', 'scandal_done_run')

add('board_robot', 'venture', '大股东',
    '机器人不领工资，让它当CEO？',
    option('试一天', '它裁了董事会，给员工涨工资。', (-10, 12, 0, -8), 'robot_ceo_run'),
    option('我才是老板', '它不抢你的椅子，改去拉员工票。', (5, -7, 3, 8), 'robot_union_run'),
    'scandal_done_run and age_scandal>=5', 1800, shared='board_run')

add('robot_nightshift', 'payoff', '机器人CEO',
    '我给你排了夜班，老板要带头。',
    option('我去', '你上了流水线，全厂给你打卡。', (-2, 12, 4, -8), 'robot_worker_run'),
    option('格式化它', '它没再说话，员工也安静了。', (-8, -12, -9, 8), 'robot_wiped_keep and robot_wiped_run'),
    'robot_ceo_run and age_board>=2', 2200, 'payoff')

add('robot_union', 'payoff', '人事总监',
    '你挡了它当CEO，它当上了工会主席。',
    option('谈条件', '它要双休，连充电器也要。', (-6, 14, -5, -5), 'robot_union_deal_run'),
    option('送去对手家', '对手发来喜报，半夜又打来求救。', (10, -7, 7, 6), 'robot_sent_run'),
    'robot_union_run and age_board>=2', 2200, 'payoff')

add('nightshift_fame', 'payoff', '直播导演',
    '你上夜班火了，粉丝要看你连轴转。',
    option('招人替我', '招工广告爆了，你终于能下班。', (-12, 14, -5, -3)),
    option('付费看我下班', '你关灯那一刻，直播收入破纪录。', (17, 5, -8, -6), 'boss_show_keep'),
    'robot_worker_run and age_board>=5', 2200, 'payoff', 'board_done_run')

add('reboot_crowdfund', 'payoff', '公关总监',
    '你刚格式化它，用户就众筹要复活。',
    option('卖复刻版', '新机第一句：这次谁替我签合同？', (15, -2, 7, 0), 'robot_reborn_keep'),
    option('花钱买安静', '众筹退了，机器终于只会扫地。', (-14, 6, -13, -8)),
    'robot_wiped_run and age_board>=5', 2200, 'payoff', 'board_done_run')

add('union_bill', 'payoff', '大股东',
    '你答应全厂双休，我的分红呢？',
    option('我也双休', '员工鼓掌，股东鼓起了腮帮子。', (-5, 10, -4, -8)),
    option('轮休，厂不停', '机器换着充电，股东照常收钱。', (12, 7, 5, 2)),
    'robot_union_deal_run and age_board>=5', 2200, 'payoff', 'board_done_run')

add('robot_return', 'payoff', '对手老板',
    '你送的机器人，把我裁了。领回去！',
    option('先付赎金', '他转了钱，备注：请别再寄。', (20, 7, -4, -4), 'robot_rival_keep'),
    option('再寄三台', '他连夜修改了公司的收货地址。', (10, -3, 11, 6), 'robot_rival_keep'),
    'robot_sent_run and age_board>=5', 2200, 'payoff', 'board_done_run')

add('partner_power', 'venture', '合伙人·{maker}',
    '爆款是我做的，采访全写你的名字。',
    option('头版给你', '他拿走采访稿，把你从家属栏删了。', (-5, 10, 4, -5), 'partner_free_run'),
    option('老板就是我', '他把老板群改名：老板一个人的群。', (5, -10, 0, 7), 'partner_control_run'),
    'board_done_run and turn>=9', 280, shared='partner_run')

add('partner_free_result', 'payoff', '合伙人·{maker}',
    '我上了封面，他们管你叫投资人。',
    option('分红别忘我', '他递来利润表，厚得能垫桌脚。', (17, 10, -4, -6), 'partner_equal_run'),
    option('下场一起上', '两张椅子，两个人都没坐正中间。', (10, 8, 6, -3), 'partner_equal_run'),
    'partner_free_run and age_partner>=3', 2100, 'payoff', 'partner_done_run')

add('partner_control_result', 'payoff', '合伙人·{maker}',
    '功劳全归你？那我另开发布会了。',
    option('分权，回来', '他把辞职信改成了合伙人协议。', (-9, 15, 0, -9), 'partner_equal_run'),
    option('走，算我投资', '你投出了第一家专门打你的公司。', (-8, -16, 5, 5), 'partner_left_run and rival_keep'),
    'partner_control_run and age_partner>=3', 2100, 'payoff', 'partner_done_run')

add('buy_company', 'venture', '收购顾问',
    '同行挂牌一元，包邮送创始人。',
    option('整家买下', '一元付了，合同足足送来三箱。', (-14, 13, 6, 5), 'buy_whole_run'),
    option('只要工程师', '人来了，创始人在楼下问要不要他。', (-10, 11, -2, 2), 'buy_team_run'),
    'board_done_run and turn>=10', 280, shared='buy_run')

add('buy_landlord', 'payoff', '旧老板',
    '你买的那家公司，房租交到我这里。',
    option('房子也买了', '房产证换了，他改口叫你房东。', (-17, 7, 4, 8)),
    option('请来当催租员', '他拿两份钱，但每周得向你汇报。', (13, 4, -6, -4)),
    'buy_whole_run and age_buy>=3', 2100, 'payoff', 'buy_done_run')

add('buy_team_result', 'payoff', '新研发组',
    '旧代码全用你名字命名，删得下手吗？',
    option('删了重写', '名字没了，机器快了三倍。', (-7, 12, 4, -3)),
    option('申请专利', '同行交起了你的姓名使用费。', (16, -5, 7, 6)),
    'buy_team_run and age_buy>=3', 2100, 'payoff', 'buy_done_run')

add('bet_start', 'venture', '技术总监',
    '下一代机器人，靠什么卖爆？',
    option('替老板开会', '会议室先订了，人不用来了。', (-12, 3, 0, 8), 'bet_meeting_run'),
    option('帮员工摸鱼', '全公司自愿报名内测。', (-10, 5, 0, 6), 'bet_slack_run'),
    'board_done_run and turn>=10', 280, shared='bet_run')

add('bet_meeting_hit', 'payoff', '技术总监',
    '会议机卖爆了，互相开了一整夜会。',
    option('按小时收费', '会议越没结论，你赚得越多。', (20, -3, 7, 4), 'bet_hit_keep'),
    option('推出散会键', '最贵的配件，只有一个按钮。', (18, 9, -8, -4), 'bet_hit_keep'),
    'bet_meeting_run and lucky_bet_run and age_bet>=4', 2300, 'payoff', 'bet_done_run')

add('bet_slack_hit', 'payoff', '销售总监',
    '摸鱼机卖爆了，买家全是公司老板。',
    option('加老板套餐', '基础版装忙，老板版替你开会。', (23, 3, 4, 4), 'bet_hit_keep'),
    option('替他们上班', '人都不来了，公司却照常赚钱。', (16, -5, 12, 6), 'bet_hit_keep'),
    'bet_slack_run and lucky_bet_run and age_bet>=4', 2300, 'payoff', 'bet_done_run')

add('bet_miss', 'payoff', '技术总监',
    '新样机跑了，桌上留着一封辞职信。',
    option('卖它的辞职信', '机器没卖掉，周边先回了本。', (10, 4, -3, -6), 'bet_wait_keep and bet_done_run'),
    option('返聘它', '它回来了，要求签无加班合同。', (-10, 9, 4, -5), 'bet_rehire_run'),
    'bet_run and !lucky_bet_run and age_bet>=4', 2300, 'payoff')

add('bet_rehire', 'payoff', '返聘的机器人',
    '我带了三个朋友，它们原厂倒闭了。',
    option('一起拆机直播', '拆到第三台，同行开始买门票。', (15, 5, 9, 4), 'bet_wait_keep'),
    option('都来上班', '新员工不用工位，只要插座。', (7, 12, -4, -3), 'bet_wait_keep'),
    'bet_rehire_run and age_bet>=7', 2300, 'payoff', 'bet_done_run')

add('zoo_payment', 'venture', '大客户',
    '现金没有，拿我的动物园抵货款？',
    option('动物园也收', '货发出去了，财务领回一只鹦鹉。', (-7, 3, 8, 6), 'zoo_run'),
    option('只收现金', '他卖了年票，把钱凑齐了。', (15, 0, -7, -3)),
    'board_done_run and turn>=10', 260)

add('parrot_sales', 'payoff', '销售总监',
    '你收的动物园，鹦鹉最会卖货。',
    option('让它直播', '它只会喊打钱，销售额却第一。', (20, -3, 10, 3), 'parrot_keep'),
    option('教它催尾款', '客户忍了三天，把欠款付清了。', (23, 5, -8, -3), 'parrot_keep'),
    'zoo_run and age_zoo>=3', 2100, 'payoff')

add('investor_power', 'venture', '大股东',
    '我给你一亿，但老板椅得换成我的。',
    option('钱先到账', '椅子换了，公章还在你兜里。', (23, 2, 9, -8), 'investor_seat_run'),
    option('我站着也能干', '融资撤了，员工把椅子抬了回来。', (-8, 9, -6, 5), 'self_funded_run'),
    'board_done_run and turn>=12', 260, shared='investor_run')

add('investor_return', 'payoff', '大股东',
    '我坐了老板椅，怎么没人听我的？',
    option('买回她的股份', '钱退了，椅子她说要留作纪念。', (-20, 5, -4, 12), 'control_back_run'),
    option('先去车间一周', '她干了三天，决定只拿分红。', (14, 8, -6, -9), 'investor_worker_keep'),
    'investor_seat_run and age_investor>=3', 2100, 'payoff')

add('fake_orders', 'venture', '财务总监',
    '机器人刷了三百单，收货人全是你。',
    option('全退，别吹了', '榜单掉了，仓库不用假装发货了。', (-10, 7, -12, -6)),
    option('算团购业绩', '你登顶销量榜，平台来验仓了。', (12, -5, 14, 6), 'fake_orders_run and hype_debt_keep'),
    'board_done_run and turn>=9', 270)

add('fake_orders_audit', 'payoff', '平台稽核',
    '三百单全寄老板家，您家开商场？',
    option('退钱认罚', '钱退了，销量榜也把你退下来了。', (-17, 7, -18, -6), '!hype_debt_keep'),
    option('真开一家店', '客厅开业，老板娘当上了店长。', (-14, 5, -8, 6), '!hype_debt_keep and home_store_keep'),
    'fake_orders_run and age_fake_orders>=3', 2200, 'payoff')

add('rival_copy', 'power', '市场总监',
    '对手抄错图，把你的二维码印上去了。',
    option('替他买广告', '广告他出镜，订单进你账。', (17, -3, 11, 4)),
    option('收广告费', '对手花钱请你别再转发。', (21, 3, -8, -4)),
    cooldown=9)

add('factory_face', 'power', '厂长',
    '代工厂把你的脸，印在了垃圾桶上。',
    option('限量款，涨价', '越有人骂，垃圾桶越缺货。', (16, -3, 9, 5)),
    option('全部重做', '你的脸没了，质检多了一道工序。', (-9, 10, -7, -4)),
    cooldown=10)

add('wedding_orders', 'power', '销售总监',
    '客户堵到你婚礼上，问机器何时发货。',
    option('现场退钱', '礼金还没拆，先赔出去一半。', (-10, 7, -15, -6)),
    option('伴手礼送机器', '客户没走，坐下来随了份子。', (11, -5, 7, 6)),
    cooldown=18)

add('self_warranty', 'power', '客服主管',
    '旧款过保了，居然给自己买了保险。',
    option('卖延保服务', '它还替邻居家的机器买了一份。', (15, 2, -6, -4)),
    option('免费修它', '维修视频火了，旧客户又回来了。', (-7, 9, 10, 3)),
    cooldown=8)

add('influencer_returns', 'power', '销售总监',
    '主播卖光了你的货，又全退回来了。',
    option('扣他的佣金', '佣金拿回来了，主播拉黑了你。', (16, 3, -14, 4)),
    option('自己开直播', '你蹲仓库拆退货，弹幕开始加单。', (8, -6, 12, 6)),
    cooldown=9)

add('ceo_double', 'power', '助理',
    '替你应酬的机器人，比你更像老板。',
    option('让它多去', '大单签了，它也签了你的体检单。', (14, 5, 4, -10)),
    option('我去见客户', '客户看你两眼，问要不要充电。', (7, 3, -4, 13)),
    cooldown=7)

add('charger_union', 'power', '厂长',
    '全厂机器统一弹窗：先交电费。',
    option('交，别废话', '灯亮了，生产线一起假装没事。', (-9, 14, -8, -5)),
    option('换便宜电网', '电费省了，开机铃变成了广告。', (12, -5, 4, 5)),
    cooldown=8)

add('locked_out', 'power', '保安',
    '门禁到点就锁，老板被关在外面了。',
    option('照常下班', '你第一次和员工一起抢末班车。', (-4, 13, -8, -6)),
    option('拆门赶工', '门拆了，员工把它列进加班账单。', (14, -9, 8, 8)),
    cooldown=7)

add('quality_colleagues', 'power', '质检主管',
    '质检机器人拒绝抽检，说那是同事。',
    option('换人工质检', '同事被拆了，人类领到检测津贴。', (-8, 12, -9, -3)),
    option('给它主管权限', '它开始抽检主管，谁都没躲过去。', (7, -4, 6, 9)),
    cooldown=9)

add('return_customer', 'power', '客服主管',
    '客户要退机器，机器也要求退客户。',
    option('两边都退', '退款了，机器高高兴兴回了仓库。', (-8, 8, -12, -5)),
    option('换个主人', '新客户不挑剔，机器送了他优惠券。', (10, 3, 8, 4)),
    cooldown=6)

add('subscription', 'power', '产品经理',
    '付费功能太多，开机得先看广告。',
    option('再卖免广告', '钱收了，差评区也开始收费吐槽。', (18, -5, -9, -4)),
    option('基础全免费', '客户终于开了机，高配款也卖动了。', (7, 6, 10, 3)),
    cooldown=8)

add('slow_warehouse', 'power', '仓库主管',
    '网红把库存当古董，卖了十倍价。',
    option('改叫收藏款', '旧货出清，每台多了一张证书。', (20, 2, -10, -6)),
    option('拆了卖零件', '原装配件上架，售后排队抢货。', (8, 7, 4, -2)),
    cooldown=8)

add('supplier_game', 'power', '采购主管',
    '供应商都喊亏本，却开着同款豪车。',
    option('请两家来竞价', '他们看了眼对方的车，都降了价。', (12, 2, -3, 4)),
    option('锁一年低价', '合同签了，豪车没再换过。', (8, 6, 2, -5)),
    cooldown=7)

add('red_envelopes', 'power', '人事总监',
    '年终奖太薄，员工拼成了辞职二字。',
    option('加钱，别拼了', '钱到账了，辞职被拼成了谢谢。', (-11, 18, -5, -4), 'paid_keep'),
    option('分产品利润', '他们连夜拆成本，奖金自己挣。', (9, 10, -4, -7), 'paid_keep'),
    cooldown=9)

add('big_order', 'power', '大客户',
    '单子给你，但要你穿玩偶服来送货。',
    option('先付一半', '预付款到账，你选了最贵的熊。', (18, -3, 9, -5)),
    option('叫销售穿', '销售接了单，也接走了一半提成。', (9, 7, -5, 5)),
    cooldown=7)

add('office_tickets', 'power', '行政',
    '游客买票看你开会，比产品还赚钱。',
    option('加开夜场', '会议开始排节目，员工开始要片酬。', (17, -7, 8, 6)),
    option('只开放周末', '游客少了，周一终于能谈点正事。', (8, 10, -8, -5)),
    cooldown=8)

add('boss_camera', 'power', '直播导演',
    '你一上直播，退款提示就响个不停。',
    option('戴面具再上', '面具卖光了，机器也跟着卖了。', (14, 4, 9, 5)),
    option('让员工上', '他没讲愿景，只演示了怎么用。', (10, 8, -5, -9)),
    cooldown=8)

add('legal_ad', 'power', '法务',
    '对手律师函上，印着你的旧款广告。',
    option('付费让他续印', '客户拿着律师函来问怎么买。', (11, 0, 10, 7)),
    option('谈个和解价', '双方都收了麦，律师最不高兴。', (15, 5, -10, -6)),
    cooldown=10)

add('ugly_shell', 'power', '设计总监',
    '用户选的丑壳，比你设计的贵三倍。',
    option('照丑的卖', '你没上发布会，销量替你上了。', (16, 7, 7, -12)),
    option('我再画一版', '设计组又加了班，样机总算像你了。', (-7, -6, -5, 14)),
    cooldown=7)

add('boss_stickers', 'power', '公关总监',
    '你的怒吼成了表情包，卖得比机器好。',
    option('卖授权', '每次有人骂老板，你都收一笔钱。', (17, -4, 7, 6)),
    option('员工免费用', '工作群安静了，表情包却刷屏了。', (5, 13, -8, -8)),
    cooldown=9)

add('chase_marathon', 'power', '财务总监',
    '欠款老板说卧床，朋友圈却在跑马。',
    option('终点等他', '他一冲线，你递上账单和水。', (20, 3, -6, 4)),
    option('赞助追款横幅', '钱转过来了，他求你别报下场名。', (14, -3, 8, 7)),
    cooldown=8)

add('overtime_meals', 'power', '行政',
    '加班餐太香，隔壁员工来蹭饭。',
    option('收饭钱', '伙食回本，隔壁老板也来了。', (13, 4, -7, -4)),
    option('发招聘表', '饭多做了一锅，工程师多了一排。', (-10, 17, 5, 3)),
    cooldown=7)

add('couple_robots', 'power', '客服主管',
    '机器人替夫妻吵架，夫妻改为围观。',
    option('卖情侣套装', '两台一起买，赠送一对耳塞。', (15, -3, 10, 5)),
    option('送和解补丁', '机器握手了，客户又买了扫地款。', (7, 9, -6, -6)),
    cooldown=9)

add('too_diligent', 'power', '客服主管',
    '差评：机器太勤快，显得我很懒。',
    option('出摸鱼模式', '机器懂事了，客户主动续了费。', (12, 6, -6, -5)),
    option('教它夸人', '它扫了一天地，说全靠主人领导。', (8, -2, 10, 7)),
    cooldown=8)

add('refund_investment', 'power', '财务总监',
    '客服把退款，谈成了追加投资。',
    option('给它提成', '客户没走，客服也有了年终奖。', (17, 9, 5, 4)),
    option('先退钱', '钱退了，客户夸你像个正常公司。', (-8, 6, -9, -7)),
    cooldown=9)

add('discount_puzzle', 'power', '财务总监',
    '满减规则太复杂，财务也凑不出来。',
    option('统一打折', '优惠券没了，付款的人多了。', (8, 8, 10, -6)),
    option('收费教凑单', '课卖火了，学员顺便退了机器。', (16, -5, -10, 6)),
    cooldown=8)

add('whole_class', 'power', '技校老师',
    '全班来应聘，能把我一起收了吗？',
    option('整班都要', '工位坐满了，还装了一块黑板。', (-12, 20, 3, 4)),
    option('先开培训班', '学费没收，工厂少请了十个师傅。', (10, 10, -7, -4)),
    cooldown=8)

add('side_hustle', 'power', '财务总监',
    '员工的副业，赚得比公司还多。',
    option('收编副业', '你买下副业，也买回了他们的心思。', (-10, 12, 11, 5)),
    option('向他们取经', '你坐进培训室，讲师是你实习生。', (14, 5, -5, -10)),
    cooldown=7)

add('double_dinner', 'power', '助理',
    '两个大客户撞期，都要你陪吃饭。',
    option('派个机器人', '两单都签了，它还打包了龙虾。', (16, -3, 8, 5)),
    option('拼成一桌', '他们吵了一晚，反而凑成一笔大单。', (11, 7, -7, -4)),
    cooldown=8)

add('market_empty', 'power', '销售总监',
    '同行全转行了，客户还在找充电器。',
    option('涨价，接单', '充电器涨了价，旧客户回了头。', (18, -3, 12, 5)),
    option('先交清旧货', '新客排着队，老客终于不堵门了。', (9, 9, -14, -5)),
    cooldown=7)

add('boss_holiday', 'power', '助理',
    '你度假一周，公司利润翻倍了。',
    option('再休一周', '全公司自费，给你续了机票。', (12, 11, -7, -11)),
    option('我另开个项目', '你拎回一台样机，假期到此结束。', (-8, 5, -4, 16)),
    cooldown=8)

add('boss_bid', 'power', '行政',
    '员工把你挂二手平台，标价一元。',
    option('拍下我自己', '你加到一万，财务说不能报销。', (-6, 8, -5, 12)),
    option('让客户来竞价', '老客户拍到了你，要求亲自上门。', (15, 5, 5, -9)),
    cooldown=11)

add('meeting_room', 'breather', '行政',
    '最大的会议室，老板给起个名字？',
    option('别开了', '通知写着：下午两点，别开了。'),
    option('老板不一定对', '你推门进去，所有人都看门牌。'),
    'turn>=3', 170, 'expression')

add('dog_ceo', 'breather', '行政',
    '最佳老板投票，您的狗又赢了。',
    option('给它发工牌', '工牌挂了，它把绳子咬断了。'),
    option('让它主持年会', '它叫了两声，全场都说讲得好。'),
    'turn>=3', 170, 'expression')

add('award', 'breather', '主办方',
    '奖杯没刻字，您想拿个什么奖？',
    option('同行失眠奖', '同行没鼓掌，摄影师拍了他们。'),
    option('最会发工资奖', '财务问这奖能不能抵个税。'),
    'turn>=3', 170, 'expression')

add('old_boss_call', 'breather', '旧老板',
    '来参观一下，不是来求职的啊。',
    option('挂入职横幅', '他站在横幅下，反复说只是参观。'),
    option('给他访客卡', '卡上写着：无审批权限。'),
    'turn>=3', 170, 'expression')

add('pajamas', 'breather', '大股东',
    '老板，您穿睡衣开董事会？',
    option('全员发一套', '她问能不能折进今年的分红。'),
    option('这是战袍', '散会后，她要了购买链接。'),
    'turn>=3', 170, 'expression')

add('success_lecture', 'breather', '主持人',
    '商学院请你讲成功学，稿子忘带了。',
    option('讲倒霉事', '讲到第三次翻车，台下开始记笔记。'),
    option('让扫地机讲', '它绕了一圈，说先把地扫干净。'),
    'turn>=3', 170, 'expression')

add('founder_statue', 'breather', '行政',
    '您的雕像做好了，保安不让它进门。',
    option('给它办离职', '雕像领到了一张离职纪念照。'),
    option('就站门口', '外卖都放在它脚边，没丢过一单。'),
    'turn>=3', 170, 'expression')

add('assistant_dream', 'breather', '助理',
    '您昨晚说的梦话，要写进战略吗？',
    option('一个字别改', '第一页：别抢我鸡腿。'),
    option('先过财务', '财务看完，批了两份鸡腿预算。'),
    'turn>=3', 170, 'expression')

add('wind_seat', 'wind', '助理',
    '投资人改签三次，只为坐您旁边。',
    option('收钱，往后坐', '钱到账了，他买了你的后一排。', (25, 0, 4, -6), 'funded_run'),
    option('先听我讲产品', '飞机落地了，他还没让你停。', (8, 4, 13, 6)),
    'phase=2 and turn>=5', 400)

add('wind_queue', 'wind', '销售总监',
    '预售排到明年，黄牛也来求你了。',
    option('再开十万台', '钱到了，厂长的手机关了机。', (20, -6, 15, 8)),
    option('关预售，交货', '黄牛走了，老客户终于收货了。', (12, 10, -16, -5)),
    'phase=2 and turn>=5', 400)

add('ebb_speeches', 'ebb', '助理',
    '风口过去，演讲邀约全变成了讨债。',
    option('卖掉发布会场', '舞台拆了，欠款先还了一半。', (18, 3, -12, -6)),
    option('上客户门讲', '鸡汤没讲，机器演示卖出去两台。', (8, -4, 10, 5)),
    'phase=3 and turn>=10', 450)

add('risk_money', 'pressure', '财务总监',
    '工资发不出了，打卡机还催人上班。',
    option('卖我的豪车', '车走了，工资提示音响成一片。', (28, 7, -9, -7)),
    option('我去堵欠款人', '老板堵老板，欠款终于到账。', (24, 3, -4, -3)),
    'money<=18 and !risk_money_run', 90000, 'crisis', 'risk_money_run')

add('risk_team', 'pressure', '人事总监',
    '离职群比公司群还热闹，快没人了。',
    option('发钱，砍加班', '离职信折成纸飞机，又飞了回来。', (-12, 29, -8, -6), 'paid_keep'),
    option('让大家罢免我', '他们只罢免了你的周报和晨会。', (-4, 24, -4, -12)),
    'team<=20 and !risk_team_run', 90000, 'crisis', 'risk_team_run')

add('risk_market_low', 'pressure', '销售总监',
    '一周只卖一台，买家还是您母亲。',
    option('半价以旧换新', '门店又排队了，你妈要求补差价。', (-10, -3, 27, 6)),
    option('带样机上门', '你守着采购，演示到电量耗尽。', (5, 3, 23, 3)),
    'market<=15 and !risk_market_low_run', 90000, 'crisis', 'risk_market_low_run')

add('risk_market_high', 'pressure', '厂长',
    '订单做不完，退款排队比抢购还长。',
    option('立刻关预售', '按钮关了，欠货开始一车车发走。', (-6, 7, -30, -6)),
    option('找同行代工', '利润分了，客户总算拆到了箱子。', (-11, 5, -27, -3)),
    'market>=85 and !risk_market_high_run', 90000, 'crisis', 'risk_market_high_run')

add('risk_mind_low', 'pressure', '技术总监',
    '签名章都比你积极，还想做产品吗？',
    option('给我拆一台', '你拆到天亮，没问一次利润率。', (-9, 4, -4, 26)),
    option('我去卖一台', '客户骂了两句，你当场改了机器。', (6, 0, 5, 22)),
    'mind<=18 and !risk_mind_low_run', 90000, 'crisis', 'risk_mind_low_run')

add('risk_mind_high', 'pressure', '财务总监',
    '没人敢说不，连机器人都装死了。',
    option('先听反对票', '第一票是保洁，她说你太能折腾。', (4, 8, -5, -30)),
    option('先锁我的公章', '公章锁了一晚，计划少了三个零。', (-3, 5, -2, -27)),
    'mind>=85 and !risk_mind_high_run', 90000, 'crisis', 'risk_mind_high_run')

add('cash_out', 'exit', '收购方',
    '公司我买，机器人也归我，您开价。',
    option('拿钱走人', '交割款到账，烦恼换了个收件人。', flags='end_sold'),
    option('我还没玩够', '支票退了，下一场发布会照开。', (-3, 4, 0, 5)),
    'money>=65 and turn>=14 and board_done_run', 140, cooldown=18)

add('hand_over', 'exit', '合伙人·{maker}',
    '公司能自己跑了，您要下班吗？',
    option('交给你', '你走到门口，打卡机替你签了退。', flags='end_next'),
    option('我还要拍板', '他把椅子挪过来，公章一人一枚。', (5, 8, 0, -10)),
    'partner_equal_run and team>=65 and turn>=15', 140, cooldown=20)

add('take_break', 'exit', '助理',
    '您把工作群全静音了，真不干了？',
    option('找人接手', '工作手机交出去了，你买了台老人机。', flags='end_pause'),
    option('换个项目玩', '样机进门，你把新群开了声音。', (-8, 5, -4, 20)),
    'mind<=27 and turn>=14', 140, cooldown=14)

add('legacy_rival', 'legacy', '前合伙人·{rival}',
    '上次你投我创业，这次我来挖你的人。',
    option('放马过来', '两家公司把招聘会开在了同一层。', (8, -3, 8, 4)),
    option('合并，别折腾', '人不用搬家，两块招牌挤在一起。', (13, 4, -3, -6)),
    'dynasty>1 and rival_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

add('legacy_paid', 'legacy', '猎头',
    '上家奖金发够了，老员工带家属来。',
    option('全都收下', '团队没散，连厨师都一起回来了。', (-7, 18, 3, 3)),
    option('先来三个', '三个人提着旧工牌，直接开始干活。', (-4, 11, 4, -2)),
    'dynasty>1 and paid_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

add('legacy_debt', 'legacy', '老客户',
    '公司换名字了，我的货还没发。',
    option('这次先还你', '旧单补完，新店少了一条置顶差评。', (-14, 4, 6, 5), '!hype_debt_keep'),
    option('新店只卖现货', '新单照发，他继续在门口等旧单。', (5, 0, -7, -4)),
    'dynasty>1 and hype_debt_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

add('legacy_bet', 'legacy', '技术买家',
    '上家机器留下的技术，我想买。',
    option('只卖授权', '旧项目终于赚钱，不用再租工厂。', (19, 0, 4, 3), '!bet_wait_keep'),
    option('收钱再做', '订金先到，封存的机器又开了。', (12, 6, 7, 5), '!bet_wait_keep'),
    'dynasty>1 and bet_wait_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

add('legacy_sold', 'legacy', '投资人',
    '上家卖完了，这家又准备卖给谁？',
    option('也许是你', '她笑了，先问能不能便宜一点。', (15, 0, 7, 5)),
    option('先看产品', '她合上估值表，接过了螺丝刀。', (5, 4, 3, -4)),
    'dynasty>1 and last_sold_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

add('legacy_robot', 'legacy', '旧机回收员',
    '你删掉的机器人，有份云端备份。',
    option('买回来封存', '备份锁进保险柜，密码你自己设。', (-12, 7, -8, -5)),
    option('让它出本书', '书名只有三个字：老板急了。', (18, -5, 10, 5)),
    'dynasty>1 and robot_wiped_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

add('legacy_failed', 'legacy', '财务总监',
    '这回先存工资，别把保险柜也卖了。',
    option('留三个月', '工资锁好了，这回钥匙归财务。', (10, 9, -5, -4)),
    option('先做赚钱的单', '场面小了，欠条也少了。', (14, 0, -8, 2)),
    'dynasty>1 and last_failed_keep and turn>=3 and !legacy_seen_run', 1900, 'payoff', 'legacy_seen_run')

ENDINGS = {
    'closed': dict(title='账户比脸干净', label='资金耗尽', body='公司停了。\n门口的机器还在喊欢迎光临。', flag='last_failed_keep'),
    'alone': dict(title='全勤奖归你', label='团队耗尽', body='最后一个员工走了。\n打卡机给你颁了全勤奖。', flag='last_failed_keep'),
    'forgotten': dict(title='只剩自动回复', label='客户耗尽', body='最后一家门店撤了货。\n客服还在自动回复亲亲在吗。', flag='last_failed_keep'),
    'overload': dict(title='退款也是爆款', label='交付失控', body='收款按钮太好用了。\n退款按钮替你结束了营业。', flag='hype_debt_keep'),
    'hollow': dict(title='不想再开会了', label='心气耗尽', body='公司还在。\n这次，你把工作群真的退了。', flag='last_failed_keep'),
    'allin': dict(title='这次你说了不算', label='心气失控', body='你说再赌一次。\n银行说，这是最后一次。', flag='last_failed_keep'),
    'sold': dict(title='烦恼已过户', label='主动出售公司', body='收购款到账。\n新老板问机器人怎么关机，你没回。', flag='last_sold_keep', win=True),
    'next': dict(title='老板先下班', label='主动交棒', body='你离开公司，没人拦。\n他们真的能自己干了。', win=True),
    'pause': dict(title='暂时不接电话', label='主动离开', body='接手的人来了。\n你第一次把闹钟全部关掉。'),
}


def export():
    with (HERE / 'cards.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, delimiter=';')
        writer.writeheader()
        writer.writerows(CARDS)
    story_data = dict(credit='GPT 6 Astra', edition='astra-1', cards=META, endings=ENDINGS)
    (HERE / 'story-meta.json').write_text(json.dumps(story_data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sections = ['# 创始人 · GPT 6 Astra 作品', '', '发布会先出事，玩家当场拍板。荒诞后果逐步回访，没有固定任期。', '',
                '日常经营卡按冷却重新入池；一次性大事与后续只出现一次。出售、交棒、休息都可以拒绝。', '']
    for card in CARDS:
        sections.extend([f"## {card['card']} · {card['bearer']}", '', card['question'].replace('\n', '  \n'), '',
                         f"- ← **{card['override_no']}**：{card['answer_no']}",
                         f"- → **{card['override_yes']}**：{card['answer_yes']}", '',
                         f"条件：`{card['conditions']}`；冷却：`{card['lockturn']}`", ''])
    sections.extend(['## 结局', ''])
    for ending in ENDINGS.values():
        sections.extend([f"### {ending['title']}", '', ending['label'], '', ending['body'], ''])
    (HERE / '故事手册.md').write_text('\n'.join(sections), encoding='utf-8')
    print(f'卡组 {len(CARDS)} 张；可循环经营卡 {sum(card["lockturn"] != "del" for card in CARDS)} 张；结局 {len(ENDINGS)} 种。')


if __name__ == '__main__':
    export()
