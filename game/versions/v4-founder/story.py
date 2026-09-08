"""手写故事源。导出兼容 V3 的 22 列卡表与可直接阅读的分支手册。"""
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


def option(label, reply, delta=(0, 0, 0, 0), flags='', keepsake=''):
    return dict(label=label, reply=reply, delta=delta, flags=flags, keepsake=keepsake)


def add(name, theme, bearer, question, left, right, condition='', weight=100,
        kind='initiative', title='', shared=''):
    card = dict.fromkeys(HEADER, '')
    card.update(thematic=theme, card=name, id=str(len(CARDS) + 1), bearer=bearer,
                question=question, conditions=condition, lockturn='del', weight=str(weight))
    metadata = dict(kind=kind, title=title or bearer.split(' · ')[0], keepsakes={})
    for side, choice in [('no', left), ('yes', right)]:
        card[f'override_{side}'] = choice['label']
        card[f'answer_{side}'] = choice['reply']
        card[f'{side}_custom'] = ' and '.join(filter(None, [choice['flags'], shared]))
        for resource, amount in zip(RESOURCES, choice['delta']):
            card[f'{side}_{resource}'] = str(amount) if amount else ''
        if choice['keepsake']:
            metadata['keepsakes'][side] = choice['keepsake']
    CARDS.append(card)
    META[name] = metadata


add('first_promise', 'opening', '阿岑 · 联合创始人',
    '辞职信交了，半间铺子租了。\n咱们的第一盏灯，到底有什么毛病？',
    option('到点赶人下班', '你焊上定时器。晚上六点半，它先替你们下了班。', flags='off_run', keepsake='下班灯｜第一份承诺：今天就到这里。'),
    option('替晚归的人等门', '你把感应器转向门口。人回来了，灯才肯睡。', flags='home_run', keepsake='等人灯｜第一份承诺：给你留着灯。'),
    'turn=1 and dynasty=1', 900000, title='先做一件自己的东西')

add('another_promise', 'opening', '{maker} · 这次的新搭档',
    '上一家店的招牌留在上一条街。\n新招牌叫「{company}」。这次，我们为什么做灯？',
    option('还是想赶人下班', '你又焊上定时器。这次你知道，一盏灯管不了所有事，但可以先管住一张桌子。', flags='off_run', keepsake='新的下班灯｜不是第一次开始，仍然是你选的。'),
    option('想替晚归的人等门', '你把感应器转向门口。新的店里，还没有人的脚步被它认出来。', flags='home_run', keepsake='新的等人灯｜门换了一扇，灯重新认人。'),
    'turn=1 and dynasty>1', 900000, title='再开一家，不是清空过去')

add('off_prototype', 'opening', '阿岑 · 焊了三夜',
    '六点半，样灯灭了。\n你手里的活还差一点。',
    option('摸黑收工', '你俩在黑暗里找钥匙，笑了足足一分钟。灯先管住了老板。', (0, 5, 0, 5), 'practice_run', '黑掉的样灯｜你也遵守了自己定的规矩。'),
    option('给它加个再五分钟', '阿岑按了六次。你拿起笔，在说明书上写：包括老板在内，最多一次。', (-3, 0, 3, 3), 'snooze_run'),
    'turn=2 and off_run', 900000, kind='expression', title='规矩先用在谁身上')

add('home_prototype', 'opening', '阿岑 · 焊了三夜',
    '样灯亮了一夜。\n阿岑睡着了，手还压在电路板上。',
    option('让它只等一个人', '你调小感应范围。以后它不会为路过的每个人醒来。', (-2, 3, 0, 5), 'private_run'),
    option('让它认谁都算回家', '隔壁老唐来借钳子，灯亮了。他愣了一下，说：这也算啊。', (-3, 3, 4, 3), 'open_door_run', '借来的钳子｜老唐是第一个被这盏灯等到的人。'),
    'turn=2 and home_run', 900000, kind='expression', title='谁算自己人')

add('off_customer', 'opening', '小许 · 第一位顾客',
    '「我想买一盏放工位上。」\n她又问：「能不能别让老板看出它会灭？」',
    option('做成普通台灯', '第一笔钱到账。你把开关藏在灯底，她把笑藏在口罩里。', (9, 0, 5, 2), 'quiet_run', '第一张收据｜买灯的人，想准时离开办公室。'),
    option('灯罩印准点下班', '她买了两盏。另一盏寄给了老板，匿名。', (7, 0, 7, 4), 'loud_run', '第一张收据｜有人替你把宣言寄给了老板。'),
    'turn=3 and off_run', 900000, title='第一笔钱')

add('home_customer', 'opening', '小许 · 第一位顾客',
    '「我值夜班，回家不想吵醒我妈。」\n「能不能只照到鞋，不照到脸？」',
    option('蹲下来改一盏', '你在地上蹲了一下午。第二天，她发来一张没有拍到人的回家照。', (7, 0, 5, 5), 'quiet_run', '一张回家照｜光只落在鞋尖上。'),
    option('每一盏都这样改', '罗姐拿起锉刀，把样灯的光削低了一截。第一条产品标准，是别吵醒人。', (5, 4, 7, 3), 'loud_run', '第一条标准｜别吵醒正在睡觉的人。'),
    'turn=3 and home_run', 900000, title='第一笔钱')

add('cat_chair', 'play', '罗姐 · 生产负责人',
    '一只猫占了唯一的老板椅。\n你决定给它一个正式职位。',
    option('董事长', '从此全公司唯一可以在会上舔屁股的，是董事长。', flags='cat_boss_run and cat_boss_keep', keepsake='猫的工牌｜董事长。没有否决权，但有指甲。'),
    option('试睡员', '它成为全公司第一个不用证明自己有用的员工。', flags='cat_sleep_run and cat_sleep_keep', keepsake='猫的工牌｜首席试睡员。试用期已睡过。'),
    'turn>=4 and turn<=8 and !breath_run', 1900, kind='expression', title='先解决老板的问题', shared='breath_run')

add('company_photo', 'play', '周野 · 刚来的实习生',
    '公司官网需要一张团队照。\n你们三个人，借来的盆栽有六盆。',
    option('盆栽也站前排', '官网上线。有人留言：贵公司看起来特别稳定。', flags='plant_run and plant_keep', keepsake='第一张合照｜三个人，六盆借来的资深员工。'),
    option('就拍三个人', '照片里空了一大半。你说留着，以后有人来再站。', (0, 2, 0, 2), 'empty_photo_run', '第一张合照｜空出来的位置，不拿盆栽凑。'),
    'turn>=4 and turn<=8 and !breath_run', 1900, kind='expression', title='公司有多大', shared='breath_run')

add('title_stamp', 'play', '你 · 还没有名片',
    '印章店问，你的职位要刻什么。\n「总裁」比「修灯的」贵十块。',
    option('修灯的', '第一次签合同，对方问谁是老板。阿岑指了指你，又指了指猫。', flags='repair_title_run', keepsake='一张名片｜六点半，修灯的。'),
    option('总裁，烫金', '章刻好了。你用它在泡面盖上压了三分钟。', flags='gold_title_run', keepsake='烫金名片｜创业初期主要用于泡面。'),
    'turn>=4 and turn<=8 and !breath_run', 1900, kind='expression', title='对自己好一点', shared='breath_run')

add('wind_off', 'wind', '周野 · 手机快没电了',
    '一间写字楼的灯在六点半一起灭了。\n视频里几百人鼓掌。有人认出了你的灯。',
    option('把购买链接置顶', '你在纸箱上写的店名，被念进了新闻。那天，收款声第一次盖过电钻。', (16, 2, 10, 4), 'famous_run', '上了新闻｜几百人同时鼓掌，只因为灯灭了。'),
    option('趁热办熄灯节', '六点半，十二座城市的人同时关灯。你们没有买过这么大的广告。', (12, 4, 13, 5), 'festival_run and famous_run', '第一届熄灯节｜十二座城市替你关了灯。'),
    'phase=2 and off_run and !wind_news_run', 8500, title='风真的来了', shared='wind_news_run')

add('wind_home', 'wind', '周野 · 手机快没电了',
    '有人拍了你们的灯，配字「原来我家也有人等我」。\n转发的人开始晒自己的玄关。',
    option('收集一百个玄关', '一百张照片里没有豪宅。你把它们贴满铺子，订单跟着挤了进来。', (12, 4, 12, 5), 'gallery_run and famous_run', '一面玄关照片｜灯替一百个人等过门。'),
    option('今晚就开直播', '你坐在自己那扇破门前开播。弹幕第一句是：老板，你家也这么小啊。', (16, 2, 10, 4), 'live_run and famous_run', '第一次直播｜你没有借一间好看的房子。'),
    'phase=2 and home_run and !wind_news_run', 8500, title='风真的来了', shared='wind_news_run')

add('wind_money', 'wind', '罗姐 · 拿着银行短信',
    '第一批大单的钱真的到账了。\n你盯着余额，罗姐问：先兑现哪句吹过的牛？',
    option('每个人发一笔', '到账声在车间响成一片。阿岑把欠房东的钱还了，还故意多打了一块。', (10, 9, 0, 3), 'bonus_run and bonus_keep', '第一笔奖金｜不是估值，不是期权，能交房租。'),
    option('包下整条生产线', '以前你在厂门外等师傅。今天，师傅在门口等你。', (5, 4, 8, 7), 'scale_run', '一整条生产线｜第一次有人等你来开工。'),
    'phase=2 and wind_news_run and age_wind>=1 and !wind_money_run', 1550,
    title='这回不是画饼', shared='wind_money_run')

add('wind_billboard', 'wind', '你 · 路过以前的公司',
    '以前的老板每天坐这班电梯。\n你现在买得起里面那一块广告屏。',
    option('只写我出来干了', '每天早上，他得看你十二秒。周野说这是最不精准、也最精准的一笔投放。', (-4, 2, 4, 8), 'revenge_ad_run', '电梯广告｜我出来干了。'),
    option('给他送一盏灯', '快递签收了。第二天，他的助理偷偷来问团购价。', (-2, 0, 6, 4), 'old_boss_lamp_run'),
    'phase=2 and wind_news_run', 100, kind='expression', title='一点私人恩怨')

