# 创始人 · GPT 6 Astra 作品

在线试玩：https://gaintenemycrabburger.github.io/reigns-ceo/gpt-6-astra/

作品按用户要求标记为 GPT 6 Astra。玩家不是从零起步，而是已经把产品卖起来的创始人：第一张卡就要处理大厂收购，之后进入价格战、交付、应收账款、收购同行、董事会和新品押注。荒谬感只来自真实商业里那些不体面的算盘，不另造世界观。

## 不变的约束

- 用原版 UI 和完整划卡交互，不用 startup 的界面，不增加面板或收藏。
- 一张卡只说一件事：78 张，卡面平均 15.5 字符、最长 19；选项最多 7，反馈最多 20。
- 没有固定任期；20 张经营卡可冷却后重抽。出售、交棒和休息都有继续选项。
- 新剧情用独立 v8 存档，旧版本存档不删除、不混入新剧情。
- 资源跌到 0 前，如果玩家曾经按时付款、留住团队、守住客户或回到产品现场，会触发一次有因果的救援卡；市场和心气冲到顶，也各有一次可见的缓冲决策。

## 构建与测试

在 game 目录执行：

```powershell
python versions/v5-sixthirty/build.py --publish
node --test versions/v5-sixthirty/verify.test.js
python -m unittest discover -s versions/v5-sixthirty -p test_build.py
node versions/v5-sixthirty/simulate.js --smart --runs 100 --generations 1 --max-turns 1000 --report
node versions/v5-sixthirty/simulate.js --policy random --runs 200 --generations 3 --max-turns 300 --report
```

修改 story.py；CSV、JSON、故事手册、玩.html 和 docs/gpt-6-astra/index.html 均由构建导出。仅在准备发布时加 --publish，不覆盖原版或 Claude 入口。

16 项 Node 测试与 3 项 Python 测试通过，覆盖原版 UI、短卡预算、开场分支、长存档、跨分支回访、资源归零救援、峰值缓冲、主动退场和坏存档。模拟时长只是观测窗口，不是游戏上限；模拟结果也不替代真人试玩。

本地目录保留旧名 v5-sixthirty 以兼容预览地址，原版入口和 Claude 的 startup 入口不改。
