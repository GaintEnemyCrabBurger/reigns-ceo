# Merged Story Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use the available Code workflow to implement this plan task-by-task.

**Goal:** Replace the default independent story arcs with one causal, four-tenure corporate struggle while preserving the current deck and shortening each tenure to 18-22 choices.

**Architecture:** Keep the semicolon-delimited card engine and express most pacing through card conditions, weights, named jumps, and persistent flags. Add only the small engine support needed for a visible board-review countdown and narrative succession endings. Extend the existing validator and simulator so story state and tenure targets are mechanically checked.

**Tech Stack:** Static HTML/CSS/JavaScript, semicolon-delimited CSV, Python build and simulation scripts.

---

### Task 1: Preserve the independent deck

**Files:**
- Create: `game/cards-independent.csv`
- Modify: `game/设计文档.md`

**Steps:**
1. Copy the current `cards.csv` byte-for-byte to `cards-independent.csv`.
2. Record that `cards.csv` is the merged default and the archived file remains available for a later selector.
3. Verify both files parse as 22-column semicolon CSV and the archive hash matches the pre-edit deck.

### Task 2: Author the merged causal story

**Files:**
- Modify: `game/cards.csv`

**Steps:**
1. Replace the four isolated arc blocks with four linked acts: rescue, founder conflict, leak, and reckoning.
2. Use `nb_story` to advance only after an act-ending succession.
3. Reuse and consume existing permanent flags such as `dealer_keep`, `security_keep`, `ipo_polish_keep`, `lie_keep`, and split outcomes.
4. Add conditional successor openings so inherited problems appear within the first five choices.
5. Keep daily cards as breathing room, but add story-relevant flags to the choices that promise exclusivity, board control, surveillance, technical debt, and publicity.
6. Verify every continuation has an incoming named jump and every permanent flag has a reader.

### Task 3: Enforce a readable 18-22 choice tenure

**Files:**
- Modify: `game/engine.js`
- Modify: `game/cards.csv`

**Steps:**
1. Define the board-review target as 18 choices.
2. Show the remaining review distance in the existing metadata row without exposing resource numbers.
3. Add a one-time narrative warning around choice 15.
4. Give the act finale priority at choice 18 and finish its continuation sequence by choice 22.
5. Keep resource-zero/resource-full endings able to end a tenure early.

### Task 4: Strengthen static validation and simulation

**Files:**
- Modify: `game/build.py`
- Modify: `game/sim.py`

**Steps:**
1. Detect permanent flags that are written but never used in a condition.
2. Detect condition counters that are never written.
3. Add configurable run counts and a story-act reach report to the simulator.
4. Track early resource failures separately from scheduled succession endings.
5. Run random and resource-aware simulations; target a resource-aware median of 18-22 cards with no run exceeding the scheduled finale except the post-story loop.

### Task 5: Build and verify the playable artifact

**Files:**
- Regenerate: `game/玩.html`

**Steps:**
1. Run `python build.py` and require zero structural validation errors.
2. Run the reduced deterministic simulation during iteration, then the full simulation for final distribution.
3. Open the local game and play through one scheduled succession with keyboard and pointer controls.
4. Verify mobile sizing, option labels, resource-impact dots, countdown text, answer timing, ending handoff, and inherited opening.

No commits are included in this plan because the working tree contains user-owned UI changes and the user did not request a commit.