add('wind_redcarpet', 'wind', '周野 · 被人叫周总了',
    '行业大会把你排在最后发言。\n现在主办方问，能不能让你第一个上。',
    option('带着样灯上去', '别人讲趋势，你关掉了会场的一盏灯。散场后，你第一次被一群人追着问。', (6, 0, 5, 5), 'stage_run'),
    option('让罗姐上', '她讲了怎样把一个歪螺丝拧正。掌声比前面所有英文缩写都长。', (4, 6, 4, 2), 'luo_stage_run and luo_stage_keep', '罗姐的胸牌｜生产负责人，不是谁带来的家属。'),
    'phase=2 and wind_news_run', 100, title='轮到你被听见')

add('wind_wrongbox', 'wind', '罗姐 · 仓库',
    '旧纸箱上还印着「绿皮鸭蛋」。\n今天一百个人来问鸭蛋灯什么时候补货。',
    option('就叫鸭蛋限定', '周野当场画了一只鸭。它比你们花钱做的商标先出了名。', (7, 0, 5, 3), 'duck_run and duck_keep', '鸭蛋纸箱｜后来真的有人收藏。'),
    option('附张认真道歉卡', '道歉卡被晒了出来。下一批人专门备注：要鸭蛋箱和道歉。', (5, 3, 5, 2), 'apology_box_run'),
    'phase=2 and wind_news_run', 100, kind='expression', title='连出错都在帮你')

add('wind_dream', 'wind', '阿岑 · 难得喝了一点',
    '「要是早知道能卖这么多……」\n他没说完。你举起杯子，替他把后半句接上。',
    option('早两年辞职', '你俩碰杯，震得桌上那盏样灯灭了。它到点了，没看你们脸色。', (0, 4, 0, 5), 'toast_early_run'),
    option('那晚多睡一会', '阿岑笑着笑着，不笑了。你们把今天最后一单留到了明天。', (0, 6, -3, -3), 'toast_sleep_run'),
    'phase=2 and wind_money_run', 100, kind='expression', title='以为自己终于懂了')

add('ebb_news', 'ebb', '周野 · 把直播关了',
    '热搜换成了别的东西。\n昨晚你说一句话就有人下单，今晚你连说了三遍。',
    option('给老顾客打电话', '第一个接电话的人说灯还好好的，不用再买。然后他给你介绍了一个朋友。', (4, 2, -7, -3), 'return_customers_run'),
    option('关掉后台，去做灯', '你拧完第一颗螺丝，才发现自己已经很久没有碰过产品了。', (-3, 4, -5, 5), 'back_to_bench_run'),
    'phase>=3 and !ebb_news_run', 8200, title='风不是你关掉的', shared='ebb_news_run')

add('winter_invitation', 'daily', '孟女士 · 投资人',
    '你想再办一次热闹的发布会。\n名单还在，愿意来的人少了一半。',
    option('改成修灯日', '来了十七个人，带着十九盏灯。你第一次知道，卖出去之后它们过得怎么样。', (-3, 4, 5, 4), 'repair_day_run and repair_day_keep', '修灯日｜有一盏在顾客家里摔过三次。'),
    option('空位也摆好', '你对着空椅子讲完了。最后一排的罗姐说：这回我倒是听懂你想做什么了。', (-5, 4, 0, 5), 'empty_chairs_run'),
    'phase>=3', 100, title='没人鼓掌的时候')

add('winter_competitor', 'daily', '老唐 · 隔壁修理铺',
    '大牌出的灯像你们，便宜一半。\n你想让买家看见哪一点不同？',
    option('直播拆两盏', '罗姐把两块电路板排在桌上。直播第一次没有喊话，只有螺丝落盘子的声音。', (-4, 2, 6, 4), 'teardown_run'),
    option('把维修电话印大', '电话真的响了。对方的灯不是你们家的，你还是教他换了开关。', (-3, 3, 5, 3), 'repair_phone_run and repair_phone_keep'),
    'phase>=3', 100, title='你到底凭什么')

add('winter_smallorder', 'daily', '小许 · 老顾客',
    '她想给新搬家的朋友买一盏。\n你刚取消了一场没人报名的团购。',
    option('亲手包好这一盏', '你找回最早那种包法。她说：我就知道你们还在。', (5, 0, 4, 4), 'small_order_run'),
    option('让她朋友自己挑', '你加上对方的微信。聊到最后，他选了你已经停产的第一版。', (4, 0, 5, 3), 'old_model_run'),
    'phase>=3', 100, title='一个人也算顾客')

add('winter_warehouse', 'daily', '你 · 晚上独自去仓库',
    '没卖掉的灯堆到肩膀。\n你突然想看看，它们一起亮起来是什么样。',
    option('全插上', '仓库像一个没有人的小区。你拍了张照，没有配「坚持」两个字。', (-2, 0, 0, 7), 'warehouse_photo_run', '仓库的照片｜没有配「坚持」。'),
    option('只点亮最早那盏', '后来的灯做得越来越薄。最早那盏依然歪，依然亮。', (0, 0, 0, 5), 'first_lamp_run'),
    'phase>=3', 100, kind='expression', title='暂时不解决问题')

add('quiet_screw', 'daily', '罗姐 · 生产负责人',
    '你想把灯底的一颗螺丝换成铜的。\n没人看得见。你自己每次都会翻过来看。',
    option('就换这一颗', '罗姐没劝你。她拿出另一颗：这个摸着还舒服点。', (-4, 2, 0, 6), 'brass_run', '一颗铜螺丝｜看不见的地方，你也想留点自己的东西。'),
    option('给每盏刻上装配人', '小陈刻了真名。罗姐只刻了一个「罗」，说剩下的地方留给修它的人。', (-3, 5, 2, 3), 'signed_run and signed_keep', '灯底的名字｜装配人：罗。'),
    'turn>=5', 100, title='一个没法讲回报的念头')

add('quiet_game', 'daily', '阿岑 · 举着游戏手柄',
    '你想和大家打一次游戏。\n第一局，你把实习生堵在出生点。',
    option('绝不放水', '第二局他们全换到对面。你第一次体验到全公司目标一致。', (0, 2, 0, 4), 'game_enemy_run'),
    option('和实习生换队', '阿岑也换过去了。你发现他们不是想赢，只是想打老板。', (0, 4, 0, 2), 'game_team_run'),
    'turn>=5', 100, kind='expression', title='平等只存在了第一局')

add('quiet_door', 'daily', '你 · 量了半天门框',
    '你想把办公室的门拆掉。\n阿岑提醒你：我们还没买办公室。',
    option('先把这半扇拆了', '隔壁老唐探头问：那我以后进来，还算借工具吗？', (0, 3, 0, 3), 'no_door_run'),
    option('那就永远不买', '罗姐用胶带在地上圈出你的工位。每次开会，大家都从「总裁办公室」上走过。', (0, 3, 0, 3), 'floor_office_run', '胶带办公室｜面积零点八平方米，四面通风。'),
    'turn>=5', 100, kind='expression', title='你想当什么老板')

add('quiet_packaging', 'daily', '周野 · 包装最后一稿',
    '盒底只能留一句话。\n这句话不用拿去路演，只有拆盒的人会看到。',
    option('坏了就找我', '罗姐把自己的工作电话写在下一行，说：别印你那个总不接的。', (0, 2, 2, 3), 'box_fix_run and repair_phone_keep'),
    option('今天就到这里', '阿岑把这句话剪下来，贴在了你每天加班的那张桌子上。', (0, 3, 0, 4), 'box_rest_run'),
    'turn>=5', 100, kind='expression', title='一句只说给买家听的话')

add('quiet_discount', 'daily', '你 · 定促销规则',
    '别人按会员等级打折。\n你想按一个只有你在乎的标准来。',
    option('六点半走的人打折', '有人把打卡记录寄来，有人寄辞职信。罗姐把后者也算过了。', (-3, 0, 5, 4), 'discount_rest_run'),
    option('带旧灯来就打折', '第一天收到最多的不是旧灯，是大家舍不得扔的故事。', (-3, 2, 4, 4), 'tradein_run and tradein_keep'),
    'turn>=5', 100, title='规则也可以是你写的')

add('quiet_salary', 'daily', '罗姐 · 工资表',
    '你想给自己也发一份工资。\n不是一块钱那种，是能活的那种。',
    option('跟罗姐一样多', '你终于不用每次吃饭都说「先记公司账」。罗姐说，这样才好骂你。', (-4, 3, 0, 3), 'salary_run'),
    option('先把欠大家的补了', '补发那一栏清零。你给自己转了生活费，这次没人拦。', (-7, 7, 0, 2), 'paid_run and paid_keep'),
    'turn>=5', 100, title='你也是这家公司的人')

add('quiet_children', 'daily', '老唐 · 带来一个小姑娘',
    '他的孙女想看你怎么造灯。\n你决定把今天当一场真正的新品发布。',
    option('认真讲工作原理', '她问为什么不能做成一只会发光的鸡。你看了阿岑一眼，他已经在画了。', (-2, 3, 0, 4), 'chicken_run', '一张鸡形草图｜唯一没问市场有多大的观众。'),
    option('让她自己拧一颗', '那颗螺丝歪了。她说这盏不能卖，因为是她做的。你第一次遇到比你还偏执的人。', (0, 3, 0, 4), 'child_screw_run'),
    'turn>=5', 100, kind='expression', title='不需要商业计划的观众')

add('quiet_logo', 'daily', '周野 · 又改了一版',
    '你想把商标上的圆画歪一点。\n他说上一版已经是手画的了。',
    option('我来画', '你画了十七个圆，选了最圆的那个。周野没说话，保存为「最后真的最后」。', (0, 0, 0, 3), 'logo_round_run'),
    option('用罗姐茶杯印', '商标少了一口。后来顾客以为那是太阳落到山后，其实茶杯磕了。', (0, 2, 0, 3), 'cup_logo_run', '一个缺口商标｜来自罗姐用了八年的茶杯。'),
    'turn>=5', 100, kind='expression', title='有用的无聊事')

