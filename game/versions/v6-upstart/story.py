"""《上位》手写卡牌源：从实习生一路冲到 CEO，再被旧账追上。"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESOURCES = ("cash", "team", "market", "capital")
MAIN_THEMES = {"act1", "act2", "act3", "act4", "act5"}
MAIN_IMPACT_SCALE = 0.35
OPEN_IMPACT_SCALE = 0.75
DIRTY_MARKERS = {
    "credit_hog", "manager_spin", "leader_favor", "kickback", "solo_take",
    "blame_vendor", "promotion_trade", "fake_growth", "leader_protected",
    "files_burned", "media_bought", "board_blackmail", "house_protected",
    "black_ceo", "witness_paid", "vendor_cut", "price_cartel", "old_leader_paid",
}
HEADER = [
    "thematic", "card", "id", "bearer", "conditions", "lockturn", "weight",
    "question", "override_yes", "answer_yes", "yes_cash", "yes_team",
    "yes_market", "yes_capital", "yes_custom", "override_no", "answer_no",
    "no_cash", "no_team", "no_market", "no_capital", "no_custom",
]
CARDS = []
META = {}


def option(label, reply, delta=(0, 0, 0, 0), flags=""):
    parts = [token.strip() for token in flags.split(" and ") if token.strip()]
    flag_tokens = set(parts)
    if ("risk+" in flag_tokens or flag_tokens & DIRTY_MARKERS) and "dirty_route" not in flag_tokens:
        parts.append("dirty_route")
    flags = " and ".join(parts)
    return {"label": label, "reply": reply, "delta": delta, "flags": flags}


def add(name, theme, bearer, question, left, right, condition="", weight=140,
        lock="del", kind="event"):
    card = dict.fromkeys(HEADER, "")
    card.update(
        thematic=theme,
        card=name,
        id=str(len(CARDS) + 1),
        bearer=bearer,
        conditions=condition,
        lockturn=lock,
        weight="" if weight is None else str(weight),
        question=question,
    )
    for side, choice in (("no", left), ("yes", right)):
        card[f"override_{side}"] = choice["label"]
        card[f"answer_{side}"] = choice["reply"]
        card[f"{side}_custom"] = choice["flags"]
        for resource, amount in zip(RESOURCES, choice["delta"]):
            if theme in MAIN_THEMES and amount:
                amount = max(1, round(abs(amount) * MAIN_IMPACT_SCALE)) * (1 if amount > 0 else -1)
            card[f"{side}_{resource}"] = str(amount) if amount else ""
    CARDS.append(card)
    META[name] = {"theme": theme, "title": bearer, "kind": kind}


def ending(name, condition=None, title="", body="", label=None, weight=None):
    label = label or "结束这一局"
    add(
        f"ending_{name}", "endings", title, body,
        option("接受结局", label, flags=f"end_{name}"),
        option("再看一眼", label, flags=f"end_{name}"),
        condition="",
        weight=None,
        kind="ending",
    )
    if condition:
        META[f"ending_{name}"]["trigger"] = condition


def finalize_ending_meta():
    ending_cards = {
        card["card"]: card
        for card in CARDS
        if card["thematic"] == "endings"
    }
    for card in CARDS:
        if card["thematic"] == "endings":
            continue
        for side in ("no", "yes"):
            for raw_token in card[f"{side}_custom"].split(" and "):
                token = raw_token.strip()
                if token.startswith(">_ending_"):
                    key = token[len(">_ending_"):]
                elif token.startswith("end_"):
                    key = token[len("end_"):]
                else:
                    continue
                ending_name = f"ending_{key}"
                if ending_name not in ending_cards:
                    continue
                entry = {
                    "card": card["card"],
                    "side": side,
                    "choice": card[f"override_{side}"],
                    "condition": card["conditions"],
                }
                entries = META[ending_name].setdefault("entries", [])
                if entry not in entries:
                    entries.append(entry)

    for ending_name in ending_cards:
        meta = META[ending_name]
        if meta.get("entries"):
            meta["trigger_type"] = "explicit_choice"
            meta["trigger"] = "显式选择"
        else:
            meta["trigger_type"] = "resource_edge"
            meta.setdefault("trigger", "资源边界")


add(
    "intern_open", "act1", "财务部主管 周启明",
    "八万元市场费报销单，差一个签字。\n主管把笔推给你：今晚把它变成花掉的钱。",
    option("上交审计", "你把单据放进审计邮箱。下午，主管第一次叫你全名。", (0, 4, -2, 2), "clean_route and evidence+ and >_intern_audit"),
    option("先平账，留副本", "你把发票拆成三张。现金到账，副本留在你的云盘里。", (10, -3, 3, 4), "dirty_route and risk+ and evidence+ and >_intern_fix"),
    condition="turn=1", weight=900000, kind="opening",
)
add(
    "intern_audit", "act1", "审计专员 林岚",
    "匿名邮箱里只有一张单据。审计问：你愿不愿意留下名字？",
    option("实名提交", "你签了名。主管没有被立刻开掉，但你的试用期被立刻延长。", (0, 5, 0, 2), "audit_report and clean_courage and >_intern_audit_result"),
    option("匿名就好", "审计收下了证据。你没出名，却多了一张能回头的牌。", (0, 3, 1, 2), "audit_report and >_intern_audit_result"),
    weight=None, kind="main",
)
add(
    "intern_audit_result", "act1", "财务部主管 周启明",
    "主管被叫去喝茶，回来后只问了一句：是不是你？",
    option("看着他说是", "你没有躲。人事部把你调去最缺人的项目组。", (1, 4, 1, 2), "clean_courage and >_intern_promotion"),
    option("装没看见", "你低头整理文件。主管笑了，记住了你的沉默。", (3, 2, 2, 1), "silent_clean and >_intern_promotion"),
    weight=None, kind="main",
)
add(
    "intern_fix", "act1", "财务部主管 周启明",
    "主管把第二张发票递回来：咨询费写高一点，差额算你的辛苦费。",
    option("改成咨询费", "你的工资还没涨，银行卡先多了八千。", (7, -1, 2, 3), "invoice_fixed and risk+ and >_intern_gift"),
    option("让他自己签", "你把笔推回去。主管没骂你，只把你的名字从会议名单删掉。", (0, 3, -1, 1), "invoice_refused and >_intern_gift"),
    weight=None, kind="main",
)
add(
    "intern_gift", "act1", "财务部主管 周启明",
    "项目过了。主管要你用部门卡买一块表，今晚送到他家。",
    option("刷部门卡", "表送到了。你的转正通知也送到了。", (-5, 0, 1, 4), "leader_favor and risk+ and >_intern_promotion"),
    option("发票走私人", "你替他垫了钱。主管说以后会还，像所有不准备还的钱一样。", (-7, 3, 1, 2), "leader_debt and >_intern_promotion"),
    weight=None, kind="main",
)
add(
    "intern_promotion", "act1", "人事经理",
    "正式员工名额只有一个。你的项目报告里，三个人都写了自己。",
    option("把功劳写给团队", "你拿到正式编制。工程师许棠把你的名字写进了项目群公告。", (0, 7, 4, 3), "team_credit and manager_role and >_manager_team"),
    option("把救火写成我的", "你升得更快。许棠在茶水间学会了不再叫你的名字。", (1, -5, 7, 5), "credit_hog and risk+ and manager_role and >_manager_power"),
    weight=None, kind="main",
)

add(
    "manager_team", "act2", "工程师 许棠",
    "你刚拿到正式编制，许棠把一份真实的故障清单放到你桌上：\n‘你要带我们赢，还是只要看起来赢？’",
    option("把他放进核心群", "你把故障清单原样发给客户。许棠第一次在会上替你说话。", (-2, 7, 3, 2), "team_mentor and honest_manager and >_manager_team_review"),
    option("先把数字做漂亮", "你删掉三条红色告警。周启明给你一张新名片：项目负责人。", (5, -4, 7, 4), "manager_spin and risk+ and >_manager_team_review"),
    weight=None, kind="promotion_branch",
)
add(
    "manager_power", "act2", "事业部副总 周启明",
    "周启明没有祝贺你，只把一把客户会议室的钥匙推过来：\n‘替我拿下这个客户，你的名字就能继续往上写。’",
    option("要书面授权", "你让他把承诺写进邮件。第一次，你的晋升速度换成了可追溯的权力。", (2, 2, 6, 5), "power_in_writing and >_manager_power_review"),
    option("先替他扛下来", "你接过钥匙，也接过他的债。周启明在通讯录里给你改了备注：自己人。", (6, -3, 5, 7), "leader_favor and risk+ and >_manager_power_review"),
    weight=None, kind="promotion_branch",
)
add(
    "manager_team_review", "act2", "项目经理 许棠",
    "许棠把客户的追问转给你：他们要的不是漂亮数字，而是明天还能不能上线。",
    option("让他当面解释", "许棠把真实故障讲清楚。客户留下，团队也知道你不会把人藏到报告后面。", (-3, 5, 4, 2), "team_mentor and >_manager_day1"),
    option("替他讲成路线图", "你把故障改名成路线图。许棠没有反驳，只把原版留在自己的硬盘里。", (3, -2, 6, 3), "manager_spin and risk+ and >_manager_day1"),
    weight=None, kind="promotion_branch",
)
add(
    "manager_power_review", "act2", "事业部副总 周启明",
    "周启明把客户会议留给你，却没有把承诺写进授权书：\n‘你先做出结果，手续总会补。’",
    option("把客户拉进邮件", "你让客户成为见证人。周启明不高兴，但再也不能说这只是你的个人承诺。", (2, 3, 5, 3), "power_in_writing and >_manager_day1"),
    option("先替他签字", "你用自己的名字填上空白。周启明的承诺变成你的债，职位也提前升了一格。", (5, -3, 4, 5), "leader_favor and risk+ and >_manager_day1"),
    weight=None, kind="promotion_branch",
)

add(
    "manager_day1", "act2", "事业部副总",
    "你刚接手曜石云的连锁客户项目。吴老板把回扣比例写在报价单背面：拿不拿，今晚就知道。",
    option("按规则招标", "报价贵了一点，但流程干净。周启明说你还不懂生意。", (-7, 5, 4, 2), "clean_procurement and >_manager_clean_bid"),
    option("收回扣，分给组里", "预算像魔术一样变多。每个人的账户里都有了同一个秘密。", (14, 8, 7, 3), "kickback and shared_secret and risk+ and evidence+ and >_manager_dirty_bid"),
    weight=None, kind="main",
)
add(
    "manager_clean_bid", "act2", "采购负责人 吴老板",
    "你拒绝了回扣，吴老板把一份更贵的合规报价放在桌上：\n‘你们公司真准备按规则活？’",
    option("签合规报价", "项目成本上升，客户却愿意把长期合同给你。干净不是便宜，是可续约。", (-8, 5, 8, 3), "clean_procurement and clean_vendor and >_manager_leader"),
    option("换一家供应商", "你保住流程，也失去一周时间。周启明说：你把机会让给了别人。", (-4, 3, 2, 1), "clean_delay and >_manager_leader"),
    weight=None, kind="procurement_branch",
)
add(
    "manager_dirty_bid", "act2", "采购负责人 吴老板",
    "回扣已经进了账。吴老板又发来一条消息：\n‘这次只要你签，下一次我让你自己挑供应商。’",
    option("把钱分给项目组", "每个人都拿到一笔‘项目奖金’。大家笑着收下，笑容里多了一份共同责任。", (8, 6, 4, 2), "shared_bonus and >_manager_leader"),
    option("钱只进自己的口袋", "你把差额转进私人账户。现金更厚，许棠却把会议录音存进了云端。", (12, -6, 5, 4), "solo_take and risk+ and evidence+ and >_manager_leader"),
    weight=None, kind="procurement_branch",
)
add(
    "manager_leader", "act2", "事业部副总",
    "周启明约你去会所谈项目。买单的人，通常也决定谁升职。",
    option("我来买单", "他拍着你的肩说放心。那一晚的账单比你的年薪还高。", (-8, 0, 1, 4), "leader_favor and risk+ and >_manager_crisis"),
    option("把客户请来", "你让客户坐主位。周启明不高兴，但合同第二天盖了章。", (6, 3, 10, 2), "client_first and >_manager_crisis"),
    weight=None, kind="main",
)
add(
    "manager_crisis", "act2", "项目总监",
    "演示前夜，核心工程师崩溃了。明早十点，客户要看一个不存在的功能。",
    option("把事故写成延期", "你让客户看到真实进度。项目没丢，但副总说你没有狼性。", (-4, 8, -3, 1), "honest_crisis and >_manager_report"),
    option("把锅甩给供应商", "演示按时开始。供应商收到律师函，客户收到你的晋升推荐。", (8, -5, 10, 3), "blame_vendor and risk+ and evidence+ and >_manager_report"),
    weight=None, kind="main",
)
add(
    "manager_report", "act2", "事业部副总",
    "季度报告里，你的增长数字被副总改成了他的。\n他问：要功劳，还是要位置？",
    option("公开争回来", "你保住名字，差点失去项目。团队第一次觉得你不是软柿子。", (0, 7, 3, 2), "public_credit and >_manager_promotion"),
    option("换一个总监位置", "你的名字从报告消失，职位从项目经理变成了总监候选人。", (4, -3, 5, 4), "promotion_trade and risk+ and >_manager_promotion"),
    weight=None, kind="main",
)
add(
    "manager_promotion", "act2", "人事经理",
    "副总把一个必败项目塞给你：做成，直接进总监名单；做不成，正好有人负责。",
    option("接下这个烂摊子", "你把失败概率写在纸上，然后签了名。人事部把你列进总监候选。", (-6, 4, 8, 4), "fast_track and director_role and >_director_budget"),
    option("先要资源再接", "你逼周启明把预算和人写进邮件。你慢了一步，但没有把命交出去。", (-3, 6, 4, 3), "resource_demand and director_role and >_director_budget"),
    weight=None, kind="main",
)

add(
    "director_budget", "act3", "董事会秘书",
    "董事会要下季度增长百分之四十。账上没有钱，市场却已经在等。",
    option("砍掉三个项目", "数字不会漂亮，但现金活了。韩董事长把你的名字写进了‘能收拾残局’名单。", (10, -7, -5, 2), "cost_cut and >_director_deputy"),
    option("先做出增长再说", "你把未签的订单写成意向。投资人欢呼，证据也一起长出来。", (12, -2, 12, 3), "fake_growth and risk+ and evidence+ and >_director_deputy"),
    weight=None, kind="main",
)
add(
    "director_deputy", "act3", "猎头",
    "总监位置给你配一个副手。一个忠诚但普通，一个能干但知道太多。",
    option("提拔老同事", "你把许棠放进核心群。他不会抢你的椅子，但会记住你给过他的名字。", (0, 8, 2, 2), "loyal_deputy and >_director_leader"),
    option("挖那个能干的", "你把顾惟挖来。他把客户和数字一起带来，也把一份备用组织架构带来。", (3, 3, 9, 4), "smart_deputy and >_director_leader"),
    weight=None, kind="main",
)
add(
    "director_leader", "act3", "前任副总",
    "周启明被调查了。他私下发来一条消息：‘你要是说实话，我也只能说实话。’",
    option("替他挡一次", "他把董事会的票带给你。你们的名字从此写在同一页。", (4, 2, 0, 4), "leader_protected and risk+ and evidence+ and >_director_audit_dirty"),
    option("把证据交上去", "周启明被带走。韩董事长夸你勇敢，也开始检查你的抽屉。", (0, 5, 2, 3), "leader_exposed and clean_route and >_director_audit_clean"),
    weight=None, kind="main",
)
add(
    "director_audit_clean", "act3", "审计负责人 林岚",
    "审计翻到了那张八万元报销单。\n她没问你是不是英雄，只问：证据要不要留下？",
    option("把证据交全", "你把原始邮件、付款记录和自己的签字一并交出。林岚写下：可整改。", (-9, 4, 0, 3), "audit_closed and risk- and clean_audit and >_director_clean_reckoning"),
    option("只交纸面材料", "你没有撒谎，却只给了她能看见的一半。林岚把缺口标成黄色。", (-3, 1, 1, 2), "audit_partial and evidence+ and >_director_clean_reckoning"),
    weight=None, kind="clean_callback",
)
add(
    "director_audit_dirty", "act3", "审计负责人 林岚",
    "审计翻到了那张八万元报销单。\n她把回扣名单推到你面前：现在补钱，还是让名单继续往上走？",
    option("补回自己的那份", "你把钱退回，却没有供出分到奖金的人。林岚说：这不是结案，是第一行。", (-12, 2, 0, 3), "audit_partial and risk- and evidence+ and >_director_dirty_reckoning"),
    option("把文件烧掉", "纸没了，扫描件还在。林岚把复印件夹进董事会材料。", (-2, 0, 1, 3), "files_burned and risk+ and evidence+ and >_director_dirty_reckoning"),
    weight=None, kind="main",
)
add(
    "director_clean_reckoning", "act3", "审计负责人 林岚",
    "林岚把整改建议分成两栏：公开，或者只给董事会看。\n‘你以后每一次增长，都要从这张表开始。’",
    option("公开整改表", "你让所有部门都看见缺口。速度慢了一点，但没人需要替你猜答案。", (-3, 4, 1, 2), "audit_public and >_director_media"),
    option("先稳住董事会", "你把整改藏在董事会材料里。林岚点头，却把副本发给独立董事。", (2, 1, 3, 3), "audit_private and >_director_media"),
    weight=None, kind="audit_branch",
)
add(
    "director_dirty_reckoning", "act3", "审计负责人 林岚",
    "林岚没有把你交上去，只问一个名字：回扣名单里，谁最先找你？\n你知道她是在给你最后一次选择。",
    option("把周启明写上去", "你交出上级的名字。林岚收下材料，周启明开始给董事会打电话。", (0, 3, 1, 3), "leader_exposed and >_director_media"),
    option("把自己写上去", "你把责任压在自己身上。林岚说：这会让你升得快，也会让你掉得重。", (-4, 1, 0, 4), "scapegoat_ready and >_director_media"),
    weight=None, kind="audit_branch",
)
add(
    "director_media", "act3", "财经记者",
    "唐记者拿着一份采购邮件找你：给一个回应，我可以等；不回应，明早全网都是曜石云。",
    option("买下这个版面", "新闻没发。唐记者收下采访费时说，下一次问题会更具体。", (-10, 0, 5, 3), "media_bought and risk+ and evidence+ and >_director_board"),
    option("让他发", "你的名字上了热搜。董事会没解雇你，因为股价先涨了。", (2, 4, 12, 2), "media_leak and >_director_board"),
    weight=None, kind="main",
)
add(
    "director_board", "act3", "董事长",
    "董事会要一个代理 CEO。董事长说：‘你可以带公司上去，也可以替所有人下去。’",
    option("接受，但公开旧账", "韩董事长把任命书推过来。台下鼓掌，台上的人开始删聊天记录。", (0, 4, 8, 6), "acting_ceo and >_acting_ceo"),
    option("拿旧账换授权", "你把证据摊在桌上，换到预算、人事和一间更大的办公室。", (6, -2, 5, 7), "acting_ceo and board_blackmail and risk+ and evidence+ and >_acting_ceo"),
    weight=None, kind="main",
)

add(
    "acting_ceo", "act4", "董事长",
    "你只有两周时间处理旧账。董事长给你两把钥匙：清算，或者继续利用。",
    option("清掉所有灰账", "你让林岚逐笔补账。现金像血一样流出去，但公司终于能被审计。", (-16, 3, -2, 3), "house_clean and audit_closed and >_acting_crisis"),
    option("先把公司做大", "你把旧账压进并购协议。估值翻倍，风险也翻倍。", (12, -3, 12, 4), "house_protected and risk+ and evidence+ and >_acting_crisis"),
    weight=None, kind="main",
)
add(
    "acting_crisis", "act4", "警方经侦联络人",
    "有人举报了供应商回扣。警察问你：是公司行为，还是你个人行为？",
    option("承担公司责任", "你把签字都认下来。董事会愿意推你上 CEO，也愿意在需要时推你出去。", (-5, 3, 2, 5), "company_liability and scapegoat_ready and >_ceo_crowning"),
    option("交出上级录音", "你打开录音。韩董事长和周启明同时安静下来。", (0, -2, 4, 5), "recording_kept and evidence+ and >_ceo_crowning"),
    weight=None, kind="main",
)
add(
    "ceo_crowning", "act4", "董事会秘书",
    "任命书放在桌上。你从实习生变成 CEO，只差最后一个选择：告诉大家你是谁。",
    option("宣布清账", "你把旧账和整改计划一起发出去。没有掌声，但所有人知道你坐稳了。", (2, 7, 3, 5), "ceo_run and clean_ceo and audit_closed and >_ceo_first_day"),
    option("宣布增长", "你把数字投到大屏幕上。所有人欢呼，只有你知道最下面那行还没解释。", (8, -2, 10, 6), "ceo_run and black_ceo and risk+ and >_ceo_first_day"),
    weight=None, kind="main",
)
add(
    "ceo_first_day", "act5", "董事会秘书",
    "你成为 CEO 的第一天，门口排着三个人：审计、记者，还有一个想要加薪的副手。",
    option("先见审计", "你把会议改名为‘清账会’。顾惟在门外等了两个小时。", (0, 4, -1, 2), "ceo_compliance and >_ceo_day_two"),
    option("先见副手", "你把增长目标交给顾惟。审计只好从门缝里听。", (2, 2, 6, 3), "ceo_growth and >_ceo_day_two"),
    weight=None, kind="main",
)
add(
    "ceo_day_two", "act5", "你的助理",
    "第二天，热搜上出现一句话：‘这家公司，谁都不干净。’",
    option("让它挂着", "你没有公关。离职群开始替你筛掉最怕审计的人。", (-2, 5, 5, 1), "public_pressure"),
    option("立刻压下去", "你买下所有关键词。舆论消失了，账单和证据都还在。", (-8, 0, 4, 2), "risk+ and evidence+ and media_bought"),
    weight=None, kind="main",
)


def open_card(name, bearer, question, left, right, condition="ceo_run and turn>=20", weight=180):
    if name.startswith("callback_") and "ceo_open" not in condition:
        condition = condition.replace("turn>=23", "ceo_open>=1")
    for choice in (left, right):
        choice["delta"] = tuple(
            max(1, round(abs(amount) * OPEN_IMPACT_SCALE)) * (1 if amount > 0 else -1)
            if amount else 0
            for amount in choice["delta"]
        )
        parts = [token.strip() for token in choice["flags"].split(" and ") if token.strip()]
        if "ceo_open+" not in parts:
            parts.append("ceo_open+")
        choice["flags"] = " and ".join(parts)
    one_shot = (
        name.startswith("callback_")
        or name.startswith("final_")
        or name in {"ceo_first_reckoning", "scapegoat_offer", "exit_offer", "handover"}
    )
    add(
        name, "open", bearer, question, left, right, condition=condition,
        weight=weight, lock="del" if one_shot else "8", kind="open_world",
    )


open_card(
    "ceo_first_reckoning", "董事会秘书 叶真",
    "CEO第一晚，叶真把三样东西放到你面前：八万元原单、许棠的故障清单、周启明的聊天记录。\n你先处理哪一件？",
    option("让林岚先看", "你把原件推给审计。第一晚没有掌声，但至少没人能说你删过它。", (-6, 3, -2, 4), "first_reckoning_audit and risk- and evidence+"),
    option("锁进董事长抽屉", "你把三样东西锁起来。叶真没有阻止你，只在交接表上多写了一行。", (4, -2, 4, 5), "first_reckoning_cover and risk+ and evidence+"),
    condition="ceo_run and ceo_open=0", weight=800,
)


open_card(
    "audit_invitation", "审计负责人", "审计部发来邀请：带上电脑，下午三点聊聊你升职前的那八万元。",
    option("带电脑去", "你打开了所有文件。审计说：至少现在你还在控制叙事。", (-10, 3, 0, 8), "audit_cooperate and risk- and evidence-"),
    option("先找律师", "律师收费很贵，但他提醒你：删文件不是补救。", (-6, 0, 0, 10), "lawyer_hired and risk+"),
    condition="ceo_run and turn>=20 and !audit_cooperate", weight=240,
)
open_card(
    "audit_witness", "老同事", "那个被你抢过功劳的同事，如今坐在审计桌对面：我可以证明，也可以不证明。",
    option("给他一笔钱", "他收了。你们都知道这不是最后一笔。", (-8, 3, 0, 8), "witness_paid and risk+ and evidence+"),
    option("请他说实话", "他把报告交上去。你的名声掉了，公司的可信度反而涨了。", (-2, 4, -3, 6), "witness_truth and clean_route"),
)
open_card(
    "audit_ledger", "财务总监", "财务总监找到一本旧账：回扣分给了团队，团队就等于证人。",
    option("让团队补钱", "大家把奖金退回来。你第一次看见共犯也能变成证人。", (-14, -4, 0, 8), "team_repay and audit_closed"),
    option("把责任切给供应商", "你签了一份切割协议。供应商说：我还有你们的聊天记录。", (7, -5, 2, 9), "vendor_cut and risk+ and evidence+"),
)
open_card(
    "audit_prosecutor", "经侦警官", "警官问：你是来解释账的，还是来交证据的？",
    option("交出上级录音", "录音开始播放。你保住了自由，失去了一整层楼的人。", (0, -8, 2, 10), "prosecutor_recording and >_ending_whistle"),
    option("只解释自己", "你说得很完整。警官也听得很完整。", (-5, -2, -1, 3), "personal_statement and risk+"),
    condition="ceo_run and turn>=23 and evidence>=4 and !prosecutor_recording", weight=260,
)
open_card(
    "board_favor", "董事长", "董事长要你把预算权交给他：‘我只是帮你分担。’",
    option("交预算权", "现金安全了，权力少了一半。董事会开始替你做 CEO 的工作。", (4, -2, 0, -15), "budget_surrender"),
    option("送他一笔并购", "他拿到一块没人要的资产，你拿到一票永远的支持。", (-14, 0, 5, 16), "board_asset and risk+"),
)
open_card(
    "board_revolt", "聪明副手", "你的副手拿着一份新组织架构：里面没有你的名字。",
    option("给他 COO 头衔", "他留下了。所有人开始先问他，再问你。", (-2, 4, 2, -10), "deputy_promoted"),
    option("把他调去海外", "他走了，顺手把三位客户和一份备份带走。", (-3, -5, -8, 7), "deputy_exiled and evidence+"),
    condition="ceo_run and turn>=22 and smart_deputy and !deputy_promoted and !deputy_exiled", weight=250,
)
open_card(
    "board_vote", "独立董事", "独立董事说：给我一项人事权，我就支持你继续当 CEO。",
    option("给他人事权", "你保住职位，但每个关键岗位都多了一个老板。", (0, 3, 0, -12), "board_shared_power"),
    option("给他看证据", "他没有拿到人事权，却成为你最危险的盟友。", (-1, 0, 0, 13), "board_evidence"),
)
open_card(
    "team_bonus", "员工代表", "大家知道你拿过回扣。员工代表问：这次奖金，分不分？",
    option("全员分", "所有人都开心了一周。现金只够开心一周。", (-16, 13, 2, 3), "team_shared_money"),
    option("只奖核心", "核心团队留下，其他人开始在匿名论坛写你的名字。", (-5, -8, 1, 10), "team_core_only and risk+"),
)
open_card(
    "team_layoff", "人事总监", "订单还没掉，现金先掉了。要不要裁掉那批最早跟你的人？",
    option("裁掉老员工", "报表好看了。离职群里有人发出那张八万元单据。", (12, -18, -2, 5), "old_staff_cut and evidence+"),
    option("先降薪", "大家留下，但每个人都记住你说过‘只是暂时’。", (4, -8, 0, 2), "salary_cut"),
)
open_card(
    "team_succession", "老同事", "你要出差三个月。谁替你坐在 CEO 的椅子上？",
    option("让忠诚者代理", "他不出错，也不做决定。公司稳住了，增长停了。", (-2, 5, -6, 8), "loyal_successor"),
    option("让能干者代理", "他把公司带得更快。回来时，椅子已经有了他的体温。", (2, 2, 12, -8), "smart_successor and risk+"),
)
open_card(
    "market_fake", "销售总监", "只差一笔大单，季度增长就能达到董事会目标。客户还没签字。",
    option("先把合同发出去", "客户第二天签了。因为他发现不签就会显得自己落后。", (10, -2, 16, 4), "growth_published and risk+ and evidence+"),
    option("等签字再说", "数字没那么漂亮，但你睡得着。投资人不睡。", (-2, 2, 3, -3), "growth_waited"),
)
open_card(
    "market_boom", "客户总监", "订单像洪水一样进来。交付负责人说：再接一单，所有人都会被淹。",
    option("继续接", "市场份额冲上去了。赔偿条款也同时启动。", (7, -8, 18, 2), "overbooked and market_heat+"),
    option("关掉入口", "你拒绝了增长。客户骂你，老员工第一次鼓掌。", (-3, 5, -7, 7), "capacity_protected"),
)
open_card(
    "market_competitor", "竞争对手 CEO", "对手给你一份合作协议，真正的内容只有一句：一起涨价。",
    option("一起涨价", "利润回来了，反垄断部门也来了。", (15, -1, 12, 6), "price_cartel and risk+ and evidence+"),
    option("把协议交出去", "对手先倒霉。你拿到市场份额，也拿到一个永远的仇家。", (4, 2, 11, 9), "competitor_report"),
)
open_card(
    "old_leader", "前任副总", "他从调查名单里消失后，约你吃饭：‘你现在坐的是我的椅子。’",
    option("给他顾问合同", "他拿钱闭嘴。你每个月都要确认他还愿意闭嘴。", (-8, 0, 0, 7), "old_leader_paid and risk+"),
    option("把他赶走", "他笑着离开：‘那我就把故事讲给记者。’", (0, 2, -1, 5), "old_leader_cut and evidence+"),
    condition="ceo_run and turn>=22 and leader_protected", weight=250,
)
open_card(
    "old_reporter", "财经记者", "记者问：你从实习生到 CEO，只用了十八次决定。有没有哪一次后悔？",
    option("承认第一笔钱", "文章标题变成：‘他承认了。’市场却喜欢诚实的坏人。", (0, 3, 8, 6), "public_confession and evidence+"),
    option("说都是团队功劳", "文章没有爆，但你的副手开始认真看你。", (1, 0, 3, 4), "public_deflection"),
)
open_card(
    "old_vendor", "供应商老板", "他把旧回扣账本放在桌上：买回去，还是让它继续流传？",
    option("买回账本", "账本进了保险柜。供应商说，他还有电子版。", (-15, 0, 0, 8), "ledger_bought and risk+ and evidence+"),
    option("让它流传", "你先召开发布会。抢着承认的人，偶尔能挑选叙事。", (-2, 2, 4, 8), "ledger_released and clean_route"),
)
open_card(
    "exit_offer", "大厂收购负责人", "大厂出价三十亿。条件是：你签完交接，就不再追问旧账。",
    option("卖掉公司", "钱到账了。你离开的时候，发现所有旧账都被留在你的名字下面。", (25, -6, 5, 10), "company_sold and >_ending_sold"),
    option("不卖，自己扛", "你留下来。大厂转身把你的价格打到成本线。", (-12, 3, 10, 8), "offer_refused"),
    condition="ceo_run and ceo_open>=7 and !company_sold", weight=360,
)
open_card(
    "handover", "接班人", "你累了。接班人把辞职信和新战略一起放在你面前：签哪一个？",
    option("签交接", "你走下 CEO 的椅子。公司第一次不需要你来做决定。", (2, 8, 2, 8), "handover_done and >_ending_handover"),
    option("再撑一年", "接班人把文件收回去。你看见他把另一份交给了董事会。", (-3, -4, 3, 5), "handover_refused"),
    condition="ceo_run and ceo_open>=7 and loyal_successor", weight=360,
)

# 早期选择的回访：每张只出现一次，且只对做过相应选择的玩家开放。
open_card(
    "callback_team_credit", "工程师 许棠", "你把功劳写给了团队。许棠现在拿着一封外部 offer：\n‘你要我留下，还是继续把我的名字写在脚注里？’",
    option("给他真正的署名", "你把下一场发布会的主讲位让给他。团队第一次把你的背影当成靠山。", (-3, 9, 3, -2), "credit_repaid and team_credit_called"),
    option("给他一个更大的目标", "你没有道歉，只给他一块更大的战场。许棠留下，但开始准备自己的旗帜。", (2, 2, 8, 4), "credit_deferred and team_credit_called"),
    condition="ceo_run and turn>=23 and team_credit and !team_credit_called", weight=430,
)
open_card(
    "callback_credit_hog", "工程师 许棠", "你把救火写成自己的功劳。许棠把当年的故障清单放到董事会桌上：\n‘今天轮到你解释。’",
    option("公开还名", "你在董事会上把功劳一项项还回去。股价没动，团队的眼神变了。", (-2, 8, 2, 1), "credit_returned and credit_hog_called"),
    option("给他升职封口", "许棠拿到头衔，也拿到一份复制件。你买到的是时间，不是忠诚。", (-5, -5, 4, 8), "credit_bought and risk+ and evidence+ and credit_hog_called"),
    condition="ceo_run and turn>=23 and credit_hog and !credit_hog_called", weight=440,
)
open_card(
    "callback_shared_secret", "员工代表 赵宁", "当年分过回扣的人排成一列。赵宁说：\n‘奖金再发一次，我们就替你守口如瓶。’",
    option("把钱分完", "大家拿到最后一笔‘项目奖’。你保住了人心，也把一整层楼变成了证人。", (-18, 12, 2, 2), "secret_paid and risk+ and evidence+ and shared_secret_called"),
    option("让林岚进来", "你把名单交给审计。有人骂你背叛，但第一次没有人能说你删过账。", (-10, -6, -1, 5), "secret_reported and audit_closed and shared_secret_called"),
    condition="ceo_run and turn>=23 and shared_secret and !shared_secret_called", weight=450,
)
open_card(
    "callback_leader_favor", "前任副总 周启明", "周启明从调查名单里消失了。他发来一张酒店房卡：\n‘你能坐上这把椅子，别忘了是谁把你推上去。’",
    option("继续替他挡", "他把两张董事票塞进你手里。你们的名字从此只能一起出现在新闻里。", (-6, 2, 1, 9), "leader_protected_again and risk+ and evidence+ and leader_favor_called"),
    option("把房卡交给林岚", "林岚收下房卡。周启明第一次不再叫你‘自己人’。", (0, -2, 2, 4), "leader_exposed_again and evidence+ and leader_favor_called"),
    condition="ceo_run and turn>=23 and leader_favor and !leader_favor_called", weight=460,
)
open_card(
    "callback_power_in_writing", "董事长 韩柏", "你当年逼周启明把承诺写进邮件。韩柏翻着那封邮件：\n‘你很会留证据，也很会把证据变成筹码。’",
    option("让董事会按邮件办", "你拿到完整预算授权。韩柏没有生气，只把你的任命期缩成了六个月。", (2, 2, 4, 8), "board_written and power_in_writing_called"),
    option("把邮件锁进档案", "你不公开，也不销毁。权力暂时归你，怀疑也暂时归你。", (1, 0, 2, 5), "board_private and power_in_writing_called"),
    condition="ceo_run and turn>=23 and power_in_writing and !power_in_writing_called", weight=400,
)
open_card(
    "callback_clean_procurement", "采购负责人 吴老板", "你当年拒绝回扣。吴老板如今拿着一份全行业最低价：\n‘签我，大家都省事。’",
    option("坚持三家比价", "你错过了最快的报价，却拿到一份能活过审计的合同。", (-5, 4, 5, 3), "clean_vendor_defended and audit_closed"),
    option("给他最后一次机会", "你让他补齐合规文件。吴老板笑了：你终于学会把灰色写成白色。", (4, -2, 7, 4), "vendor_compliance and risk+"),
    condition="ceo_run and turn>=23 and clean_procurement and !clean_vendor_defended", weight=390,
)
open_card(
    "callback_dirty_audit", "审计负责人 林岚", "林岚把回扣名单摊开：你把钱分给过谁，她就知道谁会替你说话。\n‘现在还来得及只交一半。’",
    option("全交", "名单从你手里到了监管邮箱。你失去一群盟友，换来一条不必躲的路。", (-12, -7, -2, 6), "audit_full_disclosure and audit_closed and risk- and evidence+"),
    option("只交自己的", "你把自己写成孤狼。林岚抬头：最危险的从来不是狼，是狼群的账。", (-4, 1, 1, 4), "audit_self_only and risk+ and evidence+"),
    condition="ceo_run and turn>=23 and dirty_route and !audit_full_disclosure and !audit_self_only", weight=470,
)
open_card(
    "callback_clean_audit", "审计负责人 林岚", "你曾经把原始材料交给审计。现在她把一份任命建议放在你面前：\n‘签下去，你会成为最不讨喜的 CEO。’",
    option("签整改令", "你把审计负责人直接报给董事会。公司少了几分速度，多了几分睡眠。", (-6, 5, -2, 7), "audit_champion and audit_closed and risk-"),
    option("先保住增长", "你把整改拆成三个月。林岚同意了，但把每周追踪表发给全员。", (5, 1, 5, 3), "audit_delayed and risk+"),
    condition="ceo_run and turn>=23 and clean_audit and !audit_champion and !audit_delayed", weight=420,
)
open_card(
    "callback_fast_track", "董事会秘书 叶真", "你曾经接下必败项目换跳级。叶真把当年的风险备忘录放回桌上：\n‘现在要不要让市场知道你是怎么赢的？’",
    option("公开风险表", "投资人先骂你，第二天却把长期订单签了。你第一次用真实数字换来资本。", (-4, 3, 6, 6), "risk_published and evidence+"),
    option("继续讲胜利", "掌声更大，脚下更空。叶真把备忘录复印给了独立董事。", (6, -3, 8, 4), "risk_hidden and risk+ and evidence+"),
    condition="ceo_run and turn>=23 and fast_track and !risk_published and !risk_hidden", weight=410,
)
open_card(
    "callback_media_leak", "财经记者 唐未", "你让唐未把采购邮件发出去。热搜退了，截图没有退：\n‘现在给我一个能写进标题的答案。’",
    option("承认链条", "你把周启明、吴老板和自己的签字一起说出来。舆论失控，证据终于不再只在你手里。", (-4, 3, 4, 5), "media_confessed and evidence+ and risk-"),
    option("只讲结果", "你把订单增长讲得很漂亮。唐未笑了：明天的标题会讲过程。", (5, -2, 5, 3), "media_deflected and risk+"),
    condition="ceo_run and turn>=23 and media_leak and !media_confessed and !media_deflected", weight=400,
)
open_card(
    "callback_media_bought", "财经记者 唐未", "你买下了版面。唐未没有发稿，只在邮件里附了一句：\n‘钱能买沉默，买不了时间。’",
    option("把采访费退回", "你把付款记录和采访费一起交给审计。唐未答应给你一次完整回应。", (-5, 2, 2, 5), "media_repaid and evidence+ and risk-"),
    option("再买一年", "你追加预算。公司主页很干净，唐未的硬盘很满。", (-10, -1, 3, 5), "media_retained and risk+ and evidence+"),
    condition="ceo_run and turn>=23 and media_bought and !media_repaid and !media_retained", weight=410,
)
open_card(
    "callback_loyal_deputy", "工程师 许棠", "你提拔了忠诚的许棠。董事会问：如果你明天不能签字，谁替你？",
    option("让许棠代理", "他把所有流程留痕，增长慢了，却没有一笔钱消失。", (-4, 7, -4, 8), "loyal_successor and succession_named"),
    option("把椅子留给自己", "你拒绝写接班人。许棠点头，从今天起只把事实发给董事会。", (3, -3, 2, 5), "succession_blocked and evidence+"),
    condition="ceo_run and turn>=23 and loyal_deputy and !succession_named and !succession_blocked", weight=390,
)
open_card(
    "callback_smart_deputy", "副手 顾惟", "顾惟把备用组织架构又拿了出来：\n‘你给我 COO，还是让我把这份架构发给所有投资人？’",
    option("给他 COO", "顾惟替你挡住日常火线，但董事会开始把他的名字写在你的后面。", (-3, 5, 5, -10), "deputy_promoted and succession_named"),
    option("把他调去海外", "他带走三位客户，临走前把一份备份交给了林岚。", (-2, -6, -7, 6), "deputy_exiled and evidence+"),
    condition="ceo_run and turn>=23 and smart_deputy and !deputy_promoted and !deputy_exiled", weight=450,
)

# CEO 开放段：可继续扩张，也可主动把故事交给别人。
open_card(
    "regulator_notice", "监管联络人", "监管部门发来通知：曜石云的客户合同里，有一页和竞争对手一模一样。\n‘你准备先解释，还是先删掉？’",
    option("交出原始合同", "你把版本记录交上去。对手先被查，你也失去了一部分市场。", (-6, 2, -5, 7), "regulator_cooperate and evidence+"),
    option("让法务重写", "新合同很漂亮，旧版本仍躺在三百个客户的邮箱里。", (5, -2, 4, 6), "contract_rewritten and risk+ and evidence+"),
    condition="ceo_run and turn>=24 and !regulator_cooperate and !contract_rewritten", weight=360,
)
open_card(
    "investor_demand", "投资人代表", "投资人要求你把下一季度的意向订单算进本季度：\n‘所有独角兽都这么做。’",
    option("按签字确认", "数字难看了一季，董事会却第一次知道哪一块是真增长。", (-5, 3, -4, 5), "numbers_real and risk-"),
    option("先算进去", "估值跳了一下。审计问的第一句，是谁改了模型。", (7, -3, 10, 4), "numbers_pulled and risk+ and evidence+"),
    condition="ceo_run and turn>=24 and !numbers_real and !numbers_pulled", weight=360,
)
open_card(
    "board_budget", "董事会主席 韩柏", "韩柏提出最后一笔交易：把曜石云卖给大厂，或者把他从董事会赶出去。\n‘选一个，你的任期都不会一样。’",
    option("支持收购", "你拿到一笔改变人生的钱，也把所有旧账交给了买家。", (15, -3, 4, 8), "sale_supported and company_sold and >_ending_sold"),
    option("联合独立董事", "韩柏失去控制权。你赢得董事会，也继承了他的敌人。", (-5, 4, 2, 12), "chair_removed and evidence+"),
    condition="ceo_run and ceo_open>=7 and !sale_supported and !chair_removed", weight=340,
)
open_card(
    "employee_walkout", "员工代表 赵宁", "凌晨两点，员工把办公区的灯全关了：\n‘我们要的不是团建，是知道谁会替我们签字。’",
    option("公开薪酬和账目", "有人离职，留下的人终于知道自己在为什么加班。", (-8, 6, -2, 5), "pay_transparent and audit_closed"),
    option("发一笔留任奖", "人留下了，匿名帖也留下了。你把沉默变成了一项固定成本。", (-15, 8, 3, 4), "retention_paid and risk+"),
    condition="ceo_run and turn>=25 and !pay_transparent and !retention_paid", weight=330,
)
open_card(
    "competitor_offer", "竞争对手 CEO", "对手递来一份合并方案：你们共享客户，他替你处理历史合规。\n‘两家公司合在一起，谁还分得清第一张单？’",
    option("拒绝并公开", "你失去一条捷径，却把边界画给整个行业看。", (-4, 3, 6, 5), "merger_refused and competitor_report"),
    option("签框架协议", "市场欢呼。法务把你的旧账编号写进了合并尽调清单。", (8, -4, 9, 7), "merger_signed and risk+ and evidence+"),
    condition="ceo_run and turn>=25 and !merger_refused and !merger_signed", weight=330,
)

# 终局卡必须由玩家选择，不把“自动结局”伪装成随机事件。
open_card(
    "final_investigation", "林岚与监管人员", "调查材料已经足够厚。林岚把两条路写在纸上：\n交出所有人，或者把最后一份备份带进看守所。",
    option("交出录音和账本", "你按下发送。周启明、吴老板和韩柏的名字一起亮起，自己的名字也在第一行。", (0, -8, 1, 4), "final_whistle and >_ending_whistle"),
    option("替所有人扛下", "你没有再看任何人的消息。凌晨六点，门铃响了。", (-5, -4, -2, 3), "final_arrest and >_ending_arrest"),
    condition="ceo_run and ceo_open>=7 and risk>=4 and evidence>=5 and !scapegoat_ready and !final_whistle and !final_arrest", weight=980000,
)
open_card(
    "scapegoat_offer", "董事长 韩柏", "韩柏把一份责任确认书推到你面前：\n‘签下去，公司的名字会留下；不签，所有人的名字都会留下。’",
    option("替公司签字", "你把最后一页签上自己的名字。董事会散会时，韩柏没有和你握手。", (-3, -3, 1, 3), "scapegoat_taken and >_ending_scapegoat"),
    option("把原件交给监管", "你把确认书和董事会聊天记录一起交出。韩柏终于叫了你的全名。", (-2, -5, 1, 5), "scapegoat_refused and evidence+ and >_ending_whistle"),
    condition="ceo_run and ceo_open>=7 and scapegoat_ready and risk>=5 and evidence<6 and !scapegoat_taken and !scapegoat_refused", weight=975000,
)
open_card(
    "final_clean", "董事会主席 韩柏", "清账完成，审计报告没有红字。韩柏问你最后一次：\n‘你要把公司交给市场，还是把它交给自己？’",
    option("继续做 CEO", "你签下长期任命。没有人鼓掌，但每个数字都能找到来源。", (0, 2, 3, 3), "final_clean_ceo and >_ending_clean_ceo"),
    option("卖给大厂", "你带着一笔干净的钱离场。买家买走公司，没买走你的名字。", (8, -3, 4, 2), "final_clean_sale and company_sold and >_ending_sold"),
    condition="ceo_run and ceo_open>=7 and clean_ceo and audit_closed and !dirty_route and risk<3 and !final_clean_ceo and !final_clean_sale", weight=970000,
)
open_card(
    "final_black", "投资人代表", "现金、订单和董事会的票都在你手里。投资人问：\n‘现在把公司卖掉，还是把这套玩法做成帝国？’",
    option("继续扩张", "你把灰账藏进更大的交易。没人敢说你赢得不漂亮。", (4, 1, 6, 3), "final_black_empire and >_ending_black_empire"),
    option("把账交出去", "你把最后一份备份发给记者。你终于不用再记谁欠你一个人情。", (-2, -5, 2, 3), "final_black_whistle and >_ending_whistle"),
    condition="ceo_run and ceo_open>=7 and dirty_route and risk>=4 and evidence<7 and !final_black_empire and !final_black_whistle", weight=960000,
)
open_card(
    "final_board", "独立董事 叶真", "你已经坐了很久。叶真把交接协议推来：\n‘主动走，或者等董事会用一场投票替你走。’",
    option("签交接", "你把钥匙交给接班人。掌声很轻，但没有人追着你要旧账。", (1, 6, 1, 4), "final_handover and >_ending_handover"),
    option("再赌一把", "你赢下这次表决，代价是董事会从此只剩下你的回声。", (-3, -4, 4, 5), "final_board_puppet and >_ending_board_puppet"),
    condition="ceo_run and ceo_open>=8 and !final_handover and !final_board_puppet", weight=940000,
)

ending("cash_zero", "cash=0", "现金断裂", "工资、供应商和律师同时上门。你从实习生一路签上来的每一张单，终于一起找你兑现。", "接受现金断裂")
ending("cash_max", "cash=100", "账目无法解释", "账上多出的钱足以买下半个行业，却解释不了第一张八万元报销单。审计在门口等你。", "接受审计")
ending("team_zero", "team=0", "团队散伙", "最后一个同事把工牌放在桌上：不是因为你最坏，而是因为没人知道下一次谁会被你牺牲。", "接受团队散伙")
ending("team_max", "team=100", "派系逼宫", "所有人都忠于你，也都拿着一张你的秘密。董事会一致同意：公司不能再由你一个人领导。", "接受派系逼宫")
ending("market_zero", "market=0", "失去价值", "业绩归零。董事会不再需要解释你的过去，只需要找一个更便宜的人。", "接受失去价值")
ending("market_max", "market=100", "爆单崩盘", "订单和承诺一起爆表。客户开始排队起诉，销售总监还在问要不要再签一单。", "接受爆单崩盘")
ending("capital_zero", "capital=0", "被架空", "你仍然是 CEO，直到门禁失效。董事会说这是一次平稳交接。", "接受被架空")
ending("capital_max", "capital=100", "所有人联合防你", "你终于拥有所有权力，于是所有人开始拥有同一个目标：不要让你继续拥有更多。", "接受联合防你")
ending("arrest", None, "东窗事发", "经侦在凌晨六点敲门。你坐上 CEO 用了十八次决定，离开公司只用了一副手铐。", "接受逮捕", weight=650000)
ending("scapegoat", None, "替罪羊", "所有人都做过。只有你在最关键的那张单子上签了字。", "接受替罪羊", weight=640000)
ending("clean_ceo", None, "清白上位", "你没有变成好人，只是每次都让证据留下来。公司活下来了，董事会终于只能叫你 CEO。", "接受清白上位", weight=630000)
ending("black_empire", None, "黑账帝国", "你把每一笔灰色收入都变成了更大的权力。没人能证明你清白，也没人敢证明你有罪。", "接受黑账帝国", weight=620000)
ending("whistle", None, "举报者", "你交出录音和账本。公司被拆开，旧领导被带走，而你终于不用再记谁欠你一个人情。", "接受举报者", weight=610000)
ending("sold", None, "卖掉一切", "三十亿到账。你离开了公司，却发现买家把你的名字留在了所有旧账的第一页。", "接受卖掉一切", weight=600000)
ending("handover", None, "主动交棒", "你把椅子留给接班人。最难得的不是坐上 CEO，而是让公司在你离开后仍然做决定。", "接受主动交棒", weight=590000)
ending("board_puppet", None, "董事会木偶", "你保住了 CEO 的头衔，却失去了预算、人事和最后一句自己的话。每次投票都通过，唯独没人再问你。", "接受被架空")


COMPACT_COPY = {
    "intern_open": ("财务主管", "八万报销单，差一个签字。", "交给审计", "主管会记住你。", "先把账做平", "钱到账了，副本在你手里。"),
    "intern_audit": ("审计专员", "审计问：这张单是谁的？", "实名", "你签了名，试用期延长。", "匿名", "没人知道是你。"),
    "intern_audit_result": ("财务主管", "主管回来问：是你举报的？", "承认", "你被调去救火。", "装傻", "他记住了你的沉默。"),
    "intern_fix": ("财务主管", "主管要你把咨询费写高一点。", "照办", "八千进了你的账户。", "让他签", "你被移出会议。"),
    "intern_gift": ("财务主管", "主管要你刷部门卡买表。", "刷卡", "表到了，转正也到了。", "自己付", "钱先由你垫着。"),
    "intern_promotion": ("人事经理", "正式员工只留一个名额。", "算团队的", "你留下，许棠替你说话。", "算我的", "你升得快，许棠不再替你说话。"),
    "manager_team": ("许棠", "许棠递来故障清单：报真数吗？", "报真数", "客户留下，许棠站你这边。", "修数字", "红灯少了，项目归你。"),
    "manager_power": ("周启明", "副总给你客户会议室钥匙。", "要书面授权", "承诺留在邮件里。", "收下钥匙", "你成了他的自己人。"),
    "manager_team_review": ("许棠", "客户问：明天能上线吗？", "让他实话实说", "客户留下了。", "换个说法", "报告好看了，原件还在许棠手里。"),
    "manager_power_review": ("周启明", "副总说：先做，手续以后补。", "抄送客户", "客户也看到了承诺。", "先签字", "位置升了，债也来了。"),
    "manager_day1": ("事业部副总", "供应商把回扣写在报价背面。", "按规则来", "报价高了，副总不高兴。", "收下分掉", "大家都拿了钱。"),
    "manager_clean_bid": ("吴老板", "合规报价贵了两成。", "照签", "贵一点，合同长一点。", "换供应商", "省了钱，慢了一周。"),
    "manager_dirty_bid": ("吴老板", "回扣到账了。钱怎么分？", "分给大家", "这一层楼都有份。", "自己留着", "现金多了，许棠留了录音。"),
    "manager_leader": ("事业部副总", "副总约你去会所谈项目。", "我来买单", "他替你说了句好话。", "请客户来", "客户签了，副总黑脸。"),
    "manager_crisis": ("项目总监", "明早演示，功能还没做。", "报延期", "客户没走，副总骂你。", "推给供应商", "演示过了，律师函发出去了。"),
    "manager_report": ("事业部副总", "副总把你的增长写成他的。", "要回名字", "名字回来了，项目差点没了。", "换总监位置", "报告没你，升职名单有你。"),
    "manager_promotion": ("人事经理", "必败项目，做成就升。", "接", "你进了总监名单。", "先要资源", "慢一步，少背一口锅。"),
    "director_budget": ("董事会秘书", "董事会要增长四成。", "砍项目", "现金活了，数字难看。", "先报增长", "估值涨了，审计也来了。"),
    "director_deputy": ("猎头", "副手选老实的，还是能干的？", "用老同事", "许棠稳，但慢。", "挖能干的", "顾惟带着客户来了。"),
    "director_leader": ("前任副总", "周启明被查，来找你说情。", "替他挡", "他给你一张董事票。", "交证据", "他被带走，董事长查你。"),
    "director_audit_clean": ("林岚", "审计找到第一张八万单。", "交原件", "报告可整改。", "只交报表", "审计标黄，继续追查。"),
    "director_audit_dirty": ("林岚", "回扣名单在桌上。补钱，还是继续？", "补自己的", "钱退了，名单还在。", "烧掉", "纸没了，扫描件还在。"),
    "director_clean_reckoning": ("林岚", "整改表要公开吗？", "全公司看", "大家看见了缺口。", "只给董事会", "林岚点头，副本发出去了。"),
    "director_dirty_reckoning": ("林岚", "回扣名单里，先写谁？", "写周启明", "上级先倒霉。", "写自己", "董事会会先找你。"),
    "director_media": ("财经记者", "记者拿着采购邮件来问。", "买版面", "新闻没发，账单留下了。", "让他发", "热搜来了，股价也涨了。"),
    "director_board": ("董事长", "董事会要代理 CEO。", "公开旧账", "任命书来了，大家开始删记录。", "拿旧账换权", "预算和人事权到手。"),
    "acting_ceo": ("董事长", "两周内，旧账怎么处理？", "全部补账", "现金少了，审计能进门。", "压进交易", "估值涨了，审计材料也多了。"),
    "acting_crisis": ("经侦", "经侦问：责任算公司，还是算你？", "认公司责任", "董事会推你上台，也留替罪羊口子。", "交出上级录音", "上司被查，你保住自由。"),
    "ceo_crowning": ("董事会秘书", "任命书到了。你要先说什么？", "先说清账", "公司知道你要查账。", "先说增长", "掌声很大，底账没变。"),
    "ceo_first_day": ("董事会秘书", "上任第一天，三个人等你。", "先见审计", "顾惟等了两个小时。", "先见副手", "审计只好等。"),
    "ceo_day_two": ("助理", "热搜说：这家公司没人干净。", "不回应", "离职群先替你回应了。", "压热搜", "帖子没了，账单还在。"),
    "ceo_first_reckoning": ("叶真", "原单、故障单、聊天记录，先处理哪份？", "交给审计", "原件进了审计室。", "先锁起来", "交接表多了一行。"),
    "audit_invitation": ("审计负责人", "审计叫你带电脑来。", "带电脑", "文件全摊开了。", "先找律师", "律师说：别删文件。"),
    "audit_witness": ("老同事", "被你抢过功劳的人来作证。", "给钱", "他收了，价格会再涨。", "让他说", "名声掉了，报告可信了。"),
    "audit_ledger": ("财务总监", "回扣分过的人，都是证人。", "让大家退钱", "奖金回来了，证人也多了。", "甩给供应商", "协议签了，聊天记录还在。"),
    "audit_prosecutor": ("经侦", "警官要上级录音。", "交出录音", "上级被查，你保住自由。", "只交自己的材料", "你说完了，调查继续。"),
    "board_favor": ("董事长", "董事长要拿走预算权。", "交出预算权", "钱安全了，位置空了。", "送他一单并购", "他拿资产，你拿一票。"),
    "board_revolt": ("副手", "副手拿来一份没有你的架构。", "任命 COO", "他留下，大家先找他汇报。", "调海外", "他带走客户和备份。"),
    "board_vote": ("独立董事", "交一项人事权，换你留任。", "交出人事权", "你留下，多了一个老板。", "给他看证据", "他不拿人事权，开始查你的账。"),
    "team_bonus": ("员工代表", "大家知道你拿过回扣。奖金分不分？", "全员分", "奖金发完，现金只够一周。", "只奖核心", "核心留下，论坛开帖。"),
    "team_layoff": ("人事总监", "订单没掉，现金先掉。裁谁？", "裁老员工", "报表好看，旧单上网。", "先降薪", "人留下，记住了这句话。"),
    "team_succession": ("老同事", "你出差三个月，谁代 CEO？", "用忠诚的", "公司稳，增长停。", "用能干的", "他做得快，椅子变热。"),
    "market_fake": ("销售总监", "大单未签，季度差一点。", "把意向单算进去", "估值先涨，审计来问。", "等客户签字", "数字难看，账清楚。"),
    "market_boom": ("客户总监", "订单太多，再接会延期。", "继续接", "份额涨了，赔偿也来了。", "关入口", "客户骂你，老员工鼓掌。"),
    "market_competitor": ("竞争对手", "对手提议一起涨价。", "一起涨", "利润回来了，反垄断来了。", "交给监管", "对手先倒霉，你多了仇家。"),
    "old_leader": ("前任副总", "前任说：这把椅子原来是我的。", "签顾问合同", "他闭嘴了，每月收钱。", "赶走他", "他去找记者。"),
    "old_reporter": ("财经记者", "记者问：后悔哪一步？", "认第一笔钱", "标题有了，股价没跌。", "都算团队的", "文章没爆，副手开始查你。"),
    "old_vendor": ("供应商", "供应商拿着旧账本来。", "买下来", "纸在保险柜，电子版在外面。", "让它公开", "你先开发布会。"),
    "exit_offer": ("大厂收购负责人", "大厂出三十亿，条件是不查旧账。", "卖掉", "钱到账，名字留在旧账上。", "不卖", "大厂把你的价格打下去。"),
    "handover": ("接班人", "接班人递来交接书。", "签交接", "椅子有人接了。", "再撑一年", "他把另一份交给董事会。"),
    "callback_team_credit": ("许棠", "许棠拿着外部 offer。", "给他署名", "他主讲发布会。", "给他大项目", "他留下，负责新项目。"),
    "callback_credit_hog": ("许棠", "许棠把旧故障单放上董事会桌。", "还他功劳", "你在会上把名字还回去。", "升职封口", "头衔有了，复印件也有了。"),
    "callback_shared_secret": ("赵宁", "拿过回扣的人来要第二笔。", "再分一次", "全楼都是证人。", "叫审计", "名单交出去了。"),
    "callback_leader_favor": ("周启明", "周启明发来一张房卡。", "继续替他挡", "两张董事票到手。", "交给林岚", "他不再叫你自己人。"),
    "callback_power_in_writing": ("韩柏", "韩柏翻出你留的邮件。", "按邮件办", "预算到手，任期缩短。", "锁进档案", "权限暂时归你，韩柏开始盯你。"),
    "callback_clean_procurement": ("吴老板", "吴老板拿来最低价，是否复核？", "三家比价", "慢一点，合同干净。", "直接给机会", "低价过审，回扣疑云还在。"),
    "callback_dirty_audit": ("林岚", "回扣名单摊开：交全名单，还是只交自己？", "交完整名单", "名单进审计，盟友全暴露。", "只交自己", "你成唯一证人。"),
    "callback_clean_audit": ("林岚", "林岚要你签整改令。", "现在签", "公司慢一点，夜里安静。", "保住增长", "整改表每周来。"),
    "callback_fast_track": ("叶真", "当年的风险表又回来了。", "公开", "投资人先骂，订单后签。", "继续讲胜利", "掌声大，独董先看表。"),
    "callback_media_leak": ("唐未", "记者要采购稿的标题。", "公开签字链", "签字链上了新闻。", "只讲结果", "细节迟早被追。"),
    "callback_media_bought": ("唐未", "你买过一个版面。现在还买吗？", "退采访费", "付款记录进审计。", "再买一年版面", "主页干净，付款记录更多。"),
    "callback_loyal_deputy": ("许棠", "董事会问：谁能替你签字？", "让许棠代理", "流程完整，增长慢了。", "我自己来", "许棠只给董事会发事实。"),
    "callback_smart_deputy": ("顾惟", "顾惟拿出备用架构。", "任命他 COO", "他替你挡火，董事会开始叫他的名字。", "调去海外", "客户和备份一起走。"),
    "regulator_notice": ("监管联络人", "监管发现合同一模一样。", "交原件", "对手被查，你也丢客户。", "重写合同", "新合同漂亮，旧合同还在。"),
    "investor_demand": ("投资人代表", "投资人要把意向单算进本季。", "按签字算", "数字难看，账清楚。", "先算进去", "估值涨了，审计来问。"),
    "board_budget": ("韩柏", "韩柏要卖公司，或离开董事会。", "支持收购", "钱到手，旧账交割。", "联合独董", "韩柏走了，敌人留下。"),
    "employee_walkout": ("赵宁", "员工关灯，要求看清账目。", "公开账目", "有人走，留下的人安心。", "发留任奖", "人留下，匿名帖也留下。"),
    "competitor_offer": ("竞争对手", "对手提议合并，愿意替你处理旧账。", "拒绝并公开", "合并告吹，旧账公开。", "签合并框架", "市场欢呼，尽调开始。"),
    "final_investigation": ("林岚", "调查材料够了。林岚等你一句话。", "交出全部", "录音和账本一起发出。", "自己扛", "凌晨六点，门铃响。"),
    "scapegoat_offer": ("韩柏", "韩柏递来责任书。", "签自己的名字", "公司留下，你也留下。", "交给监管", "聊天记录一起出门。"),
    "final_clean": ("韩柏", "审计报告没红字。继续，还是卖？", "继续做", "任命书签了，数字有出处。", "卖给大厂", "钱到账了，旧账仍挂你名下。"),
    "final_black": ("投资人代表", "现金和董事票都在你手里。", "继续扩张", "你把旧账并进新交易。", "把账交出", "记者收到最后一份备份。"),
    "final_board": ("叶真", "叶真推来交接协议：主动走，还是押一把？", "签交接协议", "接班人接手。", "再赌一把", "投票赢了，董事会接管。"),
    "ending_cash_zero": ("财务总监", "工资发不出来。", "结束", "公司停摆。", "再看一眼", "公司停摆。"),
    "ending_cash_max": ("财务总监", "账上钱太多，解释不清。", "结束", "审计进门。", "再看一眼", "审计进门。"),
    "ending_team_zero": ("人事总监", "最后一个人也走了。", "结束", "办公室空了。", "再看一眼", "办公室空了。"),
    "ending_team_max": ("人事总监", "所有人都听你的。", "结束", "所以所有人一起逼宫。", "再看一眼", "所以所有人一起逼宫。"),
    "ending_market_zero": ("市场总监", "没人买你的东西。", "结束", "董事会换人。", "再看一眼", "董事会换人。"),
    "ending_market_max": ("交付负责人", "订单超过交付能力。", "结束", "客户开始索赔。", "再看一眼", "客户开始索赔。"),
    "ending_capital_zero": ("董事长", "董事会七票换人。", "结束", "你被架空。", "再看一眼", "你被架空。"),
    "ending_capital_max": ("董事长", "你拿了所有权力。", "结束", "所有人开始防你。", "再看一眼", "所有人开始防你。"),
    "ending_arrest": ("东窗事发", "凌晨六点，门铃响。", "结束", "经侦带走了你。", "再看一眼", "经侦带走了你。"),
    "ending_scapegoat": ("替罪羊", "责任书上只有你的名字。", "结束", "你替所有人签了。", "再看一眼", "你替所有人签了。"),
    "ending_clean_ceo": ("清白上位", "账清了，任命书来了。", "结束", "你坐稳 CEO。", "再看一眼", "你坐稳 CEO。"),
    "ending_black_empire": ("黑账帝国", "灰账养大了公司。", "结束", "没人敢查你。", "再看一眼", "没人敢查你。"),
    "ending_whistle": ("举报者", "你把录音和账本交了。", "结束", "旧领导先被带走。", "再看一眼", "旧领导先被带走。"),
    "ending_sold": ("卖掉一切", "三十亿到账。", "结束本局", "买家接手公司，旧账仍挂你名下。", "结束本局", "买家接手公司，旧账仍挂你名下。"),
    "ending_handover": ("主动交棒", "接班人接过钥匙。", "结束本局", "董事会开始让他签字。", "结束本局", "董事会开始让他签字。"),
    "ending_board_puppet": ("董事会木偶", "你还是 CEO，预算和人事归董事会。", "结束本局", "董事会替你决定。", "结束本局", "董事会替你决定。"),
}


def apply_compact_copy():
    card_names = {card["card"] for card in CARDS}
    missing = card_names - set(COMPACT_COPY)
    extra = set(COMPACT_COPY) - card_names
    if missing or extra:
        raise RuntimeError(f"短卡文案不完整：缺少 {sorted(missing)}；多余 {sorted(extra)}")
    for card in CARDS:
        bearer, question, no_label, no_reply, yes_label, yes_reply = COMPACT_COPY[card["card"]]
        if card["thematic"] == "endings":
            no_label = yes_label = "结束本局"
        card.update(
            bearer=bearer,
            question=question,
            override_no=no_label,
            answer_no=no_reply,
            override_yes=yes_label,
            answer_yes=yes_reply,
        )
        META[card["card"]]["title"] = bearer


apply_compact_copy()
finalize_ending_meta()


def export():
    with (HERE / "cards.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, delimiter=";")
        writer.writeheader()
        writer.writerows(CARDS)
    (HERE / "story-meta.json").write_text(
        json.dumps({"cards": META}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sections = ["# 《上位》完整故事手册", "", "从实习生开始，左右每一次都不是善恶题，而是上位速度与后果的交换。", "", "## 资源", "", "现金、团队、市场、资本四条槽仍为 0–100。资源触底或爆表优先于剧情结局标记；风险和证据藏在卡牌后果里。", ""]
    previous = None
    for card in CARDS:
        if card["thematic"] != previous:
            sections.extend([f"## {card['thematic']}", ""])
            previous = card["thematic"]
        meta = META.get(card["card"], {})
        trigger_lines = []
        if card["thematic"] == "endings" and meta.get("entries"):
            trigger_lines.append("触发：显式选择")
            for entry in meta["entries"]:
                trigger_lines.append(
                    f"- `{entry['card']}` → **{entry['choice']}**；入口条件：`{entry['condition'] or '无'}`"
                )
        else:
            condition = meta.get("trigger", card["conditions"])
            trigger_lines.append(f"触发：`{condition or '无'}`")
        sections.extend([
            f"### {card['card']}", "", f"**{card['bearer']}**", "",
            card["question"].replace("\n", "  \n"), "",
            f"- ← **{card['override_no']}**：{card['answer_no']}",
            f"- → **{card['override_yes']}**：{card['answer_yes']}", "",
            *trigger_lines, "",
        ])
    (HERE / "故事手册.md").write_text("\n".join(sections), encoding="utf-8")
    print(f"cards: {len(CARDS)}; endings: {sum(c['thematic'] == 'endings' for c in CARDS)}")


if __name__ == "__main__":
    export()
