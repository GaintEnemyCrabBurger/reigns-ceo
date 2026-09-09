# Reigns CEO

三个独立试玩入口，共用最初的左右划卡玩法；新版不会覆盖其他作品。

| 版本 | 在线试玩 |
| --- | --- |
| 原版 | https://gaintenemycrabburger.github.io/reigns-ceo/ |
| Claude 版 | https://gaintenemycrabburger.github.io/reigns-ceo/startup/ |
| **GPT 6 Astra 作品** | **https://gaintenemycrabburger.github.io/reigns-ceo/gpt-6-astra/** |

## GPT 6 Astra 作品

按项目要求以“GPT 6 Astra”标记本次作品。玩家是已经掌权的创始人，发布会上自家机器人突然骂老板是骗子。接下来是付费骂人、甩锅反噬、机器人夺权、一元收购和出走样机的连锁事故。

- 90 张短卡，35 张可冷却重抽；当前卡面平均 15.4 字符、最长 18。
- 保留原版 UI、资源图标、左右划卡和反馈节奏，不使用 Claude 版 UI。
- 无固定结束回合。经营得下去就继续；出售、交棒和休息均可拒绝。
- 源码：game/versions/v5-sixthirty；发布文件：docs/gpt-6-astra/index.html。

构建并生成发布文件：

```powershell
cd game
python versions/v5-sixthirty/build.py --publish
node --test versions/v5-sixthirty/verify.test.js
python -m unittest discover -s versions/v5-sixthirty -p test_build.py
```