add('quiet_lunch', 'daily', '你 · 站在车间门口',
    '中午，所有人都在低头吃外卖。\n你想让今天和昨天有一点不一样。',
    option('把桌子搬到门外', '老唐端着碗坐了过来。第一次全体会议，有人边听边择菜。', (-2, 5, 0, 3), 'street_lunch_run'),
    option('放大家各自去吃', '阿岑去河边坐了半小时。回来只说了一句：以后都这样吧。', (0, 4, 0, 3), 'alone_lunch_run'),
    'turn>=5', 100, kind='expression', title='不需要统一热爱的午休')

add('quiet_website', 'daily', '你 · 改官网',
    '「让每个普通人被看见」这句太大。\n你想把它换成一句做得到的话。',
    option('邮件我们会回', '第一封邮件问发票，第二封讲失恋。周野回了整整一下午。', (0, 2, 3, 3), 'reply_mail_run'),
    option('灯坏了我们会修', '罗姐让你把「终身」两个字删掉。不是不想，是得先活那么久。', (0, 3, 3, 2), 'repair_word_run'),
    'turn>=5', 100, title='承诺可以小一点')

add('quiet_shoes', 'daily', '阿岑 · 看你擦鞋',
    '明天你要第一次见投资人。\n你擦了半小时皮鞋，还是像借来的。',
    option('穿自己的旧鞋', '对方第一句问你灯带了吗。你后悔了半小时，发现根本没人在看鞋。', (0, 0, 0, 4), 'old_shoes_run'),
    option('皮鞋也带上', '你拎着鞋进了会议室。孟女士说她第一次见有人随身携带另一种人生。', (0, 0, 0, 3), 'shoe_bag_run'),
    'phase=1 and turn>=5', 100, kind='expression', title='人还没红，先练习红')

add('quiet_rain', 'daily', '罗姐 · 厂门口',
    '下大雨了。下班的人挤在门口。\n你想做点什么，像个有用的老板。',
    option('开车送一趟', '你的小车只坐下三个人。剩下的人在门口给你鼓掌，像送宇航员。', (-2, 5, 0, 2), 'rain_car_run'),
    option('把样品纸箱剪开', '大家顶着写着六点半的纸板散了。公司第一批移动广告，都湿透了。', (-1, 4, 2, 2), 'rain_boxes_run'),
    'turn>=5', 100, kind='expression', title='不写进领导力课的一天')

add('a_offline', 'venture', '你 · 画了一夜电路图',
    '你想做一盏不用手机、不认账号的灯。\n阿岑说它很难卖出「智能」两个字的价。',
    option('做出来再说', '你在预算里留了一小行。每次开会它都被问到，每次你都没划掉。', (-9, 2, 0, 7), 'a_private_run and offline_run', '那一小行预算｜给一盏不认识手机的灯。'),
    option('先把图纸公开', '你按下发布，等了一夜。第一个留言是：能不能把字写清楚一点。', (-5, 3, 0, 5), 'a_public_run and open_design_run', '一张公开图纸｜最初只有一个人嫌你的字丑。'),
    'turn>=4 and turn<=8 and !slot_a_run', 1800, title='押一件现在没人要的东西',
    shared='slot_a_run and a_bet_run')

add('a_private_hit', 'payoff', '阿岑 · 把电话递给你',
    '你一直留着预算的离线灯，等来了第一张大单。\n买家是山里的值守站：那里没信号。',
    option('先给他们送去', '你们第一次为一个从没想过的地方造灯。对方付完款，问冬天还能不能订。', (19, 5, 8, 5), 'bet_hit_run and bet_hit_keep', '来自山里的订单｜那里没有信号，所以刚好需要你。'),
    option('做一批耐冷的', '罗姐把灯放进冰柜。你终于有了一个比「我觉得」更具体的理由。', (12, 7, 6, 6), 'bet_hit_run and bet_hit_keep'),
    'a_bet_run and a_private_run and age_a>=5 and lucky_bet_run', 2400,
    kind='payoff', title='原来有人在等它', shared='slot_a_done_run and !a_bet_run')

add('a_private_miss', 'payoff', '阿岑 · 又一次例会',
    '你保下来的离线灯，还是零订单。\n那一小行预算，已经绕不开了。',
    option('封样，先养活大家', '阿岑把样灯放进铁盒，没有扔。你写上日期，不写「失败」。', (5, 3, 0, -6), 'bet_shelved_run and bet_wait_keep', '封存的样灯｜不是所有坚持都会在这局获奖。'),
    option('再留一个人做', '你给项目写了一个真的期限。阿岑说这次到期，他会亲自来问你。', (-10, -2, 0, 7), 'bet_hold_run and bet_wait_keep', '续了一次的期限｜你还没有被证明是对的。'),
    'a_bet_run and a_private_run and age_a>=5 and !lucky_bet_run', 2400,
    kind='payoff', title='它仍然像个废项目', shared='slot_a_done_run and !a_bet_run')

add('a_public_hit', 'payoff', '周野 · 看着论坛',
    '你公开的灯图纸，被人改成了盲文旋钮版。\n作者说不想收钱，想借你们的模具。',
    option('借，名字刻他的', '第一批灯做出来，他在灯底摸到了自己的名字。你们的店第一次被他那群朋友找到。', (10, 6, 7, 5), 'bet_hit_run and bet_hit_keep and credit_run', '一个摸得到的名字｜图纸离开你以后，比你想得更远。'),
    option('请他一起做', '视频会议开起来，你才发现他不在同一座城市。六点半第一次有了远处的工位。', (6, 9, 6, 5), 'bet_hit_run and bet_hit_keep and partner_run'),
    'a_bet_run and a_public_run and age_a>=5 and lucky_bet_run', 2400,
    kind='payoff', title='不是你想到的答案', shared='slot_a_done_run and !a_bet_run')

add('a_public_miss', 'payoff', '周野 · 发现一家新店',
    '你公开的图纸被拿去量产了。\n详情页删掉了六点半，销量比你们好。',
    option('去评论区亮身份', '对方置顶了你的留言：「感谢技术交流。」至少名字回来了，订单没有。', (0, 2, 3, -5), 'copied_run and copied_keep'),
    option('把下一版也公开', '阿岑问你是不是赌气。你把改动列给他看，说这回我知道会发生什么。', (-6, 0, 4, 6), 'open_again_run and copied_keep', '第二张公开图纸｜这次不再以为世界会自动领情。'),
    'a_bet_run and a_public_run and age_a>=5 and !lucky_bet_run', 2400,
    kind='payoff', title='公开不保证被感谢', shared='slot_a_done_run and !a_bet_run')

add('a_challenge', 'venture', '你 · 在商场看到空展台',
    '大牌撤展，空了三天。\n你想用这三天，干件他们不会干的事。',
    option('让顾客当场拆灯', '周野写了「欢迎拆穿」。老唐背着工具箱来，说怕你真被拆穿。', (-6, 3, 4, 5), 'a_teardown_run'),
    option('摆满失败的样品', '歪的、裂的、亮一秒就灭的。你给每一盏写了个没法报销的名字。', (-4, 2, 3, 6), 'a_failure_run'),
    'turn>=4 and turn<=8 and !slot_a_run', 1800, title='先把台子抢过来',
    shared='slot_a_run and a_show_run')

add('a_teardown_return', 'payoff', '老唐 · 从展台回来',
    '你让人当场拆灯，真有人拆出了接头松动。\n他拍的视频开始往外传。',
    option('在同一张桌上修', '你没撤视频。最后流传最广的片段，是罗姐教拍视频的人焊接。', (-5, 6, 7, 3), 'honest_run and repair_day_keep', '展台上的焊点｜坏的地方没有被剪掉。'),
    option('让他带回去试坏', '你给了他一张无限次返修卡。他说：那我可真不客气了。', (-3, 2, 8, 5), 'tester_run and tester_keep'),
    'a_show_run and a_teardown_run and age_a>=2', 2400, kind='payoff',
    title='邀请来的麻烦', shared='slot_a_done_run and !a_show_run')

add('a_failure_return', 'payoff', '周野 · 展台收摊',
    '你展出的失败样灯，有人出钱要买。\n她就想要那盏「照不到明天」。',
    option('送她，别插电', '她把灯当花瓶，照片比正品广告好看。你们因此收到第一笔完全不讲道理的订单。', (7, 2, 5, 5), 'vase_run and vase_keep', '照不到明天｜它最终成了一只花瓶。'),
    option('修好，再卖给她', '她说不要修，修好就不是这一盏了。你第一次被顾客劝别把东西做得更好。', (4, 0, 5, 4), 'failure_fan_run'),
    'a_show_run and a_failure_run and age_a>=2', 2400, kind='payoff',
    title='失败也有不负责的用法', shared='slot_a_done_run and !a_show_run')

add('a_tang', 'venture', '你 · 老唐的工具墙前',
    '老唐修了三十年灯，招牌快掉了。\n你想和他合做一件东西。',
    option('让他署自己的名', '他在草稿上写「唐」。擦了，改成「老唐」，又擦了。', (-5, 5, 2, 3), 'a_tang_name_run and tang_friend_keep'),
    option('请他教会罗姐', '他嘴上说这有什么好教的，第二天带来了锁着的那只工具箱。', (-4, 7, 0, 3), 'a_tang_teach_run and tang_friend_keep'),
    'turn>=4 and turn<=8 and !slot_a_run', 1800, title='找一个不是来融资的合伙人',
    shared='slot_a_run and a_tang_run')

add('a_tang_name_return', 'payoff', '老唐 · 拿着第一批成品',
    '你答应让他署名的新灯出货了。\n经销商说：「六点半」印大点，老唐可以藏底下。',
    option('把老唐印正面', '他在店里摆了一盏，位置比营业执照还高。第一次有人来问他是不是那个老唐。', (-2, 5, 5, 5), 'tang_name_run and tang_name_keep', '老唐系列｜名字没有藏在灯底。'),
    option('这批先用公司名', '货卖得快了一点。老唐把那盏没名字的灯拿回店，朝墙摆着。', (7, -5, 4, -4), 'tang_hurt_run and tang_hurt_keep'),
    'a_tang_run and a_tang_name_run and age_a>=2', 2400, kind='payoff',
    title='当初答应的话', shared='slot_a_done_run and !a_tang_run')

