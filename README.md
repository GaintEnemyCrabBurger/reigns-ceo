# Reigns CEO

四个独立试玩入口，共用最初的左右划卡玩法；新版不会覆盖其他作品。

| 版本 | 在线试玩 |
| --- | --- |
| 原版 | https://gaintenemycrabburger.github.io/reigns-ceo/ |
| Claude 版 | https://gaintenemycrabburger.github.io/reigns-ceo/startup/ |
| **GPT 6 Astra 作品** | **https://gaintenemycrabburger.github.io/reigns-ceo/gpt-6-astra/** |
| **上位** | **https://gaintenemycrabburger.github.io/reigns-ceo/shangwei/** |

## 上位

从实习生一路决策升到 CEO。灰账、笼络、甩锅、审计、收购和交棒会形成跨阶段回访；四条资源触底或爆表立即结束，隐藏风险与证据决定八类剧情终局。

- 源码：`game/versions/v6-upstart`；发布文件：`docs/shangwei/index.html`。
- 构建发布：`cd game && python versions/v6-upstart/build.py --publish`。

## GPT 6 Astra 作品

按项目要求以“GPT 6 Astra”标记本次作品。玩家是已经卖爆产品的创始人，第一张卡就面对大厂收购；接下来是价格战、交付、应收账款、收购同行、董事会和新品押注。荒谬感来自真实商业里的算盘，不额外增加世界观或界面。

- 78 张短卡，20 张可冷却重抽；当前卡面平均 15.5 字符、最长 19。
- 保留原版 UI、资源图标、左右划卡和反馈节奏，不使用 Claude 版 UI。
- 无固定结束回合。经营得下去就继续；有先前承诺时资源归零可触发一次因果救援，出售、交棒和休息均可拒绝。
- 源码：game/versions/v5-sixthirty；发布文件：docs/gpt-6-astra/index.html。

构建并生成发布文件：

```powershell
cd game
python versions/v5-sixthirty/build.py --publish
node --test versions/v5-sixthirty/verify.test.js
python -m unittest discover -s versions/v5-sixthirty -p test_build.py
```
