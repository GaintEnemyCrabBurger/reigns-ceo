# Feedback-First Story Deck V3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the mandatory four-CEO storyline with an easier, more varied deck that gives unmistakable feedback after every decision.

**Architecture:** Keep the four-resource swipe engine and 18-decision tenure. Replace the linear story themes with two randomly selected, self-contained two-beat episodes per tenure; ordinary cards fill the gaps. The engine renders a dedicated result beat after each swipe, combining a direct character response with resource direction chips, while rare legacy cards restate their own cause.

**Tech Stack:** Semicolon-delimited CSV card data, vanilla JavaScript, HTML/CSS, Python build and simulation scripts.

---

### Task 1: Preserve the current playable version

**Files:**
- Create: `versions/v2-merged-linear/cards.csv`
- Create: `versions/v2-merged-linear/engine.js`
- Create: `versions/v2-merged-linear/index.html`
- Create: `versions/v2-merged-linear/玩.html`
- Create: `versions/v2-merged-linear/设计文档.md`
- Create: `versions/README.md`

**Step 1:** Copy the current source and self-contained build into the version directory.

**Step 2:** Compare SHA-256 hashes with the active files.

### Task 2: Build the feedback-first deck

**Files:**
- Create: `cards-feedback-first-episodes.csv`
- Modify: `cards.csv`

**Step 1:** Retain resource endings, pressure rescues, and the useful standalone daily pool.

**Step 2:** Remove the mandatory `rescue -> control -> leak -> reckoning` progression from the active deck.

**Step 3:** Add five concrete business episodes for the first half of a tenure and five workplace episodes for the second half. Each episode has one setup and one payoff within the same tenure.

**Step 4:** Add explicit, self-contained legacy cards and resource-sensitive board reviews at decision 18.

**Step 5:** Run `python -X utf8 build.py`; expect no schema, jump, duplicate, or flag errors.

### Task 3: Strengthen immediate feedback

**Files:**
- Modify: `engine.js`
- Modify: `index.html`

**Step 1:** Render the selected character response as a separate result beat.

**Step 2:** Add icon-and-arrow chips for every resource that changed, without exposing numbers.

**Step 3:** Hold the next card until the result beat has been readable for roughly 1.4 seconds.

**Step 4:** Verify the feedback panel fits narrow and short viewports.

### Task 4: Adapt pacing tests

**Files:**
- Modify: `sim.py`
- Modify: `build.py`

**Step 1:** Add the new scheduled endings to simulation inheritance.

**Step 2:** Report tenure length and early resource endings for random and resource-aware play.

**Step 3:** Tighten copy warnings for long questions and long choice labels.

### Task 5: Build, snapshot, and publish V3

**Files:**
- Create: `versions/v3-feedback-first/*`
- Modify: `玩.html`
- Modify: `../deploy/index.html`
- Modify: `../docs/index.html`

**Step 1:** Run syntax checks, card validation, simulations, and `git diff --check`.

**Step 2:** Copy the verified V3 source and playable page into its version directory.

**Step 3:** Synchronize the generated page to both publishing mirrors and verify matching hashes.