add('a_tang_teach_return', 'payoff', '罗姐 · 终于修好了',
    '老唐教给她的手艺救了整批货。\n她想把步骤写出来，让新来的人都能学。',
    option('一起写，三人署名', '老唐盯了半天，补了一句：烙铁别放这边，容易烫到自己。', (-2, 7, 3, 4), 'manual_run and tang_name_keep', '一本维修手册｜最后一条是别烫到自己。'),
    option('每周给老唐一堂课', '修理铺开始有了下课铃。老唐嘴上嫌吵，每次比学生来得早。', (-4, 9, 2, 3), 'tang_class_run and tang_class_keep'),
    'a_tang_run and a_tang_teach_run and age_a>=2', 2400, kind='payoff',
    title='把一个人的本事留下来', shared='slot_a_done_run and !a_tang_run')

add('a_floor', 'venture', '你 · 指着车间地面',
    '你想把地板刷成亮白色。\n罗姐刚把一台二手钻床的报价放在桌上。',
    option('先刷，灯要像样', '白地板铺好了。你站在中间看了很久，罗姐用手钻赶完了当天的活。', (-9, -6, 0, 9), 'a_floor_white_run'),
    option('先买钻床，我来刷', '白漆沾了你一裤腿。第一条划痕是你拖机器时弄的，谁也没说。', (-7, 6, 0, 5), 'a_floor_work_run'),
    'turn>=4 and turn<=8 and !slot_a_run', 1800, title='你的怪癖，谁来买单',
    shared='slot_a_run and a_floor_run')

add('a_floor_white_return', 'payoff', '罗姐 · 把灯搬到门外',
    '你坚持刷白的地板不让落灰。\n大家只好去门外打孔。下雨了。',
    option('把门打开，进来干', '第一把铁屑落在白地上。你拿来那张钻床报价，这次没有翻过去。', (-5, 8, 0, -4), 'listen_run', '白地板上的铁屑｜你允许公司弄脏你的理想。'),
    option('搭个棚，地板别动', '棚子搭好了。参观的人夸车间真干净，因为做事的人都在外面。', (-7, -8, 0, 7), 'vanity_run and luo_hurt_keep', '干净的车间｜做事的人在门外。'),
    'a_floor_run and a_floor_white_run and age_a>=2', 2400, kind='payoff',
    title='你想要的样子', shared='slot_a_done_run and !a_floor_run')

add('a_floor_work_return', 'payoff', '罗姐 · 新钻床旁边',
    '你买的钻床快了一倍。\n你裤子上的白漆还是没洗掉。',
    option('穿它去谈客户', '客户问什么材质。你说工作服。罗姐在旁边笑出了声。', (5, 4, 3, 4), 'work_trousers_run', '洗不掉的白漆｜这条裤子后来见过最大的客户。'),
    option('挂墙上当战旗', '周野认真做了铭牌：创始人，亲自动手，一次。', (0, 5, 0, 5), 'trouser_flag_run'),
    'a_floor_run and a_floor_work_run and age_a>=2', 2400, kind='payoff',
    title='总算有个能笑你的东西', shared='slot_a_done_run and !a_floor_run')

add('a_office', 'venture', '你 · 看见一栋通宵亮着的楼',
    '你想把灯卖进那栋最能加班的楼。\n门口的保安只允许快递进。',
    option('穿上快递马甲', '你提着样灯进了电梯。第一次路演，观众是一个正准备辞职的行政。', (-3, 0, 4, 6), 'a_delivery_run'),
    option('给每层寄一盏', '快递单铺了一地。阿岑说这是他见过最费钱的匿名信。', (-7, 0, 6, 5), 'a_gifts_run'),
    'turn>=4 and turn<=8 and !slot_a_run', 1800, title='主动敲一扇不开的门',
    shared='slot_a_run and a_office_run')

add('a_delivery_return', 'payoff', '那位行政 · 发来语音',
    '你混进去送的灯被行政摆在了会议室。\n他们想买整层楼的，但要能被老板远程控制。',
    option('卖灯，不卖遥控', '单子少了一半。留下那半层的人，用私人账户给你付了款。', (9, 3, 5, 5), 'refuse_control_run and promise_kept_run'),
    option('接，先把这单做了', '钱是真的，遥控也是真的。行政告诉你，灯现在每天都亮到最后一个人走。', (18, 0, 9, -9), 'control_run and control_keep', '一只老板遥控器｜灯开始替另一个人做决定。'),
    'a_office_run and a_delivery_run and age_a>=2', 2400, kind='payoff',
    title='大单终于来了，然后呢', shared='slot_a_done_run and !a_office_run')

add('a_gifts_return', 'payoff', '罗姐 · 拿到一张合影',
    '你寄出去的灯被搬到楼顶。\n收件人们自己办了一场不邀请老板的聚会。',
    option('带点吃的上去', '你第一次参加客户活动，不用在自我介绍里加公司名。', (6, 3, 5, 4), 'roof_run and roof_keep', '楼顶合照｜老板没有被邀请，但你被邀请了。'),
    option('给他们留个暗号', '「天台见」成了店里的隐藏备注。罗姐看到这三个字，就知道要多装一颗灯泡。', (7, 2, 6, 4), 'roof_code_run and roof_keep'),
    'a_office_run and a_gifts_run and age_a>=2', 2400, kind='payoff',
    title='灯去了你没去过的地方', shared='slot_a_done_run and !a_office_run')

add('a_night', 'venture', '你 · 翻第一张收据',
    '你想知道第一盏卖出去的灯，还亮不亮。\n电话里，小许说可以来，但她凌晨才到家。',
    option('我等你回来', '你拎着一袋包子等在楼下。三点十七分，她说你比灯还能熬。', (-3, 0, 3, 5), 'a_wait_run'),
    option('让她拍给我看', '她发来一张灯的照片。灯旁边是没洗的杯子，不是你官网上的花。', (0, 0, 3, 4), 'a_photo_run'),
    'turn>=4 and turn<=8 and !slot_a_run', 1800, title='主动去看卖出去之后',
    shared='slot_a_run and a_night_run')

add('a_wait_return', 'payoff', '小许 · 认出你的新广告',
    '你等她下夜班那晚拍的照片，被周野放进广告。\n她问，能不能不要露出门牌号。',
    option('撤掉，再问一遍', '她同意留灯的部分。你们第一份拍摄授权，签在一张包子店小票背面。', (-2, 2, 4, 4), 'consent_run and xu_friend_keep'),
    option('整张都不公开', '她说谢谢，发来另一张。那张没有门牌号，是专门替你拍的。', (0, 0, 5, 5), 'private_photo_run and xu_friend_keep', '没公开的回家照｜不是每一次感动都拿来卖灯。'),
    'a_night_run and a_wait_run and age_a>=2', 2400, kind='payoff',
    title='被信任不是广告授权', shared='slot_a_done_run and !a_night_run')

add('a_photo_return', 'payoff', '阿岑 · 看着顾客照片',
    '你收来的照片里，灯罩被夹了张便条。\n「回来帮我把垃圾带下去。」',
    option('给灯做个便条夹', '你以为它在替人等门，它顺便替人分担了家务。第一批夹子很快用完了。', (-3, 3, 5, 4), 'note_clip_run'),
    option('送她一卷好胶带', '小许回你：老板，这家公司暂时不要变大。你盯着那句话看了很久。', (-1, 0, 4, 5), 'small_wish_run and xu_friend_keep'),
    'a_night_run and a_photo_run and age_a>=2', 2400, kind='payoff',
    title='产品有了自己的生活', shared='slot_a_done_run and !a_night_run')

add('b_expand', 'venture', '你 · 在地图上画了三个圈',
    '你想把六点半开到别的城市。\n孟女士把支票放在地图上：她也要能决定卖什么。',
    option('拿钱，先开三家', '地图变成了施工单。她把自己的椅子搬进了你们的周会。', (16, 3, 5, -4), 'b_funded_run and investor_run', '多出来的椅子｜孟女士出钱，也开始决定。'),
    option('先去一个人手里', '你找了一位外地老顾客，请他开第一个取货点。地址是一家洗衣店。', (-5, 3, 5, 5), 'b_slow_run and independent_run'),
    'turn>=10 and turn<=13 and !slot_b_run', 1600, title='这次是你想变大',
    shared='slot_b_run and b_expand_run')

add('b_funded_return', 'payoff', '孟女士 · 坐在那把椅子上',
    '你让她决定卖什么。\n她想停掉第一款灯，把产线交给她请来的经理。',
    option('把这项权力买回来', '你拿到账上能拿的那笔钱。她收下，留下一句：下次签字，先想好舍不舍得。', (-14, 4, -3, 6), 'bought_back_run and independent_run', '一张回购收据｜你第二次为同一个决定付钱。'),
    option('让经理接新产线', '你保住小车间，把大产线交出去。公司开始有两张彼此不认识的工资表。', (8, -3, 4, -5), 'ceded_run and ceded_keep'),
    'b_expand_run and b_funded_run and age_b>=2', 2400, kind='payoff',
    title='不是突然失去的权力', shared='slot_b_done_run and !b_expand_run')

add('b_slow_return', 'payoff', '洗衣店老板 · 发来照片',
    '你托付给他的取货点，只卖了七盏。\n但七个人约好周六在店里见。',
    option('带着阿岑去', '你们坐在洗衣机旁边改灯。没人拍领导合影，倒有人问下个月还来不来。', (-4, 5, 5, 5), 'community_run and community_keep', '洗衣店的周六｜七个人也能把一张桌子坐满。'),
    option('把工具寄过去', '取货点变成了小修理站。你在地图上的那个圈，终于不是自己画给自己看的了。', (-3, 4, 6, 4), 'community_run and community_keep'),
    'b_expand_run and b_slow_run and age_b>=2', 2400, kind='payoff',
    title='小不是空', shared='slot_b_done_run and !b_expand_run')

