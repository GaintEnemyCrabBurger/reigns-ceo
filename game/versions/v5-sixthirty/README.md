# 创始人 · GPT 6 Astra 作品

在线试玩：https://gaintenemycrabburger.github.io/reigns-ceo/gpt-6-astra/

作品按用户要求标记为 GPT 6 Astra。现实创业作底子，事件采用荒诞喜剧：发布会机器人当众骂老板，放任它就爆红，拔电源就暴露搜索记录；股东随后要请它当 CEO。玩家自己的决定，会以不同后果回来。

## 不变的约束

- 用原版 UI 和完整划卡交互，不用 startup 的界面，不增加面板或收藏。
- 一张卡只说一件事：90 张，卡面平均 15.4 字符、最长 18；选项最多 7，反馈最多 20。
- 没有固定任期；35 张卡可冷却后重抽。出售、交棒和休息都有继续选项。
- 新剧情用独立 v7 存档，旧 v6 存档不删除、不混入新剧情。

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

17 项测试通过，包括开场到机器人夺权的全部 16 种组合。100 局平衡策略均经营到 1000 次决定；随机 600 局中位数 43 次，覆盖全部 90 张卡。测试时长不是游戏上限，模拟结果不代表真人一定觉得好玩。

本地目录保留旧名 v5-sixthirty 以兼容预览地址，内容已不是灯具厂或日常经营问卷。
