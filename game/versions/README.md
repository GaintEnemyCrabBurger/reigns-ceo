# Playable Versions

Each iteration keeps its source deck and a self-contained `玩.html` when the engine changes.

| Version | Description | Entry |
|---|---|---|
| V1 | Original independent long-story deck | `../cards-independent.csv` |
| V2 | Four-CEO mandatory merged storyline | `v2-merged-linear/玩.html` |
| V3 | Feedback-first random short episodes; clear swipe threshold | `v3-feedback-first/玩.html` |
| V4 | Open-ended tenure; fresh state on every new game | `v4-open-ended/玩.html` |
| V5 · GPT 6 Astra | Real-business founder story; 75 short cards, original UI, open-ended operation and branching consequences | `v5-sixthirty/玩.html` |

The original game remains in the parent `game` directory. The GPT 6 Astra work is an independent fork; its historical directory name is retained, but the workshop and routine-management drafts are replaced. Claude's separate iteration remains in `../startup/`.

GPT 6 Astra online entry: https://gaintenemycrabburger.github.io/reigns-ceo/gpt-6-astra/

Publish only its independent Pages directory with `python versions/v5-sixthirty/build.py --publish`. The original entry and the Claude `/startup/` entry are not overwritten.