add('b_partner', 'venture', '你 · 看新灯的设计图',
    '阿岑做了一盏和你审美完全相反的灯。\n你想拿它试一件比产品更大的事。',
    option('让他开自己的线', '他第一次没问你选哪个颜色，只问你借不借模具。', (-6, 6, 2, 2), 'b_free_run and cen_free_run'),
    option('把它改成我想要的', '他把文件命名为「老板版」。你改到凌晨，觉得终于顺眼了。', (-4, -6, 2, 6), 'b_control_run and cen_control_run'),
    'turn>=10 and turn<=13 and !slot_b_run', 1600, title='你敢不敢不当主角',
    shared='slot_b_run and b_partner_run')

add('b_free_return', 'payoff', '阿岑 · 抱着一箱样品',
    '你让阿岑自己做的灯，卖得比你的好。\n第一场采访，对方只想见他。',
    option('把他推到镜头前', '他紧张得把你的名字说了三次。你站在画面外，第一次没急着纠正他的产品描述。', (8, 9, 5, -3), 'cen_equal_run and cen_equal_keep', '一张没有你的报道｜公司还是你的作品，但不只你的。'),
    option('跟他一起去', '他把第二把椅子拉近了一点。这次你等他讲完，才开口。', (6, 6, 4, 2), 'cen_equal_run and cen_equal_keep'),
    'b_partner_run and b_free_run and age_b>=2', 2400, kind='payoff',
    title='你给出去的自由长大了', shared='slot_b_done_run and !b_partner_run')

add('b_control_return', 'payoff', '阿岑 · 发来两个文件',
    '你改过的「老板版」已经做好。\n另一个文件是他的离职信，没有让你改。',
    option('撤我的稿，留下他', '他没有立刻答应。第二天，原版图纸出现在车间，你没有再碰它。', (-5, 9, 0, -5), 'cen_repaired_run and cen_equal_keep'),
    option('图纸留下，你走', '他交出电脑，只带走了那支焊笔。半年后，你在另一家店里认出了他的线条。', (3, -11, 0, 7), 'cen_left_run and cen_rival_keep', '空下来的工位｜图纸留下了，画图的人没有。'),
    'b_partner_run and b_control_run and age_b>=2', 2400, kind='payoff',
    title='有些东西不能审批', shared='slot_b_done_run and !b_partner_run')

add('b_lie', 'venture', '你 · 彩排新品发布',
    '你想让这次发布像个奇迹。\n样灯还接着一根不能让镜头看见的线。',
    option('线也拍进去', '你说今天还做不到的，就别让大家以为做到了。周野把「颠覆」改成了「施工中」。', (0, 5, -2, 3), 'b_honest_run'),
    option('藏起来，发布再补', '镜头很漂亮。你对着掌声说下个月见，罗姐在台下数还缺的零件。', (8, -4, 9, 5), 'b_hype_run and hype_run', '一根藏起来的线｜你让日程跑在了产品前面。'),
    'turn>=10 and turn<=13 and !slot_b_run', 1600, title='亲手制造一次奇迹',
    shared='slot_b_run and b_lie_run')

add('b_honest_return', 'payoff', '周野 · 收到一封邮件',
    '你没藏那根线，有工程师发来了一张改图。\n他说你们至少没把观众当傻子。',
    option('请他来挑更多错', '他带来三页问题，其中一页你听不懂。阿岑给他搬了把椅子。', (-3, 6, 4, 3), 'engineer_run'),
    option('照图做一次公开实验', '实验第一次没成功。弹幕没有散，等到第二次灯真的亮了。', (-4, 3, 7, 5), 'live_test_run and honest_keep'),
    'b_lie_run and b_honest_run and age_b>=2', 2400, kind='payoff',
    title='不完美反而打开了一扇门', shared='slot_b_done_run and !b_lie_run')

add('b_hype_return', 'payoff', '罗姐 · 新品约定交货日',
    '你发布时藏起的那根线，还拔不掉。\n门口有人举着你的发布会截图。',
    option('出去认，退钱', '有人骂完走了，有人等你说完。罗姐把那根线放到你的桌上，没有再藏。', (-12, 6, -9, -5), 'hype_repaired_run and apology_keep', '拿出来的线｜道歉很贵，继续藏更贵。'),
    option('再给自己一个月', '延期公告用了「更好地相遇」。你把那根线塞回抽屉，罗姐没再说话。', (2, -8, -5, 5), 'hype_debt_run and hype_debt_keep'),
    'b_lie_run and b_hype_run and age_b>=2', 2400, kind='payoff',
    title='掌声不会替你焊接', shared='slot_b_done_run and !b_lie_run')

add('b_future', 'venture', '你 · 收到一份独家合同',
    '你想把灯卖进全国的连锁店。\n条件是：以后不能再在自己的小店卖同款。',
    option('签，让全国看见', '合同寄走。周野第一次把地图缩小到能看见整个国家。', (12, 0, 7, -3), 'b_exclusive_run and exclusive_run'),
    option('另做一款给他们', '罗姐把你叫到机器边：哪一款更好，不许偷偷区别对待。', (-6, 4, 5, 4), 'b_dual_run'),
    'turn>=10 and turn<=13 and !slot_b_run', 1600, title='主动选一扇更大的门',
    shared='slot_b_run and b_future_run')

add('b_exclusive_return', 'payoff', '小许 · 来店里取灯',
    '你签了独家，不能在店里卖她要的那款了。\n连锁店在她家另一头，要换三趟车。',
    option('陪她去一趟', '你第一次沿着自己的渠道走了一遍。回来后，你在地图上重新看了那些漂亮的点。', (-3, 0, 2, 4), 'channel_walk_run'),
    option('退掉这份独家', '违约的钱划走，店门重新挂上那款灯。全国少了几个点，这里多了一个人。', (-13, 3, -6, 6), 'exclusive_broken_run and independent_run', '一张退约单｜你花钱买回了自家店里的那盏灯。'),
    'b_future_run and b_exclusive_run and age_b>=2', 2400, kind='payoff',
    title='地图上的点不等于一个人', shared='slot_b_done_run and !b_future_run')

add('b_dual_return', 'payoff', '罗姐 · 两款灯都做好了',
    '你另做的连锁店版，比原版更受欢迎。\n自家店的顾客也开始问能不能买。',
    option('跟对方谈互相卖', '谈了两天，店里终于摆上两款灯。没人赢下全部，但都能开门。', (7, 3, 5, 2), 'shared_shelf_run'),
    option('给原版一次大改', '阿岑把第一版图纸摊开。你们发现，最早没做成的那个念头，现在做得到了。', (-5, 5, 5, 5), 'original_rebuilt_run'),
    'b_future_run and b_dual_run and age_b>=2', 2400, kind='payoff',
    title='成功也会把自己逼进角落', shared='slot_b_done_run and !b_future_run')

add('b_people', 'venture', '你 · 要招第一批新人',
    '你想让新人第一天就知道这里不一样。\n准备给他们什么？',
    option('能否决我的按钮', '周野买了个红色桌铃。罗姐按了一下试音，你下意识停了嘴。', (-2, 6, 0, 3), 'b_bell_run', '一只红色桌铃｜谁都可以叫停老板。'),
    option('每人一张空图纸', '你说做件不用我点头的东西。第一张交上来的图纸，是一只根本不发光的灯。', (-5, 5, 0, 5), 'b_blank_run'),
    'turn>=10 and turn<=13 and !slot_b_run', 1600, title='把公司变成你想工作的地方',
    shared='slot_b_run and b_people_run')

add('b_bell_return', 'payoff', '罗姐 · 按响了桌铃',
    '你装的否决铃第一次真响了。\n大家不同意你刚拍板的通宵赶工。',
    option('今晚不开工', '你把交期往后挪，亲自给客户打电话。第二天，没人再把那只铃当玩具。', (-6, 9, -3, 3), 'bell_real_run and bell_keep and promise_kept_run', '真的响过的铃｜它否决过买它的人。'),
    option('只破例这一次', '铃还在桌上，但大家学会了什么叫试音。你说完话，屋里很安静。', (6, -8, 3, -5), 'bell_fake_run and bell_fake_keep'),
    'b_people_run and b_bell_run and age_b>=2', 2400, kind='payoff',
    title='你的规矩值不值一笔损失', shared='slot_b_done_run and !b_people_run')

add('b_blank_return', 'payoff', '小陈 · 新人设计师',
    '你让他自由做的「不发光的灯」，其实是关机按钮。\n按一下，办公桌上的屏幕都能睡。',
    option('让他做一小批', '第一位买家是周野。第二位是你，你一直没舍得按。', (-5, 6, 5, 5), 'new_button_run and partner_run'),
    option('先放我桌上试', '六点半，阿岑伸手替你按了。原来公司的安静，需要一个按钮。', (0, 5, 0, -3), 'button_used_run and promise_kept_run'),
    'b_people_run and b_blank_run and age_b>=2', 2400, kind='payoff',
    title='别人也有自己的偏执', shared='slot_b_done_run and !b_people_run')

add('b_buytang', 'venture', '你 · 看老唐的新招牌',
    '老唐的修理铺开始自己卖灯。\n你想抢在大牌之前，把隔壁变成自己人。',
    option('直接买下铺子', '他签了，但把自己的工具单独列了一张清单。那一箱，不卖。', (-11, 3, 5, 5), 'b_tang_buy_run and tang_bought_run'),
    option('互相修对方的灯', '你俩各自留着招牌。两家店中间，第一次挂起了同一张价目表。', (-3, 5, 5, 3), 'b_tang_link_run and tang_friend_keep'),
    'turn>=10 and turn<=13 and !slot_b_run', 1600, title='不只等别人收购你',
    shared='slot_b_run and b_buytang_run')

add('b_tang_buy_return', 'payoff', '老唐 · 站在自家门口',
    '你买下的铺子开始统一装修。\n工人正要拆那块写了三十年的「老唐修灯」。',
    option('旧招牌留下', '新招牌缩小一截。老唐把不卖的工具箱搬了回来，放进原来那个抽屉。', (-2, 6, 3, 3), 'tang_sign_run and tang_name_keep', '两块招牌｜收购没有抹掉另一个人的名字。'),
    option('统一才像一家公司', '招牌卸下来了。老唐抱着它回家，第一次没有顺手替你锁门。', (3, -7, 3, 5), 'tang_erased_run and tang_hurt_keep'),
    'b_buytang_run and b_tang_buy_run and age_b>=2', 2400, kind='payoff',
    title='你买到的是哪一部分', shared='slot_b_done_run and !b_buytang_run')

add('b_tang_link_return', 'payoff', '老唐 · 拿着一盏陌生的灯',
    '你们互修的第一盏，偏偏是大牌的。\n价目表上没有写不修别人家。',
    option('修，按同一个价', '顾客走时买了一盏你的灯。老唐说别记成营销，他不买也得修。', (5, 5, 4, 4), 'tang_link_run and repair_phone_keep'),
    option('拆开，一起学学', '里面有一处做法比你们好。你们安静了一会，然后各自拍了张照。', (2, 5, 3, 5), 'tang_learn_run'),
    'b_buytang_run and b_tang_link_run and age_b>=2', 2400, kind='payoff',
    title='不是非要当赢家的关系', shared='slot_b_done_run and !b_buytang_run')

add('echo_cat_boss', 'echo', '孟女士 · 第一次参观',
    '你任命的董事长正趴在合同上。\n孟女士问，它能代表公司表态吗？',
    option('它比我稳定', '猫在签字处踩了一个爪印。孟女士把那张拿走了，说这份比较可信。', (0, 0, 0, 3), keepsake='有爪印的合同｜董事长第一次履职。'),
    option('别管它，我们签', '你刚伸手就被咬了。全公司第一次看见制衡真的发生。', (0, 2, 0, -2)),
    'cat_boss_run and turn>=9', 850, kind='payoff', title='职位不是白给的')

add('echo_cat_sleep', 'echo', '周野 · 准备拍广告',
    '你招的试睡员在直播镜头前睡着了。\n弹幕比你卖灯时热闹十倍。',
    option('镜头给它', '一小时无人讲话，卖出去九盏。周野申请把猫列为直属领导。', (6, 0, 3, 2)),
    option('镜头留给灯', '猫翻身挡住了灯。弹幕说产品确实助眠，你决定今天不澄清。', (5, 0, 4, 2)),
    'cat_sleep_run and turn>=9', 850, kind='payoff', title='唯一不焦虑的员工')

add('echo_plant', 'echo', '周野 · 重拍团队照',
    '你曾让六盆盆栽冒充员工。\n这次人站满了，盆栽没地方放。',
    option('请资深员工前排坐', '大家每人抱一盆。官网终于换图，老顾客说管理层一位都没走。', (0, 4, 0, 3)),
    option('把盆栽还回去', '老唐数了三遍，说有一盆本来没这么大。原来公司活过了足够它长高的日子。', (0, 3, 0, 4)),
    'plant_run and turn>=9', 850, kind='payoff', title='人真的来了')

add('echo_off_practice', 'echo', '小许 · 新换了工作',
    '你那盏到点灭的灯还在她桌上。\n她说新老板允许大家自己设时间。',
    option('送她一个新开关', '她把时间拨到六点。你做的东西，终于不用靠偷偷摸摸才能成立。', (-2, 0, 4, 5)),
    option('请她来给大家讲讲', '故事讲完，罗姐看了看墙上的钟。你把会议停在了六点半之前。', (0, 5, 0, 4), 'promise_kept_run'),
    'off_run and practice_run and turn>=11', 850, kind='payoff', title='第一次说的话没有白说')

add('echo_home_door', 'echo', '老唐 · 准备关店',
    '你做的那盏谁回来都会亮的灯，认得老唐了。\n他今天故意在门口走了两遍。',
    option('给他一把钥匙', '第三遍他没有停在门口。进来以后，先把歪着的样灯扶正了。', (0, 5, 0, 4), 'tang_friend_keep'),
    option('不揭穿他', '你假装低头干活。灯又亮了一次，像店里多了一个不说话的人。', (0, 2, 0, 5)),
    'home_run and open_door_run and turn>=11 and !tang_hurt_run and !tang_erased_run', 850,
    kind='payoff', title='谁算自己人，灯替你记着')

add('echo_control', 'echo', '那位行政 · 又来找你',
    '你给老板做的遥控器，锁住了下班时间。\n行政问你，能不能偷偷教她解除。',
    option('我来把锁拆了', '你退回那部分定制费。对方老板很生气，行政只回了一个句号，像松了口气。', (-8, 3, -4, 6), 'control_fixed_run and !control_run'),
    option('不能改客户设置', '你把这句话复制进客服话术。阿岑盯着看了一会，问你还记不记得最早为什么辞职。', (3, -4, 0, -6), 'promise_sold_run'),
    'control_run and turn>=11', 850, kind='payoff', title='灯开始像你离开的那家公司')

add('echo_bonus', 'echo', '阿岑 · 发来一张照片',
    '你发第一笔奖金时，他还清了房租。\n今天他终于给自己买了张能躺平的床。',
    option('批准今天不创业', '他第一次没有回工作消息。第二天来得很早，但不是你要求的。', (0, 5, 0, 2)),
    option('让他把链接发群里', '群里突然讨论起床垫。你发现大家想要的未来，比路演里写的小很多。', (0, 4, 0, 3)),
    'bonus_run and turn>=11 and !cen_left_run', 850, kind='payoff', title='那笔钱后来去了哪里')

add('legacy_rival', 'legacy', '{rival} · 以前和你一起画图的人',
    '当年你要图纸、不要画图的人。\n现在他在对面开店，把开业请柬送到了你手里。',
    option('带着新灯去', '你们把灯摆在同一张桌上。这次谁也不能在另一个人的图纸上直接动笔。', (-2, 0, 4, 4), 'rival_met_run'),
    option('送回那支旧焊笔', '快递签收了。下午他回了两个字：收着。你不知道说的是焊笔，还是那段日子。', (0, 0, 0, -3), 'rival_pen_run'),
    'dynasty>1 and cen_rival_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='行业没有失忆', shared='legacy_seen_run')

add('legacy_bet_hit', 'legacy', '采购负责人 · 从山里来',
    '当年那盏不用联网的灯，已经在山里过了一个冬天。\n采购的人循着你的名字，找到了新店。',
    option('这次从你们开始做', '你没先画海报，先问那里冬天有多冷。新公司的第一位回头客，从很远的地方来。', (8, 2, 5, 4), 'mountain_again_run'),
    option('把旧款的维修接过来', '你不再靠它卖出第一笔钱，仍然可以把它修好。采购的人说，这趟没白来。', (4, 3, 4, 3), 'old_repair_run'),
    'dynasty>1 and bet_hit_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='有些回报走得比较慢', shared='legacy_seen_run')

add('legacy_bet_wait_hit', 'legacy', '陌生来电 · 找了你好久',
    '你当年封存的离线灯，有人终于想买。\n不是投资人，是一个连手机信号都没有的值守站。',
    option('把铁盒找出来', '样灯亮了。你高兴了一会，又想到如果当年再烧半年钱，也可能等不到今天。', (11, 3, 5, 5), 'bet_hit_keep and !bet_wait_keep', '迟到的订单｜到了，不等于当年不该停。'),
    option('把旧图纸交给他们', '你赚了设计费，把生产交给别人。不是所有兑现，都需要重开一条产线。', (7, 0, 3, 3), '!bet_wait_keep'),
    'dynasty>1 and bet_wait_keep and lucky_bet_run and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='它没有赶上上一家公司', shared='legacy_seen_run')

add('legacy_bet_wait_miss', 'legacy', '你 · 整理旧仓库',
    '那盏当年没卖出去的离线灯，还在铁盒里。\n世界没有替它安排一个迟来的奇迹。',
    option('放在自己桌上', '它不需要账号，也没有顾客。今晚它照亮了你的新图纸，这就够它先亮一会。', (0, 0, 0, 5), '!bet_wait_keep', '桌上的旧灯｜没有成为传奇，仍然能照明。'),
    option('拆开，零件接着用', '你把其中一个开关焊进新灯。那件事没有以成功结束，也没有全白做。', (3, 2, 0, 2), '!bet_wait_keep'),
    'dynasty>1 and bet_wait_keep and !lucky_bet_run and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='也允许一件事真的没有成功', shared='legacy_seen_run')

add('legacy_tang_hurt', 'legacy', '老唐 · 路过新店',
    '当年你把他的名字从灯上拿掉了。\n这次他没借工具，只在门口看。',
    option('拿把椅子出去', '他坐下，但没进门。你们先聊了天气，没有谁用一句话就原谅了谁。', (0, 2, 0, -2), 'tang_repair_run'),
    option('新灯上留一个空位', '你说这一块给他，他说先别刻。信任这东西，不能先做样品。', (-2, 1, 0, 3), 'tang_repair_run'),
    'dynasty>1 and tang_hurt_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='旧账不都是钱', shared='legacy_seen_run')

add('legacy_tang_name', 'legacy', '老唐 · 带来一个纸包',
    '你当年坚持把他的名字印在灯上。\n新店开张，他送来一块亲手锉的招牌。',
    option('挂在正门', '招牌没抛光。他说这样以后有划痕，也不显得是坏了。', (0, 4, 2, 4), 'tang_sign_again_run', '老唐做的招牌｜没抛光，经得住划痕。'),
    option('请他亲手挂', '他从兜里摸出两颗螺丝。原来来之前，就想过该挂在哪儿。', (0, 5, 0, 4), 'tang_sign_again_run'),
    'dynasty>1 and tang_name_keep and !tang_hurt_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='有人替你记住了好事', shared='legacy_seen_run')

add('legacy_cat', 'legacy', '一只猫 · 没有参加公司交接',
    '你给它办过工牌。\n新店还没挂招牌，它已经占好了椅子。',
    option('工龄连续计算', '它跳上纸箱，踩了两脚。公司倒过、卖过，它从来没失过业。', (0, 3, 0, 4), 'cat_return_run'),
    option('这回我坐椅子', '你坐下三秒就让了。创业可以重新开始，座位不行。', (0, 2, 0, 4), 'cat_return_run'),
    'dynasty>1 and cat_boss_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='真正的连续创业者', shared='legacy_seen_run')

add('legacy_paid', 'legacy', '罗姐 · 来看新铺子',
    '上回你有钱时先补了大家的工资。\n这次还没发招聘，罗姐就问缺不缺人。',
    option('缺你', '她说别说好听的，先看机器。看完以后，她把包放下了。', (-3, 8, 0, 3), 'luo_back_run'),
    option('先帮我挑个靠谱的', '她带来一个徒弟，交代了一句：这个老板以前付过钱，不只是说过。', (-2, 6, 0, 3), 'luo_apprentice_run'),
    'dynasty>1 and paid_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='履历也长在别人心里', shared='legacy_seen_run')

add('legacy_hype', 'legacy', '周野 · 新账号第一条评论',
    '你上回延期时，说过「下个月一定」。\n新灯的评论区有人把那句话又贴了一遍。',
    option('先补上没交的货', '钱花在上一家公司留下的承诺上。新账号没涨粉，倒少了几个每天来问的人。', (-8, 3, 3, 5), '!hype_debt_keep'),
    option('让这批实物说话', '你不开预售，只拍现货。那条评论留在最上面，你没有删。', (-3, 0, 1, 2), 'no_presale_run'),
    'dynasty>1 and hype_debt_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='换账号不等于换个人', shared='legacy_seen_run')

add('legacy_sold', 'legacy', '孟女士 · 在新店外停车',
    '她上次买走了你的公司。\n这次她下车，先问灯多少钱，没问估值。',
    option('这次只卖灯', '她扫码付款。你们第一次做成一笔不用律师坐旁边的生意。', (5, 0, 2, 4), 'meng_customer_run'),
    option('坐会，听个新点子', '她听完说这次更难赚钱。你发现自己并没有因此不想做。', (0, 0, 0, 5), 'meng_idea_run'),
    'dynasty>1 and last_sold_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='行业里的人还在', shared='legacy_seen_run')

add('legacy_closed', 'legacy', '快递员 · 认出了你',
    '上一家关门那天，他帮你搬过最后的纸箱。\n今天来收新店的第一件快递。',
    option('还是寄灯', '他把箱子抱起来，说这回封得比以前好。你在运单上签了自己的名字。', (0, 0, 3, 5), 'courier_again_run'),
    option('先喝口水再走', '他看了看时间，说能坐两分钟。两分钟里，你没有解释为什么又开了。', (0, 2, 0, 4), 'courier_again_run'),
    'dynasty>1 and last_closed_keep and turn>=4 and turn<=8 and !legacy_seen_run', 1850,
    kind='payoff', title='失败不是唯一能认出你的东西', shared='legacy_seen_run')

add('legacy_default', 'legacy', '小许 · 找到你的新地址',
    '她在上一家店买过灯。\n新店的第一条评价是：人还在，换了个地方。',
    option('送她一颗新灯泡', '她说旧的还没坏。你说那就先放着，不急着用。', (-1, 0, 4, 3)),
    option('请她试第一款新品', '她先问价钱，再问晚上会不会晃眼。你喜欢她还是先问这些。', (3, 0, 3, 3)),
    'dynasty>1 and turn>=4 and turn<=8 and !legacy_seen_run', 1840,
    kind='payoff', title='不是完全从零开始', shared='legacy_seen_run')

add('risk_money', 'pressure', '罗姐 · 把工资表翻给你',
    '钱只够再撑一小阵了。\n现在动手，还能不让灯灭得那么难看。',
    option('清仓，把钱收回来', '仓库空了一角，工资发出去。第一版包装盒也卖光了，你没留一箱做纪念。', (23, 3, -6, -3)),
    option('接一单别人的活', '你们替别人焊了三天板子。箱子不印自己的名字，钱照样养自己的人。', (21, -3, 0, -2)),
    'money<=18 and turn<18 and !risk_money_run', 10000, kind='crisis',
    title='先把门撑住', shared='risk_money_run')

add('risk_team', 'pressure', '罗姐 · 这回没拿图纸',
    '愿意跟你干的人越来越少。\n今天她问：你是想做灯，还是想所有人都听你的？',
    option('让大家改一次我的决定', '纸被传了一圈。你发现没人想毁掉公司，只是想不用每次都猜你在想什么。', (-4, 23, 0, -5)),
    option('放掉一批单，先歇', '客户不全理解。留下的人第二天正常来上班，不是提前，也不是通宵。', (-5, 25, -7, -2)),
    'team<=20 and turn<18 and !risk_team_run', 10000, kind='crisis',
    title='不是人力，是人', shared='risk_team_run')

add('risk_market_low', 'pressure', '你 · 看了一天空店',
    '越来越少有人来找你的灯。\n要不要走出这扇门，找一个真的需要它的人？',
    option('带样灯去摆一晚', '你又开始亲自讲怎么用。第二十一个路人停了下来，问有没有暖一点的光。', (-5, 0, 22, 4)),
    option('把店借给老顾客', '他们带着朋友来修灯。有人第一次进这扇门，不是因为广告。', (-3, 3, 20, 2)),
    'market<=15 and turn<18 and !risk_market_low_run', 10000, kind='crisis',
    title='去找，不是等', shared='risk_market_low_run')

add('risk_market_high', 'pressure', '罗姐 · 订单贴满了墙',
    '已经有人等得太久。\n再说一个「没问题」，就是拿前面的人替后面的人垫。',
    option('关掉购买按钮', '周野手抖了一下才按下去。你们第一次少卖一点，却能睡个整觉。', (-4, 5, -23, -3)),
    option('先把一批转给同行', '你逐个打电话说明谁来做。少赚一截，但答应过的日子没有再往后挪。', (-7, 4, -22, 2)),
    'market>=82 and turn<18 and !risk_market_high_run', 10000, kind='crisis',
    title='接得住，才叫你的客人', shared='risk_market_high_run')

add('risk_mind_low', 'pressure', '阿岑 · 把样灯摆回来',
    '你最近只问「这能卖多少」。\n他问你，第一次焊亮它的时候，也先算过吗？',
    option('今晚只做一盏喜欢的', '你没做报价。做到一半，终于又喊他过来看，而不是过来算。', (-4, 3, 0, 22)),
    option('回第一家顾客那里', '她把灯放得很旧，却没舍得换。你终于想起，产品不是只活在报表里。', (-2, 0, 3, 20)),
    'mind<=18 and turn<18 and !risk_mind_low_run', 10000, kind='crisis',
    title='把你自己找回来一点', shared='risk_mind_low_run')

add('risk_mind_high', 'pressure', '罗姐 · 关掉了投影',
    '你已经连说三次「只有我知道」。\n她说：先别开新线，今晚不准你签字。',
    option('把章放她这里', '你第一次空着手回家。第二天那张伟大的计划，看起来没那么非做不可了。', (0, 4, 0, -24)),
    option('让反对的人先讲完', '会议开了很久。没人交辞职信，你也没有签那张押上全部的钱的单子。', (-2, 5, 0, -22)),
    'mind>=84 and turn<18 and !risk_mind_high_run', 10000, kind='crisis',
    title='信念与听不进去，只隔一个晚上', shared='risk_mind_high_run')

add('final_hype', 'finale', '你 · 抽屉里的那根线',
    '你已经为没做好的灯延期两次。\n今天不再发公告，只决定接下来人站在哪儿。',
    option('站门口，把钱退完', '你打开店门，坐在顾客看得见的位置。这次没有说很快就好。', flags='end_repair'),
    option('关门，把灯做完', '你撤掉招牌，留下焊台。以后它能不能再卖，不写在今天的承诺里。', flags='end_pause'),
    'turn>=18 and hype_debt_run', 100000, title='收回你说过的大话')

add('final_split', 'finale', '你 · 空出来的那张桌子',
    '阿岑走后，你把他的工位留了很久。\n对街的新灯今天上市。你准备怎么开始下一段？',
    option('把这边做下去', '你拆掉空桌，腾出一张真的有人用的工作台。不是原谅，是承认他已经不在。', flags='end_split'),
    option('带样灯去开业', '你站在他的店门口。这回你不是老板，他也没有让你改图纸。', flags='end_rival'),
    'turn>=18 and cen_left_run', 99000, title='公司留下了，故事换了一种关系')

add('final_ceded', 'finale', '孟女士 · 带来最后一份合同',
    '你让出去的产线，已经不需要你签字。\n她愿意把小车间也一起买下。你想带走什么？',
    option('拿钱，整家公司归她', '你签了。钱到了自己账户，不是公司账户。第一次，你不用立刻想着拿它去续命。', flags='end_sold'),
    option('只留小车间和名字', '大产线换了招牌。你们把最早的焊台搬回靠窗的位置，今天只接了三单。', flags='end_small'),
    'turn>=18 and ceded_run', 98000, title='你交出去的那一部分')

add('final_bet', 'finale', '你 · 看那张意外的订单',
    '那件没人看好的作品，真的有人需要。\n大公司想连灯、图纸和你一起买走。',
    option('卖给他们，带队去', '你在合同里留下一整页，写人怎么一起走。上楼那天，罗姐没换自己的工具包。', flags='end_summit'),
    option('留下，做下一盏', '你拒绝了那笔能解释一切的钱。明天还得算工资，但这次没人问那行预算为什么没删。', flags='end_own'),
    'turn>=18 and bet_hit_run', 97000, title='这回，你是真的可以选')

add('final_community', 'finale', '你 · 洗衣店的周六',
    '这家公司没铺满地图。\n但有人约好下周还来。你想让它接着长成什么？',
    option('每条街有这样一张桌', '你让取货点各自起名，只在工具箱上贴同一个标记。它开始长大，却没全长成你的样子。', flags='end_shared'),
    option('就先守住这张桌', '你撤掉招商的页面。不是卖不动的借口，是决定只做自己能叫出名字的生意。', flags='end_small'),
    'turn>=18 and community_run', 96000, title='这也是一种规模')

add('final_partner', 'finale', '阿岑 · 两把椅子',
    '公司的下一盏灯，不完全像你想的。\n可它已经能在你不在时继续往前走。',
    option('把决定权真分出去', '这次他不用等你点头才去拿模具。公司第一次不是只靠你不肯睡觉。', flags='end_shared'),
    option('我去开下一间小店', '你把办公室钥匙留在桌上，带走焊笔。门没有为你失效，是你自己不再需要它。', flags='end_next'),
    'turn>=18 and cen_equal_run', 95000, title='不必等被赶走才离开')

add('final_cash', 'finale', '你 · 最后一次盘点',
    '灯还有人买，钱却只够再撑一阵。\n关店和继续，都得由你亲手做，不是等谁批准。',
    option('缩回半间铺子', '你还掉租来的大仓库，把每月要花的钱削到能看得懂。灯没灭，只是照的地方小了。', flags='end_small'),
    option('把该结的都结清', '最后一笔钱给了做事的人。你没有在群里发东山再起，只发了工资到账的截图。', flags='end_closed'),
    'turn>=18 and money<=27', 93000, title='退出也可以是一次决定')

add('final_tired', 'finale', '你 · 半夜没有打开电脑',
    '这家公司还运转得下去。\n但你已经很久没想过一盏新灯是什么样。',
    option('交出去，歇一阵', '你删掉了明天六点的闹钟。没有人把这件事叫做退出赛道，只有你知道终于能睡了。', flags='end_pause'),
    option('回车间，只做产品', '周会不再由你主持。你在灯底签自己的名字，第一次不用签一整份预算。', flags='end_craft'),
    'turn>=18 and mind<=30', 92000, title='不必靠熬死自己证明喜欢')

add('final_money', 'finale', '孟女士 · 等你开口报价',
    '有人想买下你做出来的一切。\n价钱足够让你很久不必再做任何东西。',
    option('卖，先过自己的日子', '你签字时没有流泪。回家的路上，你第一次看一间店，不是在算它能不能开。', flags='end_sold'),
    option('不卖，把钱花在下一款', '你回去给罗姐批了新机器。账上少了一笔钱，白纸上多了一盏还不存在的灯。', flags='end_own'),
    'turn>=18 and money>=64', 91000, title='有钱以后，你还想不想做')

add('final_default_off', 'finale', '你 · 墙上的钟',
    '六点半到了。\n今天不必再向谁证明这盏灯有用。你想先做哪件事？',
    option('让它熄，带大家回家', '你最后一个出门，没有偷偷把灯打开。明天照常营业，今天真的到这里。', flags='end_own'),
    option('把钥匙交给大家', '罗姐接过钥匙，第一句问你明天来不来。你说来，但不用等我才能开门。', flags='end_shared'),
    'turn>=18 and off_run', 90000, title='你最早答应的那件小事')

add('final_default_home', 'finale', '你 · 门口那盏灯',
    '大家都走了，灯还在等你。\n你现在知道，它不可能替你等来所有答案。',
    option('关门，回自己的家', '你从门外看了它一眼。公司今晚不用你守着，也仍然是你做出来的。', flags='end_own'),
    option('把钥匙交给大家', '第二天有人比你先到。灯先为那个人亮起来，你没有觉得自己被取代。', flags='end_shared'),
    'turn>=18 and home_run', 90000, title='你也可以被这盏灯放过')

ENDINGS = {
    'closed': dict(title='灯灭之前', label='把门关好，也是一门手艺',
                   body='纸箱搬走了，墙上的胶带印还在。你把最后一笔该付的钱记在纸上。\n这家公司没有继续，但不是每个人都只记得它关门。', flag='last_closed_keep'),
    'alone': dict(title='公司只剩一个人', label='人 · 没有人愿意留下',
                  body='你想要一家完全照自己意思运转的公司。现在它终于完全听你的了。\n今天的灯，你一个人开，也一个人关。', flag='last_alone_keep'),
    'forgotten': dict(title='展示中的空店', label='客 · 再没有人来',
                      body='灯还亮着，玻璃也擦得很干净。你说不清从哪天起，每个进门的人都只问路。\n这一次，你没有找到需要它的人。', flag='last_closed_keep'),
    'hollow': dict(title='你已经不在里面', label='心 · 没有想做的东西了',
                   body='每一个决定都可以从上一张表里推出来。换谁坐在这里都一样。\n你离开时公司没有出事，只是那张空白图纸，终于没人再等你画。', flag='last_hollow_keep'),
    'overload': dict(title='每一盏都在等', label='客 · 许下的承诺接不住了',
                     body='订单墙盖住了窗。你已经分不清，今天的道歉是在回昨天的人，还是上个月的人。\n你关掉了购买按钮，这次不是限量，是欠下的灯还没做完。', flag='hype_debt_keep'),
    'allin': dict(title='只剩你说可以', label='心 · 再也听不进另一句话',
                  body='最后一张计划上，只剩你的签名。你把所有没回答的问题，都写成了下一次成功会解决。\n罗姐把印章收进抽屉。这次她没有等你同意。', flag='last_allin_keep'),
    'own': dict(title='明天照常营业', label='不是神话，是你的公司',
                body='你没解决创业这件事，只是把一件原本不存在的东西留在了世界上。\n窗边还有那盏歪样灯。明天有人来，你们就给他讲怎么用。', win=True),
    'small': dict(title='半间也够亮', label='不是没长大，是自己选了边界',
                  body='你不再拿地图证明自己。修得完的灯，叫得出名字的人，够发工资的钱。\n公司变小了，有些东西反而终于放得下。', win=True),
    'sold': dict(title='这笔钱归你了', label='把公司卖掉，不等于把人生输掉',
                 body='公司继续开门，招牌下面换了一行小字。你不必假装自己对钱没有兴趣。\n有人问下一步做什么。你说还没想好，第一次这不是一句拖延。', flag='last_sold_keep', win=True),
    'summit': dict(title='从半间铺子到这里', label='这一次，世界真的接住了你',
                   body='电梯上升的时候，你们都不太说话。罗姐的工具包磕到了门，阿岑先笑了。\n那件被问过无数次为什么还不砍掉的作品，终于不用再解释一遍。', flag='last_sold_keep', win=True),
    'shared': dict(title='不用等你才能开门', label='你造出了一家不只属于你的公司',
                   body='有人在你没来时做了一个不错的决定。你有点不习惯，然后发现自己可以去做下一件事。\n最早那盏灯还在，只是开关不只握在你手里。', win=True),
    'next': dict(title='我去隔壁试一件事', label='主动离开，不是被换掉',
                 body='公司有了不靠你也能继续的班底。你带走焊笔，没有带走别人已经坐稳的椅子。\n走出门时，你想到一盏新灯，还没想它能卖多少。', win=True),
    'pause': dict(title='今天先到这里', label='允许自己暂时不往前走',
                  body='你没有宣布永久告别，也没有承诺卷土重来。\n桌灯被拔掉插头。窗外的天亮了，这次不是你又熬过了一夜。'),
    'craft': dict(title='修灯的', label='不当所有人的老板，也能做自己的东西',
                  body='你给新名片删掉一行头衔。别人找你，不再为了预算和人事，而是有一盏灯想请你看看。\n你把工具从抽屉里拿出来，手还记得怎么用。', win=True),
    'repair': dict(title='不再躲在公告后面', label='没能漂亮地赢，至少亲自收场',
                   body='你把欠下的交货和退款一项项划掉。没有人因为你肯负责，就假装自己没受过损失。\n你留下了那个账号，也留下了能找到你的地址。', flag='apology_keep'),
    'split': dict(title='隔着一条街', label='公司活着，伙伴不再是伙伴',
                  body='对面也亮起了一盏灯。你们各自开门，各自忙碌，偶尔会把快递送错。\n你留下了产品，失去了那个会在半夜替你把电路接上的人。', flag='cen_rival_keep'),
    'rival': dict(title='不是朋友，也不是陌生人', label='下一次，不能再替他做决定',
                  body='他收下了你带来的样灯，没有请你剪彩。你看了看他的新作品，有一处做法真的比你好。\n你回到自己的店，摊开图纸。行业比你们的公司活得更久。', flag='cen_rival_keep'),
}


def authored_text(text, card):
    return text.replace('阿岑', '{maker}') if card['thematic'] != 'legacy' else text


def export():
    for card in CARDS:
        for field in ('bearer', 'question', 'answer_yes', 'answer_no'):
            card[field] = authored_text(card[field], card)
    with (HERE / 'cards.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, delimiter=';')
        writer.writeheader()
        writer.writerows(CARDS)
    story_data = dict(cards=META, endings=ENDINGS)
    (HERE / 'story-meta.json').write_text(json.dumps(story_data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sections = ['# 《别叫我老板》完整故事手册', '',
                '这是全分支剧本，会剧透。实际一局只经历其中 18 次决定。', '',
                '主角是你。第一家公司叫六点半。阿岑是第一位搭档；再创业会遇到新搭档，旧人以自己的名字回来。', '',
                '左右不是善恶，也不是答题。`条件`记录后续如何找到你做过的事。', '']
    previous_theme = None
    for card in CARDS:
        if card['thematic'] != previous_theme:
            sections.extend([f"## {card['thematic']}", ''])
            previous_theme = card['thematic']
        sections.extend([f"### {card['card']} · {META[card['card']]['title']}", '',
                         f"**{card['bearer']}**", '', card['question'].replace('\n', '  \n'), '',
                         f"- ← **{card['override_no']}**：{card['answer_no']}",
                         f"- → **{card['override_yes']}**：{card['answer_yes']}", '',
                         f"条件：`{card['conditions']}`", ''])
    sections.extend(['## 尾声', ''])
    for ending in ENDINGS.values():
        sections.extend([f"### {ending['title']}", '', ending['label'], '', ending['body'], ''])
    (HERE / '故事手册.md').write_text('\n'.join(sections), encoding='utf-8')
    print(f'手写卡片 {len(CARDS)} 张；尾声 {len(ENDINGS)} 种。已导出 cards.csv、story-meta.json、故事手册.md')


if __name__ == '__main__':
    export()
